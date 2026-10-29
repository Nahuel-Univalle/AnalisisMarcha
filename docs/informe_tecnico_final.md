# Informe técnico final — Análisis de marcha con Deep Learning (4 clases)

Fecha: 2026-09-07 · Pipeline: MediaPipe Pose → secuencia temporal + 36 características → CNN temporal 1D (2 ramas) → 4 clases → informe orientativo.
Clases: `normal` · `parkinson` · `esclerosis_multiple` · `riesgo_caida`.

> El sistema **no emite diagnóstico**. Todo resultado se expresa como *"patrón de
> marcha compatible con…"*, *"resultado orientativo"*, *"se recomienda valoración
> por un profesional de salud"*.

---

## A. Dataset final

| Clase | Vídeos | Sujetos | Documentados | Fuente / grabación |
|---|---:|---:|---:|---|
| normal | 59 | 30 | 30 | `.MOV` 1920×1080 · ~33 fps · ~4.9 s · pose 0.78 |
| parkinson | 28 | 7 | 7 | `.MOV` 1920×1080 · ~40 fps · ~13.5 s · pose 0.83 |
| esclerosis_multiple | 29 | 29 | 0 | `.mp4` 1280×720 · 24 fps · ~9.9 s · pose 1.00 |
| riesgo_caida | 20 | 20 | 0 | `.mp4` 1280×720 · 24 fps · ~10.0 s · pose 1.00 |
| **Total** | **136** | **86** | 37 | |

**Exclusiones (documentadas en `dataset_meta.json`):**
- `VideoEscleorosis7.mp4` — **byte-idéntico** (mismo MD5 `82162b64…`) a `VideoEscleorosis6.mp4`. Era un duplicado literal; con él, el mismo vídeo caía en *train* y *test* de folds distintos (fuga). Excluido de train/val/test vía `MANIFEST_EXCLUDE` en `video_training_common.py` (el archivo NO se borra del disco). EM pasa de 30→29 vídeos.
- No hay más duplicados exactos ni re-codificados en los 136 restantes.

**Severidad de Parkinson (metadato, NO objetivo):** mild = 6 sujetos, moderate = 7, **severe = 1 sujeto / 2 vídeos**. Con 1 solo sujeto "severe" no es defendible una cabeza de clasificación de severidad → se conserva `severity` como columna de metadatos.

---

## B. Arquitectura final

`GaitTemporalModel` (`scripts/video_training/deep/deep_common.py`), **17.860 parámetros**, PyTorch 2.14 CPU.

```
Entrada:
  secuencia  [68 canales, 96 pasos]  = 17 landmarks × (x,y) normalizados
             + sus velocidades (Δt).  Normalización: origen = centro de caderas,
             escala = longitud de tronco; remuestreo temporal a T=96.
  features   [36]  = las 36 características de marcha del pipeline histórico
             (velocidad, cadencia, simetría, estabilidad, variabilidad, brazos,
             amplitud, coordinación, postura, parámetros temporales), imputadas
             y estandarizadas.

Rama temporal (CNN 1D dilatada):
  Conv1d(68→24, k=5, pad=2)     → BatchNorm → GELU → Dropout(0.3)
  Conv1d(24→32, k=3, dil=2)     → BatchNorm → GELU → Dropout(0.3)
  Conv1d(32→32, k=3, dil=4)     → BatchNorm → GELU
  → pooling temporal (media ⊕ máximo) → 64-d

Rama de features:
  Linear(36→24) → BatchNorm → GELU → Dropout(0.3) → Linear(24→16) → GELU → 16-d

Fusión:
  concat(80) → Dropout(0.4) → Linear(80→32) → GELU → Linear(32→4) → softmax
  (logits / T=0.5 en inferencia, temperature scaling)
```

**Por qué esta arquitectura y no LSTM/GRU/TCN profunda:** 136 vídeos / 86 sujetos → capacidad mínima obligatoria. Una CNN 1D con *global pooling* es invariante a *dónde* cae el ciclo de marcha en el clip, entrena estable en CPU y tiene el menor nº de parámetros por campo receptivo; las dilataciones 1‑2‑4 cubren varios ciclos de zancada con T=96. Ablación (sección F) justifica que la rama temporal es la que aporta señal.

