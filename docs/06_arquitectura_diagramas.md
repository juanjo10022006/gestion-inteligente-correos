# Arquitectura arc42 — MVP implementado

Contraste documental con `3f9a067`. Se conservan las doce secciones y las fuentes de diseño D-01…D-09; no constituyen por sí solas evidencia de ejecución. Véanse [manual técnico](MANUAL_TECNICO.md) y [plan](PLAN_Y_RESULTADOS_PRUEBAS.md).

## 1. Introducción y objetivos
La arquitectura soporta OBJ-01 a OBJ-08 y, en especial, trazabilidad, seguridad, disponibilidad ante fallo IA y reproducibilidad (RNF-01 a RNF-12). La IA asiste; el operador conserva control.
## 2. Restricciones
React/TypeScript/Vite con CSS (sin Tailwind), FastAPI/Pydantic, MongoDB/PyMongo y scikit-learn con TF-IDF y regresión logística son las tecnologías implementadas. Solo roles OPERADOR/ADMINISTRADOR, cuatro categorías, seis estados y rutas públicas `/api/v1/`. No hay buzones externos, adjuntos ni datos personales reales.
## 3. Contexto y alcance
Operador y administrador son los únicos actores externos y usan el sistema mediante la aplicación web. El servicio IA y MongoDB forman parte interna del sistema; no existen integraciones con Gmail/Outlook, SMTP ni otros sistemas externos en el MVP. Ver [D-01](diagramas/D-01_contexto_c4.mmd) y [D-04](diagramas/D-04_casos_uso.puml).
## 4. Estrategia de solución
La interfaz consume API REST; la API persiste el mensaje y audita antes de invocar IA. El servicio desacoplado devuelve categoría, confianza y versión; MongoDB conserva documentos operativos y eventos. Un fallo IA deriva a gestión manual.
## 5. Vista de bloques
| Bloque | Responsabilidad | Contrato |
|---|---|---|
| Web | Formularios, bandeja/detalle, gestión, cuentas y auditoría | HTTP loopback a `/api/v1/`; HTTPS pendiente no local |
| API/Auth | Sesión, roles y activación | contratos de `02_srs.md` |
| API/Mensajes | Validar, persistir, consultar y estados | `/api/v1/messages` |
| API/Clasificación | Preprocesar, invocar IA, aplicar RN-03–05 | contrato interno IA |
| API/Auditoría | Eventos solo de adición y consulta administrativa | `/api/v1/audit-events` |
| Persistencia | Usuarios, sesiones, mensajes y eventos; metadatos de modelo preparados | [modelo 08](08_modelo_datos_preliminar.md) |
La separación se representa en [D-02](diagramas/D-02_contenedores_c4.mmd), [D-03](diagramas/D-03_componentes_backend.puml) y [D-09](diagramas/D-09_datos_conceptual.mmd).
## 6. Vista de ejecución
`POST /api/v1/messages` valida, persiste `RECIBIDO` y audita creación; prepara texto; consulta IA; actualiza a `CLASIFICADO`, `PENDIENTE_REVISION` o `PENDIENTE_CLASIFICACION` y audita. El operador puede asignar manualmente con motivo; se conserva predicción original cuando existe.  
El orden y las transiciones se detallan en [D-05](diagramas/D-05_secuencia_principal.puml) y [D-06](diagramas/D-06_estados.puml).
## 7. Vista de despliegue
Compose implementa `web`, `api`, `ai` y `mongo`, con DNS interno, healthchecks y dependencias de salud. Nginx publica HTTP en `127.0.0.1:8080`; MongoDB publica `127.0.0.1:27018` y persiste en `mongo_data`; API/IA no publican puertos al host. Secretos/configuración privada no se versionan. Hubo smoke HTTP previo sobre un proyecto efímero, no despliegue productivo.
La representación de [D-08](diagramas/D-08_despliegue_propuesto.mmd) conserva el destino endurecido (HTTPS/MongoDB sin puerto host), no esa configuración local exacta.
## 8. Conceptos transversales
Scrypt con sal, credenciales temporales de 24 horas, sesiones opacas de una hora/revocación, roles y auditoría sin secretos están implementados. Cuentas pendientes admiten renovación administrativa; cambios confirmados mantienen intención durable de auditoría. HTTPS, permisos MongoDB restrictivos y control de intentos siguen pendientes no locales. Errores tienen manejo HTTP; el OpenAPI automático no declara aún todas las respuestas de runtime.
El flujo de diseño está en [D-07](diagramas/D-07_pipeline_ia.mmd); el entrenamiento real es una etapa Docker cacheable que promueve bundle/manifiesto y carga un modelo por proceso. Notebooks son un target académico separado. H-01=0,70 requiere validación; Compose usa 0,45 provisional.
## 9. Decisiones arquitectónicas
Las [decisiones ADR-01…11](07_decisiones_tecnicas.md) registran MongoDB frente a PostgreSQL, desacoplamiento, persistencia previa, fallos IA, acceso, umbral provisional, bundle verificado y demo opt-in.
## 10. Requisitos de calidad
RNF-01…12 conservan criterios: p95 ≤2 s consulta y ≤5 s clasificación. Hay rendimiento básico previo y CP-01…10 ejecutados técnicamente, con parciales; resultados y límites en el [plan](PLAN_Y_RESULTADOS_PRUEBAS.md). La aceptación de UI/accesibilidad, unitarias completas y carga productiva no se deduce del smoke HTTP.
## 11. Riesgos y deuda técnica
Persisten riesgos por datos sintéticos pequeños, falta de licencia general explícita, sesgo, probabilidades no calibradas, umbral sin aprobación experimental definitiva, crecimiento de intenciones de auditoría y madurez de seguridad. Sí se entrenó/evaluó el modelo; la [evaluación IA](09_evaluacion_final_ia.md) fija la procedencia. No se midió una tasa real de correcciones humanas. Una IA inicialmente insalubre puede impedir que Compose arranque API.
## 12. Glosario y representaciones
**Predicción:** salida IA conservada; **asignación manual:** decisión humana origen `MANUAL`; **auditoría:** evento de solo adición por API, no inmutabilidad absoluta; **estado:** etapa RN-02.
D-01…D-09 tienen fuente editable en `docs/diagramas/`. No hay fuentes TikZ ni renderizado acreditado de todos los diagramas; confirmar exigencia del formato con el profesor. [Catálogo y discrepancias históricas](diagramas/README.md).
