from config.testing import cerrar_respuesta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from django.db import close_old_connections
from rest_framework.test import APITestCase, APIClient
from rest_framework.exceptions import ValidationError
from usuarios.models import Usuario, Rol, UsuarioRol, Area
from .models import SolicitudCompra, MovimientoCajaChica
from .caja_chica import registrar_operacion, resumen, mes_actual


def preparar(clase):
    from io import StringIO
    call_command('cargar_permisos_sigta', stdout=StringIO())
    clase.area = Area.objects.create(codigo='R09', nombre='Área R09')
    clase.personas = {}
    for rol in ('SOLICITANTE','DIRECTOR','TESORERIA','DAF','ENCARGADO_COMPRAS_ALMACEN'):
        u=Usuario.objects.create_user(username='r09-'+rol,email=rol.lower()+'@r09.test',nombre_completo='Persona '+rol,must_change_password=False)
        UsuarioRol.objects.create(usuario=u,rol=Rol.objects.get(codigo=rol))
        clase.personas[rol]=u


def compra(clase,codigo,monto='200',via='CAJA_CHICA'):
    return SolicitudCompra.objects.create(codigo=codigo,titulo='Requerimiento R09',area=clase.area,
        solicitante=clase.personas['SOLICITANTE'],monto_estimado=Decimal(monto),via_adquisicion=via,
        estado='EVALUADO_PENDIENTE_CERTIFICACION',informe=SimpleUploadedFile('informe.pdf',b'%PDF-1.4\nPrueba'),poa=SimpleUploadedFile('poa.pdf',b'%PDF-1.4\nPrueba'),proforma=SimpleUploadedFile('proforma.pdf',b'%PDF-1.4\nPrueba'))


