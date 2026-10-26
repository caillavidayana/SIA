# 7. CARGA DEL TECNICO (R07)
# Cambiar .env: SIA_MAX_TICKETS_TECNICO=8 para pasar de 5 a 8 activos.
# carga_activa cuenta; bloquear_y_validar impide exceder el limite.
# El cierre/resolucion libera cupo segun los estados activos existentes.

"""R07 - Cupo configurable; contar únicamente Abierto/En proceso del BPMN."""
from django.conf import settings
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from usuarios.models import Usuario
from .models import Ticket

ESTADOS_ACTIVOS = ('BORRADOR','NUEVO','EN_ANALISIS','ASIGNADO','EN_DIAGNOSTICO','EN_EJECUCION','EN_VERIFICACION')


def carga_activa(tecnico_id, excluir_ticket=None, excluir_mantenimiento=None):
    from mantenimiento.models import RequerimientoMantenimiento
    soporte=Ticket.objects.filter(Q(tecnico_asignado_id=tecnico_id)|Q(especialistas_apoyo__pk=tecnico_id),estado__codigo__in=ESTADOS_ACTIVOS).exclude(pk=excluir_ticket).distinct().count()
    mantenimiento=RequerimientoMantenimiento.objects.filter(auxiliar_asignado_id=tecnico_id,estado__codigo__in=('RECIBIDO','VALIDADO','DERIVADO','REVISION_ALMACEN','EN_ESPERA_COMPRA','EN_MANTENIMIENTO')).exclude(pk=excluir_mantenimiento).count()
    return soporte+mantenimiento


def bloquear_y_validar(tecnicos, excluir_ticket=None, excluir_mantenimiento=None):
    # Invocar dentro de atomic. Orden estable para múltiples responsables.
    for tecnico in Usuario.objects.select_for_update().filter(pk__in=tecnicos).order_by('pk'):
        if not tecnico.is_active:
            raise ValidationError({'detalle':'El técnico está inactivo.'})
        cantidad=carga_activa(tecnico.pk, excluir_ticket, excluir_mantenimiento)
        if cantidad >= settings.SIA_MAX_TICKETS_TECNICO:
            raise ValidationError({'regla':'R07','detalle':f'El técnico tiene {cantidad} tickets activos. El límite permitido es {settings.SIA_MAX_TICKETS_TECNICO}.','limite':settings.SIA_MAX_TICKETS_TECNICO})
