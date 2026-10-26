"""Acceso a evidencia con autorización del expediente y enlaces temporales."""
import hashlib
import mimetypes
from urllib.parse import urlsplit, urlencode
from django.core import signing
from django.db.models import Q, FileField
from django.http import FileResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .authentication import ExpiringTokenAuthentication

SALT = 'sia.archivo.expediente'


def firmar_urls(datos, request):
    if isinstance(datos, dict):
        return {k: firmar_urls(v, request) for k, v in datos.items()}
    if isinstance(datos, list):
        return [firmar_urls(v, request) for v in datos]
    if not isinstance(datos, str) or not request or not request.user.is_authenticated:
        return datos
    ruta = urlsplit(datos).path
    if not ruta.startswith('/media/'):
        return datos
    token = getattr(request, 'auth', None)
    if not getattr(token, 'key', None):
        return ruta
    ticket = signing.dumps({'usuario': request.user.pk, 'ruta': ruta, 'sesion': hashlib.sha256(token.key.encode()).hexdigest()}, salt=SALT)
    return ruta + '?' + urlencode({'acceso': ticket})


class AccesoArchivoAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return 'Token'
    def authenticate(self, request):
        if request.headers.get('Authorization'):
            return ExpiringTokenAuthentication().authenticate(request)
        acceso = request.query_params.get('acceso')
        if not acceso:
            return None
        try:
            datos = signing.loads(acceso, salt=SALT, max_age=300)
            if datos['ruta'] != request.path:
                raise AuthenticationFailed('El enlace no corresponde a este archivo.')
            token = Token.objects.get(user_id=datos['usuario'])
            if hashlib.sha256(token.key.encode()).hexdigest() != datos['sesion']:
                raise AuthenticationFailed('La sesión del enlace finalizó.')
        except (signing.BadSignature, KeyError, Token.DoesNotExist):
            raise AuthenticationFailed('El enlace de evidencia expiró o no es válido.')
        return ExpiringTokenAuthentication().authenticate_credentials(token.key)


@api_view(['GET'])
@authentication_classes([AccesoArchivoAuthentication])
@permission_classes([IsAuthenticated])
def archivo_expediente(request, ruta):
    from compras.views import SolicitudCompraViewSet
    from mantenimiento.views import RequerimientoMantenimientoViewSet
    from soporte.views import TicketViewSet
    if '..' in ruta.split('/') or ruta.startswith('/'):
        raise NotFound()
    if request.user.must_change_password:
        raise AuthenticationFailed('Debe cambiar su contraseña antes de consultar documentos.')
    for clase in (SolicitudCompraViewSet, RequerimientoMantenimientoViewSet, TicketViewSet):
        vista = clase()
        vista.request, vista.action = request, 'retrieve'
        queryset = vista.get_queryset()
        # R02: las cotizaciones adicionales heredan el acceso del expediente.
        # Se usa su almacenamiento real (incluido el privado), sin exponer rutas.
        from compras.models import CotizacionCompra
        from mantenimiento.models import CotizacionMantenimiento
        extras = []
        etiqueta = queryset.model._meta.label_lower
        if etiqueta == 'compras.solicitudcompra':
            extras = [c.documento for c in CotizacionCompra.objects.filter(solicitud__in=queryset, documento=ruta)]
        elif etiqueta == 'soporte.ticket':
            extras = [c.documento for c in CotizacionCompra.objects.filter(ticket_soporte__in=queryset, documento=ruta)]
            if not extras:
                # R06: el acceso a archivos anteriores depende del mismo ticket.
                from django.db.models.fields.files import FieldFile
                for historico in queryset.filter(historial_reaperturas__icontains=ruta):
                    for ciclo in historico.historial_reaperturas:
                        for campo, nombre in ciclo.get('archivos', {}).items():
                            if nombre == ruta:
                                return respuesta_archivo(FieldFile(historico, historico._meta.get_field(campo), nombre))
        elif etiqueta == 'mantenimiento.requerimientomantenimiento':
            extras = [c.archivo for c in CotizacionMantenimiento.objects.filter(requerimiento__in=queryset, archivo=ruta)]
        if extras:
            return respuesta_archivo(extras[0])
        campos = [c.name for c in queryset.model._meta.fields if isinstance(c, FileField)]
        filtro = Q()
        for campo in campos:
            filtro |= Q(**{campo: ruta})
        obj = queryset.filter(filtro).first()
        if not obj:
            continue
        for campo in campos:
            archivo = getattr(obj, campo)
            if archivo and archivo.name == ruta:
                try:
                    stream = archivo.open('rb')
                except FileNotFoundError:
                    raise NotFound()
                tipo = mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream'
                respuesta = FileResponse(stream, content_type=tipo, as_attachment=tipo not in {'application/pdf', 'image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/bmp'})
                respuesta['Cache-Control'] = 'private, no-store'
                respuesta['X-Content-Type-Options'] = 'nosniff'
                respuesta['Referrer-Policy'] = 'no-referrer'
                respuesta['X-Frame-Options'] = 'SAMEORIGIN'
                return respuesta
    raise NotFound()


def respuesta_archivo(archivo):
    try:
        stream = archivo.open('rb')
    except FileNotFoundError:
        raise NotFound()
    tipo = mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream'
    respuesta = FileResponse(stream, content_type=tipo, as_attachment=tipo not in {'application/pdf', 'image/png', 'image/jpeg', 'image/webp'})
    respuesta['Cache-Control'] = 'private, no-store'
    respuesta['X-Content-Type-Options'] = 'nosniff'
    respuesta['Referrer-Policy'] = 'no-referrer'
    respuesta['X-Frame-Options'] = 'SAMEORIGIN'
    return respuesta
