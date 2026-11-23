# Informe final integrador

## Portada

**Proyecto 15: Sistema inteligente de clasificación de correos corporativos**
**Asignatura:** Big Data — Universidad Autónoma de Occidente.
**Equipo:** Juan Camilo Gonzales y Juan Jose Solarte.
**Base técnica:** rama `implementacion-mvp`, commit `3f9a067`.
**Revisión documental:** 23 de noviembre de 2026. Este informe integra resultados disponibles; no sustituye la aceptación integral posterior.

Es el **único informe general**: consolida los hallazgos relevantes de las revisiones de requisitos, diseño y primera implementación, sin convertir sus dictámenes históricos en resultados actuales. Los manuales, plan de pruebas, evaluación IA y documentos de especificación conservan su función especializada. Esta consolidación es editorial: no incluye una nueva auditoría, entrenamiento ni ejecución integral.

## 1. Resumen ejecutivo

Se construyó un MVP local que registra mensajes ficticios, sugiere una de cuatro áreas con NLP y permite revisión humana, gestión y cierre con auditoría. Integra una interfaz React, API FastAPI, servicio independiente scikit-learn y MongoDB mediante cuatro servicios Docker Compose.

La IA se comparó con un baseline sobre un corpus sintético de 128 correos. El test separado de 24 mensajes obtuvo 23 aciertos, exactitud 95,8 % y Macro-F1 0,958 frente a 0,100 del baseline. Estos resultados no demuestran generalización empresarial. La versión del artefacto evaluado es `tfidf-logreg-4899d09a3071f491`; sus huellas y resultados están en [evaluación IA](09_evaluacion_final_ia.md).

Las pruebas técnicas previas cubren API, persistencia, historial, acceso, fallos IA, demo opt-in y flujo HTTP de cuatro servicios. Quedan pendientes pruebas unitarias completas, recorrido autenticado de navegador, accesibilidad y la prueba integral definitiva. No se presenta el smoke HTTP como validación completa de React.

## 2. Problema, justificación y objetivos

La distribución manual de solicitudes puede generar errores de destino y falta de trazabilidad. El sistema centraliza el registro y conserva una predicción asistida y la decisión humana efectiva; no toma decisiones laborales o financieras autónomas.

Objetivo general **OBJ-01**: disponer de un MVP demostrable de registro, clasificación, enrutamiento, gestión autorizada y auditoría. Objetivos específicos **OBJ-02…08**: validar registros; producir predicción con confianza/versión; distinguir certeza operativa y revisión; consultar/gestionar; conservar historia; autorizar por rol; y permitir evaluación reproducible frente a un baseline. La formulación original y exclusiones se conservan en [visión y alcance](01_vision_alcance.md).

## 3. Alcance, requisitos e historias

Seis módulos: **bandeja, preprocesamiento, clasificación NLP, enrutamiento, estados y auditoría**. Roles obligatorios `OPERADOR` y `ADMINISTRADOR`; categorías `SOPORTE_TECNICO`, `VENTAS`, `RECURSOS_HUMANOS`, `FACTURACION`. No se integran Gmail/Outlook, IMAP/SMTP, adjuntos, autoservicio externo ni datos corporativos reales.

El [SRS](02_srs.md) conserva **13 RF, 12 RNF y 8 reglas**. Cinco épicas y catorce HU se mantienen en [fichas](05_epicas_y_hu.md) y [backlog](03_backlog.md); la [matriz MD](04_matriz_trazabilidad.md) y [CSV](04_matriz_trazabilidad.csv) conectan objetivos, requisitos, HU, UI y pruebas. HU-14 es habilitador técnico, no actor de negocio ficticio.

La implementación de un flujo no equivale a aceptación de todo RNF. Los parciales incluyen H-01, preprocesamiento sin predicción, accesibilidad y seguridad no local; no se rebajaron los requisitos para hacerlos parecer cumplidos.

La revisión de requisitos corrigió la ausencia de fichas detalladas mediante cinco épicas y catorce HU, mantuvo la equivalencia **EP-01…05 → EPI-001…005** y separó el backlog ejecutivo de los criterios de aceptación. La matriz mantiene quince relaciones MD/CSV y los IDs estables OBJ, RF, RNF, RN, EPI, HU, CP y UI. **RF-13 sigue siendo Should**; los demás RF son Must. No se trasladó al proyecto el dominio ERP/POS del DOCX usado como patrón de fichas.

