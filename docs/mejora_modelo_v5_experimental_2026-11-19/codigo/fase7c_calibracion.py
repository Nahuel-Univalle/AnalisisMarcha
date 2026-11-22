"""Calibracion con temperatura POR FOLD (T ajustada solo en validacion interna): V4 base (pcal_* de step12) vs V5 (c{seed} de oof_V5*.npz)."""
import csv, json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from data_v5 import V4
OUT = HERE.parent / "resultados"; CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
z = np.load(V4 / "dataset_v4_preview.npz"); y = z["y"]; vids = [str(v) for v in z["video"]]
rows = [r for r in csv.DictReader(open(V4 / "step12_training/results/oof_predictions.csv", encoding="utf-8")) if r["variant"] == "M1_principal"]
def ece(P, yy, nb=10):
    cf = P.max(1); ok = P.argmax(1) == yy; e = 0
    for lo in np.linspace(0, 1, nb, endpoint=False):
        m = (cf > lo) & (cf <= lo + 1 / nb)
        if m.any(): e += m.mean() * abs(ok[m].mean() - cf[m].mean())
    return e
def m(PP):
    return {"ece": round(float(np.mean([ece(P, y) for P in PP])), 4), "brier": round(float(np.mean([np.mean(((P - np.eye(4)[y]) ** 2).sum(1)) for P in PP])), 4),
            "nll": round(float(np.mean([-np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1))) for P in PP])), 4)}
res = {}
V4c = []
for p in (42, 43, 44, 45, 46):
    d = {r["video"]: r for r in rows if int(r["partition_seed"]) == p}
    V4c.append(np.array([[float(d[v][f"pcal_{c}"]) for c in CL] for v in vids]))
res["V4 base (M1), calibrado por fold"] = m(V4c)
pz = np.load(V4 / "step18_bn/oof_probabilities.npz")
res["V4 base (M1), crudo"] = m([pz[f"A_{s}"] for s in (42, 43, 44, 45, 46)])
for tag in ("V5P", "V5S"):
    d = np.load(OUT / f"oof_{tag}.npz"); res[f"{tag}, crudo"] = m([d[f"p{s}"] for s in (42, 43, 44, 45, 46)]); res[f"{tag}, calibrado por fold"] = m([d[f"c{s}"] for s in (42, 43, 44, 45, 46)])
(OUT / "calibracion_v4_v5.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8"); print(json.dumps(res, indent=1, ensure_ascii=False))
