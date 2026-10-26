# Ejecucion local

El proyecto usa Vue 3 y Vite para la interfaz, Django REST Framework para la API y SQLite para los datos.

Se instalaron Python 3.14.2 y Node.js 24.22.1 en `.runtime/`, con las dependencias declaradas en `backend/requirements.txt` y `frontend/package-lock.json`. El entorno Python operativo es `backend/.venv-local/`; el antiguo `backend/.venv/` corresponde a otra computadora. Estas carpetas locales no se deben copiar ni versionar.

Desde la raiz del proyecto, abrir dos terminales PowerShell:

```powershell
# Terminal 1
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 backend
```

```powershell
# Terminal 2
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 frontend
```

Abrir http://127.0.0.1:5173. Detener cada servidor con Ctrl+C. Vite reenvia `/api` y `/media` al backend del puerto 8000. Las cuentas locales se describen en `CREDENCIALES_PRUEBA.md`.

El correo local se imprime en la consola del backend; no envia mensajes reales. Para usar correo real se requiere configurar un backend y los datos SMTP correspondientes.

## Verificacion

```powershell
.\backend\.venv-local\Scripts\python.exe -m pip check
cd backend
.\.venv-local\Scripts\python.exe manage.py check
.\.venv-local\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv-local\Scripts\python.exe manage.py test --settings=config.settings_tests --noinput
```

En otra terminal, desde la raiz:

```powershell
$env:PATH = "$PWD\.runtime\node-v24.22.1-win-x64;" + $env:PATH
cd frontend
npm.cmd run build
node --test src/utils/monto.test.js src/utils/portal.test.js src/utils/reglasCore.test.js
```

Las pruebas Django usan una base temporal y almacenamiento separado de los expedientes existentes. No ejecutar los comandos de carga de usuarios sobre la base actual sin revisar sus efectos.

R01 a R10: consultar `REQUERIMIENTOS_CONFIGURACION.md` para cambiar límites, plazos, carga y fondo mensual. La entrega actual está en `RESULTADO_DIEZ_REGLAS.md` y las pruebas manuales en `PRUEBAS_DEFENSA.md`. `RESULTADO_R01_R02_R03.md` documenta la etapa anterior.

## Configuración y dependencias

Django lee `.env` desde la raíz. `.env.example` contiene los valores iniciales; no sobrescribir una configuración personalizada. Después de editarlo, reiniciar el backend y actualizar la pantalla. Las variables de entorno de la terminal prevalecen sobre `.env`.

Para reinstalar las dependencias declaradas usando los runtimes locales:

```powershell
.\backend\.venv-local\Scripts\python.exe -m pip install -r .\backend\requirements.txt
$env:PATH = "$PWD\.runtime\node-v24.22.1-win-x64;" + $env:PATH
Set-Location frontend
npm.cmd ci
```

Las migraciones autorizadas ya están aplicadas en esta computadora. En otra copia, respaldar la base antes de ejecutar `manage.py migrate`. No ejecutar cargas iniciales de usuarios para iniciar el sistema existente. No hacen falta extensiones de VS Code para ejecutarlo.

## Pruebas reales de concurrencia

PostgreSQL 16.13 se instaló de forma portable en `.runtime/postgresql/`, aislado del SQLite usado por la aplicación. No modifica servicios del sistema ni VirtualBox.

```powershell
# Desde la raíz
powershell -ExecutionPolicy Bypass -File .\iniciar-postgres-pruebas.ps1
Set-Location backend
.\.venv-local\Scripts\python.exe manage.py test --settings=config.settings_postgres_tests --noinput
```

El servidor de prueba escucha solo en `127.0.0.1:55432`, con usuario local `sia_test`; usa autenticación trust únicamente en este entorno aislado. No debe exponerse ni utilizarse como configuración de producción. Django crea y elimina su propia base `test_sia_reglas_test_base`. Las pruebas no copian ni modifican los expedientes de la aplicación.

Para detener PostgreSQL de pruebas, desde la raíz:

```powershell
& .\.runtime\postgresql\pgsql\bin\pg_ctl.exe -D .\.runtime\pgdata stop -m fast
```
