# Catálogo de diagramas editables

Las fuentes de esta carpeta son representaciones de diseño de la fase 1C; no son implementación ni evidencia de despliegue, entrenamiento o evaluación de IA. Las fuentes PlantUML contienen `title` y `legend`; las Mermaid declaran título en su cabecera. Esta tabla aporta la leyenda y trazabilidad de las fuentes Mermaid y complementa todas las fuentes.

| ID y fuente | Formato | Propósito y leyenda | RF/HU vinculados |
|---|---|---|---|
| [D-01](D-01_contexto_c4.mmd) | Mermaid | **Contexto C4 L1.** Presenta el sistema como una única caja frente a Operador y Administrador. Flechas: interacción; no existen dependencias externas ni proveedor de correo en el MVP. | RF-01, RF-02, RF-03, RF-08, RF-12; HU-01–05, HU-13 |
| [D-02](D-02_contenedores_c4.mmd) | Mermaid | **Contenedores C4 L2.** Delimita Web, API, IA y MongoDB dentro del sistema. `/api/v1/` conecta Web–API; IA y PyMongo son enlaces internos. | RF-01–12; HU-01–13 |
| [D-03](D-03_componentes_backend.puml) | PlantUML | **Componentes backend.** Muestra dependencias de Auth, Usuarios, Mensajes, Clasificación, Enrutamiento, Auditoría y Repositorios hasta MongoDB. | RF-01–12; HU-01–13 |
| [D-04](D-04_casos_uso.puml) | PlantUML | **Casos de uso UML.** Delimita el sistema; Administrador especializa a Operador y conserva casos exclusivos. Las asociaciones son líneas UML. | RF-01, RF-02, RF-03, RF-08–13; HU-01–05, HU-10–13 |
| [D-05](D-05_secuencia_principal.puml) | PlantUML | **Secuencia UML.** Explicita validar → persistir `RECIBIDO` → auditar → preprocesar/inferir → guardar resultado y evento → responder 201. | RF-03–07; HU-03, HU-06–09 |
| [D-06](D-06_estados.puml) | PlantUML | **Máquina de estados UML.** Representa los seis estados, asignaciones motivadas, corrección sin perder predicción y cierre Should. | RF-03, RF-06, RF-07, RF-10, RF-11, RF-13; HU-03, HU-08–12 |
| [D-07](D-07_pipeline_ia.mmd) | Mermaid | **Pipeline IA.** Separa entrenamiento, validación y test para evitar fuga; las métricas son futuras y no resultados medidos. | RF-04, RF-05; HU-06, HU-07, HU-14 |
| [D-08](D-08_despliegue_propuesto.mmd) | Mermaid | **Despliegue previsto.** Distingue entrada HTTPS y red privada; MongoDB no expone puerto y los secretos quedan fuera de Git. | RNF-01, RNF-04, RNF-05, RNF-12; HU-09, HU-14 |
| [D-09](D-09_datos_conceptual.mmd) | Mermaid | **Modelo conceptual MongoDB.** Separa predicción IA original de asignación efectiva y permite eventos automáticos `SISTEMA` sin actor humano obligatorio. | RF-02–07, RF-10–12; HU-02, HU-03, HU-06–13 |

## Validación de renderizado

En esta revisión se detectaron Java, Node y `npx`, pero no PlantUML JAR/CLI ni Mermaid CLI instalados en el repositorio o disponibles como comandos locales. Por tanto, el renderizado de `.puml` y `.mmd` permanece **pendiente de validación con renderizadores compatibles**; no se instalaron dependencias. Sí se verificaron estructura, referencias, estados, contratos y orden crítico mediante análisis local; el detalle está en [el informe de revisión](../INFORME_REVISION_DIAGRAMAS.md).
