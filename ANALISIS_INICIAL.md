# Analisis inicial - 25 de octubre de 2026

## Entorno y ejecucion

- Interfaz: Vue 3, Vue Router y Vite; API: Django y Django REST Framework; datos: SQLite.
- Se instalaron Python 3.14.2 y Node.js 24.22.1 localmente en `.runtime/`.
- Se instalaron las dependencias Python declaradas y 174 paquetes npm con `npm ci`, respetando el lockfile.
- El antiguo entorno `backend/.venv` apunta a una ruta de otra computadora. Se creo `backend/.venv-local`.
- Se agregaron `iniciar.ps1` y `EJECUCION_LOCAL.md` para ejecutar ambos servicios.

## Ajustes realizados

- Se reemplazo `MAILERS`, que Django no utiliza, por `EMAIL_BACKEND` con salida a consola para desarrollo. Esto no configura envio SMTP real.
- Se declaro explicitamente `DEFAULT_AUTO_FIELD` como `BigAutoField`, coherente con las migraciones existentes.
- Se genero y aplico la migracion pendiente de los valores predeterminados de preferencias (nombre SIA y limite 1000), respetando el modelo actual. No se modificaron las reglas de compras ni los valores guardados de las preferencias existentes.
- Se respaldo SQLite antes de migrar en `tmp/db-antes-migracion-20261025-173940.sqlite3`.

## Verificaciones

- SQLite `PRAGMA quick_check`: `ok`; 17 usuarios existentes.
- `pip check`: sin dependencias incompatibles.
- `manage.py check`: sin incidencias.
- `makemigrations --check --dry-run`: sin cambios pendientes despues de generar la migracion.
- `npm run build`: correcto. Advierte de un paquete JavaScript mayor a 500 kB; conviene revisar la carga diferida de vistas para mejorar la carga inicial.
- Pruebas JavaScript existentes: 3 de 3 correctas.
- Pruebas Django: 86 de 87 correctas. Falla `mantenimiento.tests.FlujoMantenimientoTests.test_requerimiento_con_compra_no_viable` con `KeyError: requerimiento` en `mantenimiento/tests.py:266`. La respuesta de solicitar-requerimiento no contiene la clave esperada; falta diagnosticar si la prueba esta desactualizada o el flujo tiene un defecto.
- Al finalizar las pruebas aparece ademas un error de limpieza de un PDF temporal bloqueado en Windows. Conviene revisar el cierre de archivos en las pruebas.
- HTTP de la interfaz: 200 en `http://127.0.0.1:5173/`.
- API a traves del proxy de Vite: 401 en `/api/usuarios/mi-contexto/` sin sesion, respuesta esperada para ese endpoint protegido.

## Alcance pendiente

La compilacion y el arranque estan comprobados. Falta revisar visualmente las pantallas en navegador y probar los procesos completos por rol, incluyendo autenticacion, mantenimiento, soporte, compras, documentos y recuperacion de acceso. Los resultados actuales no prueban que todos los flujos funcionen correctamente.

La arquitectura documentada contiene versiones y descripciones que difieren del codigo actual. Para futuras correcciones deben contrastarse con el comportamiento y las pruebas.

No se recargaron usuarios de prueba ni se reiniciaron los datos existentes.
