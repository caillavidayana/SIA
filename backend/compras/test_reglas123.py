from config.testing import cerrar_respuesta
"""Integración R01–R03: API, permisos, archivos, transferencia e históricos."""
import json
from decimal import Decimal
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from usuarios.models import Area, Rol, Usuario, UsuarioRol
from soporte.models import Ticket, EstadoTicket, CategoriaTicket, NotificacionSoporte
from mantenimiento.models import RequerimientoMantenimiento, EstadoMantenimiento
from auditoria.models import Bitacora
from .models import SolicitudCompra, CotizacionCompra
from .reglas_cotizaciones import identidad_proveedor
from config.reglas import prioridad_automatica


class ReglasTextoTests(SimpleTestCase):
    def test_r03_palabras_completas_y_categorias(self):
        for titulo, descripcion, categoria in [('Falla de RED', '', None), ('', 'Sin CONECTIVIDAD de INTERNET', None), ('Impresora', '', 'SERVIDORES'), ('', '', 'RED')]:
            with self.subTest(titulo=titulo, categoria=categoria):
                self.assertEqual(prioridad_automatica(titulo, descripcion, categoria), 'ALTA')
        for texto in ('Pared dañada', 'Cambio de pintura', 'redimensionar', 'servidores sin categoría'):
            self.assertIsNone(prioridad_automatica(texto))

    def test_r02_normaliza_proveedor_y_documento(self):
        self.assertEqual(identidad_proveedor(' Ácme S.R.L. '), identidad_proveedor('ACME srl'))
        self.assertEqual(identidad_proveedor('Alias', '123-45'), identidad_proveedor('Otro alias', '12345'))


