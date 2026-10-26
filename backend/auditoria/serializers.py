from rest_framework import serializers

from .models import (
    Bitacora,
    ConfiguracionSMTP,
    PreferenciaSistema,
)


class BitacoraSerializer(serializers.ModelSerializer):

    usuario_nombre = serializers.CharField(
        source="usuario.nombre_completo",
        read_only=True
    )

    usuario_email = serializers.CharField(
        source="usuario.email",
        read_only=True
    )

    nivel_nombre = serializers.CharField(
        source="get_nivel_display",
        read_only=True
    )

    class Meta:
        model = Bitacora

        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "usuario_email",
            "accion",
            "modulo",
            "detalle",
            "ip",
            "nivel",
            "nivel_nombre",
            "fecha",
        ]

        read_only_fields = [
            "usuario",
            "ip",
            "fecha",
        ]


class ConfiguracionSMTPSerializer(
    serializers.ModelSerializer
):

    actualizado_por_nombre = serializers.CharField(
        source="actualizado_por.nombre_completo",
        read_only=True
    )

    class Meta:
        model = ConfiguracionSMTP

        fields = [
            "id",
            "nombre",
            "host",
            "puerto",
            "usuario",
            "remitente",
            "usar_tls",
            "activo",
            "actualizado_por",
            "actualizado_por_nombre",
            "actualizado_en",
        ]

        read_only_fields = [
            "actualizado_por",
            "actualizado_en",
        ]


class PreferenciaSistemaSerializer(
    serializers.ModelSerializer
):
    limite_caja_chica = serializers.SerializerMethodField()

    def get_limite_caja_chica(self, obj):
        from django.conf import settings
        return str(settings.SIA_LIMITE_CAJA_CHICA)


    actualizado_por_nombre = serializers.CharField(
        source="actualizado_por.nombre_completo",
        read_only=True
    )

    class Meta:
        model = PreferenciaSistema

        fields = [
            "id",
            "nombre_sistema",
            "institucion",
            "unidad_academica",
            "prefijo_soporte",
            "prefijo_compras",
            "limite_caja_chica",
            "intentos_login",
            "tiempo_bloqueo_minutos",
            "actualizado_por",
            "actualizado_por_nombre",
            "actualizado_en",
        ]

        read_only_fields = [
            "actualizado_por",
            "actualizado_en",
        ]