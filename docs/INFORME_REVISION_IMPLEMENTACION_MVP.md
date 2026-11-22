# Informe de revisión técnica de `implementacion-mvp`

**Proyecto:** Sistema inteligente de clasificación de correos corporativos

**Equipo:** Juan Camilo Gonzales y Juan Jose Solarte

**Implementación auditada:** `0641fd50e1000af02c60ddb30efd6544d23c871d`

**Línea base documental:** `3157679ca40d73d4f730dc937287a9ba9f351af4` (`main`)

**Merge-base:** `3157679ca40d73d4f730dc937287a9ba9f351af4`

## 1. Dictamen ejecutivo

**Dictamen: implementación funcional parcial; no está lista para fusionarse con `main`.**

La rama contiene un MVP ejecutable de cuatro servicios y conserva una parte sustancial del trabajo aprobado: React/Nginx, FastAPI, MongoDB, un servicio interno de IA, dataset sintético, entrenamiento reproducible en el entorno actual y una suite de aceptación aislada. Durante esta auditoría se comprobaron realmente los cuatro contenedores saludables, siete rutas públicas, el flujo principal, la tolerancia a IA inalcanzable, la evaluación del clasificador y la construcción del frontend en Docker.

No se recomienda fusionar todavía por dos incumplimientos Must:

1. **RF-01/RF-02:** no existen activación, credencial temporal, administración de usuarios por API ni su interfaz; `backend/create_user.py` crea cuentas ya activas por consola y no sustituye esos contratos.
2. **RF-11/RF-12/RNF-10/RN-08:** los eventos embebidos no forman un historial de solo adición. Una nueva acción del mismo tipo sobrescribiría la anterior, faltan `before/after`, y no se permite corregir el departamento desde `EN_GESTION`.

También faltan los filtros Must de bandeja y auditoría, metadatos previstos del modelo de datos, inicialización MongoDB, notebooks académicos y cobertura de pruebas suficiente. El umbral `0,45` tiene evidencia experimental limitada, pero no una decisión aprobada: en validación, `0,40` obtuvo más cobertura con la misma precisión automática observada.

Este dictamen **no invalida ni propone eliminar** el aporte de Juan Camilo Gonzales. La recomendación es conservar la rama abierta y corregirla incrementalmente.

## 2. Alcance, método y estado de Git

- La rama local `implementacion-mvp`, `origin/implementacion-mvp` y `HEAD` coinciden en `0641fd5`.
- `main` y `origin/main` coinciden en `3157679`.
- La implementación es un único commit sobre la línea base documental; no hay commits divergentes intermedios.
- El árbol estaba limpio al iniciar.
- Se compararon SRS, HU, matriz MD/CSV, arc42, ADR, modelo conceptual, auditoría 1D y D-05 a D-09 contra código, OpenAPI y ejecución.
- Se inspeccionaron frontend, backend, IA, tres versiones del dataset, Dockerfiles, Compose, MongoDB y pruebas.
- La suite usó una base `compose_acceptance_<UUID>` y la eliminó; se comprobó que no quedaron bases con ese prefijo.
- No se leyeron documentos de usuarios, contraseñas ni mensajes de la base de demo. Solo se consultaron nombres de colecciones e índices.
- No se iniciaron, detuvieron ni recrearon los servicios existentes; no se modificó el volumen `mongo_data`.
- No se ejecutaron scripts de DriveGuardLab.

La diferencia `main...implementacion-mvp` contiene 38 archivos y 3.384 inserciones aproximadas. Además de código y datos, modifica `README.md`, `docs/04_matriz_trazabilidad.md` y `docs/README_DOCUMENTACION.md`, y añade `docs/09_evaluacion_final_ia.md`.

## 3. Qué se observó y qué se ejecutó

### 3.1 Funciona según código y fue comprobado

- Los servicios existentes `web`, `api`, `ai` y `mongo` estaban saludables.
- Los SHA-256 de todos los `.py` del backend dentro del contenedor coinciden con la rama; también coinciden `main.py`, `train.py`, `contract.py`, `preprocessing.py` y el dataset v0.3 del contenedor IA.
- La API expone siete rutas públicas reales bajo `/api/v1/`.
- Login válido/inválido, token Bearer, expiración y autorización administrativa de auditoría.
- Registro 201 y validación 422; el código inserta `RECIBIDO` antes de invocar IA.
- Clasificación automática, baja confianza y caída del servicio IA.
- Consulta, búsqueda textual, paginación y detalle.
- Asignación manual desde estados pendientes o `CLASIFICADO`.
- Paso `CLASIFICADO → EN_GESTION → CERRADO` y conflictos 409.
- Consulta administrativa de los eventos embebidos disponibles.
- Frontend servido por Nginx; la pantalla de acceso cargó sin errores de consola.
- Construcción limpia del frontend con `node:22-alpine` y npm 10 dentro de Docker.
- Suite de aceptación incluida contra base aislada.
- Reentrenamiento y evaluación IA en el contenedor.

### 3.2 Existe en código, pero no quedó comprobado completamente

- La respuesta malformada, categoría inválida y timeout de IA convergen por código en `None`, pero la suite solo ejecuta un servicio inalcanzable.
- La persistencia previa a IA se confirma por el orden de `backend/main.py:57-75`; la suite no observa el estado intermedio.
- El manejo concurrente usa `find_one_and_update` condicionado por estado, pero no hay prueba de concurrencia.
- Los formularios autenticados contienen etiquetas y estados comprensibles, pero la revisión visual ejecutada cubrió solo la pantalla pública de acceso.

