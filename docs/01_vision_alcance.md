# Visión y alcance — Sistema inteligente de clasificación de correos corporativos

**Proyecto 15 — Ingeniería de Software, Universidad Autónoma de Occidente**  
**Estado:** Fase 1, documentación. **Versión:** 0.1 — 21 de noviembre de 2026.

> Línea base de visión conservada: la formulación en futuro corresponde al diseño inicial. El estado actual de implementación, evidencias y pendientes se integra en [INFORME_FINAL_PROYECTO.md](INFORME_FINAL_PROYECTO.md), sin cambiar los objetivos OBJ-01…08 ni declarar beneficios empresariales medidos.

## 1. Introducción y contexto

El Proyecto 15 de la guía académica propone clasificar mensajes empresariales por área o tipo de solicitud y apoyar su enrutamiento, respetando permisos y privacidad. La solución será una aplicación web para registrar mensajes corporativos de prueba, sugerir su departamento mediante clasificación de texto y gestionar su atención con trazabilidad.

La guía exige un producto de software completo, con IA integrada mediante una interfaz definida, versión de modelo y evaluación independiente; no un notebook aislado. Los requisitos definidos aquí distinguen esa guía de las decisiones del equipo: React, FastAPI, MongoDB y scikit-learn son decisiones técnicas iniciales, no imposiciones del docente.

## 2. Problema y justificación

La clasificación y distribución manual de solicitudes internas puede retrasar la atención, dirigir casos al equipo incorrecto y dificultar conocer quién modificó una decisión. El MVP reduce esa carga al proponer un departamento y conservar la decisión automática y la revisión humana. La propuesta no sustituye al operador: ante incertidumbre o indisponibilidad de IA, conserva la intervención humana y evita una asignación automática no confiable.

## 3. Objetivos

### Objetivo general

**OBJ-01.** Diseñar y construir posteriormente un MVP demostrable que registre mensajes corporativos de prueba, sugiera y enrute un departamento, permita su gestión por operadores autorizados y conserve una auditoría verificable de las decisiones.

### Objetivos específicos verificables

| ID | Objetivo | Evidencia de verificación prevista |
|---|---|---|
| OBJ-02 | Registrar mensajes con asunto y contenido válidos. | CP-01, CP-02 |
| OBJ-03 | Producir una sugerencia de una de las cuatro categorías, con confianza y versión del modelo, cuando el servicio esté disponible. | CP-03 |
| OBJ-04 | Enrutar automáticamente solo clasificaciones de confianza suficiente y marcar las demás para revisión. | CP-04 |
| OBJ-05 | Permitir consulta, filtrado, actualización controlada de estado y corrección manual. | CP-05, CP-06 |
| OBJ-06 | Conservar evidencia auditable de creación, clasificación, enrutamiento y cambios humanos. | CP-07 |
| OBJ-07 | Restringir operaciones según autenticación y rol. | CP-08 |
| OBJ-08 | Preparar una evaluación reproducible del clasificador frente a un baseline, sin declarar resultados antes de ejecutarla. | CP-09 |

## 4. Visión y solución propuesta

Para operadores corporativos que administran solicitudes internas, el sistema ofrece una bandeja única y una sugerencia de enrutamiento explicable por sus metadatos (categoría, confianza y versión), a diferencia de una clasificación manual sin trazabilidad. El flujo de referencia es: **registrar → validar → persistir `RECIBIDO` y auditar creación → preprocesar → clasificar → asignar o revisar manualmente → actualizar estado y auditar → consultar/gestionar**.

Las categorías iniciales son **Soporte técnico**, **Ventas**, **Recursos humanos** y **Facturación**. El sistema no conectará buzones reales: los mensajes ingresarán por formulario web o datos de prueba.

## 5. Interesados, actores y responsabilidades

| Interesado/actor | Interés y responsabilidad |
|---|---|
| Operador especializado | Registra, consulta, gestiona estado y revisa/corrige clasificaciones. |
| Administrador | Crea cuentas de operador/administrador, asigna roles y consulta la auditoría. |
| Equipo de dos integrantes | Define datos lícitos, implementa y prueba posteriormente el MVP. |
| Docente | Evalúa cumplimiento académico y demostración. |
| Servicio de IA (sistema externo interno) | Devuelve categoría, confianza, versión y estado de inferencia; no decide por sí solo. |

## 6. Alcance del MVP

