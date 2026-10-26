param(
    [ValidateSet('backend', 'frontend')]
    [string]$Servicio = 'frontend'
)

$ErrorActionPreference = 'Stop'
$raiz = $PSScriptRoot
if ($Servicio -eq 'backend') {
    Set-Location (Join-Path $raiz 'backend')
    $python = Join-Path $raiz 'backend/.venv-local/Scripts/python.exe'
    if (-not (Test-Path $python)) { throw 'Falta backend/.venv-local. Consulte EJECUCION_LOCAL.md.' }
    & $python manage.py runserver 127.0.0.1:8000 --noreload
} else {
    $node = Get-ChildItem (Join-Path $raiz '.runtime') -Directory -Filter 'node-*-win-x64' |
        Where-Object { Test-Path (Join-Path $_.FullName 'node.exe') } |
        Select-Object -First 1
    if (-not $node) { throw 'Falta Node.js local. Consulte EJECUCION_LOCAL.md.' }
    $env:PATH = $node.FullName + ';' + $env:PATH
    Set-Location (Join-Path $raiz 'frontend')
    & (Join-Path $node.FullName 'npm.cmd') run dev -- --host 127.0.0.1 --port 5173 --strictPort
}
exit $LASTEXITCODE
