"""
Inferencia del modelo EXPERIMENTAL de 4 clases (Dataset V4, modelo M1, protocolo V2).

Reemplaza a 13_predict_deep_video.py como Tier 1 de /api/analysis/video. NO usa el pipeline de 13_predict
(extract_video_features, video completo, cadencia con la duracion del video): reproduce exactamente el
preprocesamiento con el que se entreno el modelo, verificado bit a bit en el Paso 14
(outputs/dataset_v4_4class/step14_final_model/infer_v4exp.py):

VIDEO -> extract_normalized (15 fps, <=720 px, MediaPipe) -> ventana 5.03 s desde el primer cuadro con pose
      -> frames_to_sequence [68 x 96] -> build_feature_row (duracion = ventana analizada) -> FeatureScaler
      -> GaitTemporalModel -> softmax(logits / T) -> 4 probabilidades

Sin efectos laterales: no escribe en data/ ni en models/. Clasificacion experimental, no diagnostico.
Uso: python 14_predict_deep_video_v4exp.py --video RUTA [--output-json RUTA]
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
PROJECT_ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from deep_common import (  # noqa: E402
    FEATURE_COLUMNS, MIN_VALID_FRAMES, FeatureScaler, build_model, default_model_config,
    extract_feature_vector, frames_to_sequence, gait_feature_highlights,
)
from video_training_common import CLASS_HUMAN_LABEL, NO_DIAGNOSIS_NOTE, build_feature_row  # noqa: E402

MODEL_DIR = PROJECT_ROOT / "models" / "gait_deep_v4exp_bn_candidate_v1"
VERSION = "gait_deep_v4exp_M1_BN_recalibrated_candidate_v1"
EXPECTED_SHA256 = "7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d"
WINDOW_S = 5.03          # ventana del Dataset V4 (Paso 4)
GRID_FPS = 15.0
EPS = 1e-6
# Umbrales de advertencia: solo los sustentados por los Pasos 7, 9.1 y 13 (provisionales donde se indica).
BG_MOVING = 1e-3         # Paso 7: camara en mano / acompanando (provisional, Paso 9.1)
BG_UNSTABLE = 1e-4       # Paso 7: por encima del maximo del tripode del laboratorio (provisional)
POSE_MIN = 0.50          # puerta de calidad existente del proyecto

DISCLAIMER = ("Este análisis constituye una orientación basada en patrones de movimiento y no representa un "
              "diagnóstico médico. Los resultados corresponden a una clasificación experimental de patrones de "
              "marcha y requieren valoración por un profesional de salud.")
# Rendimiento OOF del candidato BN (Paso 18, variante B: modelos de fold del Paso 12 con BatchNorm recalibrada
# solo con el TRAIN de cada fold; validacion agrupada por sujeto, 5 folds x 5 repeticiones;
# outputs/dataset_v4_4class/step18_bn/oof_comparison.json). Solo trazabilidad: la interfaz no muestra metricas.
OOF = {"accuracy": 0.851, "macro_f1": 0.744, "macro_precision": 0.742, "macro_recall": 0.751,
       "per_class": {"normal": {"precision": 0.993, "recall": 0.934, "f1": 0.963},
                     "parkinson": {"precision": 0.813, "recall": 0.962, "f1": 0.881},
                     "esclerosis_multiple": {"precision": 0.767, "recall": 0.745, "f1": 0.755},
                     "riesgo_caida": {"precision": 0.396, "recall": 0.364, "f1": 0.378}}}
SHORT_LABEL = {"normal": "Marcha normal", "parkinson": "Parkinson", "esclerosis_multiple": "Esclerosis múltiple",
               "riesgo_caida": "Riesgo de caída"}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def emit(payload: dict, output_json: Path | None, code: int) -> int:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return code


def failure(video: str, kind: str, message: str) -> dict:
    return {"modelUsed": False, "modelUsedForVideo": False, "modelSource": "gait_deep_model", "modelVariant": "v4exp",
            "modelVersion": VERSION, "experimental": True, "failureKind": kind, "message": message, "video": video,
            "notes": NO_DIAGNOSIS_NOTE, "disclaimer": DISCLAIMER}


def load_artifact():
    import torch
    wpath = MODEL_DIR / f"{VERSION}.pt"
    files = [wpath] + [MODEL_DIR / f"{VERSION}_{s}.json" for s in ("config", "feature_scaler", "label_map")]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise FileNotFoundError(f"faltan artefactos del modelo: {missing}")
    sha = hashlib.sha256(wpath.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        raise RuntimeError(f"SHA-256 del modelo no coincide ({sha[:12]})")
    cfg = json.loads(files[1].read_text(encoding="utf-8"))
    scaler = FeatureScaler.from_json(json.loads(files[2].read_text(encoding="utf-8")))
    labels = json.loads(files[3].read_text(encoding="utf-8"))["class_names"]
    model, _ = build_model({k: cfg[k] for k in default_model_config(num_classes=len(labels))})
    model.load_state_dict(torch.load(wpath, map_location="cpu"))
    model.eval()
    return model, scaler, float(cfg["temperature"]), labels


def build_warnings(pred: str, orientation: str, bg: float | None, window_pose_rate: float) -> list[dict]:
    w = []
    if orientation == "vertical":
        w.append({"code": "VIDEO_VERTICAL", "severity": "alta",
                  "message": "El video está en orientación vertical, un formato poco representado en el entrenamiento; el resultado es más incierto."})
    if bg is not None and bg > BG_MOVING:
        w.append({"code": "CAMARA_MOVIL", "severity": "alta",
                  "message": "Se detectó movimiento de la cámara. El modelo se entrenó principalmente con cámara fija; el resultado es más incierto."})
    elif bg is not None and bg > BG_UNSTABLE:
        w.append({"code": "CAMARA_POCO_ESTABLE", "severity": "media",
                  "message": "La cámara no parece completamente fija durante la caminata."})
    if window_pose_rate < POSE_MIN:
        w.append({"code": "POSE_BAJA", "severity": "alta",
                  "message": "El cuerpo se detectó en menos de la mitad de los momentos analizados."})
    if pred == "esclerosis_multiple":
        w.append({"code": "CLASE_EM_EXPERIMENTAL", "severity": "media",
                  "message": "Clasificación experimental: el resultado se asocia en parte al tipo de video con el que se entrenó esta clase."})
    if pred == "riesgo_caida":
        w.append({"code": "CLASE_RIESGO_NO_VALIDADA", "severity": "alta",
                  "message": "Clasificación experimental — clase no validada clínicamente. Presenta mayor incertidumbre y depende del tipo de video."})
    w.append({"code": "VISTA_NO_VERIFICADA", "severity": "info",
              "message": "El sistema no verifica automáticamente la vista de la cámara; el modelo se entrenó sobre todo con video lateral de cuerpo completo."})
    return w


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Clasificacion experimental de marcha (4 clases, modelo V4).")
    ap.add_argument("--video", required=True)
    ap.add_argument("--output-json")
    args = ap.parse_args()
    out = Path(args.output_json) if args.output_json else None
    video_path = Path(args.video).resolve()
    label = video_path.name
    t0 = time.time()
    if not video_path.exists():
        return emit(failure(label, "video_not_found", "No se encontró el video para la clasificación experimental."), out, 1)
    try:
        import torch
        model, scaler, temperature, labels = load_artifact()
    except Exception as exc:  # artefacto ausente o alterado: error controlado, nunca otro modelo
        return emit(failure(label, "model_unavailable", f"El modelo experimental de 4 clases no está disponible ({exc})."), out, 1)

    rx = _load_module("rx", HERE / "24_normalized_reextract.py")
    frames, quality, err = rx.extract_normalized(video_path)
    if err or not frames:
        return emit(failure(label, "pose_insufficient", "No se detectó el cuerpo en el video."), out, 1)
    duration = float(quality["duration_seconds"])
    anchor = frames[0]["timestamp_sec"]
    window = [f for f in frames if f["timestamp_sec"] - anchor < WINDOW_S - EPS]
    w_eff = min(WINDOW_S, duration - anchor)
    grid = max(1, int(round(w_eff * GRID_FPS)))
    window_pose_rate = min(1.0, len(window) / grid)
    if len(window) < MIN_VALID_FRAMES:
        return emit(failure(label, "pose_insufficient",
                            f"Calidad de pose insuficiente para la clasificación experimental ({len(window)} momentos con cuerpo detectado)."), out, 1)
    seq, _pose_rate, n_valid = frames_to_sequence(window)
    if seq is None:
        return emit(failure(label, "pose_insufficient", "No se pudo construir la secuencia de marcha a partir del video."), out, 1)
    meta = {"video_path": str(video_path), "filename": video_path.name, "subject_id": "", "subject_documented": "",
            "condition": "unknown", "label": "", "severity": "", "sequence": ""}
    feature_row = build_feature_row(meta, window, dict(quality, duration_seconds=w_eff), None)
    feat = extract_feature_vector(feature_row)

    with torch.no_grad():
        logits = model(torch.from_numpy(seq[None].astype(np.float32)),
                       torch.from_numpy(scaler.transform(feat.reshape(1, -1)))).numpy()[0]
    z = logits / temperature
    p = np.exp(z - z.max())
    p /= p.sum()
    probs = {labels[i]: float(p[i]) for i in range(len(labels))}
    detected = max(probs, key=probs.get)
    confidence = probs[detected]

    import cv2
    cap = cv2.VideoCapture(str(video_path))
    src_w, src_h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    cap.release()
    orientation = "vertical" if src_h > src_w else "horizontal"
    try:
        bm = _load_module("background_motion", HERE / "background_motion.py")
        row = {"video": video_path.stem, "class": "", "source": "", "camera_style": "", "view": "", "video_path": str(video_path),
               "start_s": "", "end_s": "", "width": src_w, "height": src_h, "aspect_ratio": ""}
        bg = bm.measure(row, {"frames": frames, "quality": quality}, {}).get("bg_lk_median")
    except Exception:
        bg = None  # la advertencia de camara simplemente no se emite; no afecta a la prediccion

    payload = {
        "modelUsed": True,
        "modelUsedForVideo": True,
        "modelSource": "gait_deep_model",
        "modelVariant": "v4exp",
        "modelVersion": VERSION,
        "experimental": True,
        "predictionBasis": "experimental_v4_temporal_cnn_pose_sequence_plus_gait_features_subject_grouped_cv",
        "video": label,
        "detectedClass": detected,
        "detectedClassLabel": CLASS_HUMAN_LABEL[detected],
        "predicted_label": f"{detected}_pattern",
        "predictionLabel": "control" if detected == "normal" else f"possible_{detected}",
        "classProbabilities": probs,
        "classProbabilitiesList": [
            {"key": k, "label": CLASS_HUMAN_LABEL[k], "shortLabel": SHORT_LABEL[k], "probability": v}
            for k, v in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "confidence": confidence,
        "predictionConfidence": confidence,
        "confidenceMeaning": "Confianza del modelo en la clase predicha; no es la probabilidad de tener una enfermedad.",
        "orientationText": (f"Clasificación experimental: el modelo asoció la marcha del video al patrón "
                            f"«{CLASS_HUMAN_LABEL[detected]}». Es una clasificación de patrones de marcha, no un diagnóstico."),
        "poseDetectionRate": round(window_pose_rate, 4),
        "framesAnalyzed": int(quality.get("processed_frames") or 0),
        "framesWithPose": int(quality.get("valid_pose_frames") or 0),
        "validSequenceFrames": int(n_valid),
        "analysisWindowSeconds": round(w_eff, 3),
        "gaitFeatures": {col: feature_row.get(col) for col in FEATURE_COLUMNS},
        "featureHighlights": gait_feature_highlights(feature_row),
        "qualityInfo": {"orientation": orientation, "sourceWidth": src_w, "sourceHeight": src_h, "sourceFps": round(src_fps, 3),
                        "backgroundMotion15fps": bg, "windowPoseRate": round(window_pose_rate, 4)},
        "warnings": build_warnings(detected, orientation, bg, window_pose_rate),
        "validationReference": {"predictedClass": OOF["per_class"][detected], "method": "validacion cruzada agrupada por sujeto (5x5)"},
        # Metricas del propio modelo (no del modelo anterior); la interfaz no las muestra.
        "modelAccuracy": OOF["accuracy"],
        "modelMacroF1": OOF["macro_f1"],
        "modelPrecision": OOF["macro_precision"],
        "modelRecall": OOF["macro_recall"],
        "modelF1Score": OOF["macro_f1"],
        "validationMethod": "StratifiedGroupKFold por sujeto, 5 folds x 5 repeticiones, epocas por validacion interna anidada; BatchNorm recalibrada con el TRAIN de cada fold (Paso 18)",
        "modelSamples": 117,
        "modelControlSamples": 58,
        "modelParkinsonSamples": 26,
        "modelTrainSize": 117,
        "modelTestSize": 117,
        "modelWarning": "Modelo experimental; dependiente de la fuente del video; sin validación clínica.",
        "notes": NO_DIAGNOSIS_NOTE,
        "disclaimer": DISCLAIMER,
        "inferenceSeconds": round(time.time() - t0, 2),
    }
    return emit(payload, out, 0)


if __name__ == "__main__":
    raise SystemExit(main())
