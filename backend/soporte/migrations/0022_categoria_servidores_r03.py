from django.db import migrations


def agregar_categoria_servidores(apps, schema_editor):
    Categoria = apps.get_model('soporte', 'CategoriaTicket')
    Categoria.objects.get_or_create(codigo='SERVIDORES', defaults={'nombre': 'Servidores', 'activo': True})


class Migration(migrations.Migration):
    dependencies = [('soporte', '0021_notificacionsoporte_mantenimiento_ticket_via_compra_and_more')]
    operations = [migrations.RunPython(agregar_categoria_servidores, migrations.RunPython.noop)]
