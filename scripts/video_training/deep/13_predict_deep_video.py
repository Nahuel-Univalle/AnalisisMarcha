"""
Paso 13 - Inferencia con el modelo Deep Learning sobre un video nuevo.

El video pasa por EXACTAMENTE el mismo pipeline que en entrenamiento:

    video -> pose (MediaPipe) -> landmarks -> normalizacion
          -> secuencia temporal fija (+ velocidades)  [rama CNN]
          -> 36 features de marcha                     [rama features]
          -> modelo -> softmax (4 clases)

Salida JSON (stdout y --output-json): clase/patron detectado, probabilidad por
clase, confianza, caracteristicas observadas, nivel de alerta y advertencia de
no diagnostico.

Uso:
  .venv311\\Scripts\\python.exe scripts\\video_training\\deep\\13_predict_deep_video.py --video <ruta> [--output-json <ruta>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# La ruta de Next.js lee stdout como UTF-8; forzarlo evita mojibake en Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_HUMAN_LABEL,
    CLASS_NAMES,
    FEATURE_SCALER_PATH,
    FRAME_STEP,
    MODEL_CONFIG_PATH,
    MODEL_WEIGHTS_PATH,
    CV_METRICS_PATH,
    NO_DIAGNOSIS_NOTE,
    FeatureScaler,
    build_model,
    extract_feature_vector,
    gait_feature_highlights,
    read_json,
    sequence_from_landmark_csv,
)
from video_training_common import (  # noqa: E402
    extract_video_features,
    landmark_output_path,
    parse_subject_and_sequence,
    project_relative,
)

DISCLAIMER = (
    "Este analisis constituye una orientacion basada en patrones de movimiento y "
    "no representa un diagnostico medico."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inferencia Deep Learning de marcha (4 clases).")
    parser.add_argument("--video", required=True)
    parser.add_argument("--output-json", default="")
    parser.add_argument("--frame-step", type=int, default=FRAME_STEP)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def unavailable(video: str, message: str) -> dict:
    return {
        "modelUsed": False,
        "modelUsedForVideo": False,
        "modelSource": "gait_deep_model",
        "predictionConfidence": None,
        "message": message,
        "notes": NO_DIAGNOSIS_NOTE,
        "disclaimer": DISCLAIMER,
        "video": video,
    }


def risk_level(altered_probability: float, detected_class: str) -> str:
    if detected_class == "normal":
        return "bajo"
    if altered_probability < 0.40:
        return "bajo"
    if altered_probability <= 0.70:
        return "medio"
    return "alto"


def orientation_text(detected_class: str) -> str:
    if detected_class == "normal":
        return (
            "El analisis identifico patrones de marcha dentro de lo esperado para una "
            "marcha normal. No se identificaron señales claras de alteracion."
        )
    nombre = {
        "parkinson": "una alteracion asociada a Parkinson",
        "esclerosis_multiple": "una alteracion asociada a Esclerosis Multiple",
        "riesgo_caida": "inestabilidad de la marcha / riesgo de caida",
    }[detected_class]
    return f"El analisis identifico patrones de marcha compatibles con {nombre}."


def main() -> int:
    args = parse_args()
    video_path = Path(args.video)
    if not video_path.is_absolute():
        video_path = Path.cwd() / video_path
    video_label = project_relative(video_path)

    output_json = Path(args.output_json) if args.output_json else None

    def emit(payload: dict, code: int) -> int:
        text = json.dumps(payload, ensure_ascii=False)
        if output_json:
            output_json.parent.mkdir(parents=True, exist_ok=True)
            output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(text)
        return code

    if not (MODEL_WEIGHTS_PATH.exists() and MODEL_CONFIG_PATH.exists() and FEATURE_SCALER_PATH.exists()):
        return emit(unavailable(video_label, "No existe modelo Deep Learning entrenado en models/gait_deep/."), 1)

    if not video_path.exists():
        return emit(unavailable(video_label, f"No se encontro el video: {video_label}"), 1)

    subject_id, sequence_no, _documented, _warning = parse_subject_and_sequence(video_path.name, "unknown")
    metadata = {
        "video_path": str(video_path),
        "filename": video_path.name,
        "subject_id": subject_id,
        "subject_documented": False,
        "condition": "unknown",
        "label": "",
        "severity": "unknown",
        "sequence": sequence_no,
    }

    result = extract_video_features(metadata, frame_step=args.frame_step, force=args.force, save_landmarks=True)
    if result.error_row:
        return emit(unavailable(video_label, str(result.error_row.get("error") or "No se pudo procesar el video.")), 1)

    landmark_csv = landmark_output_path(metadata)
    seq, pose_rate, n_valid = sequence_from_landmark_csv(landmark_csv)
    if seq is None:
        return emit(
            unavailable(
                video_label,
                f"Calidad de pose insuficiente para el modelo de secuencias (frames validos: {n_valid}). "
                "Suba un video con cuerpo completo, buena iluminacion y camara estable.",
            ),
            1,
        )

    feature_row = result.feature_row
    feat_vector = extract_feature_vector(feature_row)
    scaler = FeatureScaler.from_json(read_json(FEATURE_SCALER_PATH))
    feat_scaled = scaler.transform(feat_vector.reshape(1, -1))

    import torch
    from torch.nn.functional import softmax

    config = read_json(MODEL_CONFIG_PATH)
    temperature = float(config.get("temperature", 1.0) or 1.0)
    model, _cfg = build_model(config)
    model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location="cpu"))
    model.eval()

    with torch.no_grad():
        seq_t = torch.from_numpy(seq[None, ...]).float()
        feat_t = torch.from_numpy(feat_scaled).float()
        logits = model(seq_t, feat_t) / temperature
        probs = softmax(logits, dim=-1).cpu().numpy()[0]

    probs = {name: float(probs[i]) for i, name in enumerate(CLASS_NAMES)}
    detected_class = max(probs, key=probs.get)
    confidence = probs[detected_class]
    altered_probability = float(1.0 - probs["normal"])
    level = risk_level(altered_probability, detected_class)

    prob_normal = probs["normal"]
    prob_parkinson = probs["parkinson"]

    metrics = read_json(CV_METRICS_PATH) if CV_METRICS_PATH.exists() else {}
    oof = metrics.get("oof", {})

    payload = {
        "modelUsed": True,
        "modelUsedForVideo": True,
        "modelSource": "gait_deep_model",
        "modelVersion": config.get("model_version"),
        "predictionBasis": "deep_temporal_cnn_pose_sequence_plus_gait_features_stratified_group_kfold",
        "video": video_label,

        "detectedClass": detected_class,
        "detectedClassLabel": CLASS_HUMAN_LABEL[detected_class],
        "predicted_label": f"{detected_class}_pattern",
        "predictionLabel": "control" if detected_class == "normal" else f"possible_{detected_class}",

        "classProbabilities": probs,
        "classProbabilitiesList": [
            {"key": k, "label": CLASS_HUMAN_LABEL[k], "probability": v}
            for k, v in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "confidence": confidence,
        "predictionConfidence": confidence,
        "alteredProbability": altered_probability,

        # compatibilidad hacia atras con el pipeline binario Parkinson:
        "probability_parkinson": prob_parkinson,
        "probability_normal": prob_normal,
        "probabilityParkinson": prob_parkinson,
        "probabilityNormal": prob_normal,

        "riskLevel": level,
        "risk_level": level,

        "poseDetectionRate": round(float(pose_rate), 4),
        "framesAnalyzed": int(result.quality_row.get("processed_frames") or 0),
        "framesWithPose": int(result.quality_row.get("valid_pose_frames") or 0),
        "validSequenceFrames": int(n_valid),

        "gaitFeatures": {col: feature_row.get(col) for col in scaler.columns},
        "featureHighlights": gait_feature_highlights(feature_row),

        "modelAccuracy": metrics.get("accuracy"),
        "modelMacroF1": metrics.get("macro_f1"),
        "modelBalancedAccuracy": metrics.get("balanced_accuracy"),
        "modelPrecision": metrics.get("precision"),
        "modelRecall": metrics.get("recall"),
        "modelF1Score": metrics.get("f1_score"),
        "validationMethod": metrics.get("validation_method"),
        "modelSamples": metrics.get("samples"),
        "classSampleCounts": metrics.get("videos_per_class"),
        "perClassMetrics": oof.get("per_class"),
        "confusionMatrix": metrics.get("confusion_matrix"),

        "orientationText": orientation_text(detected_class),
        "notes": NO_DIAGNOSIS_NOTE,
        "disclaimer": DISCLAIMER,
    }
    return emit(payload, 0)


if __name__ == "__main__":
    raise SystemExit(main())
