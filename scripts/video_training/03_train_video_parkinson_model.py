from __future__ import annotations

import argparse
import json
from statistics import mean, pstdev
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from video_training_common import (
    FEATURE_COLUMNS,
    FEATURES_CSV_PATH,
    METRICS_PATH,
    MODEL_PATH,
    MODELS_DIR,
    NO_DIAGNOSIS_NOTE,
    SCALER_PATH,
    SCHEMA_PATH,
    SPLITS_DIR,
    TRAINING_REPORT_PATH,
    now_iso,
    write_json,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Entrena modelo real Parkinson vs Normal desde features de video."
    )
    parser.add_argument("--features", default=str(FEATURES_CSV_PATH))
    parser.add_argument("--min-pose-rate", type=float, default=0.50)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if np.isfinite(parsed) else None


def subject_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for subject_id, group in df.groupby("subject_id"):
        labels = group["label"].astype(int).tolist()
        label = int(round(sum(labels) / len(labels)))
        rows.append({"subject_id": subject_id, "label": label})
    return pd.DataFrame(rows)


def stratified_subject_splits(subjects: pd.DataFrame, random_state: int):
    if subjects.empty:
        return set(), set(), set()

    labels = subjects["label"].astype(int).to_numpy()
    can_stratify = len(set(labels)) == 2 and min(np.bincount(labels)) >= 3
    indices = np.arange(len(subjects))

    if can_stratify:
        first_split = StratifiedShuffleSplit(
            n_splits=1,
            test_size=0.30,
            random_state=random_state,
        )
        train_idx, temp_idx = next(first_split.split(indices, labels))
        temp_labels = labels[temp_idx]
        if len(set(temp_labels)) == 2 and min(np.bincount(temp_labels)) >= 2:
            second_split = StratifiedShuffleSplit(
                n_splits=1,
                test_size=0.50,
                random_state=random_state,
            )
            val_rel, test_rel = next(second_split.split(temp_idx, temp_labels))
            val_idx = temp_idx[val_rel]
            test_idx = temp_idx[test_rel]
        else:
            midpoint = max(1, len(temp_idx) // 2)
            val_idx = temp_idx[:midpoint]
            test_idx = temp_idx[midpoint:]
    else:
        rng = np.random.default_rng(random_state)
        shuffled = indices.copy()
        rng.shuffle(shuffled)
        train_end = max(1, int(round(len(shuffled) * 0.70)))
        val_end = max(train_end + 1, int(round(len(shuffled) * 0.85))) if len(shuffled) > 2 else train_end
        train_idx = shuffled[:train_end]
        val_idx = shuffled[train_end:val_end]
        test_idx = shuffled[val_end:]

    train = set(subjects.iloc[train_idx]["subject_id"])
    val = set(subjects.iloc[val_idx]["subject_id"])
    test = set(subjects.iloc[test_idx]["subject_id"])
    return train, val, test


def write_split_files(train: set[str], val: set[str], test: set[str]) -> None:
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    for name, values in [
        ("train_subjects.txt", train),
        ("val_subjects.txt", val),
        ("test_subjects.txt", test),
    ]:
        (SPLITS_DIR / name).write_text("\n".join(sorted(values)) + ("\n" if values else ""), encoding="utf-8")


def model_candidates(random_state: int):
    return {
        "LogisticRegression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=random_state,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(random_state=random_state),
        "SVM_RBF": SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=random_state,
        ),
    }


def evaluate_predictions(y_true, y_pred, y_score=None) -> dict[str, Any]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["normal", "parkinson"],
            zero_division=0,
            output_dict=True,
        ),
    }
    if y_score is not None and len(set(y_true)) == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
    else:
        metrics["roc_auc"] = None
    return metrics


def fold_fit_predict(estimator, x_train, y_train, x_test):
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_train_i = imputer.fit_transform(x_train)
    x_test_i = imputer.transform(x_test)
    x_train_s = scaler.fit_transform(x_train_i)
    x_test_s = scaler.transform(x_test_i)
    estimator.fit(x_train_s, y_train)
    pred = estimator.predict(x_test_s)
    score = estimator.predict_proba(x_test_s)[:, list(estimator.classes_).index(1)] if hasattr(estimator, "predict_proba") and 1 in list(estimator.classes_) else None
    return pred, score


