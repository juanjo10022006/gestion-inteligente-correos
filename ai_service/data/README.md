# Dataset sintético de correos v0.3

128 correos ficticios en español, redactados para este proyecto con asistencia de IA. La versión 0.3 conserva los 80 registros de v0.2 con sus particiones originales y agrega 48. Incluye asuntos breves, cuerpos genéricos y solicitudes con vocabulario de varias áreas, como una falla técnica del portal de facturación o una factura de una capacitación de empleados. No se emplearon fuentes externas ni mensajes reales.

Cada línea de [correos_sinteticos_v0.3.jsonl](correos_sinteticos_v0.3.jsonl) contiene un objeto UTF‑8 con `id`, `subject`, `body`, `label` y `split`. El modelo recibe solo asunto y cuerpo. La etiqueta indica el área que debe atender la solicitud principal.

| Etiqueta | Entrenamiento | Validación | Prueba |
|---|---:|---:|---:|
| SOPORTE_TECNICO | 20 | 6 | 6 |
| FACTURACION | 20 | 6 | 6 |
| VENTAS | 20 | 6 | 6 |
| RECURSOS_HUMANOS | 20 | 6 | 6 |

Entrena con `train`, ajusta el modelo y el umbral con `validation`, y reserva `test` para la evaluación final. Al ampliar el corpus, mantén correos del mismo hilo y variantes de una misma plantilla dentro de una sola partición.

La muestra es pequeña, balanceada por diseño y contiene principalmente solicitudes claras. Sirve para comprobar el pipeline. Para estimar desempeño, amplíen la muestra con redacciones variadas, errores, solicitudes ambiguas y correos que mezclen áreas. Revisen duplicados, documenten el origen y los permisos de cualquier fuente adicional y conserven la versión de los datos usada en cada experimento.
