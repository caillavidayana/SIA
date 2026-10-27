from django.conf import settings
from django.db import models


# ==========================================================
# BITÁCORA DEL SISTEMA
# ==========================================================

class Bitacora(models.Model):

    NIVELES = [
        ("INFO", "Información"),
        ("WARNING", "Advertencia"),
        ("SECURITY", "Seguridad"),
        ("ERROR", "Error"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_bitacora"
    )

    accion = models.CharField(
        max_length=150
    )

    modulo = models.CharField(
        max_length=100
    )

    detalle = models.TextField(
        blank=True
    )

    ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    nivel = models.CharField(
        max_length=20,
        choices=NIVELES,
        default="INFO"
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        usuario = (
            self.usuario.email
            if self.usuario
            else "Sistema"
        )

        return f"{usuario} - {self.accion}"


# ==========================================================
# CONFIGURACIÓN SMTP
# ==========================================================

class ConfiguracionSMTP(models.Model):

    nombre = models.CharField(
        max_length=100,
        default="Correo institucional"
    )

    host = models.CharField(
        max_length=200,
        blank=True
    )

    puerto = models.PositiveIntegerField(
        default=587
    )

    usuario = models.EmailField(
        blank=True
    )

    remitente = models.EmailField(
        blank=True
    )

    usar_tls = models.BooleanField(
        default=True
    )

    activo = models.BooleanField(
        default=False
    )

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nombre


# ==========================================================
# PREFERENCIAS GLOBALES
# ==========================================================

class PreferenciaSistema(models.Model):

    nombre_sistema = models.CharField(
        max_length=100,
        default="SIA"
    )

    institucion = models.CharField(
        max_length=200,
        default="Escuela Militar de Ingeniería"
    )

    unidad_academica = models.CharField(
        max_length=200,
        default="Unidad Académica Santa Cruz"
    )

    prefijo_soporte = models.CharField(
        max_length=10,
        default="SOP"
    )

    prefijo_compras = models.CharField(
        max_length=10,
        default="CMP"
    )

    limite_caja_chica = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1500.00 #se puede modifcar caja chica
    )

    intentos_login = models.PositiveIntegerField(
        default=5
    )

    tiempo_bloqueo_minutos = models.PositiveIntegerField(
        default=15
    )

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nombre_sistema
