# Modelo conceptual de datos — MongoDB
**Estado:** modelo conceptual con inicialización física compatible y auditoría de mensajes integrada; los datos legados se conservan sin migración.

| Candidato | Atributos principales | Relación e integridad |
|---|---|---|
| Usuario | id, username, role, active, passwordHash, activationCredentialHash, timestamps | Rol solo OPERADOR/ADMINISTRADOR; hashes, nunca secretos planos. |
| Mensaje | id, subject, body, sender opcional demo, estado, departamentoEfectivo, creador, timestamps | Referencia a usuario; estado y departamento validados contra RN-01/RN-02. |
| Predicción original IA embebida | category, confidence, modelVersion, preprocessingVersion, source=`IA`, timestamp | Opcional: solo existe si hubo respuesta IA válida. Es inmutable frente a correcciones humanas y nunca representa una asignación manual. |
| Asignación efectiva embebida | department, source (`IA` o `MANUAL`), reason, timestamp | Representa el destino vigente. Si `source=MANUAL`, el motivo es obligatorio; no sobrescribe la predicción original. |
| Evento de auditoría | id, messageId opcional, actorType (`SISTEMA` o `USUARIO`), actorUserId opcional, action, before, after, reason, timestamp | `actorUserId` referencia al usuario solo en actos humanos; los actos automáticos usan `SISTEMA`. Historial de solo adición, sin secretos. |
| Metadato de modelo | modelVersion, algoritmo, datasetVersion, métricas futuras, createdAt | Referenciado por versión de predicción; no inventa métricas. |

**Embed/referencia:** la predicción original y la asignación efectiva se embeben porque pertenecen a un mensaje y se consultan con él. Los eventos y usuarios se referencian para evitar arreglos sin límite y duplicación. Toda intervención humana conserva `before`, `after`, motivo y timestamp en auditoría.
**Índices candidatos:** `usuarios.username` único; mensajes por `estado`, `departamentoEfectivo`, `createdAt`; auditoría por `messageId, timestamp` y `actorUserId, timestamp`; modelo por `modelVersion` único. Son recomendaciones conceptuales que deberán validarse con consultas reales.

## Correspondencia física inicial

- `users` usa `_id` como identificador único actual; no se duplica con un índice `username`. La validación permite los hashes de activación y timestamps futuros sin exigirlos a las cuentas ya creadas.
- `sessions` conserva el índice TTL `expiresAt_1`.
- `messages` mantiene los nombres físicos actuales (`status`, `department`, `createdAt`) y añade índices para la bandeja general y futuros filtros por estado o departamento ordenados por fecha.
- `audit_events` recibe creación, predicción/enrutamiento, correcciones, gestión y cierre con `createdAt` como timestamp físico, `messageId` textual, actor, motivo y snapshots antes/después del estado operativo (sin contenido del correo). La consulta une eventos nuevos y embebidos legados; los legados tienen identidad estable y `before/after=null`, sin reconstrucción ficticia.
- `model_metadata` representa `Metadato de modelo` y exige `modelVersion` único, sin afirmar ni insertar métricas.
- Las validaciones usan nivel `moderate`, acción `error` y campos adicionales permitidos. La inicialización no reescribe documentos y puede ejecutarse repetidamente.
- En MongoDB standalone, la actualización del mensaje y su intención de auditoría se guardan atómicamente en `pendingAudit`. La publicación usa `insert_one` con `_id` estable y confirmación posterior: un reintento no modifica ni duplica el evento. Los pendientes se recuperan al arrancar, antes de otra mutación del mensaje o al consultar auditoría; un error de publicación responde 503, pero la intención queda persistida. `revision` permite detectar cambios concurrentes y devolver 409 sin sobrescribir un `before` obsoleto. No se garantiza atomicidad entre dos colecciones mediante transacciones ni se requiere un replica set.
- `pendingAudit` es una cola transitoria, no el historial: antes de acumular nuevas mutaciones se intenta vaciarla; un fallo impide continuar agregando cambios. Se indexan únicamente los mensajes con entregas pendientes.
- La API no ofrece edición/eliminación de eventos y su código solo inserta en `audit_events`. La protección contra modificaciones por administradores directos de MongoDB requiere permisos de base de datos, pendiente del bloque de seguridad; un validador JSON Schema por sí solo no garantiza inmutabilidad.
