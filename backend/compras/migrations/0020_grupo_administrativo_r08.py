from django.conf import settings
from django.db import migrations


def preparar_grupo(apps, schema_editor):
    Grupo=apps.get_model('auth','Group')
    Usuario=apps.get_model('usuarios','Usuario')
    Asignacion=apps.get_model('usuarios','UsuarioRol')
    RolPermiso=apps.get_model('usuarios','RolPermiso')
    Bitacora=apps.get_model('auditoria','Bitacora')
    grupo,_=Grupo.objects.get_or_create(name=settings.SIA_GRUPO_APROBADOR)
    # Matriz real inspeccionada: únicamente Director/ADMIN con DAR_VISTO_BUENO.
    roles=RolPermiso.objects.filter(activo=True,permiso__codigo='DAR_VISTO_BUENO',rol__activo=True,rol__codigo__in=['DIRECTOR','ADMIN']).values_list('rol_id',flat=True)
    ids=Asignacion.objects.filter(activo=True,rol_id__in=roles).values_list('usuario_id',flat=True)
    cantidad=0
    for usuario in Usuario.objects.filter(pk__in=ids,is_active=True):
        usuario.groups.add(grupo);cantidad+=1
    Bitacora.objects.create(accion='R08_CONFIGURAR_GRUPO',modulo='Compras',detalle=f'Grupo {grupo.name}: {cantidad} aprobadores finales existentes verificados por rol y permiso. Sin permisos nuevos para jefaturas técnicas.',nivel='INFO')


class Migration(migrations.Migration):
    dependencies=[('compras','0019_incorporar_movimientos_historicos_r09'),('usuarios','0008_documentoproceso')]
    operations=[migrations.RunPython(preparar_grupo,migrations.RunPython.noop)]
