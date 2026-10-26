# 2. COTIZACIONES (R02)
# Cambiar .env: SIA_UMBRAL_COTIZACIONES (500), SIA_COTIZACIONES_MINIMAS (3).
# requeridas() calcula el minimo; progreso() cuenta proveedores validos.
# La misma regla se usa al enviar y aprobar, sin duplicar el umbral.

"""R02: cotizaciones de origen, proveedores, borradores y transferencia."""
import json
import re
from django.conf import settings
from django.core.files import File
from rest_framework.exceptions import ValidationError
from config.reglas import normalizar


# ==================================================
# R02 - TRES COTIZACIONES DE PROVEEDORES DISTINTOS
# REQUERIMIENTO 2: SIA_UMBRAL_COTIZACIONES (Bs 500 inicialmente)
# Función: validar cotizaciones antes de aprobación
# ==================================================
def identidad_proveedor(nombre, identificador=''):
    # Un NIT/documento identifica al proveedor si está disponible; si no,
    # normalizar nombres evita contar variantes de acentos, espacios o signos.
    limpio = re.sub(r'[^a-z0-9]', '', normalizar(nombre))
    documento = re.sub(r'[^a-z0-9]', '', normalizar(identificador))
    return f'id:{documento}' if documento else f'nombre:{limpio}' if limpio else ''


def requeridas(monto):
    return settings.SIA_COTIZACIONES_MINIMAS if monto is not None and monto > settings.SIA_UMBRAL_COTIZACIONES else 1


def cotizaciones_origen(obj):
    soporte = obj._meta.app_label == 'soporte'
    resultado = []
    for c in obj.cotizaciones_r02.all():
        archivo = c.documento if soporte else c.archivo
        resultado.append({'id': c.pk, 'proveedor': c.proveedor,
            'empresa': c.empresa, 'proveedor_identificador': c.proveedor_identificador, 'archivo': archivo,
            'nombre_original': archivo.name.split('/')[-1] if soporte else c.nombre_original,
            'creado_en': c.creado_en, 'instancia': c})
    # No reemplazar ni descartar proformas históricas.
    if obj.cotizacion_archivo and not any(c['archivo'].name == obj.cotizacion_archivo.name for c in resultado):
        resultado.append({'id': None, 'proveedor': getattr(obj, 'proveedor_cotizacion', ''),
            'empresa': '', 'proveedor_identificador': '', 'archivo': obj.cotizacion_archivo,
            'nombre_original': obj.cotizacion_archivo.name.split('/')[-1], 'creado_en': None, 'instancia': None})
    return resultado


def datos_cotizaciones(obj):
    return [{'id': c['id'], 'proveedor': c['proveedor'], 'proveedor_identificador': c['proveedor_identificador'],
             'empresa': c.get('empresa', ''), 'nombre_original': c['nombre_original'], 'creado_en': c['creado_en'],
             'archivo_url': '/media/' + c['archivo'].name if c['archivo'] else None}
            for c in cotizaciones_origen(obj)]


def nuevas_cotizaciones(request):
    archivos = list(request.FILES.getlist('cotizaciones')) + list(request.FILES.getlist('cotizaciones_archivos'))
    antiguo = request.FILES.get('cotizacion_archivo')
    if antiguo is not None and all(antiguo is not a for a in archivos):
        archivos.append(antiguo)
    try:
        metadata = request.data.get('cotizaciones_metadata', '[]')
        metadata = json.loads(metadata) if isinstance(metadata, str) else metadata
        if not isinstance(metadata, list) or len(metadata) not in (0, len(archivos)):
            raise ValueError
        if any(not isinstance(m, dict) for m in metadata):
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError({'detalle': 'Los datos de proveedores deben corresponder a cada cotización adjunta.'})
    resultado = []
    for i, archivo in enumerate(archivos):
        if not archivo.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.webp')) or not 0 < archivo.size <= 10 * 1024 * 1024:
            raise ValidationError({'detalle': 'Adjunte cotizaciones PDF, JPG, PNG o WEBP de hasta 10 MB, no vacías.'})
        m = metadata[i] if metadata else {'proveedor': request.data.get('proveedor_cotizacion', '')}
        proveedor = str(m.get('proveedor', '')).strip()
        identificador = str(m.get('proveedor_identificador', '')).strip()
        empresa = str(m.get('empresa', '')).strip()
        if len(empresa) > 180:
            raise ValidationError({'detalle': 'El nombre de empresa admite hasta 180 caracteres.'})
        if len(proveedor) > 180 or len(identificador) > 60:
            raise ValidationError({'detalle': 'El proveedor admite 180 caracteres y su identificador 60.'})
        resultado.append({'archivo': archivo, 'proveedor': proveedor, 'proveedor_identificador': identificador, 'empresa': empresa})
    return resultado


