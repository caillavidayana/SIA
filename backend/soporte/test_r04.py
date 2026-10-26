from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from usuarios.models import Usuario, Area
from .models import Ticket, CategoriaTicket, EstadoTicket
from .serializers import TicketSerializer


class SlaR04Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario=Usuario.objects.create_user(username='sla',email='sla@example.test')
        cls.area=Area.objects.create(codigo='SLA',nombre='Pruebas SLA')

    def ticket(self,prioridad='MEDIA'):
        return Ticket.objects.create(codigo='SLA-'+prioridad,titulo='Equipo dañado',descripcion='Pantalla apagada',
            categoria=CategoriaTicket.objects.get(codigo='HARDWARE'),estado=EstadoTicket.objects.get(codigo='NUEVO'),
            solicitante=self.usuario,area=self.area,prioridad=prioridad)

    def test_alta_media_baja_desde_creacion(self):
        for prioridad,horas in [('ALTA',4),('MEDIA',24),('BAJA',72)]:
            t=self.ticket(prioridad)
            self.assertEqual(t.sla_horas,horas)
            self.assertEqual(t.sla_fecha_limite-t.creado_en,timedelta(hours=horas))

    def test_vencido_no_se_aplica_a_resueltos_o_cerrados(self):
        t=self.ticket();t.sla_fecha_limite=timezone.now()-timedelta(hours=1)
        self.assertEqual(TicketSerializer(t).data['sla_estado'],'VENCIDO')
        for codigo in ['PENDIENTE_CONFORMIDAD','PENDIENTE_INFORME_FINAL','CERRADO']:
            t.estado=EstadoTicket.objects.get(codigo=codigo)
            self.assertNotEqual(TicketSerializer(t).data['sla_estado'],'VENCIDO')

    @override_settings(SIA_SLA_HORAS={'ALTA':6,'MEDIA':30,'BAJA':80,'CRITICA':2})
    def test_horas_configurables(self):
        t=self.ticket('BAJA')
        self.assertEqual(t.sla_fecha_limite-t.creado_en,timedelta(hours=80))
