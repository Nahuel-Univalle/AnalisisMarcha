# Capturas y evidencia visual

## Cómo se obtuvieron (reales, no montajes)
`scripts/capturar_pantallas.mjs` abre la **aplicación real** (build de producción local, `next start`) con Chrome controlado por CDP, en un **entorno aislado**: base técnica PostgreSQL del puerto 55432 con esquema propio, cuentas técnicas `usuario@example.invalid` («Usuario de prueba») y `admin@example.invalid` («Administrador de prueba»), Cloudinary desactivado. **No se tocó la base habitual ni datos de usuarios.** Se recorre el flujo real con un video existente del dataset de investigación (análisis V5-CR real).

**Privacidad:** los elementos `<video>` se ocultan (`visibility:hidden`) en cada captura para no publicar fotogramas de personas; el resto de cada pantalla es real. Es la única modificación (documentada también en `capturas_nuevas/INDICE_CAPTURAS_GENERADAS.json`). La fotografía del panel principal (mujer caminando) es un recurso decorativo propio de la aplicación, no un video de usuario.

**Aviso de entorno:** en las capturas 08 y 09 aparece «no se pudo guardar el video en la nube. Se mostrará una versión temporal»: es el estado real porque Cloudinary está desactivado en el entorno de prueba (no ocurre con Cloudinary configurado). No se retocó.

## Capturas nuevas (`capturas_nuevas/`, versión final V5-CR)
| Archivo | Pantalla | Uso sugerido en la tesis |
|---|---|---|
| 01_inicio_de_sesion.png | Inicio de sesión | 3.3.4 Interfaz (RF autenticación) |
| 02_registro.png | Registro de usuario | 3.3.4 |
| 03_panel_principal_usuario.png | Panel principal del usuario | 3.3.4 |
| 04_carga_de_video_vacia.png / 05_… con_vista_previa.png | Carga de video (vacía / con video) | 3.3.4 (RF carga) |
| 06_revision_del_video.png | Revisión previa al análisis | 3.3.4 |
| 07_procesamiento_en_curso.png / 08_… completado.png | Etapas de procesamiento y reproductor independiente | 3.3.4, 4.3 |
| 09_resultado_V5CR_probabilidades_y_advertencias.png | Resultado: clase, probabilidades por clase, advertencias, observaciones y parámetros | 3.3.4, 4.4 |
| 10_evaluacion_detallada.png | Análisis detallado | 3.3.4 |
| 11_informes_guardados_tras_recargar.png | Informes guardados leídos de la base | 3.3.4 |
| 12_informe_visual.png | Informe visual (mismo modelo de datos que el PDF) | 3.3.4, 10_INFORMES… |
| 13_informe_guardado_e_historial_de_informes.png | Informe guardado con «Ver informe» y «Descargar PDF» | 3.3.4 |
| 14_seguimiento_historial_de_analisis.png | Historial de análisis (Seguimiento) | 3.3.4 |
| 15_movil_panel_principal.png / 16_movil_historial.png | Vista móvil (390 px) | 3.3.4 (diseño adaptable) |
| 17_administracion_estado_del_modelo.png | Administración: usuarios y estado del sistema | 3.3.4 |
| 18_administracion_analisis.png | Administración: análisis | 3.3.4 |
| 19_administracion_informes_guardados.png | Administración: informes guardados | 3.3.4 |
| 20_administracion_inicio_estado_del_modelo.png | Inicio del administrador: tarjeta «Modelo actual» con versión `gait_deep_v5exp_V5CR_7e9ed60965fe`, 4 clases, 117 videos, 67 sujetos (grupos), macro-F1 0,785 y exactitud 0,860 (evaluación interna) | 3.3.4, 4.4 |

## Capturas reutilizadas (`reutilizadas/`)
Producidas en esta misma serie de trabajos con la versión final, también en entorno aislado: páginas 1 y 2 del PDF descargado con el botón real (`pdf_DESPUES_pagina1/2.png`), comparación pantalla–PDF (`comparacion_pantalla_vs_pdf.png`) e historial con botones (`historial_botones.png`). Fuente: `docs/pdf_informe_unificado_2026-11-19/`, `docs/historial_informes_botones_2026-11-19/`.

## Pendientes (no se inventaron; ver también `14_AUDITORIA_FINAL/PENDIENTES_Y_EVIDENCIAS_FALTANTES.md`)
| Captura | Motivo | Cómo obtenerla manualmente |
|---|---|---|
| Reproductor con el video visible (sin ocultar) | Se ocultó por privacidad | Con un video de prueba autorizado, capturar la pantalla de procesamiento |
| Descarga del PDF y apertura con «Ver informe» en un navegador con visor de PDF | Chrome sin ventana no tiene visor de PDF (se comprobó la apertura y el contenido del archivo, no su pintado) | En Chrome/Edge normales, pulsar «Ver informe» y capturar la pestaña |
| Capturas en el entorno **habitual** (con Cloudinary y usuarios reales) | No se hicieron pruebas con datos habituales para no alterar registros | Repetir el recorrido con una cuenta propia y anonimizar nombre/correo antes de insertar |
| Vista móvil del resultado y del informe | Solo se capturaron panel e historial | Repetir con ventana de 390 px |
| Pruebas visuales en Firefox/Safari/Edge | Solo se usó Chrome | Opcional |
