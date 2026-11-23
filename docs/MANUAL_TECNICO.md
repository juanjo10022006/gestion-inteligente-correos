# Manual técnico

**Proyecto 15 — Sistema inteligente de clasificación de correos corporativos**
**Equipo:** Juan Camilo Gonzales y Juan Jose Solarte.
**Base técnica:** `3f9a067`; alcance local, anterior a la prueba integral definitiva.

## Arquitectura y ejecución

| Servicio | Implementación | Comunicación |
|---|---|---|
| `web` | React/TypeScript/Vite/CSS compilado, servido por Nginx | Host `127.0.0.1:8080` → contenedor 80 |
| `api` | FastAPI/Pydantic/PyMongo | Puerto 8000 solo en red Compose; Nginx publica `/api/`, `/docs` y `/openapi.json` |
| `ai` | FastAPI, TF-IDF y regresión logística | Puerto 8001 solo en red Compose; `/predict` y `/health` internos |
| `mongo` | MongoDB 8.0 standalone | DNS `mongo:27017`; host `127.0.0.1:27018`; volumen `mongo_data` |

No se usa `localhost` para comunicar contenedores: la API llama a `http://ai:8001` y `mongodb://mongo:27017`. Nginx usa `api:8000`. El binding loopback limita el acceso del host, pero no sustituye autenticación de MongoDB ni TLS.

Fuentes: [Compose](../compose.yaml), [Dockerfile Python](../Dockerfile), [Dockerfile web](../frontend/Dockerfile) y [Nginx](../frontend/nginx.conf). Python base fijado por digest; backend e inferencia con versiones fijadas. Las etiquetas `node:22-alpine`, `nginx:alpine` y `mongo:8.0` no están fijadas por digest: no se promete identidad binaria global entre builds.

La [arquitectura arc42](06_arquitectura_diagramas.md) conserva sus doce secciones. Diagramas editables: [D-01 contexto](diagramas/D-01_contexto_c4.mmd), [D-02 contenedores](diagramas/D-02_contenedores_c4.mmd), [D-03 componentes](diagramas/D-03_componentes_backend.puml), [D-04 casos de uso](diagramas/D-04_casos_uso.puml), [D-05 secuencia](diagramas/D-05_secuencia_principal.puml), [D-06 estados](diagramas/D-06_estados.puml), [D-07 IA](diagramas/D-07_pipeline_ia.mmd), [D-08 despliegue propuesto](diagramas/D-08_despliegue_propuesto.mmd) y [D-09 datos](diagramas/D-09_datos_conceptual.mmd). D-08 es una propuesta de despliegue endurecido, no la topología local exacta: Compose usa HTTP y publica MongoDB en loopback.

## Instalación y primera puesta en marcha

Requiere Git, Docker Desktop con contenedores Linux y Compose V2 con `--wait`. Los scripts PowerShell de pruebas requieren además soporte Compose para etiquetas `!reset`. No se necesitan runtimes Python/Node del host para la aplicación. La clonación e inicio están en el [README](../README.md).

Desde la raíz:

```powershell
docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
docker compose logs --tail 100 api ai web
```

`config` puede expandir variables privadas si se imprime completo; use `--quiet` y no publique salidas sensibles. La API inicializa validadores/índices y recupera auditoría pendiente. No crea usuarios. Elija bootstrap o demo:

```powershell
docker compose exec api python -m backend.create_user admin ADMINISTRADOR
```

La CLI solicita y confirma una contraseña de 12–256 caracteres; crea una cuenta **activa**, sin activación temporal. No sobrescribe usuarios. Después se crean cuentas pendientes desde **Usuarios**.

Alternativa local explícita:

```powershell
docker compose exec -e APP_ENV=local -e DEMO_SEED_ENABLED=local-only api python -m backend.scripts.seed_demo --confirm-local-demo
```

