from decimal import Decimal, InvalidOperation
from django.db import migrations
from django.utils import timezone


def incorporar_historicos(apps, schema_editor):
    """No altera compras ni recibos. Fecha de recibo/bitácora y fallback explícito."""
    Compra = apps.get_model('compras', 'SolicitudCompra')
    Recibo = apps.get_model('compras', 'ReciboTesoreria')
    Bitacora = apps.get_model('auditoria', 'Bitacora')
    Fondo = apps.get_model('compras', 'FondoMensualCajaChica')
    Movimiento = apps.get_model('compras', 'MovimientoCajaChica')
    estados = ['APROBADO_PARA_DESEMBOLSO', 'FONDOS_DESEMBOLSADOS', 'COMPRA_REGISTRADA', 'COMPRADO_Y_ENTREGADO', 'DESCARGO_PENDIENTE_LIQUIDACION', 'CERRADO_ARCHIVADO']
    for s in Compra.objects.filter(via_adquisicion='CAJA_CHICA', estado__in=estados).iterator():
        recibo = Recibo.objects.filter(solicitud_id=s.pk, confirmado_en__isnull=False).order_by('confirmado_en').first()
        pago = s.monto_desembolsado
        if pago is None and recibo:
            try:
                pago = Decimal(str(recibo.datos.get('monto', '0')))
            except InvalidOperation:
                pago = Decimal('0')
        monto = pago if pago is not None and pago > 0 else s.monto_estimado
        if monto is None or not monto.is_finite() or monto <= 0:
            continue
        evento = Bitacora.objects.filter(accion='DESEMBOLSAR_FONDOS' if pago else 'VISTO_BUENO_DIRECTOR', detalle__startswith=s.codigo+':').order_by('fecha').first()
        fecha = recibo.confirmado_en if recibo else evento.fecha if evento else s.creado_en
        origen = 'RECIBO' if recibo else 'BITACORA' if evento else 'REGISTRO_LEGADO'
        fondo, _ = Fondo.objects.get_or_create(mes=timezone.localtime(fecha).date().replace(day=1))
        Movimiento.objects.get_or_create(solicitud_id=s.pk, defaults={'fondo_id': fondo.pk, 'monto': monto,
            'desembolsado': pago or 0, 'estado': 'DESEMBOLSADO' if pago and pago > 0 else 'COMPROMETIDO', 'origen_fecha': origen})


class Migration(migrations.Migration):
    dependencies = [('compras', '0018_fondomensualcajachica_movimientocajachica'), ('auditoria', '0002_alter_preferenciasistema_limite_caja_chica_and_more')]
    operations = [migrations.RunPython(incorporar_historicos, migrations.RunPython.noop)]
