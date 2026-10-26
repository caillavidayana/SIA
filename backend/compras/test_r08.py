from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from auditoria.models import Bitacora
from .test_caja_chica_r09 import preparar, compra
from .models import CotizacionCompra


@override_settings(SIA_REQUIERE_APROBACION_DIRECTOR=True)
class AprobacionR08Tests(APITestCase):
    @classmethod
    def setUpTestData(cls):preparar(cls)

    def aprobar(self,s,rol='DIRECTOR'):
        s.estado='VERIFICADO_PENDIENTE_AUTORIZACION';s.save(update_fields=['estado'])
        self.client.force_authenticate(self.personas[rol])
        return self.client.post(f'/api/compras/solicitudes/{s.pk}/visto-bueno-director/')

    def test_comun_aunque_tenga_grupo_no_adquiere_permiso(self):
        self.personas['SOLICITANTE'].groups.add(Group.objects.get(name=settings.SIA_GRUPO_APROBADOR))
        self.assertEqual(self.aprobar(compra(self,'R08-COMUN'),'SOLICITANTE').status_code,403)

    def test_grupo_requerido_para_mayores_a_umbral(self):
        self.assertEqual(self.aprobar(compra(self,'R08-SIN-GRUPO','400')).status_code,403)

    def test_no_autoaprobacion_incluso_con_grupo(self):
        u=self.personas['DIRECTOR'];u.groups.add(Group.objects.get(name=settings.SIA_GRUPO_APROBADOR))
        s=compra(self,'R08-PROPIA');s.solicitante=u;s.save()
        self.assertEqual(self.aprobar(s).status_code,403)

    def test_aprobacion_autorizada_de_otro_usuario_y_auditoria(self):
        self.personas['DIRECTOR'].groups.add(Group.objects.get(name=settings.SIA_GRUPO_APROBADOR))
        s=compra(self,'R08-AUTORIZADA','400')
        r=self.aprobar(s);self.assertEqual(r.status_code,200,r.data)
        self.assertTrue(Bitacora.objects.filter(accion='VISTO_BUENO_DIRECTOR',detalle__contains=s.codigo).exists())

    @override_settings(SIA_UMBRAL_APROBACION_ADMINISTRATIVA=Decimal('100'))
    def test_umbral_configurable(self):
        self.assertEqual(self.aprobar(compra(self,'R08-CONFIG','200')).status_code,403)
