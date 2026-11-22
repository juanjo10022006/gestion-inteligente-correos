# Gestión inteligente de correos

Sistema para registrar, clasificar y gestionar mensajes corporativos de prueba con apoyo de NLP. La implementación local cubre inicio de sesión, bandeja, inferencia mediante un servicio interno, asignación manual y auditoría.

## Demo completa con Docker Compose

Con Docker Desktop en ejecución, abre una terminal en la raíz del proyecto:

```powershell
docker compose up -d --build --wait
docker compose ps
```

Abre [Gestión de correos](http://127.0.0.1:8080/) o [Swagger](http://127.0.0.1:8080/docs). La primera compilación instala dependencias, construye React y entrena el clasificador v0.3 dentro de su imagen. El entrenamiento evalúa solo la partición de validación.

Compose reutiliza el volumen `mongo_data` dentro del mismo proyecto y la base `gestion_correos` por defecto. Si ya creaste cuentas locales, puedes usarlas. En una instalación nueva, crea las cuentas que necesites. Cada comando solicita la contraseña de forma interactiva.

```powershell
docker compose exec api python -m backend.create_user operador OPERADOR
docker compose exec api python -m backend.create_user admin ADMINISTRADOR
```

La web escucha en el puerto local 8080 y MongoDB en el 27018 para compatibilidad con el flujo de desarrollo. Puedes cambiar esos puertos con `WEB_HOST_PORT` y `MONGO_HOST_PORT`. La API y la IA se comunican por la red interna de Compose. El umbral predeterminado de esta demo es 0,45 y se puede cambiar con `ROUTING_THRESHOLD`.

Al iniciar, la API configura de forma idempotente las colecciones, validadores e índices de MongoDB. También puedes ejecutar esa operación explícitamente, sin borrar documentos:

```powershell
docker compose exec api python -m backend.scripts.init_db
```

La inicialización prepara `audit_events` para una integración posterior, pero no migra los eventos embebidos actuales.

Para apagar la demo conservando los datos, ejecuta `docker compose stop`. Para volver a levantarla, ejecuta `docker compose up -d --wait`.

## Interfaz React

Con la API, MongoDB y el servicio de IA en ejecución, abre otra terminal desde la raíz:

```powershell
cd frontend
npm ci
npm run dev
```

Abre [Gestión de correos](http://127.0.0.1:5173/) e inicia sesión con tu cuenta del proyecto. Puedes registrar un correo, consultar su predicción y guardar una asignación con motivo desde el detalle. Con una cuenta de administrador, abre **Auditoría** para consultar los últimos 50 eventos. También puedes abrir **Ver auditoría del correo** desde su detalle para filtrar por ese mensaje. Vite redirige las solicitudes al puerto 8000 de la API.

## Ejecutar el primer flujo en local

Usar mensajes y cuentas ficticios. La activación de cuentas por API sigue pendiente. Para activar la clasificación, inicia también el [servicio de IA](ai_service/README.md).

Desde la raíz del proyecto, con Python 3.10+ y Docker Compose:

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

Un asunto de dos caracteres devuelve 422. La bandeja admite `page`, `pageSize` y búsqueda con `text`.

Sin sesión, la bandeja y el registro devuelven 401. Para ver la auditoría de creación y de clasificación, inicia sesión como administrador, sustituye el token en **Authorize** y consulta `GET /api/v1/audit-events` con el `messageId` del correo. Un operador recibe 403 en esa ruta. Los mensajes creados antes de implementar la auditoría siguen en la bandeja y carecen de evento de creación.

## Dataset inicial

El [dataset sintético](ai_service/data/README.md) incluye 128 correos en español de las cuatro áreas y particiones fijas. El [entrenamiento local](ai_service/README.md) compara un modelo base con TF-IDF y regresión logística y genera el artefacto versionado que carga el servicio de IA.

## Módulos del MVP

Los seis módulos funcionales son:

1. Bandeja de entrada.
2. Preprocesamiento de mensajes.
3. Clasificación inteligente con NLP.
4. Enrutamiento de mensajes.
5. Gestión de estados.
6. Auditoría.

El sistema incluye autenticación y creación local de usuarios por consola. La activación y la administración de usuarios desde la aplicación siguen pendientes.

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

- [Índice documental](docs/README_DOCUMENTACION.md)
- [SRS y contratos propuestos](docs/02_srs.md)
- [Arquitectura arc42](docs/06_arquitectura_diagramas.md)
- [Catálogo de diagramas editables](docs/diagramas/README.md)
- [Prototipos UI](docs/05_prototipos.md)

La carpeta `docs/` contiene visión, backlog, historias de usuario, trazabilidad, decisiones técnicas, modelo conceptual, diagramas, prototipos e informes históricos de revisión.
