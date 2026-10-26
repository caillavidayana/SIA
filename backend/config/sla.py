# 4. TIEMPOS DE ATENCION (R04)
# Cambiar .env: SIA_SLA_ALTA_HORAS, SIA_SLA_MEDIA_HORAS, SIA_SLA_BAJA_HORAS.
# horas_sla/fecha_limite consumen esa configuracion; no poner horas fijas aqui.

"""R04 - SLA según prioridad; valores únicos en SIA_SLA_*_HORAS (.env)."""
from datetime import timedelta
from django.conf import settings
from django.utils import timezone


def horas_sla(prioridad):
    return settings.SIA_SLA_HORAS['CRITICA' if prioridad == 'URGENTE' else prioridad]


def fecha_limite(obj, prioridad):
    inicio = getattr(obj, 'reabierto_en', None) or obj.creado_en or timezone.now()
    return inicio + timedelta(hours=horas_sla(prioridad))
