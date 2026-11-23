# SRS — Especificación de requisitos de software

**Sistema:** clasificación de correos corporativos.
Inspirada en ISO/IEC/IEEE 29148 y en el Proyecto 15 (secciones 17.1–17.9).

**Estado de contraste:** MVP local del commit `3f9a067`; aceptación integral pendiente. Los criterios académicos no se consideran satisfechos solo por estar implementados.

## 1. Descripción general

El producto recibe mensajes de prueba por formulario, los valida y preprocesa, solicita una predicción a un servicio NLP y persiste el mensaje con su resultado. Operadores autorizados pueden buscarlo, cambiar su estado y corregir la categoría; administradores gestionan acceso y consultan auditoría.

**Límites:** no integra buzones externos ni transmite correos. El MVP local usa navegador, API REST HTTP detrás de Nginx, servicio IA interno y MongoDB en cuatro servicios Compose. HTTPS es requisito fuera de local, no está configurado en esta demo. MongoDB es decisión justificada en [ADR-01](07_decisiones_tecnicas.md), no una obligación del PDF; PostgreSQL sigue siendo alternativa válida. Modelo, dataset y reproducción se detallan en [evaluación IA](09_evaluacion_final_ia.md).

### Roles y permisos

| Rol | Permisos MVP |
|---|---|
| Operador | Registrar, consultar, filtrar, actualizar estado y corregir categoría. |
| Administrador | Permisos de operador, administrar usuarios/roles y consultar auditoría. |

Los únicos roles obligatorios del MVP son **operador** y **administrador**. No se define un rol de usuario final ni una vista de autoservicio en este alcance.

### Creación de usuarios y credenciales

Un administrador autenticado crea una cuenta con identificador único, rol (`OPERADOR` o `ADMINISTRADOR`) y habilitación configurable. La **credencial temporal de un solo uso** se entrega únicamente en esa respuesta autorizada (`Cache-Control: no-store`), sin auditoría del secreto ni consultas posteriores. El administrador la comunica por un canal aprobado fuera de la aplicación. El titular activa una cuenta habilitada antes de 24 horas y define una contraseña de 12–256 caracteres, no solo espacios. Se almacena hash Scrypt con sal; credenciales temporales y sesiones usan digest, nunca texto plano. La demo usa HTTP loopback; HTTPS sigue exigido fuera de local.

El flujo está implementado en API/React. La renovación administrativa de una cuenta **pendiente** invalida la credencial anterior; una cuenta activada no admite restablecimiento por esa ruta. Creación/activación persistidas responden éxito aunque falle publicar la auditoría, conservando la intención para reintento. La CLI local de bootstrap crea cuentas ya activas como excepción operativa. No hay canal automático de entrega.

## 2. Requisitos funcionales

