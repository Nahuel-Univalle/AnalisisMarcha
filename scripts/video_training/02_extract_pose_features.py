from __future__ import annotations

import argparse

from video_training_common import (
    ERROR_REPORT_PATH,
    FEATURE_CSV_COLUMNS,
    FEATURES_CSV_PATH,
    MANIFEST_COLUMNS,
    MANIFEST_PATH,
    QUALITY_COLUMNS,
    QUALITY_REPORT_PATH,
    extract_video_features,
    read_manifest,
    write_rows,
)


def progress(iterable, total: int):
    try:
        from tqdm import tqdm  # type: ignore

        return tqdm(iterable, total=total, desc="Extrayendo landmarks")
    except Exception:
        return iterable


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrae landmarks MediaPipe Pose y features reales de marcha desde manifest.csv."
    )
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--frame-step", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_manifest()
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    feature_rows = []
    quality_rows = []
    error_rows = []

    for row in progress(rows, len(rows)):
        result = extract_video_features(
            row,
            frame_step=args.frame_step,
            force=args.force,
        )
        feature_rows.append(result.feature_row)
        quality_rows.append({**row, **result.quality_row})
        if result.error_row:
            error_rows.append(result.error_row)

    write_rows(FEATURES_CSV_PATH, feature_rows, FEATURE_CSV_COLUMNS)
    write_rows(QUALITY_REPORT_PATH, quality_rows, MANIFEST_COLUMNS + QUALITY_COLUMNS)
    write_rows(ERROR_REPORT_PATH, error_rows, MANIFEST_COLUMNS + ["error"])

    valid = sum(1 for row in feature_rows if str(row.get("valid_for_training")).lower() == "true")
    print(f"features_csv: {FEATURES_CSV_PATH}")
    print(f"quality_report: {QUALITY_REPORT_PATH}")
    print(f"errors_report: {ERROR_REPORT_PATH}")
    print(f"videos_procesados: {len(feature_rows)}")
    print(f"videos_validos_entrenamiento: {valid}")
    print(f"videos_con_error: {len(error_rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
