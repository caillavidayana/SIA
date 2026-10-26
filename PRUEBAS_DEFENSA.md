# Pruebas manuales R01 a R10

**Revisión vigente posterior:** [VERIFICACION_REQUISITOS_VIGENTES.md](VERIFICACION_REQUISITOS_VIGENTES.md). Las instrucciones de esta etapa que permitan enviar 1200, sitúen cotizaciones adicionales en 1000 o requieran aprobación del Director quedan sustituidas.

**Actualización del flujo:** la revisión vigente está en [CORRECCION_FLUJO_SOLICITANTE_TECNICO.md](CORRECCION_FLUJO_SOLICITANTE_TECNICO.md). Cotizaciones adicionales únicamente sobre Bs 1000; categoría/prioridad en Jefatura UTIC y vía de adquisición en DAF. Las referencias previas a 500 y al rechazo técnico por superar 1000 quedan sustituidas.

Abrir http://127.0.0.1:5173 con las cuentas existentes. Los servicios se inician con `iniciar.ps1 backend` y `iniciar.ps1 frontend` en terminales separadas. La ejecución y las pruebas automatizadas están en `EJECUCION_LOCAL.md`. Los resultados de cada acción deben verificarse con el rol que corresponde al paso institucional.

| Regla | Acción | Resultado esperado |
|---|---|---|
| R01 | En un requerimiento técnico de Caja Chica ingresar 1000.01 | Modal de rechazo con límite 1000; conserva el formulario y los adjuntos. Con 1000 no rechaza por R01. |
| R02 | Ingresar 700 y una cotización; intentar enviar; agregar otra y repetir | Informa primero dos faltantes y luego uno. Tres proveedores distintos permiten continuar. Duplicar proveedor o NIT no completa el mínimo. |
| R03 | Crear soporte o mantenimiento titulado Falla de RED; luego probar Pared dañada | RED fuerza Alta y bloquea el selector; Pared permite prioridad manual. También probar categoría Servidores. |
| R04 | Crear Alta, Media y Baja y consultar su detalle | Plazos desde creación de 4, 24 y 72 horas. Clasificar más tarde no reinicia el plazo. Un expediente cerrado no se muestra como activo vencido. |
| R05 | Seguir clasificación, asignación, diagnóstico y solución por las acciones del sistema | No permite resolver sin solución ni saltar etapas. La conformidad y cierre mantienen los pasos institucionales. PATCH directo de estado se rechaza. |
| R06 | Cerrar un ticket y entrar como su solicitante en Mis solicitudes | Dentro de siete días ofrece Reabrir. Conserva cierre e historial anterior y abre nuevo ciclo. Otro usuario no puede hacerlo. El caso de ocho días se verifica con fechas controladas en pruebas aisladas. |
| R07 | Asignar cinco trabajos activos al mismo técnico e intentar un sexto | Rechaza el sexto y muestra carga/límite. Resolver uno libera cupo. El contador incluye apoyos y mantenimiento. |
| R08 | Intentar aprobación final de 301 con usuario sin grupo administrativo; luego con aprobador autorizado | El primero recibe 403 y conserva su sesión; el segundo puede continuar si cumple permiso, cotizaciones y saldo. Una compra propia siempre se rechaza. |
| R09 | Entrar en Tesorería → Control de Caja Chica | Muestra mes, fondo, comprometido, desembolsado, saldo, porcentaje y movimientos reales. DAF y Compras disponen del resumen autorizado. |
| R09 | Aprobar una compra con saldo; luego generar recibo y confirmar pago | Aprobar reserva; pagar convierte el compromiso sin doble descuento. El recibo conserva su saldo proyectado y la confirmación permite descargar la constancia PDF con saldo efectivo. |
| R09 | Intentar aprobar o pagar por encima del saldo disponible | Rechaza la operación con modal azul, blanco y mostaza; no registra un nuevo desembolso. No basta con superar saldo: usar un importe que siga cumpliendo el límite R01 para probar específicamente R09. |
| R10 | Abrir cambio o recuperación de contraseña y probar una contraseña inválida | Ayuda con mínimo real de 10; validadores existentes siguen rechazando contraseñas cortas, numéricas y similares. Las cuentas anteriores conservan sus hashes. |

## Cambios rápidos para la exposición

Editar `.env`, detener/reiniciar Django y actualizar el navegador. Cambiar una regla por vez y restaurarla después:

```dotenv
SIA_LIMITE_CAJA_CHICA=1200
SIA_UMBRAL_COTIZACIONES=1200
SIA_MAX_TICKETS_TECNICO=8
SIA_FONDO_MENSUAL=7000
```

Con límite 1200, un importe 1100 pasa R01, pero sigue sujeto a R02, permisos y saldo. Con umbral 1200, un importe 700 deja de exigir tres cotizaciones. Con máximo 8, la sexta asignación se permite. Con fondo 7000, el panel y la API muestran ese fondo sin recompilar Vue. Restaurar los valores 1000, 500, 5 y 5000.

El cambio de configuración se verificó también con un archivo temporal independiente: `tmp/probar_configuracion_env.py`; no altera el `.env` del usuario.

Al entregar, octubre de 2026 tiene fondo 5000, desembolsado 3500, comprometido 0 y saldo 1500, conservando los datos históricos. Las pruebas que realices cambiarán ese saldo. Para simular insuficiencia sin alterar historia, usar las pruebas automatizadas aisladas de R09 o consumir saldo mediante operaciones reales del flujo. No borrar movimientos para reiniciar una demostración.

## Evidencias y automatización

`backend/compras/test_caja_chica_r09.py`, `backend/soporte/test_r04.py`, `backend/soporte/test_r05.py`, `backend/soporte/test_r06.py`, `backend/soporte/test_r07.py`, `backend/compras/test_r08.py` y `backend/usuarios/test_r10.py` cubren reglas nuevas junto con la regresión R01–R03 y los flujos anteriores.

La suite SQLite omite dos pruebas de concurrencia que requieren PostgreSQL. La suite PostgreSQL ejecuta ambas: dos compras compiten por saldo insuficiente para ambas y dos asignaciones compiten por un solo cupo. Consultar comandos en `EJECUCION_LOCAL.md`.

Capturas de interfaz: `tmp/capturas-r123/` y `tmp/capturas-diez-reglas/`. Las capturas usan respuestas de API simuladas para verificar estilos, formularios y tamaños; las validaciones de negocio y permisos se comprueban contra Django, incluida la base PostgreSQL de pruebas. No equivalen a una aprobación o pago real registrado en la base del usuario.