def cross_validate_models(df: pd.DataFrame, feature_columns: list[str], random_state: int):
    x = df[feature_columns].apply(pd.to_numeric, errors="coerce").to_numpy()
    y = df["label"].astype(int).to_numpy()
    groups = df["subject_id"].astype(str).to_numpy()
    unique_groups = np.unique(groups)
    n_splits = min(5, len(unique_groups))
    if n_splits < 2 or len(set(y)) < 2:
        raise ValueError("Se necesitan al menos 2 sujetos y ambas clases para validar por grupos.")

    results: dict[str, Any] = {}
    splitter = GroupKFold(n_splits=n_splits)

    for model_name, estimator in model_candidates(random_state).items():
        fold_metrics = []
        for fold_index, (train_idx, test_idx) in enumerate(splitter.split(x, y, groups), start=1):
            y_train = y[train_idx]
            y_test = y[test_idx]
            if len(set(y_train)) < 2:
                continue
            pred, score = fold_fit_predict(estimator, x[train_idx], y_train, x[test_idx])
            metrics = evaluate_predictions(y_test, pred, score)
            metrics["fold"] = fold_index
            metrics["test_subjects"] = sorted(set(groups[test_idx]))
            fold_metrics.append(metrics)

        if not fold_metrics:
            continue

        recalls = [item["recall"] for item in fold_metrics]
        f1s = [item["f1_score"] for item in fold_metrics]
        results[model_name] = {
            "folds": fold_metrics,
            "mean_accuracy": mean(item["accuracy"] for item in fold_metrics),
            "mean_precision": mean(item["precision"] for item in fold_metrics),
            "mean_recall": mean(recalls),
            "mean_f1_score": mean(f1s),
            "std_f1_score": pstdev(f1s) if len(f1s) > 1 else 0.0,
            "mean_roc_auc": mean(
                item["roc_auc"] for item in fold_metrics if item["roc_auc"] is not None
            )
            if any(item["roc_auc"] is not None for item in fold_metrics)
            else None,
        }

    if not results:
        raise ValueError("No se pudo entrenar ningun modelo con validacion por grupos.")
    return results


def select_best_model(cv_results: dict[str, Any]) -> str:
    ranked = sorted(
        cv_results.items(),
        key=lambda item: (
            item[1]["mean_recall"],
            item[1]["mean_f1_score"],
            -item[1]["std_f1_score"],
        ),
        reverse=True,
    )
    return ranked[0][0]


def fit_final_model(df: pd.DataFrame, feature_columns: list[str], model_name: str, random_state: int):
    x = df[feature_columns].apply(pd.to_numeric, errors="coerce").to_numpy()
    y = df["label"].astype(int).to_numpy()
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    estimator = model_candidates(random_state)[model_name]
    x_i = imputer.fit_transform(x)
    x_s = scaler.fit_transform(x_i)
    estimator.fit(x_s, y)
    imputer_stats = {
        column: float(value) if np.isfinite(value) else 0.0
        for column, value in zip(feature_columns, imputer.statistics_)
    }
    return estimator, scaler, imputer_stats


