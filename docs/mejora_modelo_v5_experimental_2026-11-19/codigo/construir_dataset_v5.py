"""Construye el banco de ventanas V5 desde pose_cache (SOLO LECTURA). Mismos 117 videos y orden que dataset_v4_preview.npz.
Ventanas de 2.6 s con paso 0.4 s DENTRO de la ventana de analisis V4 (ancla ... ancla + w_eff): mismo tramo de video que V4, recortado.
Salida: resultados/dataset_v5_bank.npz (fuera de Git: ver .gitignore del informe)."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v5_preproc as V
from data_v5 import load_videos, V4
OUT = HERE.parent / "resultados"
STRIDE = 0.4
vids = load_videos()
z4 = np.load(V4 / "dataset_v4_preview.npz", allow_pickle=False)
assert [v["video"] for v in vids] == [str(x) for x in z4["video"]], "orden distinto al de V4"
assert np.array_equal(np.array([v["y"] for v in vids]), z4["y"]) and [v["group"] for v in vids] == [str(x) for x in z4["split_group"]]
Xs, Xf, vid, t0s, rej, interp = [], [], [], [], [], []
for i, v in enumerate(vids):
    s = 0.0; n = 0
    while v["t0"] + s + V.SPAN_S <= v["t0"] + v["w_eff"] + 1e-6:
        r = V.window_inputs(v["frames"], v["t0"] + s, v["aspect"])
        if r is None:
            rej.append((v["video"], round(s, 2)))
        else:
            Xs.append(r[0]); Xf.append(r[1]); vid.append(i); t0s.append(v["t0"] + s); interp.append(r[2]["interp_frac"]); n += 1
        s += STRIDE
    assert n > 0, f"{v['video']} sin ventanas validas"
Xs = np.stack(Xs).astype(np.float32); Xf = np.stack(Xf).astype(np.float32); vid = np.array(vid)
np.savez_compressed(OUT / "dataset_v5_bank.npz", X_seq=Xs, X_feat=Xf, vid=vid, t0=np.array(t0s), interp_frac=np.array(interp),
                    video=np.array([vids[i]["video"] for i in vid]), y=np.array([v["y"] for v in vids]), group=np.array([v["group"] for v in vids]),
                    feature_names=np.array(V.FEATURES_V5))
cnt = np.bincount(vid, minlength=len(vids))
rep = {"videos": len(vids), "ventanas": int(len(vid)), "ventanas_por_video": {"min": int(cnt.min()), "mediana": float(np.median(cnt)), "max": int(cnt.max())},
       "ventanas_medias_por_clase": {c: round(float(cnt[[v['cls'] == c for v in vids]].mean()), 2) for c in ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]},
       "ventanas_rechazadas_por_pose_insuficiente": rej, "fraccion_interpolada_media": round(float(np.mean(interp)), 4), "X_seq": list(Xs.shape), "X_feat": list(Xf.shape),
       "nan_en_X_feat": int(np.isnan(Xf).sum()), "ventanas_con_nan": int((np.isnan(Xf).any(1)).sum())}
(OUT / "fase5_dataset_v5.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(rep, indent=1, ensure_ascii=False))
