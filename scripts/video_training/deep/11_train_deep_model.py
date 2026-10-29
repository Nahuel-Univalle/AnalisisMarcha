"""
Paso 11 - Entrenamiento del modelo de Deep Learning multiclase.

- Validacion cruzada StratifiedGroupKFold (k=5) por subject_id  -> metricas OOF
  (cada sujeto aparece en test exactamente una vez; nunca en su propio train).
- Dentro de cada fold: split interno por grupos para EARLY STOPPING.
- Augmentation SOLO en train (nunca val/test, nunca crea sujetos).
- Perdida CrossEntropy ponderada por clase (maneja el desbalance 59/28/30/20).
- Modelo final entrenado con TODOS los datos (val interno para early stopping) y
  guardado en models/gait_deep/.
- Graficas: loss, accuracy y matriz de confusion.

Uso:
  .venv311\\Scripts\\python.exe scripts\\video_training\\deep\\11_train_deep_model.py
Opciones utiles:
  --epochs 200 --patience 30 --folds 5 --seed 42
  --seq-only    (ablacion: solo rama temporal)
  --feat-only   (ablacion: solo rama de 36 features)
  --no-augment
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_NAMES,
    CV_METRICS_PATH,
    FEATURE_SCALER_PATH,
    LABEL_MAP_PATH,
    MODEL_CONFIG_PATH,
    MODEL_DIR,
    MODEL_WEIGHTS_PATH,
    NUM_CLASSES,
    OOF_PATH,
    PLOTS_DIR,
    TRAINING_HISTORY_PATH,
    FeatureScaler,
    augment_sample,
    build_model,
    classification_metrics,
    default_model_config,
    load_dataset,
    seed_everything,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entrena el modelo Deep Learning de marcha (multiclase).")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=2e-4)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repeats", type=int, default=1,
                        help="repite la CV con semillas seed, seed+1, ... para estimar media±desv de las metricas OOF (el modelo final y los artefactos usan la semilla base)")
    parser.add_argument("--label-smoothing", type=float, default=0.05)
    parser.add_argument("--seq-only", action="store_true")
    parser.add_argument("--feat-only", action="store_true")
    parser.add_argument("--no-augment", action="store_true")
    parser.add_argument(
        "--dataset", default=None,
        help="Ruta a un dataset.npz alternativo (p. ej. un dataset temporal de 2 clases "
             "generado por 10_build_sequence_dataset.py --active-classes-config ...). Por "
             "defecto usa data/video_training/deep/dataset.npz (el del modelo desplegado), "
             "igual que siempre.",
    )
    return parser.parse_args()


def make_config(args: argparse.Namespace) -> dict:
    cfg = default_model_config(num_classes=NUM_CLASSES)
    if args.seq_only:
        cfg["use_feat_branch"] = False
    if args.feat_only:
        cfg["use_seq_branch"] = False
    return cfg


def grouped_inner_split(y: np.ndarray, groups: np.ndarray, seed: int, val_frac: float = 0.18):
    """Split interno train/val por grupos, intentando cubrir todas las clases en val."""
    from sklearn.model_selection import GroupShuffleSplit

    unique_groups = np.unique(groups)
    for attempt in range(25):
        splitter = GroupShuffleSplit(n_splits=1, test_size=val_frac, random_state=seed + attempt)
        train_rel, val_rel = next(splitter.split(np.zeros(len(y)), y, groups))
        if len(np.unique(y[train_rel])) == NUM_CLASSES and len(np.unique(y[val_rel])) >= max(2, NUM_CLASSES - 1):
            return train_rel, val_rel
    return train_rel, val_rel  # ultimo intento


def iterate_batches(n: int, batch_size: int, rng: np.random.Generator, shuffle: bool):
    order = np.arange(n)
    if shuffle:
        rng.shuffle(order)
    batches = [order[start:start + batch_size] for start in range(0, n, batch_size)]
    # BatchNorm en modo train falla con lotes de tamano 1. Si el ultimo lote
    # queda con 1 muestra (train), se fusiona con el anterior.
    if shuffle and len(batches) >= 2 and len(batches[-1]) == 1:
        batches[-2] = np.concatenate([batches[-2], batches[-1]])
        batches.pop()
    for b in batches:
        yield b


def build_batch(idx, X_seq, X_feat_scaled, y, augment: bool, rng):
    seqs, feats = [], []
    for i in idx:
        s, f = X_seq[i], X_feat_scaled[i]
        if augment:
            s, f = augment_sample(s, f, rng)
        seqs.append(s)
        feats.append(f)
    import torch

    return (
        torch.from_numpy(np.stack(seqs)).float(),
        torch.from_numpy(np.stack(feats)).float(),
        torch.from_numpy(y[idx]).long(),
    )


def predict_logits(model, X_seq, X_feat_scaled, y, idx, batch_size):
    import torch

    model.eval()
    out = np.zeros((len(idx), NUM_CLASSES), dtype=np.float64)
    rng = np.random.default_rng(0)
    with torch.no_grad():
        pos = 0
        for batch in iterate_batches(len(idx), batch_size, rng, shuffle=False):
            real = idx[batch]
            seq_t, feat_t, _ = build_batch(real, X_seq, X_feat_scaled, y, augment=False, rng=rng)
            out[pos:pos + len(batch)] = model(seq_t, feat_t).cpu().numpy()
            pos += len(batch)
    return out


def softmax_np(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def evaluate(model, X_seq, X_feat_scaled, y, idx, batch_size):
    logits = predict_logits(model, X_seq, X_feat_scaled, y, idx, batch_size)
    probs = softmax_np(logits).astype(np.float32)
    return probs, probs.argmax(axis=1)


def nll(logits: np.ndarray, y_true: np.ndarray) -> float:
    p = softmax_np(logits)
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y_true)), y_true], 1e-12, 1.0))))


TEMP_MIN, TEMP_MAX = 0.5, 3.0


def fit_temperature(logits: np.ndarray, y_true: np.ndarray) -> float:
    """Temperature scaling (Guo et al. 2017): 1 parametro, minimiza NLL.

    Ajustado SOLO sobre el conjunto interno de validacion (nunca sobre el test
    OOF). No cambia el argmax -> accuracy/F1 se mantienen; solo calibra.

    T se restringe a [0.5, 3.0]: sin la cota inferior el optimo de NLL cae a ~0.16
    y satura la softmax (toda prediccion pasa a ~100% de confianza), lo que seria
    enganoso para un informe orientativo. T=0.5 ya corrige fuerte la
    infra-confianza del modelo; la infra-confianza residual se documenta.
    """
    if len(y_true) < 4 or len(np.unique(y_true)) < 2:
        return 1.0
    grid = np.concatenate([np.linspace(TEMP_MIN, 1.0, 21), np.linspace(1.0, TEMP_MAX, 21)])
    best = float(grid[int(np.argmin([nll(logits / t, y_true) for t in grid]))])
    lo, hi = max(TEMP_MIN, best * 0.8), min(TEMP_MAX, best * 1.25)
    fine = np.linspace(lo, hi, 41)
    best = float(fine[int(np.argmin([nll(logits / t, y_true) for t in fine]))])
    return round(min(max(best, TEMP_MIN), TEMP_MAX), 4)


def expected_calibration_error(proba: np.ndarray, y_true: np.ndarray, n_bins: int = 10):
    conf = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    correct = (pred == y_true).astype(float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    n = len(y_true)
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        m = (conf > lo) & (conf <= hi) if i > 0 else (conf >= lo) & (conf <= hi)
        if not m.any():
            continue
        gap = abs(float(conf[m].mean()) - float(correct[m].mean()))
        ece += (m.sum() / n) * gap
        mce = max(mce, gap)
    onehot = np.eye(NUM_CLASSES)[y_true]
    brier = float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))
    return {"ece": round(ece, 4), "mce": round(mce, 4), "brier": round(brier, 4)}


def train_one(
    X_seq, X_feat_raw, y, train_idx, val_idx, cfg, args, seed, verbose_tag=""
):
    import torch
    from torch import nn

    seed_everything(seed)
    scaler = FeatureScaler.fit(X_feat_raw[train_idx])
    X_feat_scaled = scaler.transform(X_feat_raw)

    model, cfg = build_model(cfg)
    device = torch.device("cpu")
    model.to(device)

    counts = np.bincount(y[train_idx], minlength=NUM_CLASSES).astype(np.float64)
    weights = counts.sum() / (NUM_CLASSES * np.clip(counts, 1.0, None))
    class_weights = torch.tensor(weights, dtype=torch.float32)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=args.label_smoothing)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=8)

    rng = np.random.default_rng(seed)
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": [], "val_macro_f1": [], "lr": []}
    best = {"macro_f1": -1.0, "val_loss": 1e9, "state": None, "epoch": -1}
    patience_left = args.patience
    augment = not args.no_augment

    for epoch in range(1, args.epochs + 1):
        model.train()
        ep_loss, ep_correct, ep_total = 0.0, 0, 0
        for batch in iterate_batches(len(train_idx), args.batch_size, rng, shuffle=True):
            real = train_idx[batch]
            seq_t, feat_t, y_t = build_batch(real, X_seq, X_feat_scaled, y, augment, rng)
            optimizer.zero_grad()
            logits = model(seq_t, feat_t)
            loss = criterion(logits, y_t)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            ep_loss += loss.item() * len(batch)
            ep_correct += int((logits.argmax(-1) == y_t).sum().item())
            ep_total += len(batch)

        train_loss = ep_loss / max(ep_total, 1)
        train_acc = ep_correct / max(ep_total, 1)

        val_probs, val_preds = evaluate(model, X_seq, X_feat_scaled, y, val_idx, args.batch_size)
        with torch.no_grad():
            vp = torch.from_numpy(np.clip(val_probs, 1e-7, 1.0)).float()
            val_loss = float(nn.functional.nll_loss(torch.log(vp), torch.from_numpy(y[val_idx]).long()))
        from sklearn.metrics import f1_score

        val_acc = float((val_preds == y[val_idx]).mean())
        val_macro_f1 = float(
            f1_score(y[val_idx], val_preds, labels=list(range(NUM_CLASSES)), average="macro", zero_division=0)
        )
        scheduler.step(val_macro_f1)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)
        history["val_macro_f1"].append(val_macro_f1)
        history["lr"].append(optimizer.param_groups[0]["lr"])

        improved = val_macro_f1 > best["macro_f1"] + 1e-4 or (
            abs(val_macro_f1 - best["macro_f1"]) <= 1e-4 and val_loss < best["val_loss"] - 1e-4
        )
        if improved:
            best.update(
                macro_f1=val_macro_f1,
                val_loss=val_loss,
                epoch=epoch,
                state={k: v.detach().clone() for k, v in model.state_dict().items()},
            )
            patience_left = args.patience
        else:
            patience_left -= 1
            if patience_left <= 0:
                break

    if best["state"] is not None:
        model.load_state_dict(best["state"])

    # Temperature scaling ajustado SOLO en el conjunto interno de validacion.
    val_logits = predict_logits(model, X_seq, X_feat_scaled, y, val_idx, args.batch_size)
    temperature = fit_temperature(val_logits, y[val_idx])
    best["temperature"] = temperature
    best["val_logits"] = val_logits
    best["val_labels"] = y[val_idx].copy()

    if verbose_tag:
        print(
            f"    [{verbose_tag}] mejor epoca {best['epoch']:3d} | "
            f"val_macroF1={best['macro_f1']:.3f} val_loss={best['val_loss']:.3f} "
            f"| T={temperature} (epocas corridas: {len(history['train_loss'])})"
        )
    return model, scaler, history, best


def cross_validate(X_seq, X_feat_raw, y, groups, cfg, args, seed=None, quiet=False):
    from sklearn.model_selection import StratifiedGroupKFold

    seed = args.seed if seed is None else seed
    skf = StratifiedGroupKFold(n_splits=args.folds, shuffle=True, random_state=seed)
    oof_proba = np.zeros((len(y), NUM_CLASSES), dtype=np.float32)
    oof_proba_cal = np.zeros((len(y), NUM_CLASSES), dtype=np.float32)
    oof_pred = np.full(len(y), -1, dtype=np.int64)
    fold_rows = []
    pool_logits, pool_labels = [], []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X_seq, y, groups), start=1):
        assert not (set(groups[train_idx]) & set(groups[test_idx])), f"fuga de sujeto en fold {fold}"
        tr_rel, val_rel = grouped_inner_split(y[train_idx], groups[train_idx], seed + fold)
        inner_train = train_idx[tr_rel]
        inner_val = train_idx[val_rel]
        if not quiet:
            print(
                f"  Fold {fold}/{args.folds}: train={len(inner_train)} val={len(inner_val)} test={len(test_idx)} "
                f"| test clases={np.bincount(y[test_idx], minlength=NUM_CLASSES).tolist()}"
            )
        model, scaler, _history, best = train_one(
            X_seq, X_feat_raw, y, inner_train, inner_val, dict(cfg), args, seed + fold,
            verbose_tag="" if quiet else f"fold{fold}"
        )
        X_feat_scaled = scaler.transform(X_feat_raw)
        logits = predict_logits(model, X_seq, X_feat_scaled, y, test_idx, args.batch_size)
        probs = softmax_np(logits).astype(np.float32)
        temperature = best.get("temperature", 1.0)
        probs_cal = softmax_np(logits / temperature).astype(np.float32)
        preds = probs.argmax(axis=1)
        oof_proba[test_idx] = probs
        oof_proba_cal[test_idx] = probs_cal
        oof_pred[test_idx] = preds
        pool_logits.append(best["val_logits"])
        pool_labels.append(best["val_labels"])
        fold_metric = classification_metrics(y[test_idx], preds, probs, class_names=CLASS_NAMES)
        fold_rows.append(
            {
                "fold": fold,
                "test_subjects": sorted(set(groups[test_idx].tolist())),
                "accuracy": fold_metric["accuracy"],
                "macro_f1": fold_metric["macro_f1"],
                "balanced_accuracy": fold_metric["balanced_accuracy"],
                "temperature": temperature,
            }
        )

    pooled_val_logits = np.concatenate(pool_logits, axis=0)
    pooled_val_labels = np.concatenate(pool_labels, axis=0)
    pooled_temperature = fit_temperature(pooled_val_logits, pooled_val_labels)
    return oof_proba, oof_proba_cal, oof_pred, fold_rows, pooled_temperature


def save_plots(history: dict, oof_true, oof_pred):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    epochs = range(1, len(history["train_loss"]) + 1)

    plt.figure(figsize=(7, 4.5))
    plt.plot(epochs, history["train_loss"], label="train")
    plt.plot(epochs, history["val_loss"], label="validacion")
    plt.xlabel("epoca"); plt.ylabel("perdida"); plt.title("Curvas de perdida (modelo final)")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(PLOTS_DIR / "loss_curves.png", dpi=130); plt.close()

    plt.figure(figsize=(7, 4.5))
    plt.plot(epochs, history["train_acc"], label="train acc")
    plt.plot(epochs, history["val_acc"], label="val acc")
    plt.plot(epochs, history["val_macro_f1"], label="val macro-F1", linestyle="--")
    plt.xlabel("epoca"); plt.ylabel("valor"); plt.title("Accuracy / macro-F1 (modelo final)")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(PLOTS_DIR / "accuracy_curves.png", dpi=130); plt.close()

    cm = confusion_matrix(oof_true, oof_pred, labels=list(range(NUM_CLASSES)))
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(NUM_CLASSES)); ax.set_yticks(range(NUM_CLASSES))
    ax.set_xticklabels(CLASS_NAMES, rotation=40, ha="right"); ax.set_yticklabels(CLASS_NAMES)
    ax.set_xlabel("prediccion"); ax.set_ylabel("real")
    ax.set_title("Matriz de confusion (validacion cruzada OOF)")
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "confusion_matrix.png", dpi=130); plt.close(fig)


def enable_determinism() -> None:
    """Hace el entrenamiento reproducible entre corridas (dataset pequeno +
    conv1d en CPU multihilo eran no deterministas: la macro-F1 variaba ~0.03-0.05
    entre ejecuciones con la misma semilla)."""
    import os

    os.environ.setdefault("PYTHONHASHSEED", "0")
    import torch

    torch.set_num_threads(1)
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:
        pass


def main() -> int:
    global CLASS_NAMES, NUM_CLASSES

    args = parse_args()
    enable_determinism()
    seed_everything(args.seed)
    data = load_dataset(args.dataset)
    X_seq = data["X_seq"].astype(np.float32)
    X_feat_raw = data["X_feat"].astype(np.float32)
    y = data["y"].astype(np.int64)
    groups = data["subject_id"].astype(str)

    # El numero/nombre de clases se toma del propio dataset.npz (campo
    # 'class_names', escrito por 10_build_sequence_dataset.py), no de un
    # valor fijo. Para el dataset.npz de produccion (4 clases) esto no
    # cambia nada: class_names ahi ya es la misma lista de siempre. Para un
    # dataset temporal (p. ej. --dataset con solo normal+parkinson) esto
    # ajusta automaticamente el resto del script (tamano de la ultima capa,
    # matrices de confusion, graficas, label_map guardado) sin tocar mas
    # codigo.
    if "class_names" in data.files:
        loaded_names = [str(c) for c in data["class_names"]]
        if loaded_names != CLASS_NAMES:
            print(f"  aviso: dataset con clases distintas al taxonomy completo -> {loaded_names}")
        CLASS_NAMES = loaded_names
        NUM_CLASSES = len(CLASS_NAMES)

    cfg = make_config(args)

    print("=" * 66)
    print(f"  ENTRENAMIENTO DEEP LEARNING - marcha ({NUM_CLASSES} clases)")
    print("=" * 66)
    print(f"  muestras={len(y)}  secuencia={X_seq.shape[1:]}  features={X_feat_raw.shape[1]}")
    print(f"  clases  ={np.bincount(y, minlength=NUM_CLASSES).tolist()} ({CLASS_NAMES})")
    print(f"  sujetos ={len(np.unique(groups))}  | ramas: seq={cfg['use_seq_branch']} feat={cfg['use_feat_branch']}")

    t0 = time.time()
    oof_proba, oof_proba_cal, oof_pred, fold_rows, pooled_temperature = cross_validate(
        X_seq, X_feat_raw, y, groups, cfg, args
    )
    mask = oof_pred >= 0
    oof_metrics = classification_metrics(y[mask], oof_pred[mask], oof_proba[mask], class_names=CLASS_NAMES)

    # ---- estabilidad: repite la CV con varias semillas (dataset pequeno ->
    #      la particion domina la metrica) ----
    repeat_stats = None
    oof_proba_meanseeds = oof_proba.copy()
    if args.repeats and args.repeats > 1:
        print(f"\n  Estimando estabilidad con {args.repeats} semillas de particion...")
        accs, mf1s, bacc = [oof_metrics["accuracy"]], [oof_metrics["macro_f1"]], [oof_metrics["balanced_accuracy"]]
        per_seed = [{"seed": args.seed, "accuracy": round(oof_metrics["accuracy"], 4),
                     "macro_f1": round(oof_metrics["macro_f1"], 4),
                     "balanced_accuracy": round(oof_metrics["balanced_accuracy"], 4),
                     "per_class_f1": {n: round(m["f1"], 4) for n, m in oof_metrics["per_class"].items()}}]
        proba_accum = [oof_proba.copy()]
        for s in range(1, args.repeats):
            sd = args.seed + s
            op, _oc, opr, _fr, _pt = cross_validate(X_seq, X_feat_raw, y, groups, cfg, args, seed=sd, quiet=True)
            mk = opr >= 0
            mm = classification_metrics(y[mk], opr[mk], op[mk], class_names=CLASS_NAMES)
            accs.append(mm["accuracy"]); mf1s.append(mm["macro_f1"]); bacc.append(mm["balanced_accuracy"])
            per_seed.append({"seed": sd, "accuracy": round(mm["accuracy"], 4),
                             "macro_f1": round(mm["macro_f1"], 4),
                             "balanced_accuracy": round(mm["balanced_accuracy"], 4),
                             "per_class_f1": {n: round(m["f1"], 4) for n, m in mm["per_class"].items()}})
            proba_accum.append(op)
            print(f"    seed {sd}: acc={mm['accuracy']:.3f} macroF1={mm['macro_f1']:.3f} balAcc={mm['balanced_accuracy']:.3f}")
        oof_proba_meanseeds = np.mean(np.stack(proba_accum), axis=0)
        ms_metrics = classification_metrics(y, oof_proba_meanseeds.argmax(1), oof_proba_meanseeds, class_names=CLASS_NAMES)
        per_class_f1_range = {
            n: {"min": round(min(ps["per_class_f1"][n] for ps in per_seed), 4),
                "max": round(max(ps["per_class_f1"][n] for ps in per_seed), 4),
                "mean": round(float(np.mean([ps["per_class_f1"][n] for ps in per_seed])), 4)}
            for n in CLASS_NAMES
        }
        repeat_stats = {
            "n_seeds": args.repeats, "seeds": [args.seed + s for s in range(args.repeats)],
            "per_seed": per_seed,
            "accuracy_mean": round(float(np.mean(accs)), 4), "accuracy_std": round(float(np.std(accs)), 4),
            "macro_f1_mean": round(float(np.mean(mf1s)), 4), "macro_f1_std": round(float(np.std(mf1s)), 4),
            "balanced_accuracy_mean": round(float(np.mean(bacc)), 4), "balanced_accuracy_std": round(float(np.std(bacc)), 4),
            "per_class_f1_across_seeds": per_class_f1_range,
            "mean_probability_oof": {
                "accuracy": ms_metrics["accuracy"], "macro_f1": ms_metrics["macro_f1"],
                "balanced_accuracy": ms_metrics["balanced_accuracy"],
                "confusion_matrix": ms_metrics["confusion_matrix"],
                "per_class": {n: {k: round(v, 4) for k, v in m.items() if isinstance(v, (int, float))}
                              for n, m in ms_metrics["per_class"].items()},
            },
        }
        print(f"  -> macro-F1 {repeat_stats['macro_f1_mean']:.3f} ± {repeat_stats['macro_f1_std']:.3f}  "
              f"| accuracy {repeat_stats['accuracy_mean']:.3f} ± {repeat_stats['accuracy_std']:.3f}")
        print(f"  -> OOF prob. media {args.repeats} semillas: acc={ms_metrics['accuracy']:.3f} macroF1={ms_metrics['macro_f1']:.3f}")
    calib_raw = expected_calibration_error(oof_proba[mask], y[mask])
    calib_temp = expected_calibration_error(oof_proba_cal[mask], y[mask])
    calib_pooled = expected_calibration_error(
        softmax_np(np.log(np.clip(oof_proba[mask], 1e-9, 1)) / max(pooled_temperature, 1e-6)), y[mask]
    )
    calibration_block = {
        "method": "temperature scaling; T por fold ajustada en su validacion interna; "
                  "T_pooled ajustada sobre TODAS las validaciones internas concatenadas (no sobre test OOF)",
        "raw": calib_raw,
        "temperature_scaled_per_fold": calib_temp,
        "temperature_scaled_pooled": calib_pooled,
        "fold_temperatures": [r["temperature"] for r in fold_rows],
        "pooled_temperature": pooled_temperature,
    }

    print("\n  --- Metricas OOF (validacion cruzada por sujeto) ---")
    print(f"  accuracy          {oof_metrics['accuracy']:.3f}")
    print(f"  balanced accuracy {oof_metrics['balanced_accuracy']:.3f}")
    print(f"  macro-F1          {oof_metrics['macro_f1']:.3f}")
    print(f"  macro ROC-AUC OvR {oof_metrics['macro_roc_auc_ovr']}")
    for name, m in oof_metrics["per_class"].items():
        print(f"    {name:20s} P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} n={m['support']}")
    print(f"  calibracion  ECE raw={calib_raw['ece']} -> T_pooled={calib_pooled['ece']}  "
          f"(Brier {calib_raw['brier']} -> {calib_pooled['brier']})  T_pooled={pooled_temperature}  "
          f"T por fold={[r['temperature'] for r in fold_rows]}")

    # ---- modelo final: todos los datos, val interno para early stopping ----
    print("\n  Entrenando modelo FINAL con todos los datos...")
    all_idx = np.arange(len(y))
    tr_rel, val_rel = grouped_inner_split(y, groups, args.seed + 999, val_frac=0.15)
    final_model, final_scaler, final_history, final_best = train_one(
        X_seq, X_feat_raw, y, all_idx[tr_rel], all_idx[val_rel], dict(cfg), args, args.seed + 999, verbose_tag="final"
    )

    import torch

    # T del modelo desplegado = T ajustada sobre TODAS las validaciones internas
    # concatenadas (~100 muestras), mucho mas fiable que la T de un solo val
    # interno de ~16-24 muestras (que suele saturar en el limite de la rejilla).
    fold_temps = [r["temperature"] for r in fold_rows]
    final_temperature = pooled_temperature
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(final_model.state_dict(), MODEL_WEIGHTS_PATH)
    write_json(MODEL_CONFIG_PATH, {
        **cfg,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "framework": f"pytorch {torch.__version__}",
        "epochs": args.epochs, "patience": args.patience, "batch_size": args.batch_size,
        "lr": args.lr, "weight_decay": args.weight_decay, "label_smoothing": args.label_smoothing,
        "folds": args.folds, "seed": args.seed, "augment": not args.no_augment,
        "final_best_epoch": final_best["epoch"],
        "temperature": final_temperature,
        "dataset_excluded": list(getattr(__import__("video_training_common"), "MANIFEST_EXCLUDE", {}).keys()),
        "dataset_n_samples": int(len(y)),
        "dataset_n_subjects": int(len(np.unique(groups))),
        "deterministic": True,
    })
    write_json(FEATURE_SCALER_PATH, final_scaler.to_json())
    write_json(LABEL_MAP_PATH, {
        "class_names": CLASS_NAMES,
        "label_to_class": {str(i): n for i, n in enumerate(CLASS_NAMES)},
        "class_to_label": {n: i for i, n in enumerate(CLASS_NAMES)},
    })
    write_json(TRAINING_HISTORY_PATH, {"final_model": final_history, "folds": fold_rows})
    write_json(CV_METRICS_PATH, {
        "validation_method": f"StratifiedGroupKFold(k={args.folds}) por subject_id; OOF agregado",
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_samples": int(len(y)),
        "n_subjects": int(len(np.unique(groups))),
        "class_names": CLASS_NAMES,
        "videos_per_class": {CLASS_NAMES[i]: int(c) for i, c in enumerate(np.bincount(y, minlength=NUM_CLASSES))},
        "oof": oof_metrics,
        "cv_stability_multiseed": repeat_stats,
        "calibration": calibration_block,
        "final_temperature": final_temperature,
        "folds": fold_rows,
        # atajos que consume el frontend / API. Se usa la MEDIA multi-semilla
        # (estimacion honesta del rendimiento esperado de un modelo con este
        # dataset), no un unico split que tiene alta varianza. Si no hubo
        # repeticiones, se cae al split primario.
        "accuracy": (repeat_stats["accuracy_mean"] if repeat_stats else oof_metrics["accuracy"]),
        "accuracy_std": (repeat_stats["accuracy_std"] if repeat_stats else 0.0),
        "macro_f1": (repeat_stats["macro_f1_mean"] if repeat_stats else oof_metrics["macro_f1"]),
        "macro_f1_std": (repeat_stats["macro_f1_std"] if repeat_stats else 0.0),
        "balanced_accuracy": (repeat_stats["balanced_accuracy_mean"] if repeat_stats else oof_metrics["balanced_accuracy"]),
        "precision": oof_metrics["macro_precision"],
        "recall": oof_metrics["macro_recall"],
        "f1_score": (repeat_stats["macro_f1_mean"] if repeat_stats else oof_metrics["macro_f1"]),
        "confusion_matrix": (repeat_stats["mean_probability_oof"]["confusion_matrix"]
                             if repeat_stats else oof_metrics["confusion_matrix"]),
        "confusion_matrix_source": ("OOF probabilidad media 5 semillas" if repeat_stats else "OOF split primario"),
        "samples": int(len(y)),
    })
    np.savez_compressed(
        OOF_PATH, proba=oof_proba, proba_cal=oof_proba_cal, pred=oof_pred, y=y, subject_id=groups,
        proba_meanseeds=oof_proba_meanseeds, pred_meanseeds=oof_proba_meanseeds.argmax(1),
    )
    save_plots(final_history, y[mask], oof_pred[mask])

    print(f"\n  modelo      -> {MODEL_WEIGHTS_PATH}")
    print(f"  metricas CV -> {CV_METRICS_PATH}")
    print(f"  graficas    -> {PLOTS_DIR}")
    print(f"  tiempo total: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
