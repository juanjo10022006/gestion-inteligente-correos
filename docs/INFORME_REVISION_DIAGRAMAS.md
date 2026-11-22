# Informe de revisión correctiva de diagramas y README

## Alcance

Revisión puntual posterior a 1C. No sustituye el informe histórico [pre-diagramas](INFORME_REVISION_PRE_DIAGRAMAS.md) ni constituye una auditoría de implementación.

## Correcciones

- D-01 y D-02: nivel C4 y límite del sistema corregidos; IA y MongoDB quedan internos.
- D-03 y D-04: dependencias de persistencia/auditoría y notación UML ajustadas.
- D-05 y D-06: ramas de IA, respuesta 201, estados, corrección y cierre alineados con SRS.
- D-07 y D-08: separación de datos sin fuga y redes/TLS de despliegue previsto aclaradas.
- D-09 y modelo conceptual: predicción original, asignación efectiva y actor automático/humano diferenciados.
- UI-02 a UI-06: `viewBox` añadido; UI-04 explicita ausencia de predicción sin inventar valores.
- README raíz, índice documental y catálogo técnico reorganizados sin fusionar sus funciones.

## Evidencia y limitaciones

- Las fuentes D-01–D-09 y UI-01–UI-06 existen y fueron revisadas estáticamente.
- Los SVG se validaron como XML; sus coordenadas se comprobaron contra el `viewBox` declarado.
- Los enlaces Markdown, IDs, estados, categorías y rutas se compararon con el SRS.
- `git diff --check` no reportó errores en archivos rastreados; el estado y la estadística de cambios se inspeccionaron sin realizar commit.
- No había renderizador local de Mermaid ni PlantUML; el renderizado y la comprobación visual de recortes de esas fuentes quedan pendientes.
- H-01=0,70, dataset, métricas, política definitiva de contraseñas e infraestructura siguen pendientes de validación o implementación.

No se ejecutó aplicación, entrenamiento, MongoDB físico, Docker Compose, commit ni push.
