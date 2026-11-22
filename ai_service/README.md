# Entrenamiento del clasificador

Desde la raíz del proyecto, con Python 3.13 en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r ai_service/requirements.txt
.\.venv\Scripts\python.exe -m ai_service.train
```

El comando comprueba las cuatro etiquetas en cada partición y rechaza IDs o textos duplicados. Entrena usando solo `train`. Compara un modelo base que siempre predice la categoría más frecuente con TF-IDF de palabras y pares de palabras más regresión logística.

La carpeta `ai_service/artifacts/` recibe el pipeline `.joblib` y el informe JSON con Macro-F1, exactitud, métricas por clase, matriz de confusión y simulación de enrutamiento. El artefacto conserva la versión del modelo, los parámetros, las dependencias y la huella SHA-256 del dataset. Carga únicamente artefactos generados por el equipo en el entorno correspondiente.

En la versión 0.3, el entrenamiento elige la regularización `C` por Macro-F1 en validación y usa la pérdida logarítmica para desempatar. Sobre los 24 mensajes de validación, el modelo base obtuvo Macro-F1 de 0,100 y el clasificador obtuvo 0,958. Evaluado en esos mismos mensajes, el modelo v0.2 obtuvo 0,785. Son resultados de una muestra pequeña y sintética usada para seleccionar el modelo.

Usa `--dataset ruta/al/dataset.jsonl` al ampliar la muestra. El comando normal conserva `test` sin evaluar. Usa `--evaluate-test` para la evaluación final, después de cerrar modelo y umbral.

## Comparación de umbrales

Para comparar varios umbrales con el artefacto ya entrenado, sin volver a entrenar ni evaluar la partición de prueba:

```powershell
.\.venv\Scripts\python.exe -m ai_service.compare_thresholds ai_service/artifacts/tfidf-logreg-ee43f4332cf74fba.joblib
```

Con el modelo v0.3 y 0,45, se asignarían 20 de los 24 correos de validación y los 20 serían correctos. Los otros cuatro requerirían revisión. Con 0,30, se asignarían los 24, uno de ellos al área equivocada. El 0,45 es provisional para la demo.

## Servicio de IA local

Instala las dependencias de FastAPI y Uvicorn junto con las del modelo. Usa la ruta exacta del artefacto que imprimió el entrenamiento.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
$env:AI_MODEL_PATH = 'ruta/al/modelo-generado.joblib'
.\.venv\Scripts\python.exe -m uvicorn ai_service.main:app --host 127.0.0.1 --port 8001
```

La API de mensajes usa `http://127.0.0.1:8001` por defecto. Si cambias la dirección del servicio, configura `AI_SERVICE_URL` en el proceso de la API. Puedes comprobar la versión cargada en `GET /health`.
