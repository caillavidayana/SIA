"""
URL configuration for config project.

SIGTA - Sistema Integral de Gestión
de Tickets y Aprobaciones.
"""

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

from django.urls import (
    include,
    path,
)


# ==========================================================
# RUTAS PRINCIPALES
# ==========================================================

from compras.caja_chica import saldo_view
from config.publica import configuracion_publica

urlpatterns = [
    path('api/configuracion-publica/', configuracion_publica, name='configuracion-publica'),
    path('api/caja-chica/saldo/', saldo_view, name='saldo-caja-chica'),

    # ======================================================
    # ADMINISTRACIÓN DJANGO
    # ======================================================

    path(
        "admin/",
        admin.site.urls
    ),


    # ======================================================
    # USUARIOS / AUTENTICACIÓN / ROLES / ÁREAS
    # ======================================================

    path(
        "api/usuarios/",
        include(
            "usuarios.urls"
        )
    ),


    # ======================================================
    # SOPORTE TÉCNICO
    # ======================================================

    path(
        "api/soporte/",
        include(
            "soporte.urls"
        )
    ),

    path(
        "api/mantenimiento/",
        include("mantenimiento.urls")
    ),

    # ======================================================
    # COMPRAS
    # ======================================================

    path(
        "api/compras/",
        include(
            "compras.urls"
        )
    ),


    # ======================================================
    # AUDITORÍA
    # ======================================================

    path(
        "api/auditoria/",
        include(
            "auditoria.urls"
        )
    ),


    # ======================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ======================================================

    path(
        "api/recuperacion/",
        include(
            "recuperacion.urls"
        )
    ),
]


# ==========================================================
# ARCHIVOS MULTIMEDIA
# ==========================================================
#
# Durante desarrollo Django permite acceder a:
#
# /media/soporte/evidencias/...
#
# En producción estos archivos deberían ser atendidos
# por un servidor web o almacenamiento dedicado.
# ==========================================================

from usuarios.archivos import archivo_expediente
urlpatterns += [path('media/<path:ruta>', archivo_expediente, name='archivo-expediente')]