---

## C. Entrenamiento

| Parámetro | Valor |
|---|---|
| Folds | StratifiedGroupKFold k=5 por `subject_id` |
| Semilla | 42 (determinista: `torch.use_deterministic_algorithms`, 1 hilo) |
| Épocas máx. / early stopping | 240 / patience 35 sobre macro‑F1 de validación interna (restaura mejor) |
| Batch size | 16 (el último lote de tamaño 1 se fusiona: BatchNorm no admite lote de 1) |
| Optimizador | Adam, lr 1e‑3, weight_decay 2e‑4, `ReduceLROnPlateau` |
| Pérdida | CrossEntropy ponderada por clase + label_smoothing 0.05 |
| Augmentation | **solo train**: recorte+reinterpolación temporal, escala de amplitud, ruido gaussiano, espejo L/R coherente (nunca crea sujetos, nunca toca val/test) |
| Modelo desplegado | reentrenado con los 136 vídeos + un split interno por grupos para early stopping |

Reproducibilidad (`gait_deep_config.json` + `gait_deep_cv_metrics.json`): seed, arquitectura, hiperparámetros, lista de exclusiones, nº de muestras/sujetos, `label_map`, `feature_scaler`, temperatura, fecha, versión de framework.

---

## D. Evaluación (OOF, validación cruzada por sujeto)

**El dataset es pequeño → un único split tiene varianza alta.** Se reporta **media ± desviación sobre 5 semillas de partición** (StratifiedGroupKFold, semillas 42‑46).

| Métrica | Valor |
|---|---|
| **macro‑F1** | **0.833 ± 0.040** (por semilla: 0.777 / 0.880 / 0.876 / 0.809 / 0.821) |
| **accuracy** | **0.865 ± 0.037** |
| **balanced accuracy** | **0.830 ± 0.046** |
| macro ROC‑AUC OvR | ≈ 0.98 |

### Métricas por clase (OOF, probabilidad promediada de 5 semillas — estimación más estable)

| Clase | Precision | Recall / Sensibilidad | Especificidad | F1 | Soporte |
|---|---:|---:|---:|---:|---:|
| normal | 0.97 | 0.95 | 0.97 | 0.96 | 59 |
| parkinson | 0.90 | 0.93 | 0.97 | 0.91 | 28 |
| esclerosis_multiple | 0.83 | 0.86 | 0.95 | 0.85 | 29 |
| riesgo_caida | 0.79 | 0.75 | 0.97 | 0.77 | 20 |

Rango de F1 por clase entre las 5 semillas: normal 0.88–0.97 · parkinson 0.75–0.97 · EM 0.79–0.86 · riesgo_caida 0.63–0.77.

### Matriz de confusión (OOF, probabilidad media 5 semillas)

```
real \ pred        normal  parkinson  esclerosis_m  riesgo_caida
normal               56        3           0             0
parkinson             1       26           0             1
esclerosis_multiple   1        0          25             3
riesgo_caida          0        0           5            15
```

Normalizada por fila: `plots/confusion_matrix_normalized.png`, `audit/confusion_matrix_meanseeds_normalized.png`.

### Sobreajuste
In‑sample (modelo final sobre sus propios datos): acc 0.956 / macro‑F1 0.932.
Brecha in‑sample − OOF: **+0.09 macro‑F1** de media (rango +0.05 a +0.16 según split). Sobreajuste moderado, esperable con 136 muestras; controlado con dropout, weight decay, augmentation, early stopping y CV por sujeto.

### Errores (split primario seed 42, `audit/per_video_predictions.csv` tiene los 136)
- **normal → parkinson**: 2–3/59. Baja confianza (0.36–0.50).
- **parkinson → normal**: la mayoría son **PD_ML (leve)** — `001/002/003_PD_*_ML` — con confianza 0.33–0.51. *La marcha de Parkinson leve se parece a la normal* (coherente clínicamente).
- **parkinson → riesgo_caida**: los 2 clips **PD_SV (severo)** de `001_PD` (confianza 0.27–0.39). *La marcha de Parkinson severo es inestable* (coherente).
- **esclerosis_multiple ↔ riesgo_caida**: eje de confusión principal (ver E).

