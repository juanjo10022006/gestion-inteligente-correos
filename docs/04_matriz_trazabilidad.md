# Matriz de trazabilidad

**Estado:** matriz de requisitos y contratos con resultados de las pruebas ejecutadas en Docker. Las partes pendientes se indican en la tabla de resultados.

## Leyenda

- **UI-01** inicio de sesión; **UI-02** bandeja; **UI-03** registro; **UI-04** detalle y clasificación; **UI-05** gestión/corrección; **UI-06** auditoría/administración. Los SVG editables en `docs/prototipos/` son la referencia de diseño del frontend React.
- Componentes propuestos: `Auth`, `Usuarios`, `Mensajes`, `Clasificacion`, `Enrutamiento`, `Auditoria`.
- CP = caso de prueba. Los endpoints corresponden a contratos de `02_srs.md`.

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

## Casos de prueba y resultados

| ID | Resultado | Evidencia y alcance |
|---|---|---|
| CP-01 | Parcial en suite | Registro válido 201, ID y evento con actor. El orden persistencia → IA se verificó anteriormente durante la integración; la suite actual no inspecciona el estado intermedio. |
| CP-02 | Pasó | Asunto inválido devuelve 422 y la colección permanece vacía. |
| CP-03 | Pasó | La predicción real contiene categoría, confianza y versión, y se recupera en el detalle. |
| CP-04 | Pasó | Con el umbral de demo 0,45, un correo de factura se enruta y otro ambiguo pasa a revisión. |
| CP-05 | Parcial | Búsqueda por texto, paginación y detalle verificados; ID inexistente devuelve 404. Los filtros por departamento, estado y fecha siguen pendientes. |
| CP-06 | Pasó | Asignación con motivo conserva la predicción. Un correo clasificado pasa a gestión y luego se cierra con una resolución auditable. Cerrar un correo pendiente o repetir el cierre devuelve 409. Una resolución ausente o en blanco devuelve 422. |
| CP-07 | Parcial | El administrador obtiene los eventos de un correo con actor y motivo; el operador recibe 403. Falta probar la consulta por actor, acción y fechas, y validar la vista React con una sesión administrativa real. |
| CP-08 | Parcial | Credenciales incorrectas y acceso sin sesión devuelven 401. El operador recibe 403 en auditoría. Creación desde la API y activación con credencial temporal siguen pendientes. |
| CP-09 | Pasó | [Evaluación final independiente](09_evaluacion_final_ia.md) con versión, modelo base, Macro-F1 y precisión de enrutamiento. |
| CP-10 | Parcial | Un servicio inalcanzable deja el correo persistido en `PENDIENTE_CLASIFICACION` y permite asignación manual. Falta convertir la respuesta malformada y el timeout en casos separados de la suite. |

## Medición de rendimiento de la API

| Operación | Solicitudes | Mediana | p95 | Objetivo p95 del SRS |
|---|---:|---:|---:|---:|
| Registrar y clasificar | 30 | 4,98 ms | 5,72 ms | ≤ 5 s |
| Consultar bandeja | 30 | 2,90 ms | 3,45 ms | ≤ 2 s |

Se midieron peticiones HTTP secuenciales desde el contenedor de la API, con sesión válida, MongoDB e IA reales. La medición de registro incluye validación, escritura, inferencia y enrutamiento. Excluye navegador, Nginx y carga concurrente. El resultado corresponde a esta demo y su base temporal.

Para repetir la suite con Docker Compose levantado, desde la raíz en PowerShell:

```powershell
Get-Content tests/compose_acceptance.py -Raw -Encoding utf8 | docker compose exec -T api python -
```

La suite crea su propia base, arranca una API temporal y retira sus datos al terminar. La demo y sus cuentas permanecen disponibles durante la ejecución.

## Cobertura y criterios de consistencia

Los RF-01 a RF-13 y RNF-01 a RNF-12 aparecen al menos una vez en la matriz o en un caso que los verifica. RF-13 es `Should`; los demás RF son `Must`. Las referencias UI apuntan a prototipos editables de la fase 1C; no son frontend implementado.

La fuente tabular procesable equivalente es `docs/04_matriz_trazabilidad.csv`.