### 3.3 No está implementado

- `POST /api/v1/auth/activate`.
- `POST /api/v1/users` y administración de usuarios/roles desde React.
- Auditoría de login, activación y gestión de usuarios.
- Cierre de sesión con revocación del token en servidor.
- Filtros de bandeja por departamento, estado y fechas.
- Auditoría por actor, acción y fechas.
- Historial externo/inmutable con `before/after`.
- Corrección de departamento mientras el mensaje está `EN_GESTION`.
- Persistencia de `preprocessingVersion`, origen y timestamp de predicción, y asignación efectiva completa.
- Script idempotente `backend/scripts/init_db.py`, validadores e índices de mensajes/auditoría.
- Notebooks de entorno, EDA y entrenamiento/evaluación.
- Tailwind, aunque sigue siendo una decisión documental del equipo.
- Pruebas unitarias, frontend, contrato, concurrencia, carga y CI.

## 4. Inventario de implementación

### 4.1 Servicios y dependencias

| Servicio | Implementación | Dependencias y observación |
|---|---|---|
| `web` | React 19 + TypeScript + Vite; Nginx final (`frontend/Dockerfile:1-11`) | Nginx redirige `/api/`, `/docs` y `/openapi.json` a `api:8000` (`frontend/nginx.conf:5-16`). No usa Tailwind. |
| `api` | FastAPI/Pydantic/PyMongo (`Dockerfile:7-10`) | Usa `mongo:27017`, `ai:8001` y umbral Compose `0.45` (`compose.yaml:17-35`). |
| `ai` | FastAPI + pipeline TF-IDF/regresión logística (`Dockerfile:12-19`) | Entrena en cada build y sirve `/model/model.joblib`; no copia `compare_thresholds.py`. |
| `mongo` | MongoDB 8.0 con volumen (`compose.yaml:47-60`) | Publica solo en loopback `127.0.0.1:27018`; esto es útil para desarrollo, pero difiere del D-08 “sin puerto público”. |

Compose usa DNS interno correcto, healthchecks y dependencias condicionadas a salud. No usa `localhost` entre contenedores. `api` e `ai` no publican puertos al host.

### 4.2 Endpoints reales

| Método y ruta | Autorización | Evidencia | Estado frente al SRS |
|---|---|---|---|
| `POST /api/v1/auth/login` | Público | `backend/auth.py:44-63` | Parcial: login sí; no activa ni audita acceso. |
| `POST /api/v1/messages` | Sesión activa | `backend/main.py:55-98` | Implementado con flujo resiliente. |
| `GET /api/v1/messages` | Sesión activa | `backend/main.py:101-134` | Parcial: texto y paginación solamente. |
| `GET /api/v1/messages/{message_id}` | Sesión activa | `backend/main.py:137-142` | Parcial: no incluye auditoría relacionada. |
| `PATCH /api/v1/messages/{message_id}/classification` | Sesión activa | `backend/main.py:145-174` | Parcial: no admite `EN_GESTION`, ni `before/after`. |
| `PATCH /api/v1/messages/{message_id}/status` | Sesión activa | `backend/main.py:177-212` | Implementa gestión y cierre. |
| `GET /api/v1/audit-events` | Administrador | `backend/main.py:215-239` | Parcial: `messageId` y `limit`; historial incompleto. |
| `POST /api/v1/auth/activate` | — | Ausente de OpenAPI | No implementado. |
| `POST /api/v1/users` | — | Ausente de OpenAPI | No implementado. |

El OpenAPI servido se leyó realmente desde `http://127.0.0.1:8080/openapi.json`.

### 4.3 Interfaces React

| Interfaz | Evidencia | Cobertura |
|---|---|---|
| Login | `frontend/src/main.tsx:34-65` | Usuario/contraseña y errores. No activación. |
| Bandeja | `frontend/src/main.tsx:211-337` | Lista, texto, paginación, registro y detalle. Sin filtros de área/estado/fecha. |
| Registro | `frontend/src/main.tsx:68-105` | Validación cliente coherente con longitudes principales. |
| Detalle | `frontend/src/main.tsx:176-208` | Original, estado, área, predicción, confianza, modelo y resolución. |
| Asignación | `frontend/src/main.tsx:107-142,202-207` | Solo estados pendientes y `CLASIFICADO`; excluye `EN_GESTION`. |
| Gestión/cierre | `frontend/src/main.tsx:144-173,202-204` | Inicio de gestión y cierre con resolución. |
| Auditoría | `frontend/src/AuditView.tsx:23-86` | Solo administrador, últimos 50 y filtro por mensaje. |
| Usuarios/activación | Sin componente ni ruta | No implementado. |

### 4.4 Colecciones MongoDB

| Colección | Uso real | Observación |
|---|---|---|
| `users` | Usuario por `_id`, rol, activo, sal y hash (`backend/create_user.py:24-32`) | Solo índice `_id`; sin timestamps ni credencial temporal. |
| `sessions` | Digest SHA-256 del token y expiración (`backend/auth.py:54-61`) | Índice TTL `expiresAt` creado al iniciar (`backend/main.py:33-36`). |
| `messages` | Mensaje, predicción, departamento y campos de evento (`backend/main.py:57-97`) | Colección perezosa; sin validador ni índices. No existía todavía en la base de demo inspeccionada. |
| `audit_events` | Ausente | El modelo conceptual la prevé como historial referenciado. |
| metadatos de modelo | Ausente | La versión solo queda dentro de cada predicción. |

