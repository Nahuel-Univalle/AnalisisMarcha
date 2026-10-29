# Modelo Deep Learning de análisis de marcha — documentación técnica

Para desarrolladores. Explica el pipeline completo de la **versión candidata final**
(`models/gait_deep/`), desde el vídeo hasta la probabilidad por clase.

> El sistema **no diagnostica**. Devuelve un patrón de marcha compatible, con
> probabilidades y una advertencia explícita de que el resultado es orientativo.

---

## 0. Resumen del flujo

```
vídeo (.mp4 / .mov / .webm)
  → OpenCV: apertura y lectura de frames
  → MediaPipe Pose (model_complexity=1): landmarks corporales por frame
  → CSV de landmarks  (data/video_training/deep/... o tmp/ en inferencia)
  → normalización + remuestreo → secuencia [68 canales, 96 pasos]
  → 36 características de marcha (build_feature_row)  → estandarización (scaler)
  → GaitTemporalModel (PyTorch)  → logits / T=0.5  → softmax
  → { normal, parkinson, esclerosis_multiple, riesgo_caida }  (suman 1)
```

El **mismo código** (`deep_common.py`) construye la secuencia y las features en
entrenamiento y en inferencia. No hay dos pipelines.

---

## 1. Entrada y validación del vídeo

- Formatos aceptados: `video/mp4`, `video/quicktime`, `video/webm`. Tamaño máx. 120 MB (`route.ts`).
- Antes de predecir: se ejecuta `python_analysis/analyze_video.py` (métricas visuales + vídeo anotado con landmarks).
- **Gate de calidad de pose** (`route.ts`): si `pose_detection_rate < 0.45`, o
  `frames_con_pose / frames_analizados < 0.45`, o `frames_con_pose < 15`, el
  análisis se marca `analysisReliable = false`: **no se emite clase ni confianza**,
  se devuelve un mensaje pidiendo un vídeo con cuerpo completo. El modelo binario
  histórico (`04_predict_video_with_model.py`) aplica el mismo gate.
- Vídeo dañado / no-vídeo / vacío → HTTP 400 con mensaje claro.

## 2. MediaPipe Pose → landmarks

`mediapipe.solutions.pose.Pose(static_image_mode=False, model_complexity=1,
min_detection_confidence=0.5, min_tracking_confidence=0.5)`.

- Submuestreo: 1 de cada `frame_step` frames (entrenamiento `frame_step=2`;
  inferencia idéntico).
- Se guardan **17 landmarks** (`SELECTED_LANDMARKS`): NOSE, hombros, codos,
  muñecas, caderas, rodillas, tobillos, talones, puntas de pie. Por landmark:
  `x, y, z, visibility` (0–1, normalizados al tamaño de imagen).
- Un frame es "válido para secuencia" si tiene los **8 landmarks núcleo**
  (`CORE_LANDMARKS`: hombros, caderas, rodillas, tobillos).
- Los landmarks ausentes en un frame se marcan `NaN` y se interpolan en el tiempo
  (los pies suelen tener baja visibilidad). **No se inventan landmarks**: la
  interpolación es lineal entre valores observados del mismo landmark.

## 3. Normalización → secuencia temporal fija

`deep_common.frames_to_sequence(frames)`:

1. **Traslación**: origen = centro de caderas de cada frame → posiciones relativas al cuerpo.
2. **Escala**: se divide por la **mediana (por clip)** de la longitud de tronco
   (distancia centro-hombros ↔ centro-caderas; reserva: ancho de hombros / caderas).
   → invariante al tamaño de la persona en el frame y a la distancia a la cámara.
3. **Canales de posición**: 17 landmarks × (x', y') = 34.
4. **Canales de velocidad**: diferencia temporal de cada canal de posición
   (primer valor = 0) = 34 más. **Total 68 canales.**
5. **Remuestreo temporal**: interpolación lineal sobre tiempo normalizado [0, 1]
   a **T = 96 pasos**. Absorbe fps y duración variables.
6. `nan_to_num` final. Resultado: `float32 [68, 96]`.

Mínimo `MIN_VALID_FRAMES = 12` frames útiles; por debajo, el clip se descarta
(entrenamiento) o devuelve "calidad insuficiente" (inferencia).

## 4. Las 36 características de marcha

`video_training_common.build_feature_row(...)` — **se reutilizan tal cual** del
pipeline histórico. Cubren: velocidad, cadencia, simetría (piernas/tobillos/brazos),
estabilidad postural, variabilidad de zancada, movimiento y rango de brazos,
amplitud de movimiento (tobillo/rodilla), coordinación / suavidad, inclinación y
oscilación del tronco, y parámetros temporales (nº de pasos, frecuencia de paso,
variabilidad de ritmo). Lista completa en `FEATURE_COLUMNS`.

**Escalado** (`FeatureScaler`, guardado en `gait_deep_feature_scaler.json`):
imputación por mediana (aprendida en train) → estandarización (media/desv de train).
En inferencia se aplica el **mismo scaler serializado**.

## 5. Arquitectura — `GaitTemporalModel`

~17.860 parámetros. `deep_common.build_model(config)` — config en `gait_deep_config.json`.

| Bloque | Capas |
|---|---|
| **Rama temporal (CNN 1D dilatada)** | `Conv1d(68→24, k=5, pad=2)` → BN → GELU → Dropout(0.3) → `Conv1d(24→32, k=3, dil=2, pad=2)` → BN → GELU → Dropout(0.3) → `Conv1d(32→32, k=3, dil=4, pad=4)` → BN → GELU → **pooling media ⊕ máximo** sobre el tiempo → 64-d |
| **Rama de features** | `Linear(36→24)` → BN → GELU → Dropout(0.3) → `Linear(24→16)` → GELU → 16-d |
| **Fusión** | `concat(80)` → Dropout(0.4) → `Linear(80→32)` → GELU → `Linear(32→4)` |