def actualizar_proveedores(obj, request):
    """Completar proveedores de borradores propios sin reemplazar documentos."""
    try:
        datos = json.loads(request.data.get('proveedores_guardados', '[]'))
        if not isinstance(datos, list):
            raise ValueError
        for fila in datos:
            registro = obj.cotizaciones_r02.filter(pk=fila['id']).first()
            if registro is None:
                raise ValueError
            proveedor = str(fila.get('proveedor', '')).strip()
            identificador = str(fila.get('proveedor_identificador', '')).strip()
            if len(proveedor) > 180 or len(identificador) > 60:
                raise ValueError
            registro.empresa = str(fila.get('empresa', registro.empresa)).strip()
            if len(registro.empresa) > 180:
                raise ValueError
            registro.proveedor, registro.proveedor_identificador = proveedor, identificador
            registro.save(update_fields=['proveedor', 'proveedor_identificador', 'empresa'])
        # Se descartó la caché de prefetch porque ahora se validan esos cambios.
        getattr(obj, '_prefetched_objects_cache', {}).pop('cotizaciones_r02', None)
    except (ValueError, KeyError, TypeError):
        raise ValidationError({'detalle': 'Revise los proveedores guardados de este expediente.'})


def progreso(monto, cotizaciones):
    validas = [c for c in cotizaciones if c.get('archivo') and identidad_proveedor(c.get('proveedor', ''))]
    # Nombres idénticos tampoco se pueden separar inventando distintos NIT.
    nombres, ids, cuenta = set(), set(), 0
    for c in validas:
        nombre = identidad_proveedor(c['proveedor'])
        clave = identidad_proveedor(c['proveedor'], c.get('proveedor_identificador', ''))
        if settings.SIA_PROVEEDORES_DISTINTOS and (nombre in nombres or clave in ids):
            continue
        nombres.add(nombre)
        ids.add(clave)
        cuenta += 1
    cantidad = requeridas(monto)
    return {'cotizaciones_requeridas': cantidad, 'cotizaciones_actuales': cuenta,
            'cotizaciones_faltantes': max(0, cantidad - cuenta)}


def validar_cotizaciones(obj, monto=None, nuevas=()):
    estado = progreso(obj.costo_estimado if monto is None else monto, cotizaciones_origen(obj) + list(nuevas))
    if estado['cotizaciones_faltantes']:
        raise ValidationError({'regla': 'R02', 'titulo': 'Cotizaciones adicionales requeridas',
            'detalle': f"Debe adjuntar {estado['cotizaciones_requeridas']} cotización(es) válidas de proveedores distintos. Actualmente tiene {estado['cotizaciones_actuales']}; faltan {estado['cotizaciones_faltantes']}.", **estado})
    return estado


def guardar_cotizaciones(obj, nuevas, usuario):
    from .models import CotizacionCompra
    from mantenimiento.models import CotizacionMantenimiento
    for c in nuevas:
        if obj._meta.app_label == 'soporte':
            registro = CotizacionCompra.objects.create(ticket_soporte=obj, documento=c['archivo'],
                empresa=c.get('empresa', ''), proveedor=c['proveedor'], proveedor_identificador=c['proveedor_identificador'],
                descripcion=obj.componente_requerido, cantidad=obj.cantidad_componente, precio_unitario=None, creada_por=usuario)
            archivo = registro.documento
        else:
            registro = CotizacionMantenimiento.objects.create(requerimiento=obj, archivo=c['archivo'],
                nombre_original=c['archivo'].name, empresa=c.get('empresa', ''), proveedor=c['proveedor'],
                proveedor_identificador=c['proveedor_identificador'], creado_por=usuario)
            archivo = registro.archivo
        if not obj.cotizacion_archivo:
            obj.cotizacion_archivo = archivo.name


def transferir_cotizaciones(obj, solicitud, usuario):
    """Mantener todos los documentos y su origen; no duplicar por reintentos."""
    from .models import CotizacionCompra
    if obj._meta.app_label == 'soporte':
        obj.cotizaciones_r02.filter(solicitud__isnull=True).update(solicitud=solicitud)
        principal = obj.cotizaciones_r02.order_by('creado_en', 'pk').first()
        if principal:
            # El campo histórico proforma usa almacenamiento público protegido;
            # los registros de cotización continúan en almacenamiento privado.
            with principal.documento.open('rb') as stream:
                solicitud.proforma.save(principal.documento.name.split('/')[-1], File(stream), save=False)
            solicitud.save(update_fields=['proforma', 'actualizado_en'])
        return
    for origen in obj.cotizaciones_r02.all():
        if CotizacionCompra.objects.filter(cotizacion_mantenimiento=origen).exists():
            continue
        registro = CotizacionCompra(solicitud=solicitud, cotizacion_mantenimiento=origen,
            empresa=origen.empresa, proveedor=origen.proveedor, proveedor_identificador=origen.proveedor_identificador,
            descripcion=obj.producto_requerido, cantidad=obj.cantidad_requerida or 1,
            precio_unitario=None, creada_por=usuario)
        with origen.archivo.open('rb') as stream:
            registro.documento.save(origen.nombre_original or origen.archivo.name.split('/')[-1], File(stream), save=False)
        registro.save()


def validar_solicitud(solicitud):
    # Los expedientes históricos de bajo monto conservan su proforma.
    cotizaciones = [{'archivo': c.documento, 'proveedor': c.proveedor,
        'proveedor_identificador': c.proveedor_identificador} for c in solicitud.cotizaciones.all()]
    if requeridas(solicitud.monto_estimado) == 1 and solicitud.proforma and not cotizaciones:
        return
    estado = progreso(solicitud.monto_estimado, cotizaciones)
    if estado['cotizaciones_faltantes']:
        raise ValidationError({'regla': 'R02', 'detalle': 'Complete las cotizaciones de proveedores distintos antes de aprobar.', **estado})