No use `-T`, pipes, capturas ni transcripciones de esta salida. Crea `demo_admin`/`demo_operador` pendientes y tres mensajes con IDs deterministas; entrega solo credenciales de cuentas nuevas. Activación normal desde la web. La repetición no cambia cuentas existentes ni duplica los mensajes demo. Variables privadas opcionales `DEMO_ADMIN_TEMPORARY_CREDENTIAL` y `DEMO_OPERATOR_TEMPORARY_CREDENTIAL` deben llegar al proceso mediante `exec -e` y contener al menos 32 caracteres; la alternativa recomendada es generación segura automática. No hay credenciales conocidas por defecto ni envío SMTP.

Los tres requisitos de habilitación son terminal interactiva, bandera `--confirm-local-demo` y entorno `APP_ENV=local`/`DEMO_SEED_ENABLED=local-only`. Esta protección operacional no impide a un administrador del host manipular su propio entorno; no constituye una frontera de seguridad productiva.

## Variables y persistencia de configuración

| Variable | Uso real |
|---|---|
| `WEB_HOST_PORT` | Interpolación Compose, 8080 por defecto |
| `MONGO_HOST_PORT` | Interpolación Compose, 27018 por defecto |
| `MONGODB_DB_NAME` | API y scripts; `gestion_correos` por defecto |
| `MONGODB_URI` | Compose fija `mongodb://mongo:27017`; ejecución Python directa usa `mongodb://127.0.0.1:27017` si se omite |
| `AI_SERVICE_URL` | Compose fija `http://ai:8001`; API directa usa `http://127.0.0.1:8001` |
| `ROUTING_THRESHOLD` | Compose 0,45; API Python directa 0,70 si se omite; rango [0,1] |
| `APP_ENV` | Compose `local`; limita el bootstrap demo junto a su habilitación explícita |
| `AI_MODEL_PATH` | Imagen IA: `/model/model.joblib`; ruta de archivo, no URL |
| `NLP_NOTEBOOK_OUTPUT` | Directorio académico de salida; no interviene en inferencia |

Compose lee variables de la terminal o un `.env` privado para **interpolación**. No introduce automáticamente todas las variables del host dentro de cada contenedor: por ejemplo, habilite demo con `exec -e` como arriba. No versionar `.env`. Tras cambiar puertos o umbral, aplique `docker compose up -d --wait` para recrear los servicios cuya configuración cambió; `restart` no incorpora variables nuevas. Para reconstruir código cambiado, use `--build`.

## Salud, parada y datos

```powershell
docker compose exec -T ai python -c "import json; from urllib.request import urlopen; print(json.load(urlopen('http://127.0.0.1:8001/health')))"
docker compose stop
docker compose up -d --wait
```

Web comprueba `/`; API `/openapi.json`; IA `/health`; MongoDB `ping`. La salud de API prueba disponibilidad básica, no aceptación de todas las historias. Una IA que no puede cargar el bundle no supera salud y Compose puede impedir el arranque inicial de API. La tolerancia manual a IA caída está probada **una vez la API puede estar operativa**, no garantiza arranque normal con dependencia inicialmente insalubre.

El volumen es local y queda asociado al nombre del proyecto Compose. Mantenga ese nombre para reutilizarlo; una clonación nueva no contiene sus datos. `docker compose stop` los conserva. **No usar `docker compose down -v`, `docker volume prune`, ni migraciones destructivas.** No se ha validado restauración de backups; es un pendiente, no una garantía de recuperación.

## MongoDB y auditoría

Colecciones reales: `users`, `sessions`, `messages`, `audit_events`, `model_metadata`. La última tiene validador e índice único, pero no se puebla automáticamente con métricas. El modelo operativo se detalla en [08](08_modelo_datos_preliminar.md).

```powershell
docker compose exec -T api python -m backend.scripts.init_db
```

Inicialización idempotente: crea colecciones o aplica `collMod`, validación `moderate`/`error`, campos adicionales permitidos e índices definidos en [backend/db.py](../backend/db.py). Un índice incompatible produce error: no lo borra ni lo reemplaza. No revisa ni reescribe todos los documentos históricos.

Cada cambio de mensaje persiste su intención en `pendingAudit` junto al estado, con revisión optimista; la publicación usa un ID de evento estable. Los reintentos evitan duplicados. No hay transacción multicollección ni replica set. La consulta combina eventos de `audit_events` (`HISTORICAL`) y embebidos legados (`LEGACY`), sin migrarlos ni inventar `before/after`.

