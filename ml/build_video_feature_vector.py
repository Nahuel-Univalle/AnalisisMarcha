import argparse
import json
import sys
from pathlib import Path

from video_feature_mapping import (
    MIN_REQUIRED_VIDEO_FEATURES,
    VIDEO_COMPATIBLE_FEATURE_COLUMNS,
    VIDEO_FEATURE_MAPPING,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = PROJECT_ROOT / "ml" / "models" / "parkinson_model_features.json"


def to_float(value):
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def read_payload(path=None):
    if path:
        with Path(path).open("r", encoding="utf-8") as input_file:
            return json.load(input_file)

    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {}


def read_feature_columns():
    if FEATURES_PATH.exists():
        with FEATURES_PATH.open("r", encoding="utf-8") as input_file:
            metadata = json.load(input_file)
        columns = metadata.get("feature_columns")
        if isinstance(columns, list) and columns:
            return columns

    return VIDEO_COMPATIBLE_FEATURE_COLUMNS


def value_for_column(payload, column):
    mapping = VIDEO_FEATURE_MAPPING[column]
    for key in [mapping["video_key"], *mapping.get("fallback_keys", [])]:
        value = to_float(payload.get(key))
        if value is not None:
            return value, key
    return None, None


def build_video_feature_vector(payload, feature_columns=None):
    columns = feature_columns or read_feature_columns()
    values = []
    used = {}
    missing = []

    for column in columns:
        if column not in VIDEO_FEATURE_MAPPING:
            missing.append(column)
            continue

        value, source_key = value_for_column(payload, column)
        if value is None:
            missing.append(column)
            values.append(None)
            continue

        values.append(value)
        used[column] = source_key

    model_usable = len(used) >= MIN_REQUIRED_VIDEO_FEATURES and len(missing) == 0

    return {
        "modelUsable": model_usable,
        "featureColumns": columns,
        "featureVector": values if model_usable else None,
        "features": dict(zip(columns, values)),
        "usedFeatureSources": used,
        "missingFeatures": missing,
        "minimumRequiredFeatures": MIN_REQUIRED_VIDEO_FEATURES,
        "message": None
        if model_usable
        else "No se pudieron extraer suficientes métricas visuales compatibles para aplicar el modelo.",
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Construye vector compatible desde JSON visual.")
    parser.add_argument("input_json", nargs="?", help="Archivo JSON de análisis visual.")
    return parser.parse_args()


def main():
    args = parse_args()
    payload = read_payload(args.input_json)
    print(json.dumps(build_video_feature_vector(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