---

## E. Comparación de modelos (mismas particiones StratifiedGroupKFold, 3 semillas)

### Sobre el dataset TAL CUAL (136 vídeos)

| Modelo | macro‑F1 | accuracy | balanced acc |
|---|---:|---:|---:|
| Baseline LogisticRegression (36 features) | 0.796 ± 0.012 | 0.843 | 0.798 |
| Baseline RandomForest (36 features) | 0.794 ± 0.016 | 0.838 | 0.786 |
| Deep Learning — solo 36 features (rama MLP) | 0.798 ± 0.025 | 0.843 | 0.799 |
| Deep Learning — solo secuencia temporal | **0.882 ± 0.006** | 0.902 | 0.888 |
| **Deep Learning — secuencia + 36 features (desplegado)** | 0.845 ± 0.048 | 0.880 | 0.844 |

- Las 36 características tienen un **techo de ~0.80 macro‑F1** con cualquier clasificador (LR ≈ RF ≈ MLP).
- La rama temporal **rompe ese techo**: +0.08 macro‑F1 sobre las features solas.
- El modelo desplegado (fusión) está entre ambos: la rama de features añade robustez (ver más abajo) pero también algo de varianza.

### Confusión principal esclerosis_multiple ↔ riesgo_caida
`P(MS|real=MS) ≈ 0.51`, `P(fall|real=MS) ≈ 0.31`; `P(fall|real=fall) ≈ 0.46`, `P(MS|real=fall) ≈ 0.37`. **Las dos clases comparten masa de probabilidad**: son fenotipos de inestabilidad/coordinación alterada difíciles de separar visualmente. Es la limitación clínica real más clara del dataset (ver J).

---

## F. Ablación — ¿cuánto aporta la información temporal?

| | RAW (136) | Normalizado (fps/resolución igualados) |
|---|---:|---:|
| DL solo 36 features | 0.798 ± 0.025 | 0.741 ± 0.029 |
| DL solo secuencia | 0.882 ± 0.006 | 0.822 ± 0.006 |
| DL secuencia + features | 0.845 ± 0.048 | 0.812 ± 0.010 |
| **Δ (secuencia+feat) − (solo feat)** | **+0.047** | **+0.071** |
| Δ (solo secuencia) − (solo feat) | +0.084 | +0.081 |

**Conclusión:** la información temporal de la marcha aporta **~+0.08 macro‑F1 de forma consistente** en ambas condiciones (con y sin control del sesgo de fuente). No es un artefacto: el modelo aprende dinámica de marcha que las 36 características agregadas no capturan.

---

## G. Calibración

| | ECE | MCE | Brier |
|---|---:|---:|---:|
| Probabilidades crudas | 0.284 | 0.37 | 0.383 |
| Con temperature scaling (T = 0.5) | **0.154** | 0.64 | 0.287 |

- El modelo crudo es **infra‑confiado** (dice 55 % cuando acierta el 83 %). Se aplica *temperature scaling* con **T = 0.5**, ajustada sobre las validaciones internas concatenadas (nunca sobre el test OOF), y **restringida a [0.5, 3.0]**: sin la cota inferior el óptimo de NLL cae a T≈0.16 y **satura toda predicción a ~100 %** de confianza, lo que sería engañoso para un informe orientativo.
- Calibración residual **moderada** (ECE 0.15). La confianza debe leerse como **indicador ordinal**, no como probabilidad exacta. El informe lo refuerza con lenguaje de "resultado orientativo" y "no constituye diagnóstico".
- Gráfica: `audit/reliability_diagram.png`. Confianza media aciertos 0.57 vs errores 0.42 (cruda) → la confianza sí discrimina, sólo está mal escalada.

---

## H. Auditoría de sesgo de fuente

**Contexto:** `normal`+`parkinson` provienen de una colección (`.MOV`, 1080p, 33–40 fps) y `esclerosis_multiple`+`riesgo_caida` de otra (`.mp4`, 720p, 24 fps).

### Hallazgos

