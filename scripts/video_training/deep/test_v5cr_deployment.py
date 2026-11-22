"""Read-only training/evaluation parity and real-video deployment tests.

Artificial empty/corrupt clips are negative code fixtures, never patients.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT_DIR = ROOT / "docs/integracion_v5cr_2026-11-19"
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("deploy_v5cr", HERE / "15_predict_deep_video_v5cr.py")
D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
OLD = ROOT / "docs/mejora_modelo_v5_experimental_2026-11-19/codigo"
CR = ROOT / "docs/optimizacion_final_v5_2026-11-19"
sys.path.insert(0, str(OLD)); sys.path.insert(0, str(CR / "codigo"))
import v5_train_core as TC
import v5cr_preproc as ORIGINAL
from data_v5 import load_videos


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--real-videos", action="store_true"); args = ap.parse_args()
    import torch
    torch.set_num_threads(2)
    checks, real = [], []
    def check(name, condition, **detail):
        checks.append({"name": name, "passed": bool(condition), **detail})
        print(f"{'PASS' if condition else 'FAIL'} {name}", flush=True)
    model, scaler, temperature, labels = D.load_artifact()
    check("unit: frozen checkpoint SHA-256", hashlib.sha256((D.MODEL_DIR / f"{D.VERSION}.pt").read_bytes()).hexdigest() == D.EXPECTED_SHA256)
    with tempfile.TemporaryDirectory(prefix="v5cr_artifact_") as tmp:
        dest = Path(tmp)
        for p in D.MODEL_DIR.glob("*.json"): shutil.copyfile(p, dest / p.name)
        weights = D.MODEL_DIR / f"{D.VERSION}.pt"
        shutil.copyfile(weights, dest / weights.name)
        with (dest / weights.name).open("ab") as f: f.write(b"tamper-test")
        try: D.load_artifact(dest); rejected = False
        except ValueError: rejected = True
        check("unit: reject altered checkpoint, no fallback", rejected)
    z = np.load(CR / "resultados/dataset_v5cr_bank.npz", allow_pickle=False)
    check("unit: feature order (bank/config/preprocessor/scaler)", z["feature_names"].tolist() == ORIGINAL.FEATURES_C == D.FEATURES_C == scaler.columns)
    raw = json.loads((CR / f"checkpoints/{D.VERSION}_feature_scaler.json").read_text(encoding="utf-8"))
    original_scaler = TC.DC.FeatureScaler.from_json(raw)
    check("unit: statistics unchanged", all(np.array_equal(getattr(scaler, k), getattr(original_scaler, k)) for k in ("medians", "means", "stds")))
    check("unit: exact imputation/normalization", np.array_equal(scaler.transform(z["X_feat"]), original_scaler.transform(z["X_feat"])))
    # Mathematical fixture, only for nonfinite imputation.
    fixture = z["X_feat"][:1].copy(); fixture[0, :3] = [np.nan, np.inf, -np.inf]
    check("unit: NaN/inf imputed with original medians", np.array_equal(scaler.transform(fixture), original_scaler.transform(fixture)) and np.isfinite(scaler.transform(fixture)).all())
    for invalid_seq, invalid_feat in [(np.zeros((1,68,39),np.float32),np.zeros((1,33),np.float32)), (np.zeros((1,68,40),np.float32),np.zeros((1,36),np.float32))]:
        try: D.infer(model, scaler, temperature, invalid_seq, invalid_feat); rejected = False
        except ValueError: rejected = True
        check("unit: reject wrong dimensions", rejected)
    vids = load_videos()
    bank = TC.Bank(z["X_seq"], z["X_feat"], z["vid"], len(vids))
    refitted = bank.fit_scaler(np.arange(len(vids)))
    check("integrated: scaler statistics reproduced from training evaluation windows (no model training)", all(np.array_equal(getattr(refitted, k), getattr(original_scaler, k)) for k in ("medians", "means", "stds")))
    reference_logits = bank.video_logits(model, original_scaler, np.arange(len(vids)))
    max_seq = max_feat = max_logits = max_prob = max_camera = max_aspect = 0.0
    selection_ok = True
    for i, v in enumerate(vids):
        # Exact segment end is material only for short clips: use manifest's w_eff.
        anchor = v["t0"]
        end = anchor + v["w_eff"] if v["w_eff"] < D.WINDOW_S else None
        seq, feat, info = D.build_inputs(v["frames"], v["q"]["duration_seconds"], v["aspect"], anchor, end)
        idx = bank.eval[i]
        selection_ok &= len(seq) == len(idx) and np.allclose([x["t0"] for x in info["windows"]], z["t0"][idx], atol=1e-12)
        max_seq = max(max_seq, float(np.max(np.abs(seq - z["X_seq"][idx]))))
        max_feat = max(max_feat, float(np.nanmax(np.abs(feat - z["X_feat"][idx]))))
        lg, p = D.infer(model, scaler, temperature, seq, feat)
        reference_p = TC.T11.softmax_np(reference_logits[i:i+1] / temperature)[0]
        max_logits = max(max_logits, float(np.max(np.abs(lg - reference_logits[i]))))
        max_prob = max(max_prob, float(np.max(np.abs(p - reference_p))))
    check("integrated: window selection on 117 original segments", selection_ok)
    check("integrated: training bank sequence equality", max_seq == 0, max_abs_error=max_seq)
    check("integrated: training bank feature equality", max_feat == 0, max_abs_error=max_feat)
    check("integrated: evaluator/deployment logits", max_logits < 1e-6, max_abs_error=max_logits)
    check("integrated: evaluator/deployment temperature probabilities", max_prob < 1e-6, max_abs_error=max_prob)
    # All 633 windows, preserving real missing landmarks and timestamps.
    for j, i in enumerate(z["vid"]):
        v = vids[i]; t0 = float(z["t0"][j])
        moved = copy.deepcopy(v["frames"])
        for frame in moved:
            lm = frame["landmarks"]; hip = (lm["LEFT_HIP"]["x"] + lm["RIGHT_HIP"]["x"]) / 2
            for point in lm.values(): point["x"] -= hip
        r = D.window_inputs_C(moved, t0, v["aspect"])
        max_camera = max(max_camera, float(np.max(np.abs(r[0] - z["X_seq"][j]))), float(np.nanmax(np.abs(r[1] - z["X_feat"][j]))))
        stretched = copy.deepcopy(v["frames"])
        for frame in stretched:
            for point in frame["landmarks"].values(): point["x"] /= 0.75
        r = D.window_inputs_C(stretched, t0, v["aspect"] * 0.75)
        max_aspect = max(max_aspect, float(np.max(np.abs(r[0] - z["X_seq"][j]))), float(np.nanmax(np.abs(r[1] - z["X_feat"][j]))))
    check("unit on 633 real windows: horizontal camera translation", max_camera < 1e-6, max_abs_error=max_camera)
    check("unit on 633 real windows: aspect correction", max_aspect < 1e-6, max_abs_error=max_aspect)
    try: D.build_inputs([], 5, 16/9); rejected = False
    except ValueError: rejected = True
    check("unit: no prediction without pose", rejected)
    if args.real_videos:
        # Existing research videos, never represented as new patients.
        import csv
        manifest = list(csv.DictReader(open(ROOT / "outputs/dataset_v4_4class/manifest_v4_preview.csv", encoding="utf-8")))
        selected = []
        for cls in labels:
            candidates = [r for r in manifest if r["class"] == cls and r["include_in_preview"] == "true"]
            selected.append(candidates[0])
        # Include a real portrait clip if not already selected.
        portrait = next((r for r in manifest if r["include_in_preview"] == "true" and float(r["height"]) > float(r["width"])), None)
        if portrait and portrait not in selected: selected.append(portrait)
        for row in selected:
            path = ROOT / row["video_path"]
            payload = D.predict_video(path)
            name = f"real_{row['video']}"
            (REPORT_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
            valid = payload.get("modelUsed") and payload.get("modelVersion") == D.VERSION and np.isclose(sum(payload["classProbabilities"].values()), 1)
            check(f"integrated: real video {row['class']} {row['orientation']}", valid)
            real.append({"video": row["video"], "source_class": row["class"], "orientation": row["orientation"], "camera_style": row["camera_style"], "result": payload.get("detectedClass"), "modelUsed": payload["modelUsed"], "seconds": payload.get("inferenceSeconds"), "evidence": f"{name}.json"})
        with tempfile.TemporaryDirectory(prefix="v5cr_negative_") as tmp:
            import cv2
            corrupt = Path(tmp) / "corrupt.mp4"; corrupt.write_bytes(b"invalid clip")
            empty = Path(tmp) / "empty.mp4"
            writer = cv2.VideoWriter(str(empty), cv2.VideoWriter_fourcc(*"mp4v"), 15, (320,240))
            for _ in range(60): writer.write(np.zeros((240,320,3), np.uint8))
            writer.release()
            for path in (corrupt, empty, Path(tmp) / "missing.mp4"):
                payload = D.predict_video(path)
                check(f"integrated: negative fixture {path.name}", not payload["modelUsed"] and "classProbabilities" not in payload)
    report = {"checks": checks, "real_videos": real, "passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "real_videos_requested": args.real_videos}
    (REPORT_DIR / "PRUEBAS_PYTHON.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
