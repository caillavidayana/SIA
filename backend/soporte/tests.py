from config.testing import cerrar_respuesta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.core.management import call_command
from rest_framework.test import APITestCase

from usuarios.models import Area, Rol, Usuario, UsuarioRol

from compras.models import SolicitudCompra

from .models import CategoriaTicket, EstadoTicket, Ticket


class FlujoSoporteCompraTests(APITestCase):
    """Cubre el disparo real del subproceso de Compra Caja Chica
    desde un ticket de Soporte Técnico ("¿Requiere compra?"), con
    la cadena Especialista solicita -> Jefe UTIC evalúa viabilidad
    que exige el BPMN oficial."""

    def setUp(self):
        call_command("cargar_permisos_sigta")

        # Los estados (NUEVO, EN_ANALISIS, ...) y categorías ya se
        # siembran con soporte.0006_seed_estados_categorias /
        # 0008_seed_estado_cerrado_sin_compra.
        self.categoria = CategoriaTicket.objects.get(codigo="HARDWARE")
        self.area = Area.objects.create(codigo="TEST", nombre="Área de prueba")

        self.usuarios = {}
        for codigo in ("SOLICITANTE", "JEFE_UTIC", "ESPECIALISTA"):
            rol = Rol.objects.get(codigo=codigo)
            usuario = Usuario.objects.create_user(
                username=codigo.lower(),
                email=f"{codigo.lower()}@emi.edu.bo",
                nombre_completo=codigo,
                password="Prueba#2026",
            )
            UsuarioRol.objects.create(usuario=usuario, rol=rol, activo=True)
            self.usuarios[codigo] = usuario

    def autenticar(self, codigo):
        self.client.force_authenticate(self.usuarios[codigo])

    def crear_ticket_en_ejecucion(self, titulo, equipo):
        """Lleva un ticket hasta EN_EJECUCION (registrado, validado,
        clasificado, asignado y diagnosticado) para poder probar el
        subflujo de compra de componente."""

        self.autenticar("SOLICITANTE")
        r = self.client.post("/api/soporte/tickets/", {
            "titulo": titulo,
            "descripcion": f"{titulo} - descripción de prueba.",
            "area": self.area.id,
            "ubicacion": "Laboratorio 2",
            "equipo_afectado": equipo,
            "categoria": self.categoria.id,
            "evidencia_archivo": SimpleUploadedFile(
                "evidencia.jpg", b"contenido-de-prueba", content_type="image/jpeg"
            ),
        }, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        pk = r.data["ticket"]["id"] if "ticket" in r.data else r.data["id"]

        self.autenticar("JEFE_UTIC")
        r = self.client.post(f"/api/soporte/tickets/{pk}/validar-ticket/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        r = self.client.post(f"/api/soporte/tickets/{pk}/clasificar-prioridad/", {
            "prioridad": "ALTA",
            "criterio_tecnico": "Afecta clases del laboratorio.",
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        r = self.client.post(f"/api/soporte/tickets/{pk}/designar-revision/", {
            "tecnico_id": self.usuarios["ESPECIALISTA"].id,
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/iniciar-atencion/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        r = self.client.post(f"/api/soporte/tickets/{pk}/registrar-diagnostico/", {
            "diagnostico": "Componente dañado, requiere reemplazo.",
            "plan_solucion": "Solicitar el componente y reemplazarlo.",
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)

        return pk

    def test_especialista_solicita_jefe_aprueba_genera_expediente_vinculado(self):
        pk = self.crear_ticket_en_ejecucion("Monitor no enciende", "Monitor Dell")

        # El Especialista asignado solicita el componente con su
        # cotización — todavía no existe ningún expediente de compra.
        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "informe_compra": SimpleUploadedFile("informe.pdf", b"informe con cuadros"),
            "proveedor_cotizacion": "Proveedor de prueba",
            "cotizacion_archivo": SimpleUploadedFile("cotizacion.pdf", b"cotizacion"),
            "componente_requerido": "Fuente de monitor",
            "especificaciones_tecnicas": "Fuente 19V 2A",
            "cantidad_componente": 2,
            "justificacion_compra": "Es indispensable para recuperar el monitor.",
            "costo_estimado": "250.00",
        }, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["ticket"]["estado_codigo"], "EN_EJECUCION")
        self.assertFalse(r.data["ticket"]["codigo_compra_vinculada"])

        # Mientras la viabilidad no se evalúe, no se puede reparar.
        r = self.client.post(f"/api/soporte/tickets/{pk}/registrar-intervencion/", {
            "solucion": "Se reemplazó la fuente.",
        }, format="json")
        self.assertEqual(r.status_code, 409, r.data)

        # Jefe de UTIC evalúa la viabilidad: al aprobarla, recién
        # ahí se genera el expediente real y vinculado en Compras.
        self.autenticar("JEFE_UTIC")
        informe_generado = Ticket.objects.get(pk=pk).informe_compra.name
        r = self.client.get(f"/api/soporte/tickets/{pk}/informe-requerimiento-pdf/")
        self.assertEqual(r.status_code, 200)
        try:
            self.assertTrue(b"".join(r.streaming_content).startswith(b"%PDF-"))
        finally:
            cerrar_respuesta(r)
        self.assertEqual(Ticket.objects.get(pk=pk).informe_compra.name, informe_generado)
        r = self.client.post(f"/api/soporte/tickets/{pk}/validar-viabilidad-compra/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        ticket = Ticket.objects.get(pk=pk)
        self.assertEqual(ticket.estado_compra_componente, "VIABLE")
        self.assertEqual(ticket.informe_compra.name, informe_generado)
        self.assertFalse(ticket.codigo_compra_vinculada)
        self.assertFalse(SolicitudCompra.objects.filter(ticket_soporte_id=pk).exists())
        r = self.client.post(f"/api/soporte/tickets/{pk}/evaluar-viabilidad-compra/", {"viable": True}, format="json")
        self.assertEqual(r.status_code, 400, r.data)
        r = self.client.post(f"/api/soporte/tickets/{pk}/evaluar-viabilidad-compra/", {
            "poa": SimpleUploadedFile("poa.pdf", b"poa"),
            "pedido": SimpleUploadedFile("proveido.pdf", b"proveido"),
            "viable": True,
        }, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)

        codigo_compra = r.data["ticket"]["codigo_compra_vinculada"]
        self.assertTrue(codigo_compra)

        solicitud = SolicitudCompra.objects.get(codigo=codigo_compra)
        self.assertEqual(solicitud.origen_modulo, "SOPORTE")
        self.assertEqual(solicitud.ticket_soporte_id, pk)
        self.assertEqual(solicitud.solicitante_id, self.usuarios["ESPECIALISTA"].id)
        self.assertEqual(solicitud.cantidad, 2)
        self.assertTrue(solicitud.informe)
        self.assertTrue(solicitud.proforma)
        self.assertTrue(solicitud.poa)
        self.assertTrue(solicitud.pedido)
        with solicitud.informe.open("rb") as archivo:
            self.assertEqual(archivo.read(5), b"%PDF-")
        with solicitud.proforma.open("rb") as archivo:
            self.assertEqual(archivo.read(), b"cotizacion")

        # No se puede duplicar la solicitud de compra para el
        # mismo ticket.
        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "informe_compra": SimpleUploadedFile("informe.pdf", b"informe con cuadros"),
            "proveedor_cotizacion": "Proveedor de prueba",
            "cotizacion_archivo": SimpleUploadedFile("cotizacion.pdf", b"cotizacion"),
            "componente_requerido": "Otro componente",
        }, format="multipart")
        self.assertEqual(r.status_code, 409, r.data)

        # Aprobar la viabilidad no basta: el flujo técnico sigue en pausa
        # hasta que Almacén entregue físicamente el componente.
        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/registrar-intervencion/", {
            "solucion": "Se reemplazó la fuente.",
        }, format="json")
        self.assertEqual(r.status_code, 409, r.data)

        # Almacén despacha el componente: eso reanuda la atención técnica.
        ticket = Ticket.objects.get(pk=pk)
        ticket.estado_compra_componente = "ENTREGADA"
        ticket.componente_entregado_en = timezone.now()
        ticket.save(update_fields=["estado_compra_componente", "componente_entregado_en"])

        r = self.client.post(f"/api/soporte/tickets/{pk}/registrar-intervencion/", {
            "solucion": "Se reemplazó la fuente.",
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_jefe_utic_marca_no_viable_cierra_ticket_sin_compra(self):
        pk = self.crear_ticket_en_ejecucion("Necesita GPU de alta gama", "PC laboratorio")

        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "informe_compra": SimpleUploadedFile("informe.pdf", b"informe con cuadros"),
            "proveedor_cotizacion": "Proveedor de prueba",
            "cotizacion_archivo": SimpleUploadedFile("cotizacion.pdf", b"cotizacion"),
            "componente_requerido": "GPU de alta gama",
            "especificaciones_tecnicas": "GPU compatible con el equipo",
            "justificacion_compra": "El equipo no puede operar sin reemplazo.",
            "costo_estimado": "900.00",
            "via_compra": "FINANZAS",
            "cotizaciones": [SimpleUploadedFile("cotizacion2.pdf", b"dos"), SimpleUploadedFile("cotizacion3.pdf", b"tres")],
            "cotizaciones_metadata": '[{"proveedor":"Proveedor dos"},{"proveedor":"Proveedor tres"},{"proveedor":"Proveedor de prueba"}]',
        }, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)

        self.autenticar("JEFE_UTIC")
        r = self.client.post(f"/api/soporte/tickets/{pk}/evaluar-viabilidad-compra/", {
            "viable": False,
            "motivo_no_viable": "Excede el presupuesto de caja chica.",
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["ticket"]["estado_codigo"], "CERRADO_SIN_COMPRA")
        self.assertFalse(r.data["ticket"]["activo"])
        self.assertFalse(SolicitudCompra.objects.filter(ticket_soporte_id=pk).exists())

    def test_solicitante_no_puede_solicitar_componente(self):
        pk = self.crear_ticket_en_ejecucion("Teclado dañado", "Teclado Logitech")

        self.autenticar("SOLICITANTE")
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "informe_compra": SimpleUploadedFile("informe.pdf", b"informe con cuadros"),
            "proveedor_cotizacion": "Proveedor de prueba",
            "cotizacion_archivo": SimpleUploadedFile("cotizacion.pdf", b"cotizacion"),
            "componente_requerido": "Teclado nuevo",
        }, format="multipart")
        self.assertEqual(r.status_code, 403, r.data)

    def test_especialista_no_puede_evaluar_viabilidad(self):
        pk = self.crear_ticket_en_ejecucion("Mouse dañado", "Mouse Logitech")

        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "informe_compra": SimpleUploadedFile("informe.pdf", b"informe con cuadros"),
            "proveedor_cotizacion": "Proveedor de prueba",
            "cotizacion_archivo": SimpleUploadedFile("cotizacion.pdf", b"cotizacion"),
            "componente_requerido": "Mouse nuevo",
            "especificaciones_tecnicas": "Mouse USB",
            "justificacion_compra": "El periférico actual no funciona.",
            "costo_estimado": "100.00",
        }, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)

        r = self.client.post(f"/api/soporte/tickets/{pk}/evaluar-viabilidad-compra/", {
            "poa": SimpleUploadedFile("poa.pdf", b"poa"),
            "pedido": SimpleUploadedFile("proveido.pdf", b"proveido"),
            "viable": True,
        }, format="multipart")
        self.assertEqual(r.status_code, 403, r.data)

    def test_borrador_requerimiento_permanece_visible_y_editable(self):
        pk = self.crear_ticket_en_ejecucion("Fuente pendiente", "PC")
        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/guardar-borrador-requerimiento/", {
            "componente_requerido": "Fuente ATX",
            "cantidad_componente": 1,
        }, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["ticket"]["estado_compra_componente"], "BORRADOR")
        self.assertEqual(r.data["ticket"]["estado_codigo"], "EN_EJECUCION")

    def test_genera_informe_de_requerimiento_y_exige_cotizacion(self):
        pk = self.crear_ticket_en_ejecucion("Falta documentación", "PC")
        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "componente_requerido": "Fuente", "especificaciones_tecnicas": "ATX",
            "justificacion_compra": "Fuente quemada", "costo_estimado": "100.00",
        }, format="json")
        self.assertEqual(r.status_code, 400, r.data)
        self.assertFalse(Ticket.objects.get(pk=pk).estado_compra_componente)
        self.assertFalse(SolicitudCompra.objects.filter(ticket_soporte_id=pk).exists())
        r = self.client.post(f"/api/soporte/tickets/{pk}/solicitar-requerimiento-componente/", {
            "componente_requerido": "Fuente", "especificaciones_tecnicas": "ATX",
            "justificacion_compra": "Fuente quemada", "costo_estimado": "100.00",
            "proveedor_cotizacion": "Proveedor de prueba",
            "cotizacion_archivo": SimpleUploadedFile("cotizacion.jpg", b"imagen", content_type="image/jpeg"),
        }, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        ticket = Ticket.objects.get(pk=pk)
        self.assertTrue(ticket.informe_compra)
        self.assertTrue(ticket.informe_compra.name.endswith(".pdf"))

    def test_jefatura_completa_expediente_antiguo_y_daf_debe_reevaluar(self):
        pk = self.crear_ticket_en_ejecucion("Expediente antiguo", "PC")
        ticket = Ticket.objects.get(pk=pk)
        compra = SolicitudCompra.objects.create(
            codigo="CMP-LEGADO", titulo="Sin documentos", solicitante=ticket.solicitante,
            area=ticket.area, tipo="COMPONENTE", cantidad=1, ticket_soporte=ticket,
            origen_modulo="SOPORTE", estado="EVALUADO_PENDIENTE_CERTIFICACION",
        )
        url = f"/api/soporte/tickets/{pk}/completar-expediente/"
        self.autenticar("ESPECIALISTA")
        self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.autenticar("JEFE_UTIC")
        self.assertEqual(self.client.post(url, {}).status_code, 400)
        r = self.client.post(url, {
            campo: SimpleUploadedFile(campo + ".pdf", campo.encode())
            for campo in ("informe", "proforma", "poa", "pedido")
        }, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        compra.refresh_from_db()
        self.assertEqual(compra.estado, "CREADO_PENDIENTE_DAF")
        self.assertEqual(SolicitudCompra.objects.filter(ticket_soporte=ticket).count(), 1)
        self.assertEqual(self.client.post(url, {}).status_code, 409)

    def test_especialista_solo_lista_ordenes_propias(self):
        pk = self.crear_ticket_en_ejecucion("Orden propia", "PC")
        otro = Usuario.objects.create_user(
            username="otro_especialista", email="otro@emi.edu.bo",
            nombre_completo="Otro Especialista", password="Prueba#2026",
        )
        UsuarioRol.objects.create(
            usuario=otro, rol=Rol.objects.get(codigo="ESPECIALISTA"), activo=True,
        )
        self.client.force_authenticate(otro)
        r = self.client.get("/api/soporte/tickets/")
        self.assertEqual(r.status_code, 200, r.data)
        ids = [item["id"] for item in (r.data if isinstance(r.data, list) else r.data["results"])]
        self.assertNotIn(pk, ids)

    def test_conformidad_positiva_espera_informe_final_del_jefe(self):
        pk = self.crear_ticket_en_ejecucion("Equipo reparado", "PC")
        ticket = Ticket.objects.get(pk=pk)
        ticket.diagnostico = "Falla de memoria"
        ticket.solucion = "Memoria reinstalada"
        ticket.resultado_pruebas = "Pruebas satisfactorias"
        ticket.informe_tecnico = "Informe y cuadros registrados por el técnico."
        ticket.save(update_fields=[
            "estado", "diagnostico", "solucion", "resultado_pruebas", "informe_tecnico",
        ])

        firma_tecnico = [[[10, 20], [120, 60], [200, 30]]]
        url_pruebas = f"/api/soporte/tickets/{pk}/pruebas-tecnicas/"
        cuerpo = {"resultado_pruebas": ticket.resultado_pruebas, "informe_tecnico": ticket.informe_tecnico}
        self.assertEqual(self.client.post(url_pruebas, cuerpo, format="json").status_code, 400)
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado.codigo, "EN_EJECUCION")
        r = self.client.post(url_pruebas, {**cuerpo, "firma": firma_tecnico}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        ticket.refresh_from_db()
        with ticket.informe_tecnico_pdf.open('rb') as archivo:
            self.assertIn(b'1.3 w', archivo.read())

        self.autenticar("SOLICITANTE")
        r = self.client.post(
            f"/api/soporte/tickets/{pk}/informar-conformidad/",
            {"conformidad": True, "observaciones": "El equipo funciona correctamente."},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["ticket"]["estado_codigo"], "PENDIENTE_INFORME_FINAL")
        self.assertIsNone(Ticket.objects.get(pk=pk).cerrado_en)
        from usuarios.models import DocumentoProceso
        self.assertEqual(DocumentoProceso.objects.get(soporte=ticket, tipo='Conformidad del solicitante').firma, [])

        self.autenticar("JEFE_UTIC")
        r = self.client.post(
            f"/api/soporte/tickets/{pk}/elaborar-informe-final/",
            {"informe_final": "Atención verificada y expediente validado.", "firma": [[[20, 30], [150, 80]]]},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado.codigo, "CERRADO")
        self.assertIsNotNone(ticket.cerrado_en)
        self.assertTrue(ticket.informe_final_pdf)
        with ticket.informe_final_pdf.open('rb') as archivo:
            pdf = archivo.read()
        self.assertIn(b'ESPECIALISTA', pdf)
        self.assertIn(b'JEFE_UTIC', pdf)
        self.assertEqual(pdf.count(b'1.3 w'), 2)

        self.autenticar("SOLICITANTE")
        r = self.client.post(
            f"/api/soporte/tickets/{pk}/elaborar-informe-jefe-carrera/",
            {"informe_jefe_carrera": "Trabajo revisado y conforme para conocimiento de Dirección."},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        ticket.refresh_from_db()
        self.assertTrue(ticket.informe_jefe_carrera_pdf)
        self.assertIsNotNone(ticket.informe_jefe_carrera_en)

    def test_no_conformidad_exige_motivo_y_conserva_historial(self):
        pk = self.crear_ticket_en_ejecucion("Falla persistente", "Impresora")
        ticket = Ticket.objects.get(pk=pk)
        ticket.estado = EstadoTicket.objects.get(codigo="PENDIENTE_CONFORMIDAD")
        ticket.diagnostico = "Atasco del alimentador"
        ticket.solucion = "Limpieza de rodillos"
        ticket.resultado_pruebas = "Impresión de prueba"
        ticket.save(update_fields=["estado", "diagnostico", "solucion", "resultado_pruebas"])

        self.autenticar("SOLICITANTE")
        r = self.client.post(
            f"/api/soporte/tickets/{pk}/informar-conformidad/",
            {"conformidad": False, "observaciones": ""},
            format="json",
        )
        self.assertEqual(r.status_code, 400, r.data)

        r = self.client.post(
            f"/api/soporte/tickets/{pk}/informar-conformidad/",
            {"conformidad": False, "observaciones": "El papel vuelve a atascarse."},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado.codigo, "EN_EJECUCION")
        self.assertEqual(ticket.rework_count, 1)
        self.assertEqual(ticket.diagnostico, "Atasco del alimentador")
        self.assertEqual(ticket.solucion, "Limpieza de rodillos")
        self.assertEqual(ticket.resultado_pruebas, "Impresión de prueba")

    def test_recibir_orden_es_idempotente(self):
        pk = self.crear_ticket_en_ejecucion("Recepción idempotente", "PC")
        ticket = Ticket.objects.get(pk=pk)
        ticket.estado = EstadoTicket.objects.get(codigo="EN_DIAGNOSTICO")
        ticket.diagnostico = ""
        ticket.save(update_fields=["estado", "diagnostico"])

        self.autenticar("ESPECIALISTA")
        r = self.client.post(f"/api/soporte/tickets/{pk}/iniciar-atencion/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["ticket"]["estado_codigo"], "EN_DIAGNOSTICO")

    def test_diagnostico_puede_recuperar_recepcion_interrumpida(self):
        pk = self.crear_ticket_en_ejecucion("Recepción interrumpida", "Proyector")
        ticket = Ticket.objects.get(pk=pk)
        ticket.estado = EstadoTicket.objects.get(codigo="ASIGNADO")
        ticket.diagnostico = ""
        ticket.inicio_atencion_en = None
        ticket.save(update_fields=["estado", "diagnostico", "inicio_atencion_en"])

        self.autenticar("ESPECIALISTA")
        r = self.client.post(
            f"/api/soporte/tickets/{pk}/registrar-diagnostico/",
            {
                "diagnostico": "Fuente de alimentación defectuosa.",
                "plan_solucion": "Reemplazar la fuente.",
                "requiere_compra": True,
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado.codigo, "EN_EJECUCION")
        self.assertIsNotNone(ticket.inicio_atencion_en)



# ==========================================================
# INICIO PRUEBAS R04 Y R05
# ==========================================================

from datetime import timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.utils import timezone

from .views import calcular_sla_cumplido, validar_estado_ticket


class ReglasSLAyEstadosTests(SimpleTestCase):
    """
    R04: Verifica el cumplimiento de los plazos SLA.
    R05: Verifica la función de validación de estados.
    """

    # ------------------------------------------------------
    # R04 - SLA
    # ------------------------------------------------------

    def test_r04_sla_cumplido_antes_del_limite(self):
        limite = timezone.now()

        ticket = SimpleNamespace(
            sla_fecha_limite=limite
        )

        resultado = calcular_sla_cumplido(
            ticket,
            limite - timedelta(minutes=30)
        )

        self.assertTrue(resultado)

    def test_r04_sla_cumplido_exactamente_en_limite(self):
        limite = timezone.now()

        ticket = SimpleNamespace(
            sla_fecha_limite=limite
        )

        resultado = calcular_sla_cumplido(ticket, limite)

        self.assertTrue(resultado)

    def test_r04_sla_incumplido_despues_del_limite(self):
        limite = timezone.now()

        ticket = SimpleNamespace(
            sla_fecha_limite=limite
        )

        resultado = calcular_sla_cumplido(
            ticket,
            limite + timedelta(minutes=1)
        )

        self.assertFalse(resultado)

    def test_r04_ticket_sin_sla(self):
        ticket = SimpleNamespace(
            sla_fecha_limite=None
        )

        resultado = calcular_sla_cumplido(
            ticket,
            timezone.now()
        )

        self.assertIsNone(resultado)

    # ------------------------------------------------------
    # R05 - VALIDACIÓN DE ESTADOS
    # ------------------------------------------------------

    def test_r05_estado_permitido(self):
        ticket = SimpleNamespace(
            estado=SimpleNamespace(codigo="NUEVO")
        )

        resultado = validar_estado_ticket(
            ticket,
            ["NUEVO"]
        )

        self.assertTrue(resultado)

    def test_r05_estado_no_permitido(self):
        ticket = SimpleNamespace(
            estado=SimpleNamespace(codigo="CERRADO")
        )

        resultado = validar_estado_ticket(
            ticket,
            ["NUEVO"]
        )

        self.assertFalse(resultado)


# ==========================================================
# FIN PRUEBAS R04 Y R05
# ==========================================================