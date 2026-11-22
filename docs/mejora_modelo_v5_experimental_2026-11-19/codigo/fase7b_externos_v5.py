"""Fase 7b -- inferencia aislada del V5 final sobre videos NO usados en el entrenamiento (2 externos + 20 excluidos del dataset por calidad).
Procesamiento 100 % local (MediaPipe via 24_normalized_reextract.extract_normalized, el mismo extractor de V4). No sube nada, no escribe en BD.
Etiquetas: nombre de archivo / fuente, SIN validacion clinica. Los 20 excluidos fueron descartados por calidad -> no son un conjunto de evaluacion limpio.
Los resultados se comparan con las predicciones de V4 ya calculadas en C:\\Users\\fnahu\\Desktop\\COMPARACION_MODELOS_MARCHA_2026-11-19\\PREDICCIONES_COMPARADAS.csv"""
import csv, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import v5_preproc as V
import v5_train_core as TC
from data_v5 import ROOT, V4
import torch
DC, T11 = TC.DC, TC.T11
OUT = HERE.parent / "resultados"; CK = HERE.parent / "checkpoints"
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
spec = importlib.util.spec_from_file_location("rx", ROOT / "scripts/video_training/deep/24_normalized_reextract.py")
rx = importlib.util.module_from_spec(spec); spec.loader.exec_module(rx)
def load(tag):
    cfgf = [p for p in CK.glob(f"gait_deep_v5exp_{tag}_*_config.json")][0]; cfg = json.loads(cfgf.read_text(encoding="utf-8"))
    base = str(cfgf)[:-len("_config.json")]
    m, _ = DC.build_model({k: cfg[k] for k in DC.default_model_config(4)}); m.load_state_dict(torch.load(base + ".pt", map_location="cpu")); m.eval()
    sc = DC.FeatureScaler.from_json(json.loads(Path(base + "_feature_scaler.json").read_text(encoding="utf-8")))
    keep = [V.FEATURES_V5.index(n) for n in cfg["feature_names"]]
    return m, sc, float(cfg["temperature"]), keep, cfg["model_version"]
MODELS = {t: load(t) for t in ("V5P", "V5S")}
prev = {r["video"]: r for r in csv.DictReader(open(r"C:\Users\fnahu\Desktop\COMPARACION_MODELOS_MARCHA_2026-11-19\PREDICCIONES_COMPARADAS.csv", encoding="utf-8-sig")) if r["estrato"] != "T_entrenamiento"}
paths = {}
for p in (V4 / "external_validation" / "inputs").glob("*.mp4"): paths[p.stem] = p
for p in (ROOT / "videos").rglob("*"):
    if p.is_file() and p.stem in prev: paths[p.stem] = p
rows = []
for name in sorted(prev):
    t = time.time(); frames, quality, err = rx.extract_normalized(paths[name])
    if err or not frames:
        rows.append({"video": name, "clase_registrada": prev[name]["clase_registrada"], "fallo": "pose_insuficiente"}); continue
    dur = float(quality["duration_seconds"]); t0 = frames[0]["timestamp_sec"]; w_eff = min(5.03, dur - t0); aspect = float(quality["width"]) / float(quality["height"])
    starts = []; s = 0.0
    while s + V.SPAN_S <= w_eff + 1e-6: starts.append(t0 + s); s += 0.4
    if not starts: starts = [t0]
    ix = np.unique(np.round(np.linspace(0, len(starts) - 1, min(5, len(starts)))).astype(int))
    inp = [V.window_inputs(frames, starts[i], aspect) for i in ix]; inp = [r for r in inp if r is not None]
    row = {"video": name, "estrato": prev[name]["estrato"], "clase_registrada": prev[name]["clase_registrada"], "ventanas_usadas": len(inp), "aspecto": round(aspect, 3), "pred_V4_BN_A": prev[name]["pred_A_BN"], "pred_V4_base_B": prev[name]["pred_B_M1base"]}
    if not inp: row["fallo"] = "sin_ventanas_validas"; rows.append(row); continue
    Xs = np.stack([r[0] for r in inp]); Xf = np.stack([r[1] for r in inp])
    for tag, (m, sc, T, keep, ver) in MODELS.items():
        with torch.no_grad():
            lg = m(torch.from_numpy(Xs).float(), torch.from_numpy(sc.transform(Xf[:, keep])).float()).numpy().mean(0)
        p = T11.softmax_np((lg / T)[None])[0]; row[f"pred_{tag}"] = CL[int(p.argmax())]; row[f"conf_{tag}"] = round(float(p.max()), 3)
        row[f"probs_{tag}"] = ";".join(f"{c}={x:.3f}" for c, x in zip(CL, p))
    row["segundos"] = round(time.time() - t0, 1); rows.append(row); print(name, row.get("pred_V5P"), row["clase_registrada"], flush=True)
keys = list(dict.fromkeys(k for r in rows for k in r))
with open(OUT / "externos_v5.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
ok = [r for r in rows if "pred_V5P" in r]
def acc(col): return sum(r[col] == r["clase_registrada"] for r in ok)
summ = {"n": len(ok), "V4_BN_A": acc("pred_V4_BN_A"), "V4_base_B": acc("pred_V4_base_B"), "V5P": acc("pred_V5P"), "V5S": acc("pred_V5S"),
        "por_clase_n": {c: sum(r["clase_registrada"] == c for r in ok) for c in CL},
        "por_clase_aciertos_V5P": {c: sum(r["clase_registrada"] == c and r["pred_V5P"] == c for r in ok) for c in CL},
        "por_clase_aciertos_V4_BN": {c: sum(r["clase_registrada"] == c and r["pred_V4_BN_A"] == c for r in ok) for c in CL},
        "por_clase_aciertos_V4_base": {c: sum(r["clase_registrada"] == c and r["pred_V4_base_B"] == c for r in ok) for c in CL},
        "predicciones_V5P": {c: sum(r["pred_V5P"] == c for r in ok) for c in CL}, "predicciones_V4_BN": {c: sum(r["pred_V4_BN_A"] == c for r in ok) for c in CL},
        "predicciones_V4_base": {c: sum(r["pred_V4_base_B"] == c for r in ok) for c in CL}}
(OUT / "externos_v5_resumen.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False), encoding="utf-8"); print(json.dumps(summ, ensure_ascii=False))
