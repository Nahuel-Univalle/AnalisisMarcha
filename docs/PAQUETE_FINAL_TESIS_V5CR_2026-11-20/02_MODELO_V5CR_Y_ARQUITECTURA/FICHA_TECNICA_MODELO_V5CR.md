# Ficha técnica del modelo V5-CR (modelo principal de la aplicación)

> Todo lo siguiente se contrastó con el checkpoint, su configuración, el escalador, el mapa de etiquetas y el código real. Datos máquina-legibles: `FICHA_TECNICA_V5CR_DATOS.json`. Capas y parámetros: `arquitectura_capas_V5CR.csv`. Diagrama: `06_FIGURAS_Y_GRAFICAS/fig_arquitectura_GaitTemporalModel_V5CR.png`.
> Estado: **clasificación experimental de patrones de marcha, orientativa, no diagnóstica; validación interna sobre 117 videos; sin validación clínica ni externa.**

## 1. Identificación
| Campo | Valor (verificado) |
|---|---|
| Identificador oficial | `gait_deep_v5exp_V5CR_7e9ed60965fe` |
| SHA-256 del checkpoint (`.pt`) | `7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade` |
| SHA-256 config / escalador / etiquetas | `4128ef87…4076` / `ba91a6a6…31d2` / `47b3b446…b986` (completos en `deployment_manifest.json`) |
| Verificación | Los 4 hashes recalculados el 2026-11-20 coinciden con `models/gait_deep_v5cr/deployment_manifest.json`. Frente al checkpoint original de `docs/optimizacion_final_v5_2026-11-19/checkpoints/`, **los pesos (`.pt`) y el mapa de etiquetas son idénticos byte a byte**; la copia desplegada difiere solo en dos archivos de metadatos: `config.json` (campo `status` corregido de «V5-C» a «V5-CR») y `feature_scaler.json` (la lista `columns` tenía 36 nombres heredados y ahora tiene los 33 reales; las estadísticas no cambiaron) |
| Ubicación | `models/gait_deep_v5cr/` (archivos), selección en `src/lib/ml/activeModel.ts` (`DEFAULT_GAIT_MODEL = "v5cr"`) |
| Estado en el repositorio | Directorio **sin seguimiento de Git** (el último commit es `ef41974 ModeloDeepLearningV4`); los cambios V5-CR no están confirmados en un commit |
| Respaldo | V4 activo previo `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1` (SHA-256 `7b4ac547…400d`) en `models/gait_deep_v4exp_bn_candidate_v1/`; **no se usa automáticamente** si V5-CR falla (variable `GAIT_MODEL_VERSION=v4` es un retroceso explícito) |
| Estado declarado en config | «EXPERIMENTAL V5-CR; prototipo orientativo, sin validacion clinica; entrenado con 117 videos» (se corrigió en la copia desplegada la etiqueta «V5-C» heredada; los pesos no se modificaron) |

## 2. Qué es entrenado y qué es preentrenado
- **MediaPipe Pose** (red de estimación de pose **preentrenada**, `model_complexity=1`, detección/seguimiento 0,5): extrae 17 landmarks por cuadro. **No fue entrenada ni ajustada en este proyecto.**
- **GaitTemporalModel V5-CR** (clasificador propio): entrenado en este proyecto, con **17 788 parámetros entrenables**, a partir de landmarks y características derivadas.

## 3. Arquitectura real (PyTorch, CPU)
Clase `GaitTemporalModel` (`scripts/video_training/deep/deep_common.py::build_model`), CNN 1D de **dos ramas**:

| Rama / bloque | Capas (según `state_dict`) | Salida |
|---|---|---|
| Secuencia | Conv1d(68→24, k=5, pad 2) · BatchNorm · GELU · Dropout 0,3 → Conv1d(24→32, k=3, dilación 2) · BatchNorm · GELU · Dropout 0,3 → Conv1d(32→32, k=3, dilación 4) · BatchNorm · GELU | [B, 32, 40] → agrupación temporal **media + máximo** → [B, 64] |
| Características | Linear(33→24) · BatchNorm · GELU · Dropout 0,3 → Linear(24→16) · GELU | [B, 16] |
| Fusión y cabeza | concatenación (64+16 = 80) → Dropout 0,4 → Linear(80→32) · GELU → Linear(32→4) | logits [B, 4] |

Parámetros: secuencia 13 800; características 1 264; cabeza 2 724; **total 17 788** (calculado del checkpoint; los `running_mean/var` de BatchNorm son *buffers*, no parámetros entrenables). El desglose por capa está en `arquitectura_capas_V5CR.csv`.

## 4. Entradas, tiempo y orden
| Concepto | Valor |
|---|---|
| Secuencia | **68 × 40**: 34 canales de posición (x, y de 17 landmarks, relativas a la cadera, divididas por la longitud del torso) + 34 canales de velocidad (diferencia de las mismas posiciones por paso de 1/15 s; primera muestra = 0) |
| Landmarks (17) | NOSE, L/R SHOULDER, ELBOW, WRIST, HIP, KNEE, ANKLE, HEEL, FOOT_INDEX |
| Características tabulares | **33**, orden en `config.feature_names` y en `TABLA_33_CARACTERISTICAS_V5CR.csv` (idéntico al del escalador) |
| Frecuencia temporal | **15 Hz** (rejilla fija; el video se reduce a ≤ 720 px) |
| Ventana | **2,6 s** = 40 muestras (`(40−1)/15`) |
| Tramo analizado por video | desde el primer cuadro con pose, hasta **5,03 s** (o menos si el video es más corto) |
| Ventanas | inicio cada **0,4 s** dentro del tramo; se aceptan las que tienen ≥ 20 cuadros con pose reales (de 40); se seleccionan **K ≤ 5** equiespaciadas |
| Clases (orden) | `normal`, `parkinson`, `esclerosis_multiple`, `riesgo_caida` (`label_map.json`) |