@override_settings(SIA_FONDO_MENSUAL=Decimal('500'))
class CajaChicaR09Tests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        preparar(cls)

    def test_reserva_al_aprobar_y_rechazo_sin_saldo(self):
        self.client.force_authenticate(self.personas['DAF'])
        for i in range(3):
            s=compra(self,'R09-'+str(i))
            r=self.client.post(f'/api/compras/solicitudes/{s.pk}/certificar-daf/',{'certificacion_presupuestaria':SimpleUploadedFile('certificado.pdf',b'%PDF-1.4\nPrueba')},format='multipart')
            self.assertEqual(r.status_code,200 if i<2 else 400,r.data)
            if i==2:
                self.assertEqual(r.data['regla'],'R09')
                s.refresh_from_db();self.assertEqual(s.estado,'EVALUADO_PENDIENTE_CERTIFICACION')
        self.assertEqual(resumen()['saldo_disponible'],100)
        self.assertEqual(MovimientoCajaChica.objects.count(),2)

    def test_conversion_desembolso_no_duplica_y_ajusta_importe_real(self):
        s=compra(self,'R09-UNICO')
        registrar_operacion(s)
        registrar_operacion(s)
        self.assertEqual(resumen()['saldo_disponible'],300)
        registrar_operacion(s,monto='180',desembolso=True)
        self.assertEqual(resumen()['saldo_disponible'],320)
        self.assertEqual(resumen()['utilizado'],180)
        self.assertEqual(resumen()['comprometido'],0)
        with self.assertRaises(ValidationError):registrar_operacion(s,monto='180',desembolso=True)
        self.assertEqual(MovimientoCajaChica.objects.count(),1)

    def test_finanzas_no_consume_fondo_y_monto_exacto(self):
        s=compra(self,'R09-FIN','9000','FINANZAS')
        self.assertIsNone(registrar_operacion(s))
        s=compra(self,'R09-EXACTO','500')
        registrar_operacion(s)
        self.assertEqual(resumen()['saldo_disponible'],0)

    @override_settings(SIA_FONDO_MENSUAL=Decimal('7000'))
    def test_fondo_modificable_por_configuracion(self):
        registrar_operacion(compra(self,'R09-CONFIG','200'))
        self.assertEqual(resumen()['saldo_disponible'],6800)

    def test_endpoint_autenticacion_permisos_y_saldo_real(self):
        self.assertEqual(self.client.get('/api/caja-chica/saldo/').status_code,401)
        self.client.force_authenticate(self.personas['SOLICITANTE'])
        self.assertEqual(self.client.get('/api/caja-chica/saldo/').status_code,403)
        registrar_operacion(compra(self,'R09-LECTURA'))
        for rol in ('TESORERIA','DAF','ENCARGADO_COMPRAS_ALMACEN','DIRECTOR'):
            self.client.force_authenticate(self.personas[rol])
            r=self.client.get('/api/caja-chica/saldo/')
            self.assertEqual(r.status_code,200,r.data)
            self.assertEqual(Decimal(r.data['saldo_disponible']),300)
            self.assertEqual(len(r.data['movimientos']),1)

    def test_recibo_incluye_saldo_proyectado_y_conserva_reserva(self):
        s=compra(self,'R09-PDF')
        registrar_operacion(s)
        s.estado='APROBADO_PARA_DESEMBOLSO';s.save()
        self.client.force_authenticate(self.personas['TESORERIA'])
        r=self.client.post(f'/api/compras/solicitudes/{s.pk}/recibos-tesoreria/',{
            'monto_desembolsado':'200','tipo_desembolso':'Efectivo','responsable_adquisicion':'Persona Compras'},format='json')
        self.assertEqual(r.status_code,201,r.data)
        self.assertEqual(Decimal(r.data['datos']['saldo_restante']),300)
        original=self.client.get(r.data['original_url'])
        try:
            contenido=b''.join(original.streaming_content)
            self.assertTrue(contenido.startswith(b'%PDF-'))
            self.assertIn(b'SALDO RESTANTE',contenido)
        finally:
            cerrar_respuesta(original)
        self.assertEqual(resumen()['saldo_disponible'],300)

    def test_saldo_confirmado_pdf_no_altera_recibo_original(self):
        s=compra(self,'R09-CONFIRMADO')
        registrar_operacion(s);s.estado='APROBADO_PARA_DESEMBOLSO';s.save()
        self.client.force_authenticate(self.personas['TESORERIA'])
        datos={'monto_desembolsado':'200','tipo_desembolso':'Efectivo','responsable_adquisicion':'Persona Compras'}
        base=f'/api/compras/solicitudes/{s.pk}'
        r=self.client.post(base+'/recibos-tesoreria/',datos,format='json')
        self.assertEqual(r.status_code,201,r.data)
        from .models import ReciboTesoreria
        recibo=ReciboTesoreria.objects.get(pk=r.data['id'])
        with recibo.original.open('rb') as archivo:original=archivo.read()
        datos.update(recibo_id=recibo.pk,recibo_firmado=SimpleUploadedFile('firmado.pdf',b'%PDF-1.4\nFirmado',content_type='application/pdf'))
        confirmado=self.client.post(base+'/desembolsar/',datos,format='multipart')
        self.assertEqual(confirmado.status_code,200,confirmado.data)
        recibo.refresh_from_db()
        with recibo.original.open('rb') as archivo:self.assertEqual(archivo.read(),original)
        with recibo.constancia_saldo.open('rb') as archivo:
            contenido=archivo.read();self.assertIn(b'300.00',contenido)
        self.assertEqual(resumen()['utilizado'],200)


@override_settings(SIA_FONDO_MENSUAL=Decimal('300'))
class CajaChicaConcurrenciaPostgresTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_dos_aprobaciones_no_sobregiran_un_mismo_fondo(self):
        preparar(self)
        ids=[compra(self,'R09-PG-'+str(i)).pk for i in range(2)]
        barrera=Barrier(2)
        usuario=self.personas['DAF'].pk
        def aprobar(pk):
            close_old_connections()
            try:
                c=APIClient();c.force_authenticate(Usuario.objects.get(pk=usuario));barrera.wait(timeout=15)
                return c.post(f'/api/compras/solicitudes/{pk}/certificar-daf/',{'certificacion_presupuestaria':SimpleUploadedFile('certificado.pdf',b'%PDF-1.4\nPrueba')},format='multipart').status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados=list(pool.map(aprobar,ids))
        self.assertEqual(sorted(resultados),[200,400])
        self.assertEqual(resumen()['saldo_disponible'],100)
        self.assertEqual(MovimientoCajaChica.objects.count(),1)
