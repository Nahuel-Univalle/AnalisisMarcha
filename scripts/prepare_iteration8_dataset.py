"""
Sprint 4 - Iteración 8: preparación del dataset de features de marcha
Autor: Jared Quinteros García

Objetivo:
    Combinar los parámetros de marcha por video (outputs/gait_basic_parameters.csv,
    generado por scripts/calculate_basic_params.py — Iteraciones 7 y 8) con las
    categorías (data/dataset_metadata.csv) y producir un dataset de FEATURES listo
    para el modelo de Sprint 5, junto con las particiones train/validation/test.

    NO entrena ni evalúa modelos. Solo limpia, etiqueta y organiza los datos.

Genera:
    - outputs/gait_features_dataset.csv   (dataset final de features + label)
    - data/train.csv                      (70%)
    - data/validation.csv                 (15%)
    - data/test.csv                       (15%)

Mapeo de etiquetas (categoría -> label):
    control = 0 | parkinson = 1 | multiple_sclerosis = 2 | fall_risk = 3

Particiones con tamaños pequeños (no falla nunca):
    - 1 fila  -> todo a train; validation y test solo con cabeceras.
    - 2 filas -> 1 train, 1 test (validation con cabeceras).
    - 3 filas -> 1 train, 1 validation, 1 test.
    - >= 4    -> ~70/15/15 garantizando al menos 1 en cada partición.

Uso (entorno Python 3.11):
    .venv311\\Scripts\\python.exe scripts\\prepare_iteration8_dataset.py

Limitación: los valores son NORMALIZADOS y orientativos (video RGB monocular sin
escala real); no son medidas clínicas ni diagnósticos.
"""

import argparse
import csv
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAIT_PARAMS_CSV = PROJECT_ROOT / "outputs" / "gait_basic_parameters.csv"
METADATA_CSV = PROJECT_ROOT / "data" / "dataset_metadata.csv"
FEATURES_CSV = PROJECT_ROOT / "outputs" / "gait_features_dataset.csv"
TRAIN_CSV = PROJECT_ROOT / "data" / "train.csv"
VAL_CSV = PROJECT_ROOT / "data" / "validation.csv"
TEST_CSV = PROJECT_ROOT / "data" / "test.csv"

CATEGORY_TO_LABEL = {
    "control": 0,
    "parkinson": 1,
    "multiple_sclerosis": 2,
    "fall_risk": 3,
}

FEATURE_HEADER = [
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

# Mapeo columna_dataset_features <- columna_gait_basic_parameters
PARAM_SOURCE = {
    "walkingSpeed": "estimated_velocity_normalized",
    "cadence": "cadence_steps_per_min",
    "stepLength": "average_step_length_normalized",
    "symmetry": "symmetry",
    "stability": "stability",
    "gaitVariability": "gait_variability",
}


def feature_value(row, source_key):
    """Devuelve el valor numérico (redondeado) o "" si no es convertible."""
    raw = row.get(source_key, "")
    try:
        return round(float(raw), 6)
    except (TypeError, ValueError):
        return ""


def load_metadata(path):
    """Devuelve {video_id: {"category":..., "file_path":..., "notes":...}}."""
    meta = {}
    if not path.exists():
        return meta
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                vid = (row.get("video_id") or "").strip()
                if vid:
                    meta[vid] = {
                        "category": (row.get("category") or "").strip().lower(),
                        "file_path": (row.get("file_path") or "").strip(),
                        "notes": (row.get("notes") or "").strip(),
                    }
    except Exception:
        return meta
    return meta


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in header})


