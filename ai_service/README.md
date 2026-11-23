# Clasificador NLP: entrenamiento, promoción e inferencia

La ejecución principal es Docker Compose, según el [README del proyecto](../README.md). No requiere Jupyter para clasificar. La [evaluación documentada](../docs/09_evaluacion_final_ia.md) usa el artefacto `tfidf-logreg-4899d09a3071f491`; la versión de una reconstrucción se comprueba, no se fuerza por nombre.

## Reconstrucción Docker

```powershell
docker build --target ai -t gestion-correos-ai-final:local .
```

La etapa `model-build` entrena con train, selecciona `C` con validation y crea `/candidate`. `promote` copia el único candidato a `/model/model.joblib`, escribe `/model/manifest.json` y verifica compatibilidad. Se evalúa validation en `/model/validation.json`. El target `ai` copia ese bundle: no reentrena por solicitud ni evalúa test durante el build. Cambios relevantes invalidan la caché.

Python base está fijado por digest y las dependencias relevantes por versión. Se conservan LF en los archivos que intervienen en las huellas. `modelVersion` deriva del dataset, código de entrenamiento/preprocesamiento, parámetros y entorno. El SHA-256 del `.joblib` identifica el archivo concreto, no solo su receta.

## Entrenamiento local opcional

Desde la raíz, con Python 3.13 en PowerShell (el entorno Docker de referencia usa 3.13.18):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r ai_service/requirements.txt
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
.\.venv\Scripts\python.exe -m ai_service.train --output-dir ai_service/artifacts/candidate
.\.venv\Scripts\python.exe -m ai_service.promote --candidate-dir ai_service/artifacts/candidate --output-dir ai_service/artifacts/frozen
.\.venv\Scripts\python.exe -m ai_service.evaluate_artifact --model ai_service/artifacts/frozen/model.joblib --output ai_service/artifacts/validation.json
```

Use un directorio de candidatos dedicado: `promote` exige exactamente un `.joblib` y no elige silenciosamente entre modelos antiguos. Al repetir con otra receta, utilice otro directorio, sin borrar resultados anteriores indiscriminadamente.

El entrenamiento comprueba las cuatro etiquetas en cada partición y rechaza IDs o textos normalizados duplicados. Ajusta solo con train. Compara `DummyClassifier(strategy="most_frequent")` con TF-IDF de unigramas/bigramas y regresión logística. Los valores de `C` son 0,5; 1; 3; 10; 30. Selecciona por Macro-F1 en validation, desempata por log-loss y menor `C`; la referencia eligió 30.

Los [128 correos sintéticos v0.3](data/README.md) se dividen en 80/24/24. No contienen buzones reales. El artefacto conserva versión, clases, parámetros, dependencias y huellas de dataset/código. `load_verified` comprueba checksum antes de deserializar, Python/dependencias, preprocesamiento y clases. **Los hashes no son firmas y joblib puede ejecutar código:** cargar solo artefactos locales confiables del equipo.

## Evaluar el archivo realmente servido

Con Compose ya levantado:

```powershell
docker compose exec -T ai python -c "import json; from urllib.request import urlopen; print(json.load(urlopen('http://127.0.0.1:8001/health')))"
docker compose exec -T ai python -m ai_service.evaluate_artifact --include-test --service-url http://127.0.0.1:8001 --output /tmp/evaluacion-servida.json
New-Item -ItemType Directory -Force -Path ai_service/artifacts | Out-Null
docker compose cp ai:/tmp/evaluacion-servida.json ai_service/artifacts/evaluacion-servida.json
```

Este evaluador carga el bundle congelado, comprueba el dataset y contrasta `modelVersion`/`artifactSha256` con `/health`. **No reentrena**. Sin `--include-test` evalúa solo validation. El flag `train --evaluate-test` existe, pero reentrena y no es el procedimiento para acreditar el archivo servido.

La evidencia curada contiene Macro-F1 0,100 del baseline y 0,958 del clasificador tanto en validation como en test, calculados separadamente. El test tiene 23/24 aciertos. Ya fue observado anteriormente: no usarlo para volver a escoger modelo/umbral ni denominar una repetición nueva prueba ciega.

## Comparación de umbrales

El evaluador anterior incluye sensibilidad en validation para 0,30; 0,40; 0,45; 0,55; 0,70, aun cuando se solicite además el reporte test. También existe:

```powershell
.\.venv\Scripts\python.exe -m ai_service.compare_thresholds ai_service/artifacts/frozen/model.joblib
```

`compare_thresholds` es una herramienta local para un joblib confiable; para verificación de integridad prefiera `evaluate_artifact`. A 0,45 se asignan simuladamente 20/24 mensajes de validation, sin errores en esos 20; a 0,40 son 21/24 con el mismo acierto automático observado. Por tanto **0,45 no es óptimo demostrado**. Es configuración provisional de demo; H-01=0,70 permanece como hipótesis original no validada.

## Servicio de IA local

Use el bundle promovido y un entorno compatible; no apunte al candidato sin manifiesto:

```powershell
$env:AI_MODEL_PATH = (Join-Path (Get-Location) 'ai_service/artifacts/frozen/model.joblib')
.\.venv\Scripts\python.exe -m uvicorn ai_service.main:app --host 127.0.0.1 --port 8001
```

La API de mensajes usa `http://127.0.0.1:8001` por defecto. Si cambias la dirección del servicio, configura `AI_SERVICE_URL` en el proceso de la API. Puedes comprobar la versión cargada en `GET /health`.

## Fuentes, salidas y entrega del binario

Fuentes en Git: módulos `.py`, requisitos, datos JSONL y notebooks sin ejecutar. `ai_service/artifacts/` es salida local ignorada; **el binario no está en Git**. La versión se puede reconstruir desde la receta, pero no se afirma serialización idéntica byte a byte. El manifiesto garantiza integridad del archivo que se evaluó.

Si el profesor exige un binario congelado, extraiga `/model` de la imagen realmente evaluada mediante `docker compose cp ai:/model ai_service/artifacts/bundle-entrega`, agregue su reporte contrastado y las versiones de entorno, y distribuya un ZIP de entrega/release controlado fuera del historial fuente. No cambie `.gitignore` ni use `git add -f`. Compruebe que el SHA del binario coincide con el manifiesto entregado.

Consulte el [README de notebooks](notebooks/README.md), [evidencias curadas](../docs/evidencias/ia/README.md) y [manual técnico](../docs/MANUAL_TECNICO.md).
