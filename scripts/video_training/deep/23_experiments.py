"""
Paso 23 - EXPERIMENTOS: ablaciones + modelos por fuente.

No toca el modelo desplegado (models/gait_deep/gait_deep_model.pt).

A) Ablaciones (mismas particiones StratifiedGroupKFold k=5, semilla 42, mismo
   augmentation e hiperparametros que produccion):
      - feat_only : solo la rama de 36 features
      - seq_only  : solo la rama temporal (CNN)
      - full      : ambas (arquitectura desplegada)
   -> cuanto aporta la informacion temporal.

B) Modelos DENTRO de una misma fuente de grabacion (control de sesgo de fuente):
      - source_A : normal vs parkinson   (mismos .MOV, misma coleccion)
      - source_B : esclerosis_multiple vs riesgo_caida  (mismos .mp4)
   Si ambos separan bien con validacion por sujeto, el modelo aprende marcha
   DENTRO de una fuente consistente y no solo el artefacto de fuente.

Salida -> models/gait_deep/experiments/experiments_report.json
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_NAMES,
    MODEL_DIR,
    FeatureScaler,
    augment_sample,
    build_model,
    default_model_config,
    load_dataset,
    seed_everything,
    write_json,
)


def _determinism() -> None:
    import os

    os.environ.setdefault("PYTHONHASHSEED", "0")
    import torch

    torch.set_num_threads(1)
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:
        pass


_determinism()

EXP_DIR = MODEL_DIR / "experiments"
SEED = 42
FOLDS = 5
EPOCHS = 240
PATIENCE = 35
BATCH = 16
LR = 1e-3
WD = 2e-4
LS = 0.05


def metrics(y_true, y_pred, y_proba, n_classes, class_names):
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
        roc_auc_score,
    )

    labels = list(range(n_classes))
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    per_class = {}
    for i, name in enumerate(class_names):
        tp = int(cm[i, i]); fn = int(cm[i].sum() - tp)
        fp = int(cm[:, i].sum() - tp); tn = int(cm.sum() - tp - fn - fp)
        per_class[name] = {
            "precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
            "f1": round(float(f[i]), 4), "specificity": round(tn / (tn + fp), 4) if (tn + fp) else 0.0,
            "support": int(s[i]),
        }
    out = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
        "per_class": per_class,
        "confusion_matrix": cm.astype(int).tolist(),
    }
    try:
        if n_classes == 2:
            out["roc_auc"] = round(float(roc_auc_score(y_true, y_proba[:, 1])), 4)
        else:
            out["macro_roc_auc_ovr"] = round(
                float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro", labels=labels)), 4
            )
    except ValueError:
        pass
    return out


def batch(idx, X_seq, X_feat, y, augment, rng):
    import torch

    seqs, feats = [], []
    for i in idx:
        s, f = X_seq[i], X_feat[i]
        if augment:
            s, f = augment_sample(s, f, rng)
        seqs.append(s); feats.append(f)
    return (torch.from_numpy(np.stack(seqs)).float(),
            torch.from_numpy(np.stack(feats)).float(),
            torch.from_numpy(y[idx]).long())


def evaluate(model, X_seq, X_feat, y, idx, n_classes):
    import torch
    from torch.nn.functional import softmax

    model.eval()
    rng = np.random.default_rng(0)
    probs = np.zeros((len(idx), n_classes), dtype=np.float32)
    with torch.no_grad():
        for s in range(0, len(idx), BATCH):
            b = idx[s:s + BATCH]
            st, ft, _ = batch(b, X_seq, X_feat, y, False, rng)
            probs[s:s + len(b)] = softmax(model(st, ft), dim=-1).cpu().numpy()
    return probs, probs.argmax(1)


def inner_split(y, groups, seed, n_classes, val_frac=0.18):
    from sklearn.model_selection import GroupShuffleSplit

    for a in range(30):
        gss = GroupShuffleSplit(n_splits=1, test_size=val_frac, random_state=seed + a)
        tr, va = next(gss.split(np.zeros(len(y)), y, groups))
        if len(np.unique(y[tr])) == n_classes and len(np.unique(y[va])) >= max(2, n_classes - 1):
            return tr, va
    return tr, va


def train_fold(X_seq, X_feat_raw, y, tr_idx, va_idx, cfg, seed):
    import torch
    from torch import nn
    from sklearn.metrics import f1_score

    seed_everything(seed)
    scaler = FeatureScaler.fit(X_feat_raw[tr_idx])
    X_feat = scaler.transform(X_feat_raw)
    model, cfg = build_model(cfg)
    n_classes = cfg["num_classes"]

    counts = np.bincount(y[tr_idx], minlength=n_classes).astype(float)
    w = counts.sum() / (n_classes * np.clip(counts, 1, None))
    crit = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32), label_smoothing=LS)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WD)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=0.5, patience=8)
    rng = np.random.default_rng(seed)
    best = {"f1": -1.0, "vloss": 1e9, "state": None}
    patience = PATIENCE
    for ep in range(EPOCHS):
        model.train()
        order = np.arange(len(tr_idx)); rng.shuffle(order)
        chunks = [order[s:s + BATCH] for s in range(0, len(order), BATCH)]
        if len(chunks) >= 2 and len(chunks[-1]) == 1:  # BatchNorm no admite lote de 1
            chunks[-2] = np.concatenate([chunks[-2], chunks[-1]]); chunks.pop()
        for ch in chunks:
            b = tr_idx[ch]
            st, ft, yt = batch(b, X_seq, X_feat, y, True, rng)
            opt.zero_grad()
            loss = crit(model(st, ft), yt)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
        vprob, vp = evaluate(model, X_seq, X_feat, y, va_idx, n_classes)
        vf1 = f1_score(y[va_idx], vp, labels=list(range(n_classes)), average="macro", zero_division=0)
        vloss = float(-np.mean(np.log(np.clip(vprob[np.arange(len(va_idx)), y[va_idx]], 1e-9, 1.0))))
        sched.step(vf1)
        improved = vf1 > best["f1"] + 1e-4 or (abs(vf1 - best["f1"]) <= 1e-4 and vloss < best["vloss"] - 1e-4)
        if improved:
            best = {"f1": vf1, "vloss": vloss,
                    "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
            patience = PATIENCE
        else:
            patience -= 1
            if patience <= 0:
                break
    if best["state"]:
        model.load_state_dict(best["state"])
    return model, scaler


def _cv_once(X_seq, X_feat_raw, y, groups, cfg, class_names, split_seed):
    from sklearn.model_selection import StratifiedGroupKFold

    n_classes = cfg["num_classes"]
    skf = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=split_seed)
    oof_p = np.zeros((len(y), n_classes)); oof_pred = np.full(len(y), -1)
    for k, (tr, te) in enumerate(skf.split(X_seq, y, groups), 1):
        assert not (set(groups[tr]) & set(groups[te])), f"fuga fold {k}"
        itr_rel, iva_rel = inner_split(y[tr], groups[tr], split_seed + k, n_classes)
        model, scaler = train_fold(X_seq, X_feat_raw, y, tr[itr_rel], tr[iva_rel], dict(cfg), split_seed + k)
        Xf = scaler.transform(X_feat_raw)
        p, pr = evaluate(model, X_seq, Xf, y, te, n_classes)
        oof_p[te] = p; oof_pred[te] = pr
    return metrics(y, oof_pred, oof_p, n_classes, class_names)


def run_cv(X_seq, X_feat_raw, y, groups, cfg, class_names, label, repeats=1):
    t0 = time.time()
    runs = [_cv_once(X_seq, X_feat_raw, y, groups, cfg, class_names, SEED + s) for s in range(repeats)]
    base = runs[0]
    if repeats > 1:
        for key in ("accuracy", "macro_f1", "balanced_accuracy"):
            vals = [r[key] for r in runs]
            base[f"{key}_mean"] = round(float(np.mean(vals)), 4)
            base[f"{key}_std"] = round(float(np.std(vals)), 4)
        base["per_seed"] = [{"seed": SEED + s, "accuracy": round(r["accuracy"], 4),
                             "macro_f1": round(r["macro_f1"], 4),
                             "balanced_accuracy": round(r["balanced_accuracy"], 4)} for s, r in enumerate(runs)]
    base["seconds"] = round(time.time() - t0, 1)
    mf1 = base.get("macro_f1_mean", base["macro_f1"])
    sd = base.get("macro_f1_std")
    print(f"  [{label}] macroF1={mf1:.3f}" + (f"±{sd:.3f}" if sd is not None else "")
          + f"  acc={base.get('accuracy_mean', base['accuracy']):.3f}  balAcc={base.get('balanced_accuracy_mean', base['balanced_accuracy']):.3f}")
    return base


def _baseline_once(X_feat, y, groups, kind, class_names, split_seed):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    n_classes = len(class_names)
    skf = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=split_seed)
    proba = np.zeros((len(y), n_classes)); pred = np.full(len(y), -1)
    for tr, te in skf.split(X_feat, y, groups):
        assert not (set(groups[tr]) & set(groups[te])), f"[{kind}] fuga"
        clf = (LogisticRegression(max_iter=3000, class_weight="balanced", C=0.5)
               if kind == "logreg" else
               RandomForestClassifier(n_estimators=400, max_depth=6,
                                      class_weight="balanced_subsample", random_state=split_seed))
        pipe = Pipeline([("imp", SimpleImputer(strategy="median")),
                         ("sc", StandardScaler()), ("clf", clf)])
        pipe.fit(X_feat[tr], y[tr])
        p = pipe.predict_proba(X_feat[te])
        for col, cls in enumerate(pipe.named_steps["clf"].classes_):
            proba[te, cls] = p[:, col]
        pred[te] = proba[te].argmax(1)
    return metrics(y, pred, proba, n_classes, class_names)


def run_baseline(X_feat, y, groups, kind, class_names, repeats=1):
    """Baseline sklearn sobre SOLO las 36 features, mismas particiones (multi-semilla)."""
    runs = [_baseline_once(X_feat, y, groups, kind, class_names, SEED + s) for s in range(repeats)]
    base = runs[0]
    if repeats > 1:
        for key in ("accuracy", "macro_f1", "balanced_accuracy"):
            vals = [r[key] for r in runs]
            base[f"{key}_mean"] = round(float(np.mean(vals)), 4)
            base[f"{key}_std"] = round(float(np.std(vals)), 4)
        base["per_seed"] = [{"seed": SEED + s, "macro_f1": round(r["macro_f1"], 4),
                             "accuracy": round(r["accuracy"], 4)} for s, r in enumerate(runs)]
    mf1 = base.get("macro_f1_mean", base["macro_f1"]); sd = base.get("macro_f1_std")
    print(f"  [{kind}] macroF1={mf1:.3f}" + (f"±{sd:.3f}" if sd is not None else "")
          + f"  acc={base.get('accuracy_mean', base['accuracy']):.3f}")
    return base


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="", help="ruta a un .npz alternativo (p.ej. dataset_norm.npz)")
    ap.add_argument("--out", default="", help="nombre del json de salida")
    ap.add_argument("--repeats", type=int, default=3, help="semillas de particion para media±desv")
    a = ap.parse_args()
    reps = max(1, a.repeats)

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    data = load_dataset(a.dataset or None)
    tag = Path(a.dataset).stem if a.dataset else "dataset"
    out_path = EXP_DIR / (a.out or f"experiments_report_{tag}.json")
    X_seq = data["X_seq"].astype(np.float32)
    X_feat = data["X_feat"].astype(np.float32)
    y = data["y"].astype(np.int64)
    groups = data["subject_id"].astype(str)

    def mf1(m):
        return m.get("macro_f1_mean", m["macro_f1"])

    report = {"dataset": tag,
              "n_samples": int(len(y)), "n_subjects": int(len(np.unique(groups))),
              "repeats": reps,
              "protocol": f"StratifiedGroupKFold(k={FOLDS}) por subject_id, semillas {SEED}..{SEED + reps - 1}. "
                          "Todos los modelos con LAS MISMAS particiones. macro_f1_mean = media OOF entre semillas."}

    print(f"=== BASELINES (solo 36 features, {reps} semillas) ===")
    report["baselines"] = {
        "logistic_regression_36feat": run_baseline(X_feat, y, groups, "logreg", CLASS_NAMES, reps),
        "random_forest_36feat": run_baseline(X_feat, y, groups, "rf", CLASS_NAMES, reps),
    }

    print(f"\n=== A) ABLACIONES DEEP LEARNING (4 clases, {reps} semillas) ===")
    abl = {}
    for label, over in [
        ("feat_only", {"use_seq_branch": False, "use_feat_branch": True}),
        ("seq_only", {"use_seq_branch": True, "use_feat_branch": False}),
        ("full", {"use_seq_branch": True, "use_feat_branch": True}),
    ]:
        cfg = default_model_config(); cfg.update(over); cfg["num_classes"] = 4
        abl[label] = run_cv(X_seq, X_feat, y, groups, cfg, CLASS_NAMES, label, reps)
    report["ablations"] = abl
    report["aporte_temporal"] = {
        "macro_f1": {"logreg": mf1(report["baselines"]["logistic_regression_36feat"]),
                     "rf": mf1(report["baselines"]["random_forest_36feat"]),
                     "feat_only": mf1(abl["feat_only"]), "seq_only": mf1(abl["seq_only"]),
                     "full": mf1(abl["full"])},
        "delta_macro_f1_full_vs_feat_only": round(mf1(abl["full"]) - mf1(abl["feat_only"]), 4),
        "delta_macro_f1_full_vs_seq_only": round(mf1(abl["full"]) - mf1(abl["seq_only"]), 4),
        "delta_macro_f1_full_vs_best_baseline": round(
            mf1(abl["full"]) - max(mf1(report["baselines"]["logistic_regression_36feat"]),
                                   mf1(report["baselines"]["random_forest_36feat"])), 4),
    }

    print("\n=== B) MODELOS DENTRO DE FUENTE (control de sesgo) ===")
    within = {}
    for label, keep in [
        ("source_A_normal_vs_parkinson", [0, 1]),
        ("source_B_esclerosis_vs_riesgo", [2, 3]),
    ]:
        mask = np.isin(y, keep)
        remap = {c: i for i, c in enumerate(keep)}
        ys = np.array([remap[v] for v in y[mask]], dtype=np.int64)
        names = [CLASS_NAMES[c] for c in keep]
        cfg = default_model_config(); cfg["num_classes"] = 2
        n_sub = len(np.unique(groups[mask]))
        print(f"  {label}: {int(mask.sum())} videos, {n_sub} sujetos, clases {names}")
        within[label] = run_cv(X_seq[mask], X_feat[mask], ys, groups[mask], cfg, names, label, reps)
        within[label]["n_videos"] = int(mask.sum())
        within[label]["n_subjects"] = n_sub
    report["within_source"] = within

    write_json(out_path, report)
    print(f"\n-> {out_path}")
    print("\nRESUMEN (macro-F1 media entre semillas):")
    for k in ("logistic_regression_36feat", "random_forest_36feat"):
        print(f"  baseline {k:26s} {mf1(report['baselines'][k]):.3f}")
    for k in ("feat_only", "seq_only", "full"):
        print(f"  DL {k:31s} {mf1(abl[k]):.3f}")
    print(f"  aporte temporal (full - feat_only): {report['aporte_temporal']['delta_macro_f1_full_vs_feat_only']:+.3f} macroF1")
    print(f"  full - mejor baseline             : {report['aporte_temporal']['delta_macro_f1_full_vs_best_baseline']:+.3f} macroF1")
    for k, v in within.items():
        print(f"  {k}: F1={mf1(v):.3f} AUC={v.get('roc_auc')}  ({v['n_videos']}v/{v['n_subjects']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
