# Prototipos UI — fase 1C

SVG editables para revisión visual; no son frontend implementado. Como decisión de diseño futura, en móvil la barra lateral se ocultaría, las tarjetas pasarían a una columna y las acciones conservarían un orden navegable por teclado.

| UI | Objetivo / actor | Campos, acciones, navegación y errores | Accesibilidad / RF-HU / endpoint |
|---|---|---|---|
| [UI-01](prototipos/UI-01_acceso.svg) | Acceso; operador, administrador | Usuario, contraseña, activar cuenta; de activación a acceso; error de credenciales sin revelar campo. | Etiquetas y error textual; RF-01, HU-01; `POST /api/v1/auth/login`, `POST /api/v1/auth/activate` |
| [UI-02](prototipos/UI-02_bandeja.svg) | Bandeja; operador, administrador | Búsqueda, filtros y paginación; abre detalle; estados vacío y error con reintento. | Controles etiquetados y paginación por teclado; RF-08, HU-04; `GET /api/v1/messages` |
| [UI-03](prototipos/UI-03_registro.svg) | Registro; operador, administrador | Asunto, cuerpo, remitente demo opcional; enviar y volver a bandeja; validación antes de envío. | Campos obligatorios y error textual; RF-03, HU-03; `POST /api/v1/messages` |
| [UI-04](prototipos/UI-04_detalle.svg) | Detalle; operador, administrador | Estado, categoría, confianza, versión o ausencia de predicción; navega a gestión. | Estado expresado en texto, no solo color; RF-05/09, HU-05/07; `GET /api/v1/messages/{id}` |
| [UI-05](prototipos/UI-05_gestion.svg) | Gestión; operador, administrador | Estado, departamento y motivo; guarda y retorna a detalle; error de transición/motivo. | Etiquetas, foco y mensaje textual; RF-10/11, HU-10/11; `PATCH /api/v1/messages/{id}/status`, `PATCH /api/v1/messages/{id}/classification` |
| [UI-06](prototipos/UI-06_auditoria_usuarios.svg) | Auditoría/cuentas; administrador | Filtros, eventos y creación de cuenta; operador recibe 403; crear cuenta muestra la credencial temporal una vez. | Roles y acceso denegado expresados en texto; RF-02/12, HU-02/13; `POST /api/v1/users`, `GET /api/v1/audit-events` |

Los prototipos muestran etiquetas visibles, contraste propuesto y errores textuales. La navegación por teclado, el foco, el comportamiento responsive y el cumplimiento de RNF-06 son decisiones previstas que deberán verificarse cuando exista frontend; los SVG estáticos no demuestran su implementación. No incluyen integraciones externas, adjuntos ni funciones excluidas.
