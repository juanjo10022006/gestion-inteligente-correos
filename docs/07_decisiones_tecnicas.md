# Decisiones técnicas propuestas
| ADR | Decisión y justificación | Estado |
|---|---|---|
| ADR-01 | Usar MongoDB/PyMongo frente a PostgreSQL: el MVP maneja mensajes y eventos JSON de forma natural, conserva predicciones con metadatos variables y simplifica integración Python. PostgreSQL sigue siendo alternativa válida si relaciones y consultas relacionales crecen; MongoDB no es exigencia del PDF. | Propuesta pendiente de validación |
| ADR-02 | Separar API y servicio IA por contrato interno `{text,preprocessingVersion} → {category,confidence,modelVersion}`. Facilita reemplazo, pruebas y versionado sin exponer endpoint IA público. | Propuesta |
| ADR-03 | Persistir `RECIBIDO` y evento antes de inferir. Evita pérdida del mensaje cuando IA falla y permite trazabilidad completa. | Propuesta |
| ADR-04 | Ante baja confianza usar `PENDIENTE_REVISION`; ante fallo IA usar `PENDIENTE_CLASIFICACION`. Estas dos rutas admiten asignación humana motivada; H-01=0,70 no está validada. | Propuesta |
| ADR-05 | Credenciales temporales de un uso, activación y hash con sal; nunca secretos en auditoría. | Propuesta |
| ADR-06 | Inicializar MongoDB de forma idempotente desde la API y `backend.scripts.init_db`. Las colecciones existentes reciben validación `moderate` con acción `error`, sin revisar ni reescribir documentos históricos; los campos adicionales permanecen permitidos para compatibilidad. `audit_events` se prepara como colección independiente, pero la migración de eventos embebidos queda fuera de esta decisión. | Implementada para infraestructura; integración de auditoría pendiente |
