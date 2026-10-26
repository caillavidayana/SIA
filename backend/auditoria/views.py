from rest_framework import status
from django.conf import settings

from usuarios.authentication import (
    ExpiringTokenAuthentication as TokenAuthentication,
)

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import Response


from usuarios.models import UsuarioRol


from .models import (
    Bitacora,
    ConfiguracionSMTP,
    PreferenciaSistema,
)

from .serializers import (
    BitacoraSerializer,
    ConfiguracionSMTPSerializer,
    PreferenciaSistemaSerializer,
)

from .utils import registrar_bitacora


# ==========================================================
# AUXILIAR
# ==========================================================

def es_admin(usuario):

    if usuario.is_superuser:
        return True

    return UsuarioRol.objects.filter(
        usuario=usuario,
        rol__codigo__in=["ADMIN", "SUPERUSER"],
        rol__activo=True,
        activo=True,
    ).exists()


# ==========================================================
# BITÁCORA
# ==========================================================

@api_view(["GET", "POST"])
@authentication_classes([
    TokenAuthentication
])
@permission_classes([
    IsAuthenticated
])
def bitacora_view(request):

    if not es_admin(request.user):

        return Response(
            {
                "detalle":
                    "Solo el administrador puede consultar la bitácora."
            },
            status=status.HTTP_403_FORBIDDEN
        )


    # ------------------------------------------------------
    # CONSULTAR
    # ------------------------------------------------------

    if request.method == "GET":

        registros = (
            Bitacora.objects
            .select_related("usuario")
            .all()
            .order_by("-fecha")[:500]
        )

        serializer = BitacoraSerializer(
            registros,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    # ------------------------------------------------------
    # REGISTRO MANUAL
    # ------------------------------------------------------

    accion = request.data.get(
        "accion",
        ""
    ).strip()

    modulo = request.data.get(
        "modulo",
        ""
    ).strip()

    detalle = request.data.get(
        "detalle",
        ""
    ).strip()

    nivel = request.data.get(
        "nivel",
        "INFO"
    )


    if not accion or not modulo:

        return Response(
            {
                "detalle":
                    "Acción y módulo son obligatorios."
            },
            status=status.HTTP_400_BAD_REQUEST
        )


    registrar_bitacora(
        request=request,
        accion=accion,
        modulo=modulo,
        detalle=detalle,
        nivel=nivel,
    )


    return Response(
        {
            "ok": True,
            "mensaje":
                "Registro agregado correctamente."
        },
        status=status.HTTP_201_CREATED
    )


# ==========================================================
# SMTP
# ==========================================================

@api_view(["GET", "PUT"])
@authentication_classes([
    TokenAuthentication
])
@permission_classes([
    IsAuthenticated
])
def smtp_view(request):

    if not es_admin(request.user):

        return Response(
            {
                "detalle":
                    "Solo el administrador puede configurar SMTP."
            },
            status=status.HTTP_403_FORBIDDEN
        )


    configuracion, _ = (
        ConfiguracionSMTP.objects
        .get_or_create(
            pk=1,
            defaults={
                "nombre":
                    "Correo institucional",
                "puerto": 587,
                "usar_tls": True,
                "activo": False,
            }
        )
    )


    # ------------------------------------------------------
    # CONSULTAR
    # ------------------------------------------------------

    if request.method == "GET":

        serializer = (
            ConfiguracionSMTPSerializer(
                configuracion
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    # ------------------------------------------------------
    # MODIFICAR
    # ------------------------------------------------------

    serializer = (
        ConfiguracionSMTPSerializer(
            configuracion,
            data=request.data,
            partial=True
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    serializer.save(
        actualizado_por=request.user
    )


    registrar_bitacora(
        request=request,
        accion="CONFIGURAR_SMTP",
        modulo="Correo SMTP",
        detalle=(
            "El administrador modificó "
            "la configuración SMTP."
        ),
        nivel="INFO",
    )


    return Response(
        {
            "ok": True,
            "mensaje":
                "Configuración SMTP actualizada correctamente.",
            "configuracion":
                serializer.data
        },
        status=status.HTTP_200_OK
    )


# ==========================================================
# PREFERENCIAS
# ==========================================================

@api_view(["GET", "PUT"])
@authentication_classes([
    TokenAuthentication
])
@permission_classes([
    IsAuthenticated
])
def preferencias_view(request):

    if not es_admin(request.user):

        return Response(
            {
                "detalle":
                    "Solo el administrador puede modificar preferencias."
            },
            status=status.HTTP_403_FORBIDDEN
        )


    preferencias, _ = (
        PreferenciaSistema.objects
        .get_or_create(
            pk=1,
            defaults={
                "nombre_sistema":
                    "SIA",

                "institucion":
                    "Escuela Militar de Ingeniería",

                "unidad_academica":
                    "Unidad Académica Santa Cruz",

                "prefijo_soporte":
                    "SOP",

                "prefijo_compras":
                    "CMP",

                "limite_caja_chica":
                    settings.SIA_LIMITE_CAJA_CHICA,

                "intentos_login":
                    5,

                "tiempo_bloqueo_minutos":
                    15,
            }
        )
    )


    # ------------------------------------------------------
    # CONSULTAR
    # ------------------------------------------------------

    if request.method == "GET":

        serializer = (
            PreferenciaSistemaSerializer(
                preferencias
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    # ------------------------------------------------------
    # MODIFICAR
    # ------------------------------------------------------

    serializer = (
        PreferenciaSistemaSerializer(
            preferencias,
            data=request.data,
            partial=True
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    serializer.save(
        actualizado_por=request.user
    )


    registrar_bitacora(
        request=request,
        accion="MODIFICAR_PREFERENCIAS",
        modulo="Preferencias",
        detalle=(
            "El administrador modificó "
            "los parámetros generales de SIA."
        ),
        nivel="INFO",
    )


    return Response(
        {
            "ok": True,
            "mensaje":
                "Preferencias actualizadas correctamente.",
            "preferencias":
                serializer.data
        },
        status=status.HTTP_200_OK
    )
# ======================================================
# INICIO - CONSULTA PUBLICA AUTENTICADA DE CAJA CHICA
# ======================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def limite_caja_chica_view(request):
    from config.reglas import configuracion_reglas
    return Response(configuracion_reglas(), status=status.HTTP_200_OK)

# ======================================================
# FIN - CONSULTA PUBLICA AUTENTICADA DE CAJA CHICA
# ======================================================
