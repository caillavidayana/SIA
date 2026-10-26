"""Recibos imprimibles y respaldos privados de la entrega de fondos."""
from decimal import Decimal
from uuid import uuid4
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from auditoria.utils import registrar_bitacora
from soporte.informes_pdf import _documento_pdf
from .models import ReciboTesoreria, SolicitudCompra
from .serializers import MontoEstimadoField


def datos_entrega(data):
    nombre = ' '.join(str(data.get('responsable_adquisicion', '')).split())
    if len(nombre.split()) < 2 or len(nombre) > 150 or not all(any(c.isalpha() for c in parte) for parte in nombre.split()):
        raise ValidationError({'detalle': 'Ingrese el nombre completo de quien recibe los fondos, con nombres y apellidos.'})
    tipo = str(data.get('tipo_desembolso', '')).strip()
    if tipo not in {'Efectivo', 'Transferencia', 'QR'}:
        raise ValidationError({'detalle': 'Seleccione Efectivo, Transferencia o QR.'})
    monto = MontoEstimadoField(max_digits=12, decimal_places=2, min_value=Decimal('0.01')).run_validation(data.get('monto_desembolsado', ''))
    return {'recibe': nombre, 'metodo': tipo, 'monto': str(monto)}


def pdf_recibo(datos):
    from types import SimpleNamespace
    seccion_saldo = [('CONTROL DE CAJA CHICA', [('Mes del fondo', datos['mes_fondo']), ('Saldo restante proyectado después de esta entrega', 'Bs. '+datos['saldo_restante']), ('Momento del saldo', 'Calculado al emitir este recibo. La confirmación vuelve a validar el saldo y la operación se registra una sola vez.')])] if 'saldo_restante' in datos else []
    return _documento_pdf(
        'RECIBO DE ENTREGA DE FONDOS', 'Caja Chica - constancia para impresión y firma',
        SimpleNamespace(codigo=datos['codigo']),
        [('REQUERIMIENTO', [('Objeto de la compra', datos['titulo']), ('Área solicitante', datos['area']), ('Solicitante', datos['solicitante'])]),
         ('ENTREGA DE FONDOS', [('Importe entregado', f"Bs. {datos['monto']}"), ('Método de desembolso', datos['metodo']), ('Nombre completo de quien recibe', datos['recibe']), ('Nombre completo de quien entrega', datos['entrega'])]),
         ('CONFORMIDAD', [('Declaración', 'Quien recibe declara haber recibido el importe indicado para el requerimiento identificado en este recibo.'), ('Respaldo', 'Imprimir, firmar por ambas partes y adjuntar el PDF firmado en Tesorería. Para transferencia o QR, adjuntar también el comprobante de la operación.')])] + seccion_saldo,
        [('Referencia del recibo', datos['referencia']), ('Fecha de emisión', datos['fecha'])],
        unidad='TESORERÍA', espaciado=True, firmas=[([], datos['recibe'], 'Firma de quien recibe'), ([], datos['entrega'], 'Firma de quien entrega')],
    )


def representar(recibo):
    base = f'/api/compras/solicitudes/{recibo.solicitud_id}/recibos-tesoreria/{recibo.pk}'
    return {'id': recibo.pk, 'referencia': str(recibo.referencia), 'datos': recibo.datos,
            'generado_en': recibo.generado_en, 'confirmado_en': recibo.confirmado_en,
            'original_url': base + '/original/',
            'firmado_url': base + '/firmado/' if recibo.firmado else None,
            'comprobante_url': base + '/comprobante/' if recibo.comprobante else None,
            'saldo_confirmado_url': base + '/constancia_saldo/' if recibo.constancia_saldo else None}


