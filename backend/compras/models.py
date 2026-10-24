from usuarios.almacenamiento import AlmacenamientoPrivado
from django.conf import settings
from django.db import models
from django.utils import timezone

from usuarios.models import Area


class ActaEntregaAlmacen(models.Model):
    solicitud = models.ForeignKey('compras.SolicitudCompra', on_delete=models.PROTECT, related_name='actas_almacen')
    referencia = models.UUIDField(unique=True, editable=False)
    datos = models.JSONField()
    generado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    generado_en = models.DateTimeField(auto_now_add=True)
    original = models.FileField(upload_to='almacen/actas/%Y/%m/', storage=AlmacenamientoPrivado())
    firmado = models.FileField(upload_to='almacen/actas_firmadas/%Y/%m/', storage=AlmacenamientoPrivado(), blank=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)


class ReciboTesoreria(models.Model):
    """Original emitido y copia firmada del desembolso, conservados para auditoría."""
    solicitud = models.ForeignKey('compras.SolicitudCompra', on_delete=models.PROTECT, related_name='recibos_tesoreria')
    referencia = models.UUIDField(unique=True, editable=False)
    datos = models.JSONField()
    generado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    generado_en = models.DateTimeField(auto_now_add=True)
    original = models.FileField(upload_to='tesoreria/recibos/%Y/%m/', storage=AlmacenamientoPrivado())
    firmado = models.FileField(upload_to='tesoreria/firmados/%Y/%m/', storage=AlmacenamientoPrivado(), blank=True)
    comprobante = models.FileField(upload_to='tesoreria/comprobantes/%Y/%m/', storage=AlmacenamientoPrivado(), blank=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)


class CotizacionCompra(models.Model):
    solicitud = models.ForeignKey('compras.SolicitudCompra', on_delete=models.PROTECT, related_name='cotizaciones')
    proveedor = models.CharField(max_length=180)
    descripcion = models.TextField()
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    documento = models.FileField(upload_to='cotizaciones/%Y/%m/', storage=AlmacenamientoPrivado())
    seleccionada = models.BooleanField(default=False)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    creado_en = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['solicitud'], condition=models.Q(seleccionada=True), name='una_cotizacion_seleccionada')]


