from config.testing import cerrar_respuesta
from io import StringIO
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase
from usuarios.models import Area, Rol, Usuario, UsuarioRol
from .models import SolicitudCompra, ActaEntregaAlmacen, CotizacionCompra


class ActasAlmacenTests(APITestCase):
    def setUp(self):
        call_command('cargar_permisos_sigta', stdout=StringIO())
        self.usuarios = {}
        for rol, nombre in [('SOLICITANTE', 'Ana Lopez'), ('ENCARGADO_COMPRAS_ALMACEN', 'Carlos Perez'), ('TESORERIA', 'Luis Ramos'), ('AUXILIAR_SERVICIOS_GENERALES', 'Tecnico Mantenimiento'), ('ESPECIALISTA', 'Tecnico Soporte')]:
            usuario = Usuario.objects.create_user(username=rol, email=f'{rol.lower()}@example.invalid', nombre_completo=nombre)
            UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(codigo=rol))
            self.usuarios[rol] = usuario
        area = Area.objects.create(codigo='ALM', nombre='Laboratorio')
        self.s = SolicitudCompra.objects.create(codigo='CMP-QA-ACTA', titulo='Sillas para laboratorio', descripcion='Sillas de oficina', especificaciones='Color azul', area=area, solicitante=self.usuarios['SOLICITANTE'], estado='COMPRA_REGISTRADA', tipo='BIEN', cantidad=2, cantidad_recibida=2, cantidad_entregada=2, monto_real='600.00', proveedor='Proveedor Nacional', responsable_recepcion='Carlos Perez', entregado_a='Ana Lopez', fecha_ingreso_almacen=timezone.now(), fecha_despacho_almacen=timezone.now())
        self.url = f'/api/compras/solicitudes/{self.s.pk}'
        self.client.force_authenticate(self.usuarios['ENCARGADO_COMPRAS_ALMACEN'])

    def generar(self):
        r = self.client.post(self.url + '/actas-almacen/', {'recibe': 'Ana Lopez', 'observaciones': 'Bienes completos', 'entrega_confirmada': True}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        return r.data

    def firmado(self, contenido=b'%PDF-1.4\nCopia con firmas'):
        return SimpleUploadedFile('acta-firmada.pdf', contenido, content_type='application/pdf')

    def test_original_con_datos_y_archivo_firmado_en_historial(self):
        acta = self.generar()
        r = self.client.get(acta['original_url'])
        contenido = b''.join(r.streaming_content)
        cerrar_respuesta(r)
        for texto in (b'Sillas para laboratorio', b'Ana Lopez', b'Carlos Perez', b'600.00', b'Bienes completos'):
            self.assertIn(texto, contenido)
        self.assertEqual(r['Cache-Control'], 'private, no-store')
        r = self.client.post(self.url + '/entregar-con-acta/', {'acta_id': acta['id'], 'acta_conformidad': self.firmado()}, format='multipart')
        self.assertEqual(r.status_code, 200, r.data)
        self.s.refresh_from_db()
        self.assertEqual(self.s.estado, 'COMPRADO_Y_ENTREGADO')
        a = ActaEntregaAlmacen.objects.get()
        self.assertIsNotNone(a.confirmado_en)
        with a.original.open('rb') as f:
            self.assertEqual(f.read(), contenido)
        historial = self.client.get(self.url + '/actas-almacen/').data
        self.assertTrue(historial[0]['firmado_url'])
        r = self.client.get(historial[0]['firmado_url'])
        self.assertEqual(b''.join(r.streaming_content), b'%PDF-1.4\nCopia con firmas')
        cerrar_respuesta(r)

    def test_director_visualiza_actas_sin_generarlas(self):
        acta = self.generar()
        r = self.client.post(self.url + '/entregar-con-acta/', {'acta_id': acta['id'], 'acta_conformidad': self.firmado()}, format='multipart')
        self.assertEqual(r.status_code, 200, r.data)
        director = Usuario.objects.create_user(username='director', email='director@example.invalid', nombre_completo='Director')
        UsuarioRol.objects.create(usuario=director, rol=Rol.objects.get(codigo='DIRECTOR'))
        self.client.force_authenticate(director)
        r = self.client.get(self.url + '/actas-almacen/')
        self.assertEqual(r.status_code, 200, r.data)
        for campo in ('original_url', 'firmado_url'):
            pdf = self.client.get(r.data[0][campo])
            self.assertEqual(pdf.status_code, 200)
            try:
                self.assertTrue(b''.join(pdf.streaming_content).startswith(b'%PDF'))
            finally:
                cerrar_respuesta(pdf)
        r = self.client.post(self.url + '/actas-almacen/', {'recibe': 'Ana Lopez'}, format='json')
        self.assertEqual(r.status_code, 403, r.data)
        self.assertEqual(ActaEntregaAlmacen.objects.count(), 1)

    def test_tecnico_receptor_identificado_y_acta_firmada_al_entregar(self):
        from mantenimiento.models import EstadoMantenimiento, RequerimientoMantenimiento
        requerimiento = RequerimientoMantenimiento.objects.create(
            codigo='MTO-ACTA-TECNICO', titulo='Repuesto', descripcion='Reparacion', area=self.s.area,
            solicitante=self.usuarios['SOLICITANTE'],
            auxiliar_asignado=self.usuarios['AUXILIAR_SERVICIOS_GENERALES'],
            estado=EstadoMantenimiento.objects.get(codigo='EN_ESPERA_COMPRA'),
            estado_compra_componente='VIABLE',
        )
        self.s.requerimiento_mantenimiento = requerimiento
        self.s.origen_modulo = 'MANTENIMIENTO'
        self.s.save()
        r = self.client.post(self.url + '/actas-almacen/', {'recibe': 'Ana Lopez', 'entrega_confirmada': True}, format='json')
        self.assertEqual(r.status_code, 400, r.data)
        r = self.client.post(self.url + '/actas-almacen/', {'entrega_confirmada': True}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        acta = r.data
        self.assertEqual(acta['datos']['recibe'], 'Tecnico Mantenimiento')
        self.assertEqual(acta['datos']['recibe_id'], self.usuarios['AUXILIAR_SERVICIOS_GENERALES'].pk)
        self.client.force_authenticate(self.usuarios['AUXILIAR_SERVICIOS_GENERALES'])
        self.assertEqual(self.client.get(self.url + '/actas-almacen/').status_code, 200)
        pdf = self.client.get(acta['original_url'])
        self.assertEqual(pdf.status_code, 200)
        cerrar_respuesta(pdf)
        self.assertEqual(self.client.post(self.url + '/actas-almacen/', {'entrega_confirmada': True}, format='json').status_code, 404)
        self.client.force_authenticate(self.usuarios['ESPECIALISTA'])
        self.assertEqual(self.client.get(acta['original_url']).status_code, 404)
        self.client.force_authenticate(self.usuarios['ENCARGADO_COMPRAS_ALMACEN'])
        r = self.client.post(self.url + '/entregar-con-acta/', {'acta_id': acta['id'], 'acta_conformidad': self.firmado()}, format='multipart')
        self.assertEqual(r.status_code, 200, r.data)
        self.s.refresh_from_db()
        self.assertIsNotNone(self.s.acta_firmada_en)
        requerimiento.refresh_from_db()
        self.assertEqual(requerimiento.estado_compra_componente, 'PENDIENTE_RECEPCION_TECNICO')
        self.client.force_authenticate(self.usuarios['SOLICITANTE'])
        self.assertEqual(self.client.get(self.url + '/actas-almacen/').status_code, 403)
        self.assertEqual(self.client.post(self.url + '/firmar-acta/', {}, format='json').status_code, 409)
        self.client.force_authenticate(self.usuarios['AUXILIAR_SERVICIOS_GENERALES'])
        pdf = self.client.get(self.url + '/actas-almacen/').data[0]['firmado_url']
        respuesta = self.client.get(pdf)
        self.assertEqual(respuesta.status_code, 200)
        cerrar_respuesta(respuesta)

    def test_tecnico_soporte_visualiza_acta_de_su_componente(self):
        from soporte.models import Ticket, EstadoTicket, CategoriaTicket
        ticket = Ticket.objects.create(codigo='SOP-ACTA-TECNICO', titulo='Repuesto', descripcion='Reparacion',
            area=self.s.area, categoria=CategoriaTicket.objects.first(), solicitante=self.usuarios['SOLICITANTE'],
            estado=EstadoTicket.objects.get(codigo='EN_EJECUCION'), tecnico_asignado=self.usuarios['ESPECIALISTA'])
        self.s.ticket_soporte = ticket
        self.s.origen_modulo = 'SOPORTE'
        self.s.save()
        r = self.client.post(self.url + '/actas-almacen/', {'entrega_confirmada': True}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['datos']['recibe'], 'Tecnico Soporte')
        self.client.force_authenticate(self.usuarios['ESPECIALISTA'])
        acta = self.client.get(self.url + '/actas-almacen/')
        self.assertEqual(acta.status_code, 200, acta.data)
        pdf = self.client.get(acta.data[0]['original_url'])
        self.assertEqual(pdf.status_code, 200)
        cerrar_respuesta(pdf)
        self.client.force_authenticate(self.usuarios['AUXILIAR_SERVICIOS_GENERALES'])
        self.assertEqual(self.client.get(self.url + '/actas-almacen/').status_code, 404)

    def test_no_genera_acta_sin_confirmar_entrega_fisica(self):
        r = self.client.post(self.url + '/actas-almacen/', {'recibe': 'Ana Lopez'}, format='json')
        self.assertEqual(r.status_code, 400, r.data)
        self.assertFalse(ActaEntregaAlmacen.objects.exists())

    def test_no_entrega_sin_pdf_o_con_contenido_invalido(self):
        acta = self.generar()
        for datos in ({'acta_id': acta['id']}, {'acta_id': acta['id'], 'acta_conformidad': self.firmado(b'No es un PDF')}):
            r = self.client.post(self.url + '/entregar-con-acta/', datos, format='multipart')
            self.assertEqual(r.status_code, 400, r.data)
        self.s.refresh_from_db()
        self.assertEqual(self.s.estado, 'COMPRA_REGISTRADA')
        self.assertIsNone(ActaEntregaAlmacen.objects.get().confirmado_en)

    def test_datos_modificados_exigen_nueva_acta(self):
        acta = self.generar()
        SolicitudCompra.objects.filter(pk=self.s.pk).update(cantidad_entregada=1)
        r = self.client.post(self.url + '/entregar-con-acta/', {'acta_id': acta['id'], 'acta_conformidad': self.firmado()}, format='multipart')
        self.assertEqual(r.status_code, 400, r.data)
        self.assertIsNone(ActaEntregaAlmacen.objects.get().confirmado_en)

    def test_solo_ultima_acta_y_usuario_que_la_genero(self):
        anterior = self.generar()
        self.generar()
        r = self.client.post(self.url + '/entregar-con-acta/', {'acta_id': anterior['id'], 'acta_conformidad': self.firmado()}, format='multipart')
        self.assertEqual(r.status_code, 400, r.data)
        otro = Usuario.objects.create_user(username='otro-almacen', email='otro-almacen@example.invalid', nombre_completo='Otro Encargado')
        UsuarioRol.objects.create(usuario=otro, rol=Rol.objects.get(codigo='ENCARGADO_COMPRAS_ALMACEN'))
        self.client.force_authenticate(otro)
        r = self.client.post(self.url + '/entregar-con-acta/', {'acta_id': anterior['id'], 'acta_conformidad': self.firmado()}, format='multipart')
        self.assertEqual(r.status_code, 404, r.data)

    def test_permisos_estado_y_nombre_completo(self):
        self.assertEqual(self.client.post(self.url + '/actas-almacen/', {'recibe': 'Ana'}).status_code, 400)
        SolicitudCompra.objects.filter(pk=self.s.pk).update(fecha_despacho_almacen=None)
        self.assertEqual(self.client.post(self.url + '/actas-almacen/', {'recibe': 'Ana Lopez'}).status_code, 400)
        self.client.force_authenticate(self.usuarios['TESORERIA'])
        self.assertEqual(self.client.get(self.url + '/actas-almacen/').status_code, 403)

    def test_almacen_no_puede_registrar_cotizaciones(self):
        r = self.client.post(self.url + '/cotizaciones/', {'proveedor': 'Otra empresa', 'cantidad': 2, 'precio_unitario': '300.00'}, format='json')
        self.assertEqual(r.status_code, 403, r.data)
        self.assertFalse(CotizacionCompra.objects.exists())