Durante la consulta segura, la base de demo contenía únicamente `users` y `sessions`; no se leyeron documentos.

### 4.5 Scripts, datos y pruebas

| Artefacto | Propósito | Resultado de revisión |
|---|---|---|
| `backend/create_user.py` | Crear usuario activo por consola | Útil para demo, pero no satisface RF-02 ni activación. |
| `ai_service/train.py` | Validar datos, seleccionar `C`, evaluar y exportar | Usa solo `train` para ajuste y `validation` para seleccionar; `test` requiere bandera explícita. |
| `ai_service/compare_thresholds.py` | Sensibilidad en validación | Correcto en fuente; no está copiado a la imagen IA. |
| `ai_service/data/*.jsonl` | Dataset sintético v0.1-v0.3 | v0.3 contiene 128 registros; v0.1/v0.2 se preservan íntegros. |
| `tests/compose_acceptance.py` | Suite end-to-end con base única | Pasó en esta auditoría; es un script con `assert`, no una suite pytest/CI. |
| `docs/09_evaluacion_final_ia.md` | Resultado final informado | Métricas reproducidas, pero versión de modelo y latencias ya no coinciden exactamente. |

## 5. Matriz de requisitos funcionales

Estados: **cumple**, **parcial**, **no implementado** o **no comprobado**. RF-13 es Should; los demás son Must.

| ID | Esperado | Evidencia de implementación | Estado | Severidad | Prueba existente / acción mínima |
|---|---|---|---|---|---|
| RF-01 | Activar cuenta, iniciar sesión y auditar sesión | Login y sesión de una hora en `backend/auth.py:14-82`; no hay activación ni evento de acceso | Parcial | Bloqueante | La suite prueba login válido/inválido. Añadir activación de un uso y auditoría. |
| RF-02 | Administrador crea/actualiza cuenta y rol con credencial temporal | CLI crea directamente activa (`backend/create_user.py:11-35`); endpoint/UI ausentes | No implementado | Bloqueante | CP-08 no prueba creación/activación. Implementar contrato, autorización y UI. |
| RF-03 | Validar, persistir `RECIBIDO` y auditar antes de IA | Inserción `57-73`; IA en `75`; creación embebida `65-70` | Cumple | — | Suite 201/422; añadir prueba que observe el orden, no solo inspección estática. |
| RF-04 | Normalizar, conservar original y registrar versión | `prepare_text` normaliza (`ai_service/preprocessing.py:1-5`) y se envía versión (`backend/classifier.py:12-23`); no se persiste | Parcial | Alta | Persistir `preprocessingVersion` y probar original + versión. |
| RF-05 | Validar categoría, confianza y versión | Contrato Pydantic estricto (`ai_service/contract.py:8-16`) y predicción persistida (`backend/main.py:87-97`) | Cumple | — | CP-03 pasó; separar pruebas de cada respuesta inválida. |
| RF-06 | Aplicar H-01 y enrutar | Lógica correcta y configurable (`backend/main.py:23,29-32,77-97`), pero Compose usa `0.45` | Parcial | Alta / decisión | CP-04 usa 0,45. Aprobar ADR antes de reemplazar H-01=0,70. |
| RF-07 | Conservar mensaje ante fallo IA y permitir asignar | `classify` retorna `None` controlado (`backend/classifier.py:15-26`); queda pendiente (`backend/main.py:77-79`) | Cumple | — | CP-10 pasó con URL inalcanzable; añadir timeout y JSON/contrato inválido. |
| RF-08 | Texto, departamento, estado, fechas y paginación | Solo `page`, `pageSize`, `text` (`backend/main.py:101-134`) | Parcial | Alta | CP-05 solo texto/página. Añadir filtros combinables e índices. |
| RF-09 | Original, estado, asignación, predicción y auditoría relacionada | Detalle operativo en `backend/main.py:137-142`; esquema `backend/schemas.py:44-46`; auditoría no incluida | Parcial | Media | Detalle/404 probados. Añadir eventos autorizados o enlace contractual explícito. |
| RF-10 | Transiciones D-06 y evento inmutable | Cambios atómicos condicionados (`backend/main.py:177-212`); eventos embebidos no son historial de solo adición | Parcial | Alta | CP-06 cubre gestión/cierre. Añadir historial y concurrencia. |
| RF-11 | Asignar/corregir con motivo, incluso clasificación vigente, preservando predicción | Admite pendientes y `CLASIFICADO` (`backend/main.py:145-174`); no `EN_GESTION`; sin `before/after`; sobrescribe `manualEvent` | Parcial | Bloqueante | La prueba espera 409 en una segunda corrección, contrario a D-06. Corregir contrato y prueba. |
| RF-12 | Auditoría completa, inmutable y filtrable | Administrador, `messageId` y `limit` (`backend/main.py:215-239`); eventos fijos embebidos | Parcial | Bloqueante | CP-07 prueba tres eventos. Migrar a eventos append-only y añadir actor/acción/fecha. |
| RF-13 | Cerrar desde `EN_GESTION` con resolución | `backend/schemas.py:33-41`; `backend/main.py:184-212` | Cumple | — | Cierre, 409 y 422 pasaron. |

