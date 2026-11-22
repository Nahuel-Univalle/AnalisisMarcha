"""Fase 4/7 -- cuanto codifican las caracteristicas (V4 vs V5) propiedades de la GRABACION: correlacion de Spearman con la relacion de aspecto
y sondas lineales de orientacion (dentro de EM+Riesgo) y de fps (dentro de Normal+Parkinson). Solo lectura."""
import json, sys, csv
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import v5_preproc as V
from data_v5 import load_videos, V4
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
OUT = HERE.parent / "resultados"
vids = load_videos(); N = len(vids)
smp = list(csv.DictReader(open(V4 / "samples_v4_preview.csv", encoding="utf-8")))
y = np.array([v["y"] for v in vids]); g = np.array([v["group"] for v in vids])
asp = np.array([float(r["aspect_ratio"]) for r in smp]); ori = np.array([r["orientation"] for r in smp]); fps = np.array([float(r["src_fps"]) for r in smp])
z4 = np.load(V4 / "dataset_v4_preview.npz", allow_pickle=False); F4 = z4["X_feat"].astype(float)
zb = np.load(OUT / "dataset_v5_bank.npz", allow_pickle=False); F5 = np.stack([np.nanmean(zb["X_feat"][zb["vid"] == i], 0) for i in range(N)])
def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 5 or np.std(a[m]) == 0: return np.nan
    from scipy.stats import rankdata
    ra, rb = rankdata(a[m]), rankdata(b[m]); return float(np.corrcoef(ra, rb)[0, 1])
res = {}
nonlab = np.isin(y, [2, 3]); lab = ~nonlab
for name, F in (("V4", F4), ("V5", F5)):
    rho_all = np.array([spearman(F[:, j], asp) for j in range(F.shape[1])]); rho_nl = np.array([spearman(F[nonlab, j], asp[nonlab]) for j in range(F.shape[1])])
    res[f"{name}_spearman_aspecto"] = {"n_caract": F.shape[1], "|rho|>0.5 (117 videos)": int(np.nansum(np.abs(rho_all) > 0.5)), "|rho|>0.65 (117 videos)": int(np.nansum(np.abs(rho_all) > 0.65)),
                                       "|rho| mediano (117)": round(float(np.nanmedian(np.abs(rho_all))), 3), "|rho|>0.5 dentro de EM+Riesgo (n=33)": int(np.nansum(np.abs(rho_nl) > 0.5)),
                                       "|rho| mediano dentro EM+Riesgo": round(float(np.nanmedian(np.abs(rho_nl))), 3)}
def probe(F, target, mask, seeds=(42, 43, 44, 45, 46)):
    X = F[mask]; t = target[mask]; gg = g[mask]; aucs = []
    X = np.where(np.isfinite(X), X, np.nanmedian(X, 0))
    for s in seeds:
        sc = np.zeros(len(t)); ok = True
        for tr, te in StratifiedGroupKFold(4, shuffle=True, random_state=s).split(X, t, gg):
            if len(set(t[tr])) < 2: ok = False; break
            st = StandardScaler().fit(X[tr]); clf = LogisticRegression(max_iter=3000, C=0.3, class_weight="balanced").fit(st.transform(X[tr]), t[tr]); sc[te] = clf.predict_proba(st.transform(X[te]))[:, 1]
        if ok: aucs.append(roc_auc_score(t, sc))
    return round(float(np.mean(aucs)), 3) if aucs else None
t_ori = (ori == "vertical").astype(int); t_fps = (fps >= 40).astype(int)
for name, F in (("V4", F4), ("V5", F5)):
    res[f"{name}_sonda_AUC"] = {"orientacion vertical vs horizontal (dentro de EM+Riesgo; n=33)": probe(F, t_ori, nonlab), "fps>=40 vs 30 (dentro de Normal+Parkinson; n=84)": probe(F, t_fps, lab)}
res["nota"] = "AUC 0.5 = las caracteristicas no codifican esa propiedad; 1.0 = la codifican perfectamente. n pequeno: usar solo como indicador."
(OUT / "fase4b_sesgo_caracteristicas.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8"); print(json.dumps(res, indent=1, ensure_ascii=False))
