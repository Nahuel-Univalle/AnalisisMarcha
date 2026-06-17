import json
import sys
from pathlib import Path

from build_video_feature_vector import build_video_feature_vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "parkinson_video_compatible_model.joblib"
METRICS_PATH = PROJECT_ROOT / "ml" / "models" / "parkinson_video_compatible_metrics.json"
FEATURES_PATH = PROJECT_ROOT / "ml" / "models" / "parkinson_model_features.json"
INSUFFICIENT_MESSAGE = (
    "No se pudieron extraer suficientes métricas visuales compatibles para aplicar el modelo."
)


def unavailable(message=INSUFFICIENT_MESSAGE):
    return {
        "modelUsed": False,
        "modelUsedForVideo": False,
        "predictionConfidence": None,
        "message": message,
    }


def read_payload():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as input_file:
            return json.load(input_file)

    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {}


def read_json(path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as input_file:
        return json.load(input_file)


def main():
    if not MODEL_PATH.exists() or not FEATURES_PATH.exists():
        print(json.dumps(unavailable("El modelo compatible con video no está disponible."), ensure_ascii=False))
        return

    metadata = read_json(FEATURES_PATH) or {}
    metrics = read_json(METRICS_PATH) or {}
    feature_columns = metadata.get("feature_columns") or []
    payload = read_payload()
    vector_payload = build_video_feature_vector(payload, feature_columns)

    if not vector_payload["modelUsable"]:
        print(json.dumps(unavailable(vector_payload["message"]), ensure_ascii=False))
        return

    try:
        import joblib
    except ImportError:
        print(json.dumps(unavailable("Falta joblib para ejecutar el modelo."), ensure_ascii=False))
        return

    model = joblib.load(MODEL_PATH)
    probabilities = model.predict_proba([vector_payload["featureVector"]])[0]
    classes = list(model.classes_)
    probability_by_class = {
        int(label): float(probabilities[index]) for index, label in enumerate(classes)
    }
    control_probability = probability_by_class.get(0, 0.0)
    parkinson_probability = probability_by_class.get(1, 0.0)
    prediction_label = (
        "possible_parkinson" if parkinson_probability >= control_probability else "control"
    )

    print(
        json.dumps(
            {
                "modelUsed": True,
                "modelUsedForVideo": True,
                "predictionLabel": prediction_label,
                "predictionConfidence": max(control_probability, parkinson_probability),
                "classProbabilities": {
                    "control": control_probability,
                    "parkinson": parkinson_probability,
                },
                "predictionBasis": "video_features_mapped_to_reference_model",
                "featureColumns": feature_columns,
                "usedFeatureSources": vector_payload["usedFeatureSources"],
                "modelAccuracy": metrics.get("accuracy"),
                "modelPrecision": metrics.get("precision"),
                "modelRecall": metrics.get("recall"),
                "modelF1Score": metrics.get("f1_score"),
                "modelWarning": metrics.get("warning"),
                "validationMethod": metrics.get("validation_method"),
                "modelSamples": metrics.get("samples"),
                "modelControlSamples": metrics.get("control_samples"),
                "modelParkinsonSamples": metrics.get("parkinson_samples"),
                "modelTrainSize": metrics.get("train_size"),
                "modelTestSize": metrics.get("test_size"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