## 6. Matriz de requisitos no funcionales

| ID | Evidencia | Estado | Severidad | Acción o prueba mínima |
|---|---|---|---|---|
| RNF-01 Seguridad | Scrypt con sal (`backend/auth.py:32-33`), token aleatorio almacenado como digest (`54-61`), sin secretos de alto riesgo detectados; HTTP solo local | Parcial | Media | Definir TLS para ambiente no local y configuración de secretos. |
| RNF-02 Autorización | Todas las rutas operativas usan `current_user`; auditoría usa `administrator` (`backend/main.py:15,55-56,215-220`) | Parcial | Alta | Falta aplicar/probar autorización a usuarios y activación. |
| RNF-03 Rendimiento | Suite fresca: POST p95 19,83 ms; GET p95 9,54 ms, n=30 secuencial | Parcialmente comprobado | Media | Mantener evidencia, definir carga y añadir concurrencia; no confundir con inferencia aislada. |
| RNF-04 Fallos IA | Mensaje queda disponible y manualmente asignable | Cumple | — | CP-10 pasó; ampliar tipos de fallo. |
| RNF-05 Desacoplamiento | Contrato Pydantic compartido y servicio interno independiente | Parcial | Media | Añadir prueba de contrato y compatibilidad de versiones. |
| RNF-06 Accesibilidad | Etiquetas envolventes, foco y mensajes textuales; Lighthouse de login: 1,00 | Parcialmente comprobado | Baja | Revisar con sesión las pantallas y navegación completa. |
| RNF-07 Usabilidad | Detalle traduce estados/áreas y muestra IA (`frontend/src/main.tsx:176-205`) | Parcialmente comprobado | Baja | Prueba de componente o E2E autenticada. |
| RNF-08 Integridad | Pydantic y actualizaciones atómicas; sin validadores MongoDB; eventos incompletos | Parcial | Alta | Añadir validadores, índices y pruebas de operaciones sin cambios parciales. |
| RNF-09 Privacidad | Dataset declarado ficticio; remitente opcional; no se encontraron correos reales evidentes | Cumple según artefactos | Baja | Mantener revisión y licencia/procedencia por versión. |
| RNF-10 Trazabilidad | `modelVersion` se conserva; acciones humanas no guardan `before/after` y eventos se sobrescriben | Parcial | Bloqueante | Implementar `audit_events` de solo adición y asignación efectiva. |
| RNF-11 Reproducibilidad | Datos, splits, baseline, configuración, hashes y dependencias; faltan notebooks y versión documentada está desactualizada | Parcial | Alta | Estabilizar imagen/artefacto, notebooks y evidencia generada automáticamente. |
| RNF-12 Errores | 401/403/404/409/422/503 y fallo IA controlado | Parcial | Media | Probar timeout, respuesta malformada, Mongo caído y errores de frontend. |

## 7. Cobertura de los seis módulos del Proyecto 15

| Módulo | Evidencia | Estado | Brecha principal |
|---|---|---|---|
| Bandeja de entrada | API `GET /messages` y React `Workspace` | Parcial | Faltan departamento, estado y fechas. |
| Preprocesamiento | `prepare_text`, contrato con versión | Parcial | La versión no queda asociada a la predicción persistida; no hay EDA/notebook. |
| Clasificación NLP | TF-IDF + regresión logística, servicio y artefacto | Cumple para demo sintética | No demuestra generalización real; artefacto se entrena durante build. |
| Enrutamiento | Estados por confianza y fallo IA | Parcial | Umbral 0,45 no aprobado y asignación efectiva incompleta. |
| Gestión de estados | Gestión, asignación y cierre | Parcial | No permite corrección `EN_GESTION → EN_GESTION`. |
| Auditoría | Vista administrativa y eventos básicos | Parcial crítico | No es historial append-only completo ni ofrece todos los filtros. |

## 8. IA, dataset, métricas y umbral

### 8.1 Dataset

Validación ejecutada sobre `correos_sinteticos_v0.3.jsonl`:

- 128 registros: 80 entrenamiento, 24 validación y 24 prueba.
- Cada split contiene las cuatro clases: 20 por clase en entrenamiento y 6 por clase en validación/prueba.
- 128 IDs, textos, asuntos y cuerpos únicos.
- SHA-256: `f9998e9167d596d8a55b6a3e8fedd96e85709cb3c4d67301990f37e494bb96a8`.
- Los 40 registros v0.1 y los 80 v0.2 se conservan idénticos en v0.3.
- No hay duplicados exactos normalizados.
- La mayor similitud de caracteres observada entre splits fue 0,533 (`SYN-086` train frente a `SYN-090` validation). Esto no descarta similitud semántica o plantillas.

La procedencia está declarada como redacción ficticia del proyecto con asistencia de IA (`ai_service/data/README.md:1-16`), pero no hay licencia formal. El código evita evaluar `test` salvo `--evaluate-test`, aunque el historial disponible no permite demostrar que el contenido de prueba no fue inspeccionado al crear v0.2/v0.3. Por ello no se puede afirmar ausencia total de selección posterior al test.

### 8.2 Entrenamiento y evaluación reproducidos

`ai_service/train.py:91-145`:

- ajusta el baseline y cinco candidatos solo con `train`;
- elige `C` por Macro-F1 y desempata con log-loss en `validation`;
- reserva `test` por defecto;
- informa exactitud, Macro-F1, métricas por clase, matriz de confusión y enrutamiento;
- guarda hashes, parámetros, clases, Python y dependencias.

Resultado fresco dentro del contenedor:

| Split | Macro-F1 baseline | Macro-F1 clasificador | Cobertura a 0,45 | Precisión automática observada |
|---|---:|---:|---:|---:|
| Validación (24) | 0,100 | 0,958 | 20/24 = 83,3 % | 20/20 = 100 % |
| Prueba (24) | 0,100 | 0,958 | 20/24 = 83,3 % | 20/20 = 100 % |

El clasificador acertó 23/24 por categoría antes del umbral. Son 24 ejemplos sintéticos, balanceados y principalmente claros; no prueban rendimiento en correo corporativo real.

La latencia de `/predict` se volvió a medir con 24 solicitudes secuenciales: mediana 3,399 ms y p95 4,384 ms. No reproduce exactamente 1,7/2,1 ms de `docs/09_evaluacion_final_ia.md`, pero ambas mediciones son de inferencia interna y no end-to-end.

### 8.3 Sensibilidad del umbral

La comparación se ejecutó exclusivamente con validación:

| Umbral | Automáticos | Cobertura | Aciertos automáticos observados | Revisión |
|---:|---:|---:|---:|---:|
| 0,30 | 24 | 100,0 % | 23/24 | 0 |
| 0,40 | 21 | 87,5 % | 21/21 | 3 |
| 0,45 | 20 | 83,3 % | 20/20 | 4 |
| 0,55 | 16 | 66,7 % | 16/16 | 8 |
| 0,70 | 7 | 29,2 % | 7/7 | 17 |

Con esta muestra, `0,45` no domina a `0,40`: ambos tuvieron 100 % de precisión automática observada y `0,40` cubrió un caso adicional. Un criterio conservador podría preferir margen de confianza, pero no está documentado. La muestra es demasiado pequeña para convertir cualquiera de estos porcentajes en garantía.

**Decisión mínima requerida:** Juan Camilo Gonzales y Juan Jose Solarte deben aprobar el objetivo de selección —por ejemplo, costo de envío incorrecto frente a revisión manual— y registrar un ADR. Solo después debe actualizarse H-01 en SRS, HU y diagramas.

### 8.4 Artefacto y reproducibilidad

- `/health` sirve `tfidf-logreg-9b111546ffbd08b1`.
- Un reentrenamiento fresco en el mismo contenedor generó exactamente esa versión.
- `docs/09_evaluacion_final_ia.md` declara `tfidf-logreg-e7dceaa59fc6e694`; ya no coincide.
- El hash de versión incluye Python y dependencias. La imagen usa `python:3.13-slim` sin digest; el parche actual es 3.13.18, por lo que un rebuild futuro puede cambiar la versión aun sin cambiar código/datos.
- El artefacto no está versionado fuera de la imagen: se reentrena en `docker build`.
- `compare_thresholds.py` no se copia a la imagen, por lo que `python -m ai_service.compare_thresholds` falla dentro de `ai`.
- No existen notebooks `.ipynb`.

## 9. Docker, MongoDB y seguridad

### Cumple o está bien encaminado

- Cuatro servicios y volumen nombrado.
- DNS interno `api`, `ai`, `mongo`.
- `depends_on` con healthchecks.
- API e IA no publicadas al host.
- Mongo se limita a loopback.
- `.dockerignore` excluye Git, entornos, `node_modules`, artefactos, `.env`, docs y PDF.
- No hay `.env`, claves privadas, tokens o URI con credenciales rastreados.
- Hash Scrypt con sal; tokens aleatorios y solo su digest en MongoDB.
- Sesiones expiran en una hora y la consulta valida `expiresAt`; índice TTL presente.

### Brechas

- Falta `backend/scripts/init_db.py`; solo se crea el índice TTL.
- No hay validadores MongoDB ni índices para estado, departamento, fecha o auditoría.
- El modelo físico no coincide con D-09 en eventos, predicción y asignación.
- No existe revocación/logout en servidor.
- No se auditan sesiones ni usuarios.
- No hay rate limit ni protección explícita contra intentos reiterados; no es un RF separado, pero es deuda de seguridad.
- MongoDB se publica para desarrollo, mientras D-08 lo dibuja sin puerto. Debe documentarse como perfil local o retirarse en un perfil no local.
- Nginx sirve HTTP local; la terminación TLS de D-08 sigue pendiente para cualquier entorno no local.
- Las imágenes base y las dependencias del backend usan etiquetas/rangos mutables.

## 10. Pruebas existentes y resultado real

`tests/compose_acceptance.py` pasó completamente en esta ejecución y retiró su base temporal:

- 401 sin sesión y credenciales inválidas.
- 403 de operador en auditoría.
- 422 sin persistencia para mensaje inválido.
- clasificación, baja confianza y modelo/versionado;
- búsqueda textual, paginación y 404;
- conflictos de estado, asignación, gestión y cierre;
- auditoría básica;
- IA inalcanzable y asignación posterior;
- medición secuencial de 30 POST y 30 GET.

Medición fresca:

| Operación | n | Mediana | p95 | Objetivo |
|---|---:|---:|---:|---:|
| `POST /api/v1/messages` | 30 | 14,48 ms | 19,83 ms | ≤ 5 s |
| `GET /api/v1/messages` | 30 | 7,57 ms | 9,54 ms | ≤ 2 s |