| ID y nombre | Especificación verificable |
|---|---|
| **RF-01 Autenticación** | **Actor:** operador, administrador. **Prioridad:** Must. **Entradas:** identificador y secreto activado; para activación, credencial temporal de un solo uso y nueva contraseña. **Procesamiento:** activar cuenta o validar credenciales y emitir sesión autenticada. **Salidas:** identidad, rol o error sin revelar cuál campo falló. **Pre:** usuario activo; la activación requiere credencial temporal vigente. **Post:** sesión registrada en auditoría; una activación invalida la credencial temporal. **Validaciones:** campos obligatorios y contraseña conforme a política definida antes de implementar. **Aceptación:** una cuenta activada con credenciales válidas accede; credenciales inválidas devuelven 401. |
| **RF-02 Gestión de acceso** | **Actor:** administrador. **Prioridad:** Must. **Entradas:** identificador de usuario, rol y estado. **Procesamiento:** crear/actualizar usuario de prueba, asignar solo los roles permitidos y generar credencial temporal de un solo uso al crear la cuenta. **Salidas:** usuario sin secreto expuesto; la credencial temporal se muestra una sola vez en la sesión administradora. **Pre:** sesión administradora. **Post:** cambio auditable sin secreto; cuenta pendiente de activación al crearse. **Validaciones:** rol `OPERADOR` o `ADMINISTRADOR`, usuario único y estado válido. **Aceptación:** un operador recibe 403; la credencial temporal no aparece en consultas ni auditoría. |
| **RF-03 Registrar mensaje** | **Actor:** operador. **Prioridad:** Must. **Entradas:** asunto, cuerpo y remitente de prueba opcional. **Procesamiento:** validar, crear identificador, persistir primero el mensaje en `RECIBIDO` y registrar fecha, autor y evento; después inicia RF-04 a RF-07. **Salidas:** mensaje creado con el estado resultante del flujo de clasificación. **Pre:** sesión de operador. **Post:** el evento de creación queda registrado y el mensaje no se pierde aunque falle IA. **Validaciones:** asunto 3–160 caracteres; cuerpo 10–10.000; campos sin solo espacios. **Aceptación:** entrada válida retorna 201 e identificador; antes de invocar IA ya existe un registro `RECIBIDO`; inválida retorna 422 y no crea mensaje. |
| **RF-04 Preprocesar mensaje** | **Actor:** sistema. **Prioridad:** Must. **Entradas:** asunto y cuerpo válidos. **Procesamiento:** normalizar espacios y preparar el texto según pipeline versionado, sin alterar el original visible. **Salidas:** texto preparado y versión de preprocesamiento. **Pre:** RF-03 validado. **Post:** metadato disponible para clasificación. **Validaciones:** texto preparado no vacío. **Aceptación:** se conserva original y se registra versión de preparación. |
| **RF-05 Clasificar con IA** | **Actor:** sistema/servicio IA. **Prioridad:** Must. **Entradas:** texto preparado. **Procesamiento:** solicitar inferencia mediante contrato interno. **Salidas:** categoría, confianza [0,1], versión de modelo y estado. **Pre:** servicio disponible y modelo cargado. **Post:** predicción asociada al mensaje. **Validaciones:** categoría permitida y confianza numérica en rango. **Aceptación:** respuesta válida guarda los cuatro metadatos; respuesta inválida se trata como fallo controlado. |
| **RF-06 Enrutar clasificación** | **Actor:** sistema. **Prioridad:** Must. **Entradas:** predicción válida. **Procesamiento:** aplicar RN-03 y RN-04. **Salidas:** departamento asignado o cola `REVISION_MANUAL`. **Pre:** RF-05. **Post:** estado `CLASIFICADO` o `PENDIENTE_REVISION` y evento. **Validaciones:** departamento del catálogo. **Aceptación:** confianza < 0,70 no asigna automáticamente departamento. |
| **RF-07 Manejar IA no disponible** | **Actor:** sistema/operador. **Prioridad:** Must. **Entradas:** error, timeout o ausencia de modelo. **Procesamiento:** persistir mensaje sin predicción y marcarlo para revisión. **Salidas:** mensaje con estado `PENDIENTE_CLASIFICACION`. **Pre:** RF-03. **Post:** evento de fallo sin pérdida de mensaje. **Validaciones:** no inventar categoría/confianza. **Aceptación:** una simulación de indisponibilidad retorna resultado controlado y permite asignación manual posterior. |
| **RF-08 Consultar bandeja** | **Actor:** operador, administrador. **Prioridad:** Must. **Entradas:** texto, departamento, estado, intervalo de fechas y paginación opcionales. **Procesamiento:** filtrar solo mensajes autorizados. **Salidas:** lista paginada con resumen. **Pre:** sesión autorizada. **Post:** sin modificación. **Validaciones:** filtros de catálogo y paginación positiva. **Aceptación:** combina filtros y devuelve únicamente coincidencias. |
| **RF-09 Consultar detalle** | **Actor:** operador, administrador. **Prioridad:** Must. **Entradas:** identificador de mensaje. **Procesamiento:** recuperar original, estado, asignación, predicción y auditoría relacionada autorizada. **Salidas:** detalle o 404. **Pre:** sesión autorizada. **Post:** sin modificación. **Validaciones:** formato de identificador. **Aceptación:** detalle muestra confianza y versión si existen; un id inexistente retorna 404. |
| **RF-10 Gestionar estado** | **Actor:** operador, administrador. **Prioridad:** Must. **Entradas:** estado destino y motivo opcional. **Procesamiento:** validar transición según RN-02 y registrar evento. **Salidas:** estado actualizado. **Pre:** mensaje existente. **Post:** auditoría inmutable. **Validaciones:** estado y transición permitidos. **Aceptación:** transición inválida retorna 409 y no cambia el estado. |
| **RF-11 Corregir o asignar manualmente** | **Actor:** operador, administrador. **Prioridad:** Must. **Entradas:** categoría/departamento permitido y motivo obligatorio. **Procesamiento:** si existe predicción, conservarla y registrar la corrección; si no existe predicción (por RF-07), registrar una asignación manual con origen `MANUAL`. En ambos casos asignar destino. **Salidas:** clasificación efectiva actualizada. **Pre:** mensaje existente en `PENDIENTE_REVISION` o `PENDIENTE_CLASIFICACION`, o clasificación a corregir. **Post:** estado `EN_GESTION` y auditoría con antes/después o con predicción ausente. **Validaciones:** motivo 5–500 caracteres y departamento de RN-01. **Aceptación:** nunca se sobrescribe la predicción original; un mensaje sin predicción puede recibir departamento manual. |
| **RF-12 Consultar auditoría** | **Actor:** administrador. **Prioridad:** Must. **Entradas:** mensaje, actor, acción y fechas opcionales. **Procesamiento:** filtrar eventos de solo lectura. **Salidas:** lista ordenada por fecha descendente. **Pre:** sesión administradora. **Post:** sin modificación. **Validaciones:** filtros válidos. **Aceptación:** creación, clasificación, cambio de estado y corrección son consultables. |
| **RF-13 Cerrar mensaje** | **Actor:** operador, administrador. **Prioridad:** Should. **Entradas:** transición a `CERRADO` y resolución. **Procesamiento:** validar transición y registrar cierre. **Salidas:** mensaje cerrado. **Pre:** mensaje `EN_GESTION`. **Post:** auditoría de cierre. **Validaciones:** resolución 5–500 caracteres. **Aceptación:** no se permite cerrar un mensaje pendiente de revisión. |