def write_training_report(payload: dict[str, Any]) -> None:
    metrics = payload["metrics"]["cross_validation"][payload["model_selected"]]
    lines = [
        "# Entrenamiento de modelo por video",
        "",
        NO_DIAGNOSIS_NOTE.replace("diagnostico medico", "diagnóstico médico").replace("tecnologico", "tecnológico"),
        "",
        "## Dataset",
        f"- Videos totales usados: {payload['total_videos']}",
        f"- Sujetos totales: {payload['total_subjects']}",
        f"- Videos normales: {payload['total_normal_videos']}",
        f"- Videos Parkinson: {payload['total_parkinson_videos']}",
        f"- Sujetos normales: {payload['total_normal_subjects']}",
        f"- Sujetos Parkinson: {payload['total_parkinson_subjects']}",
        "",
        "## Extraccion",
        "- Landmarks extraidos con MediaPipe Pose.",
        "- Distancias y movimientos normalizados por escala corporal estimada.",
        "",
        "## Validacion",
        f"- Metodo: {payload['validation_method']}",
        "- La division se realiza por subject_id para evitar fuga de datos.",
        "",
        "## Modelo seleccionado",
        f"- {payload['model_selected']}",
        f"- Recall Parkinson promedio: {metrics['mean_recall']:.4f}",
        f"- F1 promedio: {metrics['mean_f1_score']:.4f}",
        f"- Accuracy promedio: {metrics['mean_accuracy']:.4f}",
        f"- ROC AUC promedio: {metrics['mean_roc_auc']}",
        "",
        "## Limitaciones",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.extend(
        [
            "",
            "## Recomendacion de uso",
            "Usar como apoyo tecnologico y no como diagnostico medico definitivo. "
            "Los resultados deben revisarse junto con evaluacion clinica profesional.",
            "",
            "## Features usadas",
        ]
    )
    lines.extend(f"- {item}" for item in payload["features_used"])
    TRAINING_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    features_path = FEATURES_CSV_PATH if args.features == str(FEATURES_CSV_PATH) else args.features
    df = pd.read_csv(features_path)
    if df.empty:
        print("No hay features reales para entrenar. Ejecute primero 01 y 02 con videos reales.")
        return 1

    for column in ["label", "pose_detection_rate"]:
        if column not in df.columns:
            print(f"Falta columna requerida: {column}")
            return 1

    valid_df = df[
        (pd.to_numeric(df["pose_detection_rate"], errors="coerce") >= args.min_pose_rate)
        & (df.get("error", "").fillna("") == "")
    ].copy()
    valid_df = valid_df.dropna(subset=["subject_id", "label"])
    valid_df["label"] = valid_df["label"].astype(int)

    if valid_df.empty or valid_df["label"].nunique() < 2:
        print("No hay suficientes videos validos de ambas clases para entrenar un modelo real.")
        return 1

    feature_columns = [column for column in FEATURE_COLUMNS if column in valid_df.columns]
    if not feature_columns:
        print("No hay columnas numericas de marcha para entrenar.")
        return 1

    subjects = subject_table(valid_df)
    train_subjects, val_subjects, test_subjects = stratified_subject_splits(subjects, args.random_state)
    write_split_files(train_subjects, val_subjects, test_subjects)

    cv_results = cross_validate_models(valid_df, feature_columns, args.random_state)
    best_model = select_best_model(cv_results)
    estimator, scaler, imputer_stats = fit_final_model(
        valid_df,
        feature_columns,
        best_model,
        args.random_state,
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(estimator, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    labels_by_subject = subjects.set_index("subject_id")["label"].to_dict()
    payload = {
        "training_date": now_iso(),
        "total_videos": int(len(valid_df)),
        "total_subjects": int(valid_df["subject_id"].nunique()),
        "total_normal_videos": int((valid_df["label"] == 0).sum()),
        "total_parkinson_videos": int((valid_df["label"] == 1).sum()),
        "total_normal_subjects": int(sum(1 for value in labels_by_subject.values() if value == 0)),
        "total_parkinson_subjects": int(sum(1 for value in labels_by_subject.values() if value == 1)),
        "features_used": feature_columns,
        "model_selected": best_model,
        "validation_method": "GroupKFold por subject_id; splits train/val/test por sujeto",
        "metrics": {"cross_validation": cv_results},
        "confusion_matrix": cv_results[best_model]["folds"][-1]["confusion_matrix"],
        "notes": [
            NO_DIAGNOSIS_NOTE,
            "La decision prioriza recall para Parkinson, F1 y estabilidad entre folds.",
        ],
        "limitations": [
            "El rendimiento depende de calidad, encuadre y diversidad de videos.",
            "No debe usarse como diagnostico medico definitivo.",
            "La validacion evita fuga de sujetos entre folds.",
        ],
        "splits": {
            "train_subjects": sorted(train_subjects),
            "val_subjects": sorted(val_subjects),
            "test_subjects": sorted(test_subjects),
        },
        "accuracy": cv_results[best_model]["mean_accuracy"],
        "precision": cv_results[best_model]["mean_precision"],
        "recall": cv_results[best_model]["mean_recall"],
        "f1_score": cv_results[best_model]["mean_f1_score"],
        "roc_auc": cv_results[best_model]["mean_roc_auc"],
        "samples": int(len(valid_df)),
        "control_samples": int((valid_df["label"] == 0).sum()),
        "parkinson_samples": int((valid_df["label"] == 1).sum()),
    }
    schema = {
        "created_at": now_iso(),
        "feature_columns": feature_columns,
        "imputer_strategy": "median",
        "imputer_statistics": imputer_stats,
        "label_mapping": {"0": "normal", "1": "parkinson"},
        "quality_filter": {"pose_detection_rate_min": args.min_pose_rate},
        "normalization": "distancias normalizadas por escala corporal estimada en landmarks",
    }

    write_json(METRICS_PATH, payload)
    write_json(SCHEMA_PATH, schema)
    write_training_report(payload)

    print(f"modelo_guardado: {MODEL_PATH}")
    print(f"scaler_guardado: {SCALER_PATH}")
    print(f"schema_guardado: {SCHEMA_PATH}")
    print(f"reporte_guardado: {TRAINING_REPORT_PATH}")
    print(f"modelo_ganador: {best_model}")
    print(json.dumps(payload["metrics"]["cross_validation"][best_model], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

