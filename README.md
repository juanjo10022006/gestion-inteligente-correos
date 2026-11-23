# Gestión inteligente de correos — Proyecto 15

MVP académico para registrar mensajes ficticios, sugerir un departamento mediante NLP y gestionar su atención con supervisión humana y auditoría.

**Equipo:** Juan Camilo Gonzales y Juan Jose Solarte.
**Asignatura:** Ingeniería de Software, Universidad Autónoma de Occidente.

Los seis módulos son **bandeja, preprocesamiento, clasificación NLP, enrutamiento, estados y auditoría**. Los roles son `OPERADOR` y `ADMINISTRADOR`; ambos gestionan mensajes, pero solo el administrador gestiona cuentas y consulta auditoría.

Stack implementado: React + TypeScript + Vite y CSS; FastAPI + Pydantic + PyMongo; MongoDB; scikit-learn con TF-IDF y regresión logística. Cuatro servicios Compose: `web` (Nginx), `api`, `ai` y `mongo`. Véase [arquitectura arc42/C4](docs/06_arquitectura_diagramas.md).

## Demo completa con Docker Compose

Requisitos: Git, Docker Desktop en ejecución con contenedores Linux y Docker Compose V2 con soporte para `--wait`. No se necesitan Python, Node ni Jupyter instalados en el host para usar Compose. Se requiere conexión para descargar imágenes/dependencias y puertos locales 8080 y 27018 disponibles.

```powershell
git clone --branch implementacion-mvp https://github.com/juanjo10022006/gestion-inteligente-correos.git
cd gestion-inteligente-correos
docker compose up -d --build --wait
docker compose ps
```