## 3. Requisitos no funcionales

Se conservan los criterios académicos; su presencia no implica aceptación. El [plan](PLAN_Y_RESULTADOS_PRUEBAS.md) distingue evidencia previa, revisión documental y pendientes.

| ID | Requisito verificable |
|---|---|
| **RNF-01 Seguridad** | HTTPS en ambientes no locales; no exponer secretos en consultas ni auditoría. Excepciones de entrega explícita: token de login y credencial temporal en respuesta administrativa de un solo uso, con `no-store`. |
| **RNF-02 Autorización** | Toda operación protegida verificará sesión y rol; pruebas negativas deberán obtener 401 sin sesión y 403 sin permiso. |
| **RNF-03 Rendimiento** | **Objetivo de diseño:** con dataset demo y carga definida en el plan de pruebas, p95 de consulta ≤2 s y clasificación síncrona ≤5 s; se medirá, no se afirma logrado. |
| **RNF-04 Disponibilidad y fallos** | Un fallo de IA no perderá el mensaje: RF-07 deberá dejarlo consultable y pendiente de revisión. |
| **RNF-05 Mantenibilidad** | La API y el servicio de IA estarán desacoplados por contrato versionado y contarán con pruebas de contrato previstas. |
| **RNF-06 Accesibilidad básica** | Formularios tendrán etiquetas asociadas, navegación por teclado y mensajes de error textuales verificables en revisión manual. |
| **RNF-07 Usabilidad** | La vista de detalle mostrará estado, departamento efectivo y resultado IA sin requerir interpretar códigos internos. |
| **RNF-08 Integridad** | Los campos de catálogo, transiciones y rangos de confianza se validarán antes de persistir; una operación inválida no dejará cambios parciales. |
| **RNF-09 Privacidad** | El MVP usará datos demo anonimizados; se minimizará remitente y no se incluirán correos corporativos reales sin autorización documentada. |
| **RNF-10 Trazabilidad** | Cada clasificación almacenará versión de modelo; toda modificación humana relevante conservará actor, fecha, acción y valores antes/después. |
| **RNF-11 Reproducibilidad** | Antes de evaluar IA se versionarán instrucciones, procedencia/licencia de datos, particiones, configuración, baseline y modelo; el conjunto de prueba permanecerá separado. |
| **RNF-12 Manejo de errores** | Errores de validación, autorización, inexistencia, conflicto y dependencia no disponible tendrán código HTTP y mensaje seguro consistentes. |

