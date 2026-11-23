param([string]$AiImage = "gestion-correos-ai-final:local")
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 12)
$network = "history-test-$suffix"
$mongo = "history-mongo-$suffix"
$ai = "history-ai-$suffix"
$image = "gestion-correos-history-test:$suffix"

function Assert-Exit([string]$message) {
    if ($LASTEXITCODE -ne 0) { throw $message }
}

Push-Location $root
try {
    docker build --target api -t $image .
    Assert-Exit "No se pudo construir la API de prueba."
    docker network create $network | Out-Null
    Assert-Exit "No se pudo crear la red temporal."
    docker run -d --rm --name $mongo --network $network --tmpfs /data/db --tmpfs /data/configdb mongo:8.0 | Out-Null
    Assert-Exit "No se pudo iniciar MongoDB efímero."
    docker run -d --rm --name $ai --network $network $AiImage | Out-Null
    Assert-Exit "Se requiere construir la imagen IA de verificación."
    $mongoReady = $false
    $aiReady = $false
    $ErrorActionPreference = "Continue"
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if (-not $mongoReady) {
            docker exec $mongo mongosh --quiet --eval "db.adminCommand({ping:1}).ok" 2>$null | Out-Null
            $mongoReady = $LASTEXITCODE -eq 0
        }
        if (-not $aiReady) {
            docker exec $ai python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8001/health', timeout=2).close()" 2>$null
            $aiReady = $LASTEXITCODE -eq 0
        }
        if ($mongoReady -and $aiReady) { break }
        Start-Sleep -Seconds 1
    }
    $ErrorActionPreference = "Stop"
    if (-not $mongoReady -or -not $aiReady) { throw "Los servicios temporales no quedaron disponibles." }
    docker run --rm --network none --mount "type=bind,source=$PSScriptRoot,target=/checks,readonly" `
        -e "PYTHONPATH=/app" $AiImage python /checks/artifact_verification.py
    Assert-Exit "Falló la reproducción del artefacto."
    docker exec $ai python -m ai_service.evaluate_artifact --include-test `
        --service-url http://127.0.0.1:8001 --output /tmp/evaluation-served.json | Out-Null
    Assert-Exit "El reporte no coincide con el artefacto servido."
    New-Item -ItemType Directory -Force -Path (Join-Path $root "ai_service/artifacts") | Out-Null
    docker cp "${ai}:/tmp/evaluation-served.json" (Join-Path $root "ai_service/artifacts/evaluation-served.json")
    Assert-Exit "No se pudo conservar el reporte de prueba."
    foreach ($test in @("init_db_verification.py", "compose_acceptance.py", "history_acceptance.py",
                        "access_acceptance.py", "final_acceptance.py")) {
        docker run --rm --network $network `
            --mount "type=bind,source=$PSScriptRoot,target=/checks,readonly" `
            -e "PYTHONPATH=/app" `
            -e "MONGODB_URI=mongodb://${mongo}:27017" `
            -e "MONGODB_DB_NAME=init_db_test_$suffix" `
            -e "AI_SERVICE_URL=http://${ai}:8001" `
            $image python "/checks/$test"
        Assert-Exit "Falló $test."
    }
}
finally {
    $ErrorActionPreference = "Continue"
    docker rm -f $ai 2>$null | Out-Null
    docker rm -f $mongo 2>$null | Out-Null
    docker network rm $network 2>$null | Out-Null
    docker image rm $image 2>$null | Out-Null
    Pop-Location
}
