from types import SimpleNamespace
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from config.flujo_tickets import validar_transicion


class FlujoR05Tests(SimpleTestCase):
    def ticket(self, estado, solucion='Solución registrada'):
        return SimpleNamespace(estado=SimpleNamespace(codigo=estado),solucion=solucion)

    def test_saltos_y_solucion_obligatoria(self):
        with self.assertRaises(ValidationError):
            validar_transicion(self.ticket('NUEVO'),SimpleNamespace(codigo='CERRADO'))
        with self.assertRaises(ValidationError):
            validar_transicion(self.ticket('EN_EJECUCION',''),SimpleNamespace(codigo='PENDIENTE_CONFORMIDAD'))

    def test_flujo_completo_y_devolucion(self):
        for antes,despues in [('NUEVO','ASIGNADO'),('EN_EJECUCION','PENDIENTE_CONFORMIDAD'),('PENDIENTE_CONFORMIDAD','PENDIENTE_INFORME_FINAL'),('PENDIENTE_INFORME_FINAL','CERRADO'),('PENDIENTE_CONFORMIDAD','EN_EJECUCION')]:
            validar_transicion(self.ticket(antes),SimpleNamespace(codigo=despues))