Los valores pasan holgadamente, pero no reproducen 4,98/5,72 y 2,90/3,45 ms registrados en la matriz. Son ejecuciones distintas; la matriz no debe presentarlos como constantes.

### Cobertura ausente o insuficiente

- usuarios, activación, credencial temporal y auditoría de login;
- múltiples correcciones y corrección desde `EN_GESTION`;
- inmutabilidad, `before/after` y orden total de eventos;
- filtros de bandeja y auditoría;
- respuesta IA malformada, categoría/confianza inválida y timeout separado;
- MongoDB no disponible;
- expiración/revocación de sesión;
- concurrencia y carreras;
- frontend/componente/E2E autenticado;
- validadores e índices;
- carga concurrente y navegador end-to-end;
- CI.

El texto “CP-06 pasó” de la matriz es demasiado amplio: la suite espera que una segunda corrección retorne 409 (`tests/compose_acceptance.py:125-129`), mientras D-06 exige corrección motivada en `EN_GESTION`.

## 11. Hallazgos priorizados

### Bloqueantes

#### B-01 — Gestión de acceso Must ausente

- **Evidencia:** OpenAPI no contiene `/auth/activate` ni `/users`; `backend/create_user.py:26-32` inserta `active=True`.
- **Impacto:** RF-01, RF-02, HU-01/HU-02 y CP-08 quedan incompletos; no existe flujo administrado ni credencial de un uso.
- **Corrección mínima:** implementar creación/activación, estado y rol con secretos hasheados, más UI administrativa y eventos.
- **Aceptación sugerida:** administrador crea; operador recibe 403; secreto se muestra una vez; activación invalida credencial; login posterior funciona; ningún secreto aparece en consultas/eventos.

#### B-02 — Auditoría no es inmutable ni completa

- **Evidencia:** campos únicos `creationEvent`, `classificationEvent`, `manualEvent`, `managementEvent`, `closureEvent` (`backend/main.py:65-70,91-96,160-166,184-197`); la consulta solo los proyecta (`225-237`).
- **Impacto:** una repetición sobrescribe historia; faltan `actorType`, `before/after` y eventos de acceso; contradice RN-08, RNF-10 y D-09.
- **Corrección mínima:** colección append-only con índices; conservar lectura de campos legados y preparar migración idempotente no destructiva.
- **Aceptación sugerida:** dos correcciones generan dos eventos distintos e inmutables, con actor, antes, después, motivo y fecha.

#### B-03 — Corrección en `EN_GESTION` rechazada

- **Evidencia:** API admite solo pendientes y `CLASIFICADO` (`backend/main.py:155`); React usa el mismo conjunto (`frontend/src/main.tsx:19,206`).
- **Impacto:** incumple D-06 línea 15 y RF-11; un operador no puede corregir un error detectado durante la atención.
- **Corrección mínima:** admitir actualización atómica `EN_GESTION → EN_GESTION`, conservar predicción y asignación previa, y añadir evento append-only.
- **Aceptación sugerida:** corregir dos veces conserva predicción y tres versiones efectivas en la historia sin perder eventos.

### Alta

#### A-01 — Filtros Must incompletos

- **Evidencia:** bandeja solo acepta texto/página (`backend/main.py:105-113`); auditoría solo mensaje/límite (`219-224`).
- **Impacto:** RF-08, RF-12, HU-04 y HU-13 parciales.
- **Corrección mínima:** departamento, estado, rango de fechas; actor, acción y fechas; índices acordes.

#### A-02 — Umbral 0,45 sin criterio aprobado

- **Evidencia:** `compose.yaml:25`, `ai_service/train.py:22`; SRS y D-06 conservan H-01=0,70.
- **Impacto:** comportamiento de negocio difiere de la línea base; 0,40 rindió mejor en cobertura con igual precisión observada en validación.
- **Corrección mínima:** ADR con objetivo/costo y aprobación del equipo; mantener variable de entorno.

#### A-03 — Modelo físico pierde metadatos previstos

- **Evidencia:** `Prediction` solo tiene categoría/confianza/modelo (`ai_service/contract.py:13-16`); documento no guarda versión de preprocesamiento, source/timestamp ni asignación efectiva completa.
- **Impacto:** RF-04, RN-07, RNF-10 y D-09 parciales.
- **Corrección mínima:** ampliar esquema de forma aditiva y conservar compatibilidad con documentos existentes.

#### A-04 — Reproducibilidad/documentación del modelo divergente

- **Evidencia:** versión ejecutada `9b111...` frente a `e7dce...`; artefacto entrenado durante build; base Python mutable; script de umbrales ausente de la imagen.
- **Impacto:** `docs/09` no identifica la demo actual y el rebuild puede cambiar versión.
- **Corrección mínima:** fijar entorno, exportar/promover un artefacto verificado o separar build de entrenamiento, y generar evidencia desde metadatos reales.

#### A-05 — Inicialización MongoDB incompleta

- **Evidencia:** solo índice TTL (`backend/main.py:35`); no existe `backend/scripts/init_db.py`.
- **Impacto:** integridad depende solo de API y las consultas filtradas no tienen índices previstos.
- **Corrección mínima:** script idempotente de validadores/índices, sin borrar colecciones.

#### A-06 — Cobertura de pruebas insuficiente para los Must

