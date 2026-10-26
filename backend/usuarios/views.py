from datetime import timedelta


from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone


from rest_framework import (
    status,
    viewsets,
)

from .authentication import (
    ExpiringTokenAuthentication as TokenAuthentication,
)

from rest_framework.authtoken.models import (
    Token,
)

from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
)

from rest_framework.permissions import (
    AllowAny,
    BasePermission,
    IsAuthenticated,
)

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


from auditoria.utils import registrar_bitacora


from .models import (
    Usuario,
    Rol,
    Area,
    UsuarioRol,
    Permiso,
    RolPermiso,
    DelegacionAprobacion,
    InformeJefatura,
    obtener_codigos_rol_efectivos,
)

from .serializers import (
    UsuarioSerializer,
    RolSerializer,
    AreaSerializer,
    UsuarioRolSerializer,
    PermisoSerializer,
    RolPermisoSerializer,
    DelegacionAprobacionSerializer,
    InformeJefaturaSerializer,
    generar_password_temporal,
)


# ==========================================================
# FUNCIONES DE SEGURIDAD
# ==========================================================

CODIGOS_ADMIN = {
    "ADMIN",
    "ADMINISTRADOR",
    "ADMINISTRADOR_SIGTA",
    "SUPERUSER",
}


def normalizar_codigo(valor):

    return (
        str(valor or "")
        .strip()
        .upper()
        .replace(" ", "_")
    )


def usuario_es_admin(usuario):

    if (
        not usuario
        or not usuario.is_authenticated
    ):

        return False


    # Superusuario Django
    if usuario.is_superuser:

        return True


    return (
        UsuarioRol.objects
        .filter(
            usuario=usuario,
            activo=True,
            rol__activo=True,
            rol__codigo__in=CODIGOS_ADMIN,
        )
        .exists()
    )


def obtener_permisos_usuario(usuario):

    """
    Devuelve los permisos efectivos del usuario.

    Usuario
        -> UsuarioRol
        -> Rol
        -> RolPermiso
        -> Permiso
    """

    if (
        not usuario
        or not usuario.is_authenticated
    ):

        return []


    # ------------------------------------------------------
    # ADMIN mantiene acceso total.
    # ------------------------------------------------------
    #
    # Cuando existan permisos registrados,
    # devolvemos todos los permisos activos.
    #
    # Esto evita bloquear al administrador mientras
    # estamos configurando por primera vez la matriz.
    # ------------------------------------------------------

    if usuario_es_admin(usuario):

        permisos = (
            Permiso.objects
            .filter(
                activo=True
            )
            .order_by(
                "modulo",
                "nombre"
            )
        )

    else:

        # Incluye tanto los roles propios como los roles
        # delegados temporalmente que sigan vigentes.
        codigos_rol = obtener_codigos_rol_efectivos(usuario)

        permisos = (
            Permiso.objects
            .filter(
                activo=True,
                roles_asignados__rol__codigo__in=codigos_rol,
                roles_asignados__rol__activo=True,
                roles_asignados__activo=True
            )
            .distinct()
            .order_by(
                "modulo",
                "nombre"
            )
        )


    return [
        {
            "id":
                permiso.id,

            "codigo":
                permiso.codigo,

            "nombre":
                permiso.nombre,

            "descripcion":
                permiso.descripcion,

            "modulo":
                permiso.modulo,

            "modulo_nombre":
                permiso.get_modulo_display(),
        }

        for permiso in permisos
    ]


def usuario_tiene_algun_rol(usuario, *codigos):

    if not usuario or not usuario.is_authenticated:
        return False

    codigos = {normalizar_codigo(c) for c in codigos}

    return bool(
        set(obtener_codigos_rol_efectivos(usuario)).intersection(codigos)
    )


def usuario_tiene_permiso(
    usuario,
    codigo_permiso
):

    if usuario_es_admin(usuario):

        return True


    codigo_permiso = normalizar_codigo(
        codigo_permiso
    )

    codigos_rol = obtener_codigos_rol_efectivos(usuario)

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


# ==========================================================
# PERMISO PARA ADMINISTRACIÓN DE IDENTIDAD
# ==========================================================

class EsAdministradorSIGTA(
    BasePermission
):

    message = (
        "No tiene permisos para administrar "
        "la configuración de identidad de SIA."
    )


    def has_permission(
        self,
        request,
        view
    ):

        return usuario_es_admin(
            request.user
        )


# ==========================================================
# ÁREAS
# ==========================================================

class AreaViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        AreaSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]


    def get_queryset(self):

        return (
            Area.objects
            .all()
            .order_by(
                "nombre"
            )
        )


    def get_permissions(self):

        # --------------------------------------------------
        # Los usuarios autenticados necesitan consultar
        # las áreas para registrar sus requerimientos.
        # --------------------------------------------------

        if self.action in [
            "list",
            "retrieve",
        ]:

            permission_classes_local = [
                IsAuthenticated
            ]

        else:

            permission_classes_local = [
                IsAuthenticated,
                EsAdministradorSIGTA,
            ]


        return [
            permiso()
            for permiso
            in permission_classes_local
        ]


    def perform_create(
        self,
        serializer
    ):

        area = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="CREAR_AREA",
            modulo="Administración",
            detalle=(
                f"Se registró el área "
                f"{area.codigo} - {area.nombre}."
            ),
            nivel="INFO",
        )


    def perform_update(
        self,
        serializer
    ):

        area = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="MODIFICAR_AREA",
            modulo="Administración",
            detalle=(
                f"Se modificó el área "
                f"{area.codigo} - {area.nombre}."
            ),
            nivel="INFO",
        )


    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        area = self.get_object()


        # No borramos físicamente.
        area.activo = False

        area.save(
            update_fields=[
                "activo"
            ]
        )


        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="INACTIVAR_AREA",
            modulo="Administración",
            detalle=(
                f"Se inactivó el área "
                f"{area.codigo} - {area.nombre}."
            ),
            nivel="INFO",
        )


        return Response(
            {
                "ok": True,

                "mensaje":
                    "Área inactivada correctamente."
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# ROLES
# ==========================================================

class RolViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        RolSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsAdministradorSIGTA,
    ]


    def get_queryset(self):

        return (
            Rol.objects
            .all()
            .order_by(
                "nombre"
            )
        )


    def perform_create(
        self,
        serializer
    ):

        rol = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="CREAR_ROL",
            modulo="Administración",
            detalle=(
                f"Se registró el rol "
                f"{rol.codigo} - {rol.nombre}."
            ),
            nivel="INFO",
        )


    def perform_update(
        self,
        serializer
    ):

        rol = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="MODIFICAR_ROL",
            modulo="Administración",
            detalle=(
                f"Se modificó el rol "
                f"{rol.codigo} - {rol.nombre}."
            ),
            nivel="INFO",
        )


    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        rol = self.get_object()


        rol.activo = False

        rol.save(
            update_fields=[
                "activo"
            ]
        )


        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="INACTIVAR_ROL",
            modulo="Administración",
            detalle=(
                f"Se inactivó el rol "
                f"{rol.codigo} - {rol.nombre}."
            ),
            nivel="INFO",
        )


        return Response(
            {
                "ok": True,

                "mensaje":
                    "Rol inactivado correctamente."
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# PERMISOS
# ==========================================================

class PermisoViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        PermisoSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsAdministradorSIGTA,
    ]


    def get_queryset(self):

        queryset = (
            Permiso.objects
            .all()
            .order_by(
                "modulo",
                "nombre"
            )
        )


        modulo = (
            self.request
            .query_params
            .get(
                "modulo"
            )
        )


        if modulo:

            queryset = queryset.filter(
                modulo=
                    normalizar_codigo(
                        modulo
                    )
            )


        return queryset


    def perform_create(
        self,
        serializer
    ):

        permiso = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="CREAR_PERMISO",
            modulo="Administración",
            detalle=(
                f"Se registró el permiso "
                f"{permiso.codigo}."
            ),
            nivel="INFO",
        )


    def perform_update(
        self,
        serializer
    ):

        permiso = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="MODIFICAR_PERMISO",
            modulo="Administración",
            detalle=(
                f"Se modificó el permiso "
                f"{permiso.codigo}."
            ),
            nivel="INFO",
        )


    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        permiso = self.get_object()


        permiso.activo = False

        permiso.save(
            update_fields=[
                "activo"
            ]
        )


        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="INACTIVAR_PERMISO",
            modulo="Administración",
            detalle=(
                f"Se inactivó el permiso "
                f"{permiso.codigo}."
            ),
            nivel="INFO",
        )


        return Response(
            {
                "ok": True,

                "mensaje":
                    "Permiso inactivado correctamente."
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# ROL - PERMISO
# ==========================================================

class RolPermisoViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        RolPermisoSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsAdministradorSIGTA,
    ]


    def get_queryset(self):

        queryset = (
            RolPermiso.objects
            .select_related(
                "rol",
                "permiso"
            )
            .all()
            .order_by(
                "rol__nombre",
                "permiso__modulo",
                "permiso__nombre"
            )
        )


        rol_id = (
            self.request
            .query_params
            .get(
                "rol"
            )
        )


        if rol_id:

            queryset = queryset.filter(
                rol_id=rol_id
            )


        return queryset


    def perform_create(
        self,
        serializer
    ):

        asignacion = (
            serializer.save()
        )


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="ASIGNAR_PERMISO_ROL",
            modulo="Administración",
            detalle=(
                f"Se asignó el permiso "
                f"{asignacion.permiso.codigo} "
                f"al rol {asignacion.rol.codigo}."
            ),
            nivel="INFO",
        )


    def perform_update(
        self,
        serializer
    ):

        asignacion = (
            serializer.save()
        )


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="MODIFICAR_PERMISO_ROL",
            modulo="Administración",
            detalle=(
                f"Se modificó la asignación "
                f"{asignacion.rol.codigo} - "
                f"{asignacion.permiso.codigo}."
            ),
            nivel="INFO",
        )


    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        asignacion = (
            self.get_object()
        )


        rol_codigo = (
            asignacion.rol.codigo
        )

        permiso_codigo = (
            asignacion.permiso.codigo
        )


        # En esta relación sí podemos eliminar
        # la asignación sin borrar el permiso.
        asignacion.delete()


        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="QUITAR_PERMISO_ROL",
            modulo="Administración",
            detalle=(
                f"Se quitó el permiso "
                f"{permiso_codigo} "
                f"del rol {rol_codigo}."
            ),
            nivel="INFO",
        )


        return Response(
            {
                "ok": True,

                "mensaje":
                    "Permiso retirado del rol correctamente."
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# USUARIOS
# ==========================================================

class UsuarioViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        UsuarioSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsAdministradorSIGTA,
    ]


    def get_queryset(self):

        return (
            Usuario.objects
            .all()
            .order_by(
                "nombre_completo"
            )
        )


    def perform_create(
        self,
        serializer
    ):

        usuario = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="CREAR_USUARIO",
            modulo="Administración",
            detalle=(
                f"Se registró el usuario "
                f"{usuario.email}."
            ),
            nivel="INFO",
        )


    def perform_update(
        self,
        serializer
    ):

        usuario = serializer.save()


        registrar_bitacora(
            request=self.request,
            usuario=self.request.user,
            accion="MODIFICAR_USUARIO",
            modulo="Administración",
            detalle=(
                f"Se modificó el usuario "
                f"{usuario.email}."
            ),
            nivel="INFO",
        )


    # ======================================================
    # DELETE = INACTIVAR
    # ======================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        usuario = (
            self.get_object()
        )


        # No permitir que el administrador
        # se desactive accidentalmente a sí mismo.

        if usuario.id == request.user.id:

            return Response(
                {
                    "ok": False,

                    "detalle":
                        (
                            "No puede inactivar su propia "
                            "cuenta administrativa."
                        )
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        usuario.is_active = False


        usuario.save(
            update_fields=[
                "is_active"
            ]
        )


        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="INACTIVAR_USUARIO",
            modulo="Administración",
            detalle=(
                f"Se inactivó la cuenta "
                f"{usuario.email}."
            ),
            nivel="INFO",
        )


        return Response(
            {
                "ok": True,

                "mensaje":
                    "Usuario inactivado correctamente."
            },
            status=status.HTTP_200_OK
        )


    # ======================================================
    # ACTIVAR USUARIO
    # ======================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="activar"
    )
    def activar(
        self,
        request,
        pk=None
    ):

        usuario = (
            self.get_object()
        )


        if usuario.is_active:

            return Response(
                {
                    "ok": True,

                    "mensaje":
                        "El usuario ya se encuentra activo."
                },
                status=status.HTTP_200_OK
            )


        usuario.is_active = True

        usuario.failed_attempts = 0

        usuario.locked_until = None


        usuario.save(
            update_fields=[
                "is_active",
                "failed_attempts",
                "locked_until",
            ]
        )


        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="ACTIVAR_USUARIO",
            modulo="Administración",
            detalle=(
                f"Se activó la cuenta "
                f"{usuario.email}."
            ),
            nivel="INFO",
        )


        return Response(
            {
                "ok": True,

                "mensaje":
                    "Usuario activado correctamente."
            },
            status=status.HTTP_200_OK
        )


    # ======================================================
    # RESTABLECER CONTRASEÑA
    # ======================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="restablecer-password"
    )
    @transaction.atomic
    def restablecer_password(self, request, pk=None):

        usuario = self.get_object()
        password_temporal = generar_password_temporal()
        password_validation.validate_password(password_temporal, user=usuario)

        usuario.set_password(password_temporal)
        usuario.must_change_password = True
        usuario.failed_attempts = 0
        usuario.locked_until = None
        usuario.save(update_fields=[
            "password",
            "must_change_password",
            "failed_attempts",
            "locked_until",
        ])

        # Las sesiones por token anteriores dejan de ser válidas.
        Token.objects.filter(user=usuario).delete()

        registrar_bitacora(
            request=request,
            usuario=request.user,
            accion="RESTABLECER_PASSWORD_USUARIO",
            modulo="Administración",
            detalle=(
                f"Se restableció la contraseña del usuario {usuario.email}."
            ),
            nivel="SECURITY",
        )

        return Response(
            {
                "mensaje": "Contraseña restablecida correctamente.",
                "password_temporal": password_temporal,
            },
            status=status.HTTP_200_OK,
        )