@transaction.atomic
def recibos(view, request):
    from .views import tiene_permiso, respuesta_sin_permiso
    s = view.get_object()
    if not tiene_permiso(request.user, 'REGISTRAR_DESEMBOLSO'):
        return respuesta_sin_permiso('REGISTRAR_DESEMBOLSO')
    if request.method == 'GET':
        return Response([{**representar(r), 'puede_reanudar': r.generado_por_id == request.user.pk and not r.confirmado_en}
                         for r in s.recibos_tesoreria.order_by('-generado_en', '-pk')])
    s = SolicitudCompra.objects.select_for_update().get(pk=s.pk)
    if s.estado != 'APROBADO_PARA_DESEMBOLSO' or s.cerrado_inmutable:
        return Response({'detalle': 'Solo se generan recibos de expedientes pendientes de desembolso.'}, status=409)
    datos = datos_entrega(request.data)
    referencia = uuid4()
    datos.update(codigo=s.codigo, titulo=s.titulo, solicitante=s.solicitante.nombre_completo,
                 area=s.area.nombre if s.area_id else 'Sin área', entrega=request.user.nombre_completo,
                 usuario_entrega=request.user.pk, referencia=str(referencia),
                 fecha=timezone.localtime().strftime('%d/%m/%Y %H:%M'))
    from .caja_chica import registrar_operacion
    financiero = registrar_operacion(s, monto=datos['monto'], simular=True)
    if financiero:
        datos.update(mes_fondo=financiero['mes'], saldo_restante=str(financiero['saldo_despues']))
    r = ReciboTesoreria(solicitud=s, referencia=referencia, datos=datos, generado_por=request.user)
    r.original.save(f'recibo-{referencia}.pdf', ContentFile(pdf_recibo(datos)), save=False)
    r.save()
    registrar_bitacora(request=request, accion='GENERAR_RECIBO_TESORERIA', modulo='Compras',
                      detalle=f'{s.codigo}: recibo {referencia}, recibe {datos["recibe"]}, entrega {datos["entrega"]}, Bs. {datos["monto"]}.', nivel='INFO')
    return Response(representar(r), status=201)


def validar_archivo(archivo, pdf=False):
    if not archivo:
        raise ValidationError({'detalle': 'Adjunte el PDF del recibo con las firmas de quien recibe y quien entrega.' if pdf else 'Adjunte el comprobante de transferencia o QR.'})
    if archivo.size > 10 * 1024 * 1024 or not archivo.size:
        raise ValidationError({'detalle': 'El archivo debe tener contenido y pesar hasta 10 MB.'})
    cabecera = archivo.read(12)
    archivo.seek(0)
    es_pdf = cabecera.startswith(b'%PDF-')
    es_imagen = cabecera.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff')) or (cabecera.startswith(b'RIFF') and cabecera[8:12] == b'WEBP')
    if (pdf and not es_pdf) or (not pdf and not (es_pdf or es_imagen)):
        raise ValidationError({'detalle': 'Adjunte un PDF válido.' if pdf else 'El comprobante debe ser PDF, PNG, JPG o WEBP.'})


