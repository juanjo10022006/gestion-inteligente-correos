# Informe de auditoría documental y arquitectónica — fase 1D

**Proyecto:** Sistema inteligente de clasificación de correos corporativos

**Equipo:** Juan Camilo Gonzales y Juan Jose Solarte

**Base auditada:** commit `aa2e12c` (`docs(arquitectura): consolidar requisitos diagramas y prototipos`)

## 1. Resumen ejecutivo y dictamen

**Dictamen: Aprobado con observaciones, exclusivamente en su estado documental.**

La línea base cubre de forma coherente el problema, los seis módulos del Proyecto 15, requisitos, historias, trazabilidad, contratos REST, arquitectura arc42, modelo conceptual MongoDB, nueve diagramas y seis prototipos. El flujo crítico conserva el mensaje y audita su creación antes de consultar IA; también diferencia baja confianza, fallo de IA y corrección humana.

El dictamen no acredita software ejecutable. Frontend, API, servicio IA, MongoDB físico, notebooks, dataset, modelo, Docker Compose, OpenAPI, pruebas ejecutadas, métricas, manuales y demostración siguen pendientes. Antes de implementar deben resolverse la fuente/licencia del dataset, la política de autenticación y el estado formal de algunas decisiones.

## 2. Fuentes y método

- Fuente académica leída: Proyecto 15, secciones 17.1–17.9, páginas impresas 51–53; también se contrastó la orientación general aplicable.
- Documentación auditada selectivamente: visión, SRS, backlog, matriz MD/CSV, fichas HU, arc42, ADR, modelo de datos, prototipos, diagramas y README.
- `referencias/Laboratorio DriveGuardLab.zip` se examinó en solo lectura mediante listado del ZIP y lectura de encabezados/importaciones de README y notebooks. No se ejecutó ni extrajo código, no se abrieron imágenes/modelos y no se leyó su `.env`.
- Estado inicial de Git: limpio; commit `aa2e12c`.

## 3. Matriz de auditoría

