# Épicas e historias de usuario

## Alcance y nomenclatura
Este documento detalla las historias del [SRS](02_srs.md). Conserva los identificadores del backlog y la matriz; las pruebas y pantallas son previstas, no implementadas.

| ID histórico | ID de ficha |
|---|---|
| EP-01 | EPI-001 |
| EP-02 | EPI-002 |
| EP-03 | EPI-003 |
| EP-04 | EPI-004 |
| EP-05 | EPI-005 |

## Mapa de temas
| Tema | Épica | Propósito | Historias |
|---|---|---|---|
| Acceso | EPI-001 | Identidad y permisos | HU-01–02 |
| Registro y consulta | EPI-002 | Ingresar y localizar mensajes | HU-03–05 |
| IA y enrutamiento | EPI-003 | Sugerir o escalar clasificación | HU-06–09 |
| Gestión | EPI-004 | Atender y cerrar mensajes | HU-10–12 |
| Trazabilidad | EPI-005 | Auditar y verificar calidad | HU-13–14 |

## Fichas de épica
### EPI-001 — Acceso y gestión de cuentas
| Campo | Contenido |
|---|---|
| Número / roles | EPI-001 (EP-01); OPERADOR y ADMINISTRADOR |
| Problema | Sin cuentas individuales no se puede restringir acceso ni atribuir acciones. |
| Objetivo y valor | Autenticar usuarios y administrar cuentas de prueba sin exponer secretos. |
| HU vinculadas | HU-01, HU-02 |
### EPI-002 — Registro y consulta de mensajes
| Campo | Contenido |
|---|---|
| Número / roles | EPI-002 (EP-02); OPERADOR, ADMINISTRADOR |
| Problema | Los mensajes manuales no cuentan con un registro y consulta uniforme. |
| Objetivo y valor | Registrar primero `RECIBIDO` y permitir localizar y revisar cada caso. |
| HU vinculadas | HU-03, HU-04, HU-05 |
### EPI-003 — IA y enrutamiento
| Campo | Contenido |
|---|---|
| Número / roles | EPI-003 (EP-03); OPERADOR |
| Problema | La clasificación manual repetitiva no expresa incertidumbre ni fallos. |
| Objetivo y valor | Preparar texto, registrar predicción versionada y escalar incertidumbre. |
| HU vinculadas | HU-06, HU-07, HU-08, HU-09 |
### EPI-004 — Gestión y corrección
| Campo | Contenido |
|---|---|
| Número / roles | EPI-004 (EP-04); OPERADOR, ADMINISTRADOR |
| Problema | Un mensaje requiere atención controlada y posibilidad de corregir IA. |
| Objetivo y valor | Aplicar estados válidos, asignación humana y cierre trazable. |
| HU vinculadas | HU-10, HU-11, HU-12 |
### EPI-005 — Auditoría y aseguramiento de calidad
| Campo | Contenido |
|---|---|
| Número / roles | EPI-005 (EP-05); ADMINISTRADOR; habilitador técnico |
| Problema | Sin evidencia no se puede explicar acciones ni demostrar calidad. |
| Objetivo y valor | Consultar auditoría y especificar pruebas/reproducibilidad. |
| HU vinculadas | HU-13, HU-14 |

## Fichas de historias

### HU-01 — Autenticarse y activar cuenta
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-001; OPERADOR o ADMINISTRADOR |
| Historia | Como usuario autorizado, quiero activar mi cuenta e iniciar sesión para acceder solo a funciones permitidas. |
| ¿Por qué existe? | Identifica al responsable de cada acción y protege los mensajes. La activación evita usar credenciales creadas por otra persona como contraseña permanente. |
| Prioridad / requisitos | Must; RF-01, RNF-01, RNF-02 |
| Dependencias / responsable / puntos | —; Juan Camilo Gonzales; 3 |
| Prototipo y prueba previstos | UI-01 propuesto; CP-08 |
| Excepciones | Credencial temporal vencida, contraseña inválida o cuenta inactiva. |
**Escenarios:** Dado un usuario activado, cuando inicia sesión con credenciales válidas, entonces recibe sesión y rol. Dado un secreto inválido, cuando intenta entrar, entonces recibe 401 sin revelar el campo erróneo.