## 5. Preprocesamiento (resumen; detalle en `07_PREPROCESAMIENTO_Y_FORMULAS/`)
1. **Landmarks**: se descartan puntos con visibilidad < 0,2; un cuadro solo se usa si tiene hombros y caderas. Coordenadas isotrópicas `x·(ancho/alto), y` (**corrección por relación de aspecto**).
2. **Interpolación relativa a la cadera** (`resample_grid_rel`): se interpola el centro de caderas H y cada landmark **relativo a H** por separado, y se reconstruye `p = (p−H)+H`. Corrige una fuga de traslación que tenía V5-P (interpolación de coordenadas absolutas con el borde repetido para landmarks enmascarados): 370 de 633 ventanas reales se veían afectadas; con V5-CR **0 de 633** cambian ante una cámara que sigue a la persona.
3. **Escala corporal**: mediana de |S−H| (longitud del torso) en la ventana; se descarta la ventana si s < 10⁻⁴.
4. **Landmarks faltantes**: sin ≥ 2 observaciones no se interpola → NaN; en la secuencia los NaN pasan a 0; en las características los NaN se imputan con la **mediana del entrenamiento** (ver 6).
5. **Movimiento de cámara**: las 33 características y la secuencia son relativas a la cadera (se eliminaron `hip_center_motion_mean`, `shoulder_center_motion_mean`, `horizontal_motion_mean`; `body_motion_*`, `motion_smoothness` y `gait_variability` se redefinieron sin avance horizontal). Se emite además una advertencia `CAMARA_MOVIL` si la medición de movimiento de fondo supera 10⁻⁴.

## 6. Normalización e imputación
`FeatureScaler` (`deep_common.py`): sobre el conjunto de ENTRENAMIENTO, mediana por característica (`np.nanmedian`, 0 si no es finita) → NaN se sustituyen por la mediana → media y desviación (desviación < 10⁻⁸ → 1). En inferencia se aplica exactamente la misma transformación con los 33 valores del `feature_scaler.json` (medianas, medias, desviaciones; desviación mínima 0,0163; sin valores no finitos). El escalador y la temperatura se ajustan **solo con datos de entrenamiento** de cada partición (sin fuga).

## 7. Logits, agrupación y calibración
1. Para cada una de las K ventanas, el modelo produce 4 logits.
2. **Agregación**: media aritmética de los logits de las K ventanas (float32).
3. **Calibración por temperatura**: `z = logit_medio / T`, con **T = 0,6615** (ajustada en la validación interna anidada del modelo final).
4. **Probabilidades**: `softmax(z)` → 4 probabilidades que suman 1. La clase indicada es la de mayor probabilidad; esa probabilidad se presenta como «confianza del modelo» (no es la probabilidad de padecer una enfermedad).
5. Nota metodológica: la ECE sin calibrar de V5-CR es peor que la de V4 activo; la temperatura la reduce a 0,064 en la evaluación con temperatura por partición (ver `04_METRICAS_Y_COMPARACIONES/`).

## 8. Entrenamiento del modelo final (config del checkpoint y código `fase8_entrenar_cr.py`, `v5_train_core.py`)
Adam (lr 1e-3, weight decay 2e-4), ReduceLROnPlateau (factor 0,5, paciencia 8, sobre la pérdida de entrenamiento), entropía cruzada con **pesos de clase** inversamente proporcionales a la frecuencia y *label smoothing* 0,05, recorte de gradiente 5, lote 16, máx. 240 épocas. Aumento de datos en entrenamiento: espejo horizontal físicamente correcto (prob. 0,5; intercambia izquierda/derecha y niega x en posiciones **y** velocidades) y ruido gaussiano σ = 0,01 en posiciones (prob. 0,6) con velocidades recalculadas. Época óptima **E\* = 73** y temperatura elegidas con validación cruzada agrupada interna (3 particiones, semilla 4200) y **modelo final entrenado con los 117 videos** (por eso su exactitud no se mide con ese modelo; las métricas proceden de la validación cruzada fuera de partición).

## 9. Criterios de análisis no concluyente
- El predictor devuelve `pose_insufficient` si el video no se puede abrir/decodificar, no hay cuadros con pose, el tramo es demasiado corto o **ninguna ventana** cumple ≥ 20 cuadros con pose.
- La API (`src/app/api/analysis/video/route.ts`) marca el análisis como **no concluyente** si `pose_detection_rate < 0,45`, la razón cuadros-con-pose/cuadros < 0,45, `framesWithPose < 15` o el predictor devolvió `pose_insufficient`: se anulan clase, probabilidades y confianza (nunca se inventa una clasificación) y se guarda como «no concluyente».
- Los fallos del propio modelo (tiempo agotado, error interno, artefactos ausentes) devuelven un error explícito; **no** se sustituye por V4 ni por reglas.

## 10. Rendimiento interno (resumen; fuentes en `04_…`)
Exactitud 0,8598 · F1 macro 0,7852 · F1 por clase 0,9557 / 0,9207 / 0,6839 / 0,5806 (normal / Parkinson / esclerosis múltiple / riesgo de caída) · ECE 0,131 sin calibrar, 0,064 con temperatura por partición. Validación cruzada agrupada por sujeto, 5 semillas × 5 particiones, 117 videos / 67 grupos técnicos. **No es rendimiento clínico.**
