"""
Sprint 4 - Iteración 8: validación del dataset de features para el modelo
Autor: Jared Quinteros García

Objetivo:
    Verificar que el dataset generado por scripts/prepare_iteration8_dataset.py está
    bien formado y LISTO para la preparación del modelo (Sprint 5). NO entrena ni
    evalúa: solo lee y reporta.

Comprueba:
    1. outputs/gait_features_dataset.csv existe.
    2. Existen las columnas requeridas.
    3. Las columnas de features numéricas están presentes y son numéricas.
    4. Las categorías son válidas (control/parkinson/multiple_sclerosis/fall_risk).
    5. Las etiquetas (label) son válidas y coherentes con la categoría.
    6. data/train.csv existe.
    7. data/validation.csv existe.
    8. data/test.csv existe.
    9. El dataset se puede cargar sin fallar.

Salida:
    outputs/iteration8_validation_report.json
    overall_status: READY_FOR_MODEL_PREPARATION (si todo lo crítico pasa).

Uso (entorno Python 3.11):
    .venv311\\Scripts\\python.exe scripts\\validate_iteration8.py
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = PROJECT_ROOT / "outputs" / "gait_features_dataset.csv"
TRAIN_CSV = PROJECT_ROOT / "data" / "train.csv"
VAL_CSV = PROJECT_ROOT / "data" / "validation.csv"
TEST_CSV = PROJECT_ROOT / "data" / "test.csv"
REPORT_JSON = PROJECT_ROOT / "outputs" / "iteration8_validation_report.json"

REQUIRED_COLUMNS = [
    "video_id",
    "source_file",
    "category",
    "label",
    "walkingSpeed",
    "cadence",
    "stepLength",
    "symmetry",
    "stability",
    "gaitVariability",
    "frames_with_pose",
    "notes",
]
NUMERIC_FEATURES = ["walkingSpeed", "cadence", "stepLength", "symmetry", "stability", "gaitVariability"]
CATEGORY_TO_LABEL = {"control": 0, "parkinson": 1, "multiple_sclerosis": 2, "fall_risk": 3}


def add_check(checks, name, passed, detail, critical=True):
    checks.append({"check": name, "passed": bool(passed), "critical": bool(critical), "detail": detail})
    return passed


def is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validación del dataset (Sprint 4 Iteración 8).")
    parser.add_argument("--features", "--input", dest="features", default=str(FEATURES_CSV), help="CSV del dataset de features.")
    parser.add_argument("--report", "--output", dest="report", default=str(REPORT_JSON), help="Ruta del reporte JSON de salida.")
    args = parser.parse_args()

    features_path = Path(args.features)
    report_path = Path(args.report)

    print("=" * 60)
    print("  VALIDACIÓN DEL DATASET - Sprint 4 Iteración 8")
    print("=" * 60)
    print(f"Dataset: {features_path}")

    checks = []
    rows = []
    columns = []

    # 1. Existe el dataset de features
    features_exists = features_path.exists()
    add_check(
        checks,
        "dataset_features_existe",
        features_exists,
        f"Existe {features_path}" if features_exists
        else f"No existe {features_path}. Genera con scripts/prepare_iteration8_dataset.py",
    )

    # 9. Se puede cargar sin fallar (se intenta aquí mismo)
    load_ok = False
    if features_exists:
        try:
            with open(features_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                columns = list(reader.fieldnames or [])
                rows = list(reader)
            load_ok = True
        except Exception as exc:
            add_check(checks, "dataset_cargable", False, f"No se pudo cargar: {exc}")
    add_check(
        checks,
        "dataset_cargable",
        load_ok,
        f"Cargado: {len(rows)} filas, {len(columns)} columnas." if load_ok else "No verificable.",
    )

    # 2. Columnas requeridas
    has_cols = set(REQUIRED_COLUMNS).issubset(set(columns))
    add_check(
        checks,
        "columnas_requeridas",
        has_cols,
        f"Columnas presentes: {columns}" if has_cols
        else f"Faltan columnas. Requeridas: {REQUIRED_COLUMNS}; presentes: {columns}",
    )

    # 3. Columnas numéricas de features presentes y numéricas
    numeric_present = set(NUMERIC_FEATURES).issubset(set(columns))
    numeric_values_ok = True
    bad_numeric = []
    if numeric_present and rows:
        for i, r in enumerate(rows):
            for col in NUMERIC_FEATURES:
                if not is_number(r.get(col, "")):
                    numeric_values_ok = False
                    bad_numeric.append((i, col, r.get(col, "")))
    add_check(
        checks,
        "features_numericas",
        numeric_present and numeric_values_ok,
        f"Features {NUMERIC_FEATURES} presentes y numéricas." if (numeric_present and numeric_values_ok)
        else f"Problema con features numéricas. Presentes={numeric_present}; valores no numéricos={bad_numeric[:5]}",
    )

    # 4. Categorías válidas
    invalid_categories = sorted(
        {(r.get("category") or "").strip().lower() for r in rows} - set(CATEGORY_TO_LABEL)
    )
    categories_ok = bool(rows) and not invalid_categories
    add_check(
        checks,
        "categorias_validas",
        categories_ok,
        "Todas las categorías son válidas." if categories_ok
        else (f"Categorías inválidas: {invalid_categories}" if rows else "No hay filas."),
    )

    # 5. Labels válidos y coherentes con la categoría
    labels_ok = bool(rows)
    bad_labels = []
    for r in rows:
        cat = (r.get("category") or "").strip().lower()
        label_raw = r.get("label", "")
        try:
            label = int(label_raw)
        except (TypeError, ValueError):
            labels_ok = False
            bad_labels.append((r.get("video_id"), label_raw))
            continue
        if label not in (0, 1, 2, 3) or CATEGORY_TO_LABEL.get(cat) != label:
            labels_ok = False
            bad_labels.append((r.get("video_id"), f"{cat}->{label}"))
    add_check(
        checks,
        "labels_validos",
        labels_ok,
        "Etiquetas válidas y coherentes con la categoría." if labels_ok else f"Etiquetas inválidas: {bad_labels[:5]}",
    )

    # 6,7,8. Particiones existen
    train_exists = TRAIN_CSV.exists()
    val_exists = VAL_CSV.exists()
    test_exists = TEST_CSV.exists()
    add_check(checks, "train_csv_existe", train_exists, f"{TRAIN_CSV}" if train_exists else "Falta data/train.csv")
    add_check(checks, "validation_csv_existe", val_exists, f"{VAL_CSV}" if val_exists else "Falta data/validation.csv")
    add_check(checks, "test_csv_existe", test_exists, f"{TEST_CSV}" if test_exists else "Falta data/test.csv")

    # Conteo de filas por partición (informativo)
    def count_rows(path):
        if not path.exists():
            return 0
        try:
            with open(path, newline="", encoding="utf-8") as f:
                return sum(1 for _ in csv.DictReader(f))
        except Exception:
            return 0

    split_counts = {
        "train": count_rows(TRAIN_CSV),
        "validation": count_rows(VAL_CSV),
        "test": count_rows(TEST_CSV),
    }

    # --- Resultado global ---
    critical = [c for c in checks if c["critical"]]
    passed_critical = sum(1 for c in critical if c["passed"])
    all_ok = passed_critical == len(critical)
    overall = "READY_FOR_MODEL_PREPARATION" if all_ok else "NOT_READY"

    label_distribution = {}
    for r in rows:
        cat = (r.get("category") or "").strip().lower()
        label_distribution[cat] = label_distribution.get(cat, 0) + 1

    report = {
        "iteration": 8,
        "features_file": str(features_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "rows": len(rows),
            "columns": columns,
            "label_distribution": label_distribution,
            "split_counts": split_counts,
            "label_mapping": CATEGORY_TO_LABEL,
        },
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c["passed"]),
            "failed": sum(1 for c in checks if not c["passed"]),
            "critical_total": len(critical),
            "critical_passed": passed_critical,
        },
        "overall_status": overall,
        "conclusion": (
            "El dataset está limpio, etiquetado y particionado: LISTO para la preparación del modelo en Sprint 5."
            if all_ok
            else "El dataset NO está listo; revise los checks fallidos."
        ),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "-" * 60)
    for c in checks:
        mark = "OK " if c["passed"] else "FALLA"
        print(f"  [{mark}] {c['check']}: {c['detail']}")
    print("-" * 60)
    print(f"Particiones (train/val/test): {split_counts['train']}/{split_counts['validation']}/{split_counts['test']}")
    print(f"ESTADO GLOBAL: {overall}  ({passed_critical}/{len(critical)} checks críticos)")
    print(f"Reporte JSON : {report_path}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
