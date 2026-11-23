# Laboratorio académico de NLP

**Juan Camilo Gonzales y Juan Jose Solarte — Proyecto 15.**

Ejecutar en orden:

| Notebook fuente | Objetivo |
|---|---|
| [00_verificacion_entorno.ipynb](00_verificacion_entorno.ipynb) | Dependencias, contrato y preparación de texto sin secretos |
| [01_eda_dataset.ipynb](01_eda_dataset.ipynb) | Procedencia, calidad, duplicados, balance y longitudes |
| [02_entrenamiento_evaluacion.ipynb](02_entrenamiento_evaluacion.ipynb) | Baseline, selección en validación, promoción, métricas y errores |

Son fuentes sin resultados embebidos. Importan los módulos Python de `ai_service/`; no mantienen otro algoritmo ni sustituyen al servicio HTTP.

## Alternativa A: VS Code y entorno virtual

Requiere Python 3.13, VS Code y extensiones Python y Jupyter. Desde la raíz del repositorio, en PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r ai_service/requirements.txt -r ai_service/requirements-notebooks.txt
.\.venv\Scripts\python.exe -m pip check
```

Abre cada notebook y selecciona **Select Kernel → Python Environments → .venv** del proyecto. La primera celda comprueba las versiones. No elijas un kernel global con paquetes diferentes. No es necesario activar `.venv` si se usan las rutas explícitas anteriores.

Si no está instalado el lanzador `py`, comprueba `python --version` y usa `python -m venv .venv` únicamente si ese intérprete es Python 3.13.

## Alternativa B: Anaconda/Jupyter

Es una alternativa a la anterior, no una segunda instalación obligatoria. Desde Anaconda Prompt, situado en la raíz:

```text
conda create -n correos-nlp python=3.13
conda activate correos-nlp
python -m pip install -r backend/requirements.txt -r ai_service/requirements.txt -r ai_service/requirements-notebooks.txt
python -m ipykernel install --user --name correos-nlp --display-name "correos-nlp"
python -m jupyterlab
```

Selecciona el kernel **correos-nlp**. Los paquetes de inferencia están fijados en `ai_service/requirements.txt`; las herramientas académicas en `requirements-notebooks.txt`. No basta con tener Jupyter instalado: el kernel debe usar ese entorno. La reproducción exacta de versión registrada usa el Python 3.13.18 de Docker; otro parche Python puede producir otra identificación válida.

## Ejecución automatizada

Con `.venv`, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m ai_service.run_notebooks --output-dir ai_service/artifacts/notebooks-local
```

Para conservar todas las salidas interactivas juntas, antes de abrir Jupyter:

```powershell
$env:NLP_NOTEBOOK_OUTPUT = (Join-Path (Get-Location) 'ai_service/artifacts/notebooks-local')
.\.venv\Scripts\python.exe -m jupyterlab
```

Sin esa variable, las celdas usan directorios temporales; el ejecutor automatizado la establece y crea el directorio.

Alternativa Docker, sin Python/Jupyter en el host:

```powershell
docker build --target notebooks -t gestion-correos-notebooks:local .
$salida = Join-Path (Get-Location) 'ai_service/artifacts/notebooks-local'
New-Item -ItemType Directory -Force -Path $salida | Out-Null
docker run --rm --network none --mount "type=bind,source=$salida,target=/evidence" gestion-correos-notebooks:local python -m ai_service.run_notebooks --output-dir /evidence
```

El target `notebooks` agrega las herramientas académicas. El target `ai` de Compose **no instala Jupyter**. La ejecución aislada puede mostrar una advertencia de transporte TCP del kernel; no se publican puertos ni se conecta a MongoDB.

## Datos, selección y resultados

Se lee [el dataset v0.3](../data/correos_sinteticos_v0.3.jsonl): 128 mensajes sintéticos, particiones fijas **80 train / 24 validation / 24 test**, cuatro categorías balanceadas. Véase [procedencia](../data/README.md). No es Big Data en volumen ni una muestra representativa de empresas.

`prepare_text` normaliza espacios sin alterar los originales. Se verifican IDs, textos normalizados duplicados y etiquetas. El EDA léxico/de longitudes se limita a train/validation. TF-IDF se ajusta dentro de `Pipeline` solo con train; `C` se elige por Macro-F1 en validation, con desempate por log-loss y menor `C`. El baseline siempre predice la clase más frecuente.

El umbral 0,45 permanece provisional: la tabla de sensibilidad usa **solo validation**. El test se evalúa con el artefacto ya congelado; no selecciona hiperparámetros ni umbral. Este test ya fue observado en el proyecto: repetirlo no constituye una nueva prueba ciega. Para nuevas decisiones se necesita otro protocolo y un test nuevo.

En el directorio de salida quedan:

- Tres `.ipynb` ejecutados y `execution.json` (2, 3 y 5 celdas de código en la evidencia curada, sin errores).
- `eda_balance_longitud.png` y `matriz_confusion_test.png`, también embebidas en los notebooks ejecutados.
- `candidate/`: entrenamiento y reporte de validación.
- `frozen/model.joblib` y `frozen/manifest.json`: candidato promovido.
- `notebook-evaluation.json`: evaluación del modelo congelado.

**Fuentes en Git:** `ai_service/notebooks/*.ipynb`, módulos, dataset y requisitos. **Salidas ignoradas:** `ai_service/artifacts/`. No uses `git add -f` ni publiques notebooks con secretos. Las [figuras y métricas curadas](../../docs/evidencias/ia/README.md) son una selección documental, no la carpeta temporal completa.

## Comparar con el servicio

La evidencia de referencia corresponde a `tfidf-logreg-4899d09a3071f491`; [evaluación y huellas](../../docs/09_evaluacion_final_ia.md). Desde Compose:

```powershell
docker compose exec -T ai python -c "import json; from urllib.request import urlopen; print(json.load(urlopen('http://127.0.0.1:8001/health')))"
docker compose exec -T ai python -m ai_service.evaluate_artifact --include-test --service-url http://127.0.0.1:8001 --output /tmp/evaluacion-servida.json
```

El segundo comando **no reentrena**: compara versión y SHA-256 del archivo servido. Compara también `modelVersion`, dataset, dependencias y métricas del reporte con `notebook-evaluation.json`. Distintos archivos `.joblib` pueden ser funcionalmente equivalentes sin tener el mismo checksum. La igualdad de métricas por sí sola no prueba igualdad de todas las probabilidades; el bloque técnico contrastó además vocabulario, parámetros y probabilidades.

El 95,8 % de exactitud y Macro-F1 0,958 son resultados de 24 correos sintéticos; no prometen generalización. Tampoco se midió una tasa real de correcciones humanas.
