from django.db import migrations, models


def preparar_entregas_historicas(apps, schema_editor):
    """Las entregas anteriores ya habilitaron la reparación de forma
    automática. Solo se devuelven a recepción las que no tienen ningún
    trabajo técnico iniciado; los casos avanzados se conservan intactos."""
    Requerimiento = apps.get_model("mantenimiento", "RequerimientoMantenimiento")
    SolicitudCompra = apps.get_model("compras", "SolicitudCompra")

    compras_con_acta = SolicitudCompra.objects.filter(
        estado="COMPRADO_Y_ENTREGADO",
        acta_conformidad__isnull=False,
        requerimiento_mantenimiento__isnull=False,
    ).exclude(acta_conformidad="")

    requerimiento_ids = compras_con_acta.values_list(
        "requerimiento_mantenimiento_id", flat=True
    )

    Requerimiento.objects.filter(
        id__in=requerimiento_ids,
        estado__codigo="EN_MANTENIMIENTO",
        estado_compra_componente="ENTREGADA",
        trabajo_realizado="",
        resultado_pruebas="",
        informe_trabajo="",
    ).update(
        estado_compra_componente="PENDIENTE_RECEPCION_TECNICO",
        inicio_mantenimiento_en=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("mantenimiento", "0005_estados_bpmn"),
        # La migración de datos consulta este modelo y su relación de origen.
        ("compras", "0003_solicitudcompra_componente_verificado_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="requerimientomantenimiento",
            name="componente_recibido_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="requerimientomantenimiento",
            name="componente_recibido_por",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="requerimientomantenimiento",
            name="observacion_recepcion_componente",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="requerimientomantenimiento",
            name="estado_compra_componente",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SOLICITADA", "Solicitada"),
                    ("NO_VIABLE", "No viable"),
                    ("VIABLE", "Viable"),
                    ("PENDIENTE_RECEPCION_TECNICO", "Pendiente de recepción por el técnico"),
                    ("ENTREGADA", "Componente recibido por el técnico"),
                ],
                max_length=30,
            ),
        ),
        migrations.RunPython(preparar_entregas_historicas, migrations.RunPython.noop),
    ]