La elección de solo dos roles es una delimitación del MVP: el «usuario final» de la guía es sugerido, no un autoservicio obligatorio. El servicio IA es un componente **interno** del sistema, no un actor de negocio externo, aunque se ejecute separado de la API.

## 4. Arquitectura e implementación

La [arquitectura arc42](06_arquitectura_diagramas.md) mantiene doce secciones y enlaza los nueve [diagramas UML/C4](diagramas/README.md). Los seis [prototipos SVG](05_prototipos.md) son antecedentes de diseño, no capturas de una prueba.

Las correcciones de diseño aclararon límites y niveles C4 de D-01/D-02, dependencias y notación UML de D-03/D-04, ramas/respuesta 201 y transiciones de D-05/D-06, particiones y redes/TLS de D-07/D-08, y separación de predicción/asignación/actores de D-09. En UI-02…06 se añadió `viewBox`; UI-04 distingue ausencia de predicción sin inventar valores. Se revisaron estáticamente cuatro fuentes PlantUML, cinco Mermaid y seis SVG; estos últimos se validaron como XML y se comprobaron sus coordenadas respecto del `viewBox`. La revisión visual comunicada de diseños no equivale a una prueba del frontend autenticado. Renderizado automático y recortes visuales de UML/C4 siguen pendientes.

| Servicio | Función |
|---|---|
| Web | React/TypeScript/Vite/CSS compilado en Nginx; formulario, bandeja, detalle, gestión, usuarios y auditoría |
| API | FastAPI/Pydantic/PyMongo: validación, autorización, reglas de estados/enrutamiento y auditoría |
| IA | FastAPI interno: carga un bundle TF-IDF/regresión logística y devuelve predicción con metadatos |
| MongoDB | Usuarios, sesiones, mensajes, eventos y colección preparada de metadatos |

La secuencia crítica es **validar → persistir `RECIBIDO` y auditar creación → preparar texto/inferir → actualizar y auditar resultado → responder**. Baja confianza produce `PENDIENTE_REVISION`; fallo IA produce `PENDIENTE_CLASIFICACION`. Asignación humana lleva a `EN_GESTION` sin sobrescribir predicción; el cierre exige resolución.

La autenticación/autorización es precondición de la solicitud operativa; que D-05 no dibuje una comprobación de sesión separada no la elimina. El detalle devuelve información operativa; la auditoría relacionada se consulta por su endpoint y acceso administrativo, sin exponer el historial global al operador. La predicción válida conserva preparación, origen y timestamp; la asignación efectiva se guarda por separado y los eventos distinguen actos automáticos `SISTEMA` de intervenciones humanas.

MongoDB se eligió por la forma documental de mensajes/predicciones y afinidad JSON/Python; no por imposición docente. PostgreSQL es alternativa válida con más relaciones. [ADR](07_decisiones_tecnicas.md) y [modelo de datos](08_modelo_datos_preliminar.md) explican validadores, índices, revisión optimista e intención de auditoría persistida. Los eventos legados se consultan sin migración destructiva. Un backfill requeriría respaldo y autorización separada; no se acredita recuperación de backups sin una prueba de restauración.

La formalización de ADR-01 resolvió la discrepancia entre MongoDB ya adoptado y textos que aún lo consideraban sin justificación. La implementación conserva CSS, sin exigir una migración estética a Tailwind. Compose usa DNS interno y healthchecks, API/IA sin puertos del host, Nginx HTTP en loopback 8080 y MongoDB en loopback 27018 con volumen; D-08 representa el destino endurecido, no ese perfil local exacto. `depends_on` no garantiza disponibilidad permanente y una IA inicialmente insalubre puede bloquear el arranque de API. Se fijaron Python por digest y dependencias relevantes; otras etiquetas base siguen siendo mutables, sin garantía binaria global.

## 5. Seguridad y recuperación

Las altas API generan credencial temporal de un uso de 24 horas; el titular define contraseña de 12–256 caracteres, no solo espacios, protegida con Scrypt y sal de 16 bytes (`n=2^17`, `r=8`, `p=1`). Sesiones Bearer opacas de una hora, logout revocable y versionado de autorización evitan que un cambio de rol/habilitación reactive sesiones antiguas. Credenciales temporales y tokens se almacenan mediante digest; la configuración privada queda fuera de Git.

La renovación administrativa solo sirve a cuentas pendientes e invalida la credencial anterior. Los fallos de publicación de auditoría en cuentas/sesiones no ocultan operaciones ya persistidas; sus intenciones se recuperan sin duplicar eventos. La demo opt-in crea cuentas/mensajes ficticios de forma repetible y no modifica usuarios existentes.

