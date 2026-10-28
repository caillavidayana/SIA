# 6. REAPERTURA (R06)
# Cambiar .env: SIA_HORAS_REAPERTURA=7 para permitir 7 horas.
# fecha_maxima/puede_reabrir controlan propietario, estado y plazo.
# No borrar cerrado_en: archivar_ciclo conserva el cierre y documentos previos.

"""R06 - Reapertura del propietario dentro de SIA_HORAS_REAPERTURA (.env)."""
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


def fecha_maxima(ticket):
    return ticket.cerrado_en+timedelta(hours=settings.SIA_HORAS_REAPERTURA) if ticket.cerrado_en else None


def puede_reabrir(ticket, usuario):
    limite=fecha_maxima(ticket)
    return bool(usuario and usuario.pk==ticket.solicitante_id and ticket.estado.codigo=='CERRADO'
                and limite and ticket.cerrado_en <= timezone.now() <= limite)


def archivar_ciclo(ticket):
    textos=('diagnostico','solucion','acciones_realizadas','resultado_pruebas','informe_tecnico','informe_final','informe_jefe_carrera')
    archivos={c.name:getattr(ticket,c.name).name for c in ticket._meta.fields
              if isinstance(c,models.FileField) and getattr(ticket,c.name)}
    ticket.historial_reaperturas=[*ticket.historial_reaperturas,{
        'cerrado_en':ticket.cerrado_en.isoformat(),'reabierto_en':timezone.now().isoformat(),
        'textos':{c:getattr(ticket,c) for c in textos},'archivos':archivos}]
    for campo in ('solucion','acciones_realizadas','resultado_pruebas','informe_tecnico','informe_final','informe_jefe_carrera'):
        setattr(ticket,campo,'')
    for campo in ('conformidad_usuario','conformidad_en','pruebas_en','verificado_en','informe_elevado_en','informe_recibido_director_en','proceso_finalizado_en','informe_jefe_carrera_en','sla_cumplido'):
        setattr(ticket,campo,None)
    for campo in ('informe_tecnico_pdf','informe_final_pdf','informe_jefe_carrera_pdf'):
        setattr(ticket,campo,None)
