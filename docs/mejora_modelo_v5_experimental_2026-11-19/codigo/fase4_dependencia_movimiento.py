"""Fases 4 y 7 (robustez) -- pruebas con modelos CONGELADOS (checkpoints de los 25 folds OOF; no se reentrena ni se escribe en V4).
Uso: python fase4_dependencia_movimiento.py --version v4|v5P|v5S
 * reproduce las predicciones OOF guardadas (comprobacion de que checkpoint, particion y escalador coinciden);
 * ablaciones por rama, importancia por permutacion de grupos de caracteristicas, perturbaciones temporales y espejo;
 * perturbaciones de grabacion (aspecto, paneo de camara, zoom, jitter de landmarks, perdida de cuadros) aplicadas a los
   landmarks y re-procesadas con el pipeline COMPLETO de cada version.
Cada prueba se evalua sobre los mismos 25 folds de prueba (sujetos no vistos por ese modelo)."""
import argparse, csv, json, sys, copy
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v5_preproc as V
import v5_train_core as TC
from data_v5 import load_videos, V4 as V4DIR
DC, T11 = TC.DC, TC.T11
import torch
from video_training_common import build_feature_row
OUT = HERE.parent / "resultados"
ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True, choices=["v4", "v5P", "v5S"]); ap.add_argument("--boot", type=int, default=1000)
a = ap.parse_args()
torch.set_num_threads(1)
vids = load_videos(); N = len(vids)
y = np.array([v["y"] for v in vids]); g = np.array([v["group"] for v in vids])
SEEDS = [42, 43, 44, 45, 46]
FOLDS = {p: TC.sgkf(y, g, 5, p) for p in SEEDS}
W4, EPS = 5.03, 1e-6

# ------------------------------------------------------------------------------------------------ contexto por version
class Ctx: pass
C = Ctx(); C.ver = a.version
if a.version == "v4":
    z = np.load(V4DIR / "dataset_v4_preview.npz", allow_pickle=False)
    C.Xs, C.Xf = z["X_seq"].astype(np.float32), z["X_feat"].astype(np.float32)
    C.win = [np.array([i]) for i in range(N)]; C.names = [str(x) for x in z["feature_names"]]; C.groups = V.V4_GROUPS
    C.model_path = lambda p, k: V4DIR / "step12_training" / "models_cv" / "M1_principal" / f"p{p}_f{k}.pt"
    C.scaler = lambda p, k, tr: DC.FeatureScaler.fit(C.Xf[tr])
    C.cfg = DC.default_model_config(num_classes=4)
    C.mirror_seq = lambda s: s[DC._MIRROR_PERM].copy().__setitem__(slice(None), s[DC._MIRROR_PERM]) or _v4mir(s)
    def _v4mir(s):
        o = s[..., DC._MIRROR_PERM, :].copy(); o[..., DC._POS_X_IDX, :] *= -1.0; return o
    C.mirror_seq = _v4mir
    def _v4mir_ok(s):  # espejo fisicamente correcto aplicado a V4 (para cuantificar el efecto del defecto A1)
        o = s[..., DC._MIRROR_PERM, :].copy(); xi = [i for i, n in enumerate(DC.CHANNEL_NAMES) if n.endswith("_x") or n.endswith("_vx")]; o[..., xi, :] *= -1.0; return o
    C.mirror_seq_ok = _v4mir_ok
    C.mirror_feat = lambda f: f[..., DC._FEATURE_MIRROR_PERM]
else:
    zb = np.load(OUT / "dataset_v5_bank.npz", allow_pickle=False)
    keep = list(range(36)) if a.version == "v5P" else V.S_KEEP_IDX
    C.Xs, C.Xf = zb["X_seq"], zb["X_feat"][:, keep]; vid = zb["vid"]; C.t0 = zb["t0"]
    bank = TC.Bank(C.Xs, C.Xf, vid, N, 5); C.win = bank.eval; C.names = [V.FEATURES_V5[i] for i in keep]; C.groups = V.GROUPS
    tag = "V5P" if a.version == "v5P" else "V5S"
    C.model_path = lambda p, k: OUT / f"modelos_cv_{tag}" / f"p{p}_f{k}.pt"
    C.scaler = lambda p, k, tr: DC.FeatureScaler.from_json(json.loads((OUT / f"modelos_cv_{tag}" / f"p{p}_f{k}_scaler.json").read_text()))
    C.cfg = DC.default_model_config(num_classes=4); C.cfg["num_features"] = len(keep)
    TC.set_feature_columns(keep)
    C.mirror_seq = lambda s: V.mirror_seq(s) if s.ndim == 2 else np.stack([V.mirror_seq(x) for x in s])
    C.mirror_seq_ok = C.mirror_seq
    C.mirror_feat = lambda f: np.asarray(f)[..., TC.FPERM]
