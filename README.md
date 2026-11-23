# Gestión inteligente de clasificación de correos

**Proyecto 15 · Asignatura: Big Data · Universidad Autónoma de Occidente**  
**Integrantes:** Juan Camilo Gonzales y Juan Jose Solarte

Aplicación web académica que permite registrar mensajes corporativos **ficticios**, clasificarlos en cuatro áreas mediante NLP, asignarlos de forma automática o manual, gestionar su estado y conservar un historial de auditoría.

**Áreas:** Facturación, Ventas, Recursos Humanos y Soporte Técnico.  
**Tecnologías:** React + TypeScript + Vite, FastAPI + Pydantic + PyMongo, MongoDB, scikit-learn (TF-IDF + regresión logística), Docker Compose.  
**Servicios:** `web`, `api`, `ai`, `mongo`. No se integran Gmail, Outlook ni envíos reales de correo.

## 1. Inicio rápido: ejecutar la aplicación con Docker

### Requisitos

- Git y Docker Desktop, iniciado en modo contenedores Linux.
- Docker Compose con soporte para `--wait`.
- Internet para la primera descarga de imágenes y dependencias.
- Puertos **8080** (web) y **27018** (MongoDB local) disponibles; pueden personalizarse.

**No necesitas instalar Python, Anaconda, Node.js ni Jupyter** para iniciar la aplicación con Docker.

En PowerShell:

```powershell
git clone https://github.com/juanjo10022006/gestion-inteligente-correos.git
cd gestion-inteligente-correos
docker compose up -d --build --wait
docker compose ps
```

> El repositorio debe haberse fusionado a `main` antes de utilizar este procedimiento como entrega definitiva. Mientras la implementación siga solo en `implementacion-mvp`, clona esa rama con `git clone --branch implementacion-mvp ...`.

Deben aparecer cuatro servicios activos: `web`, `api`, `ai` y `mongo` (saludables). El primer inicio compila el frontend, instala dependencias y prepara el modelo dentro de la imagen de IA; **los siguientes arranques reutilizan las imágenes y los datos persistentes**.

| Acceso | Dirección |
|---|---|
| Aplicación web | http://127.0.0.1:8080/ |
| Swagger UI | http://127.0.0.1:8080/docs |
| Contrato OpenAPI | http://127.0.0.1:8080/openapi.json |

La API prepara automáticamente las colecciones e índices de MongoDB; **una instalación nueva no contiene usuarios ni mensajes de tu computador**.

### Primera instalación: crear usuarios (elige UNA opción)

**Opción A: crear un administrador desde consola.** Es el método más directo si no necesitas datos de demostración iniciales:

```powershell
docker compose exec api python -m backend.create_user admin ADMINISTRADOR
```

Escribe la contraseña cuando se solicite. Entra a la web con esa cuenta; desde **Usuarios** puedes crear operadores, entregarles una credencial de activación y gestionar roles. Si `admin` ya existe, el comando no sobrescribe su contraseña.

**Opción B: preparar una demo local voluntaria (recomendada para la evaluación).** Desde una terminal interactiva:

```powershell
docker compose exec -e APP_ENV=local -e DEMO_SEED_ENABLED=local-only api python -m backend.scripts.seed_demo --confirm-local-demo
```

El script crea `demo_admin` y `demo_operador` **pendientes de activación** y tres mensajes ficticios. Muestra una credencial temporal **una única vez** por cuenta nueva. Consérvala de forma privada, **no la compartas en capturas, videos, repositorios ni logs publicados**. En la pantalla inicial pulsa **Activar mi cuenta**, introduce el usuario y la credencial, establece una contraseña nueva (12–256 caracteres) e inicia sesión. La credencial vence en 24 horas y no puede utilizarse dos veces.

Ejecutar el seed nuevamente **no duplica cuentas ni mensajes ni recupera las credenciales anteriores**. Si una credencial vence o se pierde, un administrador puede renovarla desde **Usuarios** mientras la cuenta siga pendiente. La demo solo está permitida en el entorno local.

