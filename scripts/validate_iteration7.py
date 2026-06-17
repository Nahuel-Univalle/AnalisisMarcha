"""
Sprint 4 - Iteración 7: validación de coordenadas de pose para parámetros de marcha
Autor: Jared Quinteros García

Objetivo:
    Verificar que el CSV de landmarks (outputs/pose_landmarks.csv generado en el
    Sprint 3) es USABLE para calcular los parámetros básicos de marcha
    (velocidad, cadencia, longitud de paso). NO modifica datos: solo lee y reporta.

Comprueba:
    1. El archivo de coordenadas existe.
    2. Existen las columnas requeridas.
    3. Existen landmarks de caderas (23, 24) y tobillos (27, 28).
    4. Hay suficientes frames.
    5. La visibilidad/confianza es aceptable.
    6. Hay suficientes frames con pose válida (los 4 landmarks requeridos).
    7. Los parámetros básicos se pueden calcular sin que el proceso falle.

Salida:
    outputs/iteration7_validation_report.json

Uso (entorno Python 3.11):
    .venv311\\Scripts\\python.exe scripts\\validate_iteration7.py
    .venv311\\Scripts\\python.exe scripts\\validate_iteration7.py --input outputs\\pose_landmarks.csv
"""

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "outputs" / "pose_landmarks.csv"
REPORT_JSON = PROJECT_ROOT / "outputs" / "iteration7_validation_report.json"

REQUIRED_COLUMNS = ("frame_index", "landmark_index", "x", "y", "visibility")
HIP_LANDMARKS = (23, 24)
ANKLE_LANDMARKS = (27, 28)
REQUIRED_LANDMARKS = HIP_LANDMARKS + ANKLE_LANDMARKS

# Umbrales (académicos, conservadores)
MIN_FRAMES = 5            # frames distintos mínimos
MIN_VALID_POSE_FRAMES = 5  # frames con los 4 landmarks requeridos
MIN_MEAN_VISIBILITY = 0.30  # visibilidad media aceptable de los landmarks clave


