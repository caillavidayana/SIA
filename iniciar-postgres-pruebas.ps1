$ErrorActionPreference = 'Stop'
$raizSia = $PSScriptRoot
$binSia = Join-Path $raizSia '.runtime/postgresql/pgsql/bin'
$datosSia = Join-Path $raizSia '.runtime/pgdata'
if (-not (Test-Path (Join-Path $binSia 'pg_ctl.exe'))) { throw 'Faltan los binarios locales de PostgreSQL para pruebas.' }
if (-not (Test-Path (Join-Path $datosSia 'PG_VERSION'))) {
    & (Join-Path $binSia 'initdb.exe') -D $datosSia -U sia_test -A trust -E UTF8 --locale=C
    if ($LASTEXITCODE) { throw 'No se pudo inicializar la base aislada.' }
}
& (Join-Path $binSia 'pg_isready.exe') -h 127.0.0.1 -p 55432
if ($LASTEXITCODE) {
    & (Join-Path $binSia 'pg_ctl.exe') -D $datosSia -l (Join-Path $raizSia '.runtime/postgresql-pruebas.log') -o '-h 127.0.0.1 -p 55432' start -w
    if ($LASTEXITCODE) { throw 'No se pudo iniciar PostgreSQL de pruebas.' }
}
$existeSia = & (Join-Path $binSia 'psql.exe') -h 127.0.0.1 -p 55432 -U sia_test -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='sia_reglas_test_base'"
if ($existeSia -notmatch '1') {
    & (Join-Path $binSia 'createdb.exe') -h 127.0.0.1 -p 55432 -U sia_test sia_reglas_test_base
    if ($LASTEXITCODE) { throw 'No se pudo crear la base vacía de pruebas.' }
}
Write-Output 'PostgreSQL de pruebas disponible en localhost:55432. El sistema continúa usando su SQLite original.'
