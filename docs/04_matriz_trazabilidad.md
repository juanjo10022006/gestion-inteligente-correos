# Matriz de trazabilidad

**Estado:** correspondencia del MVP `3f9a067`, con resultados técnicos previos y aceptación integral pendiente. Fuente de resultados/limitaciones: [plan de pruebas](PLAN_Y_RESULTADOS_PRUEBAS.md). No se reejecutaron las suites en el cierre documental.

## Leyenda

- **UI-01** inicio de sesión; **UI-02** bandeja; **UI-03** registro; **UI-04** detalle y clasificación; **UI-05** gestión/corrección; **UI-06** auditoría/administración. Los SVG editables en `docs/prototipos/` son la referencia de diseño del frontend React.
- Componentes implementados: `Auth`, `Usuarios`, `Mensajes`, `Clasificacion`, `Enrutamiento`, `Auditoria`.
- CP = caso de prueba. Los endpoints corresponden a contratos de `02_srs.md`.

| Objetivo | Requisito / regla | Épica / HU | UI de referencia | Componente técnico | Endpoint/contrato | Caso de prueba |
|---|---|---|---|---|---|---|
| OBJ-07 | RF-01, RNF-01, RNF-02 | EPI-001 / HU-01 | UI-01 | Auth | `POST /api/v1/auth/login`; `POST /api/v1/auth/activate` | CP-08 |
| OBJ-07 | RF-02, RN-06, RNF-02, RNF-10 | EPI-001 / HU-02 | UI-06 | Usuarios, Auth, Auditoria | `POST /api/v1/users`; `POST /api/v1/auth/activate`; `GET /api/v1/users`; `PATCH /api/v1/users/{username}`; `POST /api/v1/users/{username}/activation-credential` | CP-08 |
| OBJ-02 | RF-03, RNF-08, RNF-09 | EPI-002 / HU-03 | UI-03 | Mensajes, Auditoria | `POST /api/v1/messages` | CP-01, CP-02 |
| OBJ-03 | RF-04, RNF-05, RNF-11 | EPI-003 / HU-06 | UI-04 | Clasificacion | contrato interno IA | CP-03 |
| OBJ-03 | RF-05, RN-01, RNF-10 | EPI-003 / HU-07 | UI-04 | Clasificacion | contrato interno IA | CP-03 |
| OBJ-04 | RF-06, RN-03, RN-04, RNF-04 | EPI-003 / HU-08 | UI-04, UI-05 | Enrutamiento, Auditoria | `POST /api/v1/messages` | CP-04 |
| OBJ-04 | RF-07, RN-05, RNF-04, RNF-12 | EPI-003 / HU-09 | UI-03, UI-04 | Clasificacion, Mensajes | `POST /api/v1/messages`; `PATCH /api/v1/messages/{message_id}/classification` | CP-10 |
| OBJ-05 | RF-08, RNF-03, RNF-06 | EPI-002 / HU-04 | UI-02 | Mensajes | `GET /api/v1/messages` | CP-05 |
| OBJ-05 | RF-09, RNF-07 | EPI-002 / HU-05 | UI-04 | Mensajes | `GET /api/v1/messages/{message_id}` | CP-05 |
| OBJ-05 | RF-10, RN-02, RNF-08, RNF-10 | EPI-004 / HU-10 | UI-05 | Mensajes, Auditoria | `PATCH /api/v1/messages/{message_id}/status` | CP-06 |
| OBJ-05 | RF-11, RN-06, RN-07, RNF-10 | EPI-004 / HU-11 | UI-05 | Enrutamiento, Auditoria | `PATCH /api/v1/messages/{message_id}/classification` | CP-06, CP-10 |
| OBJ-05 | RF-13, RN-02 | EPI-004 / HU-12 | UI-05 | Mensajes, Auditoria | `PATCH /api/v1/messages/{message_id}/status` | CP-06 |
| OBJ-06 | RF-12, RN-08, RNF-10 | EPI-005 / HU-13 | UI-06 | Auditoria | `GET /api/v1/audit-events` | CP-07 |
| OBJ-08 | RNF-05, RNF-11 | EPI-005 / HU-14 | — | Clasificacion | contrato IA/documentación | CP-09 |
| OBJ-01 | RNF-03, RNF-12 | EPI-005 / HU-14 | UI-02–UI-05 | API, Clasificacion | todos los anteriores | CP-01–CP-10 |

