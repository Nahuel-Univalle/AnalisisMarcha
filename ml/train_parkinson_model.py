import csv
import json
import sys
from collections import Counter
from pathlib import Path

from video_feature_mapping import VIDEO_COMPATIBLE_FEATURE_COLUMNS, VIDEO_FEATURE_MAPPING


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING_PATH = PROJECT_ROOT / "ml" / "data" / "training_features.csv"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_PATH = MODEL_DIR / "parkinson_model.joblib"
METRICS_PATH = MODEL_DIR / "parkinson_model_metrics.json"
VIDEO_MODEL_PATH = MODEL_DIR / "parkinson_video_compatible_model.joblib"
VIDEO_METRICS_PATH = MODEL_DIR / "parkinson_video_compatible_metrics.json"
VIDEO_FEATURES_PATH = MODEL_DIR / "parkinson_model_features.json"

FEATURE_COLUMNS = [
    "recorded_speed_m_per_s",
    "mean_left_total",
    "std_left_total",
    "mean_right_total",
    "std_right_total",
    "mean_total_force",
    "mean_force_asymmetry_abs",
    "mean_force_asymmetry_index",
    "left_contact_ratio",
    "right_contact_ratio",
    "double_support_ratio",
    "left_step_events",
    "right_step_events",
    "estimated_cadence_steps_per_min",
    "mean_left_stance_time_sec",
    "mean_right_stance_time_sec",
    "mean_left_swing_time_sec",
    "mean_right_swing_time_sec",
    "std_left_cop_x",
    "std_left_cop_y",
    "std_right_cop_x",
    "std_right_cop_y",
]

OVERFIT_WARNING = (
    "Las metricas alcanzaron 100%. Esto puede deberse al tamano reducido del "
    "conjunto de prueba, separacion insuficiente o sobreajuste. Requiere "
    "validacion adicional."
)
BASE_WARNING = "Modelo inicial. Requiere validacion adicional."


def load_rows():
    if not TRAINING_PATH.exists():
        print(
            "No existe ml/data/training_features.csv. Ejecute primero ml/prepare_training_dataset.py.",
            file=sys.stderr,
        )
        sys.exit(1)

    with TRAINING_PATH.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def to_float(value):
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def try_import_ml():
    try:
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import (
            accuracy_score,
            confusion_matrix,
            precision_recall_fscore_support,
        )
        from sklearn.model_selection import GroupShuffleSplit
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        return {
            "joblib": joblib,
            "RandomForestClassifier": RandomForestClassifier,
            "SimpleImputer": SimpleImputer,
            "accuracy_score": accuracy_score,
            "confusion_matrix": confusion_matrix,
            "precision_recall_fscore_support": precision_recall_fscore_support,
            "GroupShuffleSplit": GroupShuffleSplit,
            "Pipeline": Pipeline,
            "StandardScaler": StandardScaler,
        }
    except ImportError:
        print(
            "Faltan dependencias para entrenar el modelo inicial. Instale scikit-learn y joblib.",
            file=sys.stderr,
        )
        sys.exit(1)


def group_column_for(rows):
    subject_groups = [row.get("subject_id") or "" for row in rows]
    if len(set(subject_groups)) > 1 and all(subject_groups):
        return "subject_id"
    return "source_file"


def has_both_classes(labels):
    return len(set(labels)) == 2


def find_group_split(ml, features, labels, groups):
    splitter = ml["GroupShuffleSplit"](n_splits=80, test_size=0.25, random_state=42)
    best_split = None

    for train_index, test_index in splitter.split(features, labels, groups):
        y_train = [labels[index] for index in train_index]
        y_test = [labels[index] for index in test_index]
        if has_both_classes(y_train) and has_both_classes(y_test):
            return list(train_index), list(test_index)
        best_split = (list(train_index), list(test_index))

    if best_split is None:
        print("No se pudo crear una division por grupos para entrenamiento.", file=sys.stderr)
        sys.exit(1)

    train_index, test_index = best_split
    print(
        "Advertencia: la division por grupos no dejo ambas clases en train y test. "
        "Revise el tamano y distribucion del dataset.",
        file=sys.stderr,
    )
    return train_index, test_index


def subset(values, indexes):
    return [values[index] for index in indexes]