C.gidx = {k: [C.names.index(n) for n in v if n in C.names] for k, v in C.groups.items()}
C.gidx = {k: v for k, v in C.gidx.items() if v}

def load_model(p, k):
    m, _ = DC.build_model(dict(C.cfg)); m.load_state_dict(torch.load(C.model_path(p, k), map_location="cpu")); m.eval(); return m

def logits_for(model, scaler, videos, Xs, Xf):
    out = np.zeros((len(videos), 4))
    with torch.no_grad():
        for j, i in enumerate(videos):
            w = C.win[i]
            out[j] = model(torch.from_numpy(Xs[w]).float(), torch.from_numpy(scaler.transform(Xf[w])).float()).numpy().mean(0)
    return out

MODELS = {(p, k): load_model(p, k) for p in SEEDS for k in range(1, 6)}
SCALERS = {(p, k): C.scaler(p, k, tr) for p in SEEDS for k, (tr, te) in enumerate(FOLDS[p], start=1)}

def run(transform=None, Xs=None, Xf=None):
    """-> pred [5,N] y probs [5,N,4]. `transform(Xs, Xf, scaler, tr_info, rng)` actua SOLO sobre las ventanas del fold de prueba."""
    Xs = C.Xs if Xs is None else Xs; Xf = C.Xf if Xf is None else Xf
    P = np.zeros((len(SEEDS), N, 4))
    for si, p in enumerate(SEEDS):
        rng = np.random.default_rng(1000 + p)
        for k, (tr, te) in enumerate(FOLDS[p], start=1):
            sc = SCALERS[(p, k)]
            xs, xf = Xs, Xf
            if transform is not None:
                xs, xf = transform(Xs.copy(), Xf.copy(), sc, tr, te, rng)
            lg = logits_for(MODELS[(p, k)], sc, te, xs, xf)
            P[si, te] = T11.softmax_np(lg)
    return P.argmax(2), P

def mf1(pred):
    out = []
    for pr in pred:
        f = []
        for c in range(4):
            tp = ((pr == c) & (y == c)).sum(); p_ = tp / max((pr == c).sum(), 1); r = tp / max((y == c).sum(), 1); f.append(2 * p_ * r / max(p_ + r, 1e-12))
        out.append(np.mean(f))
    return np.array(out)
def acc(pred): return np.array([(pr == y).mean() for pr in pred])

ug = np.unique(g); gi = {u: np.where(g == u)[0] for u in ug}
_brng = np.random.default_rng(7)
BOOT = [np.concatenate([gi[u] for u in _brng.choice(ug, len(ug))]) for _ in range(a.boot)]
def mf1_idx(pred, idx):
    out = []
    for pr in pred:
        yy, pp = y[idx], pr[idx]; f = []
        for c in range(4):
            tp = ((pp == c) & (yy == c)).sum(); p_ = tp / max((pp == c).sum(), 1); r = tp / max((yy == c).sum(), 1); f.append(2 * p_ * r / max(p_ + r, 1e-12))
        out.append(np.mean(f))
    return np.mean(out)
def delta_ci(pred0, pred1):
    d = np.array([mf1_idx(pred1, b) - mf1_idx(pred0, b) for b in BOOT]); return [round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]

RES = {"version": a.version, "n_modelos": len(MODELS)}
base_pred, base_P = run()
# 0. reproduccion de las predicciones OOF guardadas
if a.version == "v4":
    pz = np.load(V4DIR / "step18_bn/oof_probabilities.npz"); ref = np.stack([pz[f"A_{p}"].argmax(1) for p in SEEDS])
else:
    pz = np.load(OUT / f"oof_{tag}.npz"); ref = np.stack([pz[f"p{p}"].argmax(1) for p in SEEDS])
RES["reproduccion_OOF_guardado"] = {"coincidencia_prediccion": round(float((ref == base_pred).mean()), 4)}
RES["linea_base"] = {"macro_f1_media": round(float(mf1(base_pred).mean()), 4), "accuracy_media": round(float(acc(base_pred).mean()), 4)}
print("reproduccion", RES["reproduccion_OOF_guardado"], RES["linea_base"], flush=True)
rows = []
def record(name, kind, pred, note=""):
    r = {"prueba": name, "tipo": kind, "macro_f1": round(float(mf1(pred).mean()), 4), "delta_macro_f1": round(float(mf1(pred).mean() - mf1(base_pred).mean()), 4),
         "IC95_delta_(bootstrap por sujeto)": delta_ci(base_pred, pred), "accuracy": round(float(acc(pred).mean()), 4),
         "acuerdo_con_prediccion_original": round(float((pred == base_pred).mean()), 4), "nota": note}
    rows.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)