1. **Un clasificador que usa SOLO metadatos técnicos (sin marcha) alcanza:**
   - 4 clases: **RF 0.90 / LR 0.87 accuracy** (azar 0.25)
   - fuente A vs B: **1.00** (colecciones trivialmente distinguibles)
   - normal vs parkinson (dentro de A): **0.95–0.97** (normal 4.9 s vs PD 13.5 s; frame_count 159 vs 548)
   - EM vs fall (dentro de B): **0.78–0.82**
2. Diferencias entre fuentes (Cohen d): fps 1.58 · brillo −1.74 · nitidez −1.64 · saturación 1.92 · densidad de bordes −1.57 · encuadre (altura del cuerpo en el frame) **−3.36** · `pose_detection_rate` 0.78–0.83 (A) vs 1.00 (B).

### Impacto en el modelo profundo (RAW → NORMALIZADO)

| Modelo | RAW macro‑F1 | Normalizado macro‑F1 | Δ |
|---|---:|---:|---:|
| DL secuencia + features (desplegado) | 0.845 | 0.812 | **−0.033** |
| DL solo secuencia | 0.882 | 0.822 | −0.060 |
| RandomForest (36 feat) | 0.794 | 0.816 | +0.022 |
| **DL full − mejor baseline** | **+0.048** | **−0.004** | |

- Al igualar fps y resolución, el modelo profundo **pierde ~0.03–0.06 macro‑F1** → parte del rendimiento sobre el dataset crudo se apoyaba en el confound de grabación.
- Tras la normalización, el modelo profundo (**0.812**) queda **a la par de RandomForest (0.816)**: la ventaja del Deep Learning sobre los baselines **se reduce a ~0** cuando se controla el confound de fps/resolución.

### Mitigaciones y evidencia de que SÍ aprende marcha

1. **Modelos dentro de una misma fuente** (control del confound de colección), CV por sujeto:
   - **normal vs parkinson (fuente A): macro‑F1 0.952 ± 0.012 — idéntico en RAW y en normalizado (0.952).** El modelo separa la marcha parkinsoniana de la normal dentro de una colección consistente y **sin depender de fps/resolución**. Evidencia fuerte de aprendizaje real de patología de marcha. *(Matiz: dentro de A, NM y PD aún difieren en duración de clip; la normalización remuestrea a fps común y el resultado se mantiene, luego no es un puro artefacto de fps.)*
   - MS vs fall (fuente B): macro‑F1 0.74–0.76 — estable, moderado; estas dos clases se solapan de verdad.
2. La rama temporal aporta +0.08 macro‑F1 **también** en el dataset normalizado (sección F).
3. Los errores son **clínicamente coherentes** (PD leve→normal, PD severo→inestable, EM↔fall).
4. **No se eliminó ninguna característica de marcha real** para mejorar métricas.

### Normalización aplicada (dataset_norm, `dataset_norm_meta.json`)
1. Remuestreo temporal por lectura secuencial → **densidad efectiva 15 fps idéntica en las 4 clases**.
2. Reescalado a **dimensión máxima 720 px**.
3. Ventana máxima 400 frames (27 s) para acotar clips largos.
4. Después: **mismo preprocesamiento que producción** (hip‑centrado + escala de tronco + T=96 + velocidades) y **las mismas 36 características**.
5. **No se altera** la geometría de la marcha (amplitudes, asimetrías, ritmo, coordinación).

---

## I. Pruebas E2E

### Inferencia directa (`13_predict_deep_video.py`), 1 vídeo por clase

| Vídeo | Real | Predicho | Confianza | Prob. (n / p / em / rc) | modelSource | disclaimer |
|---|---|---|---:|---|---|---|
| 010_NM_02.MOV | normal | **normal** | 0.99 | 0.98 / 0.00 / 0.01 / 0.00 | gait_deep_model | sí |
| 005_PD_01_ML.MOV | parkinson | **parkinson** | 1.00 | 0.00 / 1.00 / 0.00 / 0.00 | gait_deep_model | sí |
| VideoEscleorosis25.mp4 | esclerosis_multiple | **esclerosis_multiple** | 0.96 | 0.00 / 0.00 / 0.96 / 0.03 | gait_deep_model | sí |
| RiesgoCaida18.mp4 | riesgo_caida | **riesgo_caida** | 0.99 | 0.00 / 0.00 / 0.01 / 0.99 | gait_deep_model | sí |

