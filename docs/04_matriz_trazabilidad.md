# Matriz de trazabilidad

**Estado:** especificación de trazabilidad; componentes, endpoints, pantallas y pruebas son previstos, no implementados ni ejecutados.

## Leyenda

- **UI-01** inicio de sesión; **UI-02** bandeja; **UI-03** registro; **UI-04** detalle y clasificación; **UI-05** gestión/corrección; **UI-06** auditoría/administración. Los SVG editables se encuentran en `docs/prototipos/`; siguen siendo prototipos, no frontend implementado.
- Componentes propuestos: `Auth`, `Usuarios`, `Mensajes`, `Clasificacion`, `Enrutamiento`, `Auditoria`.
- CP = caso de prueba futuro. Los endpoints corresponden a contratos de `02_srs.md`.

| Objetivo | Requisito / regla | Épica / HU | UI | Componente técnico propuesto | Endpoint/contrato | Caso de prueba previsto |
|---|---|---|---|---|---|---|
| OBJ-07 | RF-01, RNF-01, RNF-02 | EPI-001 / HU-01 | UI-01 | Auth | `POST /api/v1/auth/login`; `POST /api/v1/auth/activate` | CP-08 |
| OBJ-07 | RF-02, RN-06, RNF-02, RNF-10 | EPI-001 / HU-02 | UI-06 | Usuarios, Auth, Auditoria | `POST /api/v1/users`; `POST /api/v1/auth/activate` | CP-08 |
| OBJ-02 | RF-03, RNF-08, RNF-09 | EPI-002 / HU-03 | UI-03 | Mensajes, Auditoria | `POST /api/v1/messages` | CP-01, CP-02 |
| OBJ-03 | RF-04, RNF-05, RNF-11 | EPI-003 / HU-06 | UI-04 | Clasificacion | contrato interno IA | CP-03 |
| OBJ-03 | RF-05, RN-01, RNF-10 | EPI-003 / HU-07 | UI-04 | Clasificacion | contrato interno IA | CP-03 |
| OBJ-04 | RF-06, RN-03, RN-04, RNF-04 | EPI-003 / HU-08 | UI-04, UI-05 | Enrutamiento, Auditoria | `POST /api/v1/messages` | CP-04 |
| OBJ-04 | RF-07, RN-05, RNF-04, RNF-12 | EPI-003 / HU-09 | UI-03, UI-04 | Clasificacion, Mensajes | `POST /api/v1/messages`; `PATCH /api/v1/messages/{id}/classification` | CP-10 |
| OBJ-05 | RF-08, RNF-03, RNF-06 | EPI-002 / HU-04 | UI-02 | Mensajes | `GET /api/v1/messages` | CP-05 |
| OBJ-05 | RF-09, RNF-07 | EPI-002 / HU-05 | UI-04 | Mensajes | `GET /api/v1/messages/{id}` | CP-05 |
| OBJ-05 | RF-10, RN-02, RNF-08, RNF-10 | EPI-004 / HU-10 | UI-05 | Mensajes, Auditoria | `PATCH /api/v1/messages/{id}/status` | CP-06 |
| OBJ-05 | RF-11, RN-06, RN-07, RNF-10 | EPI-004 / HU-11 | UI-05 | Enrutamiento, Auditoria | `PATCH /api/v1/messages/{id}/classification` | CP-06, CP-10 |
| OBJ-05 | RF-13, RN-02 | EPI-004 / HU-12 | UI-05 | Mensajes, Auditoria | `PATCH /api/v1/messages/{id}/status` | CP-06 |
| OBJ-06 | RF-12, RN-08, RNF-10 | EPI-005 / HU-13 | UI-06 | Auditoria | `GET /api/v1/audit-events` | CP-07 |
| OBJ-08 | RNF-05, RNF-11 | EPI-005 / HU-14 | — | Clasificacion | contrato IA/documentación | CP-09 |
| OBJ-01 | RNF-03, RNF-12 | EPI-005 / HU-14 | UI-02–UI-05 | API, Clasificacion | todos los anteriores | CP-01–CP-10 |

## Casos de prueba previstos

| ID | Tipo | Escenario y resultado esperado |
|---|---|---|
| CP-01 | API/aceptación | Registrar un mensaje válido devuelve 201, id y evento de creación; el mensaje se persiste en `RECIBIDO` antes del intento de IA. |
| CP-02 | API negativa | Registro con asunto/cuerpo inválido devuelve 422 y no persiste mensaje. |
| CP-03 | Integración/contrato IA | Una respuesta IA válida contiene categoría permitida, confianza [0,1] y versión; se conservan junto al mensaje. |
| CP-04 | Regla de negocio | Confianza <0,70 deja `PENDIENTE_REVISION`; confianza ≥0,70 asigna departamento. |
| CP-05 | API/aceptación | Bandeja filtra y pagina; detalle existente muestra campos previstos y uno inexistente devuelve 404. |
| CP-06 | API/reglas | Cambio válido, corrección con motivo y asignación manual con predicción ausente generan eventos; transición inválida devuelve 409 sin cambio. |
| CP-07 | Integración/seguridad | Auditoría lista creación, clasificación y corrección; solo administrador puede acceder a la global. |
| CP-08 | Seguridad | Sin sesión devuelve 401; rol insuficiente devuelve 403; administrador crea solo roles permitidos, la credencial temporal se muestra una vez y se activa sin persistir secretos en auditoría. |
| CP-09 | IA/reproducibilidad | Pipeline ejecutado posteriormente conserva particiones, baseline, modelo, versión y métricas (Macro-F1 y precisión de enrutamiento) sin fuga de test. |
| CP-10 | Resiliencia | IA no disponible o respuesta inválida no pierde el mensaje ni asigna categoría inventada; queda pendiente de clasificación y el operador puede asignar un departamento manual con motivo. |

## Cobertura y criterios de consistencia

Los RF-01 a RF-13 y RNF-01 a RNF-12 aparecen al menos una vez en la matriz o en un caso que los verifica. RF-13 es `Should`; los demás RF son `Must`. Las referencias UI apuntan a prototipos editables de la fase 1C; no son frontend implementado.

La fuente tabular procesable equivalente es `docs/04_matriz_trazabilidad.csv`.
