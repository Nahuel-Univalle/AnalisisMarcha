"""Nucleo de entrenamiento V5. MISMA arquitectura GaitTemporalModel, mismo optimizador, perdida, epocas maximas, seleccion de E*
por validacion interna y calibracion por temperatura que train_protocol_v2.py (V4). Diferencias declaradas:
  - entradas V5 (v5_preproc); cada video aporta un banco de ventanas de 2.6 s; en cada epoca se muestrea UNA ventana por video;
  - evaluacion por video = media de logits de K=5 ventanas equiespaciadas;
  - aumentacion coherente (espejo fisico + ruido en posiciones con velocidades recalculadas); sin escala de amplitud ni recorte temporal."""
from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts" / "video_training")); sys.path.insert(0, str(ROOT / "scripts" / "video_training" / "deep"))
import v5_preproc as V
import deep_common as DC
spec = importlib.util.spec_from_file_location("train11", ROOT / "scripts/video_training/deep/11_train_deep_model.py")
T11 = importlib.util.module_from_spec(spec); spec.loader.exec_module(T11)
from sklearn.model_selection import StratifiedGroupKFold

CFG = {"partition_seeds": [42, 43, 44, 45, 46], "outer_folds": 5, "inner_folds": 3, "max_epochs": 240, "smoothing_window": 5,
       "batch_size": 16, "lr": 1e-3, "weight_decay": 2e-4, "label_smoothing": 0.05, "grad_clip": 5.0, "K_eval_windows": 5,
       "noise_std": 0.01, "mirror_prob": 0.5, "noise_prob": 0.6}


FPERM = None  # permutacion L/R de las columnas de caracteristicas usadas (depende de la variante)


def set_feature_columns(keep):
    global FPERM
    names = [V.FEATURES_V5[i] for i in keep]; perm = list(range(len(names)))
    for l, r in V._FLR:
        if l in names and r in names:
            i, j = names.index(l), names.index(r); perm[i], perm[j] = perm[j], perm[i]
    FPERM = np.asarray(perm)


def augment_pair(seq, feat, rng, noise_std=None, mirror_prob=None):
    noise_std = CFG["noise_std"] if noise_std is None else noise_std
    mirror_prob = CFG["mirror_prob"] if mirror_prob is None else mirror_prob
    s, f = seq, feat
    if rng.random() < mirror_prob:
        s, f = V.mirror_seq(s), np.asarray(f)[FPERM if FPERM is not None else V.FEAT_MIRROR_PERM]
    pos = s[:34].T.astype(np.float64)
    if noise_std > 0 and rng.random() < CFG["noise_prob"]:
        pos = pos + rng.normal(0.0, noise_std, size=pos.shape)
    return V.positions_to_sequence(pos), f.astype(np.float32)


def augment_v5(seq, rng, noise_std=0.01, mirror=True, force_mirror=False):
    """Solo secuencia (pruebas)."""
    s = V.mirror_seq(seq) if (mirror and (force_mirror or rng.random() < 0.5)) else seq
    pos = s[:34].T.astype(np.float64)
    if noise_std > 0 and rng.random() < CFG["noise_prob"]:
        pos = pos + rng.normal(0, noise_std, size=pos.shape)
    return V.positions_to_sequence(pos)


def sgkf(y, g, k, seed):
    return list(StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, g))


class Bank:
    """Banco de ventanas por video. Xs [Nw,68,40], Xf [Nw,36 o menos], vid [Nw]."""
    def __init__(self, Xs, Xf, vid, n_videos, K=5):
        self.Xs, self.Xf, self.vid, self.n = Xs, Xf, vid, n_videos
        self.win = [np.where(vid == i)[0] for i in range(n_videos)]
        self.eval = []
        for w in self.win:
            ix = np.unique(np.round(np.linspace(0, len(w) - 1, min(K, len(w)))).astype(int))
            self.eval.append(w[ix])

    def cols(self, keep):
        return Bank(self.Xs, self.Xf[:, keep], self.vid, self.n)

    def fit_scaler(self, videos):
        idx = np.concatenate([self.eval[i] for i in videos])
        return DC.FeatureScaler.fit(self.Xf[idx])

    def video_logits(self, model, scaler, videos):
        import torch
        model.eval(); out = np.zeros((len(videos), 4))
        with torch.no_grad():
            for j, i in enumerate(videos):
                w = self.eval[i]
                lg = model(torch.from_numpy(self.Xs[w]).float(), torch.from_numpy(scaler.transform(self.Xf[w])).float()).numpy()
                out[j] = lg.mean(0)
        return out


def train_fixed(bank, y, tr, epochs, cfg_model, seed, val=None):
    import torch
    from torch import nn
    DC.seed_everything(seed)
    scaler = bank.fit_scaler(tr)
    Xf_s = scaler.transform(bank.Xf)
    model, _ = DC.build_model(dict(cfg_model))
    counts = np.bincount(y[tr], minlength=4).astype(np.float64)
    w = counts.sum() / (4 * np.clip(counts, 1.0, None))
    crit = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32), label_smoothing=CFG["label_smoothing"])
    opt = torch.optim.Adam(model.parameters(), lr=CFG["lr"], weight_decay=CFG["weight_decay"])
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=8)
    rng = np.random.default_rng(seed)
    curve = {"train_loss": [], "val_loss": []}; val_logits = []
    for _ in range(epochs):
        model.train(); tot = n = 0
        for b in T11.iterate_batches(len(tr), CFG["batch_size"], rng, shuffle=True):
            ss, ff, tt = [], [], []
            for vi in tr[b]:
                wi = bank.win[vi][rng.integers(len(bank.win[vi]))]
                s, f = augment_pair(bank.Xs[wi], Xf_s[wi], rng)
                ss.append(s); ff.append(f); tt.append(y[vi])
            opt.zero_grad()
            loss = crit(model(torch.from_numpy(np.stack(ss)).float(), torch.from_numpy(np.stack(ff)).float()), torch.tensor(tt).long())
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), CFG["grad_clip"]); opt.step()
            tot += loss.item() * len(b); n += len(b)
        tl = tot / max(n, 1); sched.step(tl); curve["train_loss"].append(tl)
        if val is not None:
            lg = bank.video_logits(model, scaler, val)
            curve["val_loss"].append(T11.nll(lg, y[val])); val_logits.append(lg.astype(np.float32))
    return model, scaler, curve, val_logits


def choose_epoch(curves, sizes):
    m = np.average(np.array([c["val_loss"] for c in curves]), axis=0, weights=sizes)
    k = CFG["smoothing_window"]; pad = np.pad(m, (k // 2, k // 2), mode="edge")
    sm = np.convolve(pad, np.ones(k) / k, mode="valid")
    return int(np.argmin(sm)) + 1, m, sm