**Distinción de fallos:** en cuentas/sesiones, una publicación fallida después del commit conserva el resultado exitoso y la intención; devuelve `X-Audit-Status: pending` cuando la ruta dispone de respuesta explícita. En mensajes, una falla MongoDB/publicación puede responder 503 aunque exista un cambio persistido. Antes de reintentar una creación, compruebe si ya existe; no hay clave pública de idempotencia de registros de correo. La CLI `create_user` también publica estrictamente: si falla después de insertar, puede dejar una cuenta creada aunque termine con error; su recuperación específica sigue pendiente.

El MVP no ofrece edición/borrado de auditoría. Eso **no es inmutabilidad absoluta**: faltan permisos MongoDB de mínimo privilegio para impedir cambios directos por administradores.

## Acceso y seguridad

Roles `OPERADOR` y `ADMINISTRADOR`; ambos usan mensajes. Cuentas API nuevas: credencial aleatoria de un uso, hash SHA-256, 24 horas; contraseña Scrypt con sal de 16 bytes (`n=2^17`, `r=8`, `p=1`). Política de nuevas contraseñas: 12–256 caracteres, no solo espacios. No se migran contraseñas antiguas.

Las sesiones son Bearer opacas, no JWT: token aleatorio de 32 bytes, digest SHA-256, validez absoluta de una hora y revocación en logout. `authVersion` invalida sesiones al cambiar rol/habilitación. `validUntil` autoriza; TTL `expiresAt` limpia una vez publicada la auditoría. React conserva el token en memoria, no en `localStorage`.

Renovación administrativa solo para cuentas pendientes mediante `POST /api/v1/users/{username}/activation-credential`; invalida la credencial anterior y no permite restablecer una cuenta activada. Prohibida la autodesactivación/autodegradación administrativa. No hay correos reales, refresh tokens ni autoservicio de recuperación.

Fuera de local son pendientes TLS, limitación de intentos y permisos mínimos MongoDB. No publique logs, tokens, credenciales ni hashes de autenticación. Las huellas públicas de dataset/modelo no son secretos de acceso.

## API y OpenAPI

El [SRS](02_srs.md) describe las 13 operaciones públicas generadas en [openapi.json](openapi.json). Consultas de mensajes requieren sesión; cuentas y auditoría requieren administrador. `/docs` y `/openapi.json` son públicos. `/predict` y `/health` pertenecen a IA interna, sin endpoint externo de clasificación añadido a la API.

En Swagger, inicie sesión y copie el token únicamente en **Authorize**, sin capturarlo. Respuestas principales: 200/201/204, 401 sesión/credencial inválida, 403 rol insuficiente, 404 recurso ausente, 409 conflicto, 422 entrada inválida y 503 fallo MongoDB. Un fallo IA durante registro controlado devuelve **201** y `PENDIENTE_CLASIFICACION`, no 503 por defecto.

Exportación reproducible, con API ya en marcha:

```powershell
docker compose exec -T api python -c "import json; from pathlib import Path; from backend.main import app; Path('/tmp/openapi.json').write_text(json.dumps(app.openapi(),ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')"
docker compose cp api:/tmp/openapi.json docs/openapi.json
```

La exportación incluida se generó desde `app.openapi()` en una imagen con fuentes backend coincidentes, sin ejecutar su ciclo de arranque ni conectar MongoDB. **Límite del contrato generado:** las respuestas 401/403/404/409/503 de la lógica no están todas declaradas mediante `responses`; el 422 automático de FastAPI no refleja el cuerpo seguro específico de los handlers de acceso. Documentarlas expresamente en código queda pendiente; no se maquilló el JSON exportado.

## IA y notebooks

Dataset propio sintético v0.3, 128 mensajes, cuatro áreas, 80/24/24 por partición. Preprocesamiento de espacios, TF-IDF de unigramas/bigramas y regresión logística; baseline de clase más frecuente. Solo train ajusta; validation selecciona `C`; test evalúa después de congelar. El test ya fue observado: no es una nueva prueba ciega.