## Casos de prueba y resultados

| ID | Resultado | Evidencia y alcance |
|---|---|---|
| CP-01 | Ejecutada con evidencia previa | `compose_acceptance.py`, `history_acceptance.py`, `final_acceptance.py`: registro 201; observación de `RECIBIDO` y evento antes de IA. E-TECH del plan. |
| CP-02 | Pasó | Asunto inválido devuelve 422 y la colección permanece vacía. |
| CP-03 | Ejecutada; variante parcial | Predicción con categoría, confianza, modelo y preparación. RF-04 sigue parcial si no hay predicción: falta registro separado de preparación. |
| CP-04 | Ejecutada a umbral provisional | Auto/revisión a 0,45; no acredita literalmente H-01=0,70 ni umbral óptimo. |
| CP-05 | Ejecutada; UI pendiente | Texto, estado, departamento y fechas combinados, paginación y 404 en `history_acceptance.py`; no acredita accesibilidad/usabilidad. |
| CP-06 | Pasó | Asignación con motivo conserva la predicción. Un correo clasificado pasa a gestión y luego se cierra con una resolución auditable. Cerrar un correo pendiente o repetir el cierre devuelve 409. Una resolución ausente o en blanco devuelve 422. |
| CP-07 | Ejecutada; UI/privilegios pendientes | Actor/acción/fechas, legados, snapshots, recuperación y 401/403 probados; vista autenticada y permisos MongoDB restrictivos no acreditados. |
| CP-08 | Ejecutada; seguridad no local pendiente | `access_acceptance.py`: alta, activación, renovación, expiración, doble uso, carreras, revocación, roles, auditoría fallida y confidencialidad. |
| CP-09 | Ejecutada con evidencia curada | [Evaluación](09_evaluacion_final_ia.md), [reporte](evidencias/ia/evaluacion_artefacto.json), notebooks y manifiesto; test separado ya observado, no nueva prueba ciega. |
| CP-10 | Ejecutada con evidencia previa | `final_acceptance.py`: JSON/categoría/confianza/versión inválidos y timeout; también servicio inalcanzable y asignación manual. |

## Reproducción y límites de la evidencia

La tabla de rendimiento vigente con corrida, versión y alcance está en el [plan](PLAN_Y_RESULTADOS_PRUEBAS.md#rendimiento-una-corrida-histórica-no-una-medición-nueva). No se atribuyen cifras de otro modelo al artefacto actual ni se repiten aquí números sin contexto.

Desde la raíz, exclusivamente mediante los lanzadores aislados:

```powershell
docker build --target ai -t gestion-correos-ai-final:local .
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_history_checks.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_compose_smoke.ps1
```

MongoDB usa `tmpfs`, proyectos/redes propios y bases UUID. No ejecutar estos scripts apuntándolos manualmente a la base demo. Los resultados técnicos anteriores no incluyen la prueba integral de navegador.

## Cobertura y criterios de consistencia

Los RF-01 a RF-13 y RNF-01 a RNF-12 aparecen en la matriz/plan; **cobertura de referencia no implica cumplimiento demostrado**. RF-13 es `Should`; los demás RF son `Must`. Las referencias UI siguen apuntando a prototipos editables, no a capturas del React ya implementado.

HU-01/02 tienen API probada y UI pendiente; HU-03…05 y HU-07…13, ejecución técnica previa con aceptación visual pendiente. HU-06 tiene la variante RF-04 parcial; HU-08 conserva la diferencia H-01; HU-14 es parcial hasta completar pruebas unitarias y aceptación integral. RNF-01/06/07 y privilegios de RN-08 no se declaran cerrados. El detalle está en el plan, incluidos casos definidos pendientes y no aplicables justificados.

La fuente tabular procesable equivalente es [04_matriz_trazabilidad.csv](04_matriz_trazabilidad.csv). Conserva las relaciones originales y añade estado, evidencia y limitaciones para cada fila; no modifica IDs.
