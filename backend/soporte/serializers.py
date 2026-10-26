from usuarios.archivos import firmar_urls
from django.utils import timezone

from rest_framework import serializers

from usuarios.models import Area

from .models import (
    CategoriaTicket,
    EstadoTicket,
    Ticket,
    NotificacionSoporte,
)


class NotificacionSoporteSerializer(serializers.ModelSerializer):
    ticket_codigo = serializers.CharField(source="ticket.codigo", read_only=True)
    ticket_titulo = serializers.SerializerMethodField()

    def get_ticket_titulo(self, obj):
        return (obj.ticket or obj.mantenimiento).titulo if (obj.ticket or obj.mantenimiento) else ''

    class Meta:
        model = NotificacionSoporte
        fields = ["id", "tipo", "titulo", "mensaje", "leida", "creada_en", "leida_en", "ticket", "mantenimiento", "ticket_codigo", "ticket_titulo"]
        read_only_fields = fields


# ==========================================================
# CATEGORÍA
# ==========================================================

class CategoriaTicketSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = CategoriaTicket

        fields = [
            "id",
            "codigo",
            "nombre",
            "descripcion",
            "activo",
        ]


# ==========================================================
# ESTADO
# ==========================================================

class EstadoTicketSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = EstadoTicket

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
# TICKET SOPORTE TÉCNICO
# ==========================================================

