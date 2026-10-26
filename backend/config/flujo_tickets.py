# 5. FLUJO DE ESTADOS (R05)
# PUNTO DE CAMBIO: ESTADOS_FUNCIONALES y TRANSICIONES_PERMITIDAS, debajo.
# Para cambiar una fase, revisar sus acciones autorizadas en soporte/views.py.
# Resolver sigue exigiendo solucion. Reapertura excepcional corresponde a R06.

"""R05 - Abierto → En proceso → Resuelto → Cerrado; Resuelto → En proceso.

Los estados BPMN existentes son subpasos: no se borran ni se renombran.
La reapertura excepcional de Cerrado se controla por separado en R06.
"""
from rest_framework.exceptions import ValidationError

ESTADOS_FUNCIONALES = {
    'BORRADOR': 'ABIERTO', 'NUEVO': 'ABIERTO', 'EN_ANALISIS': 'ABIERTO',
    'ASIGNADO': 'EN_PROCESO', 'EN_DIAGNOSTICO': 'EN_PROCESO',
    'EN_EJECUCION': 'EN_PROCESO', 'EN_VERIFICACION': 'EN_PROCESO',
    'PENDIENTE_CONFORMIDAD': 'RESUELTO', 'PENDIENTE_INFORME_FINAL': 'RESUELTO',
    'CERRADO': 'CERRADO',
}
TRANSICIONES_PERMITIDAS = {('ABIERTO', 'EN_PROCESO'), ('EN_PROCESO', 'RESUELTO'),
                         ('RESUELTO', 'CERRADO'), ('RESUELTO', 'EN_PROCESO')}


def validar_transicion(ticket, destino):
    antes = ESTADOS_FUNCIONALES.get(ticket.estado.codigo)
    despues = ESTADOS_FUNCIONALES.get(destino.codigo)
    # Los rechazos/anulaciones conservan su acción y permiso institucional.
    if not antes or not despues:
        return
    if antes != despues and (antes, despues) not in TRANSICIONES_PERMITIDAS:
        raise ValidationError({'regla': 'R05', 'detalle': f'Transición no permitida: {antes} → {despues}.'})
    if despues == 'RESUELTO' and not str(ticket.solucion or '').strip():
        raise ValidationError({'regla': 'R05', 'detalle': 'Registre un comentario de solución antes de pasar a Resuelto.'})
