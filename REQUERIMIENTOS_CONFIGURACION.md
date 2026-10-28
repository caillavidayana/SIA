# Configuración y defensa de R01 a R10

**Flujo vigente:** consultar [VERIFICACION_REQUISITOS_VIGENTES.md](VERIFICACION_REQUISITOS_VIGENTES.md). R01 rechaza sobre 1000, R02 pide adicionales sobre 500 y DAF deriva a Tesorería sin aprobación del Director.


La configuración efectiva se centraliza en `backend/config/settings.py`. Django carga el archivo `.env` de la raíz mediante python-dotenv. Las variables ya definidas en la terminal tienen prioridad sobre `.env`. `.env.example` contiene los valores iniciales y no contiene credenciales. No copiarlo sobre un `.env` ya personalizado.

Después de cambiar valores, detener Django con Ctrl+C y volver a ejecutar `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 backend`. Actualizar la pantalla para consultar la nueva configuración. Estos cambios de valores no requieren recompilar Vue ni ejecutar migraciones; editar componentes Vue sí requiere una nueva compilación al preparar producción. El servidor local usa `--noreload`.

Vue consulta `GET /api/auditoria/limite-caja-chica/` con autenticación para R01–R09. R10 consulta `GET /api/configuracion-publica/`, que solo expone el mínimo de longitud. Las validaciones decisivas permanecen en Django aunque se modifique o se omita el formulario.

Los nombres de archivos backend indicados abajo son relativos a `backend/`; los nombres `frontend/` son relativos a la raíz. Pruebas y resultados completos: `RESULTADO_DIEZ_REGLAS.md` y `PRUEBAS_DEFENSA.md`.

## R01 — Rechazo por límite de 1000

1. **Función:** bloquear envío técnico superior al límite incluso con tres cotizaciones; modal de rechazo conserva formulario y archivos.
2. **Archivos:** `backend/config/settings.py`, `backend/config/reglas.py`, `backend/soporte/views.py`, `backend/mantenimiento/views.py`, `frontend/src/components/CotizacionesRequerimiento.vue`.
3. **Funciones:** `error_limite`, `_guardar_compra_r01_r02` y guardado de requerimiento de mantenimiento; `validar` del componente.
4. **Variable:** `SIA_LIMITE_CAJA_CHICA`.
5. **Valor inicial:** 1000.
6. **Ejemplo:** `SIA_LIMITE_CAJA_CHICA=1500` permite 1200 si cumple R02.
7. **Aplicar:** reiniciar Django y actualizar navegador, sin migración ni recompilar Vue.
8. **Probar:** 1200 se rechaza, 1000 con tres proveedores continúa. No permite eludirlo enviando Finanzas desde el técnico.
9. **Revertir valor:** restaurar 1000 y reiniciar. Conservar expedientes y archivos.
10. **Rama reservada:** `regla-01-limite-caja-chica`.

## R02 — Dos cotizaciones adicionales sobre 500

1. **Función:** por encima del umbral pide tres cotizaciones de proveedores distintos. Con una, solicita dos adicionales y conserva el formulario.
2. **Archivos:** `backend/compras/reglas_cotizaciones.py`, `backend/compras/expediente.py`, `frontend/src/utils/reglasCore.js`, `frontend/src/components/CotizacionesRequerimiento.vue`.
3. **Funciones:** `requeridas`, `progreso`, `validar_cotizaciones`, `validar_solicitud`, `documentos_faltantes`, `validar` y `adjuntar`.
4. **Variables:** `SIA_UMBRAL_COTIZACIONES`, `SIA_COTIZACIONES_MINIMAS`, `SIA_PROVEEDORES_DISTINTOS`.
5. **Valores iniciales:** 500, 3 y True. Umbral independiente de R01.
6. **Ejemplo:** `SIA_UMBRAL_COTIZACIONES=800` permite 700 con una cotización.
7. **Aplicar:** reiniciar Django y actualizar navegador, sin migración ni recompilación por valores.
8. **Probar:** 500 con una; 700 con una pide dos; 700 con tres proveedores distintos continúa; 1200 sigue rechazado por R01.
9. **Revertir valor:** restaurar 500, 3 y True. No borrar cotizaciones ni historial.
10. **Rama reservada:** `regla-02-cotizaciones`.

## R03 — Prioridad Alta automática