**Por qué así** (justificado en la ablación, `docs/informe_tecnico_final.md` §E–F):
136 vídeos / 86 sujetos → capacidad mínima. La CNN 1D con *global pooling* es
invariante a *dónde* cae el ciclo de marcha en el clip; las dilataciones 1-2-4
cubren varios ciclos con T=96. La rama de features añade robustez ante cambio de
distribución (pierde menos al normalizar fps/resolución).

## 6. Salida y calibración

- `softmax(logits / T)` con **T = 0.5** (`config["temperature"]`).
- **Temperature scaling** (Guo et al. 2017): 1 parámetro, ajustado sobre las
  validaciones internas concatenadas de la CV (nunca sobre el test OOF),
  restringido a [0.5, 3.0]. Sin la cota, el óptimo de NLL (T≈0.16) satura toda
  predicción a ~100 %.
- Calibración OOF: ECE 0.28 (crudo, infra-confiado) → **0.15** con T=0.5. La
  confianza es **indicador ordinal**, no probabilidad clínica exacta.
- `label_map`: `{0: normal, 1: parkinson, 2: esclerosis_multiple, 3: riesgo_caida}`
  (`gait_deep_label_map.json`).

## 7. Inferencia — `13_predict_deep_video.py`

```
--video <ruta> [--output-json <ruta>]
```

1. `extract_video_features(...)` → landmarks + 36 features + calidad (mismo código que entrenamiento).
2. Gate: si `sequence is None` (frames válidos < 12) → `modelUsed:false` + mensaje.
3. `FeatureScaler.from_json(...)` → estandariza las 36 features.
4. `build_model(config)` + `load_state_dict(gait_deep_model.pt)` + `model.eval()`.
5. `softmax(model(seq, feat) / temperature)` → 4 probabilidades.
6. JSON de salida: `detectedClass`, `detectedClassLabel`, `classProbabilities`
   (4), `confidence`, `riskLevel`, `probability_parkinson`/`probability_normal`
   (compatibilidad), `featureHighlights` (10 conceptos de marcha legibles),
   `modelVersion`, `orientationText`, `disclaimer`, métricas del modelo.

## 8. Integración con la aplicación

`src/app/api/analysis/video/route.ts` → `runVideoFeaturePrediction()`:

- **Tier 1**: `13_predict_deep_video.py` (este modelo). Si `modelUsed` → se usa.
- **Tier 2**: `04_predict_video_with_model.py` (modelo binario histórico Parkinson vs normal) — solo si Tier 1 no está disponible.
- **Tier 3**: reglas heurísticas (`gaitEvaluation.ts`) — último recurso.

Cuando el Deep Learning responde correctamente, **Tier 2 y 3 no se ejecutan**.
Persistencia: `GaitAnalysis` + `AssociatedCondition` (texto por clase detectada) +
`DetectedSignal` + `GaitParameter` + `SystemLog` (`GAIT_ANALYSIS_MODEL` con
`modelVersion`, para trazabilidad).

## 9. Reproducibilidad

Todo en `models/gait_deep/`:

| Archivo | Contenido |
|---|---|
| `gait_deep_model.pt` | pesos PyTorch |
| `gait_deep_config.json` | arquitectura, hiperparámetros, seed, `temperature`, `model_version`, `weights_sha256_12`, exclusiones, nº muestras/sujetos, fecha, framework |
| `gait_deep_feature_scaler.json` | medianas / medias / desv. de las 36 features (de train) |
| `gait_deep_label_map.json` | clase ↔ etiqueta + `model_version` |
| `gait_deep_cv_metrics.json` | métricas OOF, `cv_stability_multiseed` (5 semillas), calibración, folds |
| `gait_deep_training_history.json` | curvas del modelo final + resumen por fold |
| `oof_predictions.npz` | probabilidades OOF (crudas, calibradas y promedio de 5 semillas) |
| `audit/`, `experiments/` | auditoría, tabla por-vídeo, comparaciones, sesgo de fuente |

Reentrenar (**solo si es necesario**):
```
python scripts/video_training/01_build_video_manifest.py
python scripts/video_training/02_extract_pose_features.py --frame-step 2
python scripts/video_training/deep/10_build_sequence_dataset.py
python scripts/video_training/deep/11_train_deep_model.py --epochs 240 --patience 35 --folds 5 --seed 42 --repeats 5
python scripts/video_training/deep/12_evaluate_deep_model.py
python scripts/video_training/deep/20_audit_model.py
```

## 10. Limitaciones (resumen — detalle en `informe_tecnico_final.md` §J)

- Dataset pequeño (136 vídeos / 86 sujetos); métrica por split ±0.04 → se reporta media±desv de 5 semillas.
- **Sesgo de fuente**: las 4 clases vienen de 2 colecciones con fps/resolución/duración muy distintos; un clasificador de solo-metadatos alcanza ~0.90. Al normalizar fps/resolución la ventaja del DL sobre baselines se anula.
- `esclerosis_multiple` y `riesgo_caida` sin ID de sujeto (1 vídeo = 1 sujeto asumido); se confunden entre sí.
- Parkinson: 7 sujetos; PD_ML/PD_MD/PD_SV = mismos sujetos a distinta severidad; `severe` = 1 sujeto → **sin clasificación de severidad** (solo metadato).
- `riesgo_caida` no es clínicamente excluyente de Parkinson/EM: la clasificación en 4 clases es una aproximación operativa; se exponen las 4 probabilidades.