class SolicitudCompra(models.Model):

    PRIORIDADES = [
        ("BAJA", "Baja"),
        ("MEDIA", "Media"),
        ("ALTA", "Alta"),
        ("URGENTE", "Urgente"),
    ]

    # Estados vigentes del flujo real de Caja Chica (único
    # flujo implementado hoy). El BPMN lleva la certificación de la
    # DAF directamente a la autorización del Director: Tesorería solo
    # desembolsa, por lo que no existe un paso de verificación previo. Los estados de un diseño
    # "Finanzas" anterior (NUEVO, EN_COTIZACION, EN_APROBACION,
    # APROBADO, ORDEN_EMITIDA, EN_TRANSITO, RECIBIDO,
    # EN_VERIFICACION, CERRADO) fueron retirados por no usarse
    # en ninguna transición de backend ni frontend.
    ESTADOS = [
        ("CREADO_PENDIENTE_DAF", "Creado - pendiente DAF"),
        ("EVALUADO_PENDIENTE_CERTIFICACION", "Evaluado - pendiente de certificación"),
        ("VERIFICADO_PENDIENTE_AUTORIZACION", "Certificado - pendiente de autorización"),
        ("APROBADO_PARA_DESEMBOLSO", "Aprobado para desembolso"),
        ("FONDOS_DESEMBOLSADOS", "Fondos desembolsados"),
        ("COMPRA_REGISTRADA", "Compra realizada - pendiente de entrega"),
        ("COMPRADO_Y_ENTREGADO", "Comprado y entregado"),
        ("DESCARGO_PENDIENTE_LIQUIDACION", "Acta firmada - pendiente de recepción"),
        ("CERRADO_ARCHIVADO", "Cerrado y archivado"),
        ("RECHAZADO", "Rechazado"),
        ("ANULADO", "Anulado"),
    ]

    TIPOS = [
        ("BIEN", "Bien"),
        ("SERVICIO", "Servicio"),
        ("ACTIVO_FIJO", "Activo fijo"),
        ("COMPONENTE", "Componente"),
    ]

    VIAS = [
        ("PENDIENTE", "Pendiente de evaluación"),
        ("CAJA_CHICA", "Caja Chica"),
        ("FINANZAS", "Finanzas"),
    ]

    ORIGENES = [
        ("DIRECTA", "Solicitud directa"),
        ("MANTENIMIENTO", "Derivada de Mantenimiento"),
        ("SOPORTE", "Derivada de Soporte Técnico"),
    ]

    codigo = models.CharField(
        max_length=30,
        unique=True
    )

    titulo = models.CharField(
        max_length=200
    )

    descripcion = models.TextField()

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="compras_solicitadas"
    )

    tecnico_daf = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expedientes_daf_asignados",
    )

    validado_por_jefe_daf = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expedientes_daf_validados",
    )

    prioridad_daf = models.CharField(
        max_length=10,
        choices=PRIORIDADES,
        blank=True,
    )

    criterio_prioridad_daf = models.TextField(blank=True)

    asignado_daf_en = models.DateTimeField(null=True, blank=True)

    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="solicitudes_compra"
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS
    )

    cantidad = models.PositiveIntegerField(
        default=1
    )

    especificaciones = models.TextField()

    justificacion = models.TextField()

    centro_costo = models.CharField(
        max_length=100,
        blank=True
    )

    monto_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    via_adquisicion = models.CharField(
        max_length=20,
        choices=VIAS,
        default="PENDIENTE"
    )

    estado = models.CharField(
        max_length=50,
        choices=ESTADOS,
        default="CREADO_PENDIENTE_DAF"
    )

    # ======================================================
    # ORIGEN DEL EXPEDIENTE
    # ======================================================
    #
    # El subproceso "Compra de Caja Chica" es compartido por
    # 3 flujos (BPMN): solicitud directa, derivación desde
    # Mantenimiento (no hay producto en almacén) y derivación
    # desde Soporte Técnico (ticket requiere componente).
    #
    # ======================================================

    origen_modulo = models.CharField(
        max_length=20,
        choices=ORIGENES,
        default="DIRECTA"
    )

    ticket_soporte = models.ForeignKey(
        "soporte.Ticket",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="compras_generadas"
    )

    requerimiento_mantenimiento = models.ForeignKey(
        "mantenimiento.RequerimientoMantenimiento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="compras_generadas"
    )

    # Campo heredado: antes de existir ticket_soporte (FK real),
    # el vínculo con un ticket se escribía aquí como texto libre
    # sin validar. Se conserva solo para no perder historial.
    ticket_soporte_vinculado = models.CharField(
        max_length=30,
        blank=True
    )

    observaciones = models.TextField(
        blank=True
    )

    informe = models.FileField(upload_to="compras/expedientes/informes/", null=True, blank=True)
    poa = models.FileField(upload_to="compras/expedientes/poa/", null=True, blank=True)
    pedido = models.FileField(upload_to="compras/expedientes/pedidos/", null=True, blank=True)
    proforma = models.FileField(upload_to="compras/expedientes/proformas/", null=True, blank=True)
    certificacion_presupuestaria = models.FileField(upload_to="compras/certificaciones/", null=True, blank=True)
    factura = models.FileField(upload_to="compras/descargos/facturas/", null=True, blank=True)
    acta_conformidad = models.FileField(upload_to="compras/descargos/actas/", null=True, blank=True)
    fotograma = models.FileField(upload_to="compras/descargos/fotogramas/", null=True, blank=True)

    motivo_rechazo = models.TextField(blank=True)
    monto_desembolsado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tipo_desembolso = models.CharField(max_length=50, blank=True)
    comprobante_desembolso = models.FileField(upload_to="compras/comprobantes/", null=True, blank=True)

    # El dinero sale de Tesorería, pero alguien tiene que recogerlo: hasta
    # que el Encargado confirme la recepción, el expediente muestra que los
    # fondos están listos para retirar y Tesorería sabe que sigue pendiente.
    fondos_recibidos_en = models.DateTimeField(null=True, blank=True)
    fondos_recibidos_por = models.CharField(max_length=150, blank=True)

    # Avance visible mientras el Encargado gestiona la compra, para que el
    # resto del proceso sepa que el expediente está siendo trabajado y no
    # detenido.
    GESTIONES = [
        ("BUSCANDO", "Buscando producto o proveedor"),
        ("COMPRANDO", "Compra en curso"),
    ]

    gestion_estado = models.CharField(max_length=20, choices=GESTIONES, blank=True)
    gestion_nota = models.CharField(max_length=200, blank=True)
    gestion_actualizada_en = models.DateTimeField(null=True, blank=True)
    responsable_adquisicion = models.CharField(max_length=150, blank=True)
    monto_real = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    proveedor = models.CharField(max_length=180, blank=True)

    # Caso de uso "Registrar verificación de componentes"
    # (Encargado de Compras y Almacén): se confirma junto con
    # el registro de la compra, antes de habilitar el ingreso
    # a almacén.
    componente_verificado = models.BooleanField(default=False)
    observacion_verificacion = models.TextField(blank=True)

    # Sin comprobante no hay compra: el registro debe quedar respaldado
    # con la factura o recibo del proveedor.
    comprobante_compra = models.FileField(
        upload_to="compras/comprobantes/%Y/%m/",
        null=True,
        blank=True,
        help_text="Factura o recibo que respalda la compra realizada."
    )

    fecha_compra = models.DateTimeField(null=True, blank=True)

    # BPMN: entrada de almacén -> salida de almacén -> entrega del bien
    # con acta de conformidad. Son tres registros distintos y en ese orden.
    fecha_ingreso_almacen = models.DateTimeField(null=True, blank=True)

    # Control de almacén: qué cantidad ingresó, quién la recibió y qué
    # observaciones dejó la recepción.
    cantidad_recibida = models.PositiveIntegerField(null=True, blank=True)
    responsable_recepcion = models.CharField(max_length=150, blank=True)
    observacion_ingreso = models.TextField(blank=True)

    fecha_despacho_almacen = models.DateTimeField(null=True, blank=True)

    # Control de salida: qué cantidad salió y a quién se entregó.
    cantidad_entregada = models.PositiveIntegerField(null=True, blank=True)
    entregado_a = models.CharField(max_length=150, blank=True)
    observacion_salida = models.TextField(blank=True)

    fecha_entrega_solicitante = models.DateTimeField(null=True, blank=True)

    # Cierre en el carril del solicitante: firma el acta y recibe el bien.
    acta_firmada_en = models.DateTimeField(null=True, blank=True)
    solicitud_recibida_en = models.DateTimeField(null=True, blank=True)

    cerrado_inmutable = models.BooleanField(default=False)

    activo = models.BooleanField(
        default=True
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True
    )

    #def save(self, *args, **kwargs):

        # Regla EMI utilizada para Caja Chica.
 #       if self.monto_estimado is not None:
