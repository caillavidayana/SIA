from django.conf import settings
from usuarios.documentos import documentar, documentos_expediente, pdf_documento
from rest_framework import (
    status,
    viewsets,
)

from usuarios.authentication import (
    ExpiringTokenAuthentication as TokenAuthentication,
)

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation


from usuarios.models import RolPermiso, obtener_codigos_rol_efectivos

from auditoria.utils import registrar_bitacora


from .models import (
    SolicitudCompra,
)

from .serializers import (
    SolicitudCompraSerializer,
)


# ==========================================================
# AUXILIAR
# ==========================================================

def obtener_roles(usuario):

    # Incluye roles delegados temporalmente (Delegar aprobación
    # temporal) además de los roles propios.
    return obtener_codigos_rol_efectivos(usuario)


def es_admin(usuario):

    if usuario.is_superuser:
        return True

    return (
        "ADMIN"
        in obtener_roles(usuario)
    )


def tiene_permiso(usuario, codigo_permiso):
    """Autorización real de Compras: sigue el mismo patrón de
    Permiso/RolPermiso ya usado en Soporte, en vez de comprobar
    el código de rol a mano en cada acción. Incluye roles
    delegados temporalmente y vigentes (obtener_roles)."""

    if es_admin(usuario):
        return True

    codigos_rol = obtener_roles(usuario)

    return (
        RolPermiso.objects
        .filter(
            rol__codigo__in=codigos_rol,
            rol__activo=True,
            permiso__codigo=codigo_permiso,
            permiso__activo=True,
            activo=True,
        )
        .exists()
    )


def liberar_origen(solicitud, motivo, request):
    from .caja_chica import liberar
    liberar(solicitud)
    """Un expediente rechazado deja sin efecto la compra, pero el ticket o
    el requerimiento que lo originó seguía esperando el componente. Aquí se
    les devuelve el control: quedan marcados como NO_VIABLE y vuelven a la
    atención técnica para que el área decida cómo continuar."""

    ticket = solicitud.ticket_soporte

    if ticket and ticket.estado_compra_componente in ("SOLICITADA", "VIABLE"):

        from soporte.models import EstadoTicket

        ticket.estado_compra_componente = "NO_VIABLE"
        ticket.motivo_no_viable = motivo

        estado = EstadoTicket.objects.filter(codigo="EN_EJECUCION", activo=True).first()

        if estado:
            ticket.estado = estado

        ticket.save()
        from config.reglas import notificar_rechazo
        notificar_rechazo(ticket, motivo)

        registrar_bitacora(
            request=request,
            accion="LIBERAR_TICKET_POR_COMPRA_RECHAZADA",
            modulo="Compras",
            detalle=(
                f"{solicitud.codigo} fue rechazado: el ticket {ticket.codigo} "
                "vuelve a la atención técnica sin el componente."
            ),
            nivel="WARNING",
        )

    requerimiento = solicitud.requerimiento_mantenimiento

    if requerimiento and requerimiento.estado_compra_componente in ("SOLICITADA", "VIABLE"):

        from mantenimiento.models import EstadoMantenimiento

        requerimiento.estado_compra_componente = "NO_VIABLE"
        requerimiento.motivo_no_viable = motivo

        estado = EstadoMantenimiento.objects.filter(
            codigo="EN_MANTENIMIENTO", activo=True
        ).first()

        if estado:
            requerimiento.estado = estado

        requerimiento.save()
        from config.reglas import notificar_rechazo
        notificar_rechazo(requerimiento, motivo)

        registrar_bitacora(
            request=request,
            accion="LIBERAR_REQUERIMIENTO_POR_COMPRA_RECHAZADA",
            modulo="Compras",
            detalle=(
                f"{solicitud.codigo} fue rechazado: el requerimiento "
                f"{requerimiento.codigo} vuelve a la atención técnica."
            ),
            nivel="WARNING",
        )


