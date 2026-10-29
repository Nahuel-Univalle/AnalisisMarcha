"""
Paso 20 - AUDITORIA EXPERIMENTAL del modelo Deep Learning de marcha.

NO reentrena. Audita el modelo ya entrenado:

  1. Verifica que ningun sujeto este a la vez en train y test de un mismo fold.
  2. Tabla por-video con:
       - predicciones OUT-OF-FOLD  (metodologicamente correctas: cada video lo
         predijo un modelo que NO vio a su sujeto)
       - predicciones IN-SAMPLE con el modelo final (optimistas; solo para
         inspeccionar errores / medir la brecha de sobreajuste)
  3. Metricas por clase (precision, recall, F1, especificidad, support).
  4. Matriz de confusion absoluta y normalizada.
  5. Todos los errores, agrupados por clase real.
  6. Analisis de la confusion esclerosis_multiple <-> riesgo_caida.
  7. Distribuciones de probabilidad y de confianza por clase (+ graficas).
  8. Calibracion de probabilidades (ECE, MCE, Brier, diagrama de fiabilidad).

Salidas -> models/gait_deep/audit/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_NAMES,
    FEATURE_COLUMNS,
    FEATURE_SCALER_PATH,
    MODEL_CONFIG_PATH,
    MODEL_DIR,
    MODEL_WEIGHTS_PATH,
    NUM_CLASSES,
    OOF_PATH,
    FeatureScaler,
    build_model,
    classification_metrics,
    load_dataset,
    read_json,
    write_json,
)

AUDIT_DIR = MODEL_DIR / "audit"
SEED = 42
FOLDS = 5


def reconstruct_folds(X, y, groups):
    from sklearn.model_selection import StratifiedGroupKFold

    skf = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    folds = []
    leaks = []
    for k, (tr, te) in enumerate(skf.split(X, y, groups), start=1):
        inter = sorted(set(groups[tr]) & set(groups[te]))
        if inter:
            leaks.append({"fold": k, "shared_subjects": inter})
        folds.append({"fold": k, "train_idx": tr, "test_idx": te})
    return folds, leaks


def in_sample_predict(X_seq, X_feat_raw):
    import torch
    from torch.nn.functional import softmax

    scaler = FeatureScaler.from_json(read_json(FEATURE_SCALER_PATH))
    cfg = read_json(MODEL_CONFIG_PATH)
    model, _ = build_model(cfg)
    model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location="cpu"))
    model.eval()
    feat = scaler.transform(X_feat_raw)
    with torch.no_grad():
        logits = model(torch.from_numpy(X_seq).float(), torch.from_numpy(feat).float())
        proba = softmax(logits, dim=-1).cpu().numpy()
    return proba


def calibration_report(y_true: np.ndarray, proba: np.ndarray, n_bins: int = 10):
    """Calibracion de la confianza (probabilidad de la clase predicha)."""
    conf = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    correct = (pred == y_true).astype(float)

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = []
    ece = 0.0
    mce = 0.0
    n = len(y_true)
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (conf > lo) & (conf <= hi) if i > 0 else (conf >= lo) & (conf <= hi)
        count = int(mask.sum())
        if count == 0:
            bins.append({"bin": f"({lo:.1f},{hi:.1f}]", "count": 0, "avg_confidence": None, "accuracy": None, "gap": None})
            continue
        avg_conf = float(conf[mask].mean())
        acc = float(correct[mask].mean())
        gap = abs(avg_conf - acc)
        ece += (count / n) * gap
        mce = max(mce, gap)
        bins.append({
            "bin": f"({lo:.1f},{hi:.1f}]", "count": count,
            "avg_confidence": round(avg_conf, 4), "accuracy": round(acc, 4), "gap": round(gap, 4),
        })

    # Brier score multiclase (one-hot)
    onehot = np.eye(NUM_CLASSES)[y_true]
    brier = float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))

    # calibracion one-vs-rest por clase (ECE)
    per_class = {}
    for c, name in enumerate(CLASS_NAMES):
        p = proba[:, c]
        t = (y_true == c).astype(float)
        cece = 0.0
        for i in range(n_bins):
            lo, hi = edges[i], edges[i + 1]
            mask = (p > lo) & (p <= hi) if i > 0 else (p >= lo) & (p <= hi)
            if mask.sum() == 0:
                continue
            cece += (mask.sum() / n) * abs(float(p[mask].mean()) - float(t[mask].mean()))
        per_class[name] = round(cece, 4)

    return {
        "bins": bins,
        "ece": round(ece, 4),
        "mce": round(mce, 4),
        "brier_multiclass": round(brier, 4),
        "per_class_ece_ovr": per_class,
        "n_bins": n_bins,
        "interpretation": (
            "ECE = |confianza - acierto| promedio ponderado. <0.05 buena, 0.05-0.15 "
            "moderada, >0.15 mala. Brier: menor es mejor (0 = perfecto, ~0.75 = azar 4 clases)."
        ),
    }


def make_plots(table, y_true, oof_proba, calib):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    conf = oof_proba.max(axis=1)
    pred = oof_proba.argmax(axis=1)
    correct = pred == y_true

    # 1) confianza por clase real (boxplot) + aciertos/errores
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    data = [conf[y_true == c] for c in range(NUM_CLASSES)]
    ax[0].boxplot(data, tick_labels=[n[:10] for n in CLASS_NAMES])
    ax[0].set_title("Confianza (max prob) por clase real - OOF")
    ax[0].set_ylabel("confianza"); ax[0].grid(alpha=0.3, axis="y")
    ax[1].hist(conf[correct], bins=15, alpha=0.6, label=f"correctos (n={int(correct.sum())})")
    ax[1].hist(conf[~correct], bins=15, alpha=0.6, label=f"errores (n={int((~correct).sum())})")
    ax[1].set_title("Distribucion de confianza: correctos vs errores")
    ax[1].set_xlabel("confianza"); ax[1].legend(); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(AUDIT_DIR / "confidence_distributions.png", dpi=130); plt.close(fig)

    # 2) probabilidad de la clase VERDADERA por clase
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ptrue = oof_proba[np.arange(len(y_true)), y_true]
    ax.boxplot([ptrue[y_true == c] for c in range(NUM_CLASSES)],
              tick_labels=[n[:10] for n in CLASS_NAMES])
    ax.axhline(0.25, ls="--", c="grey", label="azar (0.25)")
    ax.set_title("Probabilidad asignada a la CLASE REAL, por clase - OOF")
    ax.set_ylabel("P(clase real)"); ax.legend(); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(AUDIT_DIR / "true_class_probability.png", dpi=130); plt.close(fig)

    # 3) diagrama de fiabilidad (calibracion)
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    xs = [b["avg_confidence"] for b in calib["bins"] if b["avg_confidence"] is not None]
    ys = [b["accuracy"] for b in calib["bins"] if b["accuracy"] is not None]
    ns = [b["count"] for b in calib["bins"] if b["avg_confidence"] is not None]
    ax.plot([0, 1], [0, 1], ls="--", c="grey", label="calibracion perfecta")
    ax.scatter(xs, ys, s=[max(20, n * 12) for n in ns], alpha=0.7, label="bins OOF")
    for x, y_, n_ in zip(xs, ys, ns):
        ax.annotate(f"n={n_}", (x, y_), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("confianza media del bin"); ax.set_ylabel("accuracy del bin")
    ax.set_title(f"Diagrama de fiabilidad (ECE={calib['ece']}, Brier={calib['brier_multiclass']})")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(AUDIT_DIR / "reliability_diagram.png", dpi=130); plt.close(fig)


def fmt_cm(cm):
    header = "real\\pred".ljust(20) + "".join(n[:12].rjust(13) for n in CLASS_NAMES)
    rows = [header]
    for i, name in enumerate(CLASS_NAMES):
        rows.append(name[:19].ljust(20) + "".join(str(int(v)).rjust(13) for v in cm[i]))
    return "\n".join(rows)


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_dataset()
    X_seq = data["X_seq"].astype(np.float32)
    X_feat_raw = data["X_feat"].astype(np.float32)
    y = data["y"].astype(np.int64)
    groups = data["subject_id"].astype(str)
    docs = data["subject_documented"].astype(bool)
    video_path = data["video_path"].astype(str)
    severity = data["severity"].astype(str)

    oof = np.load(OOF_PATH, allow_pickle=True)
    oof_proba = oof["proba"].astype(np.float64)
    oof_proba_cal = (
        oof["proba_cal"].astype(np.float64) if "proba_cal" in oof.files else None
    )
    oof_pred = oof["pred"].astype(np.int64)
    # Estimacion mas estable: probabilidad OOF promediada entre semillas de particion.
    oof_proba_meanseeds = (
        oof["proba_meanseeds"].astype(np.float64) if "proba_meanseeds" in oof.files else None
    )
    assert np.array_equal(oof["y"].astype(np.int64), y), "OOF y no coincide con dataset y (orden)"
    assert np.array_equal(oof["subject_id"].astype(str), groups), "OOF subject_id no coincide (orden)"
    assert (oof_pred >= 0).all(), "hay videos sin prediccion OOF"

    # ---- 1. verificacion de fuga de sujetos por fold ----
    folds, leaks = reconstruct_folds(X_seq, y, groups)
    fold_map = np.full(len(y), -1)
    for f in folds:
        fold_map[f["test_idx"]] = f["fold"]

    # ---- in-sample (modelo final) ----
    is_proba = in_sample_predict(X_seq, X_feat_raw)
    is_pred = is_proba.argmax(axis=1)

    # ---- 2. tabla por-video ----
    import csv as _csv

    rows = []
    for i in range(len(y)):
        row = {
            "index": i,
            "video": Path(video_path[i]).name,
            "video_path": video_path[i].replace("\\", "/"),
            "subject_id": groups[i],
            "subject_documented": bool(docs[i]),
            "severity": severity[i],
            "fold": int(fold_map[i]),
            "clase_real": CLASS_NAMES[y[i]],
            "oof_pred": CLASS_NAMES[oof_pred[i]],
            "oof_p_normal": round(float(oof_proba[i, 0]), 4),
            "oof_p_parkinson": round(float(oof_proba[i, 1]), 4),
            "oof_p_esclerosis_multiple": round(float(oof_proba[i, 2]), 4),
            "oof_p_riesgo_caida": round(float(oof_proba[i, 3]), 4),
            "oof_confianza_max": round(float(oof_proba[i].max()), 4),
            "oof_correcto": bool(oof_pred[i] == y[i]),
            "insample_pred": CLASS_NAMES[is_pred[i]],
            "insample_confianza_max": round(float(is_proba[i].max()), 4),
            "insample_correcto": bool(is_pred[i] == y[i]),
        }
        rows.append(row)

    with (AUDIT_DIR / "per_video_predictions.csv").open("w", newline="", encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- 3-4. metricas y matrices ----
    oof_metrics = classification_metrics(y, oof_pred, oof_proba)
    is_metrics = classification_metrics(y, is_pred, is_proba)
    meanseeds_metrics = (
        classification_metrics(y, oof_proba_meanseeds.argmax(1), oof_proba_meanseeds)
        if oof_proba_meanseeds is not None
        else None
    )
    cm = np.asarray(oof_metrics["confusion_matrix"], dtype=float)
    cm_norm = cm / np.clip(cm.sum(axis=1, keepdims=True), 1, None)

    # ---- 5. errores agrupados por clase real ----
    errors_by_class = {name: [] for name in CLASS_NAMES}
    for r in rows:
        if not r["oof_correcto"]:
            errors_by_class[r["clase_real"]].append({
                "video": r["video"], "subject_id": r["subject_id"],
                "predicho": r["oof_pred"], "confianza": r["oof_confianza_max"],
                "probs": {
                    "normal": r["oof_p_normal"], "parkinson": r["oof_p_parkinson"],
                    "esclerosis_multiple": r["oof_p_esclerosis_multiple"],
                    "riesgo_caida": r["oof_p_riesgo_caida"],
                },
                "fold": r["fold"],
            })

    # ---- 6. confusion MS <-> fall ----
    ms_to_fall = [e for e in errors_by_class["esclerosis_multiple"] if e["predicho"] == "riesgo_caida"]
    fall_to_ms = [e for e in errors_by_class["riesgo_caida"] if e["predicho"] == "esclerosis_multiple"]
    ms_idx = np.where(y == 2)[0]
    fall_idx = np.where(y == 3)[0]
    ms_fall_analysis = {
        "esclerosis_multiple_total": int(len(ms_idx)),
        "riesgo_caida_total": int(len(fall_idx)),
        "esclerosis_multiple_predicho_riesgo_caida": len(ms_to_fall),
        "riesgo_caida_predicho_esclerosis_multiple": len(fall_to_ms),
        "detalle_MS_a_fall": ms_to_fall,
        "detalle_fall_a_MS": fall_to_ms,
        "P(MS|real=MS) media": round(float(oof_proba[ms_idx, 2].mean()), 4),
        "P(fall|real=MS) media": round(float(oof_proba[ms_idx, 3].mean()), 4),
        "P(fall|real=fall) media": round(float(oof_proba[fall_idx, 3].mean()), 4),
        "P(MS|real=fall) media": round(float(oof_proba[fall_idx, 2].mean()), 4),
        "solape_MS_fall_probabilidad": (
            "Ambas clases comparten masa de probabilidad: el modelo las ve como "
            "patrones de inestabilidad proximos. La separacion MS/fall es la mas debil."
        ),
    }

    # ---- 7. distribuciones ----
    conf = oof_proba.max(axis=1)
    ptrue = oof_proba[np.arange(len(y)), y]
    dist = {
        "confianza_por_clase_real": {
            name: {
                "n": int((y == c).sum()),
                "media": round(float(conf[y == c].mean()), 4),
                "min": round(float(conf[y == c].min()), 4),
                "p25": round(float(np.percentile(conf[y == c], 25)), 4),
                "mediana": round(float(np.median(conf[y == c])), 4),
                "p75": round(float(np.percentile(conf[y == c], 75)), 4),
                "max": round(float(conf[y == c].max()), 4),
            }
            for c, name in enumerate(CLASS_NAMES)
        },
        "prob_clase_real_por_clase": {
            name: {
                "media": round(float(ptrue[y == c].mean()), 4),
                "mediana": round(float(np.median(ptrue[y == c])), 4),
                "min": round(float(ptrue[y == c].min()), 4),
            }
            for c, name in enumerate(CLASS_NAMES)
        },
        "confianza_correctos_vs_errores": {
            "correctos_media": round(float(conf[oof_pred == y].mean()), 4),
            "errores_media": round(float(conf[oof_pred != y].mean()) if (oof_pred != y).any() else 0.0, 4),
        },
    }

    # ---- 8. calibracion ----
    calib = calibration_report(y, oof_proba, n_bins=10)
    calib_cal = (
        calibration_report(y, oof_proba_cal, n_bins=10)
        if oof_proba_cal is not None
        else None
    )
    if calib_cal is not None:
        calib["temperature_scaled"] = {
            "ece": calib_cal["ece"], "mce": calib_cal["mce"],
            "brier_multiclass": calib_cal["brier_multiclass"],
            "per_class_ece_ovr": calib_cal["per_class_ece_ovr"],
            "bins": calib_cal["bins"],
        }
    make_plots(rows, y, oof_proba, calib)

    if meanseeds_metrics is not None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        cmm = np.asarray(meanseeds_metrics["confusion_matrix"], dtype=float)
        for norm, suffix, vmax in [(False, "meanseeds", None), (True, "meanseeds_normalized", 1.0)]:
            M = cmm / np.clip(cmm.sum(1, keepdims=True), 1, None) if norm else cmm
            fig, ax = plt.subplots(figsize=(6.2, 5.4))
            im = ax.imshow(M, cmap="Blues", vmin=0, vmax=vmax)
            ax.set_xticks(range(NUM_CLASSES)); ax.set_yticks(range(NUM_CLASSES))
            ax.set_xticklabels(CLASS_NAMES, rotation=40, ha="right"); ax.set_yticklabels(CLASS_NAMES)
            ax.set_xlabel("prediccion"); ax.set_ylabel("real")
            ax.set_title("Matriz de confusion OOF (prob. media 5 semillas)" + (" - normalizada" if norm else ""))
            for i in range(NUM_CLASSES):
                for j in range(NUM_CLASSES):
                    txt = f"{M[i, j]:.2f}" if norm else str(int(M[i, j]))
                    ax.text(j, i, txt, ha="center", va="center",
                            color="white" if M[i, j] > (0.5 if norm else M.max() / 2) else "black")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); fig.tight_layout()
            fig.savefig(AUDIT_DIR / f"confusion_matrix_{suffix}.png", dpi=130); plt.close(fig)

    report = {
        "nota_metodologica": (
            "Las metricas VALIDAS son las OOF (out-of-fold): cada video fue predicho "
            "por un modelo que no vio a su sujeto. Las in-sample usan el modelo final "
            "sobre sus propios datos de entrenamiento y solo sirven para inspeccionar "
            "errores y medir la brecha de sobreajuste."
        ),
        "leakage_check": {
            "folds_con_sujeto_en_train_y_test": leaks,
            "ok": len(leaks) == 0,
        },
        "oof_metrics_primary_seed42": oof_metrics,
        "oof_metrics_meanprob_5seeds": (
            {
                "accuracy": meanseeds_metrics["accuracy"],
                "macro_f1": meanseeds_metrics["macro_f1"],
                "balanced_accuracy": meanseeds_metrics["balanced_accuracy"],
                "macro_roc_auc_ovr": meanseeds_metrics["macro_roc_auc_ovr"],
                "per_class": meanseeds_metrics["per_class"],
                "confusion_matrix": meanseeds_metrics["confusion_matrix"],
                "note": "probabilidad OOF promediada entre 5 semillas de particion; "
                        "estimacion mas estable que un solo split (el dataset pequeno "
                        "hace que un unico split tenga alta varianza).",
            }
            if meanseeds_metrics is not None
            else None
        ),
        "in_sample_metrics": {
            "accuracy": is_metrics["accuracy"],
            "macro_f1": is_metrics["macro_f1"],
            "balanced_accuracy": is_metrics["balanced_accuracy"],
        },
        "overfitting_gap": {
            "accuracy_in_sample_menos_oof": round(is_metrics["accuracy"] - oof_metrics["accuracy"], 4),
            "macro_f1_in_sample_menos_oof": round(is_metrics["macro_f1"] - oof_metrics["macro_f1"], 4),
        },
        "confusion_matrix_absoluta": cm.astype(int).tolist(),
        "confusion_matrix_normalizada": np.round(cm_norm, 4).tolist(),
        "confusion_matrix_labels": CLASS_NAMES,
        "errores_por_clase_real": {
            name: {"n_errores": len(v), "total": int((y == CLASS_NAMES.index(name)).sum()), "detalle": v}
            for name, v in errors_by_class.items()
        },
        "confusion_MS_fall": ms_fall_analysis,
        "distribuciones": dist,
        "calibracion": calib,
    }
    write_json(AUDIT_DIR / "audit_report.json", report)

    # ---- consola ----
    print("=" * 70)
    print("  AUDITORIA - modelo Deep Learning de marcha")
    print("=" * 70)
    print(f"\n[14] Fuga de sujetos train/test por fold: {'SIN FUGA [OK]' if not leaks else 'FUGA! ' + str(leaks)}")
    print(f"\nOOF (seed 42, split primario): acc={oof_metrics['accuracy']:.3f}  macroF1={oof_metrics['macro_f1']:.3f}  balAcc={oof_metrics['balanced_accuracy']:.3f}  ROC-AUC={oof_metrics['macro_roc_auc_ovr']:.3f}")
    if meanseeds_metrics is not None:
        print(f"OOF (prob. media 5 semillas) : acc={meanseeds_metrics['accuracy']:.3f}  macroF1={meanseeds_metrics['macro_f1']:.3f}  balAcc={meanseeds_metrics['balanced_accuracy']:.3f}  ROC-AUC={meanseeds_metrics['macro_roc_auc_ovr']:.3f}")
        print("  confusion (prob. media 5 semillas):")
        print("  " + fmt_cm(np.asarray(meanseeds_metrics["confusion_matrix"], dtype=float)).replace("\n", "\n  "))
        for name, m in meanseeds_metrics["per_class"].items():
            print(f"    {name:20s} P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} spec={m['specificity']:.2f} n={m['support']}")
    print(f"IS   : acc={is_metrics['accuracy']:.3f}  macroF1={is_metrics['macro_f1']:.3f}  (brecha vs seed42 acc={is_metrics['accuracy'] - oof_metrics['accuracy']:+.3f}, macroF1={is_metrics['macro_f1'] - oof_metrics['macro_f1']:+.3f})")
    print("\nMetricas por clase (OOF):")
    print(f"  {'clase':22s} {'prec':>6s} {'recall':>7s} {'espec':>7s} {'F1':>6s} {'support':>8s}")
    for name, m in oof_metrics["per_class"].items():
        print(f"  {name:22s} {m['precision']:6.2f} {m['recall']:7.2f} {m['specificity']:7.2f} {m['f1']:6.2f} {m['support']:8d}")
    print("\nMatriz de confusion (OOF, absoluta):")
    print(fmt_cm(cm))
    print("\nErrores por clase real (OOF):")
    for name, v in errors_by_class.items():
        tot = int((y == CLASS_NAMES.index(name)).sum())
        print(f"  {name:22s}: {len(v)}/{tot} errores -> " +
              ", ".join(f"{e['video']}→{e['predicho']}({e['confianza']:.2f})" for e in v))
    print("\nConfusion esclerosis_multiple <-> riesgo_caida:")
    print(f"  MS→fall: {len(ms_to_fall)}/{len(ms_idx)}   fall→MS: {len(fall_to_ms)}/{len(fall_idx)}")
    print(f"  P(MS|MS)={ms_fall_analysis['P(MS|real=MS) media']}  P(fall|MS)={ms_fall_analysis['P(fall|real=MS) media']}")
    print(f"  P(fall|fall)={ms_fall_analysis['P(fall|real=fall) media']}  P(MS|fall)={ms_fall_analysis['P(MS|real=fall) media']}")
    print("\nCalibracion (OOF):")
    print(f"  RAW      ECE={calib['ece']}  MCE={calib['mce']}  Brier={calib['brier_multiclass']}")
    if calib_cal is not None:
        print(f"  con T    ECE={calib_cal['ece']}  MCE={calib_cal['mce']}  Brier={calib_cal['brier_multiclass']}")
    print(f"  ECE one-vs-rest por clase (raw): {calib['per_class_ece_ovr']}")
    print(f"  confianza media correctos={dist['confianza_correctos_vs_errores']['correctos_media']} vs errores={dist['confianza_correctos_vs_errores']['errores_media']}")
    print(f"\nSalidas -> {AUDIT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
