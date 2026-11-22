"""Diagnostico (sin entrenar): ¿de donde viene la sensibilidad residual de V5-C a la camara que sigue (-0.023)?
Hipotesis: los huecos de landmarks enmascarados (visibilidad < 0.2) se interpolan en coordenadas ABSOLUTAS, y al restar la cadera real la traslacion global se 'filtra'."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"))
import v5_preproc as V, v5c_preproc as C
from data_v5 import load_videos
z = np.load(HERE.parent / "resultados" / "dataset_v5c_bank.npz")
vids = load_videos()
hx = lambda f: (f["landmarks"]["LEFT_HIP"]["x"] + f["landmarks"]["RIGHT_HIP"]["x"]) / 2
rows = []
for j, (i, t0) in enumerate(zip(z["vid"], z["t0"])):
    v = vids[i]; h0 = hx(v["frames"][0])
    fr = [{**f, "landmarks": {n: {**p, "x": p["x"] - (hx(f) - h0)} for n, p in f["landmarks"].items()}} for f in v["frames"]]
    s, ft, _ = C.window_inputs_C(fr, float(t0), v["aspect"])
    w = [f for f in v["frames"] if t0 - 1e-6 <= f["timestamp_sec"] <= t0 + V.SPAN_S + 1e-6]
    masked = sum(1 for f in w for p in f["landmarks"].values() if p.get("visibility", 1) < V.VIS_MIN) + (V.T - len(w)) * 17
    rows.append((float(np.abs(s - z["X_seq"][j]).max()), float(np.nanmax(np.abs(ft - z["X_feat"][j]))), masked, int(z["y"][i])))
a = np.array(rows)
leak = a[:, 0] > 1e-6
res = {"ventanas": len(a), "ventanas_con_diferencia_en_secuencia(>1e-6)": int(leak.sum()), "de_ellas_con_landmarks_enmascarados_o_cuadros_interpolados": int((a[leak, 2] > 0).sum()),
       "ventanas_SIN_enmascarados": int((a[:, 2] == 0).sum()), "de_estas_con_diferencia": int(((a[:, 2] == 0) & leak).sum()),
       "max_dif_secuencia": round(float(a[:, 0].max()), 4), "mediana_dif_secuencia_en_ventanas_con_fuga": round(float(np.median(a[leak, 0])), 4) if leak.any() else 0,
       "fraccion_con_fuga_por_clase": {c: round(float(leak[a[:, 3] == k].mean()), 3) for k, c in enumerate(["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"])}}
(HERE.parent / "resultados" / "fase8_fuga_residual.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(res, indent=1, ensure_ascii=False))