Las 4 probabilidades suman 1.0; existen `detectedClass`, `confidence`, `orientationText`, `disclaimer`, `featureHighlights` (10 conceptos de marcha). *No* se usa LogisticRegression como fallback. **Nota:** estos vídeos estaban en entrenamiento → confianza saturada; en vídeos nuevos la confianza es más moderada.

### Pipeline completo por la API (`POST /api/analysis/video`) + PostgreSQL

| Vídeo | Real | `detectedClass` | Conf. | HTTP | modelSource | `AssociatedCondition` en BD |
|---|---|---|---:|---|---|---|
| 019_NM_02.MOV | normal | **normal** | 0.99 | 200 | gait_deep_model | "Sin alerta específica" |
| 005_PD_02_MD.MOV | parkinson | **parkinson** | 0.99 | 200 | gait_deep_model | "Posible patrón asociado a Parkinson" |
| VideoEscleorosis27.mp4 | esclerosis_multiple | **esclerosis_multiple** | 0.98 | 200 | gait_deep_model | "Posible patrón asociado a Esclerosis Múltiple" |
| RiesgoCaida14.mp4 | riesgo_caida | **riesgo_caida** | 0.99 | 200 | gait_deep_model | "Posible patrón asociado a inestabilidad / riesgo de caída" |

- **API**: Tier 1 = Deep Learning multiclase (`runDeepGaitPrediction` primero; si responde `modelUsed`, retorna sin ejecutar el modelo binario ni las reglas). Tier 2 = modelo binario histórico. Tier 3 = reglas heurísticas.
- **PostgreSQL**: cada análisis persiste `GaitAnalysis` + `AssociatedCondition` (texto **dependiente de la clase detectada** — bug corregido) + `DetectedSignal` (0/4/3/4) + `GaitParameter` (5).
- **Informe** (`MedicalReport.tsx`): muestra dinámicamente clase detectada, probabilidades por clase, confianza, características observadas, orientación y advertencia. Sin textos exclusivos de Parkinson. Mantiene "resultado orientativo", "no constituye un diagnóstico médico", "requiere valoración profesional".

### Verificaciones metodológicas (`21_methodology_checks.py`)
- **[13] Augmentation solo en train**: OK (AST de `11_train`: `augment=False` en evaluación, variable `augment` solo en el bucle de entrenamiento).
- **[14] Sin fuga de sujeto train/test**: OK (reconstrucción de folds; cada sujeto en 1 solo fold de test; intersección train∩test = ∅).
- **[15] Independencia EM/fall**: el duplicado exacto (VideoEscleorosis6↔7) eliminado; quedan pares con vector de 36 features similar (rms_z 0.42–0.60) **sin duplicados exactos** → compatible con fenotipo compartido, no prueba de mismo sujeto. Como estas clases no tienen ID de sujeto real, cierto optimismo en su CV no puede descartarse (limitación J).

---

## J. Limitaciones reales