class TicketSerializer(
    serializers.ModelSerializer
):

    # ======================================================
    # DATOS DESCRIPTIVOS PARA EL FRONTEND
    # ======================================================

    solicitante_nombre = serializers.CharField(
        source="solicitante.nombre_completo",
        read_only=True
    )

    solicitante_email = serializers.CharField(
        source="solicitante.email",
        read_only=True
    )

    tecnico_nombre = serializers.SerializerMethodField()

    area_nombre = serializers.CharField(
        source="area.nombre",
        read_only=True
    )

    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True
    )

    categoria_codigo = serializers.CharField(
        source="categoria.codigo",
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

    especialistas_apoyo_nombres = (
        serializers.SerializerMethodField()
    )


    # ======================================================
    # CAMPOS QUE EL PORTAL SOLICITANTE YA NO PIDE
    # ======================================================
    #
    # El formulario simplificado del solicitante solo
    # captura título, descripción y foto. Estos campos
    # se completan con un valor por defecto en la vista
    # (TicketViewSet.create) cuando no llegan en el payload.
    # ======================================================

    area = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
        required=False
    )

    ubicacion = serializers.CharField(
        required=False,
        allow_blank=True
    )

    equipo_afectado = serializers.CharField(
        required=False,
        allow_blank=True
    )

    categoria = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaTicket.objects.all(),
        required=False
    )


    # ======================================================
    # EVIDENCIA
    # ======================================================

    evidencia_archivo = serializers.FileField(
        required=False,
        allow_null=True
    )

    evidencia_archivo_url = (
        serializers.SerializerMethodField()
    )


    # ======================================================
    # DATOS CALCULADOS DEL SLA
    # ======================================================

    sla_estado = (
        serializers.SerializerMethodField()
    )

    sla_restante_minutos = (
        serializers.SerializerMethodField()
    )

    compra_vinculada = (
        serializers.SerializerMethodField()
    )

    cotizacion_archivo_url = (
        serializers.SerializerMethodField()
    )

    evidencia_diagnostico_url = serializers.SerializerMethodField()
    evidencia_intervencion_url = serializers.SerializerMethodField()
    evidencia_pruebas_url = serializers.SerializerMethodField()
    informe_final_pdf_url = serializers.SerializerMethodField()
    informe_tecnico_pdf_url = serializers.SerializerMethodField()
    informe_jefe_carrera_pdf_url = serializers.SerializerMethodField()


    # ======================================================
    # META
    # ======================================================

    def to_representation(self, instance):
        from urllib.parse import urlsplit
        data = super().to_representation(instance)
        for campo in ("informe_compra", "cotizacion_archivo"):
            if data.get(campo):
                data[campo] = urlsplit(data[campo]).path
        return firmar_urls(data, self.context.get('request'))

    prioridad = serializers.ChoiceField(choices=Ticket.PRIORIDADES, required=False)

    puede_reabrir = serializers.SerializerMethodField()
    fecha_limite_reapertura = serializers.SerializerMethodField()

    def get_puede_reabrir(self, obj):
        from .reapertura import puede_reabrir
        request=self.context.get('request')
        return puede_reabrir(obj, request.user if request else None)

    def get_fecha_limite_reapertura(self, obj):
        from .reapertura import fecha_maxima
        return fecha_maxima(obj)

    cotizaciones = serializers.SerializerMethodField()
    prioridad_automatica = serializers.SerializerMethodField()

    def get_cotizaciones(self, obj):
        from compras.reglas_cotizaciones import datos_cotizaciones
        return datos_cotizaciones(obj)

    def get_prioridad_automatica(self, obj):
        from config.reglas import prioridad_objeto
        return prioridad_objeto(obj)

    class Meta:

        model = Ticket

        fields = [
            'cotizaciones', 'prioridad_automatica', 'via_compra', 'puede_reabrir', 'fecha_limite_reapertura', 'reabierto_en', 'historial_reaperturas',

            # ------------------------------------------------
            # IDENTIFICACIÓN
            # ------------------------------------------------

            "id",

            "codigo",

            "titulo",

            "descripcion",

            # ------------------------------------------------
            # SOLICITANTE
            # ------------------------------------------------

            "solicitante",

            "solicitante_nombre",

            "solicitante_email",

            # ------------------------------------------------
            # ÁREA / UBICACIÓN
            # ------------------------------------------------

            "area",

            "area_nombre",

            "ubicacion",

            "referencia_ubicacion",

            "equipo_afectado",

            # ------------------------------------------------
            # EVIDENCIA
            # ------------------------------------------------

            "evidencia",

            "evidencia_archivo",

            "evidencia_archivo_url",

            # ------------------------------------------------
            # CLASIFICACIÓN UTIC
            # ------------------------------------------------

            "categoria",

            "categoria_nombre",

            "categoria_codigo",

            "tipo_problema",

            "prioridad",

            "criterio_tecnico",

            # ------------------------------------------------
            # SLA
            # ------------------------------------------------

            "sla_horas",

            "sla_fecha_limite",

            "sla_cumplido",

            "sla_estado",

            "sla_restante_minutos",

            # -----------------------------------------------
            # ESTADO

            # ------------------------------------------------

            "estado",

            "estado_nombre",

            "estado_codigo",

            # ------------------------------------------------
            # RESPONSABLES

            # ------------------------------------------------

            "tecnico_asignado",

            "tecnico_nombre",

            "especialistas_apoyo",

            "especialistas_apoyo_nombres",

            # ------------------------------------------------
            # DIAGNÓSTICO
            # ------------------------------------------------

            "diagnostico",

            "observaciones_diagnostico",

            "evidencia_diagnostico",

            "evidencia_diagnostico_url",

            "plan_solucion",

            "solucion",

            "acciones_realizadas",

            "componentes_utilizados",

            "evidencia_intervencion",

            "evidencia_intervencion_url",

            # ------------------------------------------------
            # COMPRA VINCULADA
            # ------------------------------------------------

            "requiere_compra",

            "cantidad_componente",

            "componente_requerido",

            "especificaciones_tecnicas",

            "justificacion_compra",

            "proveedor_cotizacion",

            "costo_estimado",

            "cotizacion_archivo", "informe_compra",

            "cotizacion_archivo_url",

            "estado_compra_componente",

            "motivo_no_viable",

            "componente_entregado_en",

            "codigo_compra_vinculada",

            "compra_vinculada",

            # ------------------------------------------------
            # RESULTADOS
            # ------------------------------------------------

            "resultado_pruebas",

            "evidencia_pruebas",

            "evidencia_pruebas_url",

            "conformidad_usuario",

            "observaciones_usuario",

            "informe_tecnico",

            "informe_tecnico_pdf",

            "informe_tecnico_pdf_url",
            "informe_jefe_carrera",

            "informe_jefe_carrera_pdf",

            "informe_jefe_carrera_pdf_url",

            "informe_jefe_carrera_en",

            "informe_final",

            "informe_final_pdf",

            "informe_final_pdf_url",

            "informe_elevado_en",

            "informe_recibido_director_en",

            "proceso_finalizado_en",

            # ------------------------------------------------
            # FECHAS DEL WORKFLOW
            # ------------------------------------------------

            "validado_en",

            "clasificado_en",

            "asignado_en",

            "inicio_atencion_en",

            "pruebas_en",

            "verificado_en",

            "conformidad_en",

            # ------------------------------------------------
            # CONTROL Y AUDITORÍA
            # ------------------------------------------------

            "rework_count",

            "activo",

            "creado_en",

            "actualizado_en",

            "cerrado_en",

        ]

        # ==================================================
        # INICIO R05 - PROTECCION DE ESTADO Y SLA
        # ==================================================

        # ==================================================
        # CAMPOS CONTROLADOS POR SIGTA
        # ==================================================
        #
        # El solicitante NO puede enviar estos valores
        # directamente.
        #
        # Son modificados mediante las acciones específicas
        # definidas en soporte/views.py.
        #
        # ==================================================

        read_only_fields = [
            'via_compra', 'reabierto_en', 'historial_reaperturas',

            "codigo",

            "solicitante",

            "estado",

            "tecnico_asignado",

            "especialistas_apoyo",

            "tipo_problema",


            "criterio_tecnico",


            # SLA

            "sla_horas",

            "sla_fecha_limite",

            "sla_cumplido",


            # Diagnóstico

            "diagnostico",

            "observaciones_diagnostico",

            "evidencia_diagnostico",

            "plan_solucion",

            "solucion",

            "acciones_realizadas",

            "componentes_utilizados",

            "evidencia_intervencion",


            # Compra

            "requiere_compra",

            "cantidad_componente",

            "componente_requerido",

            "especificaciones_tecnicas",

            "justificacion_compra",

            "proveedor_cotizacion",

            "costo_estimado",

            "cotizacion_archivo", "informe_compra",

            "estado_compra_componente",

            "motivo_no_viable",

            "componente_entregado_en",

            "codigo_compra_vinculada",


            # Resultados

            "resultado_pruebas",

            "evidencia_pruebas",

            "conformidad_usuario",

            "observaciones_usuario",

            "informe_tecnico",

            "informe_final",

            "informe_elevado_en",

            "informe_recibido_director_en",

            "proceso_finalizado_en",


            # Fechas workflow

            "validado_en",

            "clasificado_en",

            "asignado_en",

            "inicio_atencion_en",

            "pruebas_en",

            "verificado_en",

            "conformidad_en",


            # Control

            "rework_count",

            "cerrado_en",

            "creado_en",

            "actualizado_en",
        ]


    # ======================================================
    # TÉCNICO ASIGNADO
    # ======================================================

    def get_tecnico_nombre(
        self,
        obj
    ):

        if not obj.tecnico_asignado:

            return None


        return (
            obj.tecnico_asignado
            .nombre_completo
        )


    # ======================================================
    # ESPECIALISTAS DE APOYO
    # ======================================================

    def get_especialistas_apoyo_nombres(
        self,
        obj
    ):

        return [
            usuario.nombre_completo

            for usuario
            in obj.especialistas_apoyo.all()
        ]


    # ======================================================
    # COMPRA VINCULADA (RESUMEN)
    # ======================================================

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


    # ======================================================
    # URL DE LA COTIZACIÓN DEL COMPONENTE
    # ======================================================

    def _archivo_url(self, archivo):
        if not archivo:
            return None
        try:
            url = archivo.url
        except ValueError:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_evidencia_diagnostico_url(self, obj):
        return self._archivo_url(obj.evidencia_diagnostico)

    def get_evidencia_intervencion_url(self, obj):
        return self._archivo_url(obj.evidencia_intervencion)

    def get_evidencia_pruebas_url(self, obj):
        return self._archivo_url(obj.evidencia_pruebas)

    def get_informe_final_pdf_url(self, obj):
        return self._archivo_url(obj.informe_final_pdf)

    def get_informe_tecnico_pdf_url(self, obj):
        return self._archivo_url(obj.informe_tecnico_pdf)

    def get_informe_jefe_carrera_pdf_url(self, obj):
        return self._archivo_url(obj.informe_jefe_carrera_pdf)

    def get_cotizacion_archivo_url(
        self,
        obj
    ):

        if not obj.cotizacion_archivo:

            return None


        try:

            url = obj.cotizacion_archivo.url

        except ValueError:

            return None


        request = self.context.get(
            "request"
        )


        return (
            request.build_absolute_uri(url)
            if request
            else url
        )


    # ======================================================
    # URL DEL ARCHIVO DE EVIDENCIA
    # ======================================================

    def get_evidencia_archivo_url(
        self,
        obj
    ):

        if not obj.evidencia_archivo:

            return None


        try:

            url = (
                obj.evidencia_archivo.url
            )

        except ValueError:

            return None


        request = self.context.get(
            "request"
        )


        if request:

            return (
                request.build_absolute_uri(
                    url
                )
            )


        return url


    # ======================================================
    # ESTADO DEL SLA
    # ======================================================

    def get_sla_estado(self, obj):
        # R04: Resuelto/Cerrado no se etiquetan como Vencido.
        if not obj.sla_fecha_limite:
            return 'SIN_SLA'
        finalizado = obj.estado.codigo in {'PENDIENTE_CONFORMIDAD', 'PENDIENTE_INFORME_FINAL', 'CERRADO', 'CERRADO_SIN_COMPRA', 'RECHAZADO', 'ANULADO'}
        if finalizado:
            fin = obj.pruebas_en or obj.cerrado_en or timezone.now()
            return 'CUMPLIDO' if fin <= obj.sla_fecha_limite else 'INCUMPLIDO'
        restante = (obj.sla_fecha_limite-timezone.now()).total_seconds()
        if restante < 0:
            return 'VENCIDO'
        if obj.sla_horas and restante <= obj.sla_horas*3600*0.25:
            return 'EN_RIESGO'
        return 'EN_TIEMPO'

    # ======================================================
    # MINUTOS RESTANTES DEL SLA
    # ======================================================

    def get_sla_restante_minutos(
        self,
        obj
    ):

        if not obj.sla_fecha_limite:

            return None


        if obj.estado.codigo in {'CERRADO', 'CERRADO_SIN_COMPRA', 'RECHAZADO', 'ANULADO'}:

            return 0


        diferencia = (
            obj.sla_fecha_limite
            -
            timezone.now()
        )


        return int(
            diferencia.total_seconds()
            /
            60
        )


    # ======================================================
    # VALIDAR ARCHIVO DE EVIDENCIA
    # ======================================================

    def validate_evidencia_archivo(
        self,
        archivo
    ):

        if not archivo:

            return archivo


        # --------------------------------------------------
        # TAMAÑO MÁXIMO: 5 MB
        # --------------------------------------------------

        maximo = (
            5
            *
            1024
            *
            1024
        )


        if archivo.size > maximo:

            raise serializers.ValidationError(
                (
                    "El archivo no puede "
                    "superar los 5 MB."
                )
            )


        # --------------------------------------------------
        # EXTENSIONES
        # --------------------------------------------------

        nombre = (
            archivo.name
            .lower()
        )


        extensiones_permitidas = (
            ".jpg",
            ".jpeg",
            ".png",
            ".pdf",
        )


        if not nombre.endswith(
            extensiones_permitidas
        ):

            raise serializers.ValidationError(
                (
                    "Solo se permiten archivos "
                    "JPG, JPEG, PNG o PDF."
                )
            )


        return archivo


    # ======================================================
    # VALIDACIÓN GENERAL
    # ======================================================

    def validate(
        self,
        attrs
    ):

        # R05: un PATCH no puede saltarse las acciones autorizadas del BPMN.
        if self.instance and any(c in self.initial_data for c in ('estado', 'estado_codigo', 'sla_fecha_limite', 'sla_horas')):
            raise serializers.ValidationError({'detalle': 'Use las acciones autorizadas para cambiar estado o SLA.'})
        if self.instance and self.instance.clasificado_en and 'prioridad' in attrs:
            from config.reglas import prioridad_objeto
            if not prioridad_objeto(self.instance):
                raise serializers.ValidationError({'detalle': 'La prioridad clasificada solo cambia mediante Jefatura.'})

        # --------------------------------------------------
        # IMPORTANTE:
        #
        # En PATCH pueden no venir todos los campos.
        # Por eso utilizamos instance cuando exista.
        # --------------------------------------------------

        titulo = attrs.get(
            "titulo",
            getattr(
                self.instance,
                "titulo",
                ""
            )
        )


        descripcion = attrs.get(
            "descripcion",
            getattr(
                self.instance,
                "descripcion",
                ""
            )
        )


        ubicacion = attrs.get(
            "ubicacion",
            getattr(
                self.instance,
                "ubicacion",
                ""
            )
        )


        equipo = attrs.get(
            "equipo_afectado",
            getattr(
                self.instance,
                "equipo_afectado",
                ""
            )
        )


        # --------------------------------------------------
        # NORMALIZAR
        # --------------------------------------------------

        titulo = (
            str(
                titulo
                or
                ""
            )
            .strip()
        )


        descripcion = (
            str(
                descripcion
                or
                ""
            )
            .strip()
        )


        ubicacion = (
            str(
                ubicacion
                or
                ""
            )
            .strip()
        )


        equipo = (
            str(
                equipo
                or
                ""
            )
            .strip()
        )


        # --------------------------------------------------
        # VALIDACIONES
        # --------------------------------------------------

        if not titulo:

            raise serializers.ValidationError(
                {
                    "titulo":
                        "El título es obligatorio."
                }
            )


        if not descripcion:

            raise serializers.ValidationError(
                {
                    "descripcion":
                        "La descripción es obligatoria."
                }
            )


        # --------------------------------------------------
        # UBICACIÓN Y EQUIPO AFECTADO
        #
        # El formulario simplificado del portal solicitante
        # ya no pide estos campos: TicketViewSet.create()
        # les asigna un valor por defecto cuando faltan.
        # Solo se exigen aquí en edición (self.instance ya
        # existe), donde el equipo interno sí los completa.
        # --------------------------------------------------

        if self.instance is not None:

            if not ubicacion:

                raise serializers.ValidationError(
                    {
                        "ubicacion":
                            "La ubicación es obligatoria."
                    }
                )


            if not equipo:

                raise serializers.ValidationError(
                    {
                        "equipo_afectado": (
                            "Debe indicar el equipo "
                            "afectado."
                        )
                    }
                )


        return attrs


    # ======================================================
    # CREAR TICKET
    # ======================================================

    def create(
        self,
        validated_data
    ):

        request = (
            self.context.get(
                "request"
            )
        )


        if not request:

            raise serializers.ValidationError(
                {
                    "detalle": (
                        "No se pudo identificar "
                        "al usuario."
                    )
                }
            )


        usuario = (
            request.user
        )


        # ==================================================
        # ESTADO INICIAL
        # ==================================================

        try:

            estado_nuevo = (
                EstadoTicket.objects
                .get(
                    codigo="NUEVO",
                    activo=True
                )
            )


        except EstadoTicket.DoesNotExist:

            raise serializers.ValidationError(
                {
                    "estado": (
                        "No existe el estado NUEVO "
                        "activo en el sistema."
                    )
                }
            )


        # ==================================================
        # GENERAR CÓDIGO
        # SOP-2026-0001
        # ==================================================

        anio = (
            timezone.now().year
        )


        prefijo = (
            f"SOP-{anio}-"
        )


        ultimo = (
            Ticket.objects
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
                    Ticket.objects
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


        # ==================================================
        # CREAR
        # ==========================================================

        ticket = (
            Ticket.objects.create(

                codigo=codigo,

                solicitante=usuario,

                estado=estado_nuevo,

                # ==========================================
                # EL SOLICITANTE NO DEFINE:
                #
                # - prioridad
                # - SLA
                # - responsable
                # - estado
                #
                # ==========================================

                prioridad=validated_data.pop('prioridad', 'MEDIA'),

                sla_horas=None,

                sla_fecha_limite=None,

                sla_cumplido=None,

                **validated_data
            )
        )


        return ticket