1. **Función:** Red/Servidores y las palabras completas red o conectividad de internet fuerzan Alta tanto en soporte como mantenimiento. Pared no coincide con red.
2. **Archivos reales:** config/settings.py; config/reglas.py; soporte/models.py; mantenimiento/models.py; frontend/src/components/PrioridadAutomatica.vue.
3. **Implementación:** normalizar; prioridad_automatica; prioridad_objeto; save de ambos modelos.
4. **Configuración:** `SIA_CATEGORIAS_PRIORIDAD; SIA_PALABRAS_PRIORIDAD; SIA_PRIORIDAD_AUTOMATICA`.
5. **Valor inicial:** RED/REDES/SERVIDOR/SERVIDORES; red/conectividad de internet; ALTA.
6. **Ejemplo de modificación:** `En settings.py agregar 'wifi' a SIA_PALABRAS_PRIORIDAD`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** Crear una solicitud con Falla de RED y otra con Pared dañada. La primera queda Alta y bloquea la selección de prioridad en Jefatura. La categoría Red del solicitante también fuerza Alta. Repetir por API.
9. **Reversión:** Retirar wifi y reiniciar. Los expedientes existentes conservan su historial.
10. **Rama reservada:** `regla-03-prioridad-categoria`. Borrador de revisión: `docs/pull-requests/R03.md`.

## R04 — SLA desde la creación

1. **Función:** Asigna Alta 4 h, Media 24 h y Baja 72 h desde la creación; una clasificación posterior no reinicia el plazo. Vencido corresponde a expedientes activos.
2. **Archivos reales:** config/sla.py; soporte/models.py; soporte/views.py; soporte/serializers.py; mantenimiento/models.py; mantenimiento/prioridades.py; mantenimiento/serializers.py.
3. **Implementación:** horas_sla; fecha_limite; save; get_sla_estado.
4. **Configuración:** `SIA_SLA_ALTA_HORAS; SIA_SLA_MEDIA_HORAS; SIA_SLA_BAJA_HORAS; SIA_SLA_CRITICA_HORAS`.
5. **Valor inicial:** 4; 24; 72; 4 (compatibilidad de prioridad crítica existente).
6. **Ejemplo de modificación:** `SIA_SLA_ALTA_HORAS=6`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** Crear una solicitud Alta y verificar vencimiento = creación + 4 h. La clasificación no mueve esa base. Un cierre deja de mostrarse Vencido; puede conservar resultado histórico incumplido.
9. **Reversión:** Restaurar 4 y reiniciar. No modificar fechas históricas para ocultar incumplimientos.
10. **Rama reservada:** `regla-04-sla`. Borrador de revisión: `docs/pull-requests/R04.md`.

## R05 — Flujo de estados

1. **Función:** Valida las fases Abierto → En proceso → Resuelto → Cerrado y Resuelto → En proceso. Resolver exige solución. Conserva los pasos institucionales existentes del BPMN.
2. **Archivos reales:** config/flujo_tickets.py; soporte/views.py; soporte/serializers.py.
3. **Implementación:** validar_transicion; TicketSerializer.validate; acciones existentes de TicketViewSet.
4. **Configuración:** `Mapa de fases y transiciones en config/flujo_tickets.py`.
5. **Valor inicial:** Cuatro fases semánticas; solución obligatoria.
6. **Ejemplo de modificación:** `Editar el mapa de fases únicamente si cambia formalmente el flujo institucional y ajustar las pruebas.`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** Intentar saltar de abierto a cerrado o resolver sin solución; debe rechazarse. Usar acciones del flujo normal hasta el cierre. PATCH directo del estado tampoco debe eludir la regla.
9. **Reversión:** Restaurar el mapa y ejecutar pruebas. No borrar estados del catálogo ni las bitácoras.
10. **Rama reservada:** `regla-05-flujo-estados`. Borrador de revisión: `docs/pull-requests/R05.md`.

## R06 — Reapertura por el solicitante