### HU-02 — Crear cuentas de prueba
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-001; ADMINISTRADOR |
| Historia | Como administrador, quiero crear cuentas con rol permitido y credencial temporal para controlar el acceso. |
| ¿Por qué existe? | El MVP requiere cuentas individuales, no acceso compartido. La credencial de un solo uso permite al titular definir su contraseña sin almacenarla ni auditarla en texto plano. |
| Prioridad / requisitos | Must; RF-02, RN-06, RNF-01, RNF-02, RNF-10 |
| Dependencias / responsable / puntos | HU-01; Juan Jose Solarte; 3 |
| Prototipo y prueba previstos | UI-06 propuesto; CP-08 |
| Excepciones | Rol distinto de `OPERADOR`/`ADMINISTRADOR`, identificador duplicado o acceso insuficiente. |
**Escenarios:** Dado un administrador, cuando crea una cuenta válida, entonces recibe la credencial temporal solo una vez. Dado un operador, cuando crea una cuenta, entonces recibe 403.

### HU-03 — Registrar mensaje
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-002; OPERADOR |
| Historia | Como operador, quiero registrar asunto y cuerpo para iniciar el tratamiento de una solicitud. |
| ¿Por qué existe? | El mensaje debe existir y ser auditable antes de depender de IA. Esto evita perder la solicitud ante un fallo de clasificación. |
| Prioridad / requisitos | Must; RF-03, RN-02, RNF-08, RNF-09 |
| Dependencias / responsable / puntos | HU-01; Juan Camilo Gonzales; 5 |
| Prototipo y prueba previstos | UI-03 propuesto; CP-01, CP-02 |
| Excepciones | Campos vacíos, longitudes inválidas o sesión ausente. |
**Escenarios:** Dado texto válido, cuando se registra, entonces se persiste `RECIBIDO` y se audita antes de IA. Dado texto inválido, cuando se envía, entonces devuelve 422 sin crear mensaje.

### HU-04 — Consultar bandeja
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-002; OPERADOR |
| Historia | Como operador, quiero filtrar la bandeja para localizar mensajes pendientes o atendidos. |
| ¿Por qué existe? | Una lista sin filtros dificulta priorizar solicitudes. La consulta permite gestionar el flujo sin modificar datos. |
| Prioridad / requisitos | Must; RF-08, RNF-03, RNF-06 |
| Dependencias / responsable / puntos | HU-03; Juan Jose Solarte; 5 |
| Prototipo y prueba previstos | UI-02 propuesto; CP-05 |
| Excepciones | Filtros o paginación inválidos. |
**Escenarios:** Dado mensajes existentes, cuando aplico filtros válidos, entonces se devuelven coincidencias paginadas. Dado ningún resultado, cuando filtro, entonces se muestra lista vacía sin alterar registros.

### HU-05 — Consultar detalle
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-002; OPERADOR |
| Historia | Como operador, quiero ver el detalle para conocer el contenido, estado y resultado disponible. |
| ¿Por qué existe? | La decisión de atención requiere contexto y trazabilidad de la predicción. También permite distinguir una predicción de una asignación humana. |
| Prioridad / requisitos | Must; RF-09, RNF-07 |
| Dependencias / responsable / puntos | HU-03; Juan Jose Solarte; 3 |
| Prototipo y prueba previstos | UI-04 propuesto; CP-05 |
| Excepciones | Identificador inexistente o formato inválido. |
**Escenarios:** Dado un id existente, cuando lo consulto, entonces muestra estado, asignación y predicción disponible. Dado un id inexistente, cuando lo consulto, entonces devuelve 404.