### Incluido

1. Autenticación y autorización básica para los únicos roles obligatorios: operador y administrador.
2. Bandeja de entrada con búsqueda y filtros básicos.
3. Registro y validación de mensajes de prueba.
4. Preprocesamiento reproducible de texto para inferencia.
5. Clasificación NLP y metadatos de predicción.
6. Enrutamiento a una de las cuatro áreas o cola de revisión.
7. Gestión de estados y corrección humana.
8. Auditoría consultable de acciones relevantes.
9. Contratos, pruebas previstas y datos demo sin información personal real.

### No funcional incluido

Seguridad por rol, validación de entradas, privacidad mínima, trazabilidad, accesibilidad básica, manejo explícito de fallos de IA, objetivos de rendimiento y reproducibilidad documental/técnica.

### Exclusiones

- Integración con Gmail, Outlook, IMAP/SMTP u otros buzones reales.
- Envío de correos, notificaciones externas, adjuntos y OCR.
- Entrenamiento con datos corporativos reales o personales sin autorización documentada.
- SLA corporativos, alta disponibilidad multi-región, analítica avanzada y gestión de múltiples organizaciones.
- Decisiones disciplinarias, financieras o laborales tomadas exclusivamente por IA.

Las integraciones de correo y métricas avanzadas son **opcionales posteriores**, no parte del MVP.

## 7. Restricciones, supuestos y dependencias

| Tipo | Elemento |
|---|---|
| Académica | Equipo de dos integrantes y alcance limitado al MVP documentado. |
| Técnica | La arquitectura prevista separa interfaz web, API, persistencia y servicio de IA. |
| Dato | Se usarán datos demo o un dataset lícito, documentado y anonimizado antes de cualquier entrenamiento. |
| Hipótesis H-01 | El umbral inicial propuesto para “baja confianza” es menor a 0,70; deberá validarse con los datos. |
| Dependencia D-01 | Disponibilidad de un artefacto de modelo versionado y compatible con el contrato de inferencia. |
| Dependencia D-02 | Credenciales de prueba y configuración segura se definirán en la fase de implementación; no se incluyen en esta documentación. |

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación prevista |
|---|---|
| Datos insuficientes, sesgados o sin licencia | Documentar procedencia, licencia, anonimización y particiones; no entrenar hasta aprobarlos. |
| Predicción incorrecta | Umbral, cola de revisión, corrección humana y auditoría; medir Macro-F1 y correcciones posteriormente. |
| IA indisponible | Guardar el mensaje como pendiente de clasificación y permitir asignación manual. |
| Exposición de información sensible | Datos demo anonimizados, autorización por rol, minimización y auditoría. |
| Alcance excesivo | Mantener cuatro categorías, formulario local y 14 historias priorizadas. |
| Falta de reproducibilidad | Versionar dataset/instrucciones, baseline, modelo, configuración y casos de prueba en fase posterior. |

## 9. Beneficios y éxito

Beneficios esperados: centralización de solicitudes, sugerencia inicial de enrutamiento, menor esfuerzo de clasificación repetitiva y evidencia de las intervenciones humanas. No se afirma reducción real de tiempos ni precisión hasta medirlas.

| Criterio de éxito | Medición/aceptación |
|---|---|
| Flujo completo | CP-01 a CP-07 pasan con datos de prueba durante la demostración. |
| Integración IA | CP-03 verifica contrato, categoría, confianza y versión; CP-09 compara baseline y modelo con test separado. |
| Gestión segura | CP-08 verifica permisos y CP-07 verifica auditoría. |
| Confiabilidad operativa | CP-04 y CP-10 verifican baja confianza e indisponibilidad sin perder el mensaje. |
| Objetivos de diseño, no resultados | Respuesta de consulta p95 ≤ 2 s y clasificación p95 ≤ 5 s con carga demo definida; se medirán en fase de pruebas. |

## 10. Definición de terminado del MVP

El MVP estará terminado cuando el flujo principal pueda demostrarse con datos de prueba; los seis módulos mínimos estén integrados; los roles funcionen; cada RF y RNF tenga prueba prevista y evidencia de ejecución futura; la IA esté comparada contra un baseline con conjunto de prueba independiente; existan datos/instrucciones reproducibles; y los fallos o baja confianza conduzcan a revisión humana. Esta definición no declara que esos elementos ya estén implementados o probados.
