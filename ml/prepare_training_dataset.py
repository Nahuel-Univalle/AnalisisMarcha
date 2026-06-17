import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "parkinson"
    / "processed"
    / "gait_parkinson_dataset_features_summary.csv"
)
OUTPUT_PATH = PROJECT_ROOT / "ml" / "data" / "training_features.csv"

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

META_COLUMNS = [
    "source_file",
    "subject_id",
    "condition",
    "parkinson_binary",
    "walk_number",
]


def normalize_label(row):
    condition = (row.get("condition") or "").strip().lower()
    subject_type = (row.get("subject_type") or "").strip().lower()
    source_file = (row.get("source_file") or "").strip().lower()
    raw_binary = (row.get("parkinson_binary") or "").strip()

    if condition == "control" or subject_type == "co" or "co" in source_file:
        return "control", "0"

    if (
        condition in {"parkinson", "pd"}
        or subject_type == "pt"
        or "pt" in source_file
        or raw_binary == "1"
    ):
        return "parkinson", "1"

    return condition or "unknown", raw_binary or "0"


def main():
    if not SOURCE_PATH.exists():
        print(f"No existe el CSV resumido: {SOURCE_PATH}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with SOURCE_PATH.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)
        missing = [column for column in META_COLUMNS + FEATURE_COLUMNS if column not in reader.fieldnames]
        if missing:
            print(
                f"El CSV resumido no contiene columnas requeridas: {', '.join(missing)}",
                file=sys.stderr,
            )
            sys.exit(1)

        rows = []
        control = 0
        parkinson = 0
        for row in reader:
            condition, binary = normalize_label(row)
            output_row = {
                "source_file": row.get("source_file") or "",
                "subject_id": row.get("subject_id") or row.get("source_file") or "",
                "condition": condition,
                "parkinson_binary": binary,
                "walk_number": row.get("walk_number") or "",
            }
            for column in FEATURE_COLUMNS:
                output_row[column] = row.get(column) or ""

            if binary == "0":
                control += 1
            elif binary == "1":
                parkinson += 1
            rows.append(output_row)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=META_COLUMNS + FEATURE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Archivo generado: {OUTPUT_PATH}")
    print(f"Filas de entrenamiento: {len(rows)}")
    print(f"Control: {control}")
    print(f"Parkinson: {parkinson}")


if __name__ == "__main__":
    main()