class Reglas123APITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('cargar_permisos_sigta', verbosity=0)
        cls.area = Area.objects.create(codigo='R123', nombre='Área R123')
        cls.personas = {}
        for rol in ('SOLICITANTE', 'ESPECIALISTA', 'JEFE_UTIC', 'AUXILIAR_SERVICIOS_GENERALES', 'SERVICIOS_GENERALES', 'DAF', 'DIRECTOR'):
            u=Usuario.objects.create_user(username='r123-'+rol, email=rol.lower()+'@example.test', nombre_completo=rol, must_change_password=False)
            UsuarioRol.objects.create(usuario=u, rol=Rol.objects.get(codigo=rol), activo=True)
            if rol=='DIRECTOR':
                from django.contrib.auth.models import Group
                from django.conf import settings
                u.groups.add(Group.objects.get(name=settings.SIA_GRUPO_APROBADOR))
            cls.personas[rol]=u

    def archivo(self, nombre='cotizacion.pdf'):
        return SimpleUploadedFile(nombre, b'%PDF-1.4\nDocumento de prueba', content_type='application/pdf')

    def objeto(self, modulo='soporte', **extra):
        datos=dict(codigo=('R123-S-' if modulo=='soporte' else 'R123-M-')+str(Ticket.objects.count()+RequerimientoMantenimiento.objects.count()),
                   titulo='Equipo averiado', descripcion='Necesita reparación', solicitante=self.personas['SOLICITANTE'], area=self.area, ubicacion='Laboratorio', equipo_afectado='Equipo de laboratorio', **extra)
        if modulo=='soporte':
            return Ticket.objects.create(estado=EstadoTicket.objects.get(codigo='EN_EJECUCION'), categoria=CategoriaTicket.objects.get(codigo='HARDWARE'), tecnico_asignado=self.personas['ESPECIALISTA'], **datos)
        return RequerimientoMantenimiento.objects.create(estado=EstadoMantenimiento.objects.get(codigo='EN_MANTENIMIENTO'), tipo='CORRECTIVO', auxiliar_asignado=self.personas['AUXILIAR_SERVICIOS_GENERALES'], **datos)

    def enviar(self, obj, monto='700', proveedores=('Uno','Dos','Tres'), borrador=False, via='CAJA_CHICA', guardados=()):
        soporte=isinstance(obj, Ticket)
        self.client.force_authenticate(self.personas['ESPECIALISTA' if soporte else 'AUXILIAR_SERVICIOS_GENERALES'])
        datos={'costo_estimado':monto, 'via_compra':via,
            'cotizaciones':[self.archivo(f'cotizacion-{i}.pdf') for i,_ in enumerate(proveedores)],
            'cotizaciones_metadata':json.dumps([{'proveedor':p} for p in proveedores]),
            'proveedores_guardados':json.dumps(list(guardados))}
        datos.update({'componente_requerido':'Repuesto', 'cantidad_componente':1, 'especificaciones_tecnicas':'Modelo A', 'justificacion_compra':'Recuperar equipo'} if soporte else {'producto_requerido':'Repuesto', 'cantidad_requerida':1, 'especificacion_producto':'Modelo A'})
        accion='guardar-borrador-requerimiento' if borrador else 'solicitar-requerimiento-componente' if soporte else 'solicitar-requerimiento'
        base='/api/soporte/tickets' if soporte else '/api/mantenimiento/requerimientos'
        return self.client.post(f'{base}/{obj.pk}/{accion}/',datos,format='multipart')

    def test_r01_rechaza_1200_aunque_haya_tres_cotizaciones(self):
        for modulo in ('soporte','mantenimiento'):
            obj=self.objeto(modulo)
            r=self.enviar(obj,'1200')
            self.assertEqual(r.status_code,400,r.data);self.assertEqual(r.data['regla'],'R01')
            obj.refresh_from_db();self.assertEqual(obj.estado_compra_componente,'')
            self.assertEqual(obj.cotizaciones_r02.count(),0)

    @override_settings(SIA_LIMITE_CAJA_CHICA=Decimal('800'))
    def test_r01_no_se_elude_enviando_via_finanzas(self):
        for modulo in ('soporte','mantenimiento'):
            r=self.enviar(self.objeto(modulo),'900',via='FINANZAS')
            self.assertEqual(r.status_code,400,r.data);self.assertEqual(r.data['regla'],'R01')
        self.assertEqual(self.client.get('/api/auditoria/limite-caja-chica/').data['umbral_cotizaciones'],'500')

    def test_r01_limites_inclusivos_999_y_1000_con_tres(self):
        for modulo in ('soporte','mantenimiento'):
            for monto in ('999','1000'):
                self.assertEqual(self.enviar(self.objeto(modulo),monto).status_code,200)

    @override_settings(SIA_LIMITE_CAJA_CHICA=Decimal('1500'))
    def test_r01_cambio_a_1500_permite_1200_con_tres(self):
        self.assertEqual(self.enviar(self.objeto(),'1200').status_code,200)

    def test_r02_cantidades_y_proveedores_distintos(self):
        for modulo in ('soporte','mantenimiento'):
            for proveedores,faltantes in [(('Uno',),2),(('Uno','Dos'),1),(('Ácme S.R.L.','acme srl',' ACME S R L '),2)]:
                r=self.enviar(self.objeto(modulo),monto='700',proveedores=proveedores)
                self.assertEqual(r.status_code,400,r.data)
                self.assertEqual(int(r.data['cotizaciones_faltantes']),faltantes,r.data)
            self.assertEqual(self.enviar(self.objeto(modulo)).status_code,200)
            self.assertEqual(self.enviar(self.objeto(modulo),'500',('Uno',)).status_code,200)

    @override_settings(SIA_UMBRAL_COTIZACIONES=Decimal('800'))
    def test_r02_umbral_configurable(self):
        self.assertEqual(self.enviar(self.objeto(),'700',('Uno',)).status_code,200)

    def test_r02_borradores_reapertura_y_agregado_sin_reemplazo(self):
        for modulo in ('soporte','mantenimiento'):
            obj=self.objeto(modulo)
            r=self.enviar(obj,proveedores=('',),borrador=True)
            self.assertEqual(r.status_code,200,r.data)
            clave='ticket' if modulo=='soporte' else 'requerimiento'
            c=r.data[clave]['cotizaciones'][0]
            url_original=c['archivo_url']
            base='/api/soporte/tickets' if modulo=='soporte' else '/api/mantenimiento/requerimientos'
            self.assertEqual(self.client.get(f'{base}/{obj.pk}/').data['cotizaciones'][0]['id'],c['id'])
            r=self.enviar(obj,proveedores=('Dos','Tres'),guardados=[{'id':c['id'],'proveedor':'Uno'}])
            self.assertEqual(r.status_code,200,r.data)
            filas=r.data[clave]['cotizaciones']
            self.assertEqual(len(filas),3)
            self.assertEqual(filas[0]['archivo_url'],url_original)

    def test_r02_todas_llegan_a_jefatura_y_compras_y_archivos_protegidos(self):
        for modulo in ('soporte','mantenimiento'):
            obj=self.objeto(modulo)
            r=self.enviar(obj)
            self.assertEqual(r.status_code,200,r.data)
            soporte=modulo=='soporte'
            base='/api/soporte/tickets' if soporte else '/api/mantenimiento/requerimientos'
            self.client.force_authenticate(self.personas['JEFE_UTIC' if soporte else 'SERVICIOS_GENERALES'])
            detalle=self.client.get(f'{base}/{obj.pk}/')
            self.assertEqual(len(detalle.data['cotizaciones']),3)
            for c in detalle.data['cotizaciones']:
                respuesta=self.client.get(c['archivo_url'])
                self.assertEqual(respuesta.status_code,200)
                self.assertTrue(b''.join(respuesta.streaming_content).startswith(b'%PDF'))
                cerrar_respuesta(respuesta)
            r=self.client.post(f'{base}/{obj.pk}/evaluar-viabilidad-compra/',{'viable':'true','poa':self.archivo('poa.pdf'),'pedido':self.archivo('pedido.pdf')},format='multipart')
            self.assertEqual(r.status_code,200,r.data)
            compra=SolicitudCompra.objects.get(**{'ticket_soporte' if soporte else 'requerimiento_mantenimiento':obj})
            self.assertEqual(compra.cotizaciones.count(),3)
            self.client.force_authenticate(self.personas['DAF'])
            detalle=self.client.get(f'/api/compras/solicitudes/{compra.pk}/')
            self.assertEqual(len(detalle.data['cotizaciones']),3)
            for c in detalle.data['cotizaciones']:
                respuesta=self.client.get(c['documento_url'])
                self.assertEqual(respuesta.status_code,200)
                self.assertTrue(b''.join(respuesta.streaming_content).startswith(b'%PDF'))
                cerrar_respuesta(respuesta)
            self.client.force_authenticate(self.personas['SOLICITANTE'])
            # Otro solicitante no ve cotizaciones de expedientes ajenos.
            otro=Usuario.objects.create_user(username='otro-'+modulo,email='otro-'+modulo+'@example.test',nombre_completo='Otro',must_change_password=False)
            self.client.force_authenticate(otro)
            r=self.client.get(detalle.data['cotizaciones'][0]['documento_url'])
            self.assertEqual(r.status_code,404)

    def test_r01_rechazo_formal_daf_con_notificacion_sin_perder_documentos(self):
        for modulo in ('soporte','mantenimiento'):
            obj=self.objeto(modulo)
            obj.estado_compra_componente='VIABLE';obj.save()
            origen={'ticket_soporte':obj} if modulo=='soporte' else {'requerimiento_mantenimiento':obj}
            compra=SolicitudCompra.objects.create(codigo='CMP-R01-'+modulo,titulo='Exceso',solicitante=self.personas['SOLICITANTE'],area=self.area,monto_estimado=Decimal('1001'),via_adquisicion='CAJA_CHICA',proforma=self.archivo(),**origen)
            nombre=compra.proforma.name
            self.client.force_authenticate(self.personas['DAF'])
            r=self.client.post(f'/api/compras/solicitudes/{compra.pk}/evaluar-daf/',{'califica':True})
            self.assertEqual(r.status_code,400,r.data)
            compra.refresh_from_db();self.assertEqual(compra.estado,'RECHAZADO');self.assertEqual(compra.proforma.name,nombre)
            self.assertTrue(NotificacionSoporte.objects.filter(tipo='RECHAZO',**({'ticket':obj} if modulo=='soporte' else {'mantenimiento':obj})).exists())
            self.assertTrue(Bitacora.objects.filter(accion='R01_COMPRA_RECHAZADA').exists())

    @override_settings(SIA_REQUIERE_APROBACION_DIRECTOR=True)
    def test_r02_no_eludir_aprobacion_por_api(self):
        compra=SolicitudCompra.objects.create(codigo='CMP-R02',titulo='Faltan cotizaciones',solicitante=self.personas['SOLICITANTE'],area=self.area,monto_estimado=700,via_adquisicion='CAJA_CHICA',estado='VERIFICADO_PENDIENTE_AUTORIZACION')
        self.client.force_authenticate(self.personas['DIRECTOR'])
        r=self.client.post(f'/api/compras/solicitudes/{compra.pk}/visto-bueno-director/')
        self.assertEqual(r.status_code,400,r.data)
        compra.refresh_from_db();self.assertEqual(compra.estado,'VERIFICADO_PENDIENTE_AUTORIZACION')

    def test_r03_api_creacion_edicion_y_clasificacion(self):
        for modulo in ('soporte','mantenimiento'):
            soporte=modulo=='soporte'
            base='/api/soporte/tickets/' if soporte else '/api/mantenimiento/requerimientos/'
            clave='ticket' if soporte else 'requerimiento'
            campo='prioridad' if soporte else 'prioridad_jefatura'
            self.client.force_authenticate(self.personas['SOLICITANTE'])
            r=self.client.post(base,{'titulo':'Falla de RED','descripcion':'Sin servicio','ubicacion':'Laboratorio','equipo_afectado':'Router','evidencia':'Fotografía verificada','prioridad':'BAJA','prioridad_jefatura':'BAJA'},format='json')
            self.assertEqual(r.status_code,201,r.data)
            self.assertEqual(r.data[clave][campo],'ALTA')
            pk=r.data[clave]['id']
            # Jefatura conserva la revisión antes de designar personal.
            self.client.force_authenticate(self.personas['JEFE_UTIC' if soporte else 'SERVICIOS_GENERALES'])
            self.assertEqual(self.client.post(f'{base}{pk}/validar-ticket/',{'es_valido':True},format='json').status_code,200)
            r=self.client.post(f'{base}{pk}/clasificar-prioridad/',{'prioridad':'BAJA','criterio_tecnico':'Validación técnica','criterio_prioridad':'Validación técnica'},format='json')
            self.assertEqual(r.status_code,200,r.data)
            self.assertEqual(r.data[clave][campo],'ALTA')
            self.assertEqual(r.data[clave]['sla_horas'],4)
            obj=self.objeto(modulo)
            obj.descripcion='Sin conectividad de internet';setattr(obj,campo,'BAJA');obj.save()
            obj.refresh_from_db();self.assertEqual(getattr(obj,campo),'ALTA')

    def test_solicitante_consulta_mantenimiento_y_configuracion_restringida(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/auditoria/limite-caja-chica/').status_code,401)
        self.client.force_authenticate(self.personas['SOLICITANTE'])
        self.objeto('mantenimiento')
        r=self.client.get('/api/mantenimiento/requerimientos/?propias=1')
        self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(len(r.data),1)

    def test_jefatura_eleva_700_con_tres_cotizaciones(self):
        for modulo in ('soporte','mantenimiento'):
            obj=self.objeto(modulo)
            self.assertEqual(self.enviar(obj,monto='700').status_code,200)
            self.client.force_authenticate(self.personas['JEFE_UTIC' if modulo=='soporte' else 'SERVICIOS_GENERALES'])
            base='/api/soporte/tickets' if modulo=='soporte' else '/api/mantenimiento/requerimientos'
            respuesta=self.client.post(f'{base}/{obj.pk}/validar-viabilidad-compra/',{},format='json')
            self.assertEqual(respuesta.status_code,200,respuesta.data)
            obj.refresh_from_db()
            self.assertEqual(obj.estado_compra_componente,'VIABLE')
            self.assertEqual(obj.cotizaciones_r02.count(),3)

    def test_700_exige_dos_cotizaciones_adicionales(self):
        for modulo in ('soporte','mantenimiento'):
            respuesta=self.enviar(self.objeto(modulo),monto='700',proveedores=('Proveedor único',))
            self.assertEqual(respuesta.status_code,400,respuesta.data)
            self.assertEqual(respuesta.data['regla'],'R02')
            self.assertEqual(int(respuesta.data['cotizaciones_faltantes']),2)

    def test_empresa_se_conserva_y_daf_elige_finanzas(self):
        for modulo in ('soporte','mantenimiento'):
            obj=self.objeto(modulo)
            self.assertEqual(self.enviar(obj,monto='700').status_code,200)
            primera=obj.cotizaciones_r02.first()
            primera.empresa='Empresa de prueba';primera.save(update_fields=['empresa'])
            soporte=modulo=='soporte'
            base='/api/soporte/tickets' if soporte else '/api/mantenimiento/requerimientos'
            self.client.force_authenticate(self.personas['JEFE_UTIC' if soporte else 'SERVICIOS_GENERALES'])
            r=self.client.post(f'{base}/{obj.pk}/evaluar-viabilidad-compra/',{'viable':'true','poa':self.archivo('poa.pdf'),'pedido':self.archivo('pedido.pdf')},format='multipart')
            self.assertEqual(r.status_code,200,r.data)
            compra=SolicitudCompra.objects.get(**{'ticket_soporte' if soporte else 'requerimiento_mantenimiento':obj})
            self.assertTrue(compra.cotizaciones.filter(empresa='Empresa de prueba').exists())
            self.client.force_authenticate(self.personas['DAF'])
            r=self.client.post(f'/api/compras/solicitudes/{compra.pk}/evaluar-daf/',{'califica':True,'via_adquisicion':'FINANZAS'},format='json')
            self.assertEqual(r.status_code,200,r.data)
            compra.refresh_from_db();self.assertEqual(compra.via_adquisicion,'FINANZAS')

    def test_jefatura_clasifica_categoria_y_prioridad(self):
        obj=self.objeto()
        obj.estado=EstadoTicket.objects.get(codigo='EN_ANALISIS');obj.save()
        self.client.force_authenticate(self.personas['JEFE_UTIC'])
        categoria=CategoriaTicket.objects.get(codigo='SERVIDORES')
        r=self.client.post(f'/api/soporte/tickets/{obj.pk}/clasificar-prioridad/',{'categoria':categoria.pk,'prioridad':'BAJA','criterio_tecnico':'Servidor institucional'},format='json')
        self.assertEqual(r.status_code,200,r.data)
        obj.refresh_from_db();self.assertEqual(obj.categoria_id,categoria.pk);self.assertEqual(obj.prioridad,'ALTA')

    def test_r03_categoria_servidores_y_edicion_por_api_en_ambos_modulos(self):
        categoria = CategoriaTicket.objects.get(codigo='SERVIDORES')
        for modulo in ('soporte', 'mantenimiento'):
            obj = self.objeto(modulo)
            base = '/api/soporte/tickets' if modulo == 'soporte' else '/api/mantenimiento/requerimientos'
            campo = 'prioridad' if modulo == 'soporte' else 'prioridad_jefatura'
            self.client.force_authenticate(self.personas['SOLICITANTE'])
            # Preparar estado inicial editable sin saltar permisos reales de edición.
            obj.estado = (EstadoTicket if modulo == 'soporte' else EstadoMantenimiento).objects.get(codigo='NUEVO' if modulo == 'soporte' else 'RECIBIDO')
            obj.save()
            r = self.client.patch(f'{base}/{obj.pk}/', {'categoria': categoria.pk, campo: 'BAJA'}, format='json')
            self.assertEqual(r.status_code, 200, r.data)
            obj.refresh_from_db()
            self.assertEqual(getattr(obj, campo), 'ALTA')
            self.assertIsNone(obj.clasificado_en)