# ==========================================================
# USUARIO - ROL
# ==========================================================

class UsuarioRolViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        UsuarioRolSerializer
    )

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsAdministradorSIGTA,
    ]


    def get_queryset(self):

        return (
            UsuarioRol.objects
            .select_related(
                "usuario",
                "rol",
                "area"
            )
            .all()
            .order_by(
                "usuario__nombre_completo",
                "rol__nombre"
            )
        )


# ==========================================================
# DELEGACIÓN TEMPORAL DE APROBACIÓN
# ==========================================================
#
# Caso de uso "Delegar aprobación temporal": solo lo usan
# los actores que aprueban/autorizan algo en el sistema
# (DIRECTOR, DAF, TESORERIA, JEFE_UTIC). No requiere ADMIN
# para operarse día a día; ADMIN solo puede supervisar/revocar
# cualquier delegación.
#
# ==========================================================

class InformeJefaturaViewSet(viewsets.ModelViewSet):
    serializer_class = InformeJefaturaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    MAPA_JEFATURA = {
        "JEFE_UTIC": "UTIC",
        "SERVICIOS_GENERALES": "MANTENIMIENTO",
    }

    def get_queryset(self):
        queryset = InformeJefatura.objects.select_related("jefe")
        if usuario_es_admin(self.request.user):
            return queryset
        return queryset.filter(jefe=self.request.user)

    def perform_create(self, serializer):
        roles = obtener_codigos_rol_efectivos(self.request.user)
        jefatura = next((area for rol, area in self.MAPA_JEFATURA.items() if rol in roles), None)
        if not jefatura:
            raise PermissionDenied("Solo una jefatura puede elaborar informes para el Director.")
        serializer.save(jefe=self.request.user, jefatura=jefatura)