1. **Función:** Solo el propietario puede reabrir un ticket cerrado dentro de siete horas. Conserva el cierre anterior y archiva solución y referencias documentales del ciclo anterior.
2. **Archivos reales:** soporte/reapertura.py; soporte/views.py; soporte/models.py; soporte/serializers.py; usuarios/archivos.py; frontend/src/views/MisSolicitudesView.vue.
3. **Implementación:** fecha_maxima; puede_reabrir; archivar_ciclo; reabrir_ticket.
4. **Configuración:** `SIA_HORAS_REAPERTURA`.
5. **Valor configurado:** 7 horas.
6. **Ejemplo de modificación:** `SIA_HORAS_REAPERTURA=10`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** Como propietario reabrir un cierre reciente; comprobar estado En ejecución, nuevo plazo y cierre anterior conservado. Otro usuario y un cierre de ocho horas se rechazan con valor 7; las pruebas aisladas cubren esos tiempos.
9. **Reversión:** Restaurar el valor anterior en horas y reiniciar. Mantener historial_reaperturas y archivos archivados.
10. **Rama reservada:** `regla-06-reapertura`. Borrador de revisión: `docs/pull-requests/R06.md`.

## R07 — Carga máxima por técnico

1. **Función:** No permite una sexta asignación activa cuando el máximo es cinco. Cuenta asignaciones principales, apoyos y mantenimiento; resolver libera carga.
2. **Archivos reales:** soporte/carga_tecnica.py; soporte/views.py; mantenimiento/views.py; usuarios/views.py; frontend/src/views/JefeUticDashboardView.vue; frontend/src/views/ServiciosGeneralesDashboardView.vue.
3. **Implementación:** carga_activa; bloquear_y_validar; acciones de asignación y reapertura.
4. **Configuración:** `SIA_MAX_TICKETS_TECNICO`.
5. **Valor inicial:** 5.
6. **Ejemplo de modificación:** `SIA_MAX_TICKETS_TECNICO=8`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** Asignar cinco trabajos activos y rechazar el sexto. Resolver uno y volver a asignar. Con 8, la sexta asignación se permite. PostgreSQL prueba dos asignaciones concurrentes cuando queda un solo cupo.
9. **Reversión:** Restaurar 5 y reiniciar. No elimina asignaciones existentes; bloquea nuevas si ya se supera el máximo.
10. **Rama reservada:** `regla-07-carga-tecnico`. Borrador de revisión: `docs/pull-requests/R07.md`.

## R08 — Jefatura y DAF, sin aprobación del Director

1. **Función:** conservar revisión/viabilidad de Jefatura y evaluación/certificación de DAF; derivar directamente a Tesorería sin otra aprobación del Director, incluso por encima de 300.
2. **Archivos:** `backend/config/settings.py`, `backend/compras/views.py`, `backend/compras/aprobacion.py`, `backend/compras/serializers.py`, `frontend/src/views/DafDashboardView.vue`, `frontend/src/views/DafEmitirView.vue`.
3. **Funciones:** `certificar_daf`, `_transicion`, `validar_aprobador`, `puede_aprobar_final`.
4. **Variable:** `SIA_REQUIERE_APROBACION_DIRECTOR`.
5. **Valor vigente:** False. Conserva permisos institucionales, prohibición de autoaprobación y reserva de saldo.
6. **Ejemplo:** True reactiva expresamente el paso anterior del Director. El umbral de 300 y grupo administrativo solo afectan ese modo anterior.
7. **Aplicar:** reiniciar Django y actualizar navegador; sin migración ni recompilación por configuración.
8. **Probar:** DAF certifica 400 con saldo suficiente y queda APROBADO_PARA_DESEMBOLSO; sin saldo se rechaza sin avanzar. Usuario sin permiso o propia compra se rechaza. Director no tiene acción de aprobación en el modo vigente.
9. **Revertir configuración:** cambiar a True solo si se solicita volver al paso anterior. No alterar manualmente estados ni borrar certificaciones.
10. **Rama reservada:** `regla-08-aprobacion`.

## R09 — Fondo mensual y saldo

