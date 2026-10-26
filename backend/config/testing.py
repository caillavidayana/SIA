"""Utilidades de pruebas: consumir streaming antes de cerrar el TestClient."""
def cerrar_respuesta(respuesta):
    # TestClient desconecta close_old_connections durante el cierre de su
    # iterador. Cerrar sin consumirlo puede cerrar la transacción de TestCase.
    if not respuesta.closed and getattr(respuesta, 'streaming', False):
        list(respuesta.streaming_content)
    if not respuesta.closed:
        respuesta.close()