class DelegacionAprobacionViewSet(
    viewsets.ModelViewSet
):

    serializer_class = DelegacionAprobacionSerializer

    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]


    def get_queryset(self):

        usuario = self.request.user

        queryset = (
            DelegacionAprobacion.objects
            .select_related("delegante", "delegado", "rol")
            .order_by("-creado_en")
        )

        if usuario_es_admin(usuario):
            return queryset

        # Cada actor solo ve las delegaciones que otorgó o
        # que recibió: nunca las de otros.
        return queryset.filter(
            Q(delegante=usuario) | Q(delegado=usuario)
        )


    def create(self, request, *args, **kwargs):

        usuario = request.user

        # El formulario de delegación no tiene acceso al CRUD de
        # Roles (reservado a ADMIN), así que también acepta el
        # código de rol en texto (p. ej. "DIRECTOR").
        rol_id = request.data.get("rol")
        rol_codigo = normalizar_codigo(request.data.get("rol_codigo", ""))

        try:
            if rol_codigo:
                rol = Rol.objects.get(codigo=rol_codigo)
            else:
                rol = Rol.objects.get(pk=rol_id)
        except (Rol.DoesNotExist, TypeError, ValueError):
            return Response(
                {"rol": "Debe seleccionar un rol válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        puede_delegar_este_rol = (
            usuario_es_admin(usuario)
            or UsuarioRol.objects.filter(
                usuario=usuario, rol=rol, activo=True
            ).exists()
        )

        if not puede_delegar_este_rol:
            return Response(
                {"detalle": "Solo puede delegar un rol que usted mismo posea."},
                status=status.HTTP_403_FORBIDDEN
            )

        datos = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        datos["rol"] = rol.id

        serializer = self.get_serializer(
            data=datos,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        delegacion = serializer.save(delegante=usuario, activo=True)

        registrar_bitacora(
            request=request,
            accion="DELEGAR_APROBACION",
            modulo="Identidad",
            detalle=(
                f"{usuario.email} delegó el rol {rol.codigo} a "
                f"{delegacion.delegado.email} hasta {delegacion.vigencia_hasta}."
            ),
            nivel="INFO",
        )

        return Response(
            self.get_serializer(delegacion).data,
            status=status.HTTP_201_CREATED
        )


    @action(detail=True, methods=["post"], url_path="revocar")
    def revocar(self, request, pk=None):

        delegacion = self.get_object()

        usuario = request.user

        if (
            delegacion.delegante_id != usuario.id
            and not usuario_es_admin(usuario)
        ):
            return Response(
                {"detalle": "Solo quien otorgó la delegación puede revocarla."},
                status=status.HTTP_403_FORBIDDEN
            )

        delegacion.activo = False
        delegacion.save(update_fields=["activo"])

        registrar_bitacora(
            request=request,
            accion="REVOCAR_DELEGACION_APROBACION",
            modulo="Identidad",
            detalle=(
                f"Se revocó la delegación de {delegacion.rol.codigo} "
                f"de {delegacion.delegante.email} a {delegacion.delegado.email}."
            ),
            nivel="WARNING",
        )

        return Response(self.get_serializer(delegacion).data)


# ==========================================================
# LOGIN
# ==========================================================

@api_view(["GET", "PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mi_perfil(request):
    """Consulta y actualiza solamente datos propios existentes en SIGTA."""

    usuario = request.user
    asignacion = (
        UsuarioRol.objects
        .filter(usuario=usuario, activo=True, rol__activo=True)
        .select_related("area", "rol")
        .order_by("id")
        .first()
    )

    if request.method == "PATCH":
        nombre = str(request.data.get("nombre_completo", "")).strip()
        if not nombre:
            return Response(
                {"nombre_completo": "El nombre completo es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            area = Area.objects.get(pk=request.data.get("area_id"), activo=True)
        except (Area.DoesNotExist, TypeError, ValueError):
            return Response(
                {"area_id": "Seleccione un área activa válida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.nombre_completo = nombre
        usuario.save(update_fields=["nombre_completo", "updated_at"])

        if asignacion:
            asignacion.area = area
            asignacion.save(update_fields=["area"])

        registrar_bitacora(
            request=request,
            usuario=usuario,
            accion="ACTUALIZAR_PERFIL_PROPIO",
            modulo="Usuarios",
            detalle="El usuario actualizó su nombre y área desde Mi perfil.",
            nivel="INFO",
        )

    return Response({
        "id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
        "area_id": asignacion.area_id if asignacion else None,
        "area_nombre": asignacion.area.nombre if asignacion and asignacion.area else None,
        "rol_nombre": asignacion.rol.nombre if asignacion else None,
    })


@api_view([
    "POST"
])
@permission_classes([
    AllowAny
])
def login_view(
    request
):

    email = (
        request.data
        .get(
            "email",
            ""
        )
        .strip()
        .lower()
    )


    password = (
        request.data
        .get(
            "password",
            ""
        )
    )


    # ======================================================
    # CAMPOS OBLIGATORIOS
    # ======================================================

    if (
        not email
        or not password
    ):

        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    "Ingrese correo y contraseña."
            },
            status=
                status.HTTP_400_BAD_REQUEST
        )


    # ======================================================
    # BUSCAR USUARIO
    # ======================================================

    try:

        usuario = (
            Usuario.objects.get(
                email__iexact=email
            )
        )


    except Usuario.DoesNotExist:

        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    "Credenciales inválidas."
            },
            status=
                status.HTTP_401_UNAUTHORIZED
        )


    # ======================================================
    # USUARIO INACTIVO
    # ======================================================

    if not usuario.is_active:

        registrar_bitacora(
            request=request,
            usuario=usuario,
            accion=
                "LOGIN_USUARIO_INACTIVO",
            modulo=
                "Autenticación",
            detalle=(
                f"Intento de acceso de cuenta "
                f"inactiva: {usuario.email}."
            ),
            nivel=
                "SECURITY",
        )


        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        "La cuenta se encuentra "
                        "inhabilitada."
                    )
            },
            status=
                status.HTTP_403_FORBIDDEN
        )


    # ======================================================
    # CUENTA BLOQUEADA
    # ======================================================

    if (
        usuario.locked_until
        and usuario.locked_until
        > timezone.now()
    ):

        registrar_bitacora(
            request=request,
            usuario=usuario,
            accion=
                "LOGIN_CUENTA_BLOQUEADA",
            modulo=
                "Autenticación",
            detalle=(
                "Intento de acceso durante "
                f"bloqueo temporal: {usuario.email}."
            ),
            nivel=
                "SECURITY",
        )


        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        "La cuenta está temporalmente "
                        "bloqueada."
                    )
            },
            status=
                status.HTTP_403_FORBIDDEN
        )


    # ======================================================
    # AUTENTICAR
    # ======================================================

    usuario_autenticado = (
        authenticate(
            request=request,
            username=email,
            password=password
        )
    )


    # ======================================================
    # LOGIN INCORRECTO
    # ======================================================

    if usuario_autenticado is None:

        usuario.failed_attempts += 1


        bloqueado = False


        if (
            usuario.failed_attempts
            >= settings.LOGIN_MAX_INTENTOS_FALLIDOS
        ):

            usuario.locked_until = (
                timezone.now()
                +
                timedelta(
                    minutes=settings.LOGIN_MINUTOS_BLOQUEO
                )
            )


            usuario.failed_attempts = 0


            bloqueado = True


        usuario.save(
            update_fields=[
                "failed_attempts",
                "locked_until",
            ]
        )


        registrar_bitacora(
            request=request,
            usuario=usuario,
            accion=(
                "BLOQUEO_AUTOMATICO"
                if bloqueado
                else
                "LOGIN_FALLIDO"
            ),
            modulo=
                "Autenticación",
            detalle=(
                (
                    "Cuenta bloqueada temporalmente "
                    "por intentos fallidos."
                )
                if bloqueado
                else
                (
                    "Intento de acceso fallido "
                    f"para {usuario.email}."
                )
            ),
            nivel=
                "SECURITY",
        )


        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        (
                            "La cuenta fue bloqueada "
                            "temporalmente."
                        )
                        if bloqueado
                        else
                        "Credenciales inválidas."
                    )
            },
            status=
                status.HTTP_401_UNAUTHORIZED
        )


    # ======================================================
    # LOGIN CORRECTO
    # ======================================================

    usuario.failed_attempts = 0

    usuario.locked_until = None


    usuario.save(
        update_fields=[
            "failed_attempts",
            "locked_until",
        ]
    )


    token, _ = (
        Token.objects
        .get_or_create(
            user=usuario
        )
    )

    # Un login válido debe entregar una sesión vigente, aunque existiera
    # un token de un ingreso anterior que ya haya expirado.
    horas = getattr(settings, 'SESION_TOKEN_HORAS_VALIDEZ', 12)
    if timezone.now() > token.created + timezone.timedelta(hours=horas):
        token.delete()
        token = Token.objects.create(user=usuario)


    # ======================================================
    # ROLES
    # ======================================================

    roles = []


    asignaciones = (
        UsuarioRol.objects
        .filter(
            usuario=usuario,
            activo=True,
            rol__activo=True
        )
        .select_related(
            "rol",
            "area"
        )
        .order_by(
            "rol__nombre"
        )
    )


    for asignacion in asignaciones:

        roles.append(
            {
                "id":
                    asignacion.id,

                "rol_id":
                    asignacion.rol.id,

                "codigo":
                    asignacion.rol.codigo,

                "rol_codigo":
                    asignacion.rol.codigo,

                "nombre":
                    asignacion.rol.nombre,

                "rol_nombre":
                    asignacion.rol.nombre,

                "es_global":
                    asignacion.rol.es_global,

                "area_id": (
                    asignacion.area.id
                    if asignacion.area
                    else None
                ),

                "area": (
                    asignacion.area.nombre
                    if asignacion.area
                    else None
                ),

                "area_codigo": (
                    asignacion.area.codigo
                    if asignacion.area
                    else None
                ),

                "area_nombre": (
                    asignacion.area.nombre
                    if asignacion.area
                    else None
                ),
            }
        )


    # ======================================================
    # PERMISOS
    # ======================================================

    permisos = obtener_permisos_usuario(
        usuario
    )


    # ======================================================
    # BITÁCORA
    # ======================================================

    registrar_bitacora(
        request=request,
        usuario=usuario,
        accion=
            "LOGIN_CORRECTO",
        modulo=
            "Autenticación",
        detalle=(
            "Inicio de sesión correcto "
            f"de {usuario.email}."
        ),
        nivel=
            "INFO",
    )


    # ======================================================
    # RESPUESTA
    # ======================================================

    return Response(
        {
            "ok":
                True,

            "token":
                token.key,

            "usuario": {

                "id":
                    usuario.id,

                "nombre":
                    usuario.nombre_completo,

                "nombre_completo":
                    usuario.nombre_completo,

                "email":
                    usuario.email,

                "must_change_password":
                    usuario.must_change_password,

                "roles":
                    roles,

                "permisos":
                    permisos,
            }
        },
        status=
            status.HTTP_200_OK
    )


