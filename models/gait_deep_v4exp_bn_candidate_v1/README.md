# Model card — `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`

Clasificación **experimental** de patrones de marcha en 4 clases: `normal` · `parkinson` · `esclerosis_multiple` · `riesgo_caida` (en ese orden; índices 0–3).

**No es un diagnóstico médico. No está validado clínicamente.**

## Modelo

| | |
|---|---|
| Versión | `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1` |
| SHA-256 de los pesos | `7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d` |
| Modelo base | `gait_deep_v4exp_protocolV2_M1_20261029_162234_d7323250d26f` (`models/gait_deep_v4exp/`, SHA `d7323250…5213048`; se conserva intacto para rollback) |
| Arquitectura | `GaitTemporalModel`: CNN temporal sobre la secuencia de pose [68 × 96] más una rama MLP de 36 features; 18.088 parámetros. Idéntica al modelo base |
| Datos | Dataset V4: `dataset_v4_preview.npz`, 117 videos y 67 grupos de sujeto |
| Temperatura | 0,9022, la misma del modelo base |
| Scaler / label map | Idénticos al modelo base, byte a byte |
| Inferencia | `scripts/video_training/deep/14_predict_deep_video_v4exp.py`, que comprueba el SHA-256 al cargar |

**Archivos de esta carpeta:**
- `.pt`, `_config.json`, `_feature_scaler.json`, `_label_map.json`: congelados en el Paso 19; verificables con `outputs/dataset_v4_4class/step19_candidate/CANDIDATE_SHA256.txt`.
- `README.md`: este documento.

## Método

**Recalibración de BatchNorm sobre el modelo existente.** No hubo reentrenamiento: los 22 tensores entrenables son idénticos al modelo base.

- **Defecto que corrige** (Paso 17): las estadísticas BatchNorm del modelo base, acumuladas por media móvil (`momentum` 0,1) durante el entrenamiento, no eran representativas. Por eso el modelo base acertaba solo 12/26 Parkinson sobre sus propios datos.
- **Recalibración** (Pasos 18–19):
  1. Reset de `running_mean` / `running_var`.
  2. Un forward sin gradientes con las X de los 117 videos de entrenamiento en un único lote, sin etiquetas, con **solo** las capas BatchNorm en `train()` y Dropout en `eval()`.
  3. `momentum` restaurado.
- **Validación sin leakage:** el mismo procedimiento aplicado a cada fold con su TRAIN (intersección con test = 0). Detalle en `outputs/dataset_v4_4class/step18_bn/INFORME_PASO18_BATCHNORM.md`.

## Rendimiento (OOF, validación agrupada por sujeto 5 × 5, Paso 18)

**No** es rendimiento externo ni clínico.

| | Modelo base | **Este modelo** |
|---|---:|---:|
| Accuracy | 0,834 | **0,851** |
| Macro-F1 | 0,725 ± 0,014 | **0,744 ± 0,010** (mejora en 5/5 repeticiones) |
| F1 Normal | 0,953 | 0,963 |
| F1 Parkinson | 0,846 | 0,881 |
| F1 EM | 0,739 | 0,755 |
| F1 Riesgo de caída | 0,363 | **0,378 (bajo)** |

El 98 % sobre los 117 videos de entrenamiento (resustitución) **no es una métrica de generalización** y no debe citarse como tal.

## Integración

**Paso 20:** `INTEGRATION-CONDITIONAL`. Rama `test/model-bn-recalibrated-v1`, sin merge.

| Prueba | Resultado |
|---|---|
| API | 20/20 |
| Interfaz E2E | 2 flujos completos (usuario y admin) |
| Historial / informes | OK |
| Responsive | 1440, 768 y 390 px |
| Regresiones del sistema | Ninguna |

**Estado (Paso 21):** `CANDIDATE-ADOPTION-READY`, **NO PRODUCTION MERGE**, porque falta validación externa (`outputs/dataset_v4_4class/step21_adoption/PLAN_PASO22_VALIDACION_EXTERNA.md`).

## Resultado en las pruebas de integración

Casi todos los videos usados son del entrenamiento, así que son pruebas de integración, no de generalización.

**Mejoras frente al modelo base:**
- **Normal:** 3/3 (antes 1/3).
- **Parkinson:** 7/7 (antes 0/7). Incluye los casos que la app clasificaba como riesgo o normal: `006_PD_01_MD`, `001_PD_01_SV`, `003_PD_01_MD`, `002_PD_02_MD`, `007_PD_01_MD`, `001_PD_01_ML` y `001_PD_02_MD`.
- **Riesgo de caída:** 4/4 (antes 1/4).

### Errores conocidos (no ocultar)

| Video | Clase real | Modelo base | Este modelo |
|---|---|---|---|
| `Escleorosis12` | EM | EM (0,79) | **Riesgo de caída (0,47)** |
| `Escleorosis13` | EM | EM (0,88) | **Riesgo de caída (0,49)** |
| `EXT_PD_002` (externo, **vertical**) | Parkinson (por nombre de archivo) | Riesgo (0,84) | **Riesgo (0,96)** |

**Externos** (n = 2, descriptivo): 1/2. `EXT_PD_001`, horizontal, pasa de EM a Parkinson (0,87). `EXT_PD_002` sigue en riesgo.

## Limitaciones

- **Clasificación experimental:** **no diagnóstica**; requiere valoración profesional.
- **Riesgo de caída:** **clase no validada clínicamente**; rendimiento OOF bajo (F1 0,378).
- **Esclerosis múltiple:** **clase experimental**; su resultado se asocia en parte al tipo de video (fuente). Hay confusión EM ↔ Riesgo.
- **Dependencia de fuente:**
  - En el Dataset V4, el 100 % de los videos de Parkinson y Normal proceden de un único laboratorio, en horizontal.
  - El 100 % de los verticales son EM o Riesgo.
  - Ningún Parkinson es vertical: un **video vertical no está validado** y tiende a clasificarse como EM o Riesgo.
- **Vista de cámara no verificada:** el sistema no detecta la vista; el modelo se entrenó sobre todo con video lateral de cuerpo completo.
- **Pocos sujetos:** 7 de Parkinson, 9 de Riesgo. Las etiquetas de los externos no están verificadas clínicamente.
- **Temperatura:** no se reajustó. La calibración OOF mejora con ella (ECE 0,084 → 0,058), pero la confianza media en errores sube ligeramente (0,71 → 0,74).

## Advertencias que la aplicación debe mostrar (sin eliminar)

`VIDEO_VERTICAL`, `CAMARA_MOVIL`, `CAMARA_POCO_ESTABLE`, `POSE_BAJA`, `CLASE_EM_EXPERIMENTAL`, `CLASE_RIESGO_NO_VALIDADA`, `VISTA_NO_VERIFICADA`. Además, el disclaimer de no diagnóstico.

## Rollback

```text
patch -p1 -R < outputs/dataset_v4_4class/step20_integration/step20_model_reference.patch
npx next build
```

Después hay que reiniciar el servidor.

**Paso 21:** las métricas OOF de `14_predict_deep_video_v4exp.py` y `EXPERIMENTAL_V4_OOF_METRICS` tienen su propio parche de rollback en `outputs/dataset_v4_4class/step21_adoption/`.