# 1. ablacion de ramas (se sustituye la entrada de una rama por el promedio de entrenamiento; NO se reentrena -> fuera de distribucion)
def t_feat_neutral(Xs, Xf, sc, tr, te, rng):
    Xf[:] = sc.means; return Xs, Xf
def t_seq_neutral(Xs, Xf, sc, tr, te, rng):
    wt = np.concatenate([C.win[i] for i in tr]); m = Xs[wt].mean((0, 2), keepdims=True); Xs[:] = m; return Xs, Xf
record("rama de caracteristicas neutralizada (solo secuencia)", "ablacion", run(t_feat_neutral)[0], "entrada neutra = media de entrenamiento; sin reentrenar")
record("rama de secuencia neutralizada (solo caracteristicas)", "ablacion", run(t_seq_neutral)[0], "idem")
# 2. importancia por permutacion de grupos de caracteristicas (entre videos del fold de prueba; 10 repeticiones)
for gname, idx in C.gidx.items():
    def tf(Xs, Xf, sc, tr, te, rng, idx=idx):
        wt = np.concatenate([C.win[i] for i in te])
        for _ in [0]:
            perm = rng.permutation(len(wt)); Xf[np.ix_(wt, idx)] = Xf[np.ix_(wt[perm], idx)]
        return Xs, Xf
    preds = [run(tf)[0] for _ in range(10)]
    pm = np.mean([mf1(p_).mean() for p_ in preds]); r = {"prueba": f"permutar grupo '{gname}' ({len(idx)} caract.)", "tipo": "permutacion", "macro_f1": round(float(pm), 4),
         "delta_macro_f1": round(float(pm - mf1(base_pred).mean()), 4), "IC95_delta_(bootstrap por sujeto)": delta_ci(base_pred, preds[0]), "accuracy": round(float(np.mean([acc(p_).mean() for p_ in preds])), 4),
         "acuerdo_con_prediccion_original": round(float(np.mean([(p_ == base_pred).mean() for p_ in preds])), 4), "nota": "media de 10 permutaciones; IC solo de la 1a"}
    rows.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
# 3. perturbaciones de la secuencia (posiciones modificadas y velocidades RECALCULADAS: coherencia posicion-velocidad)
def pos_to_seq(pos):  # pos [n,34,T] -> [n,68,T] velocidades = diferencia de las mismas posiciones
    vel = np.zeros_like(pos); vel[..., 1:] = np.diff(pos, axis=-1); return np.concatenate([pos, vel], axis=1)
def seq_tf(fn):
    def tf(Xs, Xf, sc, tr, te, rng):
        wt = np.concatenate([C.win[i] for i in te]); pos = Xs[wt, :34, :].astype(np.float64); Xs[wt] = pos_to_seq(fn(pos, rng)).astype(np.float32); return Xs, Xf
    return tf