# ==========================================================
# USUARIOS POR ROL (SELECTORES OPERATIVOS)
# ==========================================================
#
# Permite poblar selectores como "elegir auxiliar" (Servicios
# Generales) o "elegir especialista" (Jefe de UTIC) SIN abrir
# el directorio completo de usuarios (reservado a ADMIN).
# Cada rol consultable solo es visible para quien tiene una
# relación operativa real con él.
#
# GET /api/usuarios/usuarios-por-rol/?rol=AUXILIAR_SERVICIOS_GENERALES
#
# ==========================================================

MAPA_ROLES_CONSULTABLES = {
    "AUXILIAR_SERVICIOS_GENERALES": ["SERVICIOS_GENERALES"],
    "ESPECIALISTA": ["JEFE_UTIC"],
    "AGENTE": ["JEFE_UTIC"],
}


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def buscar_usuario_por_email(request):
    """Búsqueda exacta por correo (no un listado/búsqueda parcial),
    usada solo para elegir a quién delegar una aprobación temporal.
    Evita exponer el directorio completo de usuarios."""

    email = str(request.query_params.get("email", "")).strip().lower()

    if not email:
        return Response({"detalle": "Debe indicar un correo."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.get(email__iexact=email, is_active=True)
    except Usuario.DoesNotExist:
        return Response({"detalle": "No existe un usuario activo con ese correo."}, status=status.HTTP_404_NOT_FOUND)

    if usuario.id == request.user.id:
        return Response({"detalle": "No puede delegarse su propio rol a sí mismo."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def usuarios_por_rol(request):

    codigo_rol = normalizar_codigo(request.query_params.get("rol", ""))

    roles_autorizados = MAPA_ROLES_CONSULTABLES.get(codigo_rol)

    if not usuario_es_admin(request.user):

        if not roles_autorizados:
            return Response(
                {"detalle": "Consulta no permitida."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not usuario_tiene_algun_rol(request.user, *roles_autorizados):
            return Response(
                {"detalle": "No tiene permiso para consultar este listado."},
                status=status.HTTP_403_FORBIDDEN
            )

    usuarios = (
        Usuario.objects
        .filter(
            roles_asignados__rol__codigo=codigo_rol,
            roles_asignados__activo=True,
            roles_asignados__rol__activo=True,
            is_active=True,
        )
        .distinct()
        .order_by("nombre_completo")
    )

    from soporte.carga_tecnica import carga_activa
    from django.conf import settings
    return Response([
        {
            "id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "email": usuario.email,
            'carga_activa': carga_activa(usuario.pk),
            'limite_tickets': settings.SIA_MAX_TICKETS_TECNICO,
        }
        for usuario in usuarios
    ])


# ==========================================================
# CONTEXTO DEL USUARIO AUTENTICADO
# ==========================================================
#
# Este endpoint nos permitirá refrescar roles y permisos
# sin obligar al usuario a iniciar sesión otra vez.
#
# GET:
# /api/usuarios/mi-contexto/
#
# ==========================================================

@api_view([
    "GET"
])
@authentication_classes([
    TokenAuthentication
])
@permission_classes([
    IsAuthenticated
])
def mi_contexto(
    request
):

    usuario = (
        request.user
    )


    roles = []


    asignaciones = (
        UsuarioRol.objects
        .filter(
            usuario=usuario,
            activo=True,
            rol__activo=True
        )
        .select_related(
            "rol",
            "area"
        )
        .order_by(
            "rol__nombre"
        )
    )


    for asignacion in asignaciones:

        roles.append(
            {
                "id":
                    asignacion.id,

                "rol_id":
                    asignacion.rol.id,

                "codigo":
                    asignacion.rol.codigo,

                "rol_codigo":
                    asignacion.rol.codigo,

                "nombre":
                    asignacion.rol.nombre,

                "rol_nombre":
                    asignacion.rol.nombre,

                "es_global":
                    asignacion.rol.es_global,

                "delegado":
                    False,

                "area_id": (
                    asignacion.area.id
                    if asignacion.area
                    else None
                ),

                "area": (
                    asignacion.area.nombre
                    if asignacion.area
                    else None
                ),

                "area_codigo": (
                    asignacion.area.codigo
                    if asignacion.area
                    else None
                ),

                "area_nombre": (
                    asignacion.area.nombre
                    if asignacion.area
                    else None
                ),
            }
        )


    # Roles recibidos por delegación temporal y todavía vigentes:
    # el frontend debe verlos como propios (mismo menú/dashboard),
    # marcados con "delegado": True para poder avisar al usuario.
    ahora = timezone.now()

    delegaciones_vigentes = (
        DelegacionAprobacion.objects
        .filter(
            delegado=usuario,
            activo=True,
            vigencia_desde__lte=ahora,
            vigencia_hasta__gte=ahora,
            rol__activo=True,
        )
        .select_related("rol", "delegante")
    )

    for delegacion in delegaciones_vigentes:

        roles.append(
            {
                "id": f"delegacion-{delegacion.id}",
                "rol_id": delegacion.rol.id,
                "codigo": delegacion.rol.codigo,
                "rol_codigo": delegacion.rol.codigo,
                "nombre": delegacion.rol.nombre,
                "rol_nombre": delegacion.rol.nombre,
                "es_global": delegacion.rol.es_global,
                "delegado": True,
                "delegado_por": delegacion.delegante.nombre_completo,
                "delegacion_vigencia_hasta": delegacion.vigencia_hasta,
                "area_id": None,
                "area": None,
                "area_codigo": None,
                "area_nombre": None,
            }
        )


    return Response(
        {
            "ok":
                True,

            "usuario": {

                "id":
                    usuario.id,

                "nombre":
                    usuario.nombre_completo,

                "nombre_completo":
                    usuario.nombre_completo,

                "email":
                    usuario.email,

                "must_change_password":
                    usuario.must_change_password,

                "roles":
                    roles,

                "permisos":
                    obtener_permisos_usuario(
                        usuario
                    ),
            }
        },
        status=
            status.HTTP_200_OK
    )


# ==========================================================
# CAMBIO OBLIGATORIO DE CONTRASEÑA
# ==========================================================

@api_view([
    "POST"
])
@authentication_classes([
    TokenAuthentication
])
@permission_classes([
    IsAuthenticated
])
def cambiar_password_obligatorio(
    request
):

    usuario = (
        request.user
    )


    password_actual = (
        request.data
        .get(
            "password_actual",
            ""
        )
    )


    nueva_password = (
        request.data
        .get(
            "nueva_password",
            ""
        )
    )


    confirmar_password = (
        request.data
        .get(
            "confirmar_password",
            ""
        )
    )


    # ======================================================
    # CAMPOS
    # ======================================================

    if (
        not password_actual
        or not nueva_password
        or not confirmar_password
    ):

        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        "Todos los campos "
                        "son obligatorios."
                    )
            },
            status=
                status.HTTP_400_BAD_REQUEST
        )


    # ======================================================
    # CONTRASEÑA ACTUAL
    # ======================================================

    if not usuario.check_password(
        password_actual
    ):

        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        "La contraseña actual "
                        "es incorrecta."
                    )
            },
            status=
                status.HTTP_400_BAD_REQUEST
        )


    # ======================================================
    # CONFIRMACIÓN
    # ======================================================

    if (
        nueva_password
        != confirmar_password
    ):

        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        "Las contraseñas nuevas "
                        "no coinciden."
                    )
            },
            status=
                status.HTTP_400_BAD_REQUEST
        )


    # ======================================================
    # REUTILIZACIÓN
    # ======================================================

    if usuario.check_password(
        nueva_password
    ):

        return Response(
            {
                "ok":
                    False,

                "mensaje":
                    (
                        "La nueva contraseña debe ser "
                        "diferente a la actual."
                    )
            },
            status=
                status.HTTP_400_BAD_REQUEST
        )


    # ======================================================
    # COMPLEJIDAD (misma política de AUTH_PASSWORD_VALIDATORS
    # que se aplica al crear el usuario y en recuperación)
    # ======================================================

    try:
        password_validation.validate_password(nueva_password, user=usuario)
    except DjangoValidationError as error:
        return Response(
            {
                "ok": False,
                "mensaje": " ".join(error.messages),
            },
            status=status.HTTP_400_BAD_REQUEST
        )


    # ======================================================
    # GUARDAR
    # ======================================================

    usuario.set_password(
        nueva_password
    )


    usuario.must_change_password = False


    usuario.save(
        update_fields=[
            "password",
            "must_change_password",
        ]
    )


    registrar_bitacora(
        request=request,
        usuario=usuario,
        accion=
            "CAMBIO_CONTRASENA",
        modulo=
            "Autenticación",
        detalle=(
            "El usuario realizó el cambio "
            "obligatorio de contraseña."
        ),
        nivel=
            "SECURITY",
    )


    return Response(
        {
            "ok":
                True,

            "mensaje":
                (
                    "Contraseña actualizada "
                    "correctamente."
                )
        },
        status=
            status.HTTP_200_OK
    )
