"""Criterio 1 de la Adenda 1: invariancia exacta a la camara que sigue en las 633 ventanas reales con V5-CR, e identidad con V5-C donde no hay enmascarados."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"))
import v5_preproc as V, v5c_preproc as C, v5cr_preproc as CR
from data_v5 import load_videos
z = np.load(HERE.parent / "resultados" / "dataset_v5c_bank.npz")
vids = load_videos(); hx = lambda f: (f["landmarks"]["LEFT_HIP"]["x"] + f["landmarks"]["RIGHT_HIP"]["x"]) / 2
worst_s = worst_f = 0.0; leak = 0; same_c = 0; n_unmasked = 0; diffs_vs_c = []
for j, (i, t0) in enumerate(zip(z["vid"], z["t0"])):
    v = vids[i]; h0 = hx(v["frames"][0])
    fr = [{**f, "landmarks": {n: {**p, "x": p["x"] - (hx(f) - h0)} for n, p in f["landmarks"].items()}} for f in v["frames"]]
    s0, f0, _ = CR.window_inputs_C(v["frames"], float(t0), v["aspect"]); s1, f1, _ = CR.window_inputs_C(fr, float(t0), v["aspect"])
    ds = float(np.abs(s0 - s1).max()); df = float(np.nanmax(np.abs(f0 - f1))); worst_s = max(worst_s, ds); worst_f = max(worst_f, df); leak += int(ds > 1e-6 or df > 1e-6)
    w = [f for f in v["frames"] if t0 - 1e-6 <= f["timestamp_sec"] <= t0 + V.SPAN_S + 1e-6]
    masked = sum(1 for f in w for p in f["landmarks"].values() if p.get("visibility", 1) < V.VIS_MIN) + (V.T - len(w)) * 17
    dC = float(np.abs(s0 - z["X_seq"][j]).max()); diffs_vs_c.append((masked, dC))
    if masked == 0:
        n_unmasked += 1; same_c += int(dC < 1e-6 and float(np.nanmax(np.abs(f0 - z["X_feat"][j]))) < 1e-6)
a = np.array(diffs_vs_c)
res = {"ventanas": int(len(z["vid"])), "ventanas_con_diferencia_bajo_camara_que_sigue(>1e-6)": leak, "max_dif_secuencia": worst_s, "max_dif_caracteristicas": worst_f,
       "ventanas_sin_enmascarados": n_unmasked, "de_ellas_identicas_a_V5C": same_c,
       "ventanas_con_enmascarados_donde_V5CR_difiere_de_V5C": int(((a[:, 0] > 0) & (a[:, 1] > 1e-6)).sum()),
       "criterio_1_cumple": bool(leak == 0 and same_c == n_unmasked)}
(HERE.parent / "resultados" / "fase8_prueba_cr.json").write_text(json.dumps(res, indent=1), encoding="utf-8"); print(json.dumps(res, indent=1))
