# LEEME PRIMERO — Paquete documental para actualizar la tesis de V4 a V5-CR

**Fecha:** 2026-11-20 · **Modelo final:** `gait_deep_v5exp_V5CR_7e9ed60965fe` (SHA-256 `7e9ed60965fe…c9dade`) · **Alcance:** recopilación, auditoría, figuras a partir de resultados existentes y propuestas de redacción. **No se entrenó ningún modelo, no se modificó la aplicación, los datos originales ni el Word.**

## Dossier Word autocontenido (para trabajar con Claude en Word)
`DOSSIER_COMPLETO_PARA_CLAUDE_WORD.docx` (en la raíz del paquete, 82 páginas, 64 tablas reales, 42 figuras y capturas incrustadas) reúne **todo lo anterior en un solo documento**: resumen del modelo, arquitectura y preprocesamiento, 33 características, dataset, métricas, matrices, gráficas, comparaciones, pruebas, mejoras del software, capturas, textos propuestos por capítulo, lista exacta de cambios y referencias a los originales. Está redactado con nombres académicos («modelo preliminar», «modelo final»); los nombres internos solo figuran en las secciones de trazabilidad. Se regenera con `00_INDICE_Y_GUIA/scripts/construir_dossier_word.py` (requiere `python-docx`; solo lee el contenido ya verificado del paquete).

## Tres reglas antes de escribir
1. **V4 no se borra de la tesis:** se conserva como antecedente experimental y versión de respaldo; cambia la descripción del modelo final y de sus resultados.
2. **Todo resultado es validación interna** (117 videos, 67 grupos técnicos de sujeto, 27 provisionales; sin validación clínica). La mejora global de V5-CR frente al V4 activo **no es estadísticamente concluyente**; solo la clase riesgo de caída mejora de forma respaldada; una sonda de 7 metadatos técnicos alcanza un F1 macro del mismo orden (0,777–0,786 frente a 0,785).
3. **El Word no estaba disponible:** las ubicaciones (capítulos, figuras 4.9–4.11, tablas 4.3–4.4, RF 6, 7, 9, 12–20) son **a verificar** cuando se proporcione. Usa `11_CAMBIOS_POR_CAPITULO/` como lista de búsqueda.

## Qué usar primero para cada parte de la tesis
| Parte de la tesis | Empieza por | Después |
|---|---|---|
| Resumen y Abstract | `12_TEXTOS…/01_RESUMEN_Y_ABSTRACT.md` | `04_METRICAS…/METRICAS_Y_COMPARACIONES.md` (cifras) |
| Alcance, población y muestra, metodología | `12_TEXTOS…/02_ALCANCE_Y_METODOLOGIA.md` | `03_DATASET_Y_METODOLOGIA/` |
| Propuesta tecnológica y arquitectura | `12_TEXTOS…/03_PROPUESTA_TECNOLOGICA_Y_ARQUITECTURA.md` | `02_MODELO_V5CR_Y_ARQUITECTURA/FICHA_TECNICA_MODELO_V5CR.md`; figuras 1–2 |
| RF, UML, 3.3.4 Capturas | `11_CAMBIOS_POR_CAPITULO/CAMBIOS_POR_CAPITULO.md` | `09_CAPTURAS_Y_EVIDENCIAS/INDICE_CAPTURAS.md` (20 capturas + pendientes) |
| 3.3.5 Construcción e implementación | `12_TEXTOS…/05_INTEGRACION_FINAL_3_3_5.md` | `01_ESTADO_FINAL_DEL_SOFTWARE/`; `10_INFORMES_PDF_E_HISTORIAL/` |
| 3.3.6 Dataset y modelo | `12_TEXTOS…/04_CONSTRUCCION_DEL_MODELO_3_3_6.md` | `07_PREPROCESAMIENTO_Y_FORMULAS/` (33 características) y `03_DATASET…` |
| 3.4 Fase de transición | `01_ESTADO_FINAL_DEL_SOFTWARE/ESTADO_FINAL_DEL_SOFTWARE.md` | `11_CAMBIOS…` |
| 4.3 Pruebas del sistema y 4.6 | `12_TEXTOS…/06_PRUEBAS_4_3_Y_4_6.md` | `08_PRUEBAS_DEL_SISTEMA/PRUEBAS_EJECUTADAS_RESUMEN.csv` |
| 4.4 Evaluación del modelo; Figuras 4.9–4.11, Tablas 4.3–4.4 | `12_TEXTOS…/07_EVALUACION_Y_RESULTADOS_4_4.md` | `05_MATRICES_DE_CONFUSION/`, `06_FIGURAS_Y_GRAFICAS/INDICE_FIGURAS_Y_PIES_PARA_WORD.md` |
| Limitaciones, Conclusiones, Recomendaciones | `12_TEXTOS…/08_LIMITACIONES.md`, `09_CONCLUSIONES_Y_RECOMENDACIONES.md` | `14_AUDITORIA_FINAL/PENDIENTES_Y_EVIDENCIAS_FALTANTES.md` |
| Capítulo V Costos | `11_CAMBIOS…` (revisar solo si cita V4/entrenamiento) | — |
| Apéndice 8 | `12_TEXTOS…/10_APENDICE_8_DATASET.md` | `03_DATASET…/MANIFIESTO_TRAZABILIDAD_117_VIDEOS.csv` |
| Cualquier cifra o figura | `13_FUENTES_Y_TRAZABILIDAD/MATRIZ_TRAZABILIDAD_TESIS.csv` | `MANIFIESTO_ARCHIVOS_SHA256.txt`, `FUENTES_Y_DISCREPANCIAS.md` |

## Contenido de las carpetas
`00` guía · `01` estado del software · `02` ficha técnica del modelo · `03` dataset y metodología · `04` métricas y comparaciones (CSV verificados contra los originales) · `05` matrices de confusión (PNG 300 dpi + SVG + CSV + script) · `06` figuras (PNG/SVG + datos + scripts + pies para Word) · `07` preprocesamiento y 33 características · `08` pruebas · `09` capturas · `10` informes PDF e historial · `11` cambios por capítulo · `12` textos propuestos (A nuevo, B histórico a conservar, C a reemplazar, D figuras/tablas, E fuentes) · `13` trazabilidad · `14` auditoría final.

## Cómo regenerar
Desde la raíz del repositorio con `.venv311`: `04…/scripts/calcular_metricas_y_matrices.py` → `04…/scripts/extraer_diferencias.py` → `06…/scripts/generar_figuras_resultados.py` y `generar_diagramas.py` → `07…/scripts/generar_tabla_caracteristicas.py` → `03…/scripts/generar_manifiesto_dataset.py` → `08…/scripts/compilar_pruebas.py` → `11…/scripts/generar_cambios.py` → `13…/scripts/generar_trazabilidad.py`. Las capturas: `09…/scripts/capturar_pantallas.mjs` (requiere Chrome, `next build`, el contenedor PostgreSQL técnico del puerto 55432 y la variable de entorno `V5CR_TEST_DB_PASSWORD` con su contraseña; no se incluye en el paquete). Los scripts solo leen los resultados originales.

## Qué NO hay (ver `14_AUDITORIA_FINAL/PENDIENTES_Y_EVIDENCIAS_FALTANTES.md`)
Curvas de entrenamiento (no se guardaron), validación clínica/externa, el Word para ubicar cambios, la sonda de metadatos recalculada para V5-CR, capturas con el video visible y en el entorno habitual, pruebas en otros navegadores.