1. **Sesgo de fuente (la más importante):** las 4 clases provienen de 2 colecciones con parámetros de grabación muy distintos. Un clasificador que sólo ve metadatos técnicos alcanza ~0.90 accuracy. Al igualar fps/resolución, la ventaja del Deep Learning sobre los baselines desaparece (≈ RandomForest). La evidencia de aprendizaje real de marcha es indirecta: discriminación **dentro de fuente** (normal‑vs‑Parkinson 0.95, estable a la normalización), aporte temporal consistente (+0.08) y errores clínicamente coherentes.
2. **Tamaño del dataset:** 136 vídeos / 86 sujetos. La métrica de un único split de CV varía ±0.04 macro‑F1 entre semillas; se reporta media ± desviación sobre 5 semillas.
3. **Sujetos no documentados:** `esclerosis_multiple` y `riesgo_caida` no traen ID de sujeto en el nombre → se asume 1 vídeo = 1 sujeto. Si algún par fuese la misma persona, la CV de esas 2 clases sería optimista.
4. **Parkinson:** 28 vídeos de sólo 7 sujetos; los niveles PD_ML/PD_MD/PD_SV son los mismos sujetos filmados a distinta severidad. `severe` = 1 sujeto → **sin clasificación de severidad** (metadato).
5. **`riesgo_caida` no es una enfermedad mutuamente excluyente** de Parkinson o Esclerosis Múltiple. Con carpetas disjuntas y 1 etiqueta por vídeo (sin anotaciones multi‑etiqueta), la clasificación en 4 clases excluyentes es una **aproximación operativa**: el sistema devuelve el patrón más compatible y **expone las 4 probabilidades** (una persona podría mostrar P(parkinson) y P(riesgo_caida) altas a la vez). No se afirma exclusividad clínica.
6. **EM ↔ riesgo de caída** se confunden (~15–40 % según split y dirección): fenotipos de inestabilidad genuinamente solapados y la fuente más pequeña.
7. **Calibración moderada** (ECE 0.15 tras temperature scaling). La confianza es ordinal, no una probabilidad clínica exacta.
8. **Vídeo RGB monocular:** sin escala real (metros); todas las medidas son normalizadas por el cuerpo.

---

## K. Conclusión

**Estado del sistema:** funcional de extremo a extremo. `vídeo → MediaPipe → landmarks → secuencia + 36 features → CNN temporal → 4 probabilidades → clase → API (Tier 1) → PostgreSQL → informe multiclase orientativo`. Verificado con 4 vídeos (uno por clase) por inferencia directa y por la API con persistencia correcta.

**Rendimiento (honesto, tras corregir el duplicado y con CV por sujeto multi‑semilla):**
macro‑F1 **0.83 ± 0.04**, accuracy **0.87 ± 0.04**. Por clase: normal 0.96, Parkinson 0.91, EM 0.85, riesgo de caída 0.77.

**Aporte del Deep Learning:** la rama temporal añade **+0.08 macro‑F1** sobre las 36 características (consistente con y sin control de sesgo). Sobre el dataset crudo el modelo profundo supera a los baselines en +0.05; **al controlar el sesgo de fuente esa ventaja se anula** y queda a la par de RandomForest.

**Recomendación de arquitectura final:** se mantiene el modelo de **2 ramas (secuencia + 36 features)**. Aunque la ablación muestra que *solo secuencia* rinde algo más sobre el dataset crudo (0.88 vs 0.85), la fusión **pierde menos al normalizar** (−0.033 vs −0.060) → es la opción más robusta a cambio de distribución (el escenario real: vídeos nuevos de fuentes nuevas), y conserva las 36 características clínicas como entrada del modelo, según el objetivo del proyecto. Las 36 características se mantienen además en el informe como "características observadas".

**¿Listo para la documentación académica?** Sí, con la condición de presentar los resultados **con** la limitación de sesgo de fuente como hallazgo central y las cifras como media ± desviación, no como un valor puntual. El pipeline es reproducible (seed, config, scaler, exclusiones y métricas guardados) y no tiene fuga de sujeto.

### Archivos clave
- Modelo: `models/gait_deep/gait_deep_model.pt` (+ `_config.json`, `_feature_scaler.json`, `_label_map.json`, `_cv_metrics.json`, `_training_history.json`).
- Auditoría: `models/gait_deep/audit/` (`audit_report.json`, `per_video_predictions.csv` — 136 filas, `source_bias_report.json`, `methodology_checks.json`, `video_technical_metadata.csv`, 5 PNG).
- Experimentos: `models/gait_deep/experiments/experiments_report_final.json` (raw), `experiments_report_norm_final.json` (normalizado).
- Datasets: `data/video_training/deep/dataset.npz` (136), `dataset_norm.npz`, `dataset_meta.json`.
- Gráficas: `models/gait_deep/plots/` (loss, accuracy, confusión, confusión normalizada, F1 por clase).
- Pipeline: `scripts/video_training/deep/` (`10_build` … `13_predict`, `20_audit`, `21_methodology_checks`, `22_source_bias`, `23_experiments`, `24_normalized_reextract`).
