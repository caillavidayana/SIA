"""REQUERIMIENTOS 3, 8 y 9: flujo vigente sin aprobación del Director."""
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from .test_caja_chica_r09 import preparar, compra
from .models import MovimientoCajaChica, ReciboTesoreria
from .caja_chica import resumen
from soporte.models import CategoriaTicket, Ticket


class FlujoConfirmadoTests(APITestCase):
    @classmethod
    def setUpTestData(cls): preparar(cls)

    def certificar(self,s,rol='DAF'):
        self.client.force_authenticate(self.personas[rol])
        return self.client.post(f'/api/compras/solicitudes/{s.pk}/certificar-daf/',{'certificacion_presupuestaria':SimpleUploadedFile('certificado.pdf',b'%PDF-1.4\nPrueba')},format='multipart')

    def test_r08_daf_deriva_a_tesoreria_sin_director_mayor_300(self):
        s=compra(self,'R08-SIN-DIRECTOR','400')
        r=self.certificar(s)
        self.assertEqual(r.status_code,200,r.data)
        s.refresh_from_db();self.assertEqual(s.estado,'APROBADO_PARA_DESEMBOLSO')
        self.assertEqual(MovimientoCajaChica.objects.get(solicitud=s).monto,400)
        self.client.force_authenticate(self.personas['DIRECTOR'])
        self.assertEqual(self.client.post(f'/api/compras/solicitudes/{s.pk}/visto-bueno-director/').status_code,409)

    def test_r08_usuario_sin_permiso_no_certifica(self):
        self.assertEqual(self.certificar(compra(self,'R08-NO-PERMISO'),'SOLICITANTE').status_code,403)

    def test_r08_no_autoaprobacion_por_daf(self):
        s=compra(self,'R08-PROPIA-DAF');s.solicitante=self.personas['DAF'];s.save()
        self.assertEqual(self.certificar(s).status_code,403)

    @override_settings(SIA_FONDO_MENSUAL=Decimal('300'))
    def test_r09_certificacion_insuficiente_no_reserva_ni_avanza(self):
        s=compra(self,'R09-NO-FONDO','400')
        r=self.certificar(s);self.assertEqual(r.status_code,400,r.data);self.assertEqual(r.data['regla'],'R09')
        s.refresh_from_db();self.assertEqual(s.estado,'EVALUADO_PENDIENTE_CERTIFICACION')
        self.assertFalse(MovimientoCajaChica.objects.filter(solicitud=s).exists())

    @override_settings(SIA_FONDO_MENSUAL=Decimal('100'))
    def test_r09_tesoreria_rechaza_recibo_sin_fondo(self):
        s=compra(self,'R09-RECIBO-SIN-FONDO','200');s.estado='APROBADO_PARA_DESEMBOLSO';s.save()
        self.client.force_authenticate(self.personas['TESORERIA'])
        r=self.client.post(f'/api/compras/solicitudes/{s.pk}/recibos-tesoreria/',{'responsable_adquisicion':'Persona Compras','tipo_desembolso':'Efectivo','monto_desembolsado':'200'},format='json')
        self.assertEqual(r.status_code,400,r.data);self.assertEqual(r.data['regla'],'R09')
        self.assertFalse(ReciboTesoreria.objects.filter(solicitud=s).exists())
        s.refresh_from_db();self.assertEqual(s.estado,'APROBADO_PARA_DESEMBOLSO');self.assertEqual(resumen()['utilizado'],0)

    def test_r03_solicitante_red_se_refleja_alta_en_ticket(self):
        self.client.force_authenticate(self.personas['SOLICITANTE'])
        categoria=CategoriaTicket.objects.get(codigo='RED')
        r=self.client.post('/api/soporte/tickets/',{'titulo':'Equipo de comunicaciones','descripcion':'No funciona','ubicacion':'Laboratorio','equipo_afectado':'Router','evidencia':'Foto registrada','categoria':categoria.pk},format='json')
        self.assertEqual(r.status_code,201,r.data)
        t=Ticket.objects.get(pk=r.data['ticket']['id']);self.assertEqual(t.prioridad,'ALTA')
        self.assertIsNone(t.clasificado_en)