def class_count(labels, target):
    return Counter(labels).get(target, 0)


def train_model(ml, rows, labels, feature_columns, model_path, metrics_path):
    features = [[to_float(row[column]) for column in feature_columns] for row in rows]
    group_column = group_column_for(rows)
    groups = [row.get(group_column) or row.get("source_file") or "" for row in rows]
    train_index, test_index = find_group_split(ml, features, labels, groups)

    train_groups = {groups[index] for index in train_index}
    test_groups = {groups[index] for index in test_index}
    overlap = sorted(train_groups.intersection(test_groups))
    if overlap:
        print(
            f"Fuga de datos detectada: grupos presentes en train y test: {', '.join(overlap[:5])}",
            file=sys.stderr,
        )
        sys.exit(1)

    x_train = subset(features, train_index)
    x_test = subset(features, test_index)
    y_train = subset(labels, train_index)
    y_test = subset(labels, test_index)

    model = ml["Pipeline"](
        steps=[
            ("imputer", ml["SimpleImputer"](strategy="median")),
            ("scaler", ml["StandardScaler"]()),
            (
                "classifier",
                ml["RandomForestClassifier"](
                    n_estimators=200,
                    max_depth=6,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    precision, recall, f1_score, _ = ml["precision_recall_fscore_support"](
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )
    accuracy = ml["accuracy_score"](y_test, predictions)
    perfect_metric = any(
        float(value) >= 0.999999 for value in [accuracy, precision, recall, f1_score]
    )
    warning = OVERFIT_WARNING if perfect_metric else BASE_WARNING

    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1_score),
        "confusion_matrix": ml["confusion_matrix"](y_test, predictions, labels=[0, 1]).tolist(),
        "samples": len(rows),
        "control_samples": class_count(labels, 0),
        "parkinson_samples": class_count(labels, 1),
        "validation_method": f"group_split_by_{group_column}",
        "group_column": group_column,
        "train_size": len(train_index),
        "test_size": len(test_index),
        "control_train": class_count(y_train, 0),
        "parkinson_train": class_count(y_train, 1),
        "control_test": class_count(y_test, 0),
        "parkinson_test": class_count(y_test, 1),
        "feature_columns": feature_columns,
        "warning": warning,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ml["joblib"].dump(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Modelo guardado: {model_path}")
    print(f"Metricas guardadas: {metrics_path}")
    print(f"Metodo de validacion: {metrics['validation_method']}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1-score: {metrics['f1_score']:.4f}")
    print(warning)
    return metrics


def write_video_feature_metadata(metrics):
    payload = {
        "model": "parkinson_video_compatible_model.joblib",
        "metrics": "parkinson_video_compatible_metrics.json",
        "feature_columns": VIDEO_COMPATIBLE_FEATURE_COLUMNS,
        "minimum_required_features": len(VIDEO_COMPATIBLE_FEATURE_COLUMNS),
        "mapping": VIDEO_FEATURE_MAPPING,
        "validation_method": metrics.get("validation_method"),
        "warning": (
            "Modelo compatible con video basado en proxies visuales. "
            "Resultado orientativo; no constituye diagnostico medico."
        ),
    }
    VIDEO_FEATURES_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Features compatibles guardadas: {VIDEO_FEATURES_PATH}")


def main():
    rows = load_rows()
    labels = [int(float(row["parkinson_binary"])) for row in rows]
    classes = sorted(set(labels))

    if len(classes) < 2:
        print(
            "No se puede entrenar un modelo Parkinson porque solo existe una clase. "
            "Agregue datos control y Parkinson con parkinson_binary valido."
        )
        return

    ml = try_import_ml()
    print("Entrenando modelo de referencia completo...")
    train_model(ml, rows, labels, FEATURE_COLUMNS, MODEL_PATH, METRICS_PATH)
    print("Entrenando modelo compatible con metricas visuales de video...")
    compatible_metrics = train_model(
        ml,
        rows,
        labels,
        VIDEO_COMPATIBLE_FEATURE_COLUMNS,
        VIDEO_MODEL_PATH,
        VIDEO_METRICS_PATH,
    )
    write_video_feature_metadata(compatible_metrics)


if __name__ == "__main__":
    main()
