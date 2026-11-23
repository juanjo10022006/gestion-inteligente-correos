# Manual de usuario

**Sistema inteligente de clasificación de correos corporativos — Proyecto 15**
Juan Camilo Gonzales y Juan Jose Solarte.

Utilice únicamente mensajes y personas ficticios. La aplicación no recibe ni envía correo real: registra solicitudes de prueba mediante un formulario.

## 1. Acceder

Con la aplicación iniciada por el responsable técnico, abra `http://127.0.0.1:8080/` (o el puerto que este le indique).

- **Operador:** registra, filtra y gestiona mensajes.
- **Administrador:** puede hacer lo anterior y acceder a **Usuarios** y **Auditoría**.

No existe una cuenta/contraseña pública por defecto. Solicite una cuenta al administrador. La [puesta en marcha](../README.md) corresponde al responsable técnico.

## 2. Activar e iniciar sesión

Si recibió una credencial temporal, pulse **Activar mi cuenta**. Introduzca usuario, credencial y nueva contraseña con su confirmación. La contraseña debe tener entre 12 y 256 caracteres y no estar en blanco. La credencial temporal vence en 24 horas y se consume una sola vez.

Cuando aparezca la confirmación de activación, inicie sesión con su contraseña nueva, **no** con la credencial temporal. Las cuentas creadas directamente por el responsable técnico mediante consola ya están activas y no necesitan este paso.

Si la credencial venció o se perdió, solicite al administrador una renovación mientras la cuenta siga pendiente. La anterior deja de servir. No hay botón de restablecimiento de contraseña para cuentas ya activadas ni mensajes de recuperación por correo.

## 3. Bandeja y registro

En **Bandeja de entrada** puede combinar búsqueda en asunto/contenido, estado, departamento y fechas de creación. Pulse **Filtrar** y use la paginación. Las fechas visibles se muestran en hora local; la aplicación las convierte al consultar. Un filtro sin coincidencias no borra mensajes.

Pulse **＋ Registrar correo**. Complete:

- Asunto de 3–160 caracteres.
- Contenido de 10–10.000 caracteres.
- Remitente opcional, ficticio.

Ejemplo de contenido no sensible: «Necesito una copia de la factura del servicio que ya pagamos». Pulse **Registrar y clasificar**. No envíe contraseñas ni datos laborales reales.

Si ocurre un error de base de datos, consulte primero la bandeja antes de volver a registrar: el mensaje podría haberse guardado aunque no llegara la confirmación.

## 4. Entender el resultado

Seleccione un mensaje para consultar su contenido y la sección **Clasificación**:

| Resultado | Significado |
|---|---|
| Clasificado | La confianza alcanzó el umbral configurado y hay un área asignada |
| Pendiente de revisión | Existe sugerencia, pero necesita decisión humana; el área aún no está asignada |
| Pendiente de clasificación | No hubo una respuesta IA válida; no se inventan categoría ni confianza |
| En gestión | Una persona está atendiendo el caso |
| Cerrado | Se registró una resolución; no admite nuevas correcciones |

**Sugerencia de IA**, **Confianza** y **Modelo** describen la predicción original, no una verdad garantizada. **Área asignada** y **Origen de asignación** indican la decisión efectiva. La demo usa un umbral provisional de 0,45; la probabilidad no está calibrada como garantía empresarial.

## 5. Asignar o corregir

En **Asignación manual**, elija Soporte técnico, Ventas, Recursos humanos o Facturación. Escriba un **Motivo** de 5–500 caracteres y pulse **Guardar asignación**.

Puede hacerlo cuando el mensaje está pendiente, clasificado o incluso **En gestión**. La acción lo deja **En gestión**, registra quién y por qué cambió el destino y conserva la predicción original. Si nunca hubo predicción, el origen queda **Manual**, sin categoría/confianza IA ficticias.

Si aparece un conflicto porque otra persona modificó el mensaje, vuelva a consultarlo antes de decidir; no repita cambios a ciegas.

## 6. Gestionar y cerrar

Un mensaje clasificado automáticamente ofrece **Iniciar gestión**. Una asignación manual ya inicia ese estado.

Cuando termine la atención, escriba la **Resolución del correo** (5–500 caracteres) y pulse **Cerrar correo**. La resolución permanece visible y el cambio es auditable. No se puede cerrar directamente un mensaje pendiente ni reabrir uno cerrado desde este MVP.

## 7. Usuarios — solo administrador

Abra **Usuarios** para crear una cuenta con usuario, rol y habilitación. Recibirá una credencial temporal mostrada una sola vez; entréguela por un canal aprobado, sin capturas ni publicación. Después ocúltela. No se puede recuperar mediante la lista.

Puede cambiar rol/habilitación mediante **Guardar cuenta**. Ese cambio invalida las sesiones anteriores del titular. Estar habilitada y estar activada son condiciones diferentes. No puede desactivar ni degradar su propia cuenta administrativa.

Para cuentas pendientes existe **Renovar credencial pendiente**, con confirmación de que la anterior será inválida. Oculte primero cualquier credencial que aún esté mostrando. La renovación no restablece contraseñas de cuentas ya activadas.

Una caída de publicación de auditoría no deshace una creación o activación ya guardada: el sistema conserva la intención para recuperarla. La interfaz no debe interpretarse como monitor detallado de esa cola; si hay dudas consulte al responsable técnico.

## 8. Auditoría — solo administrador

Abra **Auditoría**, o **Ver auditoría del correo** desde el detalle. Puede filtrar por ID de mensaje, actor, acción y fechas. La pantalla solicita hasta 100 resultados coincidentes, los más recientes primero; no ofrece paginación del historial completo. Se muestran fecha, responsable, acción, motivo y valores antes/después cuando existen.

Los eventos de usuarios/sesiones no tienen ID de mensaje. Los eventos automáticos se identifican como sistema. Los registros **Histórico embebido; antes/después no disponible** corresponden a información anterior: eso no implica que se reconstruyeran datos faltantes. Un operador no tiene permiso para consultar esta sección.

## 9. Salir y resolver errores

Pulse **Cerrar sesión**. Se revoca la sesión en servidor y se retira de la interfaz. Si falla la red, reintente; no se debe asumir una revocación confirmada. La sesión vence tras una hora y también puede invalidarse por cambio de rol o habilitación. Recargar la página pierde el token en memoria y puede pedir nuevo acceso.

| Mensaje/situación | Qué hacer |
|---|---|
| Credenciales inválidas | Revisar acceso, activación y habilitación con el administrador; no compartir contraseñas |
| Formato inválido | Revisar longitudes, campos y motivo/resolución |
| Sin permiso | Usar la cuenta del rol autorizado, sin compartir su sesión |
| IA no disponible | Conservar el mensaje y asignarlo manualmente con motivo |
| Estado no admite la acción | Actualizar el detalle y seguir el flujo permitido |
| La página no carga | Comunicar URL y error al responsable técnico, sin adjuntar secretos |

## Evidencia visual pendiente

Este manual se basa en las pantallas implementadas; **no acredita una prueba de navegador autenticado**. No se añadieron capturas inventadas. En la prueba final se propone capturar, sin credenciales ni tokens: bandeja filtrada, detalle con predicción, corrección conservando el original, resolución/cierre, lista pública de usuarios y auditoría filtrada. Véase el [plan](PLAN_Y_RESULTADOS_PRUEBAS.md).