Abre [Gestión de correos](http://127.0.0.1:8080/), [Swagger](http://127.0.0.1:8080/docs) o el [contrato vivo OpenAPI](http://127.0.0.1:8080/openapi.json). El comando de clonación apunta a la rama de entrega actual; no presupone su fusión a `main`.

El build instala dependencias, compila React y entrena/promueve el modelo en una etapa IA cacheable que evalúa únicamente validación. No reentrena al recibir correos. El primer arranque puede tardar más por las descargas; consulte los logs si falla.

### Primera ejecución: elige una alternativa de acceso

La API inicializa colecciones e índices, **pero no crea cuentas automáticamente**. Un volumen MongoDB local no viaja por GitHub.

**A. Bootstrap administrativo por consola:** crea una cuenta activa con contraseña solicitada interactivamente, sin activación temporal:

```powershell
docker compose exec api python -m backend.create_user admin ADMINISTRADOR
```

Entra con esa cuenta y crea operadores desde **Usuarios**. Si `admin` ya existe, no se reemplaza ni se cambia su contraseña.

**B. Demo opt-in local:** en una terminal interactiva, sin `-T` ni redirección de salida:

```powershell
docker compose exec -e APP_ENV=local -e DEMO_SEED_ENABLED=local-only api python -m backend.scripts.seed_demo --confirm-local-demo
```

Crea `demo_admin` y `demo_operador` pendientes de activación y tres mensajes ficticios. Muestra una sola vez las credenciales temporales nuevas; no las publiques, captures ni guardes en Git. En la web pulsa **Activar mi cuenta**, introduce usuario y credencial temporal y define tu contraseña de 12–256 caracteres. Después inicia sesión normalmente. La credencial vence en 24 horas.

La segunda ejecución no duplica mensajes/eventos ni modifica cuentas existentes, activadas o pendientes. No vuelve a mostrar sus credenciales. Ante pérdida o vencimiento, un administrador puede **Renovar credencial pendiente** desde **Usuarios**; no restablece contraseñas de cuentas activadas. Si no queda ningún administrador accesible, el responsable local puede crear otro identificador administrativo mediante la alternativa A, sin modificar cuentas anteriores. No habilites esta demo fuera de local.

### Ejecuciones siguientes y conservación de datos

Usa las cuentas ya creadas y el mismo proyecto Compose para reutilizar el volumen `mongo_data` y la base `gestion_correos`. No repitas el bootstrap.

La web escucha en el puerto local 8080 y MongoDB en el 27018 para compatibilidad con el flujo de desarrollo. Puedes cambiar esos puertos con `WEB_HOST_PORT` y `MONGO_HOST_PORT`. La API y la IA se comunican por la red interna de Compose. El umbral predeterminado de esta demo es 0,45 y se puede cambiar con `ROUTING_THRESHOLD`.

Al iniciar, la API configura de forma idempotente las colecciones, validadores e índices de MongoDB. También puedes ejecutar esa operación explícitamente, sin borrar documentos:

```powershell
docker compose exec api python -m backend.scripts.init_db
```

Las operaciones nuevas escriben su historial en `audit_events`. La consulta combina estos eventos con los embebidos anteriores, sin migrarlos ni eliminarlos.

```powershell
docker compose logs --tail 100 api ai web
docker compose stop
docker compose up -d --wait
```

**No ejecutes `docker compose down -v`: elimina los volúmenes del proyecto y sus datos.** No uses limpiezas globales de Docker. Los conflictos de puertos y configuración se explican en el [manual técnico](docs/MANUAL_TECNICO.md).

## Interfaz React

Con la API, MongoDB y el servicio de IA en ejecución, abre otra terminal desde la raíz:

```powershell
cd frontend
npm ci
npm run dev
```

Abre [Gestión de correos](http://127.0.0.1:5173/) e inicia sesión con tu cuenta del proyecto. Puedes registrar un correo, consultar su predicción y guardar asignaciones sucesivas con motivo, incluso durante la gestión. La bandeja permite combinar texto, estado, departamento y fechas. Con una cuenta de administrador, abre **Auditoría** para consultar hasta 100 eventos coincidentes, filtrables por mensaje, actor, acción y fechas, con sus valores antes/después. Los eventos legados se identifican sin inventar información histórica. Vite redirige las solicitudes al puerto 8000 de la API.

## Ejecutar el primer flujo en local

Usar mensajes y cuentas ficticios. Para activar la clasificación, inicia también el [servicio de IA](ai_service/README.md).

Alternativa de desarrollo, no necesaria para el inicio rápido: desde la raíz, con Python 3.13 y Docker Compose:

```powershell
$env:MONGO_HOST_PORT = '27018'
$env:MONGODB_URI = "mongodb://127.0.0.1:$env:MONGO_HOST_PORT"
docker compose up -d --wait mongo
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m backend.create_user operador OPERADOR
.\.venv\Scripts\python.exe -m backend.create_user admin ADMINISTRADOR
$env:ROUTING_THRESHOLD = '0.45'
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1
```

Los comandos de creación piden una contraseña de al menos 12 caracteres sin mostrarla ni guardarla en el historial. Se ejecutan una vez por cuenta.

En [Swagger local](http://127.0.0.1:8000/docs), usa `POST /api/v1/auth/login` con el usuario operador y su contraseña. Copia el valor de `accessToken` en **Authorize**, y ejecuta `POST /api/v1/messages` con este ejemplo. Consulta `GET /api/v1/messages` para ver el registro.

```json
{"subject":"Consulta de prueba","body":"Necesito una copia de la factura de noviembre."}
```

El registro válido devuelve 201 y un ID. MongoDB guarda el correo en `RECIBIDO` antes de que la API solicite la inferencia. La respuesta contiene el estado del intento:

- `CLASIFICADO` y departamento asignado si la confianza alcanza el umbral configurado.
- `PENDIENTE_REVISION` con la predicción si la confianza es menor.
- `PENDIENTE_CLASIFICACION` si el servicio de IA no responde o devuelve un error.

El ejemplo activa un umbral provisional de 0,45 para la demo con el modelo entrenado en el dataset v0.3. La API usa 0,70 si se omite `ROUTING_THRESHOLD`. Reinicia la API al cambiar el valor. El nuevo umbral se aplica al registrar correos.

Para revisar el resultado, usa `GET /api/v1/messages/{message_id}`. Para asignar o corregir el departamento, envía `{"department":"FACTURACION","reason":"El asunto corresponde a un cobro."}` a `PATCH /api/v1/messages/{message_id}/classification`. La asignación mueve el correo a `EN_GESTION` y conserva la predicción original. Un correo clasificado automáticamente puede pasar a ese estado desde **Iniciar gestión**. Después escribe la resolución y pulsa **Cerrar correo**. En Swagger, ambos cambios se hacen con `PATCH /api/v1/messages/{message_id}/status`; el cierre recibe `{"status":"CERRADO","reason":"Se envió la factura solicitada."}`.

Un asunto de dos caracteres devuelve 422. La bandeja admite `page`, `pageSize`, `text`, `status`, `department`, `dateFrom` y `dateTo`. Auditoría admite `messageId`, `actor`, `action`, `dateFrom`, `dateTo` y `limit` (1–100). Las fechas de API requieren ISO 8601 con zona horaria; los extremos son inclusivos y un rango invertido devuelve 422. La interfaz convierte la hora local a UTC.

### Pruebas aisladas

Con Docker disponible, desde la raíz:

```powershell
docker build --target ai -t gestion-correos-ai-final:local .
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_history_checks.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_compose_smoke.ps1
```

El primer lanzador comprueba el artefacto, evalúa el modelo servido y ejecuta inicialización, aceptación, historial/filtros, acceso y demo/fallos IA. El smoke verifica por HTTP los cuatro servicios, no los clics de React. Ambos usan MongoDB efímero con `tmpfs`, sin montar el volumen demo ni publicar puertos. Véanse [plan/resultados](docs/PLAN_Y_RESULTADOS_PRUEBAS.md) y [procedimiento técnico](docs/MANUAL_TECNICO.md).

Sin sesión, la bandeja y el registro devuelven 401. Para ver la auditoría de creación y de clasificación, inicia sesión como administrador, sustituye el token en **Authorize** y consulta `GET /api/v1/audit-events` con el `messageId` del correo. Un operador recibe 403 en esa ruta. Los mensajes creados antes de implementar la auditoría siguen en la bandeja y carecen de evento de creación.

## Dataset inicial

El [dataset sintético](ai_service/data/README.md) incluye 128 correos en español de las cuatro áreas y particiones fijas. El [entrenamiento local](ai_service/README.md) compara un modelo base con TF-IDF y regresión logística y genera el artefacto versionado que carga el servicio de IA.

Los [tres notebooks académicos](ai_service/notebooks/README.md) verifican entorno, EDA y entrenamiento/evaluación. **Docker no necesita abrir Jupyter para clasificar.** Los resultados curados y su procedencia están en [la evaluación IA](docs/09_evaluacion_final_ia.md); los `.joblib` se reconstruyen, no están subidos a Git.

## Módulos del MVP

Los seis módulos funcionales son:

1. Bandeja de entrada.
2. Preprocesamiento de mensajes.
3. Clasificación inteligente con NLP.
4. Enrutamiento de mensajes.
5. Gestión de estados.
6. Auditoría.

El sistema incluye autenticación, activación y administración de cuentas desde React. La creación local por consola se conserva para el primer administrador y cuentas demo anteriores.

### Cuentas y sesiones

- En **Usuarios**, un administrador crea cuentas de operador o administrador, define su habilitación y recibe una credencial temporal que solo se muestra en ese momento. Debe entregarla por un canal aprobado; la aplicación no envía correos.
- Desde **Activar mi cuenta**, el titular consume la credencial antes de 24 horas y define una contraseña de 12–256 caracteres no compuesta solo por espacios. El secreto temporal no puede recuperarse ni reutilizarse.
- Las cuentas CLI existentes siguen funcionando sin migración. En cuentas nuevas, estar habilitada y estar activada son condiciones diferentes.
- Cambiar el rol o estado invalida las sesiones anteriores; no se permite desactivar o degradar la propia cuenta administrativa.
- Las sesiones duran una hora. **Cerrar sesión** revoca el token en servidor antes de retirar la sesión local. No se guardan tokens ni credenciales temporales en `localStorage`.
- La auditoría administrativa incluye cuentas y sesiones, sin contraseñas, tokens, hashes ni credenciales temporales. Los detalles de almacenamiento y TTL están en [ADR-08](docs/07_decisiones_tecnicas.md).
- El lanzador `tests/run_history_checks.ps1` también ejecuta `tests/access_acceptance.py` contra MongoDB efímero, sin usar la base o volumen de demostración.

Los únicos roles son `OPERADOR` y `ADMINISTRADOR`. No se integran Gmail, Outlook, SMTP, adjuntos ni autoservicio externo.

## Stack implementado

- Web: React, TypeScript, Vite y CSS.
- API: FastAPI y Pydantic.
- Persistencia: MongoDB mediante PyMongo.
- IA: scikit-learn, TF-IDF y regresión logística.
- Demo local: React servido por Nginx, API, IA y MongoDB coordinados con Docker Compose.

## Equipo

- Juan Camilo Gonzales.
- Juan Jose Solarte.

## Documentación

| Documento | Contenido |
|---|---|
| [Manual técnico](docs/MANUAL_TECNICO.md) | Instalación, configuración, persistencia, API y diagnóstico |
| [Manual de usuario](docs/MANUAL_USUARIO.md) | Recorrido por las pantallas implementadas |
| [Informe final](docs/INFORME_FINAL_PROYECTO.md) | Integración académica y estado de entregables |
| [Plan y resultados de pruebas](docs/PLAN_Y_RESULTADOS_PRUEBAS.md) | Evidencias previas y pruebas integrales pendientes |
| [Evaluación IA](docs/09_evaluacion_final_ia.md) | Baseline, métricas, modelo y limitaciones |
| [Notebooks](ai_service/notebooks/README.md) | Laboratorio reproducible y selección del kernel |
| [SRS](docs/02_srs.md) / [trazabilidad](docs/04_matriz_trazabilidad.md) | Requisitos y correspondencia con pruebas |
| [arc42](docs/06_arquitectura_diagramas.md) / [diagramas](docs/diagramas/README.md) | Arquitectura y fuentes UML/C4 |
| [OpenAPI exportado](docs/openapi.json) | Contrato generado; [alcance y reproducción](docs/MANUAL_TECNICO.md#api-y-openapi) |
| [Índice completo](docs/README_DOCUMENTACION.md) | Prototipos, backlog e informes históricos |

La carpeta `docs/` contiene visión, backlog, historias de usuario, trazabilidad, decisiones técnicas, modelo conceptual, diagramas, prototipos e informes históricos de revisión.

## Estado y límites

Entrega documental basada en el commit técnico `3f9a067`. Los resultados corresponden a datos sintéticos y ejecución local, no a correos empresariales reales ni a una plataforma productiva. El umbral Compose 0,45 es provisional; no reemplaza como hipótesis validada H-01=0,70. HTTPS, mínimo privilegio MongoDB y limitación de intentos requieren endurecimiento no local. Quedan pendientes la prueba integral formal en navegador, la revisión de accesibilidad y el video/demo final.
