from usuarios.archivos import firmar_urls
from django.utils import timezone
from rest_framework import serializers

from usuarios.models import Area

from .models import (
    EstadoMantenimiento,
    RequerimientoMantenimiento,
    CotizacionMantenimiento,
)


# ==========================================================
# ESTADO
# ==========================================================

class EstadoMantenimientoSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = EstadoMantenimiento

        fields = [
            "id",
            "codigo",
            "nombre",
            "descripcion",
            "es_inicial",
            "es_terminal",
            "activo",
        ]


# ==========================================================
# R02 - COTIZACIONES DE MANTENIMIENTO (SOLO LECTURA)
# ==========================================================

class CotizacionMantenimientoSerializer(serializers.ModelSerializer):
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = CotizacionMantenimiento
        fields = ["id", "nombre_original", "archivo_url", "creado_en", "proveedor", "proveedor_identificador"]
        read_only_fields = fields

    def get_archivo_url(self, obj):
        if not obj.archivo:
            return None
        try:
            return obj.archivo.url
        except ValueError:
            return None


# ==========================================================
# REQUERIMIENTO DE MANTENIMIENTO
# ==========================================================

class RequerimientoMantenimientoSerializer(
    serializers.ModelSerializer
):

    solicitante_nombre = serializers.CharField(
        source="solicitante.nombre_completo",
        read_only=True
    )

    solicitante_email = serializers.CharField(
        source="solicitante.email",
        read_only=True
    )

    area_nombre = serializers.CharField(
        source="area.nombre",
        read_only=True
    )

    estado_nombre = serializers.CharField(
        source="estado.nombre",
        read_only=True
    )

    estado_codigo = serializers.CharField(
        source="estado.codigo",
        read_only=True
    )

    responsable_servicios_generales_nombre = (
        serializers.SerializerMethodField()
    )

    auxiliar_asignado_nombre = (
        serializers.SerializerMethodField()
    )

    evidencia_archivo_url = (
        serializers.SerializerMethodField()
    )

    fotografia_trabajo_url = (
        serializers.SerializerMethodField()
    )


    # ======================================================
    # CAMPOS QUE EL PORTAL SOLICITANTE YA NO PIDE
    # ======================================================
    #
    # El formulario simplificado del solicitante solo
    # captura título, descripción, categoría y foto. Estos
    # campos se completan con un valor por defecto en la
    # vista (RequerimientoMantenimientoViewSet.create)
    # cuando no llegan en el payload.
    # ======================================================

    area = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
        required=False
    )

    ubicacion = serializers.CharField(
        required=False,
        allow_blank=True
    )

    tipo = serializers.ChoiceField(
        choices=RequerimientoMantenimiento.TIPOS_MANTENIMIENTO,
        required=False
    )

    # R02: archivos asociados y progreso para el formulario.
    cotizaciones_r02 = CotizacionMantenimientoSerializer(many=True, read_only=True)
    cantidad_cotizaciones_r02 = serializers.SerializerMethodField()
    cotizaciones_requeridas_r02 = serializers.SerializerMethodField()
    cotizaciones_faltantes_r02 = serializers.SerializerMethodField()

    def get_cantidad_cotizaciones_r02(self, obj):
        archivos = {c.archivo.name for c in obj.cotizaciones_r02.all() if c.archivo}
        if obj.cotizacion_archivo:
            archivos.add(obj.cotizacion_archivo.name)
        return len(archivos)

    def get_cotizaciones_requeridas_r02(self, obj):
        from decimal import Decimal
        from compras.reglas_cotizaciones import requeridas
        return requeridas(obj.costo_estimado)

    def get_cotizaciones_faltantes_r02(self, obj):
        return max(0, self.get_cotizaciones_requeridas_r02(obj) - self.get_cantidad_cotizaciones_r02(obj))

    compra_vinculada = (
        serializers.SerializerMethodField()
    )

    sla_horas = serializers.SerializerMethodField()
    sla_fecha_limite = serializers.SerializerMethodField()
    sla_estado = serializers.SerializerMethodField()

    def get_sla_estado(self, obj):
        from datetime import timedelta
        if obj.estado.codigo in {'INFORME_REGISTRADO','CONFORMIDAD_INFORMADA','FINALIZADO','CERRADO_SIN_COMPRA','RECHAZADO','ANULADO'}:
            return 'FINALIZADO'
        return 'VENCIDO' if timezone.now() > obj.creado_en+timedelta(hours=self.get_sla_horas(obj)) else 'EN_TIEMPO'

    def get_sla_horas(self, obj):
        from config.sla import horas_sla
        return horas_sla(obj.prioridad_jefatura or 'MEDIA')

    def get_sla_fecha_limite(self, obj):
        from datetime import timedelta
        horas = self.get_sla_horas(obj)
        return (obj.creado_en + timedelta(hours=horas)).isoformat() if horas and obj.creado_en else None


    def to_representation(self, instance):
        from urllib.parse import urlsplit
        data = super().to_representation(instance)
        for campo in ("informe_compra", "cotizacion_archivo"):
            if data.get(campo):
                data[campo] = urlsplit(data[campo]).path
        return firmar_urls(data, self.context.get('request'))

    cotizaciones = serializers.SerializerMethodField()
    prioridad_automatica = serializers.SerializerMethodField()

    def get_cotizaciones(self, obj):
        from compras.reglas_cotizaciones import datos_cotizaciones
        return datos_cotizaciones(obj)

    def get_prioridad_automatica(self, obj):
        from config.reglas import prioridad_objeto
        return prioridad_objeto(obj)

    class Meta:

        model = RequerimientoMantenimiento

        fields = [
            'cotizaciones', 'prioridad_automatica', 'via_compra', 'categoria',

            "id",

            "codigo",

            "titulo",

            "descripcion",

            "solicitante",

            "solicitante_nombre",

            "solicitante_email",

            "area",

            "area_nombre",

            "ubicacion",

            "referencia_ubicacion",

            "equipo_afectado",

            "tipo",

            "evidencia",

            "evidencia_archivo",

            "evidencia_archivo_url",

            "estado",

            "estado_nombre",

            "estado_codigo",

            "responsable_servicios_generales",

            "responsable_servicios_generales_nombre",

            "auxiliar_asignado",

            "auxiliar_asignado_nombre",
            "prioridad_jefatura",
            "sla_horas", "sla_fecha_limite", "sla_estado",
            "criterio_prioridad",

            "compra_vinculada",

            "requiere_reposicion",

            "producto_requerido",

            "cantidad_requerida",

            "especificacion_producto",

            "producto_disponible_almacen",

            "producto_entregado",

            "observacion_almacen",

            "derivado_compra",

            "codigo_compra_vinculada",

            "compra_completada",

            "componente_recibido_por",

            "componente_recibido_en",

            "observacion_recepcion_componente",

            "motivo_rechazo",

            "validado_en",

            "clasificado_en",

            "diagnostico",

            "plan_solucion",

            "diagnosticado_en",

            "estado_compra_componente",

            "costo_estimado",

            "cotizacion_archivo", "informe_compra",
            "cotizaciones_r02", "cantidad_cotizaciones_r02",
            "cotizaciones_requeridas_r02", "cotizaciones_faltantes_r02",

            "motivo_no_viable",

            "resultado_pruebas",

            "pruebas_en",

            "verificado_en",

            "rework_count",

            "conformidad_en", "conformidad_solicitante", "conformidad_solicitante_en", "observaciones_conformidad",

            "informe_final",

            "informe_elevado_en",

            "informe_recibido_director_en",

            "proceso_finalizado_en",

            "trabajo_realizado",

            "observaciones_trabajo",

            "informe_trabajo",

            "fotografia_trabajo",

            "fotografia_trabajo_url",

            "recibido_en",

            "derivado_en",

            "revision_almacen_en",

            "inicio_mantenimiento_en",

            "informe_registrado_en",

            "finalizado_en",

            "activo",

            "creado_en",

            "actualizado_en",
        ]


        read_only_fields = [
            'via_compra',

            "motivo_rechazo", "validado_en", "clasificado_en",
            "diagnostico", "plan_solucion", "diagnosticado_en",
            "estado_compra_componente", "costo_estimado", "cotizacion_archivo", "informe_compra",
            "motivo_no_viable", "resultado_pruebas", "pruebas_en",
            "verificado_en", "rework_count", "conformidad_en", "conformidad_solicitante", "conformidad_solicitante_en", "observaciones_conformidad",
            "informe_final", "informe_elevado_en",
            "informe_recibido_director_en", "proceso_finalizado_en",

            "codigo",

            "solicitante",

            "estado",

            "responsable_servicios_generales",

            "auxiliar_asignado",

            "requiere_reposicion",

            "producto_requerido",

            "cantidad_requerida",

            "especificacion_producto",

            "producto_disponible_almacen",

            "producto_entregado",

            "observacion_almacen",

            "derivado_compra",

            "codigo_compra_vinculada",

            "compra_completada",

            "componente_recibido_por",

            "componente_recibido_en",

            "observacion_recepcion_componente",

            "trabajo_realizado",

            "observaciones_trabajo",

            "informe_trabajo",

            "fotografia_trabajo",

            "recibido_en",

            "derivado_en",

            "revision_almacen_en",

            "inicio_mantenimiento_en",

            "informe_registrado_en",

            "finalizado_en",

            "creado_en",

            "actualizado_en",
        ]


    def get_responsable_servicios_generales_nombre(
        self,
        obj
    ):

        if not obj.responsable_servicios_generales:
            return None

        return (
            obj.responsable_servicios_generales
            .nombre_completo
        )


    def get_auxiliar_asignado_nombre(
        self,
        obj
    ):

        if not obj.auxiliar_asignado:
            return None

        return (
            obj.auxiliar_asignado
            .nombre_completo
        )


    def get_compra_vinculada(
        self,
        obj
    ):

        solicitud = (
            obj.compras_generadas
            .filter(activo=True)
            .order_by("-creado_en")
            .first()
        )

        if not solicitud:
            return None

        from compras.serializers import SolicitudCompraResumenSerializer

        return SolicitudCompraResumenSerializer(solicitud).data


    def get_evidencia_archivo_url(
        self,
        obj
    ):

        if not obj.evidencia_archivo:
            return None

        try:

            url = obj.evidencia_archivo.url

        except ValueError:

            return None


        request = self.context.get(
            "request"
        )


        if request:

            return request.build_absolute_uri(
                url
            )


        return url


    def get_fotografia_trabajo_url(
        self,
        obj
    ):

        if not obj.fotografia_trabajo:
            return None

        try:

            url = obj.fotografia_trabajo.url

        except ValueError:

            return None


        request = self.context.get(
            "request"
        )


        if request:

            return request.build_absolute_uri(
                url
            )


        return url


    def validate_evidencia_archivo(
        self,
        archivo
    ):

        if not archivo:
            return archivo


        maximo = (
            5
            *
            1024
            *
            1024
        )


        if archivo.size > maximo:

            raise serializers.ValidationError(
                "El archivo no puede superar los 5 MB."
            )


        nombre = archivo.name.lower()


        extensiones = (
            ".jpg",
            ".jpeg",
            ".png",
            ".pdf",
        )


        if not nombre.endswith(
            extensiones
        ):

            raise serializers.ValidationError(
                "Solo se permiten archivos JPG, JPEG, PNG o PDF."
            )


        return archivo


    def create(
        self,
        validated_data
    ):

        request = self.context.get(
            "request"
        )


        if not request:

            raise serializers.ValidationError(
                {
                    "detalle":
                        "No se pudo identificar al usuario."
                }
            )


        try:

            estado_inicial = (
                EstadoMantenimiento.objects
                .get(
                    codigo="RECIBIDO",
                    activo=True
                )
            )

        except EstadoMantenimiento.DoesNotExist:

            raise serializers.ValidationError(
                {
                    "estado":
                        "No existe el estado RECIBIDO."
                }
            )


        anio = timezone.now().year

        prefijo = (
            f"MTO-{anio}-"
        )


        ultimo = (
            RequerimientoMantenimiento.objects
            .filter(
                codigo__startswith=prefijo
            )
            .order_by(
                "-codigo"
            )
            .first()
        )


        numero = 1


        if ultimo:

            try:

                numero = (
                    int(
                        ultimo.codigo
                        .split("-")[-1]
                    )
                    +
                    1
                )

            except (
                ValueError,
                IndexError
            ):

                numero = (
                    RequerimientoMantenimiento.objects
                    .filter(
                        codigo__startswith=prefijo
                    )
                    .count()
                    +
                    1
                )


        codigo = (
            f"{prefijo}{numero:04d}"
        )


        requerimiento = (
            RequerimientoMantenimiento.objects
            .create(
                codigo=codigo,
                solicitante=request.user,
                estado=estado_inicial,
                **validated_data
            )
        )


        return requerimiento
