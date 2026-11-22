"""Fase 1 -- linea base V4: hashes de artefactos originales y reproduccion de metricas desde artefactos guardados.
Solo lectura sobre el proyecto; escribe unicamente en ../resultados/."""
import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
V4 = ROOT / "outputs" / "dataset_v4_4class"
OUT = Path(__file__).resolve().parents[1] / "resultados"
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
arts = {
 "modelo_base_M1.pt": ROOT/"models/gait_deep_v4exp/gait_deep_v4exp_protocolV2_M1_20261029_162234_d7323250d26f.pt",
 "modelo_candidato_BN.pt": ROOT/"models/gait_deep_v4exp_bn_candidate_v1/gait_deep_v4exp_M1_BN_recalibrated_candidate_v1.pt",
 "scaler_base.json": ROOT/"models/gait_deep_v4exp/gait_deep_v4exp_protocolV2_M1_20261029_162234_d7323250d26f_feature_scaler.json",
 "dataset_v4_preview.npz": V4/"dataset_v4_preview.npz", "samples_v4_preview.csv": V4/"samples_v4_preview.csv",
 "manifest_v4_preview.csv": V4/"manifest_v4_preview.csv", "oof_probabilities.npz": V4/"step18_bn/oof_probabilities.npz",
 "oof_predictions_step12.csv": V4/"step12_training/results/oof_predictions.csv",
 "train_protocol_v2.py": V4/"step12_training/train_protocol_v2.py", "deep_common.py": ROOT/"scripts/video_training/deep/deep_common.py",
 "video_training_common.py": ROOT/"scripts/video_training/video_training_common.py",
 "11_train_deep_model.py": ROOT/"scripts/video_training/deep/11_train_deep_model.py",
 "14_predict_deep_video_v4exp.py": ROOT/"scripts/video_training/deep/14_predict_deep_video_v4exp.py",
 "24_normalized_reextract.py": ROOT/"scripts/video_training/deep/24_normalized_reextract.py"}
hashes = {k: sha(v) for k, v in arts.items()}
pc = {p.name: sha(p) for p in sorted((V4/"pose_cache").glob("*.pkl"))}
hashes["pose_cache_pkl_count"] = len(pc); hashes["pose_cache_combined_sha256"] = hashlib.sha256("".join(f"{k}{v}" for k, v in pc.items()).encode()).hexdigest()
z = np.load(V4/"dataset_v4_preview.npz", allow_pickle=False)
y = z["y"]; g = z["split_group"].astype(str)
info = {"n_videos": int(len(y)), "n_groups": int(len(set(g))), "videos_por_clase": np.bincount(y).tolist(),
        "grupos_por_clase": [len(set(g[y == i])) for i in range(4)], "X_seq": list(z["X_seq"].shape), "X_feat": list(z["X_feat"].shape),
        "features": [str(c) for c in z["feature_names"]], "nan_en_X_feat": int(np.isnan(z["X_feat"]).sum())}
man = [r for r in csv.DictReader(open(V4/"manifest_v4_preview.csv", encoding="utf-8")) if r["include_in_preview"] == "true"]
st = {}
for r in man: st.setdefault(r["split_group"], set()).add((r["class"], r["subject_status"]))
info["estado_grupos"] = Counter(s for v in st.values() for (_, s) in v)
info["grupos_provisionales_por_clase"] = Counter(c for v in st.values() for (c, s) in v if "provis" in s.lower())
info["valores_subject_status"] = sorted({r["subject_status"] for r in man})
# reproducir metricas OOF desde artefactos guardados (sin reentrenar)
def metrics(pred):
    M = np.zeros((4, 4), int)
    for t, p in zip(y, pred): M[t, p] += 1
    tp = np.diag(M).astype(float); P = tp/np.maximum(M.sum(0), 1); R = tp/np.maximum(M.sum(1), 1); F = np.where(P+R > 0, 2*P*R/np.maximum(P+R, 1e-12), 0)
    return dict(acc=float(tp.sum()/M.sum()), mf1=float(F.mean()), f1=F.tolist(), rec=R.tolist(), prec=P.tolist(), M=M)
pz = np.load(V4/"step18_bn/oof_probabilities.npz", allow_pickle=False)
rep = {}
for tag, key in (("M1_base", "A"), ("M1_BN_candidato", "B")):
    ms = [metrics(pz[f"{key}_{s}"].argmax(1)) for s in (42, 43, 44, 45, 46)]
    rep[tag] = {"macro_f1_mean": round(float(np.mean([m["mf1"] for m in ms])), 4), "accuracy_mean": round(float(np.mean([m["acc"] for m in ms])), 4),
                "f1_por_clase": np.round(np.mean([m["f1"] for m in ms], 0), 4).tolist(), "recall_por_clase": np.round(np.mean([m["rec"] for m in ms], 0), 4).tolist(),
                "conf_suma": np.sum([m["M"] for m in ms], 0).tolist()}
# cross-check con oof_predictions.csv del Paso 12 (M1 base)
rows = list(csv.DictReader(open(V4/"step12_training/results/oof_predictions.csv", encoding="utf-8")))
m1 = [r for r in rows if r["variant"] == "M1_principal"]
ok = {}
for p in (42, 43, 44, 45, 46):
    sel = {r["video"]: r["pred"] for r in m1 if int(r["partition_seed"]) == p}
    vids = [str(v) for v in z["video"]]
    ok[p] = bool(np.array_equal(np.array([CL.index(sel[v]) for v in vids]), pz[f"A_{p}"].argmax(1)))
rep["coincide_oof_csv_paso12_con_npz"] = ok
(OUT/"fase1_hashes_originales.json").write_text(json.dumps(hashes, indent=1), encoding="utf-8")
(OUT/"fase1_linea_base_v4.json").write_text(json.dumps({"dataset": info, "metricas_reproducidas": rep}, indent=1, ensure_ascii=False, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)), encoding="utf-8")
print(json.dumps({"dataset": info, "metricas_reproducidas": rep}, ensure_ascii=False, default=lambda o: dict(o) if isinstance(o, Counter) else str(o))[:3500])
