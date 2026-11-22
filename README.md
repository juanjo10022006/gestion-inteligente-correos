# Gestión inteligente de correos

Sistema documentalmente diseñado para registrar, clasificar y gestionar mensajes corporativos de prueba con apoyo de NLP. El MVP conserva el mensaje antes de consultar IA, expresa la incertidumbre y permite revisión humana trazable. **La aplicación todavía no está implementada.**

## Módulos del MVP

Los seis módulos funcionales son:

1. Bandeja de entrada.
2. Preprocesamiento de mensajes.
3. Clasificación inteligente con NLP.
4. Enrutamiento de mensajes.
5. Gestión de estados.
6. Auditoría.

Adicionalmente, el sistema incluye autenticación,
activación de cuentas y administración de usuarios.

Los únicos roles son `OPERADOR` y `ADMINISTRADOR`. No se integran Gmail, Outlook, SMTP, adjuntos ni autoservicio externo.

## Stack previsto

- Web: React, TypeScript, Vite y Tailwind.
- API: FastAPI y Pydantic.
- Persistencia: MongoDB mediante PyMongo.
- IA: scikit-learn, TF-IDF y regresión logística.
- Despliegue futuro: contenedores coordinados con Docker Compose.

Estas tecnologías forman parte del diseño; no implican que existan servicios desplegados, colecciones físicas o un modelo entrenado.

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
