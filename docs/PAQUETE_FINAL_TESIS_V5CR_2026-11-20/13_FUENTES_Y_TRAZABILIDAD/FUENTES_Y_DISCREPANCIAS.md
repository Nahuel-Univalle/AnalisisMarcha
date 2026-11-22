# Fuentes consultadas y discrepancias detectadas

## 1. Carpetas históricas solicitadas (todas existen)
| Carpeta (`docs/…`) | Archivos | Uso |
|---|---:|---|
| `mejora_modelo_v5_experimental_2026-11-19` | 167 | V5-P/V5-S: fórmulas (36 características), pruebas del preprocesamiento (`fase3_pruebas.json`), robustez V4/V5-P, OOF de V5-P, texto 3.3.6/4.4 de V5-P |
| `optimizacion_final_v5_2026-11-19` | 155 | V5-C/V5-CR: preregistro, OOF, banco de ventanas, `comparacion_final.json`, robustez, fuga residual, checkpoint original |
| `integracion_v5cr_2026-11-19` | 46 | Integración, equivalencia con el evaluador (117/117), baterías Python/E2E/TypeScript, integridad |
| `revision_defensa_2026-11-19` | 41 | Revisión del entorno habitual (solo lectura), PDF de texto anterior (obsoleto), lista manual |
| `recuperacion_pdf_historicos_2026-11-19` | 37 | Auditoría de los 79 informes históricos, pruebas HTTP aisladas |
| `correccion_reproductor_video_2026-11-19` | 26 | Causa y corrección del reproductor, pruebas de navegador |
| `pdf_informe_unificado_2026-11-19` | 34 | PDF unificado con la pantalla, imágenes, variantes |
| Posteriores a la implementación final | — | `correccion_inferencia_v5cr_2026-11-19` (16; tiempo máximo y errores diferenciados) e `historial_informes_botones_2026-11-19` (20; botones del historial) |
Antecedentes V4 usados: `evidencia_experimental_v4_2026-11-18`, `inventario_dataset_v4_2026-11-18`, `auditoria_aprendizaje_movimiento_v4_2026-11-18`.

## 2. Artefactos originales usados como fuente primaria (rutas y hashes en `MANIFIESTO_ARCHIVOS_SHA256.txt`)
Predicciones fuera de partición (`oof_V5CR.npz`, `oof_V5C.npz`, `oof_V5P.npz`, `step18_bn/oof_probabilities.npz`), etiquetas y grupos (`dataset_v4_preview.npz`, `dataset_v5cr_bank.npz`), manifiesto del dataset (`manifest_v4_preview.csv`), resultados de comparación y robustez (`comparacion_final.json`, `fase4_robustez_*.json`), checkpoint, configuración, escalador y etiquetas (`models/gait_deep_v5cr/`), código (`deep_common.py`, `v5cr/*.py`, `15_predict_deep_video_v5cr.py`, `route.ts`, …) y archivos de evidencia de pruebas.

## 3. Discrepancias entre documentos y cómo se resolvieron (contrastadas con los artefactos)
| # | Discrepancia | Verificación | Resolución en el paquete |
|---|---|---|---|
| 1 | Informes previos hablan de «21 pruebas» del preprocesamiento; `fase3_pruebas.json` tiene 28 filas | 21 `PASS` + 7 `DEMOSTRACION_V4` (demuestran defectos de V4) | Se informa 28 filas = 21 pruebas de V5 + 7 demostraciones, y que corresponden a V5-P |
| 2 | La batería E2E aparece con 18, 20 y 21 comprobaciones | La suite creció entre ejecuciones; la última (6 ejecuciones) da 21/21 | Se cuenta una vez con 21 |
| 3 | `FORMULAS_CARACTERISTICAS_V5.md` dice «separación ≥ 0,25 s» entre picos | `find_signal_peaks`: `int(15·0,25)=3` muestras = 0,2 s | La tabla de características usa el valor del código |
| 4 | `FORMULAS_CARACTERISTICAS_V5.md` y `TEXTO_TESIS_3_3_6_y_4_4.md` describen 36 características y recomiendan conservar V4 | Corresponden a V5-P; la decisión posterior fijó V5-CR (33 características) | Se usan solo como antecedente; la tabla de 33 características se rehizo desde el código |
| 5 | `scaler.columns` del checkpoint original tenía 36 nombres y `config.status` decía «V5-C» | Las estadísticas del escalador son de 33 valores; solo cambiaron los metadatos | Copia desplegada corregida (los pesos `.pt` y el mapa de etiquetas son idénticos al original); se documenta en la ficha |
| 6 | «~18 000 parámetros» en textos previos | V4 = 17 860; V5-CR = 17 788 (calculados de los checkpoints) | Se citan los valores exactos |
| 7 | «27 grupos provisionales» (grupos) y «27 videos provisionales» | Cada grupo provisional contiene un video, por eso coinciden | Se usa «27 grupos provisionales (1 video por grupo)» |
| 8 | ECE «calibrado» | Existe para V5-P/V5-C/V5-CR y para **V4 base** (`calibracion_v4_v5.json`: 0,0762), no para V4 activo | V5-CR calibrado se compara solo con V4 base calibrado (sin IC); frente a V4 activo solo la ECE sin calibrar |
| 9 | La robustez de «V4» en los informes es de V4 **base** | `fase4_robustez_v4.json` línea base 0,7252 = V4 base | Las figuras/tablas lo rotulan «V4 base» |
| 10 | `PRUEBAS_TYPESCRIPT.json` | Contiene las 12 pruebas de presentación (`test-v5cr-presentation.ts`), no `tsc` | Se renombra la batería como «TypeScript/tsx de presentación» |
| 11 | `matriz_confusion` en `comparacion_final.json` | Es la **suma de las 5 semillas** (585 predicciones) | Se rotula así en las figuras y se añaden la tasa normalizada y el voto mayoritario |
| 12 | `.venv311` | El intérprete es Python 3.12.3 | Se documenta |
| 13 | El PDF anterior (texto plano) y su prueba (8 comprobaciones) | Reemplazado por el PDF unificado | La prueba se marca obsoleta |
| 14 | 79 informes históricos | La base habitual tiene hoy 81 informes y 173 análisis (2 y 4 creados por el propietario) | Se mantienen 79/169 como los históricos auditados |
| 15 | Las capturas de procesamiento muestran «no se pudo guardar el video en la nube» | Cloudinary está desactivado en el entorno de prueba | Se anota en `INDICE_CAPTURAS.md` |
| 16 | Sesgo de adquisición | La sonda de 7 metadatos (F1 macro 0,777–0,786) iguala a V5-CR (0,785); no se recalculó para V5-CR | Se declara como limitación y evidencia pendiente |

## 4. Información no localizable
- El **Word de la tesis** no estaba disponible en el proyecto (solo borradores de mayo de 2026 en el escritorio del usuario, que no se abrieron): las ubicaciones de capítulos, figuras 4.9–4.11 y tablas 4.3–4.4 son **a verificar**.
- **Curvas de entrenamiento** del modelo V5-CR: no guardadas (solo resumen por partición).
- Procedencia primaria (URL/documentos) de los videos: 0 de 117 trazables.
