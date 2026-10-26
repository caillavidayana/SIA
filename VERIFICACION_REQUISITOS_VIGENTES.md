# Requisitos vigentes y pruebas para el usuario

Esta revisión corresponde a la última aclaración del usuario. Sustituye las indicaciones anteriores que trasladaban las cotizaciones adicionales al umbral de 1000 o permitían al técnico enviar 1200. Se mantuvieron las pantallas y etapas existentes salvo los cambios expresamente solicitados.

| Requerimiento | Comportamiento vigente | Configuración / código |
|---|---|---|
| R01 | Al enviar 1200, rechaza por superar 1000, muestra modal y conserva formulario y adjuntos. Tres cotizaciones no permiten eludir este rechazo. | `.env`: `SIA_LIMITE_CAJA_CHICA=1000`; `config/settings.py`, `config/reglas.py`, acciones técnicas de `soporte/views.py` y `mantenimiento/views.py`, `CotizacionesRequerimiento.vue`. |
| R02 | Por encima de 500 exige tres cotizaciones de proveedores distintos. Si ya hay una válida, el modal solicita agregar dos. Aceptar vuelve al mismo formulario conservando sus datos. | `.env`: `SIA_UMBRAL_COTIZACIONES=500`, `SIA_COTIZACIONES_MINIMAS=3`; `compras/reglas_cotizaciones.py`, `compras/expediente.py`, `reglasCore.js`, `CotizacionesRequerimiento.vue`. |
| R03 | Categoría Red del solicitante produce prioridad Alta automática. UTIC la recibe marcada y no puede seleccionar otra mientras aplique la regla. El solicitante no selecciona prioridad. | `config/settings.py`: `SIA_CATEGORIAS_PRIORIDAD`, `SIA_PALABRAS_PRIORIDAD`, `SIA_PRIORIDAD_AUTOMATICA`; `config/reglas.py`, modelos y clasificación UTIC. |
| R04 | Conserva plazos de Alta, Media y Baja y el cómputo del vencimiento. La clasificación UTIC presenta esas tres opciones. | `SIA_SLA_ALTA_HORAS=4`, `SIA_SLA_MEDIA_HORAS=24`, `SIA_SLA_BAJA_HORAS=72`. Sin cambios en la lógica del reloj durante esta revisión. |
| R05 | Conserva las acciones y el flujo de estados existentes. | Sin cambios funcionales en esta revisión. |
| R06 | Solo el solicitante propietario puede reabrir un ticket cerrado dentro de siete días. Vuelve al proceso y conserva fecha de cierre e historial. | `SIA_DIAS_REAPERTURA=7`; `soporte/reapertura.py` y acción `reabrir-ticket`. Verificado sin cambiar su lógica. |
| R07 | Conserva el control de carga técnica y las asignaciones existentes. | `SIA_MAX_TICKETS_TECNICO=5`; `soporte/carga_tecnica.py`. Sin cambios funcionales en esta revisión. |
| R08 | Conserva Jefatura → DAF y la certificación. DAF deriva directamente a Tesorería; el Director no vuelve a aprobar una compra, incluso si supera 300. No permite autoaprobación ni actuar sin permisos. | `SIA_REQUIERE_APROBACION_DIRECTOR=False`; `compras/views.py`, `compras/aprobacion.py`. |
| R09 | Tesorería ve fondo, comprometido, desembolsado y saldo en su dashboard. Sin saldo no puede generar recibo ni confirmar un pago; la certificación también impide comprometer fondos inexistentes. | `SIA_FONDO_MENSUAL=5000`; `compras/caja_chica.py`, `compras/tesoreria.py`, `CajaChicaPanel.vue`. No cambia el modelo del fondo en esta revisión. |
| R10 | Mantiene validadores y hashes de contraseña existentes. | Sin cambios funcionales en esta revisión. |

Los archivos backend de la tabla son relativos a `backend/`; los componentes y utilidades Vue están en `frontend/src/`. Los puntos modificados están identificados con `REQUERIMIENTO 1 (R01)`, `REQUERIMIENTO 2 (R02)`, `REQUERIMIENTO 8 (R08)` o el identificador correspondiente. Las reglas previamente implementadas conservan sus comentarios y pruebas.

## Pruebas manuales

