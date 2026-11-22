"""Frozen V5-CR video inference: training windows, mean logits, temperature.

No training, dataset writes, fallback predictions or changes to model weights.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from deep_common import FeatureScaler, build_model, default_model_config
from video_training_common import CLASS_HUMAN_LABEL, NO_DIAGNOSIS_NOTE
from v5cr import v5_preproc as V
from v5cr.v5cr_preproc import FEATURES_C, window_inputs_C

VERSION = "gait_deep_v5exp_V5CR_7e9ed60965fe"
EXPECTED_SHA256 = "7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade"
MODEL_DIR = ROOT / "models/gait_deep_v5cr"
LABELS = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
SHORT_LABEL = dict(zip(LABELS, ["Marcha normal", "Parkinson", "Esclerosis múltiple", "Riesgo de caída"]))
DISCLAIMER = ("Este análisis constituye una orientación basada en patrones de movimiento y no representa un "
              "diagnóstico médico. Los resultados corresponden a una clasificación experimental de patrones de "
              "marcha y requieren valoración por un profesional de salud.")
WINDOW_S = 5.03
STRIDE = 0.4
K = 5
OOF = {"accuracy": 0.8598, "macro_f1": 0.7852,
       "per_class": {"normal": {"f1": 0.9557}, "parkinson": {"f1": 0.9207},
                     "esclerosis_multiple": {"f1": 0.6839}, "riesgo_caida": {"f1": 0.5806}}}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_artifact(model_dir=MODEL_DIR):
    import torch
    # Small CPU model: cap intra-op threads to avoid oversubscription when the
    # web server and MediaPipe share this machine. No change to weights/inputs.
    torch.set_num_threads(2)
    manifest = json.loads((model_dir / "deployment_manifest.json").read_text(encoding="utf-8"))
    for suffix in (".pt", "_config.json", "_feature_scaler.json", "_label_map.json"):
        p = model_dir / f"{VERSION}{suffix}"
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha != manifest["sha256"].get(p.name) or (suffix == ".pt" and sha != EXPECTED_SHA256):
            raise ValueError(f"SHA-256 incorrecto: {p.name}")
    cfg = json.loads((model_dir / f"{VERSION}_config.json").read_text(encoding="utf-8"))
    raw = json.loads((model_dir / f"{VERSION}_feature_scaler.json").read_text(encoding="utf-8"))
    labels = json.loads((model_dir / f"{VERSION}_label_map.json").read_text(encoding="utf-8"))["class_names"]
    if cfg["feature_names"] != FEATURES_C or raw["columns"] != FEATURES_C or labels != LABELS:
        raise ValueError("Orden de características o etiquetas incompatible")
    if (cfg["in_channels"], cfg["sequence_length"], cfg["num_features"], cfg["num_classes"]) != (68, 40, 33, 4):
        raise ValueError("Dimensiones incompatibles")
    if cfg["model_version"] != VERSION or cfg["weights_sha256"] != EXPECTED_SHA256:
        raise ValueError("Identificación incompatible")
    if cfg["fps"] != 15 or cfg["window_s"] != 2.6 or cfg["protocol"]["K_eval_windows"] != K or cfg["temperature"] != 0.6615:
        raise ValueError("Protocolo incompatible")
    for key in ("medians", "means", "stds"):
        if len(raw[key]) != 33 or not np.isfinite(raw[key]).all():
            raise ValueError(f"Escalador inválido: {key}")
    if np.any(np.asarray(raw["stds"]) <= 0):
        raise ValueError("Desviaciones no positivas")
    scaler = FeatureScaler.from_json(raw)
    model, _ = build_model({k: cfg[k] for k in default_model_config(num_classes=4)})
    model.load_state_dict(torch.load(model_dir / f"{VERSION}.pt", map_location="cpu", weights_only=True))
    model.eval()
    return model, scaler, float(cfg["temperature"]), labels


def build_inputs(frames, duration, aspect, start=0.0, end=None):
    """Same segment, anchor, stride and acceptance as construir_dataset_v5.py.

    start/end allow read-only reproduction of the research manifest segments.
    Uploaded videos use [0, duration); neighboring pose frames remain available
    to the original interpolator, including beyond the 5.03 s analysis span.
    """
    if not np.isfinite([duration, aspect, start]).all() or duration <= 0 or aspect <= 0:
        raise ValueError("Metadatos inválidos")
    end = duration if end is None else min(end, duration)
    seg = [f for f in frames if start - V.EPS <= f["timestamp_sec"] < end - V.EPS]
    if not seg:
        raise ValueError("pose_insufficient")
    anchor = float(seg[0]["timestamp_sec"])
    effective = min(WINDOW_S, end - anchor)
    bank, offset = [], 0.0
    while anchor + offset + V.SPAN_S <= anchor + effective + V.EPS:
        result = window_inputs_C(seg, anchor + offset, aspect)
        if result is not None:
            bank.append(result)
        offset += STRIDE
    if not bank:
        raise ValueError("pose_insufficient")
    indices = np.unique(np.round(np.linspace(0, len(bank) - 1, min(K, len(bank)))).astype(int))
    selected = [bank[i] for i in indices]
    seq = np.stack([r[0] for r in selected]).astype(np.float32)
    feat = np.stack([r[1] for r in selected]).astype(np.float32)
    if seq.shape[1:] != (68, 40) or feat.shape != (len(selected), 33) or not np.isfinite(seq).all():
        raise ValueError("Entradas incompatibles")
    # NaN/inf in tabular inputs are deliberately imputed by the training scaler.
    return seq, feat, {"anchor": anchor, "effective_seconds": effective, "accepted_windows": len(bank),
                       "selected_indices": indices.tolist(), "windows": [r[2] for r in selected]}


def infer(model, scaler, temperature, seq, feat):
    import torch
    if seq.ndim != 3 or seq.shape[1:] != (68, 40) or feat.shape != (len(seq), 33) or len(seq) == 0:
        raise ValueError("Dimensiones de entrada inválidas")
    scaled = scaler.transform(feat)
    if not np.isfinite(seq).all() or not np.isfinite(scaled).all() or not np.isfinite(temperature) or temperature <= 0:
        raise ValueError("Entradas no finitas")
    with torch.no_grad():
        logits = model(torch.from_numpy(seq).float(), torch.from_numpy(scaled).float()).numpy()
    # Keep float32 mean, as TC.Bank.video_logits; float64 division as its output.
    mean = logits.mean(0).astype(np.float64)
    z = mean / temperature
    p = np.exp(z - z.max()); p /= p.sum()
    if p.shape != (4,) or not np.isfinite(p).all() or np.any(p < 0) or not np.isclose(p.sum(), 1):
        raise ValueError("Probabilidades inválidas")
    return mean, p


def build_warnings(pred, orientation, bg):
    warnings = []
    if orientation == "vertical":
        warnings.append({"code": "VIDEO_VERTICAL", "severity": "alta", "message": "El formato vertical está poco representado en el entrenamiento; la corrección de aspecto no valida esta vista."})
    if bg is not None and bg > 1e-4:
        warnings.append({"code": "CAMARA_MOVIL", "severity": "media", "message": "Se detectó movimiento de cámara. V5-CR corrige la traslación horizontal y la interpolación relativa; no se ha validado toda rotación, perspectiva, desenfoque u oclusión."})
    if pred in ("esclerosis_multiple", "riesgo_caida"):
        warnings.append({"code": "CLASE_EM_EXPERIMENTAL" if pred == "esclerosis_multiple" else "CLASE_RIESGO_NO_VALIDADA", "severity": "alta", "message": "Clase experimental, con confusión entre esclerosis múltiple y riesgo de caída y dependencia de la fuente de grabación; sin validación clínica."})
    warnings.append({"code": "VISTA_NO_VERIFICADA", "severity": "info", "message": "El sistema no verifica automáticamente la vista; se entrenó principalmente con video lateral de cuerpo completo. Validación interna sobre 117 videos, sin validación clínica ni externa."})
    return warnings


def failure(video, kind, message):
    return {"modelUsed": False, "modelUsedForVideo": False, "modelSource": "gait_deep_model", "modelVariant": "v5cr",
            "modelVersion": VERSION, "experimental": True, "failureKind": kind, "message": message, "video": video,
            "notes": NO_DIAGNOSIS_NOTE, "disclaimer": DISCLAIMER}


def predict_video(video):
    started = time.time()
    if not video.is_file():
        return failure(video.name, "video_not_found", "No se encontró el video.")
    try:
        model, scaler, temperature, labels = load_artifact()
    except Exception as exc:
        return failure(video.name, "model_unavailable", f"V5-CR no disponible: {exc}")
    try:
        rx = load_module("normalized_v5cr", HERE / "24_normalized_reextract.py")
        frames, quality, err = rx.extract_normalized(video)
        if err or not frames:
            return failure(video.name, "pose_insufficient", "Video no decodificable o sin pose suficiente.")
        aspect = float(quality["width"]) / float(quality["height"])
        seq, feat, selection = build_inputs(frames, float(quality["duration_seconds"]), aspect)
        _, p = infer(model, scaler, temperature, seq, feat)
    except ValueError as exc:
        kind = "pose_insufficient" if str(exc) == "pose_insufficient" else "inference_failed"
        return failure(video.name, kind, str(exc))
    except Exception as exc:
        return failure(video.name, "inference_failed", f"No se pudo procesar el video: {exc}")
    probs = dict(zip(labels, map(float, p)))
    detected = max(probs, key=probs.get)
    orientation = "vertical" if aspect < 1 else "horizontal"
    pose_rate = min(r["n_valid"] / V.T for r in selection["windows"])
    bg = None
    try:
        bm = load_module("background_v5cr", HERE / "background_motion.py")
        row = {"video": video.stem, "class": "", "source": "", "camera_style": "", "view": "", "video_path": str(video),
               "start_s": "", "end_s": "", "width": quality["width"], "height": quality["height"], "aspect_ratio": ""}
        bg = bm.measure(row, {"frames": frames, "quality": quality}, {}).get("bg_lk_median")
    except Exception:
        pass
    # Display actual V5-CR quantities without claiming diagnostic thresholds.
    values = {name: float(feat[0, i]) if np.isfinite(feat[0, i]) else None for i, name in enumerate(FEATURES_C)}
    groups = [("piernas", "Movimiento relativo de las piernas", FEATURES_C[3:13]),
              ("brazos", "Movimiento de los brazos", FEATURES_C[14:20]),
              ("postura", "Postura del tronco", FEATURES_C[22:27]),
              ("ritmo", "Ritmo de los pasos", FEATURES_C[27:])]
    highlights = [{"concept": key, "label": label, "values": {n: values[n] for n in names if values[n] is not None},
                   "note": "Mediciones de la primera ventana seleccionada, en escala corporal; sin umbrales diagnósticos."} for key, label, names in groups]
    return {
        "modelUsed": True, "modelUsedForVideo": True, "modelSource": "gait_deep_model", "modelVariant": "v5cr",
        "modelVersion": VERSION, "weightsSha256": EXPECTED_SHA256, "experimental": True,
        "predictionBasis": "experimental_v5cr_temporal_cnn_hip_relative_interpolation_mean_window_logits",
        "video": video.name, "detectedClass": detected, "detectedClassLabel": CLASS_HUMAN_LABEL[detected],
        "predicted_label": f"{detected}_pattern", "predictionLabel": "control" if detected == "normal" else f"possible_{detected}",
        "classProbabilities": probs, "classProbabilitiesList": [{"key": k, "label": CLASS_HUMAN_LABEL[k], "shortLabel": SHORT_LABEL[k], "probability": v} for k, v in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)],
        "confidence": probs[detected], "predictionConfidence": probs[detected],
        "confidenceMeaning": "Confianza del modelo en la clase predicha; no es la probabilidad de tener una enfermedad.",
        "orientationText": f"Clasificación experimental: patrón «{CLASS_HUMAN_LABEL[detected]}». Es una clasificación de patrones de marcha, no un diagnóstico.",
        "poseDetectionRate": round(pose_rate, 4), "framesAnalyzed": quality["processed_frames"], "framesWithPose": quality["valid_pose_frames"],
        "validSequenceFrames": min(r["n_valid"] for r in selection["windows"]), "analysisWindowSeconds": V.SPAN_S,
        "windowSelection": selection, "temperature": temperature, "gaitFeatures": values, "featureHighlights": highlights,
        "qualityInfo": {"orientation": orientation, "sourceWidth": quality["width"], "sourceHeight": quality["height"], "backgroundMotion15fps": bg, "windowPoseRate": pose_rate},
        "warnings": build_warnings(detected, orientation, bg), "validationReference": {"predictedClass": OOF["per_class"][detected], "method": "validación interna agrupada por sujeto (5x5); sin validación clínica"},
        "modelAccuracy": OOF["accuracy"], "modelMacroF1": OOF["macro_f1"], "modelF1Score": OOF["macro_f1"],
        "validationMethod": "StratifiedGroupKFold por sujeto, 5 folds x 5 semillas; selección anidada de épocas y temperatura; mismos 117 videos usados para desarrollar las variantes; sin validación externa",
        "modelSamples": 117, "modelControlSamples": 58, "modelParkinsonSamples": 26, "modelTrainSize": 117,
        "modelWarning": "Modelo experimental orientativo; validación interna, sin validación clínica.",
        "notes": NO_DIAGNOSIS_NOTE, "disclaimer": DISCLAIMER, "inferenceSeconds": round(time.time() - started, 2),
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Inferencia experimental V5-CR congelada")
    ap.add_argument("--video", required=True); ap.add_argument("--output-json")
    args = ap.parse_args()
    payload = predict_video(Path(args.video).resolve())
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    if args.output_json:
        out = Path(args.output_json); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    print(encoded)
    return 0 if payload["modelUsed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
