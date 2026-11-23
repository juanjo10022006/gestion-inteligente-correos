$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 12)
$project = "correos-smoke-$suffix"
$previousDatabase = $env:MONGODB_DB_NAME
$previousEnvironment = $env:APP_ENV
$env:MONGODB_DB_NAME = "compose_smoke_$suffix"
$env:APP_ENV = "local"
$arguments = @("--project-name", $project, "--file", (Join-Path $root "compose.yaml"),
               "--file", (Join-Path $PSScriptRoot "compose.ephemeral.yaml"))
Push-Location $root
try {
    # Paths in every override resolve relative to the first Compose file.
    docker compose @arguments config --quiet
    if ($LASTEXITCODE -ne 0) { throw "Configuración Compose efímera inválida." }
    docker compose @arguments up -d --build --wait --wait-timeout 120
    if ($LASTEXITCODE -ne 0) { throw "No arrancaron los cuatro servicios efímeros." }
    docker compose @arguments exec -T -e PYTHONPATH=/app api python /checks/compose_smoke.py
    if ($LASTEXITCODE -ne 0) { throw "Falló el flujo Compose efímero." }
}
finally {
    # Only our unique project; no -v and no operations on the demo project.
    docker compose @arguments down
    $env:MONGODB_DB_NAME = $previousDatabase
    $env:APP_ENV = $previousEnvironment
    Pop-Location
}
