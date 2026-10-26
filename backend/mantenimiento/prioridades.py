"""R04: SLA compartido con la configuración del servidor."""
from django.conf import settings
SLA_POR_PRIORIDAD = {**settings.SIA_SLA_HORAS, 'URGENTE': settings.SIA_SLA_HORAS['CRITICA']}