| Criterio | Estado | Evidencia concreta / método | Severidad | Acción o decisión |
|---|---|---|---|---|
| Seis módulos del Proyecto 15 | Cumple documentalmente | `README.md`; alcance de `01_vision_alcance.md`; PDF 17.2: bandeja, preprocesamiento, clasificación, enrutamiento, estados y auditoría | — | Mantener autenticación/usuarios como funciones transversales. |
| Actores del MVP | Cumple documentalmente | `02_srs.md` §1 y RN-06; D-01/D-04: `OPERADOR` y `ADMINISTRADOR` | — | La ausencia de autoservicio externo es una decisión de alcance válida; “usuario final” es sugerido, no obligatorio, en 17.2. |
| Categorías y estados | Cumple documentalmente | RN-01 y RN-02; D-06; UI-04/UI-05 | — | Validar catálogos físicamente al implementar. |
| IDs y cobertura | Cumple documentalmente | Se verificaron OBJ-01..08, RF-01..13, RNF-01..12, RN-01..08, EPI-001..005, HU-01..14, CP-01..10 y UI-01..06 | — | Conservar numeración. |
| Fichas HU | Cumple documentalmente | 14 fichas, 14 prioridades y 14 bloques de escenarios verificados | — | Convertir escenarios en pruebas de aceptación durante implementación. |
| Matriz MD/CSV | Cumple documentalmente | Conjuntos de IDs equivalentes y 9 contratos REST coincidentes con SRS | — | Automatizar esta comprobación en CI futuro. |
| Contratos `/api/v1/` | Cumple documentalmente | `02_srs.md` §5 y matriz; contrato IA interno separado | — | Generar OpenAPI desde FastAPI sin exponer el contrato IA como API pública. |
| arc42 | Cumple documentalmente | 12 secciones y enlaces D-01..D-09 verificados | — | Completar detalles operativos cuando exista infraestructura real. |
| Diagramas y prototipos | Cumple documentalmente | 4 PlantUML, 5 Mermaid y 6 SVG; el usuario confirmó revisión visual | — | Mantener fuentes editables junto con exportaciones futuras. |
| Renderizado automático de diagramas | No verificable aún | No hay Mermaid CLI, PlantUML CLI ni `plantuml.jar`; solo se validó estructura estática | Menor | Renderizar en CI o herramienta académica antes de entrega final. |
| Exigencia “TikZ/UML/C4” | Cumple parcialmente | Se entregan UML/C4 mediante PlantUML/Mermaid, no fuente TikZ | Decisión pendiente | Confirmar con el docente si “TikZ/UML/C4” exige TikZ o admite cualquiera de esos formatos. |
| Flujo persistencia → IA | Cumple documentalmente | RF-03..07, RN-02..05, D-05: validar → `RECIBIDO` → evento → preprocesar → IA | — | Proteger el orden con prueba de integración/transacción parcial. |
| Autenticación en secuencia principal | Cumple parcialmente | RF-03 exige sesión; D-05 comienza en la solicitud y no muestra verificación explícita de sesión/rol | Menor | Tratar autenticación como precondición o hacerla explícita en pruebas/implementación. |
| Fallo y baja confianza | Cumple documentalmente | RF-06/07, CP-04/10, D-05/D-06; no se inventa categoría ni confianza | — | Mantener H-01 configurable. |
| Predicción original y asignación efectiva | Cumple documentalmente | `08_modelo_datos_preliminar.md` y D-09 las separan; RN-07 conserva before/after | — | Implementar validadores y eventos inmutables. |
| Modelo MongoDB conceptual | Cumple documentalmente | Usuarios, mensajes, eventos y metadatos; embed/ref e índices candidatos documentados | — | Diseñar validaciones e inicialización idempotente antes de persistencia física. |
| MongoDB frente a PostgreSQL | Cumple parcialmente | ADR-01 justifica MongoDB, pero su estado sigue “pendiente de validación” y SRS §1 aún dice que falta justificación formal | Importante | Formalizar ADR-01 como decisión aceptada o reabrirla; después corregir el texto obsoleto del SRS. |
| Seguridad de autenticación | Cumple parcialmente | Roles, activación, hash con sal, credencial de un uso y auditoría sin secretos están especificados | Importante | Definir algoritmo/parámetros de hash, política de contraseña, expiración/revocación de credencial y token, y autorización endpoint por endpoint. |
| Privacidad y datos demo | Cumple documentalmente | RNF-09, exclusiones y riesgos de visión/SRS | — | No usar correos personales o corporativos reales sin autorización. |
| Seguridad del repositorio | Cumple documentalmente | 31 archivos rastreados; sin `.env`, ZIP, dataset/modelos ni claves de alto riesgo detectadas; `referencias/` está ignorada | — | Mantener `.env` fuera de Git y publicar solo `.env.example` seguro. |
| Dataset NLP | No verificable aún | No existe fuente, licencia, versión ni perfil de calidad aprobado | Bloqueante | Seleccionar o construir datos lícitos; documentar licencia, anonimización, duplicados, distribución y sesgos antes de entrenar. |
| H-01 = 0,70 | No verificable aún | Marcada consistentemente como hipótesis en SRS, ADR y diagramas | Decisión pendiente | Evaluarla con validación y análisis de costo de errores; no ajustarla con test. |
| Pipeline IA | Cumple documentalmente | D-07 separa entrenamiento, validación y test; HU-14/CP-09 exigen baseline y reproducibilidad | — | Implementar funciones reutilizables y test reservado. |
| Métricas IA y operativas | No verificable aún | Macro-F1, precisión de enrutamiento, latencia y correcciones son objetivos futuros, no resultados | Importante | Medir offline y extremo a extremo por separado; no generalizar desde datos demo. |
| Estrategia de pruebas | Cumple parcialmente | CP-01..10 cubren aceptación, seguridad, resiliencia y evaluación prevista | Importante | Añadir pruebas unitarias, integración, contrato/API, sistema, entradas inválidas, rendimiento y registro de defectos/correcciones según 17.7. |
| Jupyter para experimentación | Cumple parcialmente | Decisión confirmada en esta auditoría; todavía no existen notebooks del proyecto | Importante | Adoptar los tres notebooks recomendados, reutilizando el mismo código Python que producción. |
| Servicio IA desacoplado | Cumple documentalmente | ADR-02, D-02/D-03 y contrato interno versionado | — | Cargar el artefacto una vez; no depender de Jupyter/Conda ni reentrenar por solicitud. |
| Docker Compose de cuatro servicios | Cumple parcialmente | D-08 representa `web`, `api`, `ai` y MongoDB en red privada; no existe Compose real | Importante | Definir imágenes, DNS interno, volumen, healthchecks, variables, dependencias y configuración segura al implementar. |
| Aceptación extremo a extremo | No verificable aún | 17.9 exige producto demostrable; el README declara correctamente que no está implementado | Bloqueante para aceptación final | Implementar, ejecutar CP y conservar evidencia antes de afirmar aceptación. |