#
 #           if self.monto_estimado <= 1500:
#                self.via_adquisicion = "CAJA_CHICA"

  #          else:
         #       self.via_adquisicion = "FINANZAS"

       # super().save(*args, **kwargs)
    def save(self, *args, **kwargs):
        from auditoria.models import PreferenciaSistema
        from decimal import Decimal

        if self.monto_estimado is not None:
            preferencias = PreferenciaSistema.objects.first()

            limite = (
                preferencias.limite_caja_chica
                if preferencias is not None
                else Decimal("1000.00")
            )

            if self.monto_estimado <= limite:
                self.via_adquisicion = "CAJA_CHICA"
            else:
                self.via_adquisicion = "FINANZAS"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    @classmethod
    def generar_codigo(cls):
        """Código correlativo CMP-<año>-NNNN, compartido por el
        serializer (creación directa) y por los disparadores
        internos desde Mantenimiento/Soporte."""

        anio = timezone.now().year
        prefijo = f"CMP-{anio}-"

        ultimo = (
            cls.objects
            .filter(codigo__startswith=prefijo)
            .order_by("-codigo")
            .first()
        )

        numero = 1

        if ultimo:
            try:
                numero = int(ultimo.codigo.split("-")[-1]) + 1
            except ValueError:
                numero = cls.objects.count() + 1

        return f"{prefijo}{numero:04d}"