## 4. Reglas de negocio

| ID | Regla |
|---|---|
| **RN-01** | Departamentos/categorías permitidos: `SOPORTE_TECNICO`, `VENTAS`, `RECURSOS_HUMANOS`, `FACTURACION`. |
| **RN-02** | Estados: `RECIBIDO`, `PENDIENTE_CLASIFICACION`, `PENDIENTE_REVISION`, `CLASIFICADO`, `EN_GESTION`, `CERRADO`. Al crear un mensaje se persiste primero en `RECIBIDO`. Tras intentar clasificar: `RECIBIDO`→`CLASIFICADO` si cumple RN-03; `RECIBIDO`→`PENDIENTE_REVISION` si cumple RN-04; `RECIBIDO`→`PENDIENTE_CLASIFICACION` si cumple RN-05. Una asignación manual desde cualquiera de los dos estados pendientes lleva a `EN_GESTION`; `CLASIFICADO`→`EN_GESTION`; `EN_GESTION`→`CERRADO`. |
| **RN-03** | Una predicción con confianza ≥0,70 (H-01, por validar) se asigna a su departamento y queda `CLASIFICADO`. |
| **RN-04** | Con confianza <0,70 se asigna `REVISION_MANUAL`, queda `PENDIENTE_REVISION` y requiere intervención humana. |
| **RN-05** | Si IA falla o no hay modelo, no se asigna categoría automática y el estado es `PENDIENTE_CLASIFICACION`. |
| **RN-06** | Solo operador/administrador puede cambiar estado, corregir o asignar departamento manualmente; solo administrador crea cuentas, administra usuarios y consulta auditoría global. |
| **RN-07** | Una corrección no elimina la predicción original; guarda motivo, actor, marca temporal, valor anterior y nuevo. Cuando no hubo predicción, la asignación manual registra explícitamente origen `MANUAL` y predicción ausente. |
| **RN-08** | Los eventos de auditoría son de solo adición; no se editan ni eliminan desde el MVP. |

## 5. Contratos REST implementados

