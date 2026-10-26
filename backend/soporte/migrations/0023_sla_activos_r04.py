from datetime import timedelta
from django.conf import settings
from django.db import migrations


def actualizar_sla_activos(apps, schema_editor):
    Ticket = apps.get_model('soporte', 'Ticket')
    finales = ['PENDIENTE_CONFORMIDAD', 'PENDIENTE_INFORME_FINAL', 'CERRADO', 'CERRADO_SIN_COMPRA', 'RECHAZADO', 'ANULADO']
    for ticket in Ticket.objects.exclude(estado__codigo__in=finales).iterator():
        prioridad = ticket.prioridad or 'MEDIA'
        horas = settings.SIA_SLA_HORAS.get(prioridad, settings.SIA_SLA_HORAS['MEDIA'])
        Ticket.objects.filter(pk=ticket.pk).update(prioridad=prioridad, sla_horas=horas, sla_fecha_limite=ticket.creado_en+timedelta(hours=horas))


class Migration(migrations.Migration):
    dependencies = [('soporte', '0022_categoria_servidores_r03')]
    operations = [migrations.RunPython(actualizar_sla_activos, migrations.RunPython.noop)]
