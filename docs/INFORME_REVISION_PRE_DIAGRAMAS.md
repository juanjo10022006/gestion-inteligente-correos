# Informe de revisión pre-diagramas (1B2)

## Hallazgos y acciones
| Hallazgo | Severidad | Archivo/sección | Acción | Estado |
|---|---|---|---|---|
| Faltaban fichas detalladas de épicas e historias. | Alta | Gestión de requisitos | Se creó `05_epicas_y_hu.md` con 5 épicas, 14 fichas y equivalencia EP/EPI. | Corregido |
| El backlog duplicaba criterios y contenía sprints/días. | Alta | `03_backlog.md` | Se convirtió en índice ejecutivo con enlaces a fichas y se retiraron referencias temporales. | Corregido |
| La visión contenía duración de desarrollo y orden de flujo impreciso. | Media | `01_vision_alcance.md` | Se eliminó la duración y se alineó el flujo con persistencia `RECIBIDO` previa a IA. | Corregido |
| Faltaban arc42, ADR, modelo conceptual e índice documental. | Alta | `06`–`08`, `README` | Se crearon documentos textuales y conceptuales, sin artefactos ejecutables ni visuales. | Corregido |
| La matriz no mostraba la épica asociada. | Baja | `04_matriz_trazabilidad.*` | Se incorporó EPI/HU con las mismas relaciones en Markdown y CSV. | Corregido |
| Umbral H-01, dataset lícito y política detallada de contraseñas permanecen sin validar. | Media | SRS, ADR y modelo | Se conservan como decisiones/hipótesis pendientes; no se inventó una respuesta. | Pendiente de revisión humana |

## Evidencia real y aprobación
| Entregable | Evidencia real | Aprobación requerida |
|---|---|---|
| Épicas e HU | 5 fichas EPI y 14 fichas HU verificadas por conteo. El DOCX se consultó solo como patrón de estructura. | Revisar contenido |
| Backlog y visión | Índice ejecutivo y flujo ajustado; no se detectaron sprints ni cronogramas en entregables. | Revisar contenido |
| Matriz | 15 filas CSV; IDs y nueve contratos REST coinciden con Markdown y SRS. | Revisar contenido |
| Arc42, ADR y modelo | Documentación textual/conceptual creada; no hay diagramas, prototipos, esquemas físicos ni implementación. | Aprobar fase 1C si procede |

## Verificaciones ejecutadas

- Conteo: 5 encabezados `EPI-*`, 14 encabezados `HU-*` y 15 filas de datos CSV.
- Comparación de expresiones de endpoint: 9 rutas `/api/v1/` idénticas entre SRS, matriz Markdown y CSV.
- Comparación de conjuntos `OBJ`, `RF`, `RNF`, `RN`, `EPI`, `HU`, `UI` y `CP`: sin diferencias entre ambas matrices.
- Búsqueda en entregables: sin sprints ni cronogramas de desarrollo; sin archivos `.mmd`, `.puml`, SVG o imágenes.

La documentación permanece en fase pre-diagramas. No se ejecutó la fase 1C.
