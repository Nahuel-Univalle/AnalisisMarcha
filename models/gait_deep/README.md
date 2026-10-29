# `models/gait_deep/` — modelo Deep Learning de marcha (versión candidata final)

Clases: `normal` · `parkinson` · `esclerosis_multiple` · `riesgo_caida`.

## Artefactos canónicos (NO borrar)

| Archivo | Qué es |
|---|---|
| `gait_deep_model.pt` | pesos PyTorch del modelo desplegado (entrenado con los 136 vídeos) |
| `gait_deep_config.json` | arquitectura, hiperparámetros, `seed`, `temperature` (0.5), `model_version`, `weights_sha256_12`, exclusiones, nº muestras/sujetos, fecha, framework |
| `gait_deep_feature_scaler.json` | medianas/medias/desv. de las 36 features (aprendidas en train) |
| `gait_deep_label_map.json` | clase ↔ etiqueta (0..3) + `model_version` |
| `gait_deep_cv_metrics.json` | **métricas OOF finales** + `cv_stability_multiseed` (5 semillas) + calibración + folds |
| `gait_deep_training_history.json` | curvas del modelo final + resumen por fold |
| `gait_deep_evaluation_report.{json,md}` | comparación con baselines (split primario, semilla 42) |
| `plots/` | loss, accuracy, matriz de confusión, matriz normalizada, F1 por clase |
| `audit/` | auditoría: `audit_report.json`, `per_video_predictions.csv` (136 filas), `source_bias_report.json`, `methodology_checks.json`, `video_technical_metadata.csv`, PNGs |
| `experiments/experiments_report_final.json` | **comparación multi-semilla RAW** (LR / RF / DL feat / DL seq / DL full + within-source) |
| `experiments/experiments_report_norm_final.json` | lo mismo sobre `dataset_norm.npz` (control de sesgo de fuente) |

## Resultado final (usar estas cifras)

- **OOF macro-F1 0.833 ± 0.040 · accuracy 0.865 ± 0.037** (StratifiedGroupKFold k=5 por sujeto, media±desv de 5 semillas).
- Por clase (prob. media 5 semillas): normal F1 0.96 · Parkinson 0.91 · EM 0.85 · riesgo de caída 0.77.
- Aporte de la rama temporal: **+0.08 macro-F1** sobre las 36 features (consistente con y sin normalización de fuente).
- Calibración: ECE 0.28 (crudo) → 0.15 con temperature scaling (T=0.5).

## Archivos marcados como SUPERADOS (no usar sus cifras)

- `experiments/experiments_report_SUPERSEDED_nondeterministic.json` — primera corrida no determinista, reemplazada.

## Reentrenar

Ver `docs/modelo_deep_learning.md` §9. **Solo si hay un error técnico que invalide los resultados.**
