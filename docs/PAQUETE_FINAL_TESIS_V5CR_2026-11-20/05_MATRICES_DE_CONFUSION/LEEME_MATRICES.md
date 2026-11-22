# Matrices de confusión definitivas (V5-CR y V4 activo)

**Origen:** predicciones OOF originales (`oof_V5CR.npz`, `oof_probabilities.npz` de V4) y etiquetas `y` de `dataset_v4_preview.npz` (idénticas a las del banco V5-CR). **No se generó ninguna matriz a partir de métricas resumidas.** Scripts: `scripts/calcular_metricas_y_matrices.py` (datos CSV) y `06_FIGURAS_Y_GRAFICAS/scripts/generar_figuras_resultados.py` (figuras). Cada figura: PNG 300 dpi + SVG. Datos de origen: `datos/`.

## Qué representa cada matriz (denominadores y agregación)
Hay 5 semillas de partición × validación cruzada de 5 particiones, agrupada por grupo técnico de sujeto. Cada semilla da **una** predicción fuera de partición por video (117). Los 5 resultados por video **no son independientes** y no son 5 videos ni personas.
| Matriz | Archivos | Procedimiento | Denominadores |
|---|---|---|---|
| A. Absoluta | `…_A_absoluta_suma5` (`cm_*__suma5semillas_enteros.csv`) | suma de las 5 matrices por semilla; **conteos enteros reales de 585 predicciones** (117 × 5) | normal 290, Parkinson 130, esclerosis múltiple 110, riesgo de caída 55 predicciones por fila |
| B. Normalizada por clase verdadera | `…_B_normalizada` (`…tasa_por_clase_verdadera.csv`) | promedio de las 5 matrices normalizadas por fila; la diagonal es la sensibilidad media | 58, 26, 22 y 11 videos por semilla |
| C. Voto mayoritario | `…_C_voto_mayoritario` (`…voto_mayoritario_por_video_enteros.csv`) | clase más votada entre las 5 semillas para cada video (desempate: menor índice) | 117 videos (conteos enteros de videos) |
| D. Comparación V4 activo – V5-CR | `matriz_confusion_D_…` | dos matrices normalizadas (B) y su diferencia en puntos porcentuales | idénticos (mismos videos, grupos y particiones) |
También se guarda el **promedio por semilla** (`…promedio_por_semilla.csv`, valores fraccionarios con suma 117: **no son conteos de videos**). No se convirtieron promedios en enteros.

## Verificación
La matriz absoluta de V5-CR [[271,13,3,3],[0,126,1,3],[6,4,68,32],[0,1,16,38]] coincide exactamente con `matriz_confusion` de `comparacion_final.json`. Orden de clases en ejes: normal, Parkinson, esclerosis múltiple, riesgo de caída (el de `label_map.json`). Se incluyen también las matrices de V4 activo (mismas particiones) y los CSV de V4 base, V5-P y V5-C.

## Lectura
V5-CR conserva la sensibilidad de normal (93,5 %) y Parkinson (96,9 %); mejora la de riesgo de caída (36,4 % → 69,1 %; IC95 de la diferencia 12,5–52,5 puntos) pero reduce la de esclerosis múltiple (74,6 % → 61,8 %; no significativo); la confusión principal es esclerosis múltiple ↔ riesgo de caída (29,1 % de las esclerosis múltiple se predicen como riesgo de caída). Evaluación interna; sin validación clínica.
