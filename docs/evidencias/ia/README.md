# Evidencia IA curada

**Fuentes técnicas:** commit `3f9a067`; revisión documental del 23 de noviembre de 2026. No se entrenó ni se ejecutaron notebooks durante este cierre documental.

| Archivo | Procedencia y alcance |
|---|---|
| [evaluacion_artefacto.json](evaluacion_artefacto.json) | Evaluación previa del archivo servido; incluye contraste `/health` mediante `servedArtifactVerified=true` |
| [manifest.json](manifest.json) | Versión y SHA-256 del mismo archivo; no incluye el binario |
| [ejecucion_notebooks.json](ejecucion_notebooks.json) | Ejecución anterior de los tres notebooks, con 2/3/5 celdas y cero errores |
| [procedencia.json](procedencia.json) | Commit, huellas de fuentes y archivos, origen local y distinción entre modelo de notebook y servido |
| [eda_balance_longitud.png](eda_balance_longitud.png) | Balance train/validation y longitud normalizada; no explora el test para seleccionar |
| [matriz_confusion_test.png](matriz_confusion_test.png) | Confusión del test congelado, consistente con la evaluación servida |

En este cierre se comprobaron las huellas del modelo local, manifiesto, dataset, entrenamiento y preprocesamiento; se compararon las fuentes de notebooks con las celdas de su ejecución previa y la igualdad de versión/métricas entre ambos reportes. No se presentó esa revisión de archivos como una nueva ejecución HTTP o prueba integral.

El origen `ai_service/artifacts/cierre-tecnico-lf/` citado en `procedencia.json` es **local e ignorado**: no estará disponible al clonar GitHub. Esta carpeta documental contiene solo la selección pública anterior, sin credenciales, `.joblib` ni notebooks ejecutados. Los binarios se reconstruyen según el [README IA](../../../ai_service/README.md), o se distribuyen mediante un paquete de entrega explícito; no se modificó `.gitignore`.

Las huellas auxiliares de JSON documental se comprueban con UTF-8/LF: si Git convierte esos textos a CRLF en Windows, normalice CRLF a LF antes de calcularlas. Los PNG y el `.joblib` usan bytes originales; nunca normalice un binario para verificar su manifiesto.
