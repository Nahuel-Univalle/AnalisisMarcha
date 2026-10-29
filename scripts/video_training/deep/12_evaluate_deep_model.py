"""
Paso 12 - Evaluacion del modelo Deep Learning + comparacion con el baseline.

- Recalcula las metricas OOF del modelo profundo (accuracy, precision, recall,
  F1 por clase, macro-F1, balanced accuracy, ROC-AUC OvR, sensibilidad,
  especificidad) y la matriz de confusion.
- Entrena BASELINES sobre las MISMAS particiones StratifiedGroupKFold (misma
  semilla) usando SOLO las 36 features de marcha:
    * LogisticRegression multinomial (baseline historico del proyecto)
    * RandomForest
- Analiza que clases se confunden.
- Escribe models/gait_deep/gait_deep_evaluation_report.{json,md} y graficas.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_NAMES,
    CV_METRICS_PATH,
    EVAL_REPORT_JSON_PATH,
    EVAL_REPORT_MD_PATH,
    NUM_CLASSES,
    OOF_PATH,
    PLOTS_DIR,
    classification_metrics,
    load_dataset,
    read_json,
    write_json,
)


def baseline_oof(X_feat, y, groups, seed, folds, kind):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    skf = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    proba = np.zeros((len(y), NUM_CLASSES), dtype=np.float64)
    pred = np.full(len(y), -1, dtype=np.int64)

    for train_idx, test_idx in skf.split(X_feat, y, groups):
        if kind == "logreg":
            clf = LogisticRegression(max_iter=3000, class_weight="balanced", C=0.5)
        else:
            clf = RandomForestClassifier(
                n_estimators=400, max_depth=6, class_weight="balanced_subsample", random_state=seed
            )
        pipe = Pipeline(
            [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("clf", clf)]
        )
        pipe.fit(X_feat[train_idx], y[train_idx])
        p = pipe.predict_proba(X_feat[test_idx])
        classes = list(pipe.named_steps["clf"].classes_)
        for col, cls in enumerate(classes):
            proba[test_idx, cls] = p[:, col]
        pred[test_idx] = proba[test_idx].argmax(axis=1)

    return classification_metrics(y, pred, proba)


def confusion_analysis(cm: np.ndarray) -> list[str]:
    lines = []
    for i in range(NUM_CLASSES):
        row_total = cm[i].sum()
        if row_total == 0:
            continue
        for j in range(NUM_CLASSES):
            if i != j and cm[i, j] > 0:
                lines.append(
                    f"{cm[i, j]}/{row_total} videos de '{CLASS_NAMES[i]}' se clasificaron como "
                    f"'{CLASS_NAMES[j]}' ({cm[i, j] / row_total:.0%})"
                )
    return lines


def save_extra_plots(cm: np.ndarray, dl_perclass: dict, bl_perclass: dict):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cm_norm = cm / np.clip(cm.sum(axis=1, keepdims=True), 1, None)
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(NUM_CLASSES)); ax.set_yticks(range(NUM_CLASSES))
    ax.set_xticklabels(CLASS_NAMES, rotation=40, ha="right"); ax.set_yticklabels(CLASS_NAMES)
    ax.set_xlabel("prediccion"); ax.set_ylabel("real")
    ax.set_title("Matriz de confusion normalizada (OOF)")
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            ax.text(j, i, f"{cm_norm[i, j]:.2f}", ha="center", va="center",
                    color="white" if cm_norm[i, j] > 0.5 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); fig.tight_layout()
    fig.savefig(PLOTS_DIR / "confusion_matrix_normalized.png", dpi=130); plt.close(fig)

    x = np.arange(NUM_CLASSES)
    plt.figure(figsize=(7.5, 4.5))
    plt.bar(x - 0.2, [dl_perclass[n]["f1"] for n in CLASS_NAMES], width=0.4, label="Deep Learning")
    plt.bar(x + 0.2, [bl_perclass[n]["f1"] for n in CLASS_NAMES], width=0.4, label="Baseline LogReg")
    plt.xticks(x, CLASS_NAMES, rotation=30, ha="right"); plt.ylabel("F1"); plt.ylim(0, 1)
    plt.title("F1 por clase: Deep Learning vs baseline"); plt.legend(); plt.grid(alpha=0.3, axis="y")
    plt.tight_layout(); plt.savefig(PLOTS_DIR / "per_class_f1_comparison.png", dpi=130); plt.close()


def fmt_cm(cm: np.ndarray) -> str:
    header = "real\\pred  " + " ".join(f"{n[:10]:>11s}" for n in CLASS_NAMES)
    rows = [header]
    for i, name in enumerate(CLASS_NAMES):
        rows.append(f"{name[:10]:>10s} " + " ".join(f"{v:>11d}" for v in cm[i]))
    return "\n".join(rows)


def main() -> int:
    if not OOF_PATH.exists():
        print("Faltan predicciones OOF. Ejecute 11_train_deep_model.py primero.")
        return 1

    oof = np.load(OOF_PATH, allow_pickle=True)
    y = oof["y"].astype(np.int64)
    pred = oof["pred"].astype(np.int64)
    proba = oof["proba"].astype(np.float64)
    mask = pred >= 0

    data = load_dataset()
    X_feat = data["X_feat"].astype(np.float64)
    groups = data["subject_id"].astype(str)

    cv_meta = read_json(CV_METRICS_PATH)
    folds = int(cv_meta.get("validation_method", "k=5").split("k=")[-1].split(")")[0]) if "k=" in cv_meta.get("validation_method", "") else 5
    seed = 42

    dl = classification_metrics(y[mask], pred[mask], proba[mask])
    bl_lr = baseline_oof(X_feat, y, groups, seed, folds, "logreg")
    bl_rf = baseline_oof(X_feat, y, groups, seed, folds, "rf")

    cm = np.asarray(dl["confusion_matrix"])
    confusions = confusion_analysis(cm)
    save_extra_plots(cm, dl["per_class"], bl_lr["per_class"])

    report = {
        "deep_learning": dl,
        "baseline_logreg_36feat": bl_lr,
        "baseline_randomforest_36feat": bl_rf,
        "comparison": {
            "accuracy": {"deep": dl["accuracy"], "logreg": bl_lr["accuracy"], "rf": bl_rf["accuracy"]},
            "macro_f1": {"deep": dl["macro_f1"], "logreg": bl_lr["macro_f1"], "rf": bl_rf["macro_f1"]},
            "balanced_accuracy": {
                "deep": dl["balanced_accuracy"],
                "logreg": bl_lr["balanced_accuracy"],
                "rf": bl_rf["balanced_accuracy"],
            },
        },
        "confusion_analysis": confusions,
        "evaluation_protocol": (
            f"StratifiedGroupKFold(k={folds}) por subject_id, semilla {seed}. "
            "Todos los modelos evaluados con las MISMAS particiones. Metricas = "
            "predicciones out-of-fold agregadas."
        ),
    }
    write_json(EVAL_REPORT_JSON_PATH, report)

    md = []
    md.append("# Evaluacion del modelo Deep Learning de marcha\n")
    md.append(report["evaluation_protocol"] + "\n")
    md.append("## Resultados globales (OOF)\n")
    md.append("| modelo | accuracy | balanced acc | macro-F1 | macro ROC-AUC OvR |")
    md.append("|---|---|---|---|---|")
    md.append(f"| **Deep Learning (CNN temporal + 36 features)** | {dl['accuracy']:.3f} | {dl['balanced_accuracy']:.3f} | {dl['macro_f1']:.3f} | {dl['macro_roc_auc_ovr']} |")
    md.append(f"| Baseline LogisticRegression (36 features) | {bl_lr['accuracy']:.3f} | {bl_lr['balanced_accuracy']:.3f} | {bl_lr['macro_f1']:.3f} | {bl_lr['macro_roc_auc_ovr']} |")
    md.append(f"| Baseline RandomForest (36 features) | {bl_rf['accuracy']:.3f} | {bl_rf['balanced_accuracy']:.3f} | {bl_rf['macro_f1']:.3f} | {bl_rf['macro_roc_auc_ovr']} |")
    md.append("\n## Metricas por clase (Deep Learning)\n")
    md.append("| clase | precision | recall (sensibilidad) | especificidad | F1 | ROC-AUC OvR | soporte |")
    md.append("|---|---|---|---|---|---|---|")
    for name, m in dl["per_class"].items():
        md.append(
            f"| {name} | {m['precision']:.2f} | {m['recall']:.2f} | {m['specificity']:.2f} | "
            f"{m['f1']:.2f} | {m['roc_auc_ovr']} | {m['support']} |"
        )
    md.append("\n## Matriz de confusion (OOF)\n")
    md.append("```\n" + fmt_cm(cm) + "\n```\n")
    md.append("## Que clases se confunden\n")
    if confusions:
        for line in confusions:
            md.append(f"- {line}")
    else:
        md.append("- Sin confusiones fuera de la diagonal.")
    md.append("\n## Graficas\n")
    md.append("- `plots/loss_curves.png`, `plots/accuracy_curves.png` (modelo final)")
    md.append("- `plots/confusion_matrix.png`, `plots/confusion_matrix_normalized.png` (OOF)")
    md.append("- `plots/per_class_f1_comparison.png`")
    EVAL_REPORT_MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("=== EVALUACION ===")
    print(f"  DL      : acc={dl['accuracy']:.3f}  macroF1={dl['macro_f1']:.3f}  balAcc={dl['balanced_accuracy']:.3f}")
    print(f"  LogReg  : acc={bl_lr['accuracy']:.3f}  macroF1={bl_lr['macro_f1']:.3f}  balAcc={bl_lr['balanced_accuracy']:.3f}")
    print(f"  RForest : acc={bl_rf['accuracy']:.3f}  macroF1={bl_rf['macro_f1']:.3f}  balAcc={bl_rf['balanced_accuracy']:.3f}")
    print(f"  reporte -> {EVAL_REPORT_MD_PATH}")
    for line in confusions:
        print(f"    · {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
