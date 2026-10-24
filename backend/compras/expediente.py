#def documentos_faltantes(solicitud):
   # campos = {"informe": "Informe técnico", "proforma": "Cotización", "poa": "POA"}
#   if solicitud.origen_modulo in ("SOPORTE", "MANTENIMIENTO"):
#        campos["pedido"] = "Proveído de jefatura"
  #  return [nombre for campo, nombre in campos.items() if not getattr(solicitud, campo)]

from decimal import Decimal


def documentos_faltantes(solicitud):
    from .models import CotizacionCompra

    campos = {
        "informe": "Informe técnico",
        "proforma": "Cotización",
        "poa": "POA",
    }

    if solicitud.origen_modulo in ("SOPORTE", "MANTENIMIENTO"):
        campos["pedido"] = "Proveído de jefatura"

    faltantes = [
        nombre
        for campo, nombre in campos.items()
        if not getattr(solicitud, campo)
    ]

    # R02: Compras mayores a Bs 500 requieren tres cotizaciones
    if solicitud.monto_estimado is not None:
        if solicitud.monto_estimado > Decimal("500.00"):
            cantidad = CotizacionCompra.objects.filter(
                solicitud=solicitud
            ).count()

            if cantidad < 3:
                faltantes.append(
                    f"Se requieren 3 cotizaciones (registradas: {cantidad})"
                )

    return faltantes

def completar_expediente_origen(request, origen, campo_origen):
    from rest_framework.response import Response
    from auditoria.utils import registrar_bitacora
    from .models import SolicitudCompra

    solicitud = SolicitudCompra.objects.filter(**{campo_origen: origen}).order_by("-creado_en").first()
    if not solicitud or solicitud.estado not in ("CREADO_PENDIENTE_DAF", "EVALUADO_PENDIENTE_CERTIFICACION") or solicitud.cerrado_inmutable:
        return Response({"detalle": "El expediente no admite completar documentación en esta etapa."}, status=409)
    if not documentos_faltantes(solicitud):
        return Response({"detalle": "El expediente ya tiene todos los documentos."}, status=409)
    from .informes_origen import asegurar_informe_tecnico
    asegurar_informe_tecnico(origen)
    for campo in ("informe", "proforma", "poa", "pedido"):
        archivo = request.FILES.get(campo) or getattr(solicitud, campo)
        if not archivo and campo in ("informe", "proforma"):
            archivo = getattr(origen, "informe_compra" if campo == "informe" else "cotizacion_archivo")
        setattr(solicitud, campo, archivo)
    faltantes = documentos_faltantes(solicitud)
    if faltantes:
        return Response({"detalle": "Adjunte: " + ", ".join(faltantes) + "."}, status=400)
    solicitud.estado = "CREADO_PENDIENTE_DAF"
    solicitud.save(update_fields=["informe", "proforma", "poa", "pedido", "estado", "actualizado_en"])
    registrar_bitacora(request=request, accion="COMPLETAR_EXPEDIENTE", modulo="Compras",
                       detalle=f"{solicitud.codigo}: jefatura completó los documentos y remitió a evaluación DAF.", nivel="INFO")
    return Response({"detalle": "Expediente completo, remitido a evaluación DAF."})
