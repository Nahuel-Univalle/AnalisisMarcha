"""Fase 2B/2E -- decision DOCUMENTADA y pre-registrada de (B) escala corporal y (E) ventana temporal, con datos del propio dataset.
Solo lectura. Salida: resultados/fase2_escala.json, fase2_ventana.json"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v5_preproc as V
from data_v5 import load_videos
OUT = HERE.parent / "resultados"
vids = load_videos()
print(len(vids), "videos")
# --- B. alternativas de escala: estabilidad intra-ventana y dependencia de la vista ----------------------------------------
kinds = ["torso", "v4_seq_max", "v4_feat_median3", "torso_plus_thigh", "torso_shoulder_hip_mean"]
rows = {k: [] for k in kinds}; view = []; cv = {k: [] for k in kinds}; height = []
low_vis = []
for v in vids:
    ts, P = V.frames_to_points(v["frames"], v["aspect"], vis_min=0.0)
    ts2, P2 = V.frames_to_points(v["frames"], v["aspect"], vis_min=0.2)
    n_lm = sum(1 for f in v["frames"] for p in f["landmarks"].values())
    n_low = sum(1 for f in v["frames"] for p in f["landmarks"].values() if p.get("visibility", 1) < 0.2)
    low_vis.append(n_low / max(n_lm, 1))
    Pg = V.resample_grid(ts, P, v["t0"])
    LH, RH, LS, RS = (Pg[:, V.IDX[n]] for n in ("LEFT_HIP", "RIGHT_HIP", "LEFT_SHOULDER", "RIGHT_SHOULDER"))
    S, H = (LS + RS) / 2, (LH + RH) / 2
    torso = np.linalg.norm(S - H, axis=-1)
    ank = (Pg[:, V.IDX["LEFT_ANKLE"], 1] + Pg[:, V.IDX["RIGHT_ANKLE"], 1]) / 2
    h = float(np.nanmedian(np.abs(ank - Pg[:, V.IDX["NOSE"], 1])))
    height.append(h); view.append(v["view"])
    for k in kinds:
        rows[k].append(V.body_scale(Pg, k))
    # CV intra-ventana por alternativa (per-frame)
    sw = np.linalg.norm(LS - RS, axis=-1); hw = np.linalg.norm(LH - RH, axis=-1)
    thigh = (np.linalg.norm(Pg[:, V.IDX["LEFT_KNEE"]] - LH, axis=-1) + np.linalg.norm(Pg[:, V.IDX["RIGHT_KNEE"]] - RH, axis=-1)) / 2
    per = {"torso": torso, "v4_seq_max": np.maximum(np.maximum(torso, sw), hw), "v4_feat_median3": np.median(np.stack([sw, hw, torso]), 0),
           "torso_plus_thigh": torso + thigh, "torso_shoulder_hip_mean": (torso + sw + hw) / 3}
    for k in kinds:
        a = per[k]; cv[k].append(float(np.nanstd(a) / np.nanmean(a)))
height = np.array(height); view = np.array(view)
res = {"visibilidad<0.2_fraccion_de_landmarks": {"media": round(float(np.mean(low_vis)), 4), "max": round(float(np.max(low_vis)), 4)}, "alternativas": {}}
for k in kinds:
    ratio = np.array(rows[k]) / height
    per_view = {vw: round(float(np.nanmedian(ratio[view == vw])), 4) for vw in sorted(set(view))}
    vals = [x for x in per_view.values()]
    res["alternativas"][k] = {"cv_intra_ventana_mediana": round(float(np.nanmedian(cv[k])), 4), "escala/altura_corporal_mediana_por_vista": per_view,
                              "dispersion_entre_vistas_max/min": round(max(vals) / min(vals), 3), "n_por_vista": {vw: int((view == vw).sum()) for vw in sorted(set(view))}}
(OUT / "fase2_escala.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(res, indent=1, ensure_ascii=False))
# --- E. sonda de duracion: ¿se puede predecir la clase solo con la duracion de la ventana V4? --------------------------------
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
y = np.array([v["y"] for v in vids]); g = np.array([v["group"] for v in vids])
w = np.array([[v["w_eff"], float(v["w_eff"] >= 5.03 - 1e-6)] for v in vids])
def f1m(p):
    f = []
    for c in range(4):
        tp = ((p == c) & (y == c)).sum(); pr = tp / max((p == c).sum(), 1); rc = tp / max((y == c).sum(), 1); f.append(2 * pr * rc / max(pr + rc, 1e-12))
    return float(np.mean(f)), f
out = {}
for name, X in [("duracion_ventana_V4 (w_eff, llena)", w)]:
    for mname in ("logreg", "rf"):
        vals = []
        for seed in (42, 43, 44, 45, 46):
            pred = np.full(len(y), -1)
            for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(X, y, g):
                clf = LogisticRegression(max_iter=2000, class_weight="balanced") if mname == "logreg" else RandomForestClassifier(200, random_state=seed, class_weight="balanced_subsample", min_samples_leaf=2)
                from sklearn.preprocessing import StandardScaler
                sc = StandardScaler().fit(X[tr]); pred[te] = clf.fit(sc.transform(X[tr]), y[tr]).predict(sc.transform(X[te]))
            vals.append(f1m(pred)[0])
        out[f"{name} [{mname}]"] = {"macro_f1_OOF_media": round(float(np.mean(vals)), 4), "sd": round(float(np.std(vals, ddof=1)), 4)}
chance = float(np.mean([(y == c).mean() for c in range(4)]))
out["referencia_azar_aprox_macroF1"] = 0.25
out["videos_con_ventana_V4<2.6s"] = int((np.array([v["w_eff"] for v in vids]) < V.SPAN_S).sum())
out["ventana_V4_s_por_clase"] = {c: {"min": round(float(min(v['w_eff'] for v in vids if v['cls'] == c)), 2), "mediana": round(float(np.median([v['w_eff'] for v in vids if v['cls'] == c])), 2)} for c in V.__dict__.get("CLASS_NAMES", ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"])}
out["ventanas_V5: tamano fijo (s)"] = V.SPAN_S
(OUT / "fase2_ventana.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False))
