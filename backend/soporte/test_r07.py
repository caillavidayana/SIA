from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from io import StringIO
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from django.db import close_old_connections
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from usuarios.models import Usuario, Rol, UsuarioRol, Area
from .models import Ticket, EstadoTicket, CategoriaTicket


def preparar(clase):
    call_command('cargar_permisos_sigta',stdout=StringIO())
    for codigo in ('NUEVO','EN_ANALISIS','ASIGNADO','EN_DIAGNOSTICO','EN_EJECUCION','PENDIENTE_CONFORMIDAD','CERRADO'):
        EstadoTicket.objects.get_or_create(codigo=codigo,defaults={'nombre':codigo,'activo':True})
    CategoriaTicket.objects.get_or_create(codigo='HARDWARE',defaults={'nombre':'Hardware','activo':True})
    clase.area=Area.objects.create(codigo='CARGA',nombre='Carga técnica')
    clase.usuarios={}
    for codigo in ('SOLICITANTE','JEFE_UTIC','ESPECIALISTA'):
        u=Usuario.objects.create_user(username=codigo,email=codigo+'@r07.test',must_change_password=False)
        UsuarioRol.objects.create(usuario=u,rol=Rol.objects.get(codigo=codigo));clase.usuarios[codigo]=u


def ticket(clase,codigo,asignado=False):
    return Ticket.objects.create(codigo=codigo,titulo='Equipo sin funcionar',descripcion='Falla técnica',area=clase.area,
        solicitante=clase.usuarios['SOLICITANTE'],tecnico_asignado=clase.usuarios['ESPECIALISTA'] if asignado else None,
        estado=EstadoTicket.objects.get(codigo='EN_EJECUCION' if asignado else 'EN_ANALISIS'),
        categoria=CategoriaTicket.objects.get(codigo='HARDWARE'),clasificado_en=timezone.now())


class CargaR07Tests(APITestCase):
    @classmethod
    def setUpTestData(cls):preparar(cls)

    def asignar(self,t):
        self.client.force_authenticate(self.usuarios['JEFE_UTIC'])
        return self.client.post(f'/api/soporte/tickets/{t.pk}/designar-revision/',{'tecnico_id':self.usuarios['ESPECIALISTA'].pk,'especialistas_apoyo':[]},format='json')

    def test_sexto_se_bloquea_y_cerrar_libera_cupo(self):
        existentes=[ticket(self,'ACT-'+str(i),True) for i in range(5)]
        nuevo=ticket(self,'SEXTO');r=self.asignar(nuevo)
        self.assertEqual(r.status_code,400,r.data)
        existentes[0].estado=EstadoTicket.objects.get(codigo='CERRADO');existentes[0].save()
        self.assertEqual(self.asignar(nuevo).status_code,200)

    @override_settings(SIA_MAX_TICKETS_TECNICO=8)
    def test_limite_configurable_ocho(self):
        for i in range(8):self.assertEqual(self.asignar(ticket(self,'OCHO-'+str(i))).status_code,200)
        self.assertEqual(self.asignar(ticket(self,'NOVENO')).status_code,400)

    @override_settings(SIA_MAX_TICKETS_TECNICO=1)
    def test_resuelto_no_ocupa_cupo_activo(self):
        anterior=ticket(self,'RESUELTO',True);anterior.estado=EstadoTicket.objects.get(codigo='PENDIENTE_CONFORMIDAD');anterior.save()
        self.assertEqual(self.asignar(ticket(self,'ACTIVO')).status_code,200)


class CargaConcurrentePostgresTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_dos_asignaciones_simultaneas_no_producen_sexto(self):
        preparar(self)
        for i in range(4):ticket(self,'PREVIO-'+str(i),True)
        ids=[ticket(self,'PARALELO-'+str(i)).pk for i in range(2)]
        barrera=Barrier(2);actor=self.usuarios['JEFE_UTIC'].pk;tecnico=self.usuarios['ESPECIALISTA'].pk
        def asignar(pk):
            close_old_connections()
            try:
                c=APIClient();c.force_authenticate(Usuario.objects.get(pk=actor));barrera.wait(timeout=15)
                return c.post(f'/api/soporte/tickets/{pk}/designar-revision/',{'tecnico_id':tecnico,'especialistas_apoyo':[]},format='json').status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as p:resultados=list(p.map(asignar,ids))
        self.assertEqual(sorted(resultados),[200,400])
        self.assertEqual(Ticket.objects.filter(tecnico_asignado_id=tecnico).count(),5)
