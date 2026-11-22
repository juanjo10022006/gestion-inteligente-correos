# Evaluación final del clasificador de correos

Se evaluó en Docker el modelo `tfidf-logreg-e7dceaa59fc6e694`, la misma versión que sirve la demo. El dataset sintético v0.3 contiene 128 correos en español. Se usaron 80 para entrenar, 24 para elegir la configuración y 24 para la prueba final, con 6 correos de prueba por categoría. El umbral de enrutamiento de 0,45 se fijó con validación antes de evaluar la prueba.

## Comparación en la prueba final

| Modelo | Aciertos | Exactitud | Macro-F1 |
|---|---:|---:|---:|
| Base, predicción de la clase más frecuente | 6 de 24 | 25,0 % | 0,100 |
| TF-IDF y regresión logística | 23 de 24 | 95,8 % | 0,958 |

Cada fila de la matriz indica la categoría real y cada columna la predicción de mayor puntuación, antes de aplicar el umbral.

| Categoría real | Facturación | Recursos Humanos | Soporte Técnico | Ventas |
|---|---:|---:|---:|---:|
| Facturación | 6 | 0 | 0 | 0 |
| Recursos Humanos | 1 | 5 | 0 | 0 |
| Soporte Técnico | 0 | 0 | 6 | 0 |
| Ventas | 0 | 0 | 0 | 6 |

## Enrutamiento y revisión

Con el umbral del 45 %, 20 de los 24 correos (83,3 %) se habrían asignado automáticamente. Los 20 coinciden con sus etiquetas. Los otros 4 (16,7 %) habrían requerido revisión humana.

El único error de categoría fue «Inducción de personal» (`SYN-040`). Su etiqueta era Recursos Humanos y el modelo sugirió Facturación con 30,2 % de confianza. El umbral deriva ese caso a revisión. Los cuatro casos son derivaciones simuladas a partir de las predicciones. Esta evaluación no mide cuántas correcciones efectuaron operadores.

## Tiempo de inferencia

Se enviaron los 24 correos de prueba secuencialmente por HTTP a `/predict` dentro del contenedor de IA, con el modelo cargado. La mediana fue **1,7 ms** y el percentil 95 **2,1 ms**. La medición incluye la llamada HTTP local y excluye autenticación, persistencia en MongoDB, enrutamiento en la API y renderizado de la web.

## Reproducción y límites

Con la demo levantada, ejecuta desde la raíz:

```powershell
docker compose exec -T ai python -m ai_service.train --evaluate-test --output-dir /tmp/evaluacion-final
```

El comando escribe un informe JSON con las métricas por clase, la matriz, los parámetros y la procedencia del artefacto. La evaluación abarca 24 correos sintéticos y balanceados. El 100 % de acierto automático corresponde a los 20 correos asignados en esa muestra.