def lowpass(pos, rng, w=9):
    k = np.ones(w) / w; pad = np.pad(pos, ((0, 0), (0, 0), (w // 2, w // 2)), mode="edge")
    return np.stack([[np.convolve(pad[i, c], k, mode="valid") for c in range(pos.shape[1])] for i in range(pos.shape[0])])
def phase_scramble(pos, rng):
    F = np.fft.rfft(pos, axis=-1); ph = np.exp(1j * rng.uniform(0, 2 * np.pi, size=F.shape)); ph[..., 0] = 1
    return np.fft.irfft(np.abs(F) * ph, n=pos.shape[-1], axis=-1)
def block_shuffle(pos, rng):
    T_ = pos.shape[-1]; nb = 8; b = T_ // nb; order = rng.permutation(nb)
    return np.concatenate([pos[..., o * b:(o + 1) * b] for o in order] + ([pos[..., nb * b:]] if T_ % nb else []), axis=-1)
record("secuencia: filtro pasa-bajos (media movil, velocidades recalculadas)", "perturbacion temporal", run(seq_tf(lowpass))[0], "fisicamente plausible (suaviza la dinamica fina)")
record("secuencia: tiempo invertido (velocidades recalculadas)", "perturbacion temporal", run(seq_tf(lambda p, r: p[..., ::-1]))[0], "cinematica invertida; coherente pero poco natural")
record("secuencia: fases aleatorias por canal (conserva espectro de amplitud)", "perturbacion temporal", run(seq_tf(phase_scramble))[0], "NO fisica (rompe la coordinacion entre articulaciones): solo informativa")
record("secuencia: bloques temporales barajados (8 bloques)", "perturbacion temporal", run(seq_tf(block_shuffle))[0], "NO fisica (saltos entre bloques): solo informativa")
# 4. espejo: V4 (como en el entrenamiento) vs fisicamente correcto
def mir_tf(seq_fn):
    def tf(Xs, Xf, sc, tr, te, rng):
        wt = np.concatenate([C.win[i] for i in te]); Xs[wt] = seq_fn(Xs[wt]); Xf[wt] = C.mirror_feat(Xf[wt]); return Xs, Xf
    return tf
if a.version == "v4":
    record("espejo horizontal con la transformacion de V4 (no invierte vx)", "espejo", run(mir_tf(C.mirror_seq))[0], "la usada en la aumentacion de entrenamiento V4")
    record("espejo horizontal fisicamente correcto (invierte x y vx)", "espejo", run(mir_tf(C.mirror_seq_ok))[0], "V4 se entreno con la version defectuosa")
else:
    record("espejo horizontal fisicamente correcto V5", "espejo", run(mir_tf(C.mirror_seq))[0], "V5 se entreno con esta transformacion")

# 5. perturbaciones de GRABACION: se modifican los landmarks y se re-procesa con el pipeline completo de la version
def f_aspect(k):
    return lambda fr, rng: [{**f, "landmarks": {n: {**p, "x": 0.5 + (p["x"] - 0.5) * k} for n, p in f["landmarks"].items()}} for f in fr]
def f_pan(rate):
    return lambda fr, rng: [{**f, "landmarks": {n: {**p, "x": p["x"] + rate * (f["timestamp_sec"] - fr[0]["timestamp_sec"])} for n, p in f["landmarks"].items()}} for f in fr]
def f_zoom(s):
    return lambda fr, rng: [{**f, "landmarks": {n: {**p, "x": 0.5 + (p["x"] - 0.5) * s, "y": 0.5 + (p["y"] - 0.5) * s} for n, p in f["landmarks"].items()}} for f in fr]
def f_jitter(sig):
    def fn(fr, rng):
        return [{**f, "landmarks": {n: {**p, "x": p["x"] + rng.normal(0, sig), "y": p["y"] + rng.normal(0, sig)} for n, p in f["landmarks"].items()}} for f in fr]
    return fn
def f_drop(pdrop):
    def fn(fr, rng):
        keep = [f for i, f in enumerate(fr) if i == 0 or rng.random() > pdrop]; return keep
    return fn

def rebuild_v4(fn, aspect_k=1.0):
    Xs, Xf = C.Xs.copy(), C.Xf.copy(); rng = np.random.default_rng(99)
    for i, v in enumerate(vids):
        fr = fn(v["frames"], rng); t0 = v["t0"]
        win = [f for f in fr if f["timestamp_sec"] - t0 < W4 - EPS]
        seq, _, _ = DC.frames_to_sequence(win)
        meta = {k: "" for k in ("video_path", "filename", "subject_id", "subject_documented", "condition", "label", "severity", "sequence")}
        feat = DC.extract_feature_vector(build_feature_row(meta, win, dict(v["q"], duration_seconds=v["w_eff"]), None))
        if seq is not None: Xs[i] = seq
        Xf[i] = feat
    return Xs, Xf

def rebuild_v5(fn, aspect_k=1.0):
    Xs, Xf = C.Xs.copy(), C.Xf.copy(); rng = np.random.default_rng(99)
    cache = {}
    keep_idx = [V.FEATURES_V5.index(n) for n in C.names]
    for i, v in enumerate(vids):
        fr = fn(v["frames"], rng)
        for w in np.where(zb["vid"] == i)[0]:
            r = V.window_inputs(fr, float(C.t0[w]), v["aspect"] / aspect_k)
            if r is not None:
                Xs[w] = r[0]; Xf[w] = r[1][keep_idx]
    return Xs, Xf

rb = rebuild_v4 if a.version == "v4" else rebuild_v5
for name, fn, k, note in [("aspecto: escena grabada en 4:3 en lugar de 16:9 (x * 1.333)", f_aspect(1.3333), 1.3333, "V5 recibe la relacion de aspecto real; V4 no la usa"),
                          ("aspecto: x * 0.75", f_aspect(0.75), 0.75, ""),
                          ("zoom x1.3 (persona mas grande en el cuadro)", f_zoom(1.3), 1.0, ""),
                          ("paneo de camara 0.05 /s (ancho de imagen)", f_pan(0.05), 1.0, "camara acompanando"),
                          ("jitter de landmarks sigma=0.005 (peor resolucion)", f_jitter(0.005), 1.0, ""),
                          ("jitter de landmarks sigma=0.01", f_jitter(0.01), 1.0, ""),
                          ("perdida aleatoria del 20 % de los cuadros con pose", f_drop(0.2), 1.0, "")]:
    xs, xf = rb(fn, k); record(name, "grabacion", run(Xs=xs, Xf=xf)[0], note)
RES["pruebas"] = rows
(OUT / f"fase4_robustez_{a.version}.json").write_text(json.dumps(RES, indent=1, ensure_ascii=False), encoding="utf-8")
print("OK")
