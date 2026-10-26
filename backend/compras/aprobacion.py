# 8. APROBACION DE COMPRA (R08)
# Cambiar .env: SIA_REQUIERE_APROBACION_DIRECTOR=False (sin paso del Director).
# certificar_daf en compras/views.py deriva a Tesoreria y reserva el saldo.
# El grupo/umbral administrativo de este modulo aplica al modo anterior True.
# La prohibicion de aprobar la compra propia se mantiene en ambos modos.

"""R08 - Compras > SIA_UMBRAL_APROBACION_ADMINISTRATIVA y grupo autorizado.

El grupo no reemplaza DAR_VISTO_BUENO ni las fases DAF/Tesorería.
No se concede aprobación final a jefaturas técnicas por su nombre de rol.
"""
from django.conf import settings
from rest_framework.exceptions import PermissionDenied


def validar_aprobador(solicitud, usuario, final=False):
    if solicitud.solicitante_id == usuario.pk:
        raise PermissionDenied('No puede aprobar una solicitud de compra creada por usted mismo.')
    if (final and solicitud.monto_estimado is not None
            and solicitud.monto_estimado > settings.SIA_UMBRAL_APROBACION_ADMINISTRATIVA
            and not usuario.groups.filter(name=settings.SIA_GRUPO_APROBADOR).exists()):
        raise PermissionDenied(f'Las compras mayores a Bs {settings.SIA_UMBRAL_APROBACION_ADMINISTRATIVA:.2f} requieren pertenecer al grupo {settings.SIA_GRUPO_APROBADOR}.')


def puede_aprobar_final(solicitud, usuario):
    if not usuario or not usuario.is_authenticated:
        return False
    from .views import tiene_permiso
    if not settings.SIA_REQUIERE_APROBACION_DIRECTOR:
        return False
    if solicitud.estado != 'VERIFICADO_PENDIENTE_AUTORIZACION' or not tiene_permiso(usuario, 'DAR_VISTO_BUENO'):
        return False
    try:
        validar_aprobador(solicitud, usuario, final=True)
    except PermissionDenied:
        return False
    return True
