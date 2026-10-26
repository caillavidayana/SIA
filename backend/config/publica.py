# 10. CONTRASENAS (R10)
# El minimo se lee de AUTH_PASSWORD_VALIDATORS en config/settings.py.
# Cambiar alli OPTIONS.min_length (ejemplo: 10 -> 12), no en esta respuesta.
# Las pantallas consultan esta API y conservan la politica existente.

"""Metadatos públicos de presentación; no autentica ni cambia contraseñas."""
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def configuracion_publica(request):
    # R10: la interfaz lee la política existente, sin repetir un mínimo distinto.
    longitud=next(v.get('OPTIONS',{}).get('min_length',0) for v in settings.AUTH_PASSWORD_VALIDATORS
        if v['NAME'].endswith('MinimumLengthValidator'))
    return Response({'password_min_length':longitud})