### HU-06 — Preprocesar texto
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-003; OPERADOR |
| Historia | Como sistema, quiero preparar el texto sin modificar el original para obtener una entrada reproducible. |
| ¿Por qué existe? | El modelo necesita una representación consistente; el operador debe conservar el mensaje original. La versión del proceso permite explicar la inferencia posterior. |
| Prioridad / requisitos | Must; RF-04, RNF-05, RNF-11 |
| Dependencias / responsable / puntos | HU-03; Juan Camilo Gonzales; 3 |
| Prototipo y prueba previstos | UI-04 propuesto; CP-03 |
| Excepciones | Texto preparado vacío o error de preparación. |
**Escenarios:** Dado un mensaje válido, cuando se prepara, entonces conserva original y registra versión. Dado preparación vacía, cuando ocurre, entonces no invoca IA y deja evidencia de fallo.

### HU-07 — Obtener predicción
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-003; OPERADOR |
| Historia | Como operador, quiero conocer categoría, confianza y versión para comprender la sugerencia. |
| ¿Por qué existe? | La categoría aislada no permite evaluar incertidumbre ni rastrear el modelo. Los metadatos hacen revisable la automatización. |
| Prioridad / requisitos | Must; RF-05, RN-01, RNF-10 |
| Dependencias / responsable / puntos | HU-06; Juan Jose Solarte; 5 |
| Prototipo y prueba previstos | UI-04 propuesto; CP-03 |
| Excepciones | Categoría fuera del catálogo, confianza fuera de rango o respuesta IA inválida. |
**Escenarios:** Dado IA disponible, cuando devuelve respuesta válida, entonces se asocia categoría, confianza y versión. Dado respuesta inválida, cuando se recibe, entonces se activa manejo controlado de fallo.

### HU-08 — Revisar baja confianza
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-003; OPERADOR |
| Historia | Como operador, quiero que una baja confianza vaya a revisión para no enrutar una decisión incierta. |
| ¿Por qué existe? | El umbral H-01 no es evidencia de certeza. Separar estos casos preserva la supervisión humana y evita asignaciones automáticas riesgosas. |
| Prioridad / requisitos | Must; RF-06, RN-03, RN-04, RNF-04 |
| Dependencias / responsable / puntos | HU-07; Juan Camilo Gonzales; 3 |
| Prototipo y prueba previstos | UI-04/UI-05 propuestos; CP-04 |
| Excepciones | Confianza ausente se trata como fallo, no como baja confianza válida. |
**Escenarios:** Dada confianza menor a 0,70, cuando se enruta, entonces queda `PENDIENTE_REVISION`. Dada confianza igual o mayor, cuando se enruta, entonces queda `CLASIFICADO`.

### HU-09 — Gestionar fallo de IA
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-003; OPERADOR |
| Historia | Como operador, quiero conservar un mensaje sin predicción y asignarlo manualmente para continuar la atención. |
| ¿Por qué existe? | La disponibilidad de IA no puede bloquear el registro corporativo. El operador debe resolver el caso sin inventar confianza o categoría automática. |
| Prioridad / requisitos | Must; RF-07, RF-11, RN-05, RNF-04, RNF-12 |
| Dependencias / responsable / puntos | HU-03; Juan Jose Solarte; 3 |
| Prototipo y prueba previstos | UI-03/UI-04/UI-05 propuestos; CP-10 |
| Excepciones | Timeout, modelo ausente o respuesta inválida. |
**Escenarios:** Dada IA indisponible, cuando se crea el mensaje, entonces queda `PENDIENTE_CLASIFICACION`. Dado ese estado, cuando el operador asigna departamento y motivo, entonces queda `EN_GESTION` con origen `MANUAL`.

### HU-10 — Gestionar estado
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-004; OPERADOR |
| Historia | Como operador, quiero cambiar estado según reglas para reflejar la atención real. |
| ¿Por qué existe? | Los estados comunican el punto del flujo sin inferencias informales. Las transiciones restringidas evitan cierres o saltos no explicables. |
| Prioridad / requisitos | Must; RF-10, RN-02, RNF-08, RNF-10 |
| Dependencias / responsable / puntos | HU-05; Juan Camilo Gonzales; 3 |
| Prototipo y prueba previstos | UI-05 propuesto; CP-06 |
| Excepciones | Transición inválida o mensaje inexistente. |
**Escenarios:** Dado cambio permitido, cuando se confirma, entonces actualiza estado y audita. Dado cambio no permitido, cuando se solicita, entonces devuelve 409 sin modificar.