## 4. Cobertura de la guía del Proyecto 15

| Sección académica | Documentado ahora | Pendiente de construir o medir |
|---|---|---|
| 17.1 Objetivo | Visión, problema, objetivos y límites | Evidencia del producto integrado |
| 17.2 Usuarios y módulos | Dos roles adoptados, seis módulos y RNF | Validación con usuarios/pruebas de aceptación |
| 17.3 Arquitectura | arc42, D-01..D-09, REST, IA interna y MongoDB | Servicios ejecutables, observabilidad y configuración real |
| 17.4 Tecnologías | Stack elegido y sustitución de PostgreSQL justificada | Formalizar estado de ADR-01 y compatibilidades de versiones |
| 17.5 Implementación | Flujo, HU, contratos y diseño de datos | Código, dataset, EDA, baseline, modelo, integración, CI y despliegue |
| 17.6 Flujo extremo a extremo | D-05 y reglas de resiliencia | Demostración ejecutada |
| 17.7 Pruebas | CP-01..10 y trazabilidad previstas | Suites ejecutadas, rendimiento, test IA independiente y registro de defectos |
| 17.8 Entregables | Visión, SRS/backlog, matriz, prototipos, diagramas, modelo conceptual y repositorio Git | Aplicación, IA, datos/instrucciones, artefacto, OpenAPI, Docker, manuales, métricas y video/demo |
| 17.9 Aceptación | Criterios definidos | Flujo funcionando, baseline comparado, reproducibilidad y errores manejados sin cambios manuales |

La frase “diagramas TikZ/UML/C4” se interpreta provisionalmente como formatos aceptables de diagramación; la necesidad específica de entregar TikZ debe confirmarse.

## 5. Consistencia del diseño

### Flujo y resiliencia

SRS, HU-03/HU-06..11, CP-01/03/04/06/10, arc42, D-05/D-06 y D-09 coinciden en:

1. validar entrada y exigir sesión;
2. persistir `RECIBIDO` y el evento de creación antes de IA;
3. conservar texto original y versionar preprocesamiento;
4. validar categoría, confianza y versión;
5. guardar predicción original si la respuesta es válida;
6. usar `PENDIENTE_REVISION` bajo H-01 y `PENDIENTE_CLASIFICACION` ante fallo;
7. permitir asignación/corrección motivada sin sobrescribir predicción;
8. avanzar a `EN_GESTION` y cerrar desde allí, manteniendo RF-13 como Should.

No se encontró contradicción en estados, categorías o rutas. La omisión gráfica de la comprobación de sesión en D-05 es una precondición implícita, no un cambio de negocio.

### Datos y auditoría

El modelo conceptual diferencia predicción IA inmutable y asignación efectiva. Los actos automáticos usan actor `SISTEMA`; los humanos pueden referenciar `actorUserId`. Eventos separados evitan arreglos no acotados. Los índices son candidatos, no evidencia de MongoDB creado.

