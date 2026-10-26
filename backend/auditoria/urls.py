from django.urls import path

from .views import (
    bitacora_view,
    limite_caja_chica_view,
    smtp_view,
    preferencias_view,
)


urlpatterns = [

    path(
        "bitacora/",
        bitacora_view,
        name="bitacora"
    ),

    path(
        "smtp/",
        smtp_view,
        name="smtp"
    ),

    path(
        "preferencias/",
        preferencias_view,
        name="preferencias"
    ),
    path(
        "limite-caja-chica/",
        limite_caja_chica_view,
        name="limite-caja-chica"
    ),

]