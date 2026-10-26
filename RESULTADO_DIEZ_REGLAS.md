# Entrega local de R01 a R10 — 25 de octubre de 2026

**Revisión vigente posterior:** [VERIFICACION_REQUISITOS_VIGENTES.md](VERIFICACION_REQUISITOS_VIGENTES.md). Las instrucciones de esta etapa que permitan enviar 1200, sitúen cotizaciones adicionales en 1000 o requieran aprobación del Director quedan sustituidas.

**Actualización del flujo:** la revisión vigente está en [CORRECCION_FLUJO_SOLICITANTE_TECNICO.md](CORRECCION_FLUJO_SOLICITANTE_TECNICO.md). Cotizaciones adicionales únicamente sobre Bs 1000; categoría/prioridad en Jefatura UTIC y vía de adquisición en DAF. Las referencias previas a 500 y al rechazo técnico por superar 1000 quedan sustituidas.

Las diez reglas se implementaron sobre el sistema existente, conservando sus etapas institucionales, cuentas, compras, expedientes y estilos. El diagnóstico previo está en `DIAGNOSTICO_DIEZ_REGLAS.md`. Se trabajó con la autorización expresa del mensaje del usuario, incluidas dependencias y migraciones necesarias. No se modificaron VirtualBox ni Nginx.

## Resultado funcional

| Regla | Implementación |
|---|---|
| R01 | Límite configurable 1000; validación en requerimientos, aprobación y desembolso; rechazo y aviso institucional. |
| R02 | Por encima de 500 exige tres cotizaciones válidas de proveedores distintos; preserva y permite completar borradores y adjuntos. |
| R03 | Red/Servidores y palabras completas fuerzan Alta en soporte y mantenimiento; comparación normalizada y control también en backend. |
| R04 | Alta 4 h, Media 24 h y Baja 72 h desde creación; clasificación no reinicia el reloj; distingue SLA activo de resultado de cierre. |
| R05 | Valida fases Abierto → En proceso → Resuelto → Cerrado y devolución Resuelto → En proceso, con solución obligatoria; impide saltos por PATCH. |
| R06 | Reapertura por propietario hasta siete días, conservando cierre anterior e historial de solución/documentos; nuevo ciclo y plazo. |
| R07 | Máximo cinco trabajos activos por técnico, incluyendo apoyos y mantenimiento; bloqueo transaccional de usuarios en PostgreSQL. |
| R08 | Más de 300 exige grupo Jefe administrativo y permiso institucional; prohíbe aprobación propia; no concede facultades financieras a jefaturas técnicas. |
| R09 | Fondo 5000, reserva al aprobar, conversión a desembolso sin doble descuento, liberación al rechazar, bloqueo por saldo, panel financiero, API autorizada y constancia PDF efectiva. |
| R10 | Conserva política mínima de diez y compatibilidad de hashes; corrige ayuda de las pantallas para consultar el mínimo real del backend. |

Los valores de entorno se centralizan en `.env` y `backend/config/settings.py`. `.env.example` documenta los iniciales y `.env` queda excluido de Git. Configuración, funciones reales, cambios de ejemplo, aplicación, pruebas y reversión de cada regla: `REQUERIMIENTOS_CONFIGURACION.md`.

## Dependencias y migraciones

Runtimes locales: Python 3.14.2, Node.js 24.22.1 y Git portable. Dependencias frontend instaladas según el archivo de bloqueo. Backend usa `backend/.venv-local/`; se añadieron al archivo de requisitos `python-dotenv==1.2.4` para cargar `.env` y `psycopg[binary]==3.3.6` para pruebas PostgreSQL. `pip check` no encuentra dependencias incompatibles.

PostgreSQL 16.13 portable se descargó para verificar concurrencia en una base aislada en localhost:55432. La aplicación de uso manual continúa sobre su SQLite original. No se instaló un servicio del sistema ni se migraron los datos reales a PostgreSQL. Playwright con Edge se utilizó únicamente para verificar interfaz. pypdf permitió leer la guía PDF oficial del proyecto.

Migraciones nuevas de esta etapa, todas aplicadas y registradas:

- `compras.0018_fondomensualcajachica_movimientocajachica`: fondo y movimientos.
- `compras.0019_incorporar_movimientos_historicos_r09`: incorpora compras históricas sin borrarlas ni alterar sus recibos; identifica fechas de origen legado.
- `compras.0020_grupo_administrativo_r08`: grupo y membresía inicial limitada a aprobadores con permisos vigentes.
- `compras.0021_recibotesoreria_constancia_saldo`: documento complementario del saldo efectivo al pagar.
- `soporte.0023_sla_activos_r04`: plazos de tickets activos anteriores calculados desde su creación.
- `soporte.0024_ticket_historial_reaperturas_ticket_reabierto_en`: historial y fecha independiente de reapertura.

