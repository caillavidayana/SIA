from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from usuarios.models import Area, Rol, Usuario, UsuarioRol


@override_settings(SIA_REQUIERE_APROBACION_DIRECTOR=True)
class FlujoCajaChicaTests(APITestCase):
    def setUp(self):
        # Carga el catálogo real de roles/permisos (Permiso +
        # RolPermiso) para que las pruebas verifiquen la misma
        # autorización que corre en producción (tiene_permiso).
        call_command("cargar_permisos_sigta")

        self.area = Area.objects.create(codigo="TEST", nombre="Área de prueba")
        self.usuarios = {}
        for codigo in ("SOLICITANTE", "DAF", "TESORERIA", "DIRECTOR", "ENCARGADO_COMPRAS_ALMACEN", "ADMIN"):
            rol = Rol.objects.get(codigo=codigo)
            usuario = Usuario.objects.create_user(
                username=codigo.lower(), email=f"{codigo.lower()}@emi.edu.bo",
                nombre_completo=codigo, password="Prueba#2026",
            )
            UsuarioRol.objects.create(usuario=usuario, rol=rol, activo=True)
            self.usuarios[codigo] = usuario

    def archivo(self, nombre="archivo.pdf"):
        return SimpleUploadedFile(nombre, b"contenido de prueba", content_type="application/pdf")

    def autenticar(self, rol):
        self.client.force_authenticate(self.usuarios[rol])

    def test_daf_no_aprueba_incompletos_y_solo_certifica_evaluados(self):
        from compras.models import SolicitudCompra
        self.autenticar("DAF")
        solicitud = SolicitudCompra.objects.create(
            codigo="CMP-TEST-DOCUMENTOS", titulo="Expediente incompleto",
            solicitante=self.usuarios["SOLICITANTE"], area=self.area,
            tipo="BIEN", cantidad=1, origen_modulo="SOPORTE",
            estado="CREADO_PENDIENTE_DAF",
        )
        url = f"/api/compras/solicitudes/{solicitud.pk}"
        self.assertEqual(self.client.post(url + "/evaluar-daf/", {"califica": True}).status_code, 400)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "CREADO_PENDIENTE_DAF")
        self.assertEqual(self.client.get("/api/compras/solicitudes/?bandeja=certificacion").data, [])
        self.assertEqual(self.client.post(url + "/certificar-daf/", {
            "certificacion_presupuestaria": self.archivo(),
        }, format="multipart").status_code, 409)
        for campo in ("informe", "poa", "proforma"):
            setattr(solicitud, campo, self.archivo(campo + ".pdf"))
        solicitud.save()
        self.assertEqual(self.client.post(url + "/evaluar-daf/", {"califica": True}).status_code, 400)
        solicitud.pedido = self.archivo("proveido.pdf")
        solicitud.save()
        self.assertEqual(self.client.get("/api/compras/solicitudes/?bandeja=certificacion").data, [])
        self.assertEqual(self.client.post(url + "/evaluar-daf/", {"califica": True}).status_code, 200)
        bandeja = self.client.get("/api/compras/solicitudes/?bandeja=certificacion").data
        self.assertEqual([r["id"] for r in bandeja], [solicitud.pk])

    def test_monto_rechaza_letras_signos_exponentes_y_decimales_excesivos(self):
        from compras.serializers import MontoEstimadoField
        from rest_framework.exceptions import ValidationError
        campo = MontoEstimadoField(max_digits=12, decimal_places=2, min_value=0)
        for valor in ("abc", "100$", "-1", "+2", "1e3", "NaN", "Infinity", "12.345"):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                campo.run_validation(valor)
        self.assertEqual(str(campo.run_validation("1250.50")), "1250.50")

    def test_bandeja_direccion_excluye_compras_propias(self):
        from compras.models import SolicitudCompra
        director = self.usuarios["DIRECTOR"]
        propia = SolicitudCompra.objects.create(
            codigo="CMP-DIR-PROPIA", titulo="Compra propia del director",
            solicitante=director, area=self.area, tipo="BIEN", cantidad=1,
            estado="VERIFICADO_PENDIENTE_AUTORIZACION",
        )
        ajena = SolicitudCompra.objects.create(
            codigo="CMP-DIR-AJENA", titulo="Compra elevada por otra persona",
            solicitante=self.usuarios["SOLICITANTE"], area=self.area,
            tipo="BIEN", cantidad=1,
            estado="VERIFICADO_PENDIENTE_AUTORIZACION",
        )
        self.autenticar("DIRECTOR")
        respuesta = self.client.get("/api/compras/solicitudes/?bandeja=direccion")
        ids = [item["id"] for item in respuesta.data]
        self.assertIn(ajena.id, ids)
        self.assertNotIn(propia.id, ids)

    def test_ciclo_completo_caja_chica(self):
        self.autenticar("SOLICITANTE")
        respuesta = self.client.post("/api/compras/solicitudes/", {
            "titulo": "Compra de prueba", "descripcion": "Prueba integral",
            "area": self.area.id, "tipo": "BIEN", "cantidad": 1,
            "especificaciones": "Especificaciones", "justificacion": "Necesario",
            "monto_estimado": "100.00", "informe": self.archivo("informe.pdf"),
            "poa": self.archivo("poa.pdf"), "pedido": self.archivo("pedido.pdf"),
            "proforma": self.archivo("proforma.pdf"),
        }, format="multipart")
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        pk = respuesta.data["id"]
        self.assertEqual(respuesta.data["estado"], "CREADO_PENDIENTE_DAF")

        self.autenticar("DAF")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/evaluar-daf/", {"califica": True}, format="json")
        self.assertEqual(r.data["estado"], "EVALUADO_PENDIENTE_CERTIFICACION")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/certificar-daf/", {"certificacion_presupuestaria": self.archivo("certificacion.pdf")}, format="multipart")
        # La certificación de la DAF pasa directo al Director: Tesorería
        # solo desembolsa (no hay verificación previa en el BPMN).
        self.assertEqual(r.data["estado"], "VERIFICADO_PENDIENTE_AUTORIZACION")

        self.autenticar("DIRECTOR")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/visto-bueno-director/", {}, format="json")
        self.assertEqual(r.data["estado"], "APROBADO_PARA_DESEMBOLSO")

        self.autenticar("TESORERIA")
        recibo = self.client.post(f"/api/compras/solicitudes/{pk}/recibos-tesoreria/", {
            "monto_desembolsado": "100.00", "responsable_adquisicion": "Responsable de Almacén", "tipo_desembolso": "Efectivo",
        }, format="json")
        self.assertEqual(recibo.status_code, 201, recibo.data)
        r = self.client.post(f"/api/compras/solicitudes/{pk}/desembolsar/", {
            "monto_desembolsado": "100.00",
            "responsable_adquisicion": "Responsable de Almacén",
            "tipo_desembolso": "Efectivo",
            "recibo_id": recibo.data['id'],
            "recibo_firmado": SimpleUploadedFile('firmado.pdf', b'%PDF-1.4\n', content_type='application/pdf'),
        }, format="multipart")
        self.assertEqual(r.data["estado"], "FONDOS_DESEMBOLSADOS")

        self.autenticar("ENCARGADO_COMPRAS_ALMACEN")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/confirmar-recepcion-fondos/", {'firma': [[[10, 10], [50, 40], [90, 20]]]}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        r = self.client.post(f"/api/compras/solicitudes/{pk}/registrar-compra/", {
            "monto_real": "100.00",
            "proveedor": "Proveedor",
            "componente_verificado": True,
            "comprobante_compra": self.archivo("compra.pdf"),
        }, format="multipart")
        self.assertEqual(r.data["estado"], "COMPRA_REGISTRADA", r.data)
        r = self.client.post(f"/api/compras/solicitudes/{pk}/registrar-ingreso-almacen/", {
            "cantidad_recibida": 1,
            "responsable_recepcion": "Almacén",
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        # Salida de almacén y entrega con acta son dos registros distintos.
        r = self.client.post(f"/api/compras/solicitudes/{pk}/registrar-despacho-almacen/", {
            "cantidad_entregada": 1,
            "entregado_a": "Sección solicitante",
        }, format="json")
        self.assertEqual(r.data["estado"], "COMPRA_REGISTRADA", r.data)

        acta_generada = self.client.post(f"/api/compras/solicitudes/{pk}/actas-almacen/", {"recibe": "Juan Perez", "entrega_confirmada": True}, format="json")
        self.assertEqual(acta_generada.status_code, 201, acta_generada.data)
        r = self.client.post(f"/api/compras/solicitudes/{pk}/entregar-con-acta/", {
            "acta_id": acta_generada.data["id"],
            "acta_conformidad": SimpleUploadedFile("acta-firmada.pdf", b"%PDF-1.4\nDocumento firmado", content_type="application/pdf"),
        }, format="multipart")
        self.assertEqual(r.data["estado"], "COMPRADO_Y_ENTREGADO", r.data)

        # El cierre ocurre en el carril del solicitante: firma el acta y
        # recibe formalmente el bien.
        self.autenticar("SOLICITANTE")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/firmar-acta/", {'firma': [[[10, 10], [50, 40], [90, 20]]]}, format="json")
        self.assertEqual(r.data["estado"], "DESCARGO_PENDIENTE_LIQUIDACION", r.data)

        r = self.client.post(f"/api/compras/solicitudes/{pk}/recibir-solicitud/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["estado"], "CERRADO_ARCHIVADO")
        self.assertTrue(r.data["cerrado_inmutable"])


class SeguridadFlujoComprasTests(APITestCase):
    """'Modo Teniente': intenta romper el flujo de Caja Chica
    saltando estados, actuando fuera de rol y alterando el
    monto estimado una vez que el expediente ya está en
    evaluación/aprobación."""

    def setUp(self):
        call_command("cargar_permisos_sigta")

        self.area = Area.objects.create(codigo="TEST2", nombre="Área de prueba 2")
        self.usuarios = {}
        for codigo in ("ADMIN", "SOLICITANTE", "DAF", "TESORERIA", "DIRECTOR", "ENCARGADO_COMPRAS_ALMACEN"):
            rol = Rol.objects.get(codigo=codigo)
            usuario = Usuario.objects.create_user(
                username=f"{codigo.lower()}2", email=f"{codigo.lower()}2@emi.edu.bo",
                nombre_completo=codigo, password="Prueba#2026",
            )
            UsuarioRol.objects.create(usuario=usuario, rol=rol, activo=True)
            self.usuarios[codigo] = usuario

    def archivo(self, nombre="archivo.pdf"):
        return SimpleUploadedFile(nombre, b"contenido de prueba", content_type="application/pdf")

    def autenticar(self, rol):
        self.client.force_authenticate(self.usuarios[rol])

    def crear_solicitud(self):
        self.autenticar("SOLICITANTE")
        r = self.client.post("/api/compras/solicitudes/", {
            "titulo": "Compra de prueba", "descripcion": "Prueba de seguridad",
            "area": self.area.id, "tipo": "BIEN", "cantidad": 1,
            "especificaciones": "Especificaciones", "justificacion": "Necesario",
            "monto_estimado": "100.00", "informe": self.archivo("informe.pdf"),
            "poa": self.archivo("poa.pdf"), "pedido": self.archivo("pedido.pdf"),
            "proforma": self.archivo("proforma.pdf"),
        }, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        return r.data["id"]

    def test_no_se_puede_saltar_directo_a_desembolsar(self):
        pk = self.crear_solicitud()
        self.autenticar("TESORERIA")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/desembolsar/", {
            "monto_desembolsado": "100.00", "responsable_adquisicion": "Almacén",
        }, format="json")
        self.assertEqual(r.status_code, 409, r.data)

    def test_tesoreria_recibe_sin_director_pero_exige_recibo_firmado(self):
        pk = self.crear_solicitud()
        self.autenticar("DAF")
        self.client.post(f"/api/compras/solicitudes/{pk}/evaluar-daf/", {"califica": True}, format="json")
        self.client.post(f"/api/compras/solicitudes/{pk}/certificar-daf/", {"certificacion_presupuestaria": self.archivo("cert.pdf")}, format="multipart")

        self.autenticar("TESORERIA")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/desembolsar/", {
            "monto_desembolsado": "100.00", "responsable_adquisicion": "Almacén",
        }, format="json")
        self.assertEqual(r.status_code, 400, r.data)
        self.assertIn("recibo", str(r.data).lower())

        r = self.client.get(f"/api/compras/solicitudes/{pk}/")
        self.assertEqual(r.data["estado"], "APROBADO_PARA_DESEMBOLSO")

    def test_tesoreria_no_puede_ejecutar_accion_de_daf(self):
        pk = self.crear_solicitud()
        self.autenticar("TESORERIA")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/evaluar-daf/", {"califica": True}, format="json")
        self.assertEqual(r.status_code, 403, r.data)

    def test_encargado_almacen_no_puede_dar_visto_bueno_director(self):
        pk = self.crear_solicitud()
        self.autenticar("ENCARGADO_COMPRAS_ALMACEN")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/visto-bueno-director/", {}, format="json")
        self.assertEqual(r.status_code, 403, r.data)

    def test_solicitante_no_puede_ver_ni_editar_solicitud_ajena(self):
        pk = self.crear_solicitud()

        otro_solicitante = Usuario.objects.create_user(
            username="intruso", email="intruso@emi.edu.bo",
            nombre_completo="Intruso", password="Prueba#2026",
        )
        UsuarioRol.objects.create(usuario=otro_solicitante, rol=Rol.objects.get(codigo="SOLICITANTE"), activo=True)
        self.client.force_authenticate(otro_solicitante)

        # No aparece en su bandeja (get_queryset filtra por dueño).
        r = self.client.get("/api/compras/solicitudes/")
        self.assertNotIn(pk, [item["id"] for item in r.data])

        # Tampoco puede modificarla directamente por id.
        r = self.client.patch(f"/api/compras/solicitudes/{pk}/", {"titulo": "Hackeado"}, format="json")
        self.assertIn(r.status_code, (403, 404))

    def test_nadie_puede_modificar_monto_estimado_en_evaluacion(self):
        pk = self.crear_solicitud()

        self.autenticar("DAF")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/evaluar-daf/", {"califica": True}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        # Ni siquiera ADMIN puede reescribir el monto una vez
        # que el expediente entró al flujo de aprobación.
        self.autenticar("ADMIN")
        r = self.client.patch(f"/api/compras/solicitudes/{pk}/", {"monto_estimado": "999999.00"}, format="json")
        self.assertEqual(r.status_code, 403, r.data)

        r = self.client.get(f"/api/compras/solicitudes/{pk}/")
        self.assertEqual(r.data["monto_estimado"], "100.00")

    def test_expediente_cerrado_es_inmutable_incluso_para_admin(self):
        # Ciclo feliz completo hasta el cierre.
        pk = self.crear_solicitud()
        self.autenticar("DAF")
        self.client.post(f"/api/compras/solicitudes/{pk}/evaluar-daf/", {"califica": True}, format="json")
        self.client.post(f"/api/compras/solicitudes/{pk}/certificar-daf/", {"certificacion_presupuestaria": self.archivo("cert.pdf")}, format="multipart")
        self.autenticar("DIRECTOR")
        self.client.post(f"/api/compras/solicitudes/{pk}/visto-bueno-director/", {}, format="json")
        self.autenticar("TESORERIA")
        recibo = self.client.post(f"/api/compras/solicitudes/{pk}/recibos-tesoreria/", {
            "monto_desembolsado": "100.00", "responsable_adquisicion": "Responsable de Almacén", "tipo_desembolso": "Efectivo",
        }, format="json")
        self.assertEqual(recibo.status_code, 201, recibo.data)
        self.client.post(f"/api/compras/solicitudes/{pk}/desembolsar/", {
            "monto_desembolsado": "100.00",
            "responsable_adquisicion": "Responsable de Almacén",
            "tipo_desembolso": "Efectivo",
            "recibo_id": recibo.data['id'],
            "recibo_firmado": SimpleUploadedFile('firmado.pdf', b'%PDF-1.4\n', content_type='application/pdf'),
        }, format="multipart")
        self.autenticar("ENCARGADO_COMPRAS_ALMACEN")
        self.client.post(f"/api/compras/solicitudes/{pk}/confirmar-recepcion-fondos/", {'firma': [[[10, 10], [50, 40], [90, 20]]]}, format="json")
        self.client.post(f"/api/compras/solicitudes/{pk}/registrar-compra/", {
            "monto_real": "100.00",
            "proveedor": "Proveedor",
            "componente_verificado": True,
            "comprobante_compra": self.archivo("compra.pdf"),
        }, format="multipart")
        self.client.post(f"/api/compras/solicitudes/{pk}/registrar-ingreso-almacen/", {
            "cantidad_recibida": 1,
            "responsable_recepcion": "Almacén",
        }, format="json")
        self.client.post(f"/api/compras/solicitudes/{pk}/registrar-despacho-almacen/", {
            "cantidad_entregada": 1,
            "entregado_a": "Sección solicitante",
        }, format="json")
        acta_generada = self.client.post(f"/api/compras/solicitudes/{pk}/actas-almacen/", {"recibe": "Juan Perez", "entrega_confirmada": True}, format="json")
        self.assertEqual(acta_generada.status_code, 201, acta_generada.data)
        self.client.post(f"/api/compras/solicitudes/{pk}/entregar-con-acta/", {
            "acta_id": acta_generada.data["id"],
            "acta_conformidad": SimpleUploadedFile("acta-firmada.pdf", b"%PDF-1.4\nDocumento firmado", content_type="application/pdf"),
        }, format="multipart")

        # Solo la sección solicitante cierra el proceso.
        self.autenticar("TESORERIA")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/firmar-acta/", {'firma': [[[10, 10], [50, 40], [90, 20]]]}, format="json")
        self.assertEqual(r.status_code, 403, r.data)

        self.autenticar("SOLICITANTE")
        self.client.post(f"/api/compras/solicitudes/{pk}/firmar-acta/", {'firma': [[[10, 10], [50, 40], [90, 20]]]}, format="json")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/recibir-solicitud/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        # Ya cerrado: ninguna transición vuelve a aplicarse,
        # ni con el rol correcto.
        self.autenticar("TESORERIA")
        r = self.client.post(f"/api/compras/solicitudes/{pk}/desembolsar/", {"monto_desembolsado": "1.00", "responsable_adquisicion": "X"}, format="json")
        self.assertEqual(r.status_code, 409, r.data)