La etapa Docker `model-build` produce `/candidate`, promueve `/model/model.joblib` con `manifest.json` y genera `validation.json`. El target `ai` copia ese bundle y verifica checksum/compatibilidad al cargar, no por petición. `candidate/` local no equivale al modelo servido. Un hash no es firma: cargar solo joblib confiables del equipo.

Versión de referencia `tfidf-logreg-4899d09a3071f491`; [métricas, huellas y límites](09_evaluacion_final_ia.md). El 0,45 de demo es provisional, no óptimo demostrado ni sustitución validada de H-01=0,70. Las huellas usan bytes de fuentes/dataset: conservar LF según `.gitattributes`. Véanse [reproducción IA](../ai_service/README.md) y [laboratorio notebook](../ai_service/notebooks/README.md).

## Pruebas aisladas

Desde PowerShell en la raíz:

```powershell
docker build --target ai -t gestion-correos-ai-final:local .
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_history_checks.ps1 -AiImage gestion-correos-ai-final:local
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_compose_smoke.ps1
```

El primer lanzador construye API y usa red privada con MongoDB `tmpfs`; ejecuta `artifact_verification.py`, evaluación servida y las cinco suites `init_db_verification.py`, `compose_acceptance.py`, `history_acceptance.py`, `access_acceptance.py`, `final_acceptance.py`. `artifact_verification.py` sí reentrena para contrastar reproducción funcional; la evaluación servida no.

El segundo usa [override efímero](../tests/compose.ephemeral.yaml), proyecto UUID y `compose_smoke.py`: construye/inicia cuatro servicios sin puertos ni volumen demo, comprueba el proxy y flujos HTTP y retira su proyecto sin `-v`. No prueba renderizado/interacción React.

Todos son scripts con `assert`: no ejecute Python con `-O`. Algunas suites crean y eliminan bases UUID; por eso **solo deben lanzarse con los wrappers aislados**, no apuntando manualmente a MongoDB de demo. Código de salida distinto de cero invalida el resultado; revise la aserción sin publicar cuerpos con secretos. No equivalen a una suite unitaria completa. [Plan y resultados](PLAN_Y_RESULTADOS_PRUEBAS.md).

## Desarrollo y diagnóstico

Para desarrollo directo se requiere Python 3.13 y Node 22 compatible. API en host: configure `MONGODB_URI=mongodb://127.0.0.1:27018`, `AI_SERVICE_URL` del servicio accesible y `ROUTING_THRESHOLD=0.45`. Compose no publica API/IA al host por defecto: Vite (`npm ci`, `npm run dev`, puerto 5173) redirige a API en `127.0.0.1:8000`, no a la API privada Compose. No basta con iniciar Vite junto a los contenedores sin ajustar esa topología.

| Síntoma | Diagnóstico/acción no destructiva |
|---|---|
| Puerto ocupado | Cambiar `WEB_HOST_PORT`/`MONGO_HOST_PORT` y volver a aplicar `up -d --wait`; usar la URL resultante |
| IA no responde tras arrancar | Revisar `logs ai api`; el mensaje puede quedar pendiente y admitir asignación manual |
| Bundle/ruta inválida | `AI_MODEL_PATH` es archivo local con manifiesto hermano; revisar versiones y checksum; no descargar joblib desconocido |
| Usuario duplicado | No sobrescribirlo; usar su acceso o crear otro identificador autorizado |
| Credencial perdida/vencida | Renovar solo cuenta pendiente desde un administrador accesible |
| Sesión expirada/revocada | Volver a iniciar sesión; comprobar rol/habilitación actual |
| Error de auditoría/cuenta | Resultado persistido puede ser éxito con auditoría pendiente; no eliminar cuentas para reintentar |
| Notebook no importa paquetes | Seleccionar kernel `.venv`/Conda correcto y ejecutar `pip check` |
| Versión modelo distinta | Comparar dataset, Python, dependencias y bytes LF; generar un nuevo reporte de ese artefacto, no reutilizar métricas de otro |

Este manual define el procedimiento; no acredita una nueva instalación integral en este cierre documental.
