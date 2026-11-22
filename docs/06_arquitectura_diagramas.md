# Arquitectura arc42 — fase 1C

## 1. Introducción y objetivos
La arquitectura soporta OBJ-01 a OBJ-08 y, en especial, trazabilidad, seguridad, disponibilidad ante fallo IA y reproducibilidad (RNF-01 a RNF-12). La IA asiste; el operador conserva control.
## 2. Restricciones
React/TypeScript/Vite/Tailwind, FastAPI/Pydantic, MongoDB/PyMongo y scikit-learn con TF-IDF y regresión logística son decisiones del equipo. Solo roles OPERADOR/ADMINISTRADOR, cuatro categorías, seis estados y rutas públicas `/api/v1/`. No hay buzones externos, adjuntos ni datos personales reales.
## 3. Contexto y alcance
Operador y administrador son los únicos actores externos y usan el sistema mediante la aplicación web. El servicio IA y MongoDB forman parte interna del sistema; no existen integraciones con Gmail/Outlook, SMTP ni otros sistemas externos en el MVP. Ver [D-01](diagramas/D-01_contexto_c4.mmd) y [D-04](diagramas/D-04_casos_uso.puml).
## 4. Estrategia de solución
La interfaz consume API REST; la API persiste el mensaje y audita antes de invocar IA. El servicio desacoplado devuelve categoría, confianza y versión; MongoDB conserva documentos operativos y eventos. Un fallo IA deriva a gestión manual.
## 5. Vista de bloques
| Bloque | Responsabilidad | Contrato |
|---|---|---|
| Web | Formularios, bandeja y detalle; muestra estados | HTTPS a `/api/v1/` |
| API/Auth | Sesión, roles y activación | contratos de `02_srs.md` |
| API/Mensajes | Validar, persistir, consultar y estados | `/api/v1/messages` |
| API/Clasificación | Preprocesar, invocar IA, aplicar RN-03–05 | contrato interno IA |
| API/Auditoría | Eventos solo de adición y consulta administrativa | `/api/v1/audit-events` |
| Persistencia | Usuarios, mensajes, eventos y metadatos | modelo conceptual `08` |
La separación se representa en [D-02](diagramas/D-02_contenedores_c4.mmd), [D-03](diagramas/D-03_componentes_backend.puml) y [D-09](diagramas/D-09_datos_conceptual.mmd).
## 6. Vista de ejecución
`POST /api/v1/messages` valida, persiste `RECIBIDO` y audita creación; prepara texto; consulta IA; actualiza a `CLASIFICADO`, `PENDIENTE_REVISION` o `PENDIENTE_CLASIFICACION` y audita. El operador puede asignar manualmente con motivo; se conserva predicción original cuando existe.  
El orden y las transiciones se detallan en [D-05](diagramas/D-05_secuencia_principal.puml) y [D-06](diagramas/D-06_estados.puml).
## 7. Vista de despliegue
Se propone una interfaz web, API, servicio IA y MongoDB en contenedores y red privada; es un diseño futuro, no un despliegue realizado. Secretos se inyectarán fuera del repositorio.
La representación propuesta está en [D-08](diagramas/D-08_despliegue_propuesto.mmd).
## 8. Conceptos transversales
HTTPS, hash con sal, credenciales temporales de un uso, autorización por rol y auditoría sin secretos. Errores usan códigos HTTP definidos. El pipeline NLP y artefacto de modelo deben versionarse; H-01=0,70 requiere validación.
El flujo de datos/modelo propuesto está en [D-07](diagramas/D-07_pipeline_ia.mmd).
## 9. Decisiones arquitectónicas
Las decisiones propuestas se documentan en [07_decisiones_tecnicas.md](07_decisiones_tecnicas.md): MongoDB frente a PostgreSQL, desacoplamiento IA, persistencia previa e indisponibilidad.
## 10. Requisitos de calidad
RNF-01–12 son fuente de criterios. Rendimiento p95 ≤2 s para consulta y ≤5 s para clasificación son objetivos de diseño, no resultados. CP-01–10 definen evidencia futura.
## 11. Riesgos y deuda técnica
Datos sin licencia/sesgo, modelo indisponible, umbral sin validar, crecimiento de auditoría y madurez de seguridad requieren validación posterior. No se han medido métricas ni entrenado modelos.
## 12. Glosario y representaciones
**Predicción:** salida IA; **asignación manual:** decisión humana origen `MANUAL`; **auditoría:** evento inmutable; **estado:** etapa RN-02.  
D-01 a D-09 tienen fuente editable en `docs/diagramas/`. Son representaciones de diseño, no evidencia de arquitectura desplegada ni modelo evaluado.