def add_check(checks, name, passed, detail, critical=True):
    checks.append(
        {"check": name, "passed": bool(passed), "critical": bool(critical), "detail": detail}
    )
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Validación de coordenadas de pose (Sprint 4 Iteración 7).")
    parser.add_argument("--input", default=str(INPUT_CSV), help="CSV de landmarks a validar.")
    parser.add_argument("--report", "--output", dest="report", default=str(REPORT_JSON), help="Ruta del reporte JSON de salida.")
    args = parser.parse_args()

    input_csv = Path(args.input)
    report_path = Path(args.report)

    print("=" * 60)
    print("  VALIDACIÓN DE COORDENADAS - Sprint 4 Iteración 7")
    print("=" * 60)
    print(f"Archivo de coordenadas: {input_csv}")

    checks = []

    # 1. El archivo existe
    file_exists = input_csv.exists()
    add_check(
        checks,
        "archivo_coordenadas_existe",
        file_exists,
        f"Existe {input_csv}" if file_exists else f"No existe {input_csv}. Genera primero pose_landmarks.csv con scripts/export_pose_csv.py",
    )

    frames = {}
    visibility_values = []
    columns = []

    if file_exists:
        try:
            with open(input_csv, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                columns = list(reader.fieldnames or [])
                has_required_cols = set(REQUIRED_COLUMNS).issubset(set(columns))
                # 2. Columnas requeridas
                add_check(
                    checks,
                    "columnas_requeridas",
                    has_required_cols,
                    f"Columnas presentes: {columns}" if has_required_cols
                    else f"Faltan columnas. Requeridas: {list(REQUIRED_COLUMNS)}; presentes: {columns}",
                )

                if has_required_cols:
                    for row in reader:
                        try:
                            fi = int(row["frame_index"])
                            li = int(row["landmark_index"])
                            x = float(row["x"])
                            y = float(row["y"])
                        except (TypeError, ValueError):
                            continue
                        frames.setdefault(fi, {})[li] = (x, y)
                        if li in REQUIRED_LANDMARKS:
                            try:
                                visibility_values.append(float(row["visibility"]))
                            except (TypeError, ValueError):
                                pass
        except Exception as exc:  # lectura defensiva
            add_check(checks, "lectura_csv", False, f"No se pudo leer el CSV: {exc}")
    else:
        # Si no existe, marcamos las columnas como no verificables (fallo crítico ya registrado)
        add_check(checks, "columnas_requeridas", False, "No verificable: el archivo no existe.")

    # Conjunto de landmarks presentes en todo el archivo
    present_landmarks = set()
    for lm in frames.values():
        present_landmarks.update(lm.keys())

    # 3. Suficientes frames
    n_frames = len(frames)
    add_check(
        checks,
        "suficientes_frames",
        n_frames >= MIN_FRAMES,
        f"{n_frames} frames distintos (minimo {MIN_FRAMES}).",
    )

    # 4. Landmarks de caderas presentes
    hips_ok = all(lm in present_landmarks for lm in HIP_LANDMARKS)
    add_check(
        checks,
        "landmarks_caderas_presentes",
        hips_ok,
        f"Caderas {HIP_LANDMARKS} presentes." if hips_ok else f"Faltan landmarks de cadera {HIP_LANDMARKS}.",
    )

    # 5. Landmarks de tobillos presentes
    ankles_ok = all(lm in present_landmarks for lm in ANKLE_LANDMARKS)
    add_check(
        checks,
        "landmarks_tobillos_presentes",
        ankles_ok,
        f"Tobillos {ANKLE_LANDMARKS} presentes." if ankles_ok else f"Faltan landmarks de tobillo {ANKLE_LANDMARKS}.",
    )

    # 6. Frames con pose válida (los 4 landmarks requeridos)
    valid_pose_frames = sum(
        1 for lm in frames.values() if all(idx in lm for idx in REQUIRED_LANDMARKS)
    )
    add_check(
        checks,
        "suficientes_frames_con_pose_valida",
        valid_pose_frames >= MIN_VALID_POSE_FRAMES,
        f"{valid_pose_frames} frames con caderas+tobillos (minimo {MIN_VALID_POSE_FRAMES}).",
    )

    # 7. Visibilidad/confianza aceptable
    mean_visibility = sum(visibility_values) / len(visibility_values) if visibility_values else 0.0
    add_check(
        checks,
        "visibilidad_aceptable",
        mean_visibility >= MIN_MEAN_VISIBILITY,
        f"Visibilidad media de landmarks clave = {mean_visibility:.3f} (minimo {MIN_MEAN_VISIBILITY}).",
        critical=False,  # informativa: visibilidad baja no impide el cálculo, pero avisa
    )

    # 8. Los parámetros básicos se pueden calcular sin fallar (dry run)
    params_ok = False
    params_detail = "No se intentó (faltan frames válidos)."
    if valid_pose_frames >= 2:
        try:
            ankle_series = []
            hip_xs = []
            for fi in sorted(frames):
                lm = frames[fi]
                if not all(idx in lm for idx in REQUIRED_LANDMARKS):
                    continue
                lxa, lya = lm[27]
                rxa, rya = lm[28]
                lxh, _ = lm[23]
                rxh, _ = lm[24]
                ankle_series.append(math.hypot(lxa - rxa, lya - rya))
                hip_xs.append((lxh + rxh) / 2)
            # Operaciones que harán falta en el cálculo real:
            mean_ankle = sum(ankle_series) / len(ankle_series)
            hip_displacement = abs(hip_xs[-1] - hip_xs[0])
            params_ok = True
            params_detail = (
                f"Calculo de prueba OK: {len(ankle_series)} frames usables; "
                f"separacion media tobillos = {mean_ankle:.4f} (norm); "
                f"desplazamiento cadera = {hip_displacement:.4f} (norm)."
            )
        except Exception as exc:
            params_ok = False
            params_detail = f"El calculo de prueba falló: {exc}"
    add_check(checks, "parametros_calculables", params_ok, params_detail)

    # --- Resultado global ---
    critical_checks = [c for c in checks if c["critical"]]
    passed_critical = sum(1 for c in critical_checks if c["passed"])
    all_critical_ok = passed_critical == len(critical_checks)
    overall = "USABLE" if all_critical_ok else "NO_USABLE"

    report = {
        "iteration": 7,
        "input_file": str(input_csv),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "min_frames": MIN_FRAMES,
            "min_valid_pose_frames": MIN_VALID_POSE_FRAMES,
            "min_mean_visibility": MIN_MEAN_VISIBILITY,
        },
        "stats": {
            "columns": columns,
            "distinct_frames": n_frames,
            "valid_pose_frames": valid_pose_frames,
            "mean_visibility_key_landmarks": round(mean_visibility, 4),
            "present_required_landmarks": sorted(
                lm for lm in REQUIRED_LANDMARKS if lm in present_landmarks
            ),
        },
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c["passed"]),
            "failed": sum(1 for c in checks if not c["passed"]),
            "critical_total": len(critical_checks),
            "critical_passed": passed_critical,
        },
        "overall_status": overall,
        "conclusion": (
            "Las coordenadas de pose son USABLES para calcular velocidad, cadencia y longitud de paso."
            if all_critical_ok
            else "Las coordenadas NO son suficientes; revise los checks fallidos (genere un pose_landmarks.csv válido)."
        ),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Resumen por consola
    print("\n" + "-" * 60)
    for c in checks:
        mark = "OK " if c["passed"] else "FALLA"
        tag = "" if c["critical"] else " (info)"
        print(f"  [{mark}] {c['check']}{tag}: {c['detail']}")
    print("-" * 60)
    print(f"ESTADO GLOBAL: {overall}  ({passed_critical}/{len(critical_checks)} checks críticos)")
    print(f"Reporte JSON : {report_path}")

    return 0 if all_critical_ok else 1


if __name__ == "__main__":
    sys.exit(main())