def respuesta_sin_permiso(codigo_permiso):
    return Response(
        {
            "detalle": "No tiene permiso para realizar esta actividad.",
            "permiso_requerido": codigo_permiso,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


# ==========================================================
# SOLICITUDES DE COMPRA
# ==========================================================

class SolicitudCompraViewSet(
    viewsets.ModelViewSet
):

    @action(detail=True, methods=['get', 'post'], url_path='actas-almacen')
    def actas_almacen(self, request, pk=None):
        from .actas_almacen import actas
        return actas(self, request)

    @action(detail=True, methods=['get'], url_path=r'actas-almacen/(?P<acta_id>[0-9]+)/(?P<clase>original|firmado)')
    def archivo_acta_almacen(self, request, pk=None, acta_id=None, clase=None):
        from .actas_almacen import archivo_acta
        return archivo_acta(self, request, acta_id, clase)

    @action(detail=True, methods=['get', 'post'], url_path='recibos-tesoreria')
    def recibos_tesoreria(self, request, pk=None):
        from .tesoreria import recibos
        return recibos(self, request)

    @action(detail=True, methods=['get'], url_path=r'recibos-tesoreria/(?P<recibo_id>[0-9]+)/(?P<clase>original|firmado|comprobante|constancia_saldo)')
    def archivo_recibo_tesoreria(self, request, pk=None, recibo_id=None, clase=None):
        from .tesoreria import archivo_recibo
        return archivo_recibo(self, request, recibo_id, clase)

    @action(detail=True, methods=['get'], url_path='documentos')
    def documentos(self, request, pk=None):
        return documentos_expediente(self, request, pk)

    @action(detail=True, methods=['get'], url_path=r'documentos/(?P<documento_id>[0-9]+)/pdf')
    def documento_pdf(self, request, pk=None, documento_id=None):
        return pdf_documento(self, request, pk, documento_id)

    @action(detail=True, methods=['get'], url_path=r'cotizaciones/(?P<cotizacion_id>[0-9]+)/archivo')
    def archivo_cotizacion(self, request, pk=None, cotizacion_id=None):
        from django.http import FileResponse
        from django.shortcuts import get_object_or_404
        solicitud = self.get_object()
        cotizacion = get_object_or_404(solicitud.cotizaciones, pk=cotizacion_id)
        respuesta = FileResponse(cotizacion.documento.open('rb'), as_attachment=True)
        respuesta['Cache-Control'] = 'private, no-store'
        respuesta['X-Content-Type-Options'] = 'nosniff'
        return respuesta

    @action(detail=True, methods=['get', 'post'], url_path='cotizaciones')
    def cotizaciones(self, request, pk=None):
        from .cotizaciones import CotizacionCompraSerializer
        solicitud = self.get_object()
        if request.method == 'GET':
            return Response(CotizacionCompraSerializer(solicitud.cotizaciones.order_by('creado_en'), many=True, context={'request': request}).data)
        if not es_admin(request.user):
            return Response({'detalle': 'No tiene permiso para registrar cotizaciones.'}, status=403)
        if solicitud.estado not in {'CREADO_PENDIENTE_DAF', 'EVALUADO_PENDIENTE_CERTIFICACION', 'FONDOS_DESEMBOLSADOS'}:
            return Response({'detalle': 'La etapa actual no permite registrar cotizaciones.'}, status=409)
        serializer = CotizacionCompraSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            type(solicitud).objects.select_for_update().get(pk=solicitud.pk)
            serializer.save(solicitud=solicitud, creada_por=request.user)
            registrar_bitacora(request=request, accion='REGISTRAR_COTIZACION', modulo='Compras', detalle=f'{solicitud.codigo}: cotización {serializer.instance.pk} registrada.', nivel='INFO')
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'], url_path='seleccionar-cotizacion')
    @transaction.atomic
    def seleccionar_cotizacion(self, request, pk=None):
        from .models import CotizacionCompra
        solicitud = self.get_object()
        solicitud = type(solicitud).objects.select_for_update().get(pk=solicitud.pk)
        if not (tiene_permiso(request.user, 'REALIZAR_COMPRA') or tiene_permiso(request.user, 'EVALUAR_EXPEDIENTE')):
            return Response({'detalle': 'No tiene permiso para seleccionar cotizaciones.'}, status=403)
        if solicitud.estado not in {'CREADO_PENDIENTE_DAF', 'EVALUADO_PENDIENTE_CERTIFICACION', 'FONDOS_DESEMBOLSADOS'}:
            return Response({'detalle': 'La etapa actual no permite cambiar la cotización.'}, status=409)
        try:
            cotizacion = solicitud.cotizaciones.get(pk=request.data.get('cotizacion_id'))
        except (CotizacionCompra.DoesNotExist, ValueError, TypeError):
            return Response({'detalle': 'Seleccione una cotización de este expediente.'}, status=400)
        motivo = str(request.data.get('motivo', '')).strip()
        if not motivo:
            return Response({'detalle': 'Registre el motivo de selección.'}, status=400)
        solicitud.cotizaciones.filter(seleccionada=True).update(seleccionada=False)
        cotizacion.seleccionada = True
        cotizacion.save(update_fields=['seleccionada'])
        registrar_bitacora(request=request, accion='SELECCIONAR_COTIZACION', modulo='Compras', detalle=f'{solicitud.codigo}: cotización {cotizacion.pk}. Motivo: {motivo}', nivel='INFO')
        return Response({'detalle': 'Cotización seleccionada por el responsable autorizado.'})

    serializer_class = (
        SolicitudCompraSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    # ======================================================
    # CONSULTA
    # ======================================================

    def get_queryset(self):

        usuario = self.request.user


        queryset = (
            SolicitudCompra.objects
            .select_related(
                "solicitante",
                "area"
            )
            .prefetch_related('cotizaciones')
            .order_by(
                "-creado_en"
            )
        )


        if self.action == 'list' and self.request.query_params.get('tesoreria') == '1' and tiene_permiso(usuario, 'REGISTRAR_DESEMBOLSO'):
            from django.db.models import OuterRef, Subquery
            from django.db.models.functions import Coalesce
            from usuarios.models import DocumentoProceso
            from .models import ReciboTesoreria
            recibo = ReciboTesoreria.objects.filter(solicitud_id=OuterRef('pk'), confirmado_en__isnull=False).order_by('-confirmado_en')
            constancia = DocumentoProceso.objects.filter(compra_id=OuterRef('pk'), tipo='Constancia de desembolso').order_by('-creado_en')
            queryset = queryset.annotate(tesoreria_fecha=Coalesce(Subquery(recibo.values('confirmado_en')[:1]), Subquery(constancia.values('creado_en')[:1])))

        if self.action == "list" and self.request.query_params.get("bandeja") == "certificacion":
            queryset = queryset.filter(estado="EVALUADO_PENDIENTE_CERTIFICACION")
            for campo in ("informe", "proforma", "poa"):
                queryset = queryset.exclude(**{campo: ""}).exclude(**{campo + "__isnull": True})
            from django.db.models import Q
            queryset = queryset.exclude(Q(origen_modulo__in=["SOPORTE", "MANTENIMIENTO"]) & (Q(pedido="") | Q(pedido__isnull=True)))

        if self.action == "list" and self.request.query_params.get("bandeja") == "direccion":
            queryset = queryset.exclude(solicitante=usuario)

        # Actores del BPMN consultan la bandeja institucional. La DAF
        # recibe directamente la solicitud de compra (no existe una
        # jefatura que se la asigne previamente), así que ve la misma
        # bandeja que el resto de los actores del proceso.
        if tiene_permiso(usuario, "VER_COMPRAS"):
            return queryset


        # Lectura del acta y su expediente por el tecnico receptor.
        if self.request.method == 'GET' and self.action in ('actas_almacen', 'archivo_acta_almacen', 'retrieve'):
            from django.db.models import Q
            return queryset.filter(Q(solicitante=usuario) | Q(ticket_soporte__tecnico_asignado=usuario) | Q(requerimiento_mantenimiento__auxiliar_asignado=usuario))

        # SOLICITANTE VE LOS SUYOS
        return queryset.filter(
            solicitante=usuario
        )


    # ======================================================
    # CREAR
    # ======================================================

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        if not tiene_permiso(request.user, "CARGAR_EXPEDIENTE"):
            return respuesta_sin_permiso("CARGAR_EXPEDIENTE")

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        solicitud = serializer.save()


        registrar_bitacora(
            request=request,
            accion="CREAR_SOLICITUD_COMPRA",
            modulo="Compras",
            detalle=(
                f"Se creó la solicitud "
                f"{solicitud.codigo}: "
                f"{solicitud.titulo}."
            ),
            nivel="INFO",
        )


        salida = self.get_serializer(
            solicitud
        )


        return Response(
            salida.data,
            status=status.HTTP_201_CREATED
        )


    # ======================================================
    # MODIFICAR
    # ======================================================

    # Campos que determinan el monto/objeto evaluado por DAF.
    # Una vez que el expediente sale de CREADO_PENDIENTE_DAF,
    # NADIE (ni ADMIN) puede modificarlos por esta vía genérica:
    # solo así el monto que Tesorería y Director vieron es
    # garantizado el mismo que se desembolsa/cierra.
    CAMPOS_INMUTABLES_EN_PROCESO = {
        "monto_estimado", "cantidad", "tipo",
        "especificaciones", "justificacion",
        "informe", "poa", "pedido", "proforma",
    }

    def partial_update(
        self,
        request,
        *args,
        **kwargs
    ):

        solicitud = (
            self.get_object()
        )

        en_proceso = solicitud.estado != "CREADO_PENDIENTE_DAF"


        # --------------------------------------------------
        # SOLICITANTE
        # --------------------------------------------------

        if (
            solicitud.solicitante_id
            == request.user.id
        ):

            if en_proceso:

                return Response(
                    {
                        "detalle":
                            "La solicitud ya está siendo procesada y no puede modificarse."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # --------------------------------------------------
        # ADMIN
        # --------------------------------------------------

        elif not es_admin(
            request.user
        ):

            return Response(
                {
                    "detalle":
                        "No tiene permiso para modificar esta solicitud."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        elif en_proceso:

            campos_prohibidos = (
                self.CAMPOS_INMUTABLES_EN_PROCESO
                & set(request.data.keys())
            )

            if campos_prohibidos:

                return Response(
                    {
                        "detalle": (
                            "No se puede modificar "
                            f"{', '.join(sorted(campos_prohibidos))} "
                            "una vez que el expediente está en "
                            "proceso de aprobación."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
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
            accion="MODIFICAR_SOLICITUD_COMPRA",
            modulo="Compras",
            detalle=(
                f"Se modificó la solicitud "
                f"{solicitud.codigo}."
            ),
            nivel="INFO",
        )


        return respuesta


    # ======================================================
    # ANULAR
    # ======================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        solicitud = (
            self.get_object()
        )


        # --------------------------------------------------
        # SOLO EL AUTOR
        # --------------------------------------------------

        if (
            solicitud.solicitante_id
            != request.user.id
        ):

            return Response(
                {
                    "detalle":
                        "Solo el solicitante puede anular su solicitud."
                },
                status=status.HTTP_403_FORBIDDEN
            )


        # --------------------------------------------------
        # SOLO NUEVO
        # --------------------------------------------------

        if (
            solicitud.estado
            not in ("NUEVO", "CREADO_PENDIENTE_DAF")
        ):

            return Response(
                {
                    "detalle":
                        "La solicitud ya está en procesamiento y no puede anularse."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        solicitud.estado = (
            "ANULADO"
        )

        solicitud.activo = False


        solicitud.save(
            update_fields=[
                "estado",
                "activo",
                "actualizado_en",
            ]
        )


        registrar_bitacora(
            request=request,
            accion="ANULAR_SOLICITUD_COMPRA",
            modulo="Compras",
            detalle=(
                f"Se anuló la solicitud "
                f"{solicitud.codigo}."
            ),
            nivel="WARNING",
        )


        return Response(
            {
                "ok": True,
                "mensaje":
                    "Solicitud de compra anulada correctamente."
            },
            status=status.HTTP_200_OK
        )

    def _validar_aprobacion_r01_r02(self, request, solicitud):
        from .aprobacion import validar_aprobador
        validar_aprobador(solicitud, request.user)
        from config.reglas import error_limite, notificar_rechazo
        from .reglas_cotizaciones import validar_solicitud
        error = error_limite(solicitud.monto_estimado, solicitud.via_adquisicion)
        if error:
            solicitud.estado, solicitud.activo = 'RECHAZADO', False
            solicitud.motivo_rechazo = error['detalle']
            solicitud.save()
            liberar_origen(solicitud, error['detalle'], request)
            registrar_bitacora(request=request, accion='R01_COMPRA_RECHAZADA', modulo='Compras', detalle=f'{solicitud.codigo}: {error["detalle"]}', nivel='WARNING')
            return Response(error, status=400)
        validar_solicitud(solicitud)
        return None

    @transaction.atomic
    def _transicion(self, request, solicitud, permiso, origen, destino, accion, detalle):
        solicitud = SolicitudCompra.objects.select_for_update().get(pk=solicitud.pk)
        if not tiene_permiso(request.user, permiso):
            return respuesta_sin_permiso(permiso)
        if solicitud.cerrado_inmutable:
            return Response({"detalle": "El expediente está cerrado y es inmutable."}, status=status.HTTP_409_CONFLICT)
        if solicitud.estado not in origen:
            return Response({"detalle": f"Transición no permitida desde {solicitud.estado}."}, status=status.HTTP_409_CONFLICT)
        if destino == 'APROBADO_PARA_DESEMBOLSO':
            from .aprobacion import validar_aprobador
            validar_aprobador(solicitud, request.user, final=settings.SIA_REQUIERE_APROBACION_DIRECTOR)
        if destino in {'EVALUADO_PENDIENTE_CERTIFICACION', 'VERIFICADO_PENDIENTE_AUTORIZACION', 'APROBADO_PARA_DESEMBOLSO'}:
            bloqueo = self._validar_aprobacion_r01_r02(request, solicitud)
            if bloqueo is not None:
                return bloqueo
        if destino == 'APROBADO_PARA_DESEMBOLSO':
            from .caja_chica import registrar_operacion
            registrar_operacion(solicitud)
        solicitud.estado = destino
        solicitud.save()
        registrar_bitacora(request=request, accion=accion, modulo="Compras", detalle=f"{solicitud.codigo}: {detalle}", nivel="INFO")
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"], url_path="evaluar-daf")
    @transaction.atomic
    def evaluar_daf(self, request, pk=None):
        solicitud = self.get_object()
        solicitud = SolicitudCompra.objects.select_for_update().get(pk=solicitud.pk)
        if not tiene_permiso(request.user, "EVALUAR_EXPEDIENTE"):
            return respuesta_sin_permiso("EVALUAR_EXPEDIENTE")
        if solicitud.estado != "CREADO_PENDIENTE_DAF":
            return Response({"detalle": "El expediente no está pendiente de evaluación DAF."}, status=409)
        califica = str(request.data.get("califica", "")).lower() in ("true", "1", "si", "sí")
        if not califica:
            motivo = str(request.data.get("motivo", "")).strip()
            if not motivo:
                return Response({"detalle": "Debe registrar el motivo del rechazo."}, status=400)
            solicitud.estado, solicitud.motivo_rechazo, solicitud.activo = "RECHAZADO", motivo, False
            solicitud.save()
            liberar_origen(solicitud, motivo, request)
            return Response(self.get_serializer(solicitud).data)
        from .aprobacion import validar_aprobador
        validar_aprobador(solicitud, request.user)
        via = request.data.get('via_adquisicion', solicitud.via_adquisicion if solicitud.via_adquisicion != 'PENDIENTE' else 'CAJA_CHICA')
        if via not in ('CAJA_CHICA', 'FINANZAS'):
            return Response({'detalle': 'Seleccione Caja chica o Finanzas.'}, status=400)
        solicitud.via_adquisicion = via
        solicitud.save(update_fields=['via_adquisicion', 'actualizado_en'])
        bloqueo = self._validar_aprobacion_r01_r02(request, solicitud)
        if bloqueo is not None:
            return bloqueo
        from .expediente import documentos_faltantes
        faltantes = documentos_faltantes(solicitud)
        if faltantes:
            return Response({"detalle": "Complete el expediente antes de aprobar: " + ", ".join(faltantes) + "."}, status=400)
        return self._transicion(request, solicitud, "EVALUAR_EXPEDIENTE", ["CREADO_PENDIENTE_DAF"], "EVALUADO_PENDIENTE_CERTIFICACION", "EVALUAR_PRESUPUESTO", "La solicitud califica presupuestariamente.")

    @action(detail=True, methods=["post"], url_path="certificar-daf")
    @transaction.atomic
    def certificar_daf(self, request, pk=None):
        solicitud = self.get_object()
        if not tiene_permiso(request.user, "CERTIFICAR_PRESUPUESTO"):
            return respuesta_sin_permiso("CERTIFICAR_PRESUPUESTO")
        # REQUERIMIENTO 8 (R08): DAF conserva su permiso y certificación.
        estados_certificables = ['EVALUADO_PENDIENTE_CERTIFICACION']
        if not settings.SIA_REQUIERE_APROBACION_DIRECTOR:
            estados_certificables.append('VERIFICADO_PENDIENTE_AUTORIZACION')
        if solicitud.estado not in estados_certificables:
            return Response({"detalle": "El expediente no está pendiente de certificación."}, status=409)
        archivo = request.FILES.get("certificacion_presupuestaria")
        if not archivo and solicitud.estado == 'VERIFICADO_PENDIENTE_AUTORIZACION':
            archivo = solicitud.certificacion_presupuestaria
        if not archivo:
            return Response({"detalle": "Debe adjuntar la certificación presupuestaria PDF."}, status=400)
        if not archivo.name.lower().endswith(".pdf"):
            return Response({"detalle": "La certificación debe ser un archivo PDF."}, status=400)
        # BPMN: "verificar requisitos" es tarea de la DAF (informe, proforma
        # y POA). Antes lo comprobaba Tesorería en un paso posterior que el
        # proceso no contempla, así que el control se ejerce aquí.
        bloqueo = self._validar_aprobacion_r01_r02(request, solicitud)
        if bloqueo is not None:
            return bloqueo
        from .expediente import documentos_faltantes
        faltantes = documentos_faltantes(solicitud)
        if faltantes:
            return Response({"detalle": "Documentos faltantes: " + ", ".join(faltantes) + "."}, status=400)
        solicitud.certificacion_presupuestaria = archivo
        solicitud.save(update_fields=["certificacion_presupuestaria", "actualizado_en"])
        # Emitida la certificación, el expediente queda disponible para la
        # autorización del Director (BPMN: DAF -> DIRECTOR, sin escalas).
        # REQUERIMIENTO 8 (R08): sin Director, Tesorería recibe el expediente.
        # REQUERIMIENTO 9 (R09): _transicion reserva saldo de forma atómica.
        destino = 'VERIFICADO_PENDIENTE_AUTORIZACION' if settings.SIA_REQUIERE_APROBACION_DIRECTOR else 'APROBADO_PARA_DESEMBOLSO'
        return self._transicion(request, solicitud, "CERTIFICAR_PRESUPUESTO", estados_certificables, destino, "CERTIFICAR_PRESUPUESTO", "Certificación emitida; expediente derivado a " + ('Dirección.' if settings.SIA_REQUIERE_APROBACION_DIRECTOR else 'Tesorería sin aprobación del Director.'))

  #  @action(detail=True, methods=["post"], url_path="visto-bueno-director")
   # def visto_bueno_director(self, request, pk=None):
        # Igual que certificar-daf: al dar el visto bueno, el expediente
        # queda automáticamente disponible para Tesorería (desembolso).
      #  return self._transicion(request, self.get_object(), "DAR_VISTO_BUENO", ["VERIFICADO_PENDIENTE_AUTORIZACION"], "APROBADO_PARA_DESEMBOLSO", "VISTO_BUENO_DIRECTOR", "Director autorizó; expediente derivado automáticamente a Tesorería para desembolso.")
    @action(detail=True, methods=["post"], url_path="visto-bueno-director")
    def visto_bueno_director(self, request, pk=None):
        if not tiene_permiso(request.user, 'DAR_VISTO_BUENO'):
            return respuesta_sin_permiso('DAR_VISTO_BUENO')
        # REQUERIMIENTO 8: este paso no pertenece al flujo vigente.
        if not settings.SIA_REQUIERE_APROBACION_DIRECTOR:
            return Response({'detalle': 'La aprobación del Director está desactivada. DAF deriva directamente a Tesorería.'}, status=409)


        # ======================================================
        # INICIO R08 - PROHIBIR AUTOAPROBACION DE COMPRAS
        # ======================================================

        solicitud = self.get_object()

        # Verificar que el solicitante no apruebe su propia compra
        if solicitud.solicitante_id == request.user.pk:
            return Response(
                {
                    "detalle": (
                        "No puede aprobar una solicitud "
                        "de compra creada por usted mismo."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ======================================================
        # FIN R08 - PROHIBIR AUTOAPROBACION DE COMPRAS
        # ======================================================

        # Mantener el flujo original de aprobacion
        return self._transicion(
            request,
            solicitud,
            "DAR_VISTO_BUENO",
            ["VERIFICADO_PENDIENTE_AUTORIZACION"],
            "APROBADO_PARA_DESEMBOLSO",
            "VISTO_BUENO_DIRECTOR",
            "Director autorizo; expediente derivado "
            "automaticamente a Tesoreria para desembolso."
        )

    @action(detail=True, methods=["post"], url_path="rechazar")
    def rechazar(self, request, pk=None):
        # Rechazo genérico previo al desembolso. evaluar-daf ya cubre el
        # rechazo en el primer paso (CREADO_PENDIENTE_DAF); esta acción
        # cubre el resto de los pasos previos al desembolso, incluida la
        # decisión final del Director (visto-bueno-director no tenía
        # rama de rechazo).
        solicitud = self.get_object()

        if not tiene_permiso(request.user, "DAR_VISTO_BUENO"):
            return respuesta_sin_permiso("DAR_VISTO_BUENO")

        if solicitud.cerrado_inmutable:
            return Response({"detalle": "El expediente está cerrado y es inmutable."}, status=status.HTTP_409_CONFLICT)

        estados_rechazables = [
            "CREADO_PENDIENTE_DAF",
            "EVALUADO_PENDIENTE_CERTIFICACION",
            "VERIFICADO_PENDIENTE_AUTORIZACION",
        ]

        if solicitud.estado not in estados_rechazables:
            return Response({"detalle": f"Transición no permitida desde {solicitud.estado}."}, status=status.HTTP_409_CONFLICT)

        motivo = str(request.data.get("motivo", "")).strip()

        if not motivo:
            return Response({"detalle": "Debe registrar el motivo del rechazo."}, status=400)

        solicitud.estado = "RECHAZADO"
        solicitud.motivo_rechazo = motivo
        solicitud.activo = False
        solicitud.save()

        liberar_origen(solicitud, motivo, request)

        registrar_bitacora(
            request=request,
            accion="RECHAZAR_EXPEDIENTE",
            modulo="Compras",
            detalle=f"{solicitud.codigo}: {motivo}",
            nivel="INFO",
        )

        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"], url_path="desembolsar")
    @documentar('Constancia de desembolso')
    def desembolsar(self, request, pk=None):
        from .tesoreria import confirmar
        return confirmar(self, request)

    @action(detail=True, methods=["post"], url_path="confirmar-recepcion-fondos")
    @documentar('Recepción de fondos', firma_obligatoria=True)
    def confirmar_recepcion_fondos(self, request, pk=None):
        """Tesorería entrega el efectivo, pero el dinero lo retira una
        persona. Este acuse deja constancia de quién lo recibió y cuándo:
        hasta entonces el expediente muestra que los fondos están listos
        para retirar y Tesorería ve que la entrega sigue pendiente."""

        s = self.get_object()

        if not tiene_permiso(request.user, "REALIZAR_COMPRA"):
            return respuesta_sin_permiso("REALIZAR_COMPRA")

        if s.estado != "FONDOS_DESEMBOLSADOS":
            return Response(
                {"detalle": "Tesorería todavía no desembolsó los fondos de este expediente."},
                status=409
            )

        if s.fondos_recibidos_en:
            return Response({"detalle": "La recepción de fondos ya fue confirmada."}, status=409)

        quien = request.user.nombre_completo

        if not quien:
            quien = request.user.nombre_completo

        s.fondos_recibidos_en = timezone.now()
        s.fondos_recibidos_por = quien

        s.save(update_fields=["fondos_recibidos_en", "fondos_recibidos_por", "actualizado_en"])

        registrar_bitacora(
            request=request,
            accion="CONFIRMAR_RECEPCION_FONDOS",
            modulo="Compras",
            detalle=(
                f"{s.codigo}: {quien} confirmó haber recibido Bs "
                f"{s.monto_desembolsado} de Tesorería."
            ),
            nivel="INFO",
        )

        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"], url_path="actualizar-gestion")
    def actualizar_gestion(self, request, pk=None):
        """Deja ver al resto del proceso que el expediente está siendo
        trabajado —buscando proveedor o comprando— en lugar de parecer
        detenido entre el desembolso y el registro de la compra."""

        s = self.get_object()

        if not tiene_permiso(request.user, "REALIZAR_COMPRA"):
            return respuesta_sin_permiso("REALIZAR_COMPRA")

        if s.estado != "FONDOS_DESEMBOLSADOS":
            return Response(
                {"detalle": "Solo puede informar avances mientras gestiona la compra."},
                status=409
            )

        gestion = str(request.data.get("gestion_estado", "")).strip().upper()

        if gestion not in dict(SolicitudCompra.GESTIONES):
            return Response(
                {"gestion_estado": "Indique si está buscando el producto o comprando."},
                status=400
            )

        s.gestion_estado = gestion
        s.gestion_nota = str(request.data.get("gestion_nota", "")).strip()[:200]
        s.gestion_actualizada_en = timezone.now()

        s.save(update_fields=[
            "gestion_estado", "gestion_nota", "gestion_actualizada_en", "actualizado_en",
        ])

        registrar_bitacora(
            request=request,
            accion="ACTUALIZAR_GESTION_COMPRA",
            modulo="Compras",
            detalle=(
                f"{s.codigo}: {dict(SolicitudCompra.GESTIONES)[gestion]}"
                + (f" — {s.gestion_nota}" if s.gestion_nota else "")
            ),
            nivel="INFO",
        )

        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"], url_path="registrar-compra")
    def registrar_compra(self, request, pk=None):
        s = self.get_object()
        if not tiene_permiso(request.user, "REALIZAR_COMPRA"):
            return respuesta_sin_permiso("REALIZAR_COMPRA")
        if s.estado != "FONDOS_DESEMBOLSADOS":
            return Response({"detalle": "Los fondos todavía no fueron desembolsados."}, status=409)
        if not s.fondos_recibidos_en:
            return Response(
                {"detalle": "Primero debe confirmar en el sistema que recibió el efectivo de Tesorería."},
                status=409
            )
        try: monto = Decimal(str(request.data.get("monto_real", "")))
        except InvalidOperation: return Response({"detalle": "Monto real inválido."}, status=400)
        proveedor = str(request.data.get("proveedor", "")).strip()
        if monto <= 0 or not proveedor:
            return Response({"detalle": "Debe registrar monto real y proveedor."}, status=400)
        # Caso de uso "Registrar verificación de componentes": se exige
        # como parte del mismo registro de compra (no hay un paso de
        # verificación separado en el BPMN de Caja Chica).
        verificado = str(request.data.get("componente_verificado", "")).lower() in ("true", "1", "si", "sí")
        if not verificado:
            return Response({"detalle": "Debe confirmar que el producto adquirido corresponde a lo solicitado."}, status=400)

        # La compra debe quedar respaldada: sin comprobante no hay registro.
        comprobante = request.FILES.get("comprobante_compra")

        if not comprobante:
            return Response(
                {"detalle": "Debe adjuntar la factura o recibo que respalda la compra."},
                status=400
            )

        s.monto_real, s.proveedor = monto, proveedor
        s.componente_verificado = True
        s.observacion_verificacion = str(request.data.get("observacion_verificacion", "")).strip()
        s.comprobante_compra = comprobante
        s.fecha_compra = timezone.now()

        s.save(update_fields=[
            "monto_real", "proveedor", "componente_verificado",
            "observacion_verificacion", "comprobante_compra",
            "fecha_compra", "actualizado_en",
        ])
        return self._transicion(request, s, "REALIZAR_COMPRA", ["FONDOS_DESEMBOLSADOS"], "COMPRA_REGISTRADA", "REGISTRAR_COMPRA", "Compra física registrada y componentes verificados.")

    @action(detail=True, methods=["post"], url_path="registrar-ingreso-almacen")
    @documentar('Constancia de ingreso a almacén')
    def registrar_ingreso_almacen(self, request, pk=None):
        s = self.get_object()
        if not tiene_permiso(request.user, "REGISTRAR_ENTRADA_SALIDA_ALMACEN"):
            return respuesta_sin_permiso("REGISTRAR_ENTRADA_SALIDA_ALMACEN")
        if s.estado != "COMPRA_REGISTRADA":
            return Response({"detalle": "La compra todavía no fue registrada."}, status=409)
        if s.fecha_ingreso_almacen:
            return Response({"detalle": "El ingreso a almacén ya fue registrado."}, status=409)

        # Control de almacén: qué cantidad ingresó y quién la recibió.
        try:
            cantidad = int(request.data.get("cantidad_recibida") or 0)
        except (TypeError, ValueError):
            return Response({"cantidad_recibida": "Cantidad inválida."}, status=400)

        if cantidad <= 0:
            return Response(
                {"cantidad_recibida": "Indique la cantidad recibida en almacén."},
                status=400
            )

        if cantidad > s.cantidad:
            return Response(
                {
                    "cantidad_recibida": (
                        f"La cantidad recibida no puede superar las {s.cantidad} "
                        "unidades solicitadas."
                    )
                },
                status=400
            )

        responsable = str(request.data.get("responsable_recepcion", "")).strip()

        if not responsable:
            return Response(
                {"responsable_recepcion": "Indique quién recibe el producto en almacén."},
                status=400
            )

        s.fecha_ingreso_almacen = timezone.now()
        s.cantidad_recibida = cantidad
        s.responsable_recepcion = responsable
        s.observacion_ingreso = str(request.data.get("observacion_ingreso", "")).strip()

        s.save(update_fields=[
            "fecha_ingreso_almacen", "cantidad_recibida",
            "responsable_recepcion", "observacion_ingreso", "actualizado_en",
        ])

        registrar_bitacora(
            request=request,
            accion="REGISTRAR_INGRESO_ALMACEN",
            modulo="Compras",
            detalle=(
                f"{s.codigo}: ingresaron {cantidad} unidad(es) a almacén, "
                f"recibidas por {responsable}."
            ),
            nivel="INFO",
        )

        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"], url_path="registrar-despacho-almacen")
    @documentar('Constancia de salida de almacén')
    def registrar_despacho_almacen(self, request, pk=None):
        s = self.get_object()
        if not tiene_permiso(request.user, "ENTREGAR_PRODUCTO"):
            return respuesta_sin_permiso("ENTREGAR_PRODUCTO")
        if s.estado != "COMPRA_REGISTRADA":
            return Response({"detalle": "La compra todavía no fue registrada."}, status=409)
        if not s.fecha_ingreso_almacen:
            return Response({"detalle": "Debe registrar primero el ingreso a almacén."}, status=409)
        if s.fecha_despacho_almacen:
            return Response({"detalle": "La salida de almacén ya fue registrada."}, status=409)

        # Control de salida: qué cantidad sale y para quién.
        try:
            cantidad = int(request.data.get("cantidad_entregada") or 0)
        except (TypeError, ValueError):
            return Response({"cantidad_entregada": "Cantidad inválida."}, status=400)

        if cantidad <= 0:
            return Response(
                {"cantidad_entregada": "Indique la cantidad que sale de almacén."},
                status=400
            )

        if s.cantidad_recibida and cantidad > s.cantidad_recibida:
            return Response(
                {
                    "cantidad_entregada": (
                        f"No puede salir más de lo que ingresó "
                        f"({s.cantidad_recibida} unidad/es)."
                    )
                },
                status=400
            )

        destinatario = str(request.data.get("entregado_a", "")).strip()

        if s.ticket_soporte_id or s.requerimiento_mantenimiento_id:
            from .actas_almacen import receptor_acta
            receptor = receptor_acta(s)
            if not receptor:
                return Response({'detalle': 'Asigne el tecnico que recibira el producto.'}, status=409)
            destinatario = receptor.nombre_completo

        if not destinatario:
            return Response(
                {"entregado_a": "Indique a quién se entrega el producto."},
                status=400
            )

        s.fecha_despacho_almacen = timezone.now()
        s.cantidad_entregada = cantidad
        s.entregado_a = destinatario
        s.observacion_salida = str(request.data.get("observacion_salida", "")).strip()

        s.save(update_fields=[
            "fecha_despacho_almacen", "cantidad_entregada",
            "entregado_a", "observacion_salida", "actualizado_en",
        ])

        registrar_bitacora(
            request=request,
            accion="REGISTRAR_SALIDA_ALMACEN",
            modulo="Compras",
            detalle=f"{s.codigo}: salieron {cantidad} unidad(es) de almacén con destino a {destinatario}.",
            nivel="INFO",
        )

        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"], url_path="entregar-con-acta")
    @documentar('Constancia de entrega de producto')
    def entregar_con_acta(self, request, pk=None):
        """BPMN: "Entregar la solicitud con un acta de conformidad".
        El bien sale del almacén y se entrega formalmente al solicitante
        acompañado del acta que respalda la recepción."""

        s = self.get_object()

        if not tiene_permiso(request.user, "ENTREGAR_PRODUCTO"):
            return respuesta_sin_permiso("ENTREGAR_PRODUCTO")

        if s.estado != "COMPRA_REGISTRADA":
            return Response({"detalle": "La compra todavía no fue registrada."}, status=409)

        if not s.fecha_despacho_almacen:
            return Response({"detalle": "Debe registrar primero la salida de almacén."}, status=409)

        from .actas_almacen import guardar_firmada
        guardar_firmada(request, s)
        s.fecha_entrega_solicitante = timezone.now()
        s.save(update_fields=["acta_conformidad", "acta_firmada_en", "fecha_entrega_solicitante", "actualizado_en"])

        # Si el expediente nació de un ticket de Soporte, la entrega física
        # del componente es lo que reanuda la atención técnica: hasta aquí
        # el especialista estuvo bloqueado esperando el repuesto.
        ticket = s.ticket_soporte

        if ticket and ticket.estado_compra_componente == "VIABLE":

            ticket.estado_compra_componente = "ENTREGADA"
            ticket.componente_entregado_en = s.fecha_entrega_solicitante

            ticket.save(
                update_fields=[
                    "estado_compra_componente",
                    "componente_entregado_en",
                    "actualizado_en",
                ]
            )

            registrar_bitacora(
                request=request,
                accion="ENTREGAR_COMPONENTE_SOPORTE",
                modulo="Compras",
                detalle=(
                    f"{s.codigo}: componente entregado; el ticket "
                    f"{ticket.codigo} queda habilitado para continuar "
                    "la atención técnica."
                ),
                nivel="INFO",
            )

        # Lo mismo para un requerimiento de Mantenimiento: la entrega del
        # componente reanuda el trabajo del técnico.
        requerimiento = s.requerimiento_mantenimiento

        if requerimiento and requerimiento.estado_compra_componente == "VIABLE":

            requerimiento.estado_compra_componente = "PENDIENTE_RECEPCION_TECNICO"
            requerimiento.compra_completada = True
            requerimiento.producto_entregado = True

            requerimiento.save()

            registrar_bitacora(
                request=request,
                accion="ENTREGAR_COMPONENTE_MANTENIMIENTO",
                modulo="Compras",
                detalle=(
                    f"{s.codigo}: componente entregado; el requerimiento "
                    f"{requerimiento.codigo} puede continuar."
                ),
                nivel="INFO",
            )

        destino = "DESCARGO_PENDIENTE_LIQUIDACION" if s.ticket_soporte_id or s.requerimiento_mantenimiento_id else "COMPRADO_Y_ENTREGADO"
        return self._transicion(request, s, "ENTREGAR_PRODUCTO", ["COMPRA_REGISTRADA"], destino, "ENTREGAR_CON_ACTA", "Bien entregado a la sección solicitante con acta de conformidad.")

    @action(detail=True, methods=["post"], url_path="firmar-acta")
    @documentar('Acta de conformidad y recepción', firma_obligatoria=True)
    def firmar_acta(self, request, pk=None):
        """BPMN: "Firmar acta de conformidad". La sección solicitante
        revisa la entrega y firma el acta como constancia de que recibió
        el bien conforme."""

        s = self.get_object()

        if s.ticket_soporte_id or s.requerimiento_mantenimiento_id:
            return Response({'detalle': 'El acta la firman el encargado de almacen y el tecnico receptor durante la entrega del producto.'}, status=409)

        if s.solicitante_id != request.user.id and not es_admin(request.user):
            return Response({"detalle": "Solo la sección solicitante puede firmar el acta."}, status=403)

        if s.estado != "COMPRADO_Y_ENTREGADO":
            return Response({"detalle": "El bien todavía no fue entregado."}, status=409)

        if s.acta_firmada_en:
            return Response({"detalle": "El acta ya fue firmada."}, status=409)

        s.acta_firmada_en = timezone.now()
        s.save(update_fields=["acta_firmada_en", "actualizado_en"])

        return self._transicion(
            request, s, "REGISTRAR_DESCARGO",
            ["COMPRADO_Y_ENTREGADO"], "DESCARGO_PENDIENTE_LIQUIDACION",
            "FIRMAR_ACTA_CONFORMIDAD",
            "La sección solicitante firmó el acta de conformidad.",
        )

    @action(detail=True, methods=["post"], url_path="recibir-solicitud")
    @transaction.atomic
    def recibir_solicitud(self, request, pk=None):
        """BPMN: "Recibir la solicitud". Último paso del proceso: el
        solicitante recibe formalmente el bien y el expediente queda
        cerrado de forma inmutable."""

        s = self.get_object()

        if s.solicitante_id != request.user.id and not es_admin(request.user):
            return Response({"detalle": "Solo la sección solicitante puede recibir la solicitud."}, status=403)

        if not s.acta_firmada_en:
            return Response({"detalle": "Debe firmar primero el acta de conformidad."}, status=409)

        if s.estado != "DESCARGO_PENDIENTE_LIQUIDACION":
            return Response({"detalle": "El expediente no está pendiente de recepción."}, status=409)

        s.solicitud_recibida_en = timezone.now()
        s.cerrado_inmutable = True
        s.activo = False
        s.estado = "CERRADO_ARCHIVADO"
        s.save()

        registrar_bitacora(
            request=request,
            accion="RECIBIR_SOLICITUD",
            modulo="Compras",
            detalle=(
                f"{s.codigo}: la sección solicitante recibió el bien. "
                "El proceso de compra quedó cerrado."
            ),
            nivel="INFO",
        )

        return Response(self.get_serializer(s).data)
