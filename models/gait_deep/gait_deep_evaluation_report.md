# Evaluacion del modelo Deep Learning de marcha

StratifiedGroupKFold(k=5) por subject_id, semilla 42. Todos los modelos evaluados con las MISMAS particiones. Metricas = predicciones out-of-fold agregadas.

## Resultados globales (OOF)

| modelo | accuracy | balanced acc | macro-F1 | macro ROC-AUC OvR |
|---|---|---|---|---|
| **Deep Learning (CNN temporal + 36 features)** | 0.824 | 0.768 | 0.777 | 0.9543229917901503 |
| Baseline LogisticRegression (36 features) | 0.838 | 0.795 | 0.792 | 0.9591221794457659 |
| Baseline RandomForest (36 features) | 0.853 | 0.807 | 0.814 | 0.9626963934158532 |

## Metricas por clase (Deep Learning)

| clase | precision | recall (sensibilidad) | especificidad | F1 | ROC-AUC OvR | soporte |
|---|---|---|---|---|---|---|
| normal | 0.88 | 0.97 | 0.90 | 0.92 | 0.9863526304204271 | 59 |
| parkinson | 0.90 | 0.64 | 0.98 | 0.75 | 0.9315476190476191 | 28 |
| esclerosis_multiple | 0.76 | 0.86 | 0.93 | 0.81 | 0.9532710280373832 | 29 |
| riesgo_caida | 0.67 | 0.60 | 0.95 | 0.63 | 0.9461206896551724 | 20 |

## Matriz de confusion (OOF)

```
real\pred       normal   parkinson  esclerosis  riesgo_cai
    normal          57           2           0           0
 parkinson           8          18           0           2
esclerosis           0           0          25           4
riesgo_cai           0           0           8          12
```

## Que clases se confunden

- 2/59 videos de 'normal' se clasificaron como 'parkinson' (3%)
- 8/28 videos de 'parkinson' se clasificaron como 'normal' (29%)
- 2/28 videos de 'parkinson' se clasificaron como 'riesgo_caida' (7%)
- 4/29 videos de 'esclerosis_multiple' se clasificaron como 'riesgo_caida' (14%)
- 8/20 videos de 'riesgo_caida' se clasificaron como 'esclerosis_multiple' (40%)

## Graficas

- `plots/loss_curves.png`, `plots/accuracy_curves.png` (modelo final)
- `plots/confusion_matrix.png`, `plots/confusion_matrix_normalized.png` (OOF)
- `plots/per_class_f1_comparison.png`