### HU-11 — Corregir o asignar manualmente
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-004; OPERADOR |
| Historia | Como operador, quiero corregir o asignar departamento con motivo para resolver errores sin perder evidencia. |
| ¿Por qué existe? | La IA es apoyo, no autoridad final. Preservar la predicción o ausencia de ella permite analizar decisiones posteriores. |
| Prioridad / requisitos | Must; RF-11, RN-06, RN-07, RNF-10 |
| Dependencias / responsable / puntos | HU-07, HU-10; Juan Jose Solarte; 5 |
| Prototipo y prueba previstos | UI-05 propuesto; CP-06, CP-10 |
| Excepciones | Motivo corto/ausente o departamento fuera de RN-01. |
**Escenarios:** Dada predicción existente, cuando se corrige, entonces conserva original y registra antes/después. Dada predicción ausente, cuando se asigna, entonces registra `MANUAL` y pasa a `EN_GESTION`.

### HU-12 — Cerrar mensaje
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-004; OPERADOR |
| Historia | Como operador, quiero cerrar un mensaje gestionado con resolución para completar su ciclo. |
| ¿Por qué existe? | El cierre diferencia atención terminada de casos todavía en trabajo. La resolución deja contexto para auditoría. |
| Prioridad / requisitos | Should; RF-13, RN-02 |
| Dependencias / responsable / puntos | HU-10; Juan Camilo Gonzales; 2 |
| Prototipo y prueba previstos | UI-05 propuesto; CP-06 |
| Excepciones | Cierre desde estado distinto de `EN_GESTION`. |
**Escenarios:** Dado `EN_GESTION`, cuando aporta resolución válida, entonces queda `CERRADO`. Dado estado pendiente, cuando intenta cerrar, entonces recibe 409.

### HU-13 — Consultar auditoría
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-005; ADMINISTRADOR |
| Historia | Como administrador, quiero consultar eventos filtrables para revisar quién realizó cada cambio. |
| ¿Por qué existe? | La auditoría permite explicar modificaciones y detectar accesos o decisiones. Debe ser consultable sin dar capacidades de edición. |
| Prioridad / requisitos | Must; RF-12, RN-08, RNF-10 |
| Dependencias / responsable / puntos | HU-02, HU-03, HU-11; Juan Jose Solarte; 3 |
| Prototipo y prueba previstos | UI-06 propuesto; CP-07 |
| Excepciones | Operador intenta auditoría global o filtros inválidos. |
**Escenarios:** Dado administrador, cuando filtra eventos, entonces obtiene resultados ordenados. Dado operador, cuando solicita auditoría global, entonces recibe 403.

### HU-14 — Especificar pruebas y reproducibilidad
| Campo | Descripción |
|---|---|
| Épica / rol | EPI-005; habilitador técnico, sin actor de negocio |
| Historia | Como equipo, queremos especificar pruebas y reproducibilidad para demostrar requisitos y fallos controlados. |
| ¿Por qué existe? | El sistema requiere evidencia futura para software e IA. La documentación de particiones, baseline y contratos evita afirmar resultados no obtenidos. |
| Prioridad / requisitos | Must; RNF-03, RNF-04, RNF-05, RNF-11, RNF-12 |
| Dependencias / responsable / puntos | HU-01 a HU-13; Juan Camilo Gonzales y Juan Jose Solarte; 5 |
| Prototipo y prueba previstos | No aplica UI; CP-01 a CP-10 |
| Excepciones | Caso sin trazabilidad o conjunto de prueba contaminado debe impedir declarar evaluación reproducible. |
**Escenarios:** Dado un requisito obligatorio, cuando se documenta, entonces queda vinculado a CP futuro. Dado evaluación IA futura, cuando se ejecuta, entonces conserva particiones, baseline, modelo y versión sin fuga de test.

## Resumen
La tabla de [03_backlog.md](03_backlog.md) es el resumen ejecutivo vigente de prioridad, dependencias, puntos y responsables.