@transaction.atomic
def confirmar(view, request):
    from .views import tiene_permiso, respuesta_sin_permiso
    s = view.get_object()
    if not tiene_permiso(request.user, 'REGISTRAR_DESEMBOLSO'):
        return respuesta_sin_permiso('REGISTRAR_DESEMBOLSO')
    s = SolicitudCompra.objects.select_for_update().get(pk=s.pk)
    if s.estado != 'APROBADO_PARA_DESEMBOLSO' or s.cerrado_inmutable:
        return Response({'detalle': 'El expediente no está aprobado para desembolso.'}, status=409)
    recibo_id = str(request.data.get('recibo_id', ''))
    if not recibo_id.isdigit():
        raise ValidationError({'detalle': 'Genere primero el recibo de entrega de fondos.'})
    r = get_object_or_404(ReciboTesoreria.objects.select_for_update(), pk=recibo_id, solicitud=s, generado_por=request.user)
    if r.confirmado_en:
        return Response({'detalle': 'Este recibo ya fue confirmado.'}, status=409)
    ultimo = s.recibos_tesoreria.filter(generado_por=request.user).order_by('-generado_en', '-pk').first()
    if ultimo.pk != r.pk:
        return Response({'detalle': 'Utilice el último recibo generado para estos datos.'}, status=409)
    datos = datos_entrega(request.data)
    if any(datos[k] != r.datos[k] for k in ('monto', 'metodo', 'recibe')):
        return Response({'detalle': 'Los datos cambiaron. Genere e imprima un nuevo recibo antes de adjuntar las firmas.'}, status=409)
    if s.codigo != r.datos['codigo'] or s.titulo != r.datos['titulo']:
        return Response({'detalle': 'El requerimiento cambió. Genere un nuevo recibo.'}, status=409)
    firmado = request.FILES.get('recibo_firmado')
    validar_archivo(firmado, pdf=True)
    comprobante = request.FILES.get('comprobante_desembolso')
    if datos['metodo'] != 'Efectivo':
        validar_archivo(comprobante)
    elif comprobante:
        validar_archivo(comprobante)
    # R09: convertir el compromiso en desembolso; no descontar otra vez.
    from .caja_chica import registrar_operacion
    from config.reglas import error_limite
    error = error_limite(Decimal(datos['monto']), s.via_adquisicion)
    if error:
        return Response(error, status=400)
    financiero = registrar_operacion(s, monto=datos['monto'], desembolso=True)
    if financiero:
        # R09: evidencia del saldo real al confirmar, sin alterar el PDF firmado.
        from types import SimpleNamespace
        constancia = _documento_pdf('CONSTANCIA DE SALDO DE CAJA CHICA', 'Complemento del recibo firmado; no sustituye sus firmas.',
            SimpleNamespace(codigo=s.codigo),
            [('SALDO DESPUÉS DEL DESEMBOLSO', [('Mes del fondo', financiero['mes']), ('Importe entregado', 'Bs. '+datos['monto']),
                ('Saldo disponible después de la operación', f'Bs. {financiero["saldo_despues"]:.2f}'), ('Referencia del recibo', str(r.referencia)),
                ('Fecha de confirmación', timezone.localtime().strftime('%d/%m/%Y %H:%M'))])], [], unidad='TESORERÍA')
        r.constancia_saldo.save(f'saldo-confirmado-{r.referencia}.pdf', ContentFile(constancia), save=False)
    r.firmado = firmado
    if comprobante:
        r.comprobante = comprobante
    r.confirmado_en = timezone.now()
    r.save(update_fields=['firmado', 'comprobante', 'confirmado_en', 'constancia_saldo'])
    s.monto_desembolsado = Decimal(datos['monto'])
    s.responsable_adquisicion = datos['recibe']
    s.tipo_desembolso = datos['metodo']
    # Mantener el respaldo que consultan los carriles ya existentes.
    if comprobante:
        s.comprobante_desembolso = comprobante
    else:
        with r.firmado.open('rb') as copia:
            s.comprobante_desembolso = ContentFile(copia.read(), name=f'recibo-firmado-{r.referencia}.pdf')
    s.save(update_fields=['monto_desembolsado', 'responsable_adquisicion', 'tipo_desembolso', 'comprobante_desembolso', 'actualizado_en'])
    registrar_bitacora(request=request, accion='ADJUNTAR_RECIBO_FIRMADO', modulo='Compras',
                      detalle=f'{s.codigo}: recibo {r.referencia} firmado y respaldo de {datos["metodo"]} archivados por {request.user.nombre_completo}.', nivel='INFO')
    return view._transicion(request, s, 'REGISTRAR_DESEMBOLSO', ['APROBADO_PARA_DESEMBOLSO'], 'FONDOS_DESEMBOLSADOS', 'DESEMBOLSAR_FONDOS', 'Tesorería registró la entrega de fondos con recibo firmado.')


def archivo_recibo(view, request, recibo_id, clase):
    from .views import tiene_permiso, respuesta_sin_permiso
    s = view.get_object()
    if not tiene_permiso(request.user, 'REGISTRAR_DESEMBOLSO'):
        return respuesta_sin_permiso('REGISTRAR_DESEMBOLSO')
    r = get_object_or_404(ReciboTesoreria, pk=recibo_id, solicitud=s)
    archivo = getattr(r, clase)
    if not archivo:
        from rest_framework.exceptions import NotFound
        raise NotFound('No existe este documento en el recibo.')
    import mimetypes
    try:
        respuesta = FileResponse(archivo.open('rb'), content_type=mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream')
    except FileNotFoundError:
        from rest_framework.exceptions import NotFound
        raise NotFound('No se encontró el archivo del recibo.')
    respuesta['Cache-Control'] = 'private, no-store'
    respuesta['X-Content-Type-Options'] = 'nosniff'
    return respuesta
