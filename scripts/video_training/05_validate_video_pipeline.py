from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from video_training_common import (
    FEATURE_COLUMNS,
    FEATURES_CSV_PATH,
    MANIFEST_PATH,
    MODEL_PATH,
    SCALER_PATH,
    SCHEMA_PATH,
    SPLITS_DIR,
    read_json,
    read_manifest,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Valida pipeline de entrenamiento por video.")
    parser.add_argument("--run-predictor", action="store_true")
    return parser.parse_args()


def read_subject_file(name: str) -> set[str]:
    path = SPLITS_DIR / name
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def run_predictor(video_path: str) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).with_name("04_predict_video_with_model.py")),
        "--video",
        video_path,
    ]
    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=180,
    )
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        payload = {"ok": False, "stdout": completed.stdout, "stderr": completed.stderr}
    payload["exit_code"] = completed.returncode
    return payload


def main() -> int:
    args = parse_args()
    checks = []
    manifest_rows = read_manifest()
    checks.append({"check": "manifest.csv existe", "ok": MANIFEST_PATH.exists()})
    checks.append({"check": "hay videos normales", "ok": any(row.get("condition") == "normal" for row in manifest_rows)})
    checks.append({"check": "hay videos Parkinson", "ok": any(row.get("condition") == "parkinson" for row in manifest_rows)})
    checks.append({"check": "hay sujetos unicos", "ok": len({row.get("subject_id") for row in manifest_rows}) > 0})

    features_ok = FEATURES_CSV_PATH.exists()
    checks.append({"check": "features existen", "ok": features_ok})
    features_df = pd.read_csv(FEATURES_CSV_PATH) if features_ok else pd.DataFrame()
    checks.append({"check": "features no vacias", "ok": not features_df.empty})

    train = read_subject_file("train_subjects.txt")
    val = read_subject_file("val_subjects.txt")
    test = read_subject_file("test_subjects.txt")
    leakage = bool((train & val) or (train & test) or (val & test))
    checks.append({"check": "no fuga train/val/test por sujeto", "ok": not leakage})
    checks.append({"check": "modelo entrenado existe", "ok": MODEL_PATH.exists()})
    checks.append({"check": "scaler existe", "ok": SCALER_PATH.exists()})
    checks.append({"check": "schema existe", "ok": SCHEMA_PATH.exists()})

    schema = read_json(SCHEMA_PATH) or {}
    schema_features = schema.get("feature_columns") or []
    checks.append(
        {
            "check": "features del predictor coinciden con entrenamiento",
            "ok": bool(schema_features) and all(column in FEATURE_COLUMNS for column in schema_features),
        }
    )

    if args.run_predictor and MODEL_PATH.exists() and manifest_rows:
        normal_video = next((row["video_path"] for row in manifest_rows if row.get("condition") == "normal"), None)
        parkinson_video = next((row["video_path"] for row in manifest_rows if row.get("condition") == "parkinson"), None)
        if normal_video:
            checks.append({"check": "predictor funciona con video normal", "ok": run_predictor(normal_video).get("modelUsed") is True})
        if parkinson_video:
            checks.append({"check": "predictor funciona con video Parkinson", "ok": run_predictor(parkinson_video).get("modelUsed") is True})
    else:
        checks.append(
            {
                "check": "predictor normal/parkinson",
                "ok": False,
                "note": "omitido: use --run-predictor cuando existan modelo y videos reales",
            }
        )

    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in checks if item["check"] != "predictor normal/parkinson") else 1


if __name__ == "__main__":
    raise SystemExit(main())

