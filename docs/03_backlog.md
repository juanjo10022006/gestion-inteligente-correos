# Backlog ejecutivo — MVP de clasificación de correos

Este documento es el índice priorizado del trabajo funcional. Las fichas, justificaciones, excepciones y escenarios completos están en [05_epicas_y_hu.md](05_epicas_y_hu.md).

**Estado de entrega:** implementación local consolidada en `3f9a067`, con pruebas técnicas previas; no es una declaración de aceptación integral. HU-01…05 y HU-07…13 tienen cobertura API/integración referida en la [matriz](04_matriz_trazabilidad.md); todas sus interacciones visuales requieren recorrido final. HU-06 conserva el parcial de versión de preparación cuando no hay predicción; HU-08 la diferencia H-01/umbral operativo; HU-14 sigue parcial por cobertura unitaria y aceptación integral pendientes. No se alteran prioridades, puntos, dependencias ni responsables para declarar cierre.

| Épica | Propósito | Fichas |
|---|---|---|
| EPI-001 (EP-01) | Acceso y gestión de cuentas | HU-01, HU-02 |
| EPI-002 (EP-02) | Registro y consulta de mensajes | HU-03, HU-04, HU-05 |
| EPI-003 (EP-03) | IA y enrutamiento | HU-06, HU-07, HU-08, HU-09 |
| EPI-004 (EP-04) | Gestión y corrección | HU-10, HU-11, HU-12 |
| EPI-005 (EP-05) | Auditoría y aseguramiento de calidad | HU-13, HU-14 |

| HU | Título | Prioridad | Dependencias | Puntos | Responsable | Ficha |
|---|---|---|---|---:|---|---|
| HU-01 | Autenticarse y activar cuenta | Must | — | 3 | Juan Camilo Gonzales | [ficha](05_epicas_y_hu.md#hu-01--autenticarse-y-activar-cuenta) |
| HU-02 | Crear cuentas de prueba | Must | HU-01 | 3 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-02--crear-cuentas-de-prueba) |
| HU-03 | Registrar mensaje | Must | HU-01 | 5 | Juan Camilo Gonzales | [ficha](05_epicas_y_hu.md#hu-03--registrar-mensaje) |
| HU-04 | Consultar bandeja | Must | HU-03 | 5 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-04--consultar-bandeja) |
| HU-05 | Consultar detalle | Must | HU-03 | 3 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-05--consultar-detalle) |
| HU-06 | Preprocesar texto | Must | HU-03 | 3 | Juan Camilo Gonzales | [ficha](05_epicas_y_hu.md#hu-06--preprocesar-texto) |
| HU-07 | Obtener predicción | Must | HU-06 | 5 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-07--obtener-predicción) |
| HU-08 | Revisar baja confianza | Must | HU-07 | 3 | Juan Camilo Gonzales | [ficha](05_epicas_y_hu.md#hu-08--revisar-baja-confianza) |
| HU-09 | Gestionar fallo de IA | Must | HU-03 | 3 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-09--gestionar-fallo-de-ia) |
| HU-10 | Gestionar estado | Must | HU-05 | 3 | Juan Camilo Gonzales | [ficha](05_epicas_y_hu.md#hu-10--gestionar-estado) |
| HU-11 | Corregir o asignar manualmente | Must | HU-07, HU-10 | 5 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-11--corregir-o-asignar-manualmente) |
| HU-12 | Cerrar mensaje | Should | HU-10 | 2 | Juan Camilo Gonzales | [ficha](05_epicas_y_hu.md#hu-12--cerrar-mensaje) |
| HU-13 | Consultar auditoría | Must | HU-02, HU-03, HU-11 | 3 | Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-13--consultar-auditoría) |
| HU-14 | Especificar pruebas y reproducibilidad | Must | HU-01 a HU-13 | 5 | Juan Camilo Gonzales y Juan Jose Solarte | [ficha](05_epicas_y_hu.md#hu-14--especificar-pruebas-y-reproducibilidad) |
