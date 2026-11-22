# Formulas y significado físico de las 36 características V5

Implementación: `codigo/v5_preproc.py` (`features_from_grid`, líneas indicadas por función). Todas se calculan sobre una ventana fija de 2,6 s (40 muestras a 15 fps), en **coordenadas isotrópicas** `X = x·(ancho/alto)`, `Y = y` y **sin unidades físicas** (no hay calibración a metros): las distancias se expresan en «longitudes de torso» `s`.

Notación: `H` = centro de caderas, `S` = centro de hombros, `s` = mediana en la ventana de |S − H| (escala corporal), `Δ` = diferencia entre muestras consecutivas (1/15 s), `rng(·)` = percentil 95 − percentil 5 (robusto a saltos de un landmark), `asim(a,b)` = |a−b| / max(|a|,|b|,1e-6).

| # | Característica V5 (V4) | Fórmula | Qué mide | Cambio |
|---|---|---|---|---|
| 1-2 | `body_motion_mean/std` | media y desviación de |Δp|/s sobre hombros, caderas, rodillas y tobillos | desplazamiento global (incluye avance y cámara) | coordenadas isotrópicas, escala torso |
| 3-4 | `hip_center_motion_mean`, `shoulder_center_motion_mean` | media de |ΔH|/s, |ΔS|/s | desplazamiento global de pelvis/tronco | igual semántica |
| 5-6 | `vertical_motion_mean`, `horizontal_motion_mean` | media de |ΔH_y|/s y |ΔH_x|/s | oscilación vertical y avance de la pelvis | igual semántica |
| 7-10 | `left/right_ankle_rel_motion_mean`, `left/right_knee_rel_motion_mean` (V4: `*_motion_mean`) | media de |Δ(p − H)|/s | movimiento de la extremidad **relativo a la pelvis** | **C**: V4 incluía la traslación global |
| 11 | `leg_rel_motion_asymmetry` | asim(tobillo izq., tobillo der.) | asimetría del movimiento relativo de las piernas | usa 7-8 corregidos |
| 12-13 | `ankle_rel_vrange_left/right` (V4: `ankle_vertical_range_*`) | rng((A_y − H_y)/s) | elevación vertical del tobillo respecto a la pelvis | **C**: V4 usaba y absoluta (mezclaba camara/desplazamiento) |
| 14 | `ankle_rel_vrange_asymmetry` | asim(12, 13) | asimetría de elevación | usa 12-13 |
| 15-16 | `knee_rel_vrange_left/right` | rng((K_y − H_y)/s) | elevación de la rodilla respecto a la pelvis | **C** |
| 17 | `step_regularity_score` | 1/(1+CV de intervalos entre picos); NaN si hay < 3 picos | regularidad del ritmo | **A6**: una sola definición (V4 caía a otra fórmula) |
| 18-19 | `left/right_wrist_rel_motion_mean` | media de |Δ(W − hombro del mismo lado)|/s | movimiento de la mano relativo a su hombro | **C** |
| 20 | `arm_swing_angle_mean` (V4: `arm_swing_mean`) | media de 22 y 23 | amplitud angular del balanceo de brazos (rad) | **C**: V4 era el rango de x absoluta de la muñeca |
| 21 | `arm_swing_angle_asymmetry` | asim(22, 23) | asimetría del balanceo | **C** |
| 22-23 | `left/right_arm_swing_angle` (V4: `*_arm_range`) | rng(θ), θ = ángulo con signo entre el eje del tronco (S→H) y el vector hombro→muñeca | balanceo angular de cada brazo | **C**; en vista frontal la proyección subestima el balanceo (limitación de 2D) |
| 24-25 | `shoulder_width_mean`, `hip_width_mean` | media de |LS − RS|/s, |LH − RH|/s | proxy de la vista (lateral ≈ pequeño, frontal ≈ grande), no de la marcha | se conserva en V5-P; **se elimina en V5-S** |
| 26-27 | `trunk_inclination_mean/std` | |atan2(S_x − H_x, H_y − S_y)| en grados | inclinación del tronco respecto a la vertical de la imagen | **D**: ángulo en coordenadas isotrópicas (V4 dependía del aspecto) |
| 28-29 | `trunk_sway_mean/std` | |S_x − H_x|/s | desplazamiento lateral hombros-caderas | isotrópico |
| 30 | `posture_stability_score` | 1/(1 + std(sway) + std(inclinación)/45) | estabilidad postural | igual fórmula |
| 31 | `estimated_step_count` | picos de la altura relativa de cada tobillo (umbral media + 0,2 sd, separación ≥ 0,25 s) | número de eventos de paso en 2,6 s | señal relativa a la pelvis; **A8**: fps = 15 exacto |
| 32 | `estimated_cadence_steps_per_min` | pasos / (40/15 s) · 60 | cadencia aproximada | duración **constante** (V4 dependía de la ventana efectiva) |
| 33 | `step_frequency_hz` | pasos / (40/15 s) | = cadencia/60 (redundante) | se elimina en V5-S |
| 34 | `gait_variability` | media de std(mov. rel. tobillo izq.), std(mov. rel. tobillo der.), std(mov. cadera) | variabilidad del movimiento | tobillos relativos |
| 35 | `motion_smoothness` | 1/(1 + std(jerk de la cadera)) | suavidad del avance | rejilla uniforme |
| 36 | `rhythm_variability` | CV de los intervalos entre picos | irregularidad del ritmo | igual |

## Secuencia [68 × 40]
Posiciones: (x, y) de 17 landmarks, relativas a H, divididas por `s` (34 canales). Velocidades: diferencia de las **mismas** posiciones (34 canales, por paso de 1/15 s; la primera muestra vale 0). Orden de canales idéntico a V4 (compatibilidad con la arquitectura y la permutación L/R).

## Espejo (`mirror_seq`, `mirror_feat`)
Intercambia izquierda/derecha en posiciones **y** velocidades, y niega el eje x en posiciones **y** velocidades (V4 negaba solo las posiciones: `deep_common.py:422`). Las características se permutan con los pares L/R de la tabla (7-10, 12-13, 15-16, 18-19, 22-23). Verificado numéricamente reflejando los landmarks (prueba `espejo V5 … == landmarks reflejados`, error 1,8·10⁻¹⁵).

## Limitaciones geométricas (declaradas)
- Todo sigue siendo 2D; la perspectiva y la rotación de la persona respecto a la cámara no se corrigen.
- La longitud del torso se acorta si la persona se inclina hacia la cámara; se usa la mediana de la ventana.
- Los ángulos de brazo y las características de tronco dependen de la vista (en vista frontal el balanceo no se proyecta).
- No se convierte a metros: no hay calibración ni estatura conocida.
