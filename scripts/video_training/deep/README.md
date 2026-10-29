# Modelo de Deep Learning para análisis de marcha (multiclase)

Pipeline temporal que clasifica un video de marcha en **4 patrones**:

`normal` · `parkinson` · `esclerosis_multiple` · `riesgo_caida`

> El sistema **no emite diagnóstico**. El resultado es una **orientación basada
> en patrones de movimiento** y siempre requiere valoración de un profesional de
> salud.

## Flujo (idéntico en entrenamiento e inferencia)

```
video
  └─ MediaPipe Pose  ─────────────►  landmarks por frame (17 puntos, x/y/z/visibility)
        └─ normalización  ─────────►  origen = centro de caderas · escala = torso
              └─ secuencia temporal fija  ──►  [68 canales, 96 pasos]
                    (17 landmarks × (x,y) + velocidades)
              └─ 36 características de marcha (build_feature_row, reutilizadas)
                    ├─ rama temporal:  Conv1D dilatada (24→32→32) + pooling avg/max
                    └─ rama de features: MLP (36→24→16)
                          └─ fusión (48→32→4) → softmax
```

## Arquitectura y por qué

- **CNN temporal dilatada compacta (~18 K parámetros)**, no LSTM/GRU profundas.
  Con ~137 videos / ~87 sujetos el riesgo de sobreajuste es alto: una CNN 1D con
  *global pooling* es invariante a *dónde* cae el ciclo de marcha en el clip,
  entrena estable en CPU y tiene el menor número de parámetros por campo
  receptivo. Las dilataciones (1, 2, 4) cubren varios ciclos de zancada con
  T = 96.
- **Doble rama**: la rama de las 36 características de marcha (velocidad,
  cadencia, simetría, estabilidad, variabilidad, brazos, amplitud, coordinación,
  postura, parámetros temporales) aporta una señal de baja varianza que
  complementa a la rama aprendida. Ablaciones: `--seq-only`, `--feat-only`.
- **Anti-sobreajuste**: BatchNorm + Dropout (0.3–0.4) + weight decay +
  `label_smoothing` + `CrossEntropy` ponderada por clase + early stopping sobre
  macro-F1 de validación + **validación cruzada por sujeto** +
  **augmentation solo en train** (recorte/reinterpolación temporal, escala de
  amplitud, ruido gaussiano, espejo L/R coherente). El augmentation nunca crea
  sujetos ni toca validación/prueba.

## Scripts

| Script | Rol | Salida |
|---|---|---|
| `10_build_sequence_dataset.py` | Manifest → pose → secuencias + 36 features | `data/video_training/deep/dataset.npz`, `dataset_meta.json` |
| `11_train_deep_model.py` | `StratifiedGroupKFold(k=5)` por `subject_id` + modelo final | `models/gait_deep/*` + `plots/*` |
| `12_evaluate_deep_model.py` | Métricas OOF + baselines (LogReg / RF) sobre las mismas particiones | `gait_deep_evaluation_report.{json,md}` |
| `13_predict_deep_video.py` | Inferencia de un video (mismo preprocesamiento) | JSON: clase, probabilidades, confianza, características, señales |
| `deep_common.py` | Núcleo compartido (secuencias, modelo, métricas, augmentation) | — |

## Uso

```powershell
.\.venv311\Scripts\python.exe scripts\video_training\01_build_video_manifest.py
.\.venv311\Scripts\python.exe scripts\video_training\02_extract_pose_features.py --frame-step 2
.\.venv311\Scripts\python.exe scripts\video_training\deep\10_build_sequence_dataset.py
.\.venv311\Scripts\python.exe scripts\video_training\deep\11_train_deep_model.py --epochs 240 --patience 35 --folds 5
.\.venv311\Scripts\python.exe scripts\video_training\deep\12_evaluate_deep_model.py
.\.venv311\Scripts\python.exe scripts\video_training\deep\13_predict_deep_video.py --video <ruta_video>
```

Requisitos Python extra: `torch` (CPU) y `matplotlib` (ver `requirements.txt`).

## Integración con la app

`src/app/api/analysis/video/route.ts` invoca `13_predict_deep_video.py` como
**Tier 1**. Si el modelo profundo no está disponible o la calidad del video es
insuficiente, cae al modelo binario histórico (`models/video_parkinson/`) y, por
último, a reglas heurísticas. El modelo binario `LogisticRegression` se conserva
solo como **baseline / comparación**, no como modelo principal.