1. **Función:** Reserva al aprobar, convierte la reserva en desembolso sin descontar dos veces y bloquea operaciones sin saldo. Expone resumen financiero, movimientos y constancia PDF.
2. **Archivos reales:** compras/caja_chica.py; compras/models.py; compras/views.py; compras/tesoreria.py; config/urls.py; frontend/src/components/CajaChicaPanel.vue; frontend/src/utils/errorRegla.js; frontend/src/views/TesoreriaDashboardView.vue.
3. **Implementación:** resumen; registrar_operacion; liberar; saldo_view; acciones existentes de recibo y confirmación.
4. **Configuración:** `SIA_FONDO_MENSUAL`.
5. **Valor inicial:** 5000.
6. **Ejemplo de modificación:** `SIA_FONDO_MENSUAL=7000`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** En Tesorería → Control de Caja Chica comprobar fondo, comprometido, desembolsado, saldo y porcentaje. Aprobar reserva el importe; confirmar el pago lo convierte sin doble descuento. Intentar un importe mayor al saldo: rechazo R09 y modal institucional. Cambiar a 7000 y verificar respuesta y panel tras reiniciar/actualizar.
9. **Reversión:** Restaurar 5000 y reiniciar. Mantener movimientos y documentos: reducir el fondo puede dejar saldo histórico negativo y bloquear nuevos compromisos.
10. **Rama reservada:** `regla-09-fondo-saldo`. Borrador de revisión: `docs/pull-requests/R09.md`.

## R10 — Política de contraseñas

1. **Función:** Conserva los validadores y hashes existentes. Corrige la ayuda de las pantallas que indicaba ocho caracteres para mostrar el mínimo real de diez.
2. **Archivos reales:** config/settings.py; config/publica.py; config/urls.py; usuarios/test_r10.py; frontend/src/utils/politicaPassword.js; frontend/src/views/CambiarPasswordView.vue; frontend/src/views/RecuperarPasswordView.vue.
3. **Implementación:** validadores AUTH_PASSWORD_VALIDATORS existentes; configuración pública de presentación; comprobar hashes en test_r10.
4. **Configuración:** `AUTH_PASSWORD_VALIDATORS → MinimumLengthValidator → OPTIONS.min_length`.
5. **Valor inicial:** 10; Argon2 como hash preferido; PBKDF2 compatible.
6. **Ejemplo de modificación:** `En settings.py cambiar OPTIONS de MinimumLengthValidator a {'min_length': 12}; mantener el resto de validadores`.
7. **Aplicación del cambio:** reiniciar Django y actualizar la pantalla; sin migración ni recompilación para modificar estos valores. La instalación inicial sí aplica las migraciones documentadas.
8. **Prueba:** Ejecutar usuarios.test_r10. Verificar mínimo, similitud, contraseña numérica y compatibilidad Argon2/PBKDF2. GET /api/configuracion-publica/ devuelve únicamente password_min_length. Las pantallas consultan ese valor.
9. **Reversión:** Restaurar min_length 10 y reiniciar. No modificar hashes ni contraseñas almacenadas.
10. **Rama reservada:** `regla-10-contrasenas`. Borrador de revisión: `docs/pull-requests/R10.md`.

## Detalles que afectan las pruebas

- R04 conserva estados y etapas existentes. Los tickets activos anteriores reciben plazo desde su creación mediante migración; por eso una solicitud antigua puede aparecer vencida correctamente. Cambiar la configuración afecta cálculos nuevos; no reescribe masivamente fechas de expedientes guardados.
- R06 conserva `cerrado_en`; la fecha de reapertura se guarda aparte y se inicia otro plazo. Las soluciones y documentos anteriores quedan en el historial del expediente, con los mismos controles de acceso.
- R07 y R09 usan transacciones y bloqueos de filas en PostgreSQL. SQLite tiene una protección local para el proceso de desarrollo; no equivale a concurrencia de múltiples procesos. Ejecutar la suite PostgreSQL para demostrar las carreras.
- R08 no concede permisos financieros a jefaturas técnicas. La membresía del antiguo paso del Director se conserva como dato histórico y solo interviene si SIA_REQUIERE_APROBACION_DIRECTOR=True.
- R09 registra movimientos históricos sin borrar compras ni recibos. Si no había fecha inequívoca de pago, identifica el origen como REGISTRO_LEGADO. La reserva queda ligada al mes de aprobación incluso si el pago se confirma en otro mes. El panel usa el fondo configurado vigente también al consultar meses históricos.
- R09 mantiene intacto el recibo original firmado. Su saldo es una proyección al generarlo; al confirmar el pago genera una constancia PDF adicional con el saldo efectivo de la transacción. Otros pagos entre ambas acciones pueden cambiar ese saldo.
- No se recomienda revertir migraciones para cambiar valores. Restaurar la configuración y conservar el historial. El respaldo previo está en `tmp/db-antes-diez-reglas-20261025-182658.sqlite3`.
