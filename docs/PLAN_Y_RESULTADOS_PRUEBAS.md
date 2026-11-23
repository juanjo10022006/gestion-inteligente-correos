# Plan y resultados de pruebas — Proyecto 15

**Equipo:** Juan Camilo Gonzales y Juan Jose Solarte.
**Base técnica:** `3f9a067`. **Revisión documental:** 23 de noviembre de 2026.

## Alcance y estados

Responde al apartado **17.7** de la guía: pruebas unitarias de servicios/reglas, integración de persistencia/IA, API, aceptación de HU, entradas inválidas, IA con test separado y rendimiento básico. Conserva **CP-01…CP-10** de la matriz, sin renumerarlos.

- **E — ejecutada con evidencia:** existe resultado previo observado; se identifica su alcance y soporte. No significa reejecutada en este cierre.
- **P — definida y pendiente:** todavía no se ejecutó/formalizó la comprobación indicada.
- **NA — no aplicable justificadamente:** fuera del alcance aprobado, nunca sustituto de un requisito obligatorio.

La cobertura de aceptación/API no equivale a cobertura unitaria completa ni a validación de la interfaz gráfica.

## Evidencias y procedencia

| Ref. | Evidencia | Qué acredita / límite |
|---|---|---|
| E-IA | [Reporte servido](evidencias/ia/evaluacion_artefacto.json), [manifiesto](evidencias/ia/manifest.json), [procedencia](evidencias/ia/procedencia.json), [ejecución notebook](evidencias/ia/ejecucion_notebooks.json) | Resultados del bloque técnico, contrastados ahora por huellas y correspondencia de fuentes; no nueva inferencia ni entrenamiento |
| E-TECH | Salidas observadas en la intervención técnica anterior; código de pruebas en `3f9a067` | Cinco suites, artefacto y smoke pasaron entonces. No hay un log autónomo de toda esa corrida versionado; se debe conservar uno en la prueba final. El código de un test no prueba por sí solo que se ejecutó |
| E-GIT | Commits `d657e7a`, `e48ff3f`, `5443006`, `3f9a067` comprobados en el historial | Correcciones presentes; no sustituyen la evidencia de ejecución |
| E-DOC | [OpenAPI generado](openapi.json), comparación con `app.openapi()` y fuentes backend coincidentes | Exportación realizada ahora sin ciclo de arranque ni MongoDB; no acredita respuestas HTTP reales |
| E-HIST | [Hallazgos y resultados históricos consolidados](INFORME_FINAL_PROYECTO.md#7-pruebas-y-calidad) | Revisión de `0641fd5`; antecedentes, correcciones y límites, no dictamen del código actual. Originales recuperables en Git según la procedencia del informe |

En esta intervención **no se ejecutaron suites integrales, builds completos ni entrenamientos**. Se comprobaron documentos, archivos curados, contratos y sintaxis de comandos. En el cierre técnico anterior, después de corregir LF, se verificó el modelo `4899…` contra `/health` y se reprodujeron notebooks; las pruebas de software anteriores se conservaron y se contrastó equivalencia funcional del pipeline. No se confunden esas corridas.

## Casos CP-01 a CP-10

R1 = `powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_history_checks.ps1 -AiImage gestion-correos-ai-final:local`. R1 ejecuta los archivos indicados abajo en contenedores aislados.

| ID | Tipo | RF/RNF/HU | Archivo / comando | Estado y resultado observado | Evidencia / limitación |
|---|---|---|---|---|---|
| CP-01 | Integración, API, aceptación HU | RF-03; RNF-08/10; HU-03 | R1: `compose_acceptance.py`, `history_acceptance.py`, `final_acceptance.py` | E: 201, original conservado, `RECIBIDO` y evento antes de inferencia | E-TECH; observación intermedia mediante mock y servidor IA de prueba, no solo orden textual |
| CP-02 | Entrada inválida, API | RF-03; RNF-08/12; HU-03 | R1: `compose_acceptance.py` | E: asunto corto 422, sin crear mensaje | E-TECH; no cubre exhaustivamente todas las fronteras posibles |
| CP-03 | Integración IA/API, aceptación HU | RF-04/05; RNF-05/10/11; HU-06/07 | R1: `compose_acceptance.py`; notebooks 00/02 | E: predicción con categoría/confianza/versión; P para versión de preparación independiente cuando IA falla | E-TECH/E-IA; RF-04 parcial en variante sin predicción |
| CP-04 | Regla/enrutamiento, aceptación HU | RF-06; RN-03/04; RNF-04; HU-08 | R1: `compose_acceptance.py`; reporte validation | E: clasificación y revisión a 0,45 | E-TECH/E-IA; no valida literalmente H-01=0,70 ni demuestra umbral óptimo |
| CP-05 | API, filtros, aceptación HU | RF-08/09; RNF-03; HU-04/05 | R1: `compose_acceptance.py`, `history_acceptance.py` | E: texto/estado/área/fechas combinados, paginación, 404, fechas inválidas 422 | E-TECH; RNF-06/07 de UI se revisan aparte |
| CP-06 | Integración, concurrencia, aceptación HU | RF-10/11/13; RN-02/07; RNF-08/10; HU-10/11/12 | R1: `history_acceptance.py`, `compose_acceptance.py` | E: correcciones múltiples incluso en gestión, predicción conservada, cierre, conflictos y motivos inválidos | E-TECH; pruebas concurrentes controladas, no carga de usuarios |
| CP-07 | API, seguridad, historial | RF-12; RN-08; RNF-02/10; HU-13 | R1: `history_acceptance.py`, `access_acceptance.py` | E: filtros actor/acción/fechas, 401/403/405, eventos legados y recuperación sin duplicados | E-TECH; no prueba permisos MongoDB restrictivos ni interfaz React |
| CP-08 | API, seguridad, concurrencia | RF-01/02; RNF-01/02/08/10; HU-01/02 | R1: `access_acceptance.py` | E: alta, activación, expiración, doble uso, renovación, carrera renovación/activación, revocación, CLI y auditoría fallida/reintento sin secretos | E-TECH; pruebas con MongoDB, no unitarias puras; TLS y rate limiting pendientes |
| CP-09 | IA independiente, calidad de datos | RF-05; RNF-11; HU-14 | R1: `artifact_verification.py`, `evaluate_artifact`; notebooks | E: checksum previo a carga, incompatibilidades, reproducción funcional y test congelado | E-IA/E-TECH; test separado del ajuste pero observado previamente, sin garantía binaria |
| CP-10 | Fallos IA, integración, aceptación HU | RF-07/11; RNF-04/12; HU-09/11 | R1: `compose_acceptance.py`, `final_acceptance.py` | E: servicio inalcanzable, JSON malformado, categoría/confianza/versión inválidas, timeout y asignación manual | E-TECH; no promete arranque Compose cuando IA inicialmente falla salud |

Los nombres de archivo son relativos a [tests](../tests/). La [matriz MD/CSV](04_matriz_trazabilidad.md) vincula los objetivos y las catorce HU.

## Cobertura adicional y pruebas pendientes

| ID local de plan | Tipo / relación | Procedimiento o archivo | Estado y aceptación |
|---|---|---|---|
| INIT | Integración MongoDB; RNF-08/10 | R1: `init_db_verification.py` | E, E-TECH: inicialización repetible, validadores/índices, preservación y conflicto sin reemplazo destructivo |
| DEMO | Integración/seguridad; RF-01/02/03 | R1: `final_acceptance.py` | E, E-TECH: base vacía, repetición, cuentas existentes intactas, TTY/opt-in/no local, entrega previa a fallo posterior |
| E2E-HTTP | Sistema HTTP, cuatro servicios; HU-01…13 | `tests/run_compose_smoke.ps1` → `compose_smoke.py` | E, E-TECH: web compilada, proxy, activación/login, demo, inferencia y auditoría con MongoDB `tmpfs`; no ejecuta JavaScript del navegador |
| BUILD | Compilación/dependencias; RNF-05/11 | `npm ci`, `npm run build`, `npm audit`; `pip check`; `docker compose config --quiet` | E en bloque técnico; `npm audit` volvió a dar cero vulnerabilidades en cierre técnico. No se ejecutó build nuevo en documentación |
| DOC-API | Contrato documental; RNF-05/12 | Exportación `app.openapi()` del manual técnico | E ahora: 13 operaciones y esquemas coinciden; faltan declaraciones explícitas de varios errores de runtime |
| UT-01 | Unitaria; RF-04/HU-06 | Definir suite sin MongoDB para `prepare_text` y contrato de preparación | P: espacios, Unicode, texto vacío y versión; celdas de notebook no equivalen a suite unitaria exhaustiva |
| UT-02 | Unitaria; RF-01/02, RNF-08 | Definir suite aislada para `validate_password`, modelos y límites | P: fronteras 11/12/256/257, espacios y tipos; no confundir con pruebas HTTP ya realizadas |
| UT-03 | Unitaria; RF-08/12, RNF-12 | Definir suite aislada para `date_range` y validadores | P: zonas, extremos y rango invertido sin levantar API |
| UI-INT | Aceptación manual HU-01…13; RNF-06/07 | Recorrido descrito abajo | P: navegador autenticado, usabilidad, foco/teclado, estados de carga/error y permisos visibles |
| CORR-H | Resultado humano; RF-11/RNF-10 | Sesión de demo con conjunto fijado y registro de decisiones | P: número de mensajes revisados, correcciones y denominador; no medir con el conjunto test para volver a ajustar |
| PERF-F | Rendimiento básico; RNF-03 | Repetir `measure()` y documentar corrida final; separar prueba `/predict` si se mide | P para informe integral actual; rendimiento básico previo se registra abajo |
| BACKUP | Recuperación operativa; RNF-04 | Definir copia/restauración sobre instancia exclusivamente temporal | P: no afirmar recuperación del volumen sin probar |
| EXT | Integración de buzón real | Gmail/Outlook/IMAP/SMTP | NA: excluidos del MVP; no exime de probar el formulario ni el servicio IA |

## Rendimiento: una corrida histórica, no una medición nueva

Registro observado en la última corrida completa del lanzador durante el bloque técnico previo a la normalización LF (modelo `tfidf-logreg-b020c42c96952038`). API Python 3.13 en contenedor Linux sobre Docker Desktop/Windows, MongoDB efímero e IA reales; hardware/recursos del host no caracterizados. No se atribuye esta medición al archivo `4899…`.

| Operación | n secuencial | Mediana | p95 | Objetivo SRS |
|---|---:|---:|---:|---:|
| POST `/api/v1/messages` | 30 | 10,61 ms | 12,40 ms | ≤5 s |
| GET `/api/v1/messages` | 30 | 3,52 ms | 4,33 ms | ≤2 s |

Fuente: salida de sesión técnica E-TECH, no un log autónomo versionado. `measure()` calcula p95 mediante `statistics.quantiles(..., method="inclusive")`, sin etapa de calentamiento explícita. Incluye llamada HTTP local desde el contenedor API, autenticación Bearer, MongoDB y, en POST, inferencia/enrutamiento. Excluye Nginx, navegador, acceso por Internet y carga concurrente. Cumplir esos objetivos en esta muestra no demuestra capacidad productiva. La prueba final debe guardar su propio log saneado, entorno, versión/checksum, n y percentiles; no mezclar corridas.

## Registro de defectos y correcciones

| ID | Síntoma/evidencia | Corrección o estado | Commit comprobado |
|---|---|---|---|
| DEF-01 | Historial embebido sobrescribía acciones; auditoría inicial | `audit_events`, snapshots, CAS y legados sin migración; `history_acceptance.py` | `e48ff3f` |
| DEF-02 | Faltaban filtros Must, corrección durante gestión e inicialización | Filtros/historial y validadores/índices idempotentes; suites history/init | `e48ff3f`, `d657e7a` |
| DEF-03 | Sin altas API/activación ni revocación | Cuentas/activación/sesiones API y React; `access_acceptance.py` | `5443006` |
| DEF-04 | Una publicación fallida ocultaba creación/activación ya persistidas; pérdida de credencial entregable | `publish_after_commit`, renovación pendiente, auditoría durable y pruebas de carreras/fallos | `3f9a067` |
| DEF-05 | Reporte/modelo divergentes; cambios CRLF alteraban huellas | Bundle/manifiesto, evaluador servido, versiones fijadas y LF acotado; evidencia `4899…` | `3f9a067` |
| DEF-06 | Gráfico de confusión no aceptaba lista; faltaba tipado Node; aviso alto Vite | Conversión a array, `@types/node`, Vite 6.4.6; ejecución notebook/build/audit previos | `3f9a067` |
| DEF-07 | CLI `create_user` aún publica estrictamente después de insertar | Pendiente: posible cuenta creada con salida de error ante fallo de publicación; evidencia de código, fallo no inyectado ahora | Sin corrección; sin referencia comprobada de corrección |
| DEF-08 | 422 automático OpenAPI no refleja handler seguro de acceso; varios errores no declarados | Pendiente documental/técnico del contrato; no se alteró a mano el exportado | Sin corrección |
| DEF-09 | RF-04 pide versión de preparación; no se registra separadamente cuando falta predicción | Pendiente acordar aceptación/corrección específica, sin rebajar requisito | Sin corrección |

Las referencias de commit se contrastaron en el cierre documental. El [informe general](INFORME_FINAL_PROYECTO.md#7-pruebas-y-calidad) integra los hallazgos preliminares con sus correcciones y estados vigentes; sus versiones completas permanecen en Git. No se interpreta la retirada de informes redundantes como ausencia histórica de defectos.

## Recorrido integral manual pendiente

La auditoría histórica observó la pantalla pública de acceso; **no consta una comprobación formal del usuario de todo el recorrido autenticado**. No se inventan capturas ni observaciones personales.

En una instalación/base de evaluación separada y con cuentas ficticias:

1. Arranque limpio, healthchecks y acceso mediante la guía; registrar entorno y commit.
2. Bootstrap o demo opt-in; activación de ambos roles y segunda ejecución idempotente.
3. Operador: bandeja/filtros, registro válido/inválido, revisión de categoría/confianza/modelo.
4. Asignación motivada, corrección durante gestión, conservación original y cierre con resolución.
5. Administrador: usuarios, renovación pendiente, cambio de rol/estado y auditoría por filtros.
6. Revocación/logout, expiración, falta de permiso y errores sin secretos. La falla IA se provoca solo en entorno efímero, no deteniendo la demo del equipo.
7. Teclado, etiquetas, foco, errores textuales y presentación; tomar solo las capturas propuestas en el manual.
8. Guardar resultados saneados y medir rendimiento/correcciones humanas con protocolo y denominador explícitos.

## Criterios de aceptación académica y salida

Para **17.9**: demostrar el flujo UI→API→IA→MongoDB→UI sin editar código durante la demo; baseline y modelo comparables; recetas y artefacto identificables; requisitos vinculados con pruebas; y errores manejados con ruta manual.

Antes del merge: revisar estos documentos, ejecutar/formalizar UI-INT y aceptación integral, resolver o aceptar explícitamente los parciales (incluido H-01), completar cobertura unitaria exigida por 17.7, conservar logs saneados de la corrida final y preparar video/demo en una fase separada. TLS, mínimo privilegio y limitación de intentos son restricciones de cualquier uso no local; no se presenta esta demo como producción segura. Renderizado UML/C4 y necesidad específica de TikZ requieren confirmación. No se declara todavía aceptación académica definitiva.
