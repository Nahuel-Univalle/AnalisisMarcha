import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "parkinson_model.joblib"
METRICS_PATH = PROJECT_ROOT / "ml" / "models" / "parkinson_model_metrics.json"
INCOMPATIBLE_MESSAGE = (
    "El modelo de referencia usa datos de sensores de marcha. "
    "El video actual se evaluo mediante analisis visual."
)


def unavailable(message=INCOMPATIBLE_MESSAGE):
    return {
        "modelUsed": False,
        "predictionConfidence": None,
        "message": message,
    }


def read_payload():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as input_file:
            return json.load(input_file)

    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def read_metrics():
    if not METRICS_PATH.exists():
        return None
    with METRICS_PATH.open("r", encoding="utf-8") as input_file:
        return json.load(input_file)


def to_float(value):
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def main():
    metrics = read_metrics()
    feature_columns = metrics.get("feature_columns", []) if metrics else []

    if not MODEL_PATH.exists() or not feature_columns:
        print(json.dumps(unavailable("El modelo entrenado no esta disponible.")))
        return

    payload = read_payload()
    features = payload.get("features", payload)
    if not isinstance(features, dict):
        print(json.dumps(unavailable()))
        return

    values = []
    missing = []
    for column in feature_columns:
        value = to_float(features.get(column))
        if value is None:
            missing.append(column)
        values.append(0.0 if value is None else value)

    if missing:
        print(json.dumps(unavailable()))
        return

    try:
        import joblib
    except ImportError:
        print(json.dumps(unavailable("Falta joblib para ejecutar el modelo.")))
        return

    model = joblib.load(MODEL_PATH)
    probabilities = model.predict_proba([values])[0]
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
                "predictionLabel": prediction_label,
                "predictionConfidence": max(control_probability, parkinson_probability),
                "classProbabilities": {
                    "control": control_probability,
                    "parkinson": parkinson_probability,
                },
            }
        )
    )


if __name__ == "__main__":
    main()
