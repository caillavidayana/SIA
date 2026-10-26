from usuarios.documentos import documentar, documentos_expediente, pdf_documento
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction

from rest_framework import (
    status,
    viewsets,
)

from usuarios.authentication import (
    ExpiringTokenAuthentication as TokenAuthentication,
)

from rest_framework.decorators import (
    action,
)

from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import Response


from usuarios.models import (
    Area,
    Usuario,
    UsuarioRol,
    obtener_codigos_rol_efectivos,
)

from auditoria.utils import (
    registrar_bitacora,
)


from .models import (
    EstadoMantenimiento,
    RequerimientoMantenimiento,
    CotizacionMantenimiento,
)

from .serializers import (
    EstadoMantenimientoSerializer,
    RequerimientoMantenimientoSerializer,
)
from soporte.informes_pdf import informe_requerimiento_mantenimiento


# ==========================================================
# VALORES POR DEFECTO DEL FORMULARIO SIMPLIFICADO
# ==========================================================
#
# El portal solicitante ya no pide área ni tipo: solo
# título, descripción, categoría (Soporte/Mantenimiento)
# y foto. Este helper completa el área que el modelo
# RequerimientoMantenimiento sigue requiriendo.
# ==========================================================

def _area_por_defecto():

    return (
        Area.objects
        .filter(activo=True)
        .order_by("id")
        .first()
    )


# ==========================================================
# ROLES ADMINISTRATIVOS
# ==========================================================

ROLES_ADMIN = {
    "ADMIN",
    "ADMINISTRADOR",
    "ADMINISTRADOR_SIGTA",
}


# ==========================================================
# OBTENER ROLES DEL USUARIO
# ==========================================================

def obtener_roles(usuario):

    # Incluye roles delegados temporalmente (Delegar aprobación
    # temporal) además de los roles propios.
    return obtener_codigos_rol_efectivos(usuario)


# ==========================================================
# ADMIN
# ==========================================================

def es_admin(usuario):

    if (
        not usuario
        or not usuario.is_authenticated
    ):
        return False


    if usuario.is_superuser:
        return True


    roles = {
        str(codigo).strip().upper()
        for codigo in obtener_roles(usuario)
    }


    return bool(
        roles.intersection(
            ROLES_ADMIN
        )
    )


# ==========================================================
# VERIFICAR ROL
# ==========================================================

def tiene_rol(
    usuario,
    *codigos
):

    if es_admin(usuario):
        return True


    roles_usuario = {
        str(codigo).strip().upper()
        for codigo in obtener_roles(usuario)
    }


    codigos_validos = {
        str(codigo).strip().upper()
        for codigo in codigos
    }


    return bool(
        roles_usuario.intersection(
            codigos_validos
        )
    )


# ==========================================================
# PERSONAL QUE OPERA MANTENIMIENTO
# ==========================================================

def puede_operar_mantenimiento(usuario):

    return (
        es_admin(usuario)
        or
        tiene_rol(
            usuario,
            "SERVICIOS_GENERALES",
            "AUXILIAR_SERVICIOS_GENERALES",
            "ENCARGADO_COMPRAS_ALMACEN",
        )
    )


# ==========================================================
# OBTENER ESTADO
# ==========================================================

def obtener_estado(codigo):

    try:

        return EstadoMantenimiento.objects.get(
            codigo=codigo,
            activo=True
        )

    except EstadoMantenimiento.DoesNotExist:

        return None


# ==========================================================
# VALIDAR ESTADO
# ==========================================================

def estado_permitido(
    requerimiento,
    codigos
):

    return (
        requerimiento.estado.codigo
        in codigos
    )


# ==========================================================
# RESPUESTA DEL REQUERIMIENTO
# ==========================================================

def respuesta_requerimiento(
    requerimiento,
    mensaje,
    request,
    codigo_http=status.HTTP_200_OK
):

    serializer = (
        RequerimientoMantenimientoSerializer(
            requerimiento,
            context={
                "request": request
            }
        )
    )


    return Response(
        {
            "ok": True,
            "mensaje": mensaje,
            "requerimiento": serializer.data,
        },
        status=codigo_http
    )


# ==========================================================
# ESTADOS
# ==========================================================