## 2. Recorrido funcional

1. Inicia sesión con un operador o administrador. El administrador tiene acceso adicional a **Usuarios** y **Auditoría**.
2. En **Bandeja**, pulsa **Registrar correo** e introduce asunto y contenido ficticios.
3. Observa la categoría sugerida, la confianza y la versión del modelo. Con el umbral de demo **0,45**, el correo se enruta automáticamente si lo supera; en caso contrario se envía a revisión. Si la IA falla, queda pendiente de clasificación.
4. Pulsa **Iniciar gestión** o realiza una **asignación manual con motivo**. Se conserva la predicción de IA original y se registran las correcciones.
5. Para cerrar el caso, escribe una resolución y pulsa **Cerrar correo**.
6. Combina filtros por texto, estado, departamento y fechas. Como administrador, consulta **Auditoría** para inspeccionar actores, acciones, motivos y valores antes/después.

**Nota:** guardar una resolución no envía realmente un correo. Todos los registros del MVP son simulados.

## 3. Datos persistentes y control de servicios

MongoDB utiliza un volumen nombrado `mongo_data` asociado al proyecto Compose. Se conserva con `stop` y con `down` normal, siempre que no elimines el volumen ni cambies accidentalmente de proyecto.

```powershell
docker compose logs --tail 60 api ai web
docker compose stop
docker compose up -d --wait
```

**Nunca ejecutes `docker compose down -v` ni `docker volume prune` si quieres conservar los datos.** Los volúmenes Docker no se suben a GitHub.

Si los puertos están ocupados, antes del `up` puedes cambiar los puertos del host:

```powershell
$env:WEB_HOST_PORT = '8081'
$env:MONGO_HOST_PORT = '27019'
docker compose up -d --build --wait
```

Para una **prueba aislada**, utiliza además un nombre de proyecto distinto, por ejemplo `docker compose -p correos-integral up -d --build --wait`; así no utilizas el volumen de tu demo habitual. Consulta el [manual técnico](docs/MANUAL_TECNICO.md) para variables y solución de errores.

## 4. Verificar API, MongoDB e IA

```powershell
docker compose ps
docker compose exec -T mongo mongosh --quiet gestion_correos --eval "printjson(db.getCollectionNames())"
docker compose exec -T ai python -c "import json; from urllib.request import urlopen; print(json.load(urlopen('http://127.0.0.1:8001/health')))"
```

La base recién inicializada debe incluir `users`, `sessions`, `messages`, `audit_events` y `model_metadata`. La respuesta IA incluye `modelVersion` y `artifactSha256`. Si modificaste `MONGODB_DB_NAME`, utiliza ese nombre en el comando de MongoDB.

## 5. Pruebas automatizadas y verificación integral

Desde la raíz, con Docker Desktop en ejecución:

```powershell
docker build --target ai -t gestion-correos-ai-final:local .
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_history_checks.ps1 -AiImage gestion-correos-ai-final:local
powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_compose_smoke.ps1
```

El primer lanzador comprueba integridad/reproducción de IA y ejecuta **cinco suites**: inicialización de MongoDB, aceptación, historial y filtros, acceso y seguridad, y recuperación/fallos IA. El segundo verifica el **flujo HTTP integrado de los cuatro servicios** con un entorno efímero. Los scripts utilizan MongoDB temporal y **no montan el volumen de demostración**. El smoke no sustituye la prueba manual de la interfaz en el navegador.

Guía detallada de requisitos, evidencias, defectos y limitaciones: [Plan y resultados de pruebas](docs/PLAN_Y_RESULTADOS_PRUEBAS.md).

## 6. Notebooks de inteligencia artificial y gráficas

Los archivos fuente están en [`ai_service/notebooks/`](ai_service/notebooks/). Se ejecutan en este orden:

1. `00_verificacion_entorno.ipynb`: entorno y datos.
2. `01_eda_dataset.ipynb`: calidad, distribución de clases y longitudes.
3. `02_entrenamiento_evaluacion.ipynb`: baseline, clasificación y matriz de confusión.

**Opción sin instalaciones adicionales en Windows: ejecutar mediante Docker.**

```powershell
docker build --target notebooks -t gestion-correos-notebooks:local .
$salida = Join-Path (Get-Location) 'ai_service/artifacts/notebooks-final'
New-Item -ItemType Directory -Force -Path $salida | Out-Null
docker run --rm --network none --mount "type=bind,source=$salida,target=/evidence" gestion-correos-notebooks:local python -m ai_service.run_notebooks --output-dir /evidence
Get-ChildItem $salida
```

Resultados esperados: los tres `.ipynb` ejecutados, `execution.json`, `notebook-evaluation.json`, `eda_balance_longitud.png` y `matriz_confusion_test.png`, además de `candidate/` y `frozen/`. El código fuente también se puede abrir y ejecutar en VS Code/Jupyter o Anaconda siguiendo el [README del laboratorio](ai_service/notebooks/README.md).

Resultados de referencia del dataset sintético v0.3: **128 mensajes**, partición **80/24/24**, exactitud **23/24 = 95,8 %** y **Macro-F1 = 0,958** en test; la cobertura al umbral provisional 0,45 es **83,3 %**. No deben interpretarse como desempeño probado en correos empresariales reales. El modelo versionado se reconstruye en Docker; los `.joblib` generados bajo `ai_service/artifacts/` no se publican en Git.

## 7. Documentación y entregables

| Recurso | Para qué sirve |
|---|---|
| [Manual técnico](docs/MANUAL_TECNICO.md) | Configuración, seguridad, arquitectura, MongoDB, IA y diagnóstico |
| [Manual de usuario](docs/MANUAL_USUARIO.md) | Activación, registro, clasificación, gestión, cierre y auditoría |
| [Informe final del proyecto](docs/INFORME_FINAL_PROYECTO.md) | Objetivos, diseño, implementación, resultados y conclusiones |
| [Plan y resultados de pruebas](docs/PLAN_Y_RESULTADOS_PRUEBAS.md) | Casos CP, evidencias, métricas y pendientes |
| [Evaluación del modelo](docs/09_evaluacion_final_ia.md) | Baseline, dataset, modelo congelado y límites de las métricas |
| [Notebooks académicos](ai_service/notebooks/README.md) | Entorno, kernel, ejecución y reproducción de gráficas |
| [SRS y requisitos](docs/02_srs.md) · [trazabilidad](docs/04_matriz_trazabilidad.md) | Requisitos y su relación con las pruebas |
| [Arquitectura arc42](docs/06_arquitectura_diagramas.md) · [diagramas](docs/diagramas/README.md) | Arquitectura y fuentes editables UML/C4 |
| [Swagger](http://127.0.0.1:8080/docs) · [OpenAPI exportado](docs/openapi.json) | Contratos y endpoints de la API |
| [Índice documental](docs/README_DOCUMENTACION.md) | Inventario completo de la documentación |

## 8. Estado y limitaciones

El sistema fue construido y probado como **MVP académico local** con datos sintéticos. El umbral 0,45 es provisional y no demuestra una optimización universal; H-01=0,70 se conserva como hipótesis histórica no confirmada. El test del modelo ya fue consultado durante el desarrollo y no debe presentarse como nueva evaluación ciega. Faltan garantías de producción como TLS, limitación de intentos y permisos mínimos en MongoDB, además de algunas pruebas unitarias y de accesibilidad documentadas como pendientes.

Para desarrollo manual con Vite/Anaconda, consulta el [manual técnico](docs/MANUAL_TECNICO.md) y la [guía de notebooks](ai_service/notebooks/README.md). El flujo oficial de evaluación recomendado es **Docker Compose**.