1. Abrir http://127.0.0.1:5173 y actualizar con Ctrl+F5. Usar las cuentas existentes.
2. **R01:** en un requerimiento técnico pendiente, ingresar 1200 y enviar. Debe aparecer rechazo por límite 1000; cerrar el modal debe conservar todos los campos y documentos. Repetir incluso con tres cotizaciones: sigue rechazado.
3. **R02:** corregir a 700 y adjuntar una cotización con proveedor. Enviar debe solicitar dos adicionales. Aceptar conserva el formulario. Agregar archivos de otros dos proveedores, completar sus nombres y enviar de nuevo; ahora continúa. Empresa sigue siendo opcional. 500 exactos admite una cotización; 500.01 exige tres, siempre dentro de R01.
4. **R03:** como solicitante, crear con categoría Red. No hay selector de prioridad. Como Jefatura UTIC, validar los requisitos y comprobar Alta marcada y bloqueada; conservar criterio técnico y asignación del flujo anterior.
5. **R04/R07:** comprobar plazo y carga en el flujo normal. No se añadió otro paso de asignación ni se reinicia el reloj al clasificar.
6. **R06:** cerrar un ticket y entrar como su solicitante; reabrir dentro del plazo. Verificar nuevo ciclo y cierre anterior conservado. El caso de más de siete días se prueba en la base temporal automatizada sin alterar fechas reales.
7. **R08:** elevar una compra viable desde Jefatura, evaluar y certificar con DAF. Debe quedar `APROBADO_PARA_DESEMBOLSO`, visible para Tesorería. No hay aprobación pendiente del Director. Los expedientes antiguos ya certificados pueden continuarse desde el detalle de DAF con **Derivar a Tesorería**, conservando su certificación.
8. **R09:** abrir Tesorería → Control de Caja Chica. Si una operación excede el saldo disponible, debe rechazarse sin desembolso. Para demostrar el bloqueo sin consumir fondos reales, ejecutar las pruebas aisladas del backend.

## Cambios numéricos para la defensa

Editar `.env`, reiniciar Django y actualizar el navegador. No requieren migración ni recompilación Vue:

```dotenv
# R01: cambiar a 1500 permite 1200, pero sigue exigiendo R02.
SIA_LIMITE_CAJA_CHICA=1500
# R02: cambiar a 800 permite 700 con una cotización.
SIA_UMBRAL_COTIZACIONES=800
# R06: cambia la ventana de reapertura.
SIA_DIAS_REAPERTURA=10
# R07: conserva el mismo control con otro máximo.
SIA_MAX_TICKETS_TECNICO=8
# R09: mismo cálculo y controles, con otro fondo.
SIA_FONDO_MENSUAL=7000
```

Restaurar respectivamente 1000, 500, 7, 5 y 5000 al terminar. El entorno definido en la terminal tiene prioridad sobre `.env`. La configuración efectiva se consulta en el endpoint autenticado `/api/auditoria/limite-caja-chica/`.

Para volver expresamente al paso anterior del Director puede usarse `SIA_REQUIERE_APROBACION_DIRECTOR=True` y reiniciar. Con False, el umbral/grupo administrativo del antiguo paso del Director no añaden otra aprobación. Esta opción de compatibilidad no está activada en el flujo entregado.

## Evidencia

Pruebas del flujo vigente en `backend/compras/test_flujo_confirmado.py`, `test_reglas123.py` y `test_caja_chica_r09.py`. La carrera de dos compras por un mismo saldo ahora usa certificación DAF, sin Director. Los casos del flujo anterior se conservan con `SIA_REQUIERE_APROBACION_DIRECTOR=True` explícito para verificar también la compatibilidad configurable.

Regresión completa: `tmp/confirmacion-final-sqlite.log` y `tmp/confirmacion-final-postgres.log`. Navegador: `tmp/validar_requisitos_confirmados.cjs`; capturas en `tmp/capturas-requisitos-confirmados/`. Las pruebas visuales usan respuestas simuladas y no crean pagos ni expedientes reales; las pruebas de API usan bases temporales.

Los comandos de inicio y pruebas están en `EJECUCION_LOCAL.md`. No se necesitan dependencias ni migraciones nuevas para esta revisión. No se ejecutaron commits, push, merge ni despliegues.
