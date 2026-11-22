# Índice de figuras, datos de origen y pies sugeridos para Word

Todas las figuras: PNG a 300 dpi + SVG, generadas con los scripts de `scripts/` **solo a partir de datos existentes** (predicciones OOF originales, checkpoint, código, manifiesto). Datos de cada figura en `datos/*.csv` (o `04_…`/`05_…`). Ejecución: `calcular_metricas_y_matrices.py` → `generar_figuras_resultados.py` y `generar_diagramas.py`. Los números de figura son **propuestas**: deben ajustarse a la numeración real del Word (no estaba disponible para lectura).

| # | Archivo (PNG/SVG) | Datos / script | Pie sugerido (Word) | Sección propuesta |
|---|---|---|---|---|
| 1 | `fig_arquitectura_GaitTemporalModel_V5CR` | `datos/arquitectura_capas_V5CR.csv`; lee el checkpoint (`generar_diagramas.py`) | **Figura 3.x. Arquitectura del clasificador GaitTemporalModel (V5-CR): CNN 1D de dos ramas (17 788 parámetros entrenables).** Fuente: Elaboración propia (2026), a partir de la configuración y los pesos del checkpoint. | 3.3.6 |
| 2 | `fig_flujo_completo_sistema_V5CR` | código del sistema (`generar_diagramas.py`) | **Figura 3.x. Flujo de análisis del video al resultado orientativo.** MediaPipe Pose es una red preentrenada; el clasificador es propio. Fuente: Elaboración propia (2026). | 3.3.5 |
| 3 | `fig_diagrama_preprocesamiento_V5CR` | `v5cr/*.py` | **Figura 3.x. Preprocesamiento V5-CR de una ventana de 2,6 s.** Fuente: Elaboración propia (2026). | 3.3.6 |
| 4 | `fig_comparacion_caracteristicas_V4_vs_V5CR` | `datos/fig_caracteristicas_V4_vs_V5CR.csv` | **Figura 3.x. Características de marcha por grupo funcional: V4 (36) frente a V5-CR (33).** Fuente: Elaboración propia (2026), a partir del código del proyecto. | 3.3.6 |
| 5 | `fig_distribucion_dataset` | `datos/fig_distribucion_dataset.csv` | **Figura 3.x. Distribución del conjunto de 117 videos por clase, grupo de sujeto y fuente de grabación.** «Provisional»: la fuente no identifica a la persona. Fuente: Elaboración propia (2026), a partir del manifiesto del dataset. | 3.3.6 / Apéndice 8 |
| 6 | `fig_comparacion_exactitud_f1macro_por_version` | `datos/fig_comparacion_exactitud_f1macro_por_version.csv` | **Figura 4.x. Exactitud y F1 macro por versión del modelo (validación cruzada agrupada por sujeto, 5 semillas, IC95 % por remuestreo de grupos).** Evaluación interna. Fuente: Elaboración propia (2026). | 4.4 |
| 7 | `fig_V5CR_precision_sensibilidad_f1_por_clase` | `datos/fig_V5CR_precision_sensibilidad_f1_por_clase.csv` | **Figura 4.x. Precisión, sensibilidad y F1 por clase de V5-CR.** Fuente: Elaboración propia (2026). | 4.4 |
| 8 | `fig_f1_macro_por_semilla` | `datos/fig_f1_macro_por_semilla.csv` | **Figura 4.x. F1 macro por semilla de partición.** Fuente: Elaboración propia (2026). | 4.4 |
| 9 | `fig_calibracion_V5CR_diagrama_fiabilidad` | `datos/fig_calibracion_V5CR_diagrama_fiabilidad.csv` | **Figura 4.x. Diagrama de fiabilidad de V5-CR (sin calibrar y con temperatura) y V4 activo (sin calibrar).** Predicciones agrupadas de las 5 repeticiones. Fuente: Elaboración propia (2026). | 4.4 |
| 10 | `fig_robustez_camara_ruido_perdida_fotogramas` | `04_…/ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv` | **Figura 4.x. Cambio del F1 macro ante perturbaciones de la grabación (modelos congelados).** V4 = modelo base. Fuente: Elaboración propia (2026), a partir de `fase4_robustez_*.json`. | 4.4 |
| 11 | `05_MATRICES_DE_CONFUSION/matriz_confusion_V5CR_A_absoluta_suma5` | `05_…/datos/cm_V5-CR__suma5semillas_enteros.csv` | **Figura 4.x. Matriz de confusión de V5-CR en valores absolutos (suma de 5 repeticiones: 585 predicciones, no 585 videos).** Fuente: Elaboración propia (2026). | 4.4 |
| 12 | `matriz_confusion_V5CR_B_normalizada` | `…tasa_por_clase_verdadera.csv` | **Figura 4.x. Matriz de confusión de V5-CR normalizada por clase verdadera (%).** Fuente: Elaboración propia (2026). | 4.4 (recomendada) |
| 13 | `matriz_confusion_V5CR_C_voto_mayoritario` | `…voto_mayoritario_por_video_enteros.csv` | **Figura 4.x. Matriz de confusión de V5-CR por voto mayoritario de las 5 semillas (117 videos).** Fuente: Elaboración propia (2026). | opcional |
| 14 | `matriz_confusion_D_comparacion_V4activo_vs_V5CR` | `diferencia_tasas_V5CR_menos_V4activo_puntos_porcentuales.csv` | **Figura 4.x. Comparación de matrices normalizadas V4 activo – V5-CR y diferencia (puntos porcentuales).** Fuente: Elaboración propia (2026). | 4.4 |
| 15 | `matriz_confusion_V4activo_A/B/C…` | idem | Matrices del V4 activo (absoluta, normalizada, voto mayoritario) | 4.4 / apéndice |

## Figuras NO generadas (sin datos reales)
- **Curvas de entrenamiento, pérdida o validación:** el código calcula la pérdida por época pero **no la guardó**; los registros (`entrenamiento_*.log`, `folds_V5CR.csv`) solo contienen el resumen por partición (E\*, T, exactitud, F1). No se reconstruyen ni inventan. Para obtenerlas habría que reentrenar guardando las curvas (fuera del alcance).
- **Figuras antiguas de V4** (`docs/evidencia_experimental_v4_2026-11-18/figura_4_4_*.png`, `models/gait_deep/plots/*`): se conservan como histórico de V4; no deben presentarse como resultados de V5-CR.
- Las figuras actuales de la tesis numeradas 4.9, 4.10 y 4.11 y las tablas 4.3 y 4.4 deben comprobarse en el Word (no disponible): si son las de V4 (matriz de confusión, comparación, calibración), se reemplazan por las equivalentes de esta lista (11–14, 6, 9) etiquetando claramente la versión.

## Notas de lectura de las figuras
- Todas las matrices con pie metodológico: denominadores y procedimiento de agregación (suma, promedio de tasas, voto mayoritario).
- Las comparaciones V4 activo–V5-CR usan las mismas particiones y videos; las diferencias de las matrices no tienen IC propio.
- Evaluación interna sobre 117 videos / 67 grupos técnicos; no es validación clínica.
