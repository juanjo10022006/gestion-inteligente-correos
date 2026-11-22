# Modelo conceptual de datos — MongoDB
**Estado:** modelo conceptual con inicialización física compatible en `backend/scripts/init_db.py`; la integración de auditoría externa sigue pendiente.

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
- `audit_events` queda creada y validada para eventos futuros con `createdAt` como timestamp físico. Sus índices soportan consulta global y filtros por mensaje, actor y acción. El script no copia ni elimina los eventos embebidos existentes.
- `model_metadata` representa `Metadato de modelo` y exige `modelVersion` único, sin afirmar ni insertar métricas.
- Las validaciones usan nivel `moderate`, acción `error` y campos adicionales permitidos. La inicialización no reescribe documentos y puede ejecutarse repetidamente.
