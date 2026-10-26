from config.testing import cerrar_respuesta
from io import StringIO
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from usuarios.models import Area, Rol, Usuario, UsuarioRol, DocumentoProceso
from .models import SolicitudCompra, CotizacionCompra


FIRMA = [[[10, 10], [50, 40], [90, 20]]]


class DocumentosCompraTests(APITestCase):
    def setUp(self):
        call_command('cargar_permisos_sigta', stdout=StringIO())
        self.area = Area.objects.create(codigo='QA', nombre='Área de prueba')
        self.personas = {}
        for i, rol in enumerate(['SOLICITANTE', 'ENCARGADO_COMPRAS_ALMACEN', 'DAF', 'TESORERIA', 'ADMIN']):
            u = Usuario.objects.create_user(username=f'qa-{i}', email=f'qa-{i}@example.invalid', nombre_completo=f'Usuario de prueba {i}')
            UsuarioRol.objects.create(usuario=u, rol=Rol.objects.get(codigo=rol))
            self.personas[rol] = u
        self.compra = SolicitudCompra.objects.create(codigo='QA-01', titulo='Expediente de prueba', solicitante=self.personas['SOLICITANTE'], area=self.area, tipo='BIEN', cantidad=2, estado='FONDOS_DESEMBOLSADOS', monto_desembolsado='20.00')
        self.url = f'/api/compras/solicitudes/{self.compra.pk}'

    def autenticar(self, rol):
        self.client.force_authenticate(self.personas[rol])

    def test_daf_consulta_pero_no_registra_cotizaciones(self):
        self.autenticar('DAF')
        self.compra.estado = 'CREADO_PENDIENTE_DAF'
        self.compra.save(update_fields=['estado'])
        self.assertEqual(self.client.get(self.url + '/cotizaciones/').status_code, 200)
        respuesta = self.client.post(self.url + '/cotizaciones/', {
            'proveedor': 'Proveedor de prueba', 'descripcion': 'Producto',
            'cantidad': 1, 'precio_unitario': '10.00',
            'documento': SimpleUploadedFile('prueba.pdf', b'%PDF-1.4\n', content_type='application/pdf'),
        }, format='multipart')
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(CotizacionCompra.objects.exists())

    def test_recepcion_sin_firma_no_muta_expediente(self):
        self.autenticar('ENCARGADO_COMPRAS_ALMACEN')
        r = self.client.post(self.url + '/confirmar-recepcion-fondos/', {}, format='json')
        self.assertEqual(r.status_code, 400)
        self.compra.refresh_from_db()
        self.assertIsNone(self.compra.fondos_recibidos_en)
        self.assertFalse(DocumentoProceso.objects.exists())

    def test_firma_identifica_usuario_y_no_se_reutiliza(self):
        self.autenticar('ENCARGADO_COMPRAS_ALMACEN')
        r = self.client.post(self.url + '/confirmar-recepcion-fondos/', {'firma': FIRMA, 'fondos_recibidos_por': 'Identidad ajena'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        d = DocumentoProceso.objects.get()
        self.assertEqual(d.usuario_id, self.personas['ENCARGADO_COMPRAS_ALMACEN'].pk)
        self.assertEqual(d.firma, FIRMA)
        self.assertIn('ENCARGADO_COMPRAS_ALMACEN', d.roles_firmante)
        self.compra.refresh_from_db()
        self.assertEqual(self.compra.fondos_recibidos_por, d.nombre_firmante)
        self.assertEqual(self.client.post(self.url + '/confirmar-recepcion-fondos/', {'firma': FIRMA}, format='json').status_code, 409)
        self.assertEqual(DocumentoProceso.objects.count(), 1)

    def test_documentos_no_visibles_a_otro_solicitante(self):
        self.autenticar('ENCARGADO_COMPRAS_ALMACEN')
        self.client.post(self.url + '/confirmar-recepcion-fondos/', {'firma': FIRMA}, format='json')
        otro = Usuario.objects.create_user(username='qa-otro', email='otro@example.invalid', nombre_completo='Otro usuario de prueba')
        UsuarioRol.objects.create(usuario=otro, rol=Rol.objects.get(codigo='SOLICITANTE'))
        self.client.force_authenticate(otro)
        self.assertEqual(self.client.get(self.url + '/documentos/').status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url + '/documentos/').status_code, 401)

    def test_pdf_incorpora_firma_y_conserva_instantanea(self):
        self.autenticar('ENCARGADO_COMPRAS_ALMACEN')
        self.client.post(self.url + '/confirmar-recepcion-fondos/', {'firma': FIRMA}, format='json')
        d = DocumentoProceso.objects.get()
        SolicitudCompra.objects.filter(pk=self.compra.pk).update(titulo='Título modificado después de la firma')
        r = self.client.get(self.url + f'/documentos/{d.pk}/pdf/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'%PDF-1.4'))
        self.assertIn(b'Expediente de prueba', r.content)
        self.assertNotIn(b'T\355tulo modificado', r.content)
        self.assertIn(b'84.50', r.content)  # coordenada de la firma transformada a la página
        self.assertEqual(r['Cache-Control'], 'private, no-store')

    def test_comparacion_seleccion_y_documento_privado(self):
        self.autenticar('ADMIN')
        cotizaciones = []
        for i, precio in enumerate(['10.00', '12.50']):
            r = self.client.post(self.url + '/cotizaciones/', {'proveedor': f'Proveedor de prueba {i}', 'descripcion': 'Producto de prueba', 'cantidad': 2, 'precio_unitario': precio, 'documento': SimpleUploadedFile('prueba.pdf', b'%PDF-1.4\n', content_type='application/pdf')}, format='multipart')
            self.assertEqual(r.status_code, 201, r.data)
            self.assertNotIn('documento', r.data)
            cotizaciones.append(r.data)
        self.assertFalse(CotizacionCompra.objects.filter(seleccionada=True).exists())
        self.assertEqual(cotizaciones[1]['total'], '25.00')
        r = self.client.post(self.url + '/seleccionar-cotizacion/', {'cotizacion_id': cotizaciones[1]['id'], 'motivo': 'Criterio del responsable de prueba'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(CotizacionCompra.objects.get(seleccionada=True).pk, cotizaciones[1]['id'])
        self.autenticar('SOLICITANTE')
        self.assertEqual(self.client.post(self.url + '/seleccionar-cotizacion/', {'cotizacion_id': cotizaciones[0]['id'], 'motivo': 'No autorizado'}, format='json').status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(cotizaciones[0]['documento_url']).status_code, 401)

    def test_evidencia_exige_permiso_o_enlace_de_sesion_vigente(self):
        from rest_framework.authtoken.models import Token
        self.compra.factura = SimpleUploadedFile('evidencia-prueba.pdf', b'%PDF-1.4\n', content_type='application/pdf')
        self.compra.save()
        propietario = self.personas['SOLICITANTE']
        propietario.must_change_password = False
        propietario.save(update_fields=['must_change_password'])
        token = Token.objects.create(user=propietario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        r = self.client.get(self.url + '/')
        self.assertEqual(r.status_code, 200, r.data)
        enlace = r.data['factura']
        self.assertIn('?acceso=', enlace)
        self.client.credentials()
        r = self.client.get(enlace)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Cache-Control'], 'private, no-store')
        cerrar_respuesta(r)
        self.assertEqual(r['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(self.client.get('/media/' + self.compra.factura.name).status_code, 401)
        token.delete()
        self.assertEqual(self.client.get(enlace).status_code, 401)