- **Evidencia:** un script de 192 líneas y sin CI; omisiones listadas en §10.
- **Impacto:** la matriz puede sugerir más cobertura de la realmente ejercida.
- **Corrección mínima:** separar unitarias, integración, contrato, aceptación y frontend; mantener la suite aislada.

### Media

#### M-01 — Detalle no entrega auditoría relacionada

- **Evidencia:** `MessageDetail` termina en cuerpo/resolución (`backend/schemas.py:44-46`).
- **Impacto:** RF-09 parcial; el administrador debe hacer otra consulta y el operador no ve trazabilidad.
- **Corrección mínima:** decidir si se incluye resumen autorizado o enlace/endpoint por mensaje.

#### M-02 — Notebooks académicos ausentes

- **Evidencia:** no hay `.ipynb`.
- **Impacto:** falta evidencia pedagógica de entorno, EDA, gráficas y evaluación solicitada; el runtime Python sí está correctamente separado.
- **Corrección mínima:** notebooks que importen lógica de `.py`, sin convertir Jupyter en dependencia de Compose.

#### M-03 — Desarrollo frontend depende de versión de npm

- **Evidencia:** Node 24/npm 11 falló con TS2688 por `@types/node`; build limpio en Docker Node 22/npm 10 pasó.
- **Impacto:** los pasos locales del README no son reproducibles en todo entorno compatible.
- **Corrección mínima:** declarar Node soportado y añadir explícitamente `@types/node` o excluir/configurar `vite.config.ts` de manera compatible.

#### M-04 — Desviación React/CSS frente a React/Tailwind

- **Evidencia:** no hay dependencia/configuración Tailwind; README cambió el stack a CSS.
- **Impacto:** contradice una decisión del equipo, aunque no impide el flujo funcional.
- **Corrección mínima:** aprobar CSS actual o migrar incrementalmente; no rehacer la UI sin decisión.

#### M-05 — Sesión sin revocación ni auditoría

- **Evidencia:** logout React solo elimina estado (`frontend/src/main.tsx:340-347`); no hay endpoint de revocación.
- **Impacto:** el token sigue válido hasta una hora y no queda evento de acceso/salida.
- **Corrección mínima:** endpoint logout/revocación y eventos, si se aprueba dentro de RF-01.

### Baja

- Lighthouse del login obtuvo accesibilidad y buenas prácticas 1,00; SEO 0,60 por meta descripción y `robots.txt`. No es crítico para el MVP interno.
- SRS/arc42 aún contienen frases “no implementado/futuro”; deben actualizarse solo después de aprobar las correcciones y evidencia final.
- La matriz conserva métricas de otra ejecución y debe identificar fecha/hash/entorno o enlazar artefactos generados.

## 12. Siguientes cambios atómicos propuestos

El orden expresa dependencias, no duración.

1. **Aprobar decisiones de umbral, auditoría física, CSS/Tailwind y política de credenciales.**
   - Documentos futuros: `docs/07_decisiones_tecnicas.md`, SRS/diagramas solo tras aprobación.
   - Prueba: revisión de consistencia de IDs y contratos.
   - Commit sugerido: `docs(adr): documenta las decisiones pendientes del mvp`

2. **Crear inicialización MongoDB idempotente y esquema append-only.**
   - Archivos: `backend/scripts/init_db.py`, `backend/db.py`, `compose.yaml`.
   - Añadir validadores e índices; no borrar datos.
   - Pruebas: dos ejecuciones del script dejan el mismo esquema.
   - Commit: `feat(datos): inicializa validadores e índices de forma idempotente`

3. **Introducir auditoría externa compatible con datos legados.**
   - Archivos: nuevo `backend/audit.py`, `backend/main.py`, `backend/auth.py`, `backend/schemas.py`.
   - Escribir eventos append-only; mantener lectura temporal de eventos embebidos. Cualquier backfill requiere respaldo y aprobación separada.
   - Pruebas: múltiples eventos, filtros y no modificación.
   - Commit: `feat(auditoria): conserva un historial inmutable de eventos`

4. **Permitir correcciones sucesivas y completar asignación efectiva.**
   - Archivos: `backend/main.py`, `backend/schemas.py`, `frontend/src/main.tsx`, `frontend/src/api.ts`.
   - Pruebas: pendientes, `CLASIFICADO` y `EN_GESTION`; predicción inmutable; `before/after`.
   - Commit: `fix(mensajes): permite correcciones motivadas durante la gestión`

5. **Implementar usuarios y activación.**
   - Archivos: `backend/auth.py`, nuevo módulo de usuarios, esquemas, componentes React y API cliente.
   - Pruebas: secreto de un uso, duplicado 409, roles 403, activación y auditoría sin secretos.
   - Commit: `feat(auth): implementa activación y gestión de usuarios`

6. **Completar filtros y detalle.**
   - Archivos: `backend/main.py`, `backend/schemas.py`, `frontend/src/main.tsx`, `frontend/src/AuditView.tsx`, `frontend/src/api.ts`.
   - Pruebas: combinaciones de departamento/estado/fecha y actor/acción/fecha.
   - Commit: `feat(bandeja): añade filtros de mensajes y auditoría`

7. **Persistir metadatos completos de IA.**
   - Archivos: `ai_service/contract.py`, `backend/classifier.py`, `backend/schemas.py`, `backend/main.py`.
   - Pruebas: versión de preprocesamiento, origen, timestamp y compatibilidad con documentos anteriores.
   - Commit: `fix(ia): persiste metadatos de predicción y asignación`