### Inconsistencias documentales localizadas

1. `02_srs.md` §1 afirma que la justificación MongoDB está pendiente, aunque ADR-01 ya contiene la comparación.
2. ADR-01 conserva estado “Propuesta pendiente de validación”, mientras las decisiones del equipo tratan MongoDB como adoptado.
3. `01_vision_alcance.md` denomina al servicio IA “sistema externo interno”; arc42 lo define correctamente como componente interno.

No se corrigieron durante la auditoría porque implican formalizar o aclarar decisiones; deben resolverse con aprobación del equipo.

## 6. Recomendación para IA con Jupyter

Se recomienda conservar Jupyter como entorno académico de análisis y evidencia, sin convertirlo en dependencia de ejecución:

- `ai_service/notebooks/00_verificacion_entorno.ipynb`: Python, librerías, rutas, artefactos y conectividad opcional sin mostrar secretos.
- `ai_service/notebooks/01_eda_dataset.ipynb`: procedencia/licencia, anonimización, limpieza, duplicados, faltantes, distribución de las cuatro categorías, sesgos y gráficas.
- `ai_service/notebooks/02_entrenamiento_evaluacion.ipynb`: partición reproducible, baseline, TF-IDF + regresión logística, selección con validación, matriz de confusión, precision/recall/F1 por clase, Macro-F1 y análisis de errores; test solo al final.
- `ai_service/src/` o `ai_service/scripts/`: funciones compartidas de carga, preparación, entrenamiento, evaluación y exportación. Los notebooks deben importarlas.
- Artefacto versionado: pipeline completo, clases, versión de datos, configuración, versiones de Python/scikit-learn y métricas reproducibles.
- El servicio `ai` carga el artefacto al iniciar y responde `{category, confidence, modelVersion}`; no entrena por request ni requiere Jupyter/Anaconda.

DriveGuardLab respalda únicamente el patrón pedagógico: notebook de entorno, experimentación, evaluación, módulos reutilizables, API, MongoDB y pruebas. No deben copiarse su CNN, imágenes, modelos, variables de entorno ni funcionalidades de visión.

## 7. Recomendación para Docker Compose y MongoDB

La ejecución integrada objetivo debe usar cuatro servicios:

| Servicio | Responsabilidad futura |
|---|---|
| `web` | Compilar/servir la SPA React y consumir únicamente la API pública configurada. |
| `api` | FastAPI/Pydantic/PyMongo; autenticación, reglas, estados y auditoría. |
| `ai` | Inferencia interna scikit-learn con artefacto versionado y healthcheck. |
| `mongo` | Persistencia privada con volumen; sin puerto público cuando no sea necesario. |

Recomendaciones para implementación:

- `compose.yaml` y Dockerfiles reproducibles; DNS interno por nombre de servicio, nunca `localhost` entre contenedores.
- `.env` privado ignorado y `.env.example` sin secretos.
- `MONGODB_URI` y `MONGODB_DB_NAME` consumidos por API y scripts; el host interno puede ser `mongo`.
- Healthchecks y dependencias basadas en salud, sin presentar `depends_on` como garantía absoluta de disponibilidad.
- `backend/scripts/init_db.py` futuro, idempotente, para validadores e índices; datos demo en operación separable.
- Compatibilidad explícita entre la versión de scikit-learn que exporta y la que sirve el artefacto.
- Jupyter/Anaconda opcionales en el equipo para experimentación; Compose es el modo de ejecución demostrable.
- Distinguir HTTP local de TLS previsto; no declarar puertos, imágenes o contenedores funcionales antes de probarlos.

No se requiere MongoDB Atlas, Kubernetes, Kafka ni infraestructura adicional para el MVP.

## 8. Seguridad y operabilidad