Amenazas y límites: exposición de tokens/credenciales, abuso de login, acceso directo a MongoDB y sesgo del corpus. Mitigaciones existentes: respuestas permitidas, hashes, `no-store`, roles, datos sintéticos y revisión humana. TLS fuera de local, control de intentos y permisos mínimos MongoDB siguen pendientes; no hay inmutabilidad absoluta frente a administradores directos. La CLI de bootstrap conserva una posible respuesta ambigua si falla publicar después de insertar; consta como defecto pendiente, no se corrigió durante documentación.

## 6. Dataset, experimentación y resultados IA

Datos propios ficticios en español, redactados con asistencia de IA, sin fuentes externas ni correos reales. **80 train / 24 validation / 24 test**, balance de cuatro categorías; versiones anteriores preservadas. Se documentan procedencia y limitaciones en [datos](../ai_service/data/README.md); no se presume una licencia de distribución general ausente.

El control histórico de calidad registró 128 IDs y textos normalizados únicos, sin duplicados exactos, y conservación de los 40 registros v0.1 y 80 de v0.2. La máxima similitud de caracteres observada entre particiones fue 0,533 (`SYN-086`, train, frente a `SYN-090`, validation): no descarta parentesco semántico ni plantillas. Tampoco puede demostrarse que el contenido de test nunca se inspeccionó al ampliar el corpus; la separación de ajuste/selección en código no prueba por sí sola independencia histórica absoluta.

El preprocesamiento normaliza espacios. TF-IDF de unigramas/bigramas y regresión logística se ajustan en `Pipeline` solo con train. Validation selecciona regularización `C` por Macro-F1 y log-loss; la referencia usa `C=30`, semilla 42 y `max_iter=1000`. Baseline: clase más frecuente.

El umbral Compose **0,45** es provisional, no óptimo demostrado; no reemplaza silenciosamente H-01=0,70. En test, 20/24 casos se asignarían automáticamente y 4 pasarían a revisión; los 20 automáticos coinciden con sus etiquetas. El único error de clasificación global es `SYN-040` (Recursos Humanos→Facturación). La precisión de enrutamiento es una simulación sobre esa muestra, no un indicador empresarial.

En validation, 0,40 asignó 21/24 casos con 21 aciertos automáticos, frente a 20/24 con 20 aciertos a 0,45. El objetivo/costo de envío incorrecto frente a revisión humana requiere aprobación explícita del equipo; esos porcentajes no bastan para escoger un óptimo ni autorizan ajustar con test. El reporte de IA conserva la sensibilidad completa sin duplicar aquí todas sus tablas.

La [evaluación](09_evaluacion_final_ia.md) incluye métricas por clase, matrices, análisis de errores, baseline y huellas. Los [tres notebooks](../ai_service/notebooks/README.md) reutilizan módulos Python y generaron las [dos figuras reales](evidencias/ia/README.md). Test está separado de selección, pero ya fue observado: una reproducción no es una nueva prueba ciega.

Build entrena en una etapa cacheable y promueve un bundle con manifiesto. Inferencia no depende de Jupyter. El `.joblib` está en la imagen, no en Git; se reconstruye o entrega como ZIP controlado junto al manifiesto/reporte. La equivalencia funcional se comprobó; no se promete serialización idéntica. La tasa de correcciones humanas y nueva latencia del artefacto actual siguen pendientes.

## 7. Pruebas y calidad

El [plan/resultados](PLAN_Y_RESULTADOS_PRUEBAS.md) distingue **ejecutada con evidencia**, **definida y pendiente** y **no aplicable justificada**. Reutiliza los scripts técnicos sin repetirlos durante este cierre. Las evidencias IA sí se contrastaron ahora con fuentes y huellas; OpenAPI se exportó de `app.openapi()` sin conexión a MongoDB.

Resultados técnicos previos: inicialización idempotente, filtros combinados, correcciones múltiples, preservación original, concurrencia/CAS, recuperación de auditoría, permisos, activación/renovación/revocación, demo opt-in, IA malformada/timeout y smoke HTTP con cuatro servicios efímeros. Compilación frontend y auditoría npm pasaron en el cierre técnico. El registro de defectos relaciona correcciones con commits reales.

La aprobación «con observaciones» de la línea documental `aa2e12c` no acreditaba software. La revisión de la primera implementación `0641fd5` sí observó cuatro servicios saludables, siete operaciones API, aceptación HTTP en base temporal, build Docker y pantalla pública de acceso, pero detectó incumplimientos que impedían entonces recomendar la fusión. No se heredan como ausencias actuales los componentes incorporados después; la evolución relevante es:

| Hallazgo inicial | Resolución y estado vigente |
|---|---|
| B-01 y M-05: faltaban altas/activación, auditoría de acceso y revocación | `5443006` incorporó cuentas/sesiones; `3f9a067` añadió recuperación segura ante publicación fallida. Pruebas técnicas previas; aceptación visual pendiente |
| B-02/B-03 y A-01: historia sobrescrita, corrección en gestión rechazada y filtros incompletos | `e48ff3f`: eventos separados, snapshots, correcciones sucesivas y filtros; lectura de legados sin migración. No implica inmutabilidad frente a administradores MongoDB |
| A-03/A-05: faltaban esquema físico y metadatos | `d657e7a` y `e48ff3f`: validadores/índices e información de predicción/asignación. `model_metadata` está preparada, no poblada automáticamente; persiste el parcial RF-04 sin predicción |
| A-04 y M-02: modelo/reporte divergentes y notebooks ausentes | `3f9a067`: bundle/manifiesto, entorno fijado, LF, evaluación del servido y notebooks compartidos. La comparación de umbrales ya está incluida en la imagen; binario fuera de Git |
| M-01/M-04: auditoría no incluida en detalle y discrepancia CSS/Tailwind | Contrato vigente separa detalle y consulta administrativa; se conserva CSS según decisión del equipo. No se agrega acceso de operador a auditoría ni se rehace la interfaz |
| M-03 y aviso alto de dependencias: TS2688 por tipado Node/Vite | `3f9a067`: tipado Node explícito y Vite 6.4.6; compilación y revisión npm técnicas previas, no repetidas en esta consolidación |
| A-02/A-06: umbral sin criterio definitivo y cobertura insuficiente | Provisionalidad/limitaciones explícitas; nuevas suites cubren fallos, carreras y contratos, pero no cierran unitarias completas, UI ni aprobación del umbral |