Las migraciones de la etapa R01–R03 también permanecen aplicadas. `showmigrations` quedó en `tmp/migraciones-finales.log`; no hay migraciones pendientes ni cambios de modelo sin migración.

## Verificación ejecutada

| Comprobación | Resultado |
|---|---|
| `manage.py check` | Sin errores. |
| `manage.py makemigrations --check --dry-run` | No changes detected. |
| `manage.py showmigrations` | Migraciones aplicadas. |
| Suite Django SQLite | 127 pruebas: 125 aprobadas y dos de concurrencia PostgreSQL omitidas. |
| Suite Django PostgreSQL | 127 pruebas aprobadas, sin omisiones; incluye competencia por saldo y por cupo técnico. |
| `npm run build` | Compilación correcta. |
| Pruebas JavaScript | Seis aprobadas. |
| `pip check` | Sin dependencias rotas. |
| Cambio de configuración con otro `.env` | 1200 límite, 1200 umbral, ocho trabajos y fondo 7000 reflejados en configuración efectiva; no se cambia el `.env` de uso normal. |
| Interfaz en Edge | Formularios soporte/mantenimiento, cotizaciones faltantes, prioridad automática, panel financiero y modales escritorio/móvil; sin errores JavaScript. |
| Permisos de saldo con las 17 cuentas existentes | Siete accesos autorizados y diez rechazos 403, mediante consultas autenticadas sin modificar expedientes. |
| HTTP local | Frontend 200; configuración pública 200; saldo sin autenticar 401. |
| Conservación de datos | 17 usuarios, 23 tickets, 46 mantenimientos y 26 compras; mismos hashes de contraseña; integridad SQLite correcta. |

Registros reproducibles: `tmp/validacion-final-sqlite.log`, `tmp/validacion-final-postgres.log`, `tmp/probar_configuracion_env.py` y `tmp/verificar_entrega.py`. Los comandos están en `EJECUCION_LOCAL.md`. Las pruebas Django crean bases temporales y almacenamiento separado.

Las capturas en `tmp/capturas-r123/` y `tmp/capturas-diez-reglas/` usan datos simulados para revisar la presentación, colores, adaptación móvil y conservación del formulario. Las validaciones financieras, permisos, límites, PDF y carreras se verificaron contra Django y PostgreSQL; las capturas no representan pagos reales del usuario.

## Inicio y pruebas del usuario

Abrir http://127.0.0.1:5173. API en http://127.0.0.1:8000. Ambos servidores quedaron iniciados para la entrega. Usar las cuentas existentes; no se cambiaron contraseñas. Si se cierran, reiniciarlos con los dos comandos de `EJECUCION_LOCAL.md`.

En Tesorería → Control de Caja Chica, octubre de 2026 refleja fondo 5000, desembolsado 3500, comprometido 0, saldo 1500 y utilización 70 %. Las operaciones que se realicen después de esta entrega cambiarán esos valores. La guía paso a paso para probar las diez reglas está en `PRUEBAS_DEFENSA.md`.

## Git y respaldo

Se conservaron los cambios previos del usuario. Respaldo anterior: `tmp/db-antes-diez-reglas-20261025-182658.sqlite3`; inventario y parche previo en `tmp/estado-antes-diez-reglas.txt` y `tmp/cambios-antes-diez-reglas.patch`.

Las diez ramas locales `regla-01-*` a `regla-10-*` quedaron reservadas, manteniendo activa `practica-10-reglas-sia`. Cada una tiene borrador en `docs/pull-requests/`. No se ejecutaron commit, push, merge, publicación de PR ni despliegue, conforme al texto solicitado.

Las ramas apuntan al HEAD previo: no contienen todavía commits independientes de las reglas. Los cambios completos están en el árbol de trabajo compartido. Los parches `tmp/etapas-reglas/` documentan etapas cronológicas y pueden incluir correcciones comunes. Preparar diez revisiones independientes requiere separar sus dependencias y crear los commits en un paso posterior autorizado; no se presenta la reserva de nombres como diez PR terminados.

## Límites conocidos

La compilación avisa que un paquete JavaScript supera 500 kB; termina correctamente. La protección concurrente entre procesos se comprobó en PostgreSQL; SQLite es la opción local existente y su mutex de desarrollo no reemplaza bloqueos de base distribuidos. El fondo vigente se aplica también al consultar períodos históricos. La reserva conserva el mes original aunque el pago se confirme después. El recibo original firmado permanece intacto y la constancia adicional registra el saldo efectivo al confirmar.

Los documentos `RESULTADO_R01_R02_R03.md` y `PREPARACION_R01_R02_R03.md` conservan la historia de la primera etapa; esta entrega y `REQUERIMIENTOS_CONFIGURACION.md` describen el estado actual de las diez reglas.