8. **Estabilizar el artefacto y el entorno IA.**
   - Archivos: `Dockerfile`, requisitos, `ai_service/train.py`, `compare_thresholds.py`, README y evaluación.
   - Pruebas: hash/versiones iguales entre artefacto evaluado, `/health` y reporte.
   - Commit: `build(ia): sirve un artefacto evaluado y versionado`

9. **Añadir notebooks académicos con lógica compartida.**
   - Archivos: `ai_service/notebooks/00_verificacion_entorno.ipynb`, `01_eda_dataset.ipynb`, `02_entrenamiento_evaluacion.ipynb`.
   - Pruebas: ejecución limpia y comparación con resultados del módulo Python.
   - Commit: `docs(ia): añade análisis y evaluación reproducibles`

10. **Ampliar y automatizar pruebas.**
    - Archivos: `tests/`, configuración pytest y CI; mantener bases únicas.
    - Incluir usuarios, auditoría, filtros, IA inválida, concurrencia y frontend.
    - Commit: `test(mvp): cubre contratos seguridad y resiliencia`

11. **Cerrar coherencia documental.**
    - Archivos: SRS, matriz MD/CSV, arc42, ADR, evaluación y README.
    - Solo después de ejecutar toda la evidencia.
    - Commit: `docs(mvp): sincroniza requisitos y evidencia ejecutada`

## 13. Decisiones para Juan Camilo Gonzales y Juan Jose Solarte

1. ¿Se adopta `0,45`, `0,40`, se conserva `0,70` o se amplía el dataset antes de decidir?
2. ¿Se confirma `audit_events` como colección append-only y una migración aditiva de eventos embebidos?
3. ¿Qué vigencia tendrán credencial temporal y sesión, y se exige logout/revocación?
4. ¿Se mantiene CSS actual o se cumple la decisión previa de Tailwind?
5. ¿MongoDB seguirá publicado en loopback solo para desarrollo mediante un perfil Compose?
6. ¿Se promoverá un artefacto evaluado o se mantendrá entrenamiento durante build con imágenes fijadas?
7. ¿La procedencia declarada del dataset sintético es suficiente o se añadirá una licencia explícita del equipo?

## 14. Validaciones ejecutadas

| Validación | Resultado |
|---|---|
| Git: estado, ramas, remotos, hashes, merge-base y diff | Correcto; versiones esperadas y árbol inicialmente limpio |
| AST Python de backend, IA y prueba | 12 archivos válidos |
| `docker compose config` | Válido |
| `docker compose ps --all` | Cuatro servicios saludables |
| Hash host/contenedor | Backend e IA coinciden con la rama |
| OpenAPI real | 7 rutas; faltan 2 del SRS |
| Suite `compose_acceptance.py` | Pasó; base aislada retirada |
| Base temporal residual | Ninguna `compose_acceptance_*` |
| Dataset v0.3 | 128; 80/24/24; balanceado; sin duplicados exactos |
| Entrenamiento/evaluación IA | Macro-F1 0,958 en validation y test |
| Sensibilidad 0,30–0,70 | Ejecutada en validation |
| Inferencia HTTP IA | n=24; mediana 3,399 ms; p95 4,384 ms |
| Frontend Docker limpio | Build exitoso con Node 22/npm 10 |
| Frontend local temporal | Falló TS2688 con Node 24/npm 11 |
| Interfaz pública | Login renderizado; sin errores de consola |
| Lighthouse login | Accesibilidad 1,00; buenas prácticas 1,00; SEO 0,60 |
| MongoDB | Solo metadatos de colecciones/índices; sin lectura de documentos |
| Secretos rastreados | Sin patrones de alto riesgo |

### Comandos principales reproducibles

```powershell
git status --short --branch
git branch --all --verbose --no-abbrev
git diff --stat main...implementacion-mvp
docker compose config
docker compose ps --all
Get-Content tests/compose_acceptance.py -Raw -Encoding utf8 | docker compose exec -T api python -
docker compose exec -T ai python -m ai_service.train --evaluate-test --output-dir /tmp/evaluacion
docker build --no-cache --target build -f frontend/Dockerfile .
```

La comparación de umbrales se ejecutó mediante el mismo `routing_summary` dentro del contenedor porque el módulo `ai_service.compare_thresholds` no está copiado en la imagen.

## 15. Limitaciones y cierre

- No se usaron credenciales existentes ni se ejecutó un flujo React autenticado.
- No se modificó ni migró la base de demo.
- No se ejecutó carga concurrente, TLS, accesibilidad autenticada ni navegadores múltiples.
- No se puede demostrar ausencia semántica total de fuga de datos con una comparación estática.
- Las métricas corresponden al entorno y muestra descritos, no a correos corporativos reales.
- No se modificó código, dataset, requisitos, diagramas, configuración/ciclo de vida de contenedores ni volúmenes; solo se generó evidencia temporal en `/tmp` del contenedor IA.
- No se realizó commit, push, merge, rebase, reset ni cambio de rama.

**Recomendación final:** mantener `implementacion-mvp` abierta, aprobar las decisiones de §13 y corregir primero B-01 a B-03. Después debe repetirse la auditoría sobre un nuevo hash antes de considerar la fusión.
