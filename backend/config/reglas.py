# 1. CAJA CHICA (R01): error_limite valida el valor de settings/.env.
# 2. COTIZACIONES (R02): configuracion_reglas publica el umbral real a Vue.
# 3. PRIORIDAD AUTOMATICA (R03): modificar categorias/palabras en settings.py,
# no aqui; prioridad_automatica compara el catalogo y los textos normalizados.

"""Reglas compartidas por API y modelos; configuración efectiva R01–R09 para Vue."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from django.conf import settings
from rest_framework.exceptions import ValidationError


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(texto or '').casefold())
                   if not unicodedata.combining(c))


# ==================================================
# R03 - PRIORIDAD ALTA AUTOMÁTICA
# Categorías: Red y Servidores
# Palabras clave: red, conectividad de internet
# Aplicación: Soporte y Mantenimiento
# ==================================================
def prioridad_automatica(titulo='', descripcion='', categoria=None):
    codigo = getattr(categoria, 'codigo', categoria) or ''
    nombre = getattr(categoria, 'nombre', '')
    categorias = {normalizar(c) for c in settings.SIA_CATEGORIAS_PRIORIDAD}
    if normalizar(codigo) in categorias or normalizar(nombre) in categorias:
        return settings.SIA_PRIORIDAD_AUTOMATICA
    for texto in (titulo, descripcion):
        for palabra in settings.SIA_PALABRAS_PRIORIDAD:
            patron = r'(?<!\w)' + r'\s+'.join(re.escape(p) for p in normalizar(palabra).split()) + r'(?!\w)'
            if re.search(patron, normalizar(texto)):
                return settings.SIA_PRIORIDAD_AUTOMATICA
    return None


def prioridad_objeto(obj):
    return prioridad_automatica(obj.titulo, obj.descripcion, getattr(obj, 'categoria', None))


def configuracion_reglas():
    return {
        'limite_caja_chica': str(settings.SIA_LIMITE_CAJA_CHICA),
        'umbral_cotizaciones': str(settings.SIA_UMBRAL_COTIZACIONES),
        'cotizaciones_minimas': settings.SIA_COTIZACIONES_MINIMAS,
        'proveedores_distintos': settings.SIA_PROVEEDORES_DISTINTOS,
        'categorias_prioridad': list(settings.SIA_CATEGORIAS_PRIORIDAD),
        'palabras_prioridad': list(settings.SIA_PALABRAS_PRIORIDAD),
        'prioridad_automatica': settings.SIA_PRIORIDAD_AUTOMATICA,
        'sla_horas': settings.SIA_SLA_HORAS,
        'horas_reapertura': settings.SIA_HORAS_REAPERTURA,
        'max_tickets_tecnico': settings.SIA_MAX_TICKETS_TECNICO,
        'umbral_aprobacion_administrativa': str(settings.SIA_UMBRAL_APROBACION_ADMINISTRATIVA),
        'fondo_mensual': str(settings.SIA_FONDO_MENSUAL),
        'requiere_aprobacion_director': settings.SIA_REQUIERE_APROBACION_DIRECTOR,
    }


def monto_valido(valor, requerido=True):
    if valor in (None, '') and not requerido:
        return None
    try:
        monto = Decimal(str(valor))
        if not monto.is_finite() or monto < 0 or monto.as_tuple().exponent < -2 or monto >= Decimal('10000000000'):
            raise ValueError
        return monto
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError({'costo_estimado': 'Ingrese un monto válido no negativo, con hasta dos decimales.'})


# ==================================================
# R01 - LÍMITE CONFIGURABLE DE CAJA CHICA
# Variable: SIA_LIMITE_CAJA_CHICA
# Función: impedir compras que superen el límite
# ==================================================
def error_limite(monto, via='CAJA_CHICA'):
    if via == 'CAJA_CHICA' and monto is not None and monto > settings.SIA_LIMITE_CAJA_CHICA:
        limite = settings.SIA_LIMITE_CAJA_CHICA
        return {'regla': 'R01', 'titulo': 'Compra de caja chica rechazada',
                'detalle': f'El monto de esta compra es de Bs {monto:.2f}, y supera el límite permitido de caja chica de Bs {limite:.2f}. La compra no puede aprobarse mediante caja chica.',
                'monto': str(monto), 'limite': str(limite)}
    return None


def bloquear_limite(request, obj, monto, via):
    error = error_limite(monto, via)
    if error:
        from auditoria.utils import registrar_bitacora
        registrar_bitacora(request=request, accion='R01_ENVIO_BLOQUEADO', modulo='Compras',
                           detalle=f'{obj.codigo}: {error["detalle"]} Sin rechazo formal del técnico.', nivel='WARNING')
        raise ValidationError(error)


def notificar_rechazo(obj, motivo):
    from soporte.models import NotificacionSoporte
    tecnico = getattr(obj, 'tecnico_asignado', None) or getattr(obj, 'auxiliar_asignado', None)
    if tecnico:
        origen = {'ticket': obj} if obj._meta.app_label == 'soporte' else {'mantenimiento': obj}
        NotificacionSoporte.objects.create(destinatario=tecnico, tipo='RECHAZO',
            titulo=f'{obj.codigo} · Compra rechazada', mensaje=motivo, **origen)


def rechazar_origen_por_limite(request, obj):
    """Solo se invoca desde las acciones autorizadas de Jefatura."""
    from django.db import transaction
    from auditoria.utils import registrar_bitacora
    error = error_limite(obj.costo_estimado, obj.via_compra)
    if not error:
        return None
    with transaction.atomic():
        estado = obj.estado.__class__.objects.get(codigo='CERRADO_SIN_COMPRA')
        obj.estado = estado
        obj.estado_compra_componente = 'NO_VIABLE'
        obj.motivo_no_viable = error['detalle']
        obj.activo = False
        obj.save()
        notificar_rechazo(obj, error['detalle'])
        registrar_bitacora(request=request, accion='R01_RECHAZO_JEFATURA', modulo=obj._meta.app_label,
                           detalle=f'{obj.codigo}: {error["detalle"]}', nivel='WARNING')
    return error