| Método y ruta | Permiso | Solicitud / respuesta | Errores |
|---|---|---|---|
| `POST /api/v1/auth/login` | Público | `{username,password}` → `{accessToken,user:{id,role}}` | 401, 422 |
| `POST /api/v1/auth/activate` | Público con credencial temporal | `{username,temporaryCredential,newPassword}` → `204` | 401, 422 |
| `POST /api/v1/auth/logout` | Sesión vigente | revoca la sesión presentada → `204` | 401 |
| `POST /api/v1/messages` | Sesión de operador/administrador | `{subject,body,sender?}` → `{id,status,prediction?,department?}`; persiste primero `RECIBIDO`; IA fallida responde 201 pendiente | 401, 422, 503 MongoDB |
| `GET /api/v1/messages` | Operador | filtros → `{items,page,pageSize,total}` | 401, 422 |
| `GET /api/v1/messages/{message_id}` | Sesión de operador/administrador | — → detalle; historial autorizado mediante RF-12 | 401, 404, 422 |
| `PATCH /api/v1/messages/{message_id}/status` | Sesión de operador/administrador | `{status,reason?}` → detalle; resolución obligatoria al cerrar | 401, 404, 409, 422 |
| `PATCH /api/v1/messages/{message_id}/classification` | Sesión de operador/administrador | `{department,reason}` → detalle; admite `EN_GESTION`, conserva predicción | 401, 404, 409, 422 |
| `GET /api/v1/audit-events` | Administrador | filtros → `{items}` | 401, 403, 422 |
| `POST /api/v1/users` | Administrador | `{username,role,active}` → usuario y credencial temporal mostrada solo una vez | 401, 403, 409, 422 |
| `GET /api/v1/users` | Administrador | `{page,pageSize}` → `{items,page,pageSize,total}` sin secretos | 401, 403, 422 |
| `PATCH /api/v1/users/{username}` | Administrador | `{role,active}` → cuenta pública; invalida sesiones anteriores ante cambio | 401, 403, 404, 409, 422 |
| `POST /api/v1/users/{username}/activation-credential` | Administrador | sin cuerpo → `{user,temporaryCredential,credentialExpiresAt}`; solo pendiente | 401, 403, 404, 409, 422 |

Todas las rutas están implementadas. [OpenAPI generado](openapi.json) es la referencia de esquemas. MongoDB puede producir 503 en cualquier ruta dependiente; no todos esos errores están declarados en el OpenAPI automático. Mensajes filtra por `text,status,department,dateFrom,dateTo,page,pageSize`; auditoría por `messageId,actor,action,dateFrom,dateTo,limit`. Fechas ISO 8601 con zona, extremos inclusivos y rango invertido 422; `pageSize`/`limit` 1–100. El detalle no incorpora la auditoría global.

Ejemplo **ilustrativo, no medición** de una respuesta de creación:

```json
{
  "id": "000000000000000000000001",
  "status": "PENDIENTE_CLASIFICACION",
  "prediction": null,
  "department": null
}
```

El contrato interno implementado recibe `{text,preprocessingVersion}` en `POST /predict` y devuelve `{category,confidence,modelVersion,preprocessingVersion,source,timestamp}`. IA usa `/health` para versión/checksum. No tiene autenticación propia: se mantiene en red interna sin puertos de host, con endurecimiento pendiente fuera de local.

## 6. Diferencias y aceptación todavía no cerrada

- **H-01 y RF-06/RN-03/RN-04:** se conserva arriba el criterio histórico 0,70. La ejecución compara contra `ROUTING_THRESHOLD`, valor Compose 0,45 provisional ([ADR-09](07_decisiones_tecnicas.md)). No se declara validado el 0,70 ni satisfecho literalmente ese valor por pruebas al 0,45. `REVISION_MANUAL` es nombre conceptual de la cola, no departamento persistido: se guarda `department=null` y `PENDIENTE_REVISION`.
- **RF-04/HU-06:** la predicción válida conserva versión de preprocesamiento; si no hay predicción, no hay un campo independiente que la registre. Esa variante queda parcialmente aceptada.
- **RF-10/RN-08:** auditoría de solo adición por API/código, no inmutabilidad frente a administradores de base de datos; permisos restrictivos pendientes.
- **RNF-01/06/07/09:** TLS no local, revisión manual de accesibilidad/usabilidad y autorización de datos reales no se acreditan por pruebas HTTP. Hoy solo se usan datos ficticios.
- **RNF-03/11:** hay evaluación y rendimiento básico previos, no carga productiva. Dataset, código y receta están en Git; binario se reconstruye o entrega aparte. Test separado, pero observado históricamente.
- La aceptación formal RF/RNF/HU requiere prueba integral posterior; véanse [plan](PLAN_Y_RESULTADOS_PRUEBAS.md) y [matriz](04_matriz_trazabilidad.md). No se alteran criterios para declarar artificialmente su cumplimiento.