- No se detectaron archivos sensibles rastreados ni patrones de claves privadas, tokens GitHub/AWS o URI MongoDB con credenciales.
- `.gitignore` excluye `.env`, `.env.*` salvo `.env.example`, prompts locales y `referencias/`.
- DriveGuardLab contiene un `.env` dentro del ZIP ignorado. No se leyó y no debe copiarse ni versionarse.
- Deben definirse antes de autenticación real: política de contraseña, algoritmo/parámetros de hash, vigencia de credencial temporal, emisión/expiración/revocación de tokens y rotación de secretos.
- Los objetivos p95 y las métricas IA permanecen pendientes de medición.

## 9. Hallazgos priorizados

### Bloqueantes

1. **Dataset sin aprobación:** bloquea entrenamiento reproducible y cualquier afirmación de desempeño.
2. **Sistema no implementado:** bloquea aceptación académica 17.9, pero es coherente con la fase actual.

### Importantes

1. Formalizar ADR-01 y actualizar la frase obsoleta del SRS sobre MongoDB.
2. Definir política completa de autenticación y secretos.
3. Especificar y ejecutar pruebas por capas, rendimiento y registro de defectos.
4. Implementar el flujo Jupyter → código reutilizable → artefacto → servicio IA sin fuga de datos.
5. Completar operabilidad Compose: volumen, healthchecks, DNS, configuración e inicialización.
6. Separar métricas offline de IA de latencia, enrutamiento y correcciones end-to-end.

### Menores

1. Aclarar en visión que el servicio IA es interno.
2. Explicitar la sesión/rol como precondición del flujo D-05 o de su prueba.
3. Automatizar renderizado de Mermaid/PlantUML y validación de enlaces/IDs en CI.

### Decisiones pendientes

1. Confirmar si el docente exige fuente TikZ.
2. Validar H-01 con datos y costos de error.
3. Aprobar dataset/licencia y política de contraseñas/tokens.
4. Formalizar MongoDB como ADR aceptada.

## 10. Siguiente fase sugerida

Tras aprobación humana, iniciar implementación incremental manteniendo trazabilidad:

1. cerrar decisiones de datos, seguridad y ADR;
2. definir estructura de código y contratos compartidos;
3. preparar pruebas de aceptación derivadas de CP antes de implementar;
4. construir persistencia/API y flujo resiliente;
5. desarrollar notebooks y módulo NLP reutilizable;
6. integrar frontend, servicio IA y auditoría;
7. contenerizar los cuatro servicios y ejecutar pruebas extremo a extremo;
8. generar evidencia académica: OpenAPI, métricas, manuales y demo.

El orden expresa dependencias funcionales y no fija plazos.

## 11. Validaciones ejecutadas y limitaciones

**Ejecutado:**

- lectura del PDF académico y contraste de 17.1–17.9;
- inspección de solo lectura del ZIP DriveGuardLab, README y estructura de notebooks;
- conteo de IDs, fichas HU, prioridades, escenarios, secciones arc42, D y UI;
- equivalencia de IDs y 9 endpoints entre matriz MD/CSV y SRS;
- validación XML de 6 SVG con `viewBox`;
- validación estructural de 4 `.puml` y 5 `.mmd`;
- verificación del orden crítico de D-05, seis estados de D-06 y separación conceptual de D-09;
- comprobación de enlaces locales;
- revisión de rutas rastreadas y búsqueda de patrones de secretos;
- inspección de Git antes de modificar.

**No verificable todavía:**

- renderizado automático Mermaid/PlantUML por ausencia de herramientas locales;
- funcionamiento, seguridad dinámica, persistencia, healthchecks, latencias y pruebas;
- calidad del dataset, métricas IA, H-01 y compatibilidad del artefacto;
- aceptación extremo a extremo.

## 12. Archivos y acciones de esta auditoría

- Creado: `docs/INFORME_AUDITORIA_DOCUMENTAL.md`.
- No se modificaron requisitos, prioridades, contratos, diagramas, prototipos ni el modelo conceptual.
- No se creó código, notebook, dataset, base de datos, Dockerfile, Compose o infraestructura.
- No se ejecutaron scripts del laboratorio, aplicación, entrenamiento ni contenedores.
- No se realizó commit, push ni cambio de rama.
