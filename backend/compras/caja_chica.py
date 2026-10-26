# 9. FONDO Y SALDO (R09)
# Cambiar .env: SIA_FONDO_MENSUAL=7000 para pasar de 5000 a 7000.
# resumen() alimenta el dashboard; registrar_operacion() bloquea insuficiencia.
# No cambiar el saldo ni sumas en Vue: Tesoreria muestra lo calculado por API.

"""R09 - Fondo mensual y control de saldo compartido por aprobación y Tesorería."""
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from usuarios.authentication import ExpiringTokenAuthentication
from config.bloqueos import escritura_serializada
from .models import FondoMensualCajaChica, MovimientoCajaChica


def mes_actual():
    return timezone.localdate().replace(day=1)


def resumen(mes=None):
    mes = mes or mes_actual()
    movimientos = MovimientoCajaChica.objects.filter(fondo__mes=mes).exclude(estado='LIBERADO')
    comprometido = movimientos.filter(estado='COMPROMETIDO').aggregate(total=Sum('monto'))['total'] or Decimal('0')
    usado = movimientos.filter(estado='DESEMBOLSADO').aggregate(total=Sum('desembolsado'))['total'] or Decimal('0')
    fondo = settings.SIA_FONDO_MENSUAL
    total = comprometido + usado
    return {'mes': mes.strftime('%Y-%m'), 'fondo_mensual': fondo, 'comprometido': comprometido,
            'utilizado': usado, 'total_utilizado_comprometido': total, 'saldo_disponible': fondo-total,
            'porcentaje_utilizado': (total/fondo*100).quantize(Decimal('0.01'))}


def _error_saldo(saldo, monto):
    return ValidationError({'regla': 'R09', 'titulo': 'Saldo insuficiente de Caja Chica',
        'detalle': f'El saldo disponible del fondo mensual es de Bs {saldo:.2f}. La compra solicitada es de Bs {monto:.2f} y no puede aprobarse porque supera el saldo disponible.',
        'saldo': str(saldo), 'monto': str(monto)})


# ==================================================
# R09 - FONDO MENSUAL Y CONTROL DE SALDO
# Configuración: SIA_FONDO_MENSUAL
# Valor inicial: 5000. Ejemplo: SIA_FONDO_MENSUAL=7000
# Función: impedir compras que superen el saldo.
# ==================================================
def registrar_operacion(solicitud, monto=None, desembolso=False, simular=False):
    if solicitud.via_adquisicion != 'CAJA_CHICA':
        return None
    monto = Decimal(str(monto if monto is not None else solicitud.monto_estimado or '0'))
    if not monto.is_finite() or monto <= 0:
        raise ValidationError({'detalle': 'Registre un monto positivo antes de comprometer Caja Chica.'})
    with escritura_serializada(), transaction.atomic():
        # La misma fila mensual serializa compras diferentes en PostgreSQL.
        anterior = MovimientoCajaChica.objects.filter(solicitud=solicitud).select_related('fondo').first()
        mes = anterior.fondo.mes if anterior else mes_actual()
        fondo, _ = FondoMensualCajaChica.objects.get_or_create(mes=mes)
        fondo = FondoMensualCajaChica.objects.select_for_update().get(pk=fondo.pk)
        anterior = MovimientoCajaChica.objects.select_for_update().filter(solicitud=solicitud).first()
        if anterior and anterior.estado == 'DESEMBOLSADO':
            if desembolso:
                raise ValidationError({'detalle': 'Esta compra ya tiene un desembolso registrado.'})
            return resumen(mes)
        actual = resumen(mes)
        credito = anterior.monto if anterior and anterior.estado == 'COMPROMETIDO' else Decimal('0')
        disponible = actual['saldo_disponible'] + credito
        if monto > disponible:
            raise _error_saldo(disponible, monto)
        saldo_despues = disponible - monto
        if not simular:
            MovimientoCajaChica.objects.update_or_create(solicitud=solicitud, defaults={
                'fondo': fondo, 'monto': monto, 'desembolsado': monto if desembolso else Decimal('0'),
                'estado': 'DESEMBOLSADO' if desembolso else 'COMPROMETIDO', 'saldo_despues': saldo_despues})
        return {**actual, 'saldo_despues': saldo_despues, 'mes': mes.strftime('%Y-%m')}


def liberar(solicitud):
    with escritura_serializada(), transaction.atomic():
        movimiento = MovimientoCajaChica.objects.filter(solicitud=solicitud).first()
        if movimiento:
            FondoMensualCajaChica.objects.select_for_update().get(pk=movimiento.fondo_id)
            MovimientoCajaChica.objects.filter(pk=movimiento.pk, estado='COMPROMETIDO').update(estado='LIBERADO')


@api_view(['GET'])
@authentication_classes([ExpiringTokenAuthentication])
@permission_classes([IsAuthenticated])
def saldo_view(request):
    from .views import tiene_permiso
    if not any(tiene_permiso(request.user, p) for p in ('REGISTRAR_DESEMBOLSO', 'EVALUAR_EXPEDIENTE', 'REALIZAR_COMPRA', 'DAR_VISTO_BUENO')):
        return Response({'detalle': 'No tiene permiso para consultar el control financiero de Caja Chica.'}, status=403)
    mes = mes_actual()
    if request.query_params.get('mes'):
        try:
            mes = date.fromisoformat(request.query_params['mes']+'-01')
        except ValueError:
            return Response({'detalle': 'Use un mes válido en formato AAAA-MM.'}, status=400)
    datos = resumen(mes)
    datos = {k: str(v) if isinstance(v, Decimal) else v for k,v in datos.items()}
    datos['movimientos'] = [{'compra_id': m.solicitud_id, 'codigo': m.solicitud.codigo,
        'titulo': m.solicitud.titulo, 'estado': m.estado, 'monto': str(m.monto),
        'desembolsado': str(m.desembolsado), 'origen_fecha': m.origen_fecha,
        'actualizado_en': m.actualizado_en.isoformat()}
        for m in MovimientoCajaChica.objects.filter(fondo__mes=mes).select_related('solicitud').order_by('-registrado_en')]
    return Response(datos)
