from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from video_training_common import (
    FEATURE_COLUMNS,
    METRICS_PATH,
    MODEL_PATH,
    NO_DIAGNOSIS_NOTE,
    PREDICTIONS_DIR,
    SCALER_PATH,
    SCHEMA_PATH,
    extract_video_features,
    parse_subject_and_sequence,
    project_relative,
    read_json,
    safe_stem,
    write_json,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predice patron Parkinson vs Normal para un video individual."
    )
    parser.add_argument("--video", required=True)
    parser.add_argument("--output-json", default="")
    parser.add_argument("--frame-step", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def unavailable(video: str, message: str) -> dict[str, Any]:
    return {
        "video": video,
        "modelSource": "fallback_gait_rules",
        "modelUsed": False,
        "modelUsedForVideo": False,
        "predictionConfidence": None,
        "message": message,
        "notes": NO_DIAGNOSIS_NOTE,
    }


def risk_level(probability_parkinson: float) -> str:
    if probability_parkinson < 0.40:
        return "bajo"
    if probability_parkinson <= 0.70:
        return "medio"
    return "alto"


def output_path_for(video_path: Path, explicit: str) -> Path:
    if explicit:
        return Path(explicit)
    return PREDICTIONS_DIR / f"{safe_stem(video_path.stem)}_prediction.json"


def vector_from_features(feature_row: dict[str, Any], schema: dict[str, Any]) -> list[float]:
    columns = schema.get("feature_columns") or FEATURE_COLUMNS
    medians = schema.get("imputer_statistics") or {}
    values = []
    for column in columns:
        raw_value = feature_row.get(column)
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = float(medians.get(column, 0.0))
        if not np.isfinite(value):
            value = float(medians.get(column, 0.0))
        values.append(value)
    return values


def main() -> int:
    args = parse_args()
    video_path = Path(args.video)
    if not video_path.is_absolute():
        video_path = Path.cwd() / video_path

    output_json = output_path_for(video_path, args.output_json)
    if not MODEL_PATH.exists() or not SCALER_PATH.exists() or not SCHEMA_PATH.exists():
        payload = unavailable(
            project_relative(video_path),
            "No existe modelo entrenado en models/video_parkinson/.",
        )
        write_json(output_json, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 1

    subject_id, sequence, _, _ = parse_subject_and_sequence(video_path.name, "unknown")
    metadata = {
        "video_path": str(video_path),
        "filename": video_path.name,
        "subject_id": subject_id,
        "condition": "unknown",
        "label": "",
        "severity": "unknown",
        "sequence": sequence,
    }
    result = extract_video_features(
        metadata,
        frame_step=args.frame_step,
        force=args.force,
        save_landmarks=True,
    )
    if result.error_row:
        payload = unavailable(project_relative(video_path), str(result.error_row.get("error")))
        write_json(output_json, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 1

    # Gate de calidad: sin suficiente pose no se emite prediccion (evita
    # predecir sobre el vector mediano imputado y devolver falsa confianza).
    try:
        pose_rate = float(result.feature_row.get("pose_detection_rate"))
    except (TypeError, ValueError):
        pose_rate = 0.0
    valid_frames = int(float(result.feature_row.get("valid_pose_frames") or 0))
    if pose_rate < 0.45 or valid_frames < 15:
        payload = unavailable(
            project_relative(video_path),
            f"Calidad de pose insuficiente (deteccion {pose_rate:.0%}, {valid_frames} frames validos).",
        )
        write_json(output_json, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 1

    schema = read_json(SCHEMA_PATH) or {}
    metrics = read_json(METRICS_PATH) or {}
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    vector = np.array([vector_from_features(result.feature_row, schema)], dtype=float)
    scaled = scaler.transform(vector)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(scaled)[0]
        classes = list(model.classes_)
        probability_by_class = {
            int(label): float(probabilities[index]) for index, label in enumerate(classes)
        }
        probability_normal = probability_by_class.get(0, 0.0)
        probability_parkinson = probability_by_class.get(1, 0.0)
    else:
        predicted = int(model.predict(scaled)[0])
        probability_parkinson = 1.0 if predicted == 1 else 0.0
        probability_normal = 1.0 - probability_parkinson

    predicted_label = (
        "parkinson_pattern" if probability_parkinson > probability_normal else "normal_pattern"
    )
    route_prediction_label = (
        "possible_parkinson" if probability_parkinson > probability_normal else "control"
    )
    confidence = max(probability_normal, probability_parkinson)
    payload = {
        "video": project_relative(video_path),
        "modelSource": "video_parkinson_model",
        "predicted_label": predicted_label,
        "predictionLabel": route_prediction_label,
        "probability_parkinson": probability_parkinson,
        "probability_normal": probability_normal,
        "risk_level": risk_level(probability_parkinson),
        "confidence": confidence,
        "predictionConfidence": confidence,
        "classProbabilities": {
            "control": probability_normal,
            "parkinson": probability_parkinson,
        },
        "modelUsed": True,
        "modelUsedForVideo": True,
        "predictionBasis": "video_landmarks_model_subject_group_validation",
        "featureColumns": schema.get("feature_columns") or FEATURE_COLUMNS,
        "poseDetectionRate": result.feature_row.get("pose_detection_rate"),
        "modelAccuracy": metrics.get("accuracy"),
        "modelPrecision": metrics.get("precision"),
        "modelRecall": metrics.get("recall"),
        "modelF1Score": metrics.get("f1_score"),
        "validationMethod": metrics.get("validation_method"),
        "modelSamples": metrics.get("samples"),
        "modelControlSamples": metrics.get("control_samples"),
        "modelParkinsonSamples": metrics.get("parkinson_samples"),
        "notes": "Patrones de marcha compatibles con alteraciones motoras. No representa diagnostico medico definitivo.",
    }
    write_json(output_json, payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