def split_rows(rows, seed=42):
    """Particiona en (train, validation, test) con reservas seguras para n pequeño."""
    n = len(rows)
    if n == 0:
        return [], [], []

    shuffled = rows[:]
    random.Random(seed).shuffle(shuffled)

    if n == 1:
        return shuffled, [], []
    if n == 2:
        return shuffled[:1], [], shuffled[1:]
    if n == 3:
        return shuffled[:1], shuffled[1:2], shuffled[2:]

    # n >= 4: ~70/15/15 garantizando al menos 1 en validation y test
    n_val = max(1, round(n * 0.15))
    n_test = max(1, round(n * 0.15))
    n_train = n - n_val - n_test
    if n_train < 1:  # guarda defensiva para casos límite
        n_train = 1
        n_val = max(1, (n - n_train) // 2)
        n_test = n - n_train - n_val
    return (
        shuffled[:n_train],
        shuffled[n_train:n_train + n_val],
        shuffled[n_train + n_val:],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Preparación del dataset de features (Sprint 4 Iteración 8).")
    parser.add_argument("--params", "--input", dest="params", default=str(GAIT_PARAMS_CSV), help="CSV de parámetros por video (Iteración 7/8).")
    parser.add_argument("--metadata", default=str(METADATA_CSV), help="CSV de metadatos de categorías.")
    parser.add_argument("--features-output", "--global-output", dest="features_output", default=str(FEATURES_CSV), help="CSV global de features (upsert por video_id).")
    parser.add_argument("--train", default=str(TRAIN_CSV), help="CSV de entrenamiento.")
    parser.add_argument("--validation", default=str(VAL_CSV), help="CSV de validación.")
    parser.add_argument("--test", default=str(TEST_CSV), help="CSV de prueba.")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para la partición (reproducible).")
    args = parser.parse_args()

    params_path = Path(args.params)
    metadata_path = Path(args.metadata)
    features_path = Path(args.features_output)
    train_path = Path(args.train)
    val_path = Path(args.validation)
    test_path = Path(args.test)

    print("=" * 60)
    print("  PREPARACIÓN DEL DATASET - Sprint 4 Iteración 8")
    print("=" * 60)
    print(f"Parámetros : {params_path}")

    if not params_path.exists():
        print("\n[ERROR] No existe el CSV de parámetros por video.")
        print("        Genera primero con:")
        print("        .venv311\\Scripts\\python.exe scripts\\calculate_basic_params.py --video-id <id> --fps 30")
        return 1

    metadata = load_metadata(metadata_path)

    with open(params_path, newline="", encoding="utf-8") as f:
        param_rows = list(csv.DictReader(f))

    if not param_rows:
        print("\n[ERROR] El CSV de parámetros no tiene filas. Procesa al menos un video.")
        return 1

    feature_rows = []
    skipped = []

    for row in param_rows:
        video_id = (row.get("video_id") or "").strip()
        meta = metadata.get(video_id, {})

        # Categoría: prioridad a metadata (autoritativa); si no, la del CSV de parámetros.
        category = meta.get("category") or (row.get("category") or "").strip().lower()

        if category not in CATEGORY_TO_LABEL:
            skipped.append((video_id, category or "vacia"))
            continue

        label = CATEGORY_TO_LABEL[category]
        source_file = (row.get("source_file") or "").strip() or meta.get("file_path", "")

        feature_rows.append(
            {
                "video_id": video_id,
                "source_file": source_file,
                "category": category,
                "label": label,
                "walkingSpeed": feature_value(row, PARAM_SOURCE["walkingSpeed"]),
                "cadence": feature_value(row, PARAM_SOURCE["cadence"]),
                "stepLength": feature_value(row, PARAM_SOURCE["stepLength"]),
                "symmetry": feature_value(row, PARAM_SOURCE["symmetry"]),
                "stability": feature_value(row, PARAM_SOURCE["stability"]),
                "gaitVariability": feature_value(row, PARAM_SOURCE["gaitVariability"]),
                "frames_with_pose": (row.get("frames_with_pose") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
            }
        )

    if not feature_rows:
        print("\n[ERROR] Ninguna fila tenía una categoría válida (control/parkinson/multiple_sclerosis/fall_risk).")
        print("        Asigna categorías en data/dataset_metadata.csv y vuelve a ejecutar.")
        return 1

    # 1. UPSERT por video_id en el dataset GLOBAL de features (acumula varias subidas).
    #    Se conservan las filas existentes y se actualizan/añaden las nuevas.
    merged = {}
    if features_path.exists():
        try:
            with open(features_path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    vid = (r.get("video_id") or "").strip()
                    if vid:
                        merged[vid] = {k: r.get(k, "") for k in FEATURE_HEADER}
        except Exception:
            merged = {}
    for r in feature_rows:
        merged[r["video_id"]] = r
    all_rows = list(merged.values())

    write_csv(features_path, FEATURE_HEADER, all_rows)

    # 2. Particiones train / validation / test sobre TODO el dataset
    train_rows, val_rows, test_rows = split_rows(all_rows, seed=args.seed)
    write_csv(train_path, FEATURE_HEADER, train_rows)
    write_csv(val_path, FEATURE_HEADER, val_rows)
    write_csv(test_path, FEATURE_HEADER, test_rows)

    # Resumen
    label_counts = {}
    for r in all_rows:
        cat = (r.get("category") or "")
        label_counts[cat] = label_counts.get(cat, 0) + 1

    print("\n" + "-" * 60)
    print("RESUMEN DEL DATASET")
    print(f"  Filas nuevas/actualiz.: {len(feature_rows)}")
    print(f"  Filas totales         : {len(all_rows)}")
    print(f"  Por categoría         : {label_counts}")
    if skipped:
        print(f"  Filas omitidas        : {len(skipped)} (categoría inválida) -> {skipped}")
    print(f"  train / val / test    : {len(train_rows)} / {len(val_rows)} / {len(test_rows)}")
    print(f"  Dataset features      -> {features_path}")
    print(f"  Partición train       -> {train_path}")
    print(f"  Partición validation  -> {val_path}")
    print(f"  Partición test        -> {test_path}")
    print("-" * 60)
    print("\n[EXITO] Dataset de Iteración 8 preparado y particionado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
