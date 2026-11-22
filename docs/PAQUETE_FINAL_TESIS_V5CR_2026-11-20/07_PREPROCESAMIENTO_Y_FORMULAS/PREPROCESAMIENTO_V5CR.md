# Preprocesamiento V5-CR y fórmulas

Archivos de este directorio: `TABLA_33_CARACTERISTICAS_V5CR.csv` (nombre en código, nombre en español, fórmula, significado, unidad, puntos corporales, normalización, limitaciones, archivo/función, equivalente V4), `CORRESPONDENCIA_36_V4_A_33_V5CR.csv`. Se generan con `scripts/generar_tabla_caracteristicas.py`, que **falla si el orden o los nombres no coinciden con la configuración real del checkpoint**. Código fuente desplegado: `scripts/video_training/deep/v5cr/` (`v5_preproc.py`, `v5c_preproc.py`, `v5cr_preproc.py`); su origen experimental está en `docs/mejora_modelo_v5_experimental_2026-11-19/codigo/` y `docs/optimizacion_final_v5_2026-11-19/codigo/`. El script de inferencia es `scripts/video_training/deep/15_predict_deep_video_v5cr.py`.

## 1. Procedimiento (por ventana de 2,6 s)
| Paso | Operación | Función |
|---|---|---|
| 1 | Extracción de 17 landmarks (MediaPipe Pose) a rejilla de 15 fps, ≤ 720 px | `24_normalized_reextract.py::extract_normalized` |
| 2 | `frames_to_points`: coordenadas isotrópicas `(x·aspecto, y)`; se descartan landmarks con visibilidad < 0,2; el cuadro exige hombros y caderas | `v5_preproc.py::frames_to_points` (l. 135) |
| 3 | Ventana de 40 muestras a 15 Hz (t0…t0+2,6 s); mínimo 20 cuadros con pose | `window_inputs_C` |
| 4 | **Interpolación relativa a la cadera**: `H` interpolada; `(p−H)` interpolada por separado; `p = (p−H)+H` | `v5cr_preproc.py::resample_grid_rel` (l. 11) |
| 5 | Escala `s` = mediana de `|S−H|`; si `s < 10⁻⁴` se descarta | `v5_preproc.py::body_scale` (l. 167) |
| 6 | Secuencia [68×40]: `(p−H)/s` (34 canales) + velocidad = diferencia de las mismas posiciones (34 canales) | `sequence_from_grid` (l. 273) |
| 7 | 33 características (36 de V5-P menos 3, con 4 redefinidas) | `features_from_grid` (l. 214) y `features_C` (v5c_preproc.py l. 13) |
| 8 | Escalado: NaN → mediana del entrenamiento; `(x−media)/desv.` | `deep_common.FeatureScaler` |

Notación: `H` centro de caderas, `S` centro de hombros, `s` longitud del torso, `Δ` diferencia entre muestras consecutivas (1/15 s), `rng` = percentil 95 − percentil 5, `asim(a,b) = |a−b|/max(|a|,|b|,10⁻⁶)`.

## 2. Qué corrige V5-CR frente a V4 (defectos verificados por auditoría)
1. **Espejo (aumento):** V4 negaba solo las posiciones x; V5 niega x en posiciones **y** velocidades e intercambia izquierda/derecha.
2. **Escala:** V4 normalizaba con medidas dependientes de la vista (coeficiente de variación 0,41; razón 3,5 entre vistas); V5 usa la longitud del torso (mediana de la ventana).
3. **Características de «balanceo de brazos»/«rango articular»:** en V4 medían desplazamiento global; V5 usa movimiento relativo al hombro y el ángulo del brazo respecto al eje del tronco.
4. **Coordenadas:** V4 normalizaba x por el ancho e y por el alto sin corregir la relación de aspecto; V5 usa coordenadas isotrópicas.
5. **Ventana:** V4 reescalaba a 96 pasos una ventana de 5,03 s cuya duración efectiva variaba con la clase (la duración permitía predecir la clase con F1 macro 0,43); V5 usa una ventana fija de 2,6 s en tiempo físico, sin reescalado.
6. **V5-C:** se eliminan `hip_center_motion_mean`, `shoulder_center_motion_mean`, `horizontal_motion_mean` y se redefinen `body_motion_mean/std`, `motion_smoothness`, `gait_variability` sin avance horizontal (invarianza a la cámara que sigue a la persona: ΔF1 −0,313 en V5-P → −0,023 en V5-C).
7. **V5-CR:** corrige una fuga residual de V5-C/V5-P: interpolar coordenadas absolutas con el borde repetido para landmarks enmascarados filtraba la traslación de la cadera en las coordenadas relativas (370 de 633 ventanas, todas con landmarks enmascarados). Con la interpolación relativa a la cadera, 0 de 633 ventanas cambian; las 137 ventanas sin enmascarados son idénticas a V5-C.

## 3. Valores faltantes (NaN)
- En el banco de 633 ventanas de V5-CR hay **437 valores NaN en 139 ventanas (22 %)**, sin ningún infinito. Provienen casi todos de las características de **muñeca y brazo** cuando la muñeca no es visible: `left_wrist_rel_motion_mean` y `left_arm_swing_angle` (102 ventanas), `right_wrist_rel_motion_mean` y `right_arm_swing_angle` (43), `arm_swing_angle_mean` (7) y `arm_swing_angle_asymmetry` (138); `step_regularity_score` y `rhythm_variability` solo 1 ventana cada una (menos de 3 picos de tobillo).
- El escalador sustituye cada NaN por la **mediana del entrenamiento** (calculada ignorando NaN) tanto al entrenar como en la inferencia (misma clase `FeatureScaler`; `test_v5cr_deployment.py` comprueba imputación y dimensiones). Las entradas NaN se aceptan solo en las características tabulares, nunca en la secuencia.
- En la secuencia, un landmark sin ≥ 2 observaciones en la ventana se rellena con 0 (posición relativa) y su velocidad queda en 0.
- **Consecuencia:** cuando las muñecas no se ven, las características de brazos se vuelven valores típicos (medianas) y no aportan información; la validación contempla estos casos porque el entrenamiento los incluye.

## 4. Limitaciones geométricas declaradas
Todo es 2D: no se corrigen perspectiva ni rotación de la persona; la longitud del torso cambia si la persona se inclina hacia la cámara; ángulos de brazo y características de tronco dependen de la vista; no se convierte a metros (sin calibración ni estatura). Por eso ninguna característica debe presentarse como medida clínica en metros, segundos o grados.

## 5. Características de V5-CR (resumen; detalle en el CSV)
Movimiento relativo a la cadera (2), oscilación vertical de la pelvis (1), movimiento relativo de tobillos y rodillas (4) y su asimetría (1), rango vertical de tobillos (2) y rodillas (2) y asimetría de tobillos (1), regularidad del ritmo (1), movimiento relativo de muñecas (2), ángulo de balanceo de brazos (4), anchos de hombros y caderas como proxies de la vista (2), inclinación y balanceo lateral del tronco con sus variabilidades (4) y estabilidad postural (1), picos/cadencia/frecuencia de picos (3), variabilidad del movimiento (1), suavidad (1), variabilidad del ritmo (1) = **33**.
