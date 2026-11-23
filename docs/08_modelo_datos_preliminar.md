# Modelo conceptual de datos — MongoDB
**Estado:** modelo conceptual conservado y correspondencia física con `3f9a067`. Inicialización idempotente y auditoría de mensajes/cuentas/sesiones integradas; legados sin migración. La nomenclatura conceptual no implica que todos los candidatos sean colecciones pobladas.

| Candidato | Atributos principales | Relación e integridad |
|---|---|---|
| Usuario | id, username, role, active, passwordHash, activationCredentialHash, timestamps | Rol solo OPERADOR/ADMINISTRADOR; hashes, nunca secretos planos. |
| Sesión | digest de token como id, userId, authVersion, validUntil, expiresAt, revokedAt, pendingAudit | Autorización por vigencia/versionado/revocación; TTL solo limpieza tras publicar auditoría. |
| Mensaje | id, subject, body, sender opcional demo, estado, departamentoEfectivo, creador, timestamps | Referencia a usuario; estado y departamento validados contra RN-01/RN-02. |
| Predicción original IA embebida | category, confidence, modelVersion, preprocessingVersion, source=`IA`, timestamp | Opcional: solo existe si hubo respuesta IA válida. Es inmutable frente a correcciones humanas y nunca representa una asignación manual. |
| Asignación efectiva embebida | department, source (`IA` o `MANUAL`), reason, timestamp | Representa el destino vigente. Si `source=MANUAL`, el motivo es obligatorio; no sobrescribe la predicción original. |
| Evento de auditoría | id, messageId opcional, actorType (`SISTEMA` o `USUARIO`), actorUserId opcional, action, before, after, reason, timestamp | `actorUserId` referencia al usuario solo en actos humanos; los actos automáticos usan `SISTEMA`. Historial de solo adición, sin secretos. |
| Metadato de modelo | modelVersion, algoritmo, datasetVersion, métricas, createdAt | Colección preparada pero no poblada automáticamente; las métricas verificadas están en el reporte externo y bundle. |

**Embed/referencia:** la predicción original y la asignación efectiva se embeben porque pertenecen a un mensaje y se consultan con él. Los eventos y usuarios se referencian para evitar arreglos sin límite y duplicación. Toda intervención humana conserva `before`, `after`, motivo y timestamp en auditoría.
**Índices candidatos:** `usuarios.username` único; mensajes por `estado`, `departamentoEfectivo`, `createdAt`; auditoría por `messageId, timestamp` y `actorUserId, timestamp`; modelo por `modelVersion` único. Son recomendaciones conceptuales que deberán validarse con consultas reales.

## Correspondencia física inicial

- `users` usa `_id` como identificador único actual; no se duplica con un índice `username`. La validación permite los hashes de activación y timestamps futuros sin exigirlos a las cuentas ya creadas.
- `users`: `activated`, `activationExpiresAt`, `authVersion`, `revision` y `pendingAudit` completan el flujo de alta/renovación/activación. Consumir activación elimina hash/vencimiento temporal; cuenta CLI sin `activated` se interpreta compatible como activada.
- `sessions` conserva TTL `expiresAt_1`; `validUntil` autoriza aun si auditoría pendiente impide programar TTL. `revokedAt` y versión de autorización bloquean sesiones sin esperar limpieza.
- `messages` mantiene los nombres físicos actuales (`status`, `department`, `createdAt`) y añade índices para la bandeja general y futuros filtros por estado o departamento ordenados por fecha.
- `audit_events` recibe creación, predicción/enrutamiento, correcciones, gestión y cierre con `createdAt` como timestamp físico, `messageId` textual, actor, motivo y snapshots antes/después del estado operativo (sin contenido del correo). La consulta une eventos nuevos y embebidos legados; los legados tienen identidad estable y `before/after=null`, sin reconstrucción ficticia.
- `model_metadata` representa `Metadato de modelo` y exige `modelVersion` único, sin afirmar ni insertar métricas.
- Las validaciones usan nivel `moderate`, acción `error` y campos adicionales permitidos. La inicialización no reescribe documentos y puede ejecutarse repetidamente.
- En MongoDB standalone, la actualización del mensaje y su intención de auditoría se guardan atómicamente en `pendingAudit`. La publicación usa `insert_one` con `_id` estable y confirmación posterior: un reintento no modifica ni duplica el evento. Los pendientes se recuperan al arrancar, antes de otra mutación del mensaje o al consultar auditoría; un error de publicación responde 503, pero la intención queda persistida. `revision` permite detectar cambios concurrentes y devolver 409 sin sobrescribir un `before` obsoleto. No se garantiza atomicidad entre dos colecciones mediante transacciones ni se requiere un replica set.
- `pendingAudit` es intención transitoria, no historial. En mensajes se intenta publicar antes de otra mutación; un fallo bloquea ese flujo. Cuentas/sesiones permiten confirmar cambios ya persistidos pese a fallas de publicación, conservando sus intenciones para reintento. Puede crecer durante una indisponibilidad sostenida: no se promete tamaño acotado ni supervisión operacional implementada. Hay índices parciales de pendientes en `messages`, `users` y `sessions`.
- La API no ofrece edición/eliminación de eventos y su código solo inserta en `audit_events`. La protección contra modificaciones por administradores directos de MongoDB requiere permisos de base de datos, pendiente del bloque de seguridad; un validador JSON Schema por sí solo no garantiza inmutabilidad.

`audit_events` también recibe altas, activación, renovación, cambios de cuenta y login/logout con `messageId=null`, sin hashes de acceso ni secretos. `messages.prediction` conserva `{category,confidence,modelVersion,preprocessingVersion,source,timestamp}` y puede ser nulo; el destino efectivo usa `department`, `assignmentOrigin` y `assignment`. El original, resolución y timestamps permanecen en el mensaje. No hay colección nueva de correcciones: el historial completo está en eventos.

Los índices efectivos, no solo candidatos, están declarados en [backend/db.py](../backend/db.py): orden de creación/ID, estado/fecha, departamento/fecha; auditoría por fecha, mensaje, actor y acción; pendientes parciales; TTL de sesión y versión única de `model_metadata`. MongoDB no impone claves foráneas entre estas colecciones. Las pruebas y limitaciones están en el [plan](PLAN_Y_RESULTADOS_PRUEBAS.md).
