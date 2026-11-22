# Modelo conceptual de datos — MongoDB
**Estado:** conceptual; no define colecciones físicas, validadores ni scripts.

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
