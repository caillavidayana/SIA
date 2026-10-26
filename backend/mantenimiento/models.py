from django.conf import settings
from django.db import models

from usuarios.models import Area


# ==========================================================
# ESTADOS DEL PROCESO DE MANTENIMIENTO
# ==========================================================

class EstadoMantenimiento(models.Model):

    codigo = models.CharField(
        max_length=40,
        unique=True
    )

    nombre = models.CharField(
        max_length=100
    )

    descripcion = models.TextField(
        blank=True
    )

    es_inicial = models.BooleanField(
        default=False
    )

    es_terminal = models.BooleanField(
        default=False
    )

    activo = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.nombre


# ==========================================================
# REQUERIMIENTO DE MANTENIMIENTO
# ==========================================================

class RequerimientoMantenimiento(models.Model):
    # R03: reutiliza el catálogo de categorías; los históricos pueden no tenerla.
    categoria = models.ForeignKey('soporte.CategoriaTicket', on_delete=models.PROTECT, null=True, blank=True)
    # R03: la API y las escrituras del ORM imponen la prioridad automática.
    def save(self, *args, **kwargs):
        from config.reglas import prioridad_objeto
        prioridad = prioridad_objeto(self) or (self.prioridad_jefatura if self.prioridad_jefatura else 'MEDIA')
        if prioridad:
            self.prioridad_jefatura = prioridad
            campos = {'prioridad_jefatura'}
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | campos
        super().save(*args, **kwargs)

    via_compra = models.CharField(max_length=20, choices=[('CAJA_CHICA', 'Caja chica'), ('FINANZAS', 'Finanzas')], default='CAJA_CHICA')


    # ======================================================
    # TIPOS
    # ======================================================

    TIPOS_MANTENIMIENTO = [
        (
            "PREVENTIVO",
            "Preventivo"
        ),
        (
            "CORRECTIVO",
            "Correctivo"
        ),
    ]


    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================

    codigo = models.CharField(
        max_length=30,
        unique=True
    )

    titulo = models.CharField(
        max_length=200
    )

    descripcion = models.TextField()


    # ======================================================
    # SOLICITANTE
    # ======================================================

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mantenimientos_solicitados"
    )

    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="requerimientos_mantenimiento"
    )

    ubicacion = models.CharField(
        max_length=200
    )

    referencia_ubicacion = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    equipo_afectado = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )


    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_MANTENIMIENTO
    )


    # ======================================================
    # EVIDENCIA DEL SOLICITANTE
    # ======================================================

    evidencia = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Descripción adicional o referencia "
            "de la evidencia."
        )
    )

    evidencia_archivo = models.FileField(
        upload_to="mantenimiento/evidencias/%Y/%m/",
        blank=True,
        null=True,
        help_text=(
            "Imagen o documento cargado "
            "como evidencia."
        )
    )


    # ======================================================
    # ESTADO DEL PROCESO
    # ======================================================

    estado = models.ForeignKey(
        EstadoMantenimiento,
        on_delete=models.PROTECT,
        related_name="requerimientos"
    )


    # ======================================================
    # SERVICIOS GENERALES
    # ======================================================
    #
    # BPMN:
    # Servicios Generales recibe el requerimiento
    # y lo deriva a su auxiliar.
    #
    # ======================================================

    responsable_servicios_generales = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mantenimientos_servicios_generales",
        null=True,
        blank=True
    )

    auxiliar_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mantenimientos_asignados",
        null=True,
        blank=True
    )

    prioridad_jefatura = models.CharField(max_length=10, blank=True)
    criterio_prioridad = models.TextField(blank=True)

    motivo_rechazo = models.TextField(blank=True)

    validado_en = models.DateTimeField(null=True, blank=True)
    clasificado_en = models.DateTimeField(null=True, blank=True)


    # ======================================================
    # INSPECCIÓN TÉCNICA Y DIAGNÓSTICO
    # ======================================================

    diagnostico = models.TextField(blank=True)

    plan_solucion = models.TextField(blank=True)

    diagnosticado_en = models.DateTimeField(null=True, blank=True)


    # ======================================================
    # REPOSICIÓN DE ALMACÉN
    # ======================================================
    #
    # BPMN:
    #
    # ¿Requiere reposición de almacén?
    #
    # SI  -> verificar existencia.
    # NO  -> realizar mantenimiento.
    #
    # ======================================================

    requiere_reposicion = models.BooleanField(
        null=True,
        blank=True
    )

    producto_requerido = models.CharField(
        max_length=200,
        blank=True
    )

    cantidad_requerida = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    especificacion_producto = models.TextField(
        blank=True
    )


    # ======================================================
    # EXISTENCIA EN ALMACÉN
    # ======================================================

    producto_disponible_almacen = models.BooleanField(
        null=True,
        blank=True
    )

    producto_entregado = models.BooleanField(
        default=False
    )

    observacion_almacen = models.TextField(
        blank=True
    )


    # ======================================================
    # COMPRA CAJA CHICA
    # ======================================================
    #
    # Si NO existe producto:
    # se deriva al subproceso de Compra Caja Chica.
    #
    # ======================================================

    # ------------------------------------------------------
    # BPMN: "¿Requiere compra?" -> el técnico realiza el
    # requerimiento con características y cotización, y la
    # jefatura evalúa su viabilidad antes de elevarlo a la DAF.
    # ------------------------------------------------------

    ESTADOS_COMPRA_COMPONENTE = [
        ("SOLICITADA", "Solicitada"),
        ("NO_VIABLE", "No viable"),
        ("VIABLE", "Viable"),
        ("PENDIENTE_RECEPCION_TECNICO", "Pendiente de recepción por el técnico"),
        ("ENTREGADA", "Componente recibido por el técnico"),
    ]

    estado_compra_componente = models.CharField(
        max_length=30,
        choices=ESTADOS_COMPRA_COMPONENTE,
        blank=True
    )

    costo_estimado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    informe_compra = models.FileField(upload_to="mantenimiento/informes_compra/%Y/%m/", blank=True, null=True)

    cotizacion_archivo = models.FileField(
        upload_to="mantenimiento/cotizaciones/%Y/%m/",
        blank=True,
        null=True
    )

    motivo_no_viable = models.TextField(blank=True)

    derivado_compra = models.BooleanField(
        default=False
    )

    codigo_compra_vinculada = models.CharField(
        max_length=30,
        blank=True
    )

    compra_completada = models.BooleanField(
        default=False
    )

    # La entrega de Almacén debe ser aceptada expresamente por el técnico
    # asignado antes de habilitar la reparación del equipo.
    componente_recibido_por = models.CharField(max_length=150, blank=True)

    componente_recibido_en = models.DateTimeField(null=True, blank=True)

    observacion_recepcion_componente = models.TextField(blank=True)


    # ======================================================
    # EJECUCIÓN DEL MANTENIMIENTO
    # ======================================================

    trabajo_realizado = models.TextField(
        blank=True
    )

    observaciones_trabajo = models.TextField(
        blank=True
    )


    # ======================================================
    # INFORME Y FOTOGRAFÍA
    # ======================================================
    #
    # BPMN:
    # "Realiza un informe, fotograma del trabajo realizado"
    #
    # ======================================================

    resultado_pruebas = models.TextField(blank=True)

    pruebas_en = models.DateTimeField(null=True, blank=True)

    informe_trabajo = models.TextField(
        blank=True
    )

    fotografia_trabajo = models.FileField(
        upload_to="mantenimiento/trabajos/%Y/%m/",
        blank=True,
        null=True,
        help_text=(
            "Fotografía del trabajo "
            "de mantenimiento realizado."
        )
    )


    # ======================================================
    # CONTROL DE FECHAS DEL PROCESO
    # ======================================================

    recibido_en = models.DateTimeField(
        null=True,
        blank=True
    )

    derivado_en = models.DateTimeField(
        null=True,
        blank=True
    )

    revision_almacen_en = models.DateTimeField(
        null=True,
        blank=True
    )

    inicio_mantenimiento_en = models.DateTimeField(
        null=True,
        blank=True
    )

    informe_registrado_en = models.DateTimeField(
        null=True,
        blank=True
    )

    verificado_en = models.DateTimeField(null=True, blank=True)

    rework_count = models.PositiveIntegerField(default=0)

    conformidad_en = models.DateTimeField(null=True, blank=True)
    conformidad_solicitante = models.BooleanField(null=True, blank=True)
    conformidad_solicitante_en = models.DateTimeField(null=True, blank=True)
    observaciones_conformidad = models.TextField(blank=True)


    # ======================================================
    # INFORME FINAL Y DISTRIBUCIÓN
    # ======================================================

    informe_final = models.TextField(blank=True)

    informe_elevado_en = models.DateTimeField(null=True, blank=True)

    informe_recibido_director_en = models.DateTimeField(null=True, blank=True)

    proceso_finalizado_en = models.DateTimeField(null=True, blank=True)

    finalizado_en = models.DateTimeField(
        null=True,
        blank=True
    )


    # ======================================================
    # CONTROL GENERAL
    # ======================================================

    activo = models.BooleanField(
        default=True
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True
    )


    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return (
            f"{self.codigo} - "
            f"{self.titulo}"
        )

# ==========================================================
# R02 - COTIZACIONES MULTIPLES DE MANTENIMIENTO
# ==========================================================
# Se mantiene RequerimientoMantenimiento.cotizacion_archivo
# por compatibilidad con los registros y procesos existentes.
# Las nuevas cotizaciones se almacenan como registros separados.

class CotizacionMantenimiento(models.Model):
    proveedor = models.CharField(max_length=180, blank=True)
    empresa = models.CharField(max_length=180, blank=True)
    proveedor_identificador = models.CharField(max_length=60, blank=True)
    requerimiento = models.ForeignKey(
        RequerimientoMantenimiento,
        on_delete=models.CASCADE,
        related_name="cotizaciones_r02",
    )
    archivo = models.FileField(
        upload_to="mantenimiento/cotizaciones/%Y/%m/",
    )
    nombre_original = models.CharField(max_length=255, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cotizaciones_mantenimiento_r02",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en", "id"]

    def __str__(self):
        return f"Cotización {self.pk} - {self.requerimiento.codigo}"
