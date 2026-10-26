"""R06: integración por propietario, plazo y conservación del expediente."""
from datetime import timedelta
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from usuarios.models import Usuario, Area
from .models import Ticket, EstadoTicket, CategoriaTicket


class ReaperturaR06Tests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario=Usuario.objects.create_user(username='reabrir',email='reabrir@example.test',must_change_password=False)
        cls.otro=Usuario.objects.create_user(username='otro-reabrir',email='otro-reabrir@example.test',must_change_password=False)
        cls.area=Area.objects.create(codigo='R06',nombre='Área reapertura')

    def crear(self,dias=3):
        return Ticket.objects.create(codigo='R06',titulo='Falla recurrente',descripcion='Vuelve a fallar',solucion='Solución del ciclo anterior',
            area=self.area,solicitante=self.usuario,estado=EstadoTicket.objects.get(codigo='CERRADO'),
            categoria=CategoriaTicket.objects.get(codigo='HARDWARE'),cerrado_en=timezone.now()-timedelta(days=dias))

    def reabrir(self,ticket,usuario=None):
        self.client.force_authenticate(usuario or self.usuario)
        return self.client.post(f'/api/soporte/tickets/{ticket.pk}/reabrir-ticket/')

    def test_propietario_reabre_conservando_cierre_y_solucion_anterior(self):
        t=self.crear();cierre=t.cerrado_en
        r=self.reabrir(t);self.assertEqual(r.status_code,200,r.data)
        t.refresh_from_db()
        self.assertEqual(t.estado.codigo,'EN_EJECUCION');self.assertEqual(t.cerrado_en,cierre)
        self.assertEqual(t.historial_reaperturas[0]['textos']['solucion'],'Solución del ciclo anterior')
        self.assertEqual(t.solucion,'');self.assertTrue(t.reabierto_en)

    def test_ocho_dias_no_permite(self):
        t=self.crear(8);self.assertEqual(self.reabrir(t).status_code,400)
        t.refresh_from_db();self.assertEqual(t.estado.codigo,'CERRADO')

    def test_tercero_no_puede_reabrir(self):
        self.assertEqual(self.reabrir(self.crear(),self.otro).status_code,404)

    def test_solo_cerrados_y_fecha_requerida(self):
        t=self.crear();t.cerrado_en=None;t.save()
        self.assertEqual(self.reabrir(t).status_code,400)
        t.estado=EstadoTicket.objects.get(codigo='EN_EJECUCION');t.save()
        self.assertEqual(self.reabrir(t).status_code,400)

    @override_settings(SIA_DIAS_REAPERTURA=2)
    def test_plazo_configurable(self):
        self.assertEqual(self.reabrir(self.crear(3)).status_code,400)