class EstadoMantenimientoViewSet(
    viewsets.ReadOnlyModelViewSet
):

    queryset = (
        EstadoMantenimiento.objects
        .filter(
            activo=True
        )
        .order_by(
            "id"
        )
    )

    serializer_class = (
        EstadoMantenimientoSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


# ==========================================================
# REQUERIMIENTOS DE MANTENIMIENTO
# ==========================================================

class RequerimientoMantenimientoViewSet(
    viewsets.ModelViewSet
):

    @action(detail=True, methods=['get'], url_path='documentos')
    def documentos(self, request, pk=None):
        return documentos_expediente(self, request, pk)

    @action(detail=True, methods=['get'], url_path=r'documentos/(?P<documento_id>[0-9]+)/pdf')
    def documento_pdf(self, request, pk=None, documento_id=None):
        return pdf_documento(self, request, pk, documento_id)

    serializer_class = (
        RequerimientoMantenimientoSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]


    # ======================================================
    # CONSULTA
    # ======================================================

    def get_queryset(self):

        usuario = self.request.user


        queryset = (
            RequerimientoMantenimiento.objects
            .select_related(
                "solicitante",
                "area",
                "estado",
                "responsable_servicios_generales",
                "auxiliar_asignado",
                "categoria",
            )
            .prefetch_related('cotizaciones_r02')
            .order_by(
                "-creado_en"
            )
        )


        if self.action == "list" and self.request.query_params.get("propias") == "1":
            return queryset.filter(solicitante=usuario)

        # ADMIN y personal de mantenimiento ven todos
        if puede_operar_mantenimiento(
            usuario
        ):

            return queryset


        # Director: acceso de solo lectura a los requerimientos
        # ya finalizados (BPMN: "Director recibe los reportes").
        # No opera el flujo, por eso no entra en
        # puede_operar_mantenimiento.
        if tiene_rol(usuario, "DIRECTOR"):

            # La Dirección ve los informes que la jefatura le elevó
            # (para acusar recibo) y los ya finalizados.
            from django.db.models import Q

            return queryset.filter(
                Q(informe_elevado_en__isnull=False)
                | Q(estado__codigo="FINALIZADO")
            )


        # Solicitante solamente ve sus requerimientos
        return queryset.filter(
            solicitante=usuario
        )


    # ======================================================
    # REGISTRAR REQUERIMIENTO
    # ======================================================

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = self.get_serializer(
            data=request.data
        )


        serializer.is_valid(
            raise_exception=True
        )


        extra = {}

        if not serializer.validated_data.get("area"):

            area_defecto = _area_por_defecto()

            if area_defecto is None:
                return Response(
                    {"detalle": "No hay áreas registradas en el sistema."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            extra["area"] = area_defecto

        if not serializer.validated_data.get("ubicacion"):
            extra["ubicacion"] = "No especificado"

        if not serializer.validated_data.get("tipo"):
            extra["tipo"] = "CORRECTIVO"


        requerimiento = (
            serializer.save(**extra)
        )


        registrar_bitacora(
            request=request,
            accion=
                "REGISTRAR_REQUERIMIENTO_MANTENIMIENTO",
            modulo=
                "Mantenimiento",
            detalle=(
                f"Se registró el requerimiento "
                f"{requerimiento.codigo}: "
                f"{requerimiento.titulo}."
            ),
            nivel=
                "INFO",
        )


        return respuesta_requerimiento(
            requerimiento,
            "Requerimiento de mantenimiento registrado correctamente.",
            request,
            status.HTTP_201_CREATED
        )


    # ======================================================
    # MODIFICAR REQUERIMIENTO
    # ======================================================

    def partial_update(
        self,
        request,
        *args,
        **kwargs
    ):

        requerimiento = (
            self.get_object()
        )

        usuario = request.user


        # --------------------------------------------------
        # SOLICITANTE
        # --------------------------------------------------

        if (
            requerimiento.solicitante_id
            ==
            usuario.id
        ):

            if (
                requerimiento.estado.codigo
                !=
                "RECIBIDO"
            ):

                return Response(
                    {
                        "detalle": (
                            "El requerimiento ya fue "
                            "derivado y no puede "
                            "modificarse libremente."
                        )
                    },
                    status=
                        status.HTTP_400_BAD_REQUEST
                )


        # --------------------------------------------------
        # PERSONAL AUTORIZADO
        # --------------------------------------------------

        elif not puede_operar_mantenimiento(
            usuario
        ):

            return Response(
                {
                    "detalle": (
                        "No tiene permiso para "
                        "modificar este requerimiento."
                    )
                },
                status=
                    status.HTTP_403_FORBIDDEN
            )


        respuesta = (
            super()
            .partial_update(
                request,
                *args,
                **kwargs
            )
        )


        registrar_bitacora(
            request=request,
            accion=
                "MODIFICAR_REQUERIMIENTO_MANTENIMIENTO",
            modulo=
                "Mantenimiento",
            detalle=(
                f"Se modificó el requerimiento "
                f"{requerimiento.codigo}."
            ),
            nivel=
                "INFO",
        )


        return respuesta


    # ======================================================
    # ANULAR REQUERIMIENTO
    # ======================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        requerimiento = (
            self.get_object()
        )

        usuario = request.user


        if (
            requerimiento.solicitante_id
            !=
            usuario.id
        ):

            return Response(
                {
                    "detalle": (
                        "Solo el solicitante puede "
                        "anular este requerimiento."
                    )
                },
                status=
                    status.HTTP_403_FORBIDDEN
            )


        if (
            requerimiento.estado.codigo
            !=
            "RECIBIDO"
        ):

            return Response(
                {
                    "detalle": (
                        "El requerimiento ya está "
                        "siendo atendido y no puede "
                        "anularse."
                    )
                },
                status=
                    status.HTTP_400_BAD_REQUEST
            )


        estado_anulado = obtener_estado(
            "ANULADO"
        )


        if not estado_anulado:

            return Response(
                {
                    "detalle":
                        "No existe el estado ANULADO."
                },
                status=
                    status.HTTP_400_BAD_REQUEST
            )


        requerimiento.estado = (
            estado_anulado
        )

        requerimiento.activo = False


        requerimiento.save(
            update_fields=[
                "estado",
                "activo",
                "actualizado_en",
            ]
        )


        registrar_bitacora(
            request=request,
            accion=
                "ANULAR_REQUERIMIENTO_MANTENIMIENTO",
            modulo=
                "Mantenimiento",
            detalle=(
                f"Se anuló el requerimiento "
                f"{requerimiento.codigo}."
            ),
            nivel=
                "WARNING",
        )


        return Response(
            {
                "ok": True,
                "mensaje":
                    "Requerimiento anulado correctamente."
            },
            status=status.HTTP_200_OK
        )


    # ======================================================
    # AUXILIAR DE ESTADOS
    # ======================================================

    def _cambiar_estado(self, requerimiento, codigo):

        estado = obtener_estado(codigo)

        if estado:
            requerimiento.estado = estado

        return estado


    # ======================================================
    # 1. RECIBIR Y VALIDAR TICKET  (Jefe de Mantenimiento)
    # ======================================================
    #
    # BPMN: "Recibir Ticket y validar Ticket" -> ¿Ticket válido?
    # NO -> "Notificar rechazo al usuario" -> "Ticket no procede".
    #
    # ======================================================

    @action(detail=True, methods=["post"], url_path="validar-ticket")
    def validar_ticket(self, request, pk=None):

        if not tiene_rol(request.user, "SERVICIOS_GENERALES"):
            return Response(
                {"detalle": "Solo el Jefe de Mantenimiento puede validar el ticket."},
                status=status.HTTP_403_FORBIDDEN
            )

        requerimiento = self.get_object()

        if not estado_permitido(requerimiento, ["RECIBIDO"]):
            return Response(
                {"detalle": "Solo los requerimientos RECIBIDOS pueden validarse."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ahora = timezone.now()

        if request.data.get("es_valido", True) is False:

            motivo = str(request.data.get("motivo_rechazo", "")).strip()

            if not motivo:
                return Response(
                    {"motivo_rechazo": "Debe indicar el motivo del rechazo."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not self._cambiar_estado(requerimiento, "RECHAZADO"):
                return Response({"detalle": "No existe el estado RECHAZADO."}, status=400)

            requerimiento.motivo_rechazo = motivo
            requerimiento.validado_en = ahora
            requerimiento.activo = False
            requerimiento.save()

            registrar_bitacora(
                request=request,
                accion="RECHAZAR_REQUERIMIENTO_MANTENIMIENTO",
                modulo="Mantenimiento",
                detalle=f"Se rechazó {requerimiento.codigo}: {motivo}",
                nivel="WARNING",
            )

            return respuesta_requerimiento(
                requerimiento, "Ticket rechazado y notificado al solicitante.", request
            )

        faltantes = [nombre for campo, nombre in [('titulo', 'título'), ('descripcion', 'descripción'), ('ubicacion', 'ubicación')]
                     if not str(getattr(requerimiento, campo, '')).strip() or (campo == 'ubicacion' and str(requerimiento.ubicacion).strip().lower() in {'no especificado', 'sin especificar'})]
        if not (requerimiento.evidencia_archivo or requerimiento.evidencia.strip()):
            faltantes.append('evidencia')
        if faltantes:
            return Response({'detalle': 'Faltan requisitos: ' + ', '.join(faltantes), 'requisitos_faltantes': faltantes}, status=400)

        if not self._cambiar_estado(requerimiento, "VALIDADO"):
            return Response({"detalle": "No existe el estado VALIDADO."}, status=400)

        requerimiento.responsable_servicios_generales = request.user
        requerimiento.validado_en = ahora
        requerimiento.recibido_en = requerimiento.recibido_en or ahora
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="VALIDAR_REQUERIMIENTO_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"Se recibió y validó {requerimiento.codigo}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento, "Ticket recibido y validado correctamente.", request
        )


    # ======================================================
    # 2. CLASIFICAR PRIORIDAD  (Jefe de Mantenimiento)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="clasificar-prioridad")
    def clasificar_prioridad(self, request, pk=None):

        if not tiene_rol(request.user, "SERVICIOS_GENERALES"):
            return Response(
                {"detalle": "Solo el Jefe de Mantenimiento puede clasificar la prioridad."},
                status=status.HTTP_403_FORBIDDEN
            )

        requerimiento = self.get_object()

        if not estado_permitido(requerimiento, ["VALIDADO"]):
            return Response(
                {"detalle": "El requerimiento debe estar VALIDADO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        prioridad = str(request.data.get("prioridad", "")).strip().upper()
        from config.reglas import prioridad_objeto
        prioridad = prioridad_objeto(requerimiento) or prioridad
        criterio = str(request.data.get("criterio_prioridad", "")).strip()

        if prioridad not in {"BAJA", "MEDIA", "ALTA", "URGENTE"}:
            return Response(
                {"prioridad": "Seleccione BAJA, MEDIA, ALTA o URGENTE."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not criterio:
            return Response(
                {"criterio_prioridad": "Debe justificar la prioridad asignada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        requerimiento.prioridad_jefatura = prioridad
        requerimiento.criterio_prioridad = criterio
        requerimiento.clasificado_en = timezone.now()

        requerimiento.save(update_fields=[
            "prioridad_jefatura", "criterio_prioridad",
            "clasificado_en", "actualizado_en",
        ])

        registrar_bitacora(
            request=request,
            accion="CLASIFICAR_PRIORIDAD_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"{requerimiento.codigo} clasificado como {prioridad}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento, f"Prioridad {prioridad} registrada.", request
        )


    # ======================================================
    # 3. DESIGNAR REVISIÓN AL EQUIPO  (Jefe de Mantenimiento)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="designar-revision")
    @transaction.atomic
    def designar_revision(self, request, pk=None):

        if not tiene_rol(request.user, "SERVICIOS_GENERALES"):
            return Response(
                {"detalle": "Solo el Jefe de Mantenimiento puede designar al técnico."},
                status=status.HTTP_403_FORBIDDEN
            )

        requerimiento = self.get_object()
        requerimiento = RequerimientoMantenimiento.objects.select_for_update().get(pk=requerimiento.pk)

        if not estado_permitido(requerimiento, ["VALIDADO"]):
            return Response(
                {"detalle": "El requerimiento debe estar VALIDADO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not requerimiento.clasificado_en:
            return Response(
                {"detalle": "Primero debe clasificar la prioridad."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tecnico_id = request.data.get("tecnico_id") or request.data.get("auxiliar_id")

        if not tecnico_id:
            return Response(
                {"tecnico_id": "Debe seleccionar al técnico responsable."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tecnico = Usuario.objects.get(id=tecnico_id, is_active=True)
        except (Usuario.DoesNotExist, TypeError, ValueError):
            return Response(
                {"tecnico_id": "El técnico seleccionado no existe o está inactivo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tiene_rol_tecnico = (
            UsuarioRol.objects
            .filter(
                usuario=tecnico,
                activo=True,
                rol__activo=True,
                rol__codigo="AUXILIAR_SERVICIOS_GENERALES",
            )
            .exists()
        )

        if not tiene_rol_tecnico:
            return Response(
                {"tecnico_id": "El usuario seleccionado no es Técnico de Mantenimiento."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # R07: mismo cupo global de técnicos; la fila Usuario serializa asignaciones.
        from soporte.carga_tecnica import bloquear_y_validar
        bloquear_y_validar([tecnico.pk], excluir_mantenimiento=requerimiento.pk)

        if not self._cambiar_estado(requerimiento, "DERIVADO"):
            return Response({"detalle": "No existe el estado DERIVADO."}, status=400)

        requerimiento.auxiliar_asignado = tecnico
        requerimiento.derivado_en = timezone.now()
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="DESIGNAR_REVISION_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"{requerimiento.codigo} designado a {tecnico.nombre_completo}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento, "Técnico designado correctamente.", request
        )


    # ======================================================
    # 4. INSPECCIÓN TÉCNICA Y DIAGNÓSTICO  (Técnico)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="registrar-diagnostico")
    def registrar_diagnostico(self, request, pk=None):

        requerimiento = self.get_object()

        if not (
            es_admin(request.user)
            or requerimiento.auxiliar_asignado_id == request.user.id
        ):
            return Response(
                {"detalle": "Solo el técnico asignado puede registrar el diagnóstico."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not estado_permitido(requerimiento, ["DERIVADO"]):
            return Response(
                {"detalle": "El requerimiento debe estar DERIVADO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        diagnostico = str(request.data.get("diagnostico", "")).strip()
        plan = str(request.data.get("plan_solucion", "")).strip()

        if not diagnostico:
            return Response({"diagnostico": "Debe registrar el diagnóstico."}, status=400)

        if not plan:
            return Response({"plan_solucion": "Debe registrar el plan de solución."}, status=400)

        ahora = timezone.now()

        requerimiento.diagnostico = diagnostico
        requerimiento.plan_solucion = plan
        requerimiento.diagnosticado_en = ahora

        # Compuerta "¿Requiere compra?" -> NO: sigue a la intervención.
        self._cambiar_estado(requerimiento, "EN_MANTENIMIENTO")
        requerimiento.inicio_mantenimiento_en = ahora
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="REGISTRAR_DIAGNOSTICO_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"Se registró la inspección y diagnóstico de {requerimiento.codigo}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Diagnóstico registrado. Puede realizar el mantenimiento.",
            request
        )


    # ======================================================
    # 5. REALIZAR REQUERIMIENTO  (Técnico)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="solicitar-requerimiento")
    def solicitar_requerimiento(self, request, pk=None):
        return self._guardar_requerimiento_compra(request, pk, borrador=False)

    @action(detail=True, methods=["post"], url_path="guardar-borrador-requerimiento")
    def guardar_borrador_requerimiento(self, request, pk=None):
        return self._guardar_requerimiento_compra(request, pk, borrador=True)

    @staticmethod
    def _archivos_cotizacion_r02(requerimiento):
        """Devuelve rutas únicas, incluyendo la cotización histórica."""
        archivos = {}
        if requerimiento.cotizacion_archivo:
            archivos[requerimiento.cotizacion_archivo.name] = requerimiento.cotizacion_archivo
        for cotizacion in requerimiento.cotizaciones_r02.all():
            if cotizacion.archivo:
                archivos[cotizacion.archivo.name] = cotizacion.archivo
        return archivos

    @staticmethod
    def _cantidad_requerida_r02(costo):
        from compras.reglas_cotizaciones import requeridas
        return requeridas(costo)

    @staticmethod
    def _validar_archivos_r02(archivos):
        extensiones = (".pdf", ".jpg", ".jpeg", ".png", ".webp")
        for archivo in archivos:
            if not archivo.name.lower().endswith(extensiones):
                return "Las cotizaciones deben ser PDF, JPG, PNG o WEBP."
            if archivo.size > 10 * 1024 * 1024:
                return "Cada cotización debe tener un tamaño máximo de 10 MB."
            if archivo.size == 0:
                return "No se permiten cotizaciones vacías."
        return None

    @transaction.atomic
    def _guardar_requerimiento_compra(self, request, pk, borrador):
        requerimiento = self.get_object()
        requerimiento = RequerimientoMantenimiento.objects.select_for_update().get(pk=requerimiento.pk)
        if not (es_admin(request.user) or requerimiento.auxiliar_asignado_id == request.user.id):
            return Response({"detalle": "Solo el técnico asignado puede realizar el requerimiento."}, status=403)
        if not estado_permitido(requerimiento, ["DERIVADO", "EN_MANTENIMIENTO"]):
            return Response({"detalle": "El requerimiento debe estar en atención técnica."}, status=400)
        if requerimiento.estado_compra_componente:
            return Response({"detalle": "Este requerimiento ya tiene una compra en curso."}, status=409)

        producto = str(request.data.get("producto_requerido", "")).strip()
        if not producto and not borrador:
            return Response({"producto_requerido": "Indique el componente requerido."}, status=400)
        try:
            cantidad = int(request.data.get("cantidad_requerida") or 1)
        except (TypeError, ValueError):
            return Response({"cantidad_requerida": "Cantidad inválida."}, status=400)
        if cantidad <= 0:
            return Response({"cantidad_requerida": "La cantidad debe ser mayor a cero."}, status=400)
        costo_raw = request.data.get("costo_estimado")
        try:
            costo = Decimal(str(costo_raw)) if costo_raw not in (None, "") else None
        except (InvalidOperation, TypeError):
            return Response({"costo_estimado": "Monto estimado inválido."}, status=400)
        if costo is not None and (not costo.is_finite() or costo < 0):
            return Response({"costo_estimado": "El monto debe ser un número no negativo."}, status=400)
        if not borrador and costo is None:
            return Response({"costo_estimado": "Indique el costo estimado antes de enviar."}, status=400)

        from config.reglas import monto_valido, error_limite
        from compras.reglas_cotizaciones import nuevas_cotizaciones, validar_cotizaciones, guardar_cotizaciones, actualizar_proveedores
        costo = monto_valido(costo_raw, requerido=not borrador)
        # La vía corresponde a DAF; el técnico no puede seleccionarla.
        via = requerimiento.via_compra
        # REQUERIMIENTO 1 (R01): el envío técnico no admite superar el límite.
        error = error_limite(costo, 'CAJA_CHICA')
        if error and not borrador:
            return Response(error, status=400)
        actualizar_proveedores(requerimiento, request)
        nuevos = nuevas_cotizaciones(request)
        if not borrador:
            validar_cotizaciones(requerimiento, costo, nuevos)
        requerimiento.via_compra = via

        requerimiento.requiere_reposicion = True
        requerimiento.producto_requerido = producto
        requerimiento.especificacion_producto = str(request.data.get("especificacion_producto", "")).strip()
        requerimiento.cantidad_requerida = cantidad
        requerimiento.costo_estimado = costo
        if borrador and request.FILES.get("informe_compra"):
            requerimiento.informe_compra = request.FILES["informe_compra"]

        guardar_cotizaciones(requerimiento, nuevos, request.user)

        if not borrador:
            requerimiento.informe_compra.save(
                f"informe-requerimiento-{requerimiento.codigo}.pdf",
                ContentFile(informe_requerimiento_mantenimiento(requerimiento)), save=False,
            )
            requerimiento.estado_compra_componente = "SOLICITADA"
            self._cambiar_estado(requerimiento, "EN_ESPERA_COMPRA")
        requerimiento.save()
        registrar_bitacora(
            request=request,
            accion="GUARDAR_BORRADOR_REQUERIMIENTO_MANTENIMIENTO" if borrador else "SOLICITAR_REQUERIMIENTO_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"{requerimiento.codigo}: {'borrador guardado' if borrador else 'requerimiento enviado'}; {len(self._archivos_cotizacion_r02(requerimiento))} cotización(es).",
            nivel="INFO",
        )
        return respuesta_requerimiento(
            requerimiento,
            "Borrador guardado." if borrador else "Requerimiento enviado al Jefe de Mantenimiento para evaluar su viabilidad.",
            request,
        )

    # ======================================================
    # 6. RECIBIR REQUERIMIENTO Y EVALUAR VIABILIDAD  (Jefe)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="completar-expediente")
    def completar_expediente(self, request, pk=None):
        if not (es_admin(request.user) or tiene_rol(request.user, "SERVICIOS_GENERALES")):
            return Response({"detalle": "Solo la jefatura de la sección puede completar el expediente."}, status=403)
        from compras.expediente import completar_expediente_origen
        return completar_expediente_origen(request, self.get_object(), "requerimiento_mantenimiento")

    @action(detail=True, methods=["get"], url_path=r"informes-pdf/(?P<tipo>tecnico|final)")
    def informe_consulta_pdf(self, request, pk=None, tipo=None):
        from django.http import HttpResponse
        from soporte.informes_pdf import _documento_pdf
        from usuarios.models import DocumentoProceso
        from usuarios.documentos import pdf_documento
        requerimiento = self.get_object()
        titulo = "Informe tecnico de mantenimiento" if tipo == "tecnico" else "Informe final de mantenimiento"
        documento = DocumentoProceso.objects.filter(mantenimiento=requerimiento, tipo=titulo.replace("tecnico", "t\u00e9cnico")).order_by('-creado_en').first()
        if documento:
            return pdf_documento(self, request, pk, documento.pk)
        texto = requerimiento.informe_trabajo if tipo == "tecnico" else requerimiento.informe_final
        if not texto:
            return Response({"detalle": "Este informe todavia no fue elaborado."}, status=404)
        contenido = _documento_pdf(titulo, "Consulta del informe registrado", requerimiento,
            [("DATOS DEL REQUERIMIENTO", [("Solicitante", requerimiento.solicitante.nombre_completo), ("Ubicacion", requerimiento.ubicacion), ("Descripcion", requerimiento.descripcion)]),
             ("CONTENIDO DEL INFORME", [("Informe registrado", texto)])], [("Origen", requerimiento.codigo)], unidad="MANTENIMIENTO")
        respuesta = HttpResponse(contenido, content_type='application/pdf')
        respuesta['Content-Disposition'] = f'inline; filename="informe-{tipo}-{requerimiento.codigo}.pdf"'
        respuesta['Cache-Control'] = 'private, no-store'
        return respuesta

    @action(detail=True, methods=["get"], url_path="informe-requerimiento-pdf")
    def informe_requerimiento_pdf(self, request, pk=None):
        from compras.informes_origen import visualizar_informe_tecnico
        return visualizar_informe_tecnico(self.get_object())

    @action(detail=True, methods=["post"], url_path="validar-viabilidad-compra")
    def validar_viabilidad_compra(self, request, pk=None):
        if not (es_admin(request.user) or tiene_rol(request.user, 'SERVICIOS_GENERALES')):
            return Response({'detalle': 'Solo el Jefe de Mantenimiento puede validar la viabilidad.'}, status=403)
        requerimiento = self.get_object()
        if requerimiento.estado_compra_componente != 'SOLICITADA' or requerimiento.derivado_compra:
            return Response({'detalle': 'La compra no está pendiente de validación.'}, status=400)
        from compras.reglas_cotizaciones import validar_cotizaciones
        validar_cotizaciones(requerimiento)
        from compras.informes_origen import asegurar_informe_tecnico
        informe = asegurar_informe_tecnico(requerimiento)
        cotizacion = requerimiento.cotizacion_archivo
        requeridas = self._cantidad_requerida_r02(requerimiento.costo_estimado)
        if len(self._archivos_cotizacion_r02(requerimiento)) < requeridas:
            return Response({"detalle": f"R02: Se requieren al menos {requeridas} cotizaciones antes de validar."}, status=400)
        if not informe or not cotizacion:
            return Response({'detalle': 'Revise y adjunte el informe técnico y la cotización antes de validar.'}, status=400)
        requerimiento.informe_compra = informe
        requerimiento.cotizacion_archivo = cotizacion
        requerimiento.estado_compra_componente = 'VIABLE'
        requerimiento.save(update_fields=['informe_compra', 'cotizacion_archivo', 'estado_compra_componente', 'actualizado_en'])
        registrar_bitacora(request=request, accion='VALIDAR_VIABILIDAD_MANTENIMIENTO', modulo='Mantenimiento',
                           detalle=f'{requerimiento.codigo}: compra viable, pendiente de POA y proveído.', nivel='INFO')
        return respuesta_requerimiento(requerimiento, 'Viabilidad validada. Adjunte el POA y el proveído para elevar la compra.', request)

    @action(detail=True, methods=["post"], url_path="evaluar-viabilidad-compra")
    @transaction.atomic
    def evaluar_viabilidad_compra(self, request, pk=None):

        if not (es_admin(request.user) or tiene_rol(request.user, "SERVICIOS_GENERALES")):
            return Response(
                {"detalle": "Solo el Jefe de Mantenimiento puede evaluar la viabilidad."},
                status=status.HTTP_403_FORBIDDEN
            )

        requerimiento = self.get_object()

        if requerimiento.estado_compra_componente not in {"SOLICITADA", "VIABLE"} or requerimiento.derivado_compra:
            return Response(
                {"detalle": "Este requerimiento no tiene una compra pendiente de evaluación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        viable_raw = request.data.get("viable")
        viable = viable_raw in [True, "true", "True", 1, "1"] if viable_raw is not None else None

        if viable is None:
            return Response({"viable": "Debe indicar True o False."}, status=400)

        if viable is False:

            motivo = str(request.data.get("motivo_no_viable", "")).strip()

            if not motivo:
                return Response(
                    {"motivo_no_viable": "Debe indicar el motivo de no viabilidad."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not self._cambiar_estado(requerimiento, "CERRADO_SIN_COMPRA"):
                return Response(
                    {"detalle": "No existe el estado CERRADO_SIN_COMPRA."},
                    status=400
                )

            requerimiento.estado_compra_componente = "NO_VIABLE"
            requerimiento.motivo_no_viable = motivo
            requerimiento.activo = False
            requerimiento.save()
            from config.reglas import notificar_rechazo
            notificar_rechazo(requerimiento, motivo)

            registrar_bitacora(
                request=request,
                accion="COMUNICAR_NO_VIABILIDAD_MANTENIMIENTO",
                modulo="Mantenimiento",
                detalle=f"Compra no viable para {requerimiento.codigo}: {motivo}",
                nivel="WARNING",
            )

            return respuesta_requerimiento(
                requerimiento, "Compra no viable. El caso se cerró sin compra.", request
            )

        from compras.models import SolicitudCompra

        from compras.reglas_cotizaciones import validar_cotizaciones
        validar_cotizaciones(requerimiento)
        from compras.informes_origen import asegurar_informe_tecnico
        informe = asegurar_informe_tecnico(requerimiento)
        proforma = requerimiento.cotizacion_archivo
        requeridas = self._cantidad_requerida_r02(requerimiento.costo_estimado)
        if len(self._archivos_cotizacion_r02(requerimiento)) < requeridas:
            return Response({"detalle": f"R02: Se requieren al menos {requeridas} cotizaciones para elevar la compra."}, status=400)
        poa = request.FILES.get("poa")
        pedido = request.FILES.get("pedido")
        if not all((informe, proforma, poa, pedido)):
            return Response({"detalle": "Para elevar a DAF se requieren informe técnico, cotización, POA y proveído de jefatura."}, status=400)

        solicitud = SolicitudCompra.objects.create(
            codigo=SolicitudCompra.generar_codigo(),
            titulo=requerimiento.producto_requerido or f"Reposición {requerimiento.codigo}",
            descripcion=(
                requerimiento.especificacion_producto
                or requerimiento.producto_requerido
                or ""
            ),
            solicitante=request.user,
            area=requerimiento.area,
            tipo="COMPONENTE",
            cantidad=requerimiento.cantidad_requerida or 1,
            especificaciones=requerimiento.especificacion_producto,
            justificacion=f"Requerido para atender el mantenimiento {requerimiento.codigo}.",
            monto_estimado=requerimiento.costo_estimado,
            via_adquisicion=requerimiento.via_compra,
            estado="CREADO_PENDIENTE_DAF",
            origen_modulo="MANTENIMIENTO",
            requerimiento_mantenimiento=requerimiento,
            informe=informe,
            poa=poa,
            proforma=proforma,
            pedido=pedido,
        )

        from compras.reglas_cotizaciones import transferir_cotizaciones
        transferir_cotizaciones(requerimiento, solicitud, request.user)

        requerimiento.estado_compra_componente = "VIABLE"
        requerimiento.derivado_compra = True
        requerimiento.codigo_compra_vinculada = solicitud.codigo
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="ELEVAR_INFORME_COMPRA_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=(
                f"El Jefe de Mantenimiento elevó el informe de {requerimiento.codigo} "
                f"a la DAF. Expediente {solicitud.codigo}."
            ),
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            f"Informe elevado a la DAF. Expediente de compra {solicitud.codigo}.",
            request
        )


    # ======================================================
    # 7. REPARACIÓN O INSTALACIÓN  (Técnico)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="recibir-componente-acta")
    def recibir_componente_acta(self, request, pk=None):
        """El técnico asignado acepta formalmente el componente y el acta
        enviados por Almacén antes de iniciar la reparación."""

        requerimiento = self.get_object()

        if not (
            es_admin(request.user)
            or requerimiento.auxiliar_asignado_id == request.user.id
        ):
            return Response(
                {"detalle": "Solo el técnico asignado puede recibir el componente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if requerimiento.estado_compra_componente != "PENDIENTE_RECEPCION_TECNICO":
            return Response(
                {"detalle": "No hay un componente pendiente de recepción."},
                status=status.HTTP_409_CONFLICT,
            )

        compra = requerimiento.compras_generadas.order_by("-creado_en").first()
        if not compra or not compra.acta_conformidad:
            return Response(
                {"detalle": "La entrega aún no cuenta con un acta de conformidad."},
                status=status.HTTP_409_CONFLICT,
            )

        if not self._cambiar_estado(requerimiento, "EN_MANTENIMIENTO"):
            return Response({"detalle": "No existe el estado EN_MANTENIMIENTO."}, status=400)

        requerimiento.estado_compra_componente = "ENTREGADA"
        requerimiento.componente_recibido_por = (
            request.user.nombre_completo or request.user.email
        )
        requerimiento.componente_recibido_en = timezone.now()
        requerimiento.observacion_recepcion_componente = str(
            request.data.get("observacion_recepcion_componente", "")
        ).strip()
        requerimiento.inicio_mantenimiento_en = requerimiento.componente_recibido_en
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="RECIBIR_COMPONENTE_Y_ACTA_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=(
                f"El técnico recibió el componente y acta de {compra.codigo} "
                f"para {requerimiento.codigo}."
            ),
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Recepción registrada. Ya puede realizar la reparación y las pruebas.",
            request,
        )


    @action(detail=True, methods=["post"], url_path="realizar-mantenimiento")
    def realizar_mantenimiento(self, request, pk=None):

        requerimiento = self.get_object()

        if not (
            es_admin(request.user)
            or requerimiento.auxiliar_asignado_id == request.user.id
        ):
            return Response(
                {"detalle": "Solo el técnico asignado puede registrar el mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not estado_permitido(requerimiento, ["EN_MANTENIMIENTO"]):
            return Response(
                {"detalle": "El requerimiento no se encuentra EN MANTENIMIENTO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # El trabajo queda en pausa mientras el componente esté en compra.
        if requerimiento.estado_compra_componente in ("SOLICITADA", "VIABLE"):
            return Response(
                {
                    "detalle": (
                        "El componente todavía no fue entregado: el expediente "
                        f"{requerimiento.codigo_compra_vinculada or 'de compra'} "
                        "sigue en proceso."
                    )
                },
                status=status.HTTP_409_CONFLICT
            )

        trabajo = str(request.data.get("trabajo_realizado", "")).strip()

        if not trabajo:
            return Response(
                {"trabajo_realizado": "Debe registrar el trabajo realizado."},
                status=400
            )

        requerimiento.trabajo_realizado = trabajo
        requerimiento.observaciones_trabajo = str(
            request.data.get("observaciones_trabajo", "")
        ).strip()

        requerimiento.save(update_fields=[
            "trabajo_realizado", "observaciones_trabajo", "actualizado_en",
        ])

        registrar_bitacora(
            request=request,
            accion="REALIZAR_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"Se registró el trabajo realizado en {requerimiento.codigo}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento, "Trabajo de mantenimiento registrado correctamente.", request
        )


    # ======================================================
    # 8. PRUEBAS TÉCNICAS  (Técnico)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="pruebas-tecnicas")
    def pruebas_tecnicas(self, request, pk=None):

        requerimiento = self.get_object()

        if not (
            es_admin(request.user)
            or requerimiento.auxiliar_asignado_id == request.user.id
        ):
            return Response(
                {"detalle": "Solo el técnico asignado puede registrar las pruebas."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not estado_permitido(requerimiento, ["EN_MANTENIMIENTO"]):
            return Response(
                {"detalle": "El requerimiento no se encuentra EN MANTENIMIENTO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not requerimiento.trabajo_realizado:
            return Response(
                {"detalle": "Primero debe registrar la reparación o instalación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resultado = str(request.data.get("resultado_pruebas", "")).strip()

        if not resultado:
            return Response(
                {"resultado_pruebas": "Debe registrar el resultado de las pruebas técnicas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        requerimiento.resultado_pruebas = resultado
        requerimiento.pruebas_en = timezone.now()

        requerimiento.save(update_fields=[
            "resultado_pruebas", "pruebas_en", "actualizado_en",
        ])

        registrar_bitacora(
            request=request,
            accion="REALIZAR_PRUEBAS_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"Se registraron las pruebas técnicas de {requerimiento.codigo}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento, "Pruebas técnicas registradas correctamente.", request
        )


    # ======================================================
    # 9. REGISTRAR INFORME AL JEFE DE MANTENIMIENTO  (Técnico)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="registrar-informe")
    @documentar('Informe técnico de mantenimiento')
    def registrar_informe(self, request, pk=None):

        requerimiento = self.get_object()

        if not (
            es_admin(request.user)
            or requerimiento.auxiliar_asignado_id == request.user.id
        ):
            return Response(
                {"detalle": "Solo el técnico asignado puede registrar el informe."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not estado_permitido(requerimiento, ["EN_MANTENIMIENTO"]):
            return Response(
                {"detalle": "El requerimiento debe estar EN MANTENIMIENTO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not requerimiento.resultado_pruebas:
            return Response(
                {"detalle": "Primero debe registrar las pruebas técnicas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        informe = str(request.data.get("informe_trabajo", "")).strip()

        if not informe:
            return Response(
                {"informe_trabajo": "Debe registrar el informe del trabajo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        requerimiento.informe_trabajo = informe

        fotografia = request.FILES.get("fotografia_trabajo")

        if fotografia:
            requerimiento.fotografia_trabajo = fotografia

        if not self._cambiar_estado(requerimiento, "INFORME_REGISTRADO"):
            return Response({"detalle": "No existe el estado INFORME_REGISTRADO."}, status=400)

        requerimiento.informe_registrado_en = timezone.now()
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="REGISTRAR_INFORME_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=(
                f"El técnico registró el informe de {requerimiento.codigo} "
                "para el Jefe de Mantenimiento."
            ),
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Informe registrado. La jefatura verificará el funcionamiento.",
            request
        )


    # ======================================================
    # 10. VERIFICAR FUNCIONAMIENTO  (Solicitante)
    # ======================================================
    #
    # BPMN: ¿Problema resuelto? NO -> el caso vuelve a la atención
    # técnica; SÍ -> se informa la conformidad.
    #
    # ======================================================

    @action(detail=True, methods=["post"], url_path="verificar-funcionamiento")
    @documentar('Verificación y conformidad de mantenimiento', solo_conforme=True)
    def verificar_funcionamiento(self, request, pk=None):

        requerimiento = self.get_object()

        es_solicitante = requerimiento.solicitante_id == request.user.id
        if not es_solicitante:
            return Response(
                {"detalle": "Solo el solicitante puede verificar y registrar su conformidad."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not estado_permitido(requerimiento, ["INFORME_REGISTRADO"]):
            return Response(
                {"detalle": "El requerimiento debe tener el informe del técnico registrado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resuelto = request.data.get("problema_resuelto")

        if resuelto not in [True, False]:
            return Response({"problema_resuelto": "Debe indicar True o False."}, status=400)

        observaciones = str(request.data.get('observaciones', '')).strip()
        if es_solicitante and requerimiento.conformidad_solicitante is True:
            return Response({'detalle': 'Su conformidad ya fue registrada.'}, status=409)
        if resuelto is False and not observaciones:
            return Response({'observaciones': 'Debe indicar por qué el problema continúa.'}, status=400)
        ahora = timezone.now()
        if es_solicitante:
            requerimiento.conformidad_solicitante = resuelto
            requerimiento.conformidad_solicitante_en = ahora
            requerimiento.observaciones_conformidad = observaciones

        requerimiento.verificado_en = ahora

        if resuelto is False:

            # Ciclo de retroalimentación: vuelve a la atención técnica.
            self._cambiar_estado(requerimiento, "EN_MANTENIMIENTO")
            requerimiento.rework_count += 1
            requerimiento.resultado_pruebas = ""
            requerimiento.trabajo_realizado = ""
            requerimiento.pruebas_en = None
            requerimiento.verificado_en = None
            requerimiento.conformidad_en = None
            requerimiento.informe_elevado_en = None
            requerimiento.informe_final = ""
            if not es_solicitante:
                requerimiento.conformidad_solicitante = None
                requerimiento.conformidad_solicitante_en = None
            requerimiento.save()

            registrar_bitacora(
                request=request,
                accion="VERIFICACION_NO_CONFORME_MANTENIMIENTO",
                modulo="Mantenimiento",
                detalle=(
                    f"{requerimiento.codigo}: el problema no fue resuelto; "
                    "vuelve a la atención técnica."
                ),
                nivel="WARNING",
            )

            return respuesta_requerimiento(
                requerimiento,
                "El problema no fue resuelto. El caso volvió al técnico.",
                request
            )

        if not self._cambiar_estado(requerimiento, "CONFORMIDAD_INFORMADA"):
            return Response({"detalle": "No existe el estado CONFORMIDAD_INFORMADA."}, status=400)
        requerimiento.conformidad_en = ahora
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="VERIFICAR_FUNCIONAMIENTO_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=f"Se verificó el funcionamiento de {requerimiento.codigo}.",
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Conformidad registrada por el solicitante. La jefatura puede elaborar el informe final.",
            request
        )


    # ======================================================
    # 11. INFORMAR CONFORMIDAD  (Solicitante)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="informar-conformidad")
    def informar_conformidad(self, request, pk=None):

        requerimiento = self.get_object()
        if requerimiento.solicitante_id != request.user.id:
            return Response(
                {"detalle": "Solo el solicitante puede informar la conformidad."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if requerimiento.conformidad_solicitante is not True:
            return Response({'detalle': 'Está pendiente la conformidad explícita del solicitante.'}, status=409)

        if not requerimiento.verificado_en:
            return Response(
                {"detalle": "Primero debe verificar el funcionamiento."},
                status=status.HTTP_409_CONFLICT
            )

        if not estado_permitido(requerimiento, ["INFORME_REGISTRADO"]):
            return Response(
                {"detalle": "El requerimiento no está en condiciones de informar conformidad."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not self._cambiar_estado(requerimiento, "CONFORMIDAD_INFORMADA"):
            return Response({"detalle": "No existe el estado CONFORMIDAD_INFORMADA."}, status=400)

        requerimiento.conformidad_en = timezone.now()
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="INFORMAR_CONFORMIDAD_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=(
                f"Se informó la conformidad del mantenimiento {requerimiento.codigo}."
            ),
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Conformidad informada. Elabore el informe final.",
            request
        )


    # ======================================================
    # 12. ELABORAR Y VALIDAR INFORME FINAL  (Jefe)
    # ======================================================

    @action(detail=True, methods=["post"], url_path="elaborar-informe-final")
    @documentar('Informe final de mantenimiento')
    def elaborar_informe_final(self, request, pk=None):

        if not (es_admin(request.user) or tiene_rol(request.user, "SERVICIOS_GENERALES")):
            return Response(
                {"detalle": "Solo el Jefe de Mantenimiento puede elaborar el informe final."},
                status=status.HTTP_403_FORBIDDEN
            )

        requerimiento = self.get_object()

        if requerimiento.conformidad_solicitante is not True:
            return Response(
                {"detalle": "Esta pendiente la conformidad del solicitante."},
                status=status.HTTP_409_CONFLICT,
            )
        # Expedientes anteriores pueden tener la respuesta registrada sin
        # haber avanzado aun al estado de informe final.
        if estado_permitido(requerimiento, ["INFORME_REGISTRADO"]) and requerimiento.verificado_en:
            if not self._cambiar_estado(requerimiento, "CONFORMIDAD_INFORMADA"):
                return Response({"detalle": "No existe el estado CONFORMIDAD_INFORMADA."}, status=400)
            requerimiento.conformidad_en = requerimiento.conformidad_solicitante_en

        if not estado_permitido(requerimiento, ["CONFORMIDAD_INFORMADA"]):
            return Response(
                {"detalle": "Primero debe informarse la conformidad del mantenimiento."},
                status=status.HTTP_400_BAD_REQUEST
            )

        informe = str(request.data.get("informe_final", "")).strip()

        if not informe:
            return Response(
                {"informe_final": "Debe elaborar el informe final."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ahora = timezone.now()

        requerimiento.informe_final = informe
        requerimiento.informe_elevado_en = ahora
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="ELABORAR_INFORME_FINAL_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=(
                f"Se elaboró y validó el informe final de {requerimiento.codigo} "
                "y fue elevado a la Dirección."
            ),
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Informe final validado y elevado a la Dirección.",
            request
        )


    # ======================================================
    # 13. RECIBIR INFORME DE ACTIVIDADES  (Dirección) -> FIN
    # ======================================================

    @action(detail=True, methods=["post"], url_path="recibir-informe")
    def recibir_informe(self, request, pk=None):

        if not (es_admin(request.user) or tiene_rol(request.user, "DIRECTOR")):
            return Response(
                {"detalle": "Solo la Dirección puede recibir el informe de actividades."},
                status=status.HTTP_403_FORBIDDEN
            )

        requerimiento = self.get_object()

        if not requerimiento.informe_elevado_en:
            return Response(
                {"detalle": "La jefatura todavía no elevó el informe final."},
                status=status.HTTP_409_CONFLICT
            )

        if requerimiento.informe_recibido_director_en:
            return Response(
                {"detalle": "Usted ya recibió este informe."},
                status=status.HTTP_409_CONFLICT
            )

        ahora = timezone.now()

        if not self._cambiar_estado(requerimiento, "FINALIZADO"):
            return Response({"detalle": "No existe el estado FINALIZADO."}, status=400)

        requerimiento.informe_recibido_director_en = ahora
        requerimiento.proceso_finalizado_en = ahora
        requerimiento.finalizado_en = ahora
        requerimiento.save()

        registrar_bitacora(
            request=request,
            accion="RECIBIR_INFORME_ACTIVIDADES_MANTENIMIENTO",
            modulo="Mantenimiento",
            detalle=(
                f"La Dirección recibió el informe de {requerimiento.codigo}: "
                "el proceso de mantenimiento quedó cerrado."
            ),
            nivel="INFO",
        )

        return respuesta_requerimiento(
            requerimiento,
            "Informe recibido. El proceso de mantenimiento quedó cerrado.",
            request
        )


    # ======================================================
    # 7. REPORTE MENSUAL
    # ======================================================
    #
    # BPMN: "A fin de mes se da a conocer todos los
    # mantenimientos" -> "Director recibe los reportes".
    # Consolidado real por periodo (no un filtro de texto
    # en el frontend).
    #
    # ======================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="reporte-mensual"
    )
    def reporte_mensual(
        self,
        request
    ):

        if not (
            es_admin(request.user)
            or
            tiene_rol(
                request.user,
                "SERVICIOS_GENERALES",
                "DIRECTOR",
            )
        ):

            return Response(
                {
                    "detalle": (
                        "No tiene permiso para consultar "
                        "el reporte mensual de mantenimiento."
                    )
                },
                status=
                    status.HTTP_403_FORBIDDEN
            )


        ahora = timezone.now()

        try:
            anio = int(request.query_params.get("anio", ahora.year))
            mes = int(request.query_params.get("mes", ahora.month))
        except ValueError:
            return Response(
                {"detalle": "Año y mes deben ser numéricos."},
                status=status.HTTP_400_BAD_REQUEST
            )


        queryset = (
            RequerimientoMantenimiento.objects
            .filter(
                estado__codigo="FINALIZADO",
                finalizado_en__year=anio,
                finalizado_en__month=mes,
            )
            .select_related(
                "solicitante",
                "area",
                "responsable_servicios_generales",
                "auxiliar_asignado",
            )
            .order_by("-finalizado_en")
        )

        serializer = RequerimientoMantenimientoSerializer(
            queryset,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "anio": anio,
                "mes": mes,
                "total_finalizados": queryset.count(),
                "requerimientos": serializer.data,
            }
        )