Los identificadores B/A/M se conservan solo para localizar los hallazgos originales en Git; no reemplazan los IDs DEF ni repiten el [registro operativo del plan](PLAN_Y_RESULTADOS_PRUEBAS.md#registro-de-defectos-y-correcciones).

Como evidencia histórica separada, la revisión de `0641fd5` registró las siguientes mediciones en contenedores, con el servicio IA que entonces identificaba `/health` como `tfidf-logreg-9b111546ffbd08b1`. Son cifras transcritas del informe original, no reejecutadas ni atribuibles al artefacto actual `4899…`:

| Operación histórica | n secuencial | Mediana | p95 | Alcance |
|---|---:|---:|---:|---|
| POST `/api/v1/messages` | 30 | 14,48 ms | 19,83 ms | HTTP desde el contenedor API; incluye registro, persistencia, inferencia y enrutamiento |
| GET `/api/v1/messages` | 30 | 7,57 ms | 9,54 ms | HTTP desde el contenedor API y consulta MongoDB; no navegador |
| POST interno `/predict` | 24 | 3,399 ms | 4,384 ms | Inferencia HTTP interna; no equivale a flujo extremo a extremo |

No se caracterizaron suficientemente hardware/carga para extrapolar esos valores; no se mezclan con la corrida posterior `b020…` del plan ni con las antiguas cifras del documento IA. Lighthouse de la pantalla pública reportó accesibilidad/buenas prácticas 1,00 y SEO 0,60, con observaciones de meta descripción y `robots.txt`; es evidencia histórica de login, no conformidad de accesibilidad de todas las pantallas ni requisito SEO del MVP interno. La comprobación de hashes host/contenedor de aquella revisión vinculaba sus resultados al código examinado; se consultaron solo metadatos de MongoDB, sin leer cuentas/mensajes de demo ni modificar su volumen.

No hay cobertura unitaria exhaustiva ni acta de aceptación autenticada en navegador. La corrida de rendimiento histórico se documenta con n, percentiles, entorno y versión anterior, sin atribuirla al modelo actual ni mezclarla con latencia IA antigua. Los logs integrales saneados deben conservarse en la prueba final.

También permanecen por formalizar pruebas de MongoDB no disponible, carga concurrente, compatibilidad entre navegadores y automatización CI; las carreras controladas de actualización no sustituyen una prueba de carga. Las validaciones estáticas de enlaces/IDs/XML y las observaciones de diseño no son mediciones de comportamiento de la aplicación. Los estados y defectos todavía abiertos de CLI, OpenAPI y preparación sin predicción se mantienen en el plan; no se resuelven por esta reorganización.

## 8. Reproducción y operación

El [README principal](../README.md) contiene clonación, `docker compose up -d --build --wait`, acceso y bootstrap/demo. El [manual técnico](MANUAL_TECNICO.md) explica entorno, salud, persistencia, pruebas y diagnóstico; el [manual de usuario](MANUAL_USUARIO.md), las pantallas reales.

La API actual dispone de trece operaciones documentadas en [OpenAPI generado](openapi.json) y Swagger en `http://127.0.0.1:8080/docs`; el contrato vivo es `/openapi.json`. Varias respuestas de error y el 422 seguro de acceso requieren declaraciones explícitas futuras en código; el exportado no se editó manualmente. No se alteró la aplicación para documentarla.

## 9. Entregables y aceptación académica

| Apartado | Entregable/criterio | Estado al cierre documental |
|---|---|---|
| 17.7 | Integración persistencia/IA, API, HU y entradas inválidas | Ejecución técnica previa; repetir y guardar acta integral definitiva |
| 17.7 | Pruebas unitarias de servicios/reglas | Parcial; casos aislados definidos y pendientes, no equiparar con aceptación |
| 17.7 | Evaluación independiente y rendimiento básico | Evaluación curada; test separado ya observado; rendimiento histórico contextualizado |
| 17.7 | Defectos vinculados a correcciones | Registro documental con commits y pendientes explícitos |
| 17.8 | Visión, SRS/backlog, matriz, modelo de datos | Disponibles y alineados; visión preservada como línea base |
| 17.8 | Prototipos y diagramas | Seis SVG y nueve fuentes UML/C4 preservados; renderizado pendiente; TikZ por confirmar |
| 17.8 | Git, aplicación, servicio IA, datos/modelo y Docker | Fuentes/receta versionadas, ejecución técnica previa; binario reconstruible/no incluido en Git |
| 17.8 | OpenAPI, manuales e informe de métricas | Documentos y exportación disponibles; limitaciones del contrato explicitadas |
| 17.8 | Video/demo | Pendiente de fase posterior; no se preparó guion |
| 17.9 | Flujo principal, errores, reproducibilidad y requisitos/pruebas | Demostrado técnicamente por HTTP; aceptación UI integral y revisión humana finales pendientes |

## 10. Conclusiones y trabajo futuro

El MVP materializa la separación software/IA y permite continuar manualmente sin predicción, preservando trazabilidad. La evaluación sintética permite comprobar la integración y comparar baseline; no permite prometer ahorro de trabajo ni seguridad/desempeño productivo.

Antes de aceptar la entrega se requiere revisar documentos, completar los parciales obligatorios y probar el recorrido integral sin cambios manuales de código. Después podrán considerarse corpus autorizado más representativo, evaluación nueva, calibración y despliegue endurecido. Integraciones de correo, multiorganización y alta disponibilidad continúan fuera del alcance.

## 11. Referencias y procedencia

- Guía local: *Proyectos de Ingeniería de Software + IA, Colección III*, Proyecto 15, secciones 17.1–17.9, páginas impresas 51–53. El PDF está en `referencias/` del equipo, carpeta ignorada; **no se afirma publicado en GitHub**. No se inventan autor/editor/año bibliográfico.
- [FastAPI / OpenAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), [MongoDB/PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/).
- [scikit-learn: Pipeline y evaluación](https://scikit-learn.org/stable/), [Jupyter](https://docs.jupyter.org/), [Docker Compose](https://docs.docker.com/compose/).
- [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/docs/), [Vite](https://vite.dev/), [arc42](https://arc42.org/).
- Materiales auxiliares del equipo: el DOCX de épicas/HU se utilizó solo como patrón de estructura; el laboratorio DriveGuardLab, como referencia pedagógica de módulos/notebooks/API. Su revisión registrada fue de solo lectura: no se ejecutaron scripts ni se copiaron su dominio, modelos, imágenes o configuración privada. Estos materiales locales no se presumen publicados en GitHub.
- Procedencia histórica: los cuatro informes preliminares se consolidaron en este documento y se retiraron por decisión expresa del equipo. Su contenido íntegro permanece en el commit documental **`a9c5159`**, anterior a esta reorganización; la auditoría documental identificó `aa2e12c` y la primera revisión técnica, `0641fd5`. Para recuperar un original se puede consultar `git ls-tree -r --name-only a9c5159 docs/` y después `git show a9c5159:<ruta_del_informe>`, sin restablecerlo ni interpretar su dictamen como actual.
