from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "video_training"
MANIFEST_PATH = DATA_ROOT / "manifest.csv"
LANDMARKS_DIR = DATA_ROOT / "pose_landmarks"
FEATURES_DIR = DATA_ROOT / "features"
REPORTS_DIR = DATA_ROOT / "reports"
SPLITS_DIR = DATA_ROOT / "splits"
PREDICTIONS_DIR = REPORTS_DIR / "predictions"
MODELS_DIR = PROJECT_ROOT / "models" / "video_parkinson"

FEATURES_CSV_PATH = FEATURES_DIR / "video_gait_features.csv"
QUALITY_REPORT_PATH = REPORTS_DIR / "pose_quality_report.csv"
ERROR_REPORT_PATH = REPORTS_DIR / "pose_extraction_errors.csv"

MODEL_PATH = MODELS_DIR / "video_parkinson_model.joblib"
SCALER_PATH = MODELS_DIR / "video_parkinson_scaler.joblib"
SCHEMA_PATH = MODELS_DIR / "video_parkinson_feature_schema.json"
METRICS_PATH = MODELS_DIR / "video_parkinson_metrics.json"
TRAINING_REPORT_PATH = MODELS_DIR / "video_parkinson_training_report.md"

SUPPORTED_EXTENSIONS = {".mov", ".mp4", ".avi", ".mkv"}

# ---------------------------------------------------------------------------
#  Clases del sistema.
#  El pipeline historico era BINARIO (normal vs parkinson). A partir de la
#  ampliacion multiclase se agregan esclerosis multiple y riesgo de caida.
#  Los scripts binarios legacy (03_train_video_parkinson_model.py) siguen
#  funcionando: filtran a label in {0, 1}.
# ---------------------------------------------------------------------------
CLASS_NAMES = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
CLASS_TO_LABEL = {name: index for index, name in enumerate(CLASS_NAMES)}
LABEL_TO_CLASS = {index: name for index, name in enumerate(CLASS_NAMES)}
NUM_CLASSES = len(CLASS_NAMES)

# Etiquetas legibles para informes / frontend (se replican en TS).
CLASS_HUMAN_LABEL = {
    "normal": "Marcha dentro de patrones esperados",
    "parkinson": "Patrón compatible con alteración asociada a Parkinson",
    "esclerosis_multiple": "Patrón compatible con alteración asociada a Esclerosis Múltiple",
    "riesgo_caida": "Patrón compatible con inestabilidad / riesgo de caída",
}

VIDEO_SOURCES = [
    {
        "folder": PROJECT_ROOT / "videos" / "normal",
        "condition": "normal",
        "label": 0,
        "severity": "none",
        "source_folder": "normal",
    },
    {
        "folder": PROJECT_ROOT / "videos" / "parkinson" / "PD_ML",
        "condition": "parkinson",
        "label": 1,
        "severity": "mild",
        "source_folder": "PD_ML",
    },
    {
        "folder": PROJECT_ROOT / "videos" / "parkinson" / "PD_MD",
        "condition": "parkinson",
        "label": 1,
        "severity": "moderate",
        "source_folder": "PD_MD",
    },
    {
        "folder": PROJECT_ROOT / "videos" / "parkinson" / "PD_SV",
        "condition": "parkinson",
        "label": 1,
        "severity": "severe",
        "source_folder": "PD_SV",
    },
    {
        "folder": PROJECT_ROOT / "videos" / "esclerosis_multiple",
        "condition": "esclerosis_multiple",
        "label": 2,
        "severity": "unknown",
        "source_folder": "esclerosis_multiple",
    },
    {
        "folder": PROJECT_ROOT / "videos" / "riesgo_caida",
        "condition": "riesgo_caida",
        "label": 3,
        "severity": "unknown",
        "source_folder": "riesgo_caida",
    },
]

# Archivos excluidos del pipeline (NO se borran del disco; solo no entran a
# manifest/dataset). Motivo documentado por archivo.
#  - VideoEscleorosis7.mp4: byte-identico a VideoEscleorosis6.mp4 (mismo MD5).
#    Duplicado literal; incluirlo mete el mismo video en train y test de folds
#    distintos (fuga) e infla el conteo de la clase esclerosis_multiple.
#  - Escleorosis3.mp4 (lote nuevo, subido 2026-09-15): revision visual de esta
#    sesion (contact sheet de 15 fotogramas a lo largo de sus 183s) muestra
#    multiples escenas/actividades no relacionadas con marcha en piso plano
#    (sala con juguetes, estiramientos con brazos en alto, y una secuencia
#    completa de subir escaleras sujetando el pasamanos). No es una secuencia
#    de marcha coherente; se excluye del manifest, no se recorta ni modifica
#    el archivo de video.
MANIFEST_EXCLUDE = {
    "VideoEscleorosis7.mp4": "duplicado byte-identico de VideoEscleorosis6.mp4",
    "Escleorosis3.mp4": (
        "contiene multiples escenas/actividades no relacionadas con marcha en "
        "piso plano (sala con juguetes, estiramientos, subir escaleras) a lo "
        "largo de sus 183s; no es una secuencia de marcha coherente "
        "(revision visual, sesion 2026-09-27)."
    ),
}

MANIFEST_COLUMNS = [
    "video_path",
    "filename",
    "subject_id",
    "subject_documented",
    "condition",
    "label",
    "severity",
    "sequence",
    "source_folder",
    "file_extension",
]

ID_COLUMNS = [
    "video_path",
    "filename",
    "subject_id",
    "subject_documented",
    "condition",
    "label",
    "severity",
    "sequence",
]

QUALITY_COLUMNS = [
    "total_frames",
    "processed_frames",
    "valid_pose_frames",
    "pose_detection_rate",
    "duration_seconds",
    "fps",
    "width",
    "height",
    "valid_for_training",
    "quality_warning",
]

FEATURE_COLUMNS = [
    "body_motion_mean",
    "body_motion_std",
    "hip_center_motion_mean",
    "shoulder_center_motion_mean",
    "vertical_motion_mean",
    "horizontal_motion_mean",
    "left_ankle_motion_mean",
    "right_ankle_motion_mean",
    "left_knee_motion_mean",
    "right_knee_motion_mean",
    "leg_motion_asymmetry",
    "ankle_vertical_range_left",
    "ankle_vertical_range_right",
    "ankle_vertical_asymmetry",
    "knee_vertical_range_left",
    "knee_vertical_range_right",
    "step_regularity_score",
    "left_wrist_motion_mean",
    "right_wrist_motion_mean",
    "arm_swing_mean",
    "arm_swing_asymmetry",
    "left_arm_range",
    "right_arm_range",
    "shoulder_width_mean",
    "hip_width_mean",
    "trunk_inclination_mean",
    "trunk_inclination_std",
    "trunk_sway_mean",
    "trunk_sway_std",
    "posture_stability_score",
    "estimated_step_count",
    "estimated_cadence_steps_per_min",
    "step_frequency_hz",
    "gait_variability",
    "motion_smoothness",
    "rhythm_variability",
]

FEATURE_CSV_COLUMNS = ID_COLUMNS + QUALITY_COLUMNS + FEATURE_COLUMNS + [
    "landmarks_file",
    "error",
]

SELECTED_LANDMARKS = [
    "NOSE",
    "LEFT_SHOULDER",
    "RIGHT_SHOULDER",
    "LEFT_ELBOW",
    "RIGHT_ELBOW",
    "LEFT_WRIST",
    "RIGHT_WRIST",
    "LEFT_HIP",
    "RIGHT_HIP",
    "LEFT_KNEE",
    "RIGHT_KNEE",
    "LEFT_ANKLE",
    "RIGHT_ANKLE",
    "LEFT_HEEL",
    "RIGHT_HEEL",
    "LEFT_FOOT_INDEX",
    "RIGHT_FOOT_INDEX",
]

CORE_LANDMARKS = [
    "LEFT_SHOULDER",
    "RIGHT_SHOULDER",
    "LEFT_HIP",
    "RIGHT_HIP",
    "LEFT_KNEE",
    "RIGHT_KNEE",
    "LEFT_ANKLE",
    "RIGHT_ANKLE",
]

NO_DIAGNOSIS_NOTE = (
    "Este analisis constituye una orientacion basada en patrones de movimiento y "
    "no representa un diagnostico medico. Identifica patrones de marcha que "
    "pueden asociarse a marcha normal, Parkinson, Esclerosis Multiple o riesgo "
    "de caida, y siempre requiere valoracion por un profesional de salud."
)


@dataclass
class ExtractionResult:
    feature_row: dict[str, Any]
    quality_row: dict[str, Any]
    error_row: dict[str, Any] | None


def ensure_training_dirs() -> None:
    for path in [
        DATA_ROOT,
        LANDMARKS_DIR,
        FEATURES_DIR,
        REPORTS_DIR,
        SPLITS_DIR,
        PREDICTIONS_DIR,
        MODELS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)


def safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    cleaned = cleaned.strip("._")
    return cleaned[:120] or "video"


def parse_subject_and_sequence(
    filename: str, condition: str
) -> tuple[str, str, bool, str | None]:
    """Devuelve (subject_id, sequence, subject_documented, warning).

    - normal / parkinson: nombres tipo ``001_NM_02`` o ``001_PD_01_MD`` -> el
      sujeto es ``001_NM`` / ``001_PD`` y NO depende del nivel de severidad
      (ML/MD/SV son clips del mismo sujeto). subject_documented=True.
    - esclerosis_multiple: ``VideoEsclerosis7.mp4`` -> pseudo-sujeto ``MS_007``.
    - riesgo_caida: ``RiesgoCaida7.mp4`` -> pseudo-sujeto ``FALL_007``.
      En ambos casos NO hay identificador clinico de sujeto en los datos: se
      asume 1 video == 1 sujeto y subject_documented=False (limitacion
      registrada para la division train/val/test).
    """
    stem = Path(filename).stem
    normalized = stem.replace("-", "_")

    pattern = re.compile(
        r"^(?P<prefix>[A-Za-z0-9]+)_(?P<tag>NM|PD)_(?P<sequence>\d+)(?:_(?P<suffix>[A-Za-z]+))?$",
        re.IGNORECASE,
    )
    match = pattern.match(normalized)
    if match:
        subject_id = f"{match.group('prefix')}_{match.group('tag').upper()}"
        return subject_id, match.group("sequence"), True, None

    ms_match = re.match(r"^video?_?escl?erosis_?(\d+)$", normalized, re.IGNORECASE)
    if condition == "esclerosis_multiple" or ms_match:
        number = ms_match.group(1) if ms_match else _trailing_digits(normalized) or "0"
        return f"MS_{int(number):03d}", "01", False, None

    fall_match = re.match(
        r"^riesgo_?(?:de_?)?caida_?(\d+)$", normalized, re.IGNORECASE
    )
    if condition == "riesgo_caida" or fall_match:
        number = fall_match.group(1) if fall_match else _trailing_digits(normalized) or "0"
        return f"FALL_{int(number):03d}", "01", False, None

    parts = [part for part in normalized.split("_") if part]
    if len(parts) >= 2 and parts[-1].isdigit():
        return "_".join(parts[:-1]), parts[-1], True, None

    inferred_tag = "NM" if condition == "normal" else "PD"
    fallback_subject = (
        f"{normalized}_{inferred_tag}"
        if inferred_tag not in normalized.upper()
        else normalized
    )
    return fallback_subject, "", False, f"Nombre fuera del patron esperado: {filename}"


def _trailing_digits(value: str) -> str | None:
    match = re.search(r"(\d+)\s*$", value)
    return match.group(1) if match else None


def discover_videos() -> tuple[list[dict[str, Any]], list[str]]:
    ensure_training_dirs()
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for source in VIDEO_SOURCES:
        folder = source["folder"]
        if not folder.exists():
            warnings.append(f"No existe carpeta: {project_relative(folder)}")
            continue

        for video_path in sorted(folder.rglob("*")):
            if not video_path.is_file():
                continue
            extension = video_path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                continue
            if video_path.name in MANIFEST_EXCLUDE:
                warnings.append(
                    f"Excluido {video_path.name}: {MANIFEST_EXCLUDE[video_path.name]}"
                )
                continue

            subject_id, sequence, subject_documented, warning = parse_subject_and_sequence(
                video_path.name,
                str(source["condition"]),
            )
            if warning:
                warnings.append(warning)

            rows.append(
                {
                    "video_path": project_relative(video_path),
                    "filename": video_path.name,
                    "subject_id": subject_id,
                    "subject_documented": bool(subject_documented),
                    "condition": source["condition"],
                    "label": source["label"],
                    "severity": source["severity"],
                    "sequence": sequence,
                    "source_folder": source["source_folder"],
                    "file_extension": extension,
                }
            )

    return rows, warnings


def write_manifest(rows: list[dict[str, Any]], path: Path = MANIFEST_PATH) -> None:
    ensure_training_dirs()
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_manifest(path: Path = MANIFEST_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def manifest_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = {
        source["source_folder"]: sum(
            1 for row in rows if row.get("source_folder") == source["source_folder"]
        )
        for source in VIDEO_SOURCES
    }
    summary: dict[str, Any] = {
        "total_videos": len(rows),
        "extensiones_encontradas": sorted({str(row.get("file_extension")) for row in rows}),
        "total_PD_ML": by_source.get("PD_ML", 0),
        "total_PD_MD": by_source.get("PD_MD", 0),
        "total_PD_SV": by_source.get("PD_SV", 0),
    }
    for class_name in CLASS_NAMES:
        class_rows = [row for row in rows if str(row.get("condition")) == class_name]
        subjects = {row.get("subject_id") for row in class_rows}
        documented = {
            row.get("subject_id")
            for row in class_rows
            if str(row.get("subject_documented")).lower() == "true"
        }
        summary[f"videos_{class_name}"] = len(class_rows)
        summary[f"sujetos_{class_name}"] = len(subjects)
        summary[f"sujetos_{class_name}_documentados"] = len(documented)
    return summary


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def finite_or_none(value: Any, digits: int = 8) -> float | None:
    parsed = to_float(value)
    if parsed is None:
        return None
    return round(parsed, digits)


def mean(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(value)]
    return sum(clean) / len(clean) if clean else None


def std(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(value)]
    if len(clean) < 2:
        return 0.0 if clean else None
    avg = sum(clean) / len(clean)
    return math.sqrt(sum((value - avg) ** 2 for value in clean) / len(clean))


def percentile(values: list[float], fraction: float) -> float | None:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    index = (len(clean) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return clean[int(index)]
    return clean[lower] * (upper - index) + clean[upper] * (index - lower)


def median(values: Iterable[float]) -> float | None:
    return percentile([float(value) for value in values if value is not None], 0.5)


def point_distance(a: dict[str, float], b: dict[str, float]) -> float:
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)


def center_point(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    return {
        "x": (a["x"] + b["x"]) / 2,
        "y": (a["y"] + b["y"]) / 2,
        "z": (a.get("z", 0.0) + b.get("z", 0.0)) / 2,
        "visibility": min(a.get("visibility", 0.0), b.get("visibility", 0.0)),
    }


def frame_point(frame: dict[str, Any], name: str, min_visibility: float = 0.2) -> dict[str, float] | None:
    point = frame.get("landmarks", {}).get(name)
    if not point:
        return None
    if point.get("visibility", 0.0) < min_visibility:
        return None
    return point


def frame_center(
    frame: dict[str, Any],
    left_name: str,
    right_name: str,
    min_visibility: float = 0.2,
) -> dict[str, float] | None:
    left = frame_point(frame, left_name, min_visibility)
    right = frame_point(frame, right_name, min_visibility)
    if not left or not right:
        return None
    return center_point(left, right)


def frame_body_scale(frame: dict[str, Any]) -> float | None:
    scales: list[float] = []
    left_shoulder = frame_point(frame, "LEFT_SHOULDER")
    right_shoulder = frame_point(frame, "RIGHT_SHOULDER")
    left_hip = frame_point(frame, "LEFT_HIP")
    right_hip = frame_point(frame, "RIGHT_HIP")
    if left_shoulder and right_shoulder:
        scales.append(point_distance(left_shoulder, right_shoulder))
    if left_hip and right_hip:
        scales.append(point_distance(left_hip, right_hip))
    shoulder_center = frame_center(frame, "LEFT_SHOULDER", "RIGHT_SHOULDER")
    hip_center = frame_center(frame, "LEFT_HIP", "RIGHT_HIP")
    if shoulder_center and hip_center:
        scales.append(point_distance(shoulder_center, hip_center))
    clean = [value for value in scales if value > 0]
    return median(clean)


def normalized(value: float | None, scale: float | None) -> float | None:
    if value is None:
        return None
    if not scale or scale <= 0:
        return value
    return value / scale


def point_series(frames: list[dict[str, Any]], name: str) -> list[tuple[float, dict[str, float]]]:
    series: list[tuple[float, dict[str, float]]] = []
    for frame in frames:
        point = frame_point(frame, name)
        if point:
            series.append((float(frame["timestamp_sec"]), point))
    return series


def center_series(
    frames: list[dict[str, Any]],
    left_name: str,
    right_name: str,
) -> list[tuple[float, dict[str, float]]]:
    series: list[tuple[float, dict[str, float]]] = []
    for frame in frames:
        point = frame_center(frame, left_name, right_name)
        if point:
            series.append((float(frame["timestamp_sec"]), point))
    return series


def motion_values(series: list[tuple[float, dict[str, float]]], scale: float | None) -> list[float]:
    values: list[float] = []
    for index in range(1, len(series)):
        values.append(normalized(point_distance(series[index - 1][1], series[index][1]), scale) or 0.0)
    return values


def coordinate_values(series: list[tuple[float, dict[str, float]]], axis: str) -> list[float]:
    return [point[axis] for _, point in series]


def value_range(values: list[float], scale: float | None = None) -> float | None:
    clean = [value for value in values if math.isfinite(value)]
    if not clean:
        return None
    return normalized(max(clean) - min(clean), scale)


def asymmetry(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return abs(left - right) / max(abs(left), abs(right), 1e-6)


def trunk_angle_deg(frame: dict[str, Any]) -> float | None:
    shoulders = frame_center(frame, "LEFT_SHOULDER", "RIGHT_SHOULDER")
    hips = frame_center(frame, "LEFT_HIP", "RIGHT_HIP")
    if not shoulders or not hips:
        return None
    dx = shoulders["x"] - hips["x"]
    dy = hips["y"] - shoulders["y"]
    if dy == 0:
        return 0.0
    return abs(math.degrees(math.atan2(dx, dy)))


def find_signal_peaks(values: list[float], fps: float) -> list[int]:
    if len(values) < 5:
        return []
    clean = [value for value in values if math.isfinite(value)]
    if len(clean) < 5:
        return []
    avg = mean(clean) or 0.0
    deviation = std(clean) or 0.0
    threshold = avg + deviation * 0.20
    min_distance = max(2, int(max(fps, 1.0) * 0.25))
    peaks: list[int] = []
    last_peak = -min_distance
    for index in range(1, len(values) - 1):
        if index - last_peak < min_distance:
            continue
        if values[index] > values[index - 1] and values[index] > values[index + 1]:
            if values[index] >= threshold:
                peaks.append(index)
                last_peak = index
    return peaks


def regularity_from_peaks(peaks: list[int], fps: float) -> tuple[float | None, float | None]:
    if len(peaks) < 3 or fps <= 0:
        return None, None
    intervals = [(peaks[index] - peaks[index - 1]) / fps for index in range(1, len(peaks))]
    interval_mean = mean(intervals)
    if not interval_mean or interval_mean <= 0:
        return None, None
    variability = (std(intervals) or 0.0) / interval_mean
    return max(0.0, min(1.0, 1.0 / (1.0 + variability))), variability


def smoothness_from_series(series: list[tuple[float, dict[str, float]]], scale: float | None) -> float | None:
    if len(series) < 4:
        return None
    motions = motion_values(series, scale)
    if len(motions) < 3:
        return None
    acceleration = [motions[index] - motions[index - 1] for index in range(1, len(motions))]
    jerk = [acceleration[index] - acceleration[index - 1] for index in range(1, len(acceleration))]
    jerk_std = std(jerk)
    if jerk_std is None:
        return None
    return max(0.0, min(1.0, 1.0 / (1.0 + jerk_std)))


def build_feature_row(
    metadata: dict[str, Any],
    frames: list[dict[str, Any]],
    quality: dict[str, Any],
    landmarks_file: Path | None,
    error: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {column: metadata.get(column, "") for column in ID_COLUMNS}
    row.update({column: quality.get(column, "") for column in QUALITY_COLUMNS})
    for column in FEATURE_COLUMNS:
        row[column] = None
    row["landmarks_file"] = project_relative(landmarks_file) if landmarks_file else ""
    row["error"] = error

    if error or not frames:
        return row

    scales = [frame_body_scale(frame) for frame in frames]
    body_scale = median([scale for scale in scales if scale and scale > 0]) or 1.0
    visual_fps = len(frames) / max(float(quality.get("duration_seconds") or 0.0), 1e-6)

    left_ankle = point_series(frames, "LEFT_ANKLE")
    right_ankle = point_series(frames, "RIGHT_ANKLE")
    left_knee = point_series(frames, "LEFT_KNEE")
    right_knee = point_series(frames, "RIGHT_KNEE")
    left_wrist = point_series(frames, "LEFT_WRIST")
    right_wrist = point_series(frames, "RIGHT_WRIST")
    hip_center = center_series(frames, "LEFT_HIP", "RIGHT_HIP")
    shoulder_center = center_series(frames, "LEFT_SHOULDER", "RIGHT_SHOULDER")

    core_motion: list[float] = []
    for landmark in CORE_LANDMARKS:
        core_motion.extend(motion_values(point_series(frames, landmark), body_scale))

    left_ankle_motion = mean(motion_values(left_ankle, body_scale))
    right_ankle_motion = mean(motion_values(right_ankle, body_scale))
    left_knee_motion = mean(motion_values(left_knee, body_scale))
    right_knee_motion = mean(motion_values(right_knee, body_scale))
    left_wrist_motion = mean(motion_values(left_wrist, body_scale))
    right_wrist_motion = mean(motion_values(right_wrist, body_scale))

    left_ankle_y = coordinate_values(left_ankle, "y")
    right_ankle_y = coordinate_values(right_ankle, "y")
    left_knee_y = coordinate_values(left_knee, "y")
    right_knee_y = coordinate_values(right_knee, "y")
    left_wrist_x = coordinate_values(left_wrist, "x")
    right_wrist_x = coordinate_values(right_wrist, "x")
    hip_x = coordinate_values(hip_center, "x")
    hip_y = coordinate_values(hip_center, "y")
    shoulder_x = coordinate_values(shoulder_center, "x")
    shoulder_y = coordinate_values(shoulder_center, "y")

    left_peaks = find_signal_peaks(left_ankle_y, visual_fps)
    right_peaks = find_signal_peaks(right_ankle_y, visual_fps)
    combined_peaks = sorted(left_peaks + right_peaks)
    step_count = len(combined_peaks)
    duration = float(quality.get("duration_seconds") or 0.0)
    cadence = (step_count / duration) * 60.0 if duration > 0 and step_count > 0 else None
    step_frequency = step_count / duration if duration > 0 and step_count > 0 else None
    step_regularity, rhythm_variability = regularity_from_peaks(combined_peaks, visual_fps)

    trunk_angles = [value for value in (trunk_angle_deg(frame) for frame in frames) if value is not None]
    shoulder_widths: list[float] = []
    hip_widths: list[float] = []
    for frame in frames:
        ls = frame_point(frame, "LEFT_SHOULDER")
        rs = frame_point(frame, "RIGHT_SHOULDER")
        lh = frame_point(frame, "LEFT_HIP")
        rh = frame_point(frame, "RIGHT_HIP")
        if ls and rs:
            shoulder_widths.append(normalized(point_distance(ls, rs), body_scale) or 0.0)
        if lh and rh:
            hip_widths.append(normalized(point_distance(lh, rh), body_scale) or 0.0)

    trunk_sway_values = []
    if shoulder_x and hip_x:
        for sx, hx in zip(shoulder_x, hip_x):
            trunk_sway_values.append(normalized(abs(sx - hx), body_scale) or 0.0)

    gait_variability_parts = [
        std(motion_values(left_ankle, body_scale)),
        std(motion_values(right_ankle, body_scale)),
        std(motion_values(hip_center, body_scale)),
    ]
    gait_variability = mean([value for value in gait_variability_parts if value is not None])
    trunk_sway_std = std(trunk_sway_values)
    trunk_inclination_std = std(trunk_angles)
    posture_stability = None
    if trunk_sway_std is not None or trunk_inclination_std is not None:
        posture_stability = 1.0 / (
            1.0 + (trunk_sway_std or 0.0) + ((trunk_inclination_std or 0.0) / 45.0)
        )

    if step_regularity is None:
        ankle_asymmetry = asymmetry(
            value_range(left_ankle_y, body_scale),
            value_range(right_ankle_y, body_scale),
        )
        step_regularity = None if ankle_asymmetry is None else max(0.0, 1.0 - ankle_asymmetry)

    row.update(
        {
            "body_motion_mean": mean(core_motion),
            "body_motion_std": std(core_motion),
            "hip_center_motion_mean": mean(motion_values(hip_center, body_scale)),
            "shoulder_center_motion_mean": mean(motion_values(shoulder_center, body_scale)),
            "vertical_motion_mean": mean(
                [abs(hip_y[index] - hip_y[index - 1]) / body_scale for index in range(1, len(hip_y))]
            )
            if len(hip_y) > 1
            else None,
            "horizontal_motion_mean": mean(
                [abs(hip_x[index] - hip_x[index - 1]) / body_scale for index in range(1, len(hip_x))]
            )
            if len(hip_x) > 1
            else None,
            "left_ankle_motion_mean": left_ankle_motion,
            "right_ankle_motion_mean": right_ankle_motion,
            "left_knee_motion_mean": left_knee_motion,
            "right_knee_motion_mean": right_knee_motion,
            "leg_motion_asymmetry": asymmetry(left_ankle_motion, right_ankle_motion),
            "ankle_vertical_range_left": value_range(left_ankle_y, body_scale),
            "ankle_vertical_range_right": value_range(right_ankle_y, body_scale),
            "ankle_vertical_asymmetry": asymmetry(
                value_range(left_ankle_y, body_scale),
                value_range(right_ankle_y, body_scale),
            ),
            "knee_vertical_range_left": value_range(left_knee_y, body_scale),
            "knee_vertical_range_right": value_range(right_knee_y, body_scale),
            "step_regularity_score": step_regularity,
            "left_wrist_motion_mean": left_wrist_motion,
            "right_wrist_motion_mean": right_wrist_motion,
            "arm_swing_mean": mean(
                [
                    value
                    for value in [
                        value_range(left_wrist_x, body_scale),
                        value_range(right_wrist_x, body_scale),
                    ]
                    if value is not None
                ]
            ),
            "arm_swing_asymmetry": asymmetry(
                value_range(left_wrist_x, body_scale),
                value_range(right_wrist_x, body_scale),
            ),
            "left_arm_range": value_range(left_wrist_x, body_scale),
            "right_arm_range": value_range(right_wrist_x, body_scale),
            "shoulder_width_mean": mean(shoulder_widths),
            "hip_width_mean": mean(hip_widths),
            "trunk_inclination_mean": mean(trunk_angles),
            "trunk_inclination_std": trunk_inclination_std,
            "trunk_sway_mean": mean(trunk_sway_values),
            "trunk_sway_std": trunk_sway_std,
            "posture_stability_score": posture_stability,
            "estimated_step_count": step_count,
            "estimated_cadence_steps_per_min": cadence,
            "step_frequency_hz": step_frequency,
            "gait_variability": gait_variability,
            "motion_smoothness": smoothness_from_series(hip_center, body_scale),
            "rhythm_variability": rhythm_variability,
        }
    )

    for column in FEATURE_COLUMNS:
        row[column] = finite_or_none(row.get(column))
    return row


def landmark_output_path(metadata: dict[str, Any], suffix: str = "landmarks") -> Path:
    # Se indexa por el nombre de archivo del video (unico por video). Antes se
    # usaba subject_id + sequence, lo que hacia colisionar los clips de Parkinson
    # de distinta severidad (001_PD_01_ML / 001_PD_01_MD / 001_PD_01_SV escribian
    # todos el mismo CSV). Al indexar por stem cada video conserva sus landmarks.
    stem = safe_stem(str(Path(str(metadata.get("filename", "") or metadata.get("video_path", "video"))).stem))
    if not stem or stem == "video":
        subject = safe_stem(str(metadata.get("subject_id") or "subject"))
        sequence = safe_stem(str(metadata.get("sequence") or "seq"))
        stem = f"{subject}_{sequence}"
    return LANDMARKS_DIR / f"{stem}_{suffix}.csv"


def import_pose_dependencies():
    try:
        import cv2  # type: ignore
        import mediapipe as mp  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias Python para vision por computadora. "
            "Instale requirements.txt antes de extraer landmarks."
        ) from exc
    return cv2, mp


def extract_video_features(
    metadata: dict[str, Any],
    frame_step: int = 3,
    force: bool = False,
    landmarks_path: Path | None = None,
    save_landmarks: bool = True,
) -> ExtractionResult:
    ensure_training_dirs()
    cv2, mp = import_pose_dependencies()
    frame_step = max(1, int(frame_step or 1))
    video_path = Path(str(metadata.get("video_path", "")))
    if not video_path.is_absolute():
        video_path = PROJECT_ROOT / video_path

    if landmarks_path is None:
        landmarks_path = landmark_output_path(metadata)

    if landmarks_path.exists() and not force:
        frames, quality = read_landmarks_for_features(landmarks_path)
        feature_row = build_feature_row(metadata, frames, quality, landmarks_path)
        return ExtractionResult(feature_row, quality, None)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        quality = empty_quality(error=True)
        error = f"No se pudo abrir el video: {project_relative(video_path)}"
        feature_row = build_feature_row(metadata, [], quality, None, error=error)
        return ExtractionResult(feature_row, quality, {**metadata, "error": error})

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = total_frames / fps if fps > 0 else 0.0

    mp_pose = mp.solutions.pose
    pose_landmark = mp_pose.PoseLandmark
    processed_frames = 0
    valid_pose_frames = 0
    rows: list[dict[str, Any]] = []
    feature_frames: list[dict[str, Any]] = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        frame_index = 0
        while capture.isOpened():
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_step != 0:
                frame_index += 1
                continue

            processed_frames += 1
            timestamp = frame_index / fps if fps > 0 else float(processed_frames - 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            frame_landmarks: dict[str, dict[str, float]] = {}
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                for name in SELECTED_LANDMARKS:
                    landmark = landmarks[pose_landmark[name].value]
                    point = {
                        "x": float(landmark.x),
                        "y": float(landmark.y),
                        "z": float(getattr(landmark, "z", 0.0)),
                        "visibility": float(getattr(landmark, "visibility", 0.0)),
                    }
                    frame_landmarks[name] = point
                    rows.append(
                        {
                            "frame_index": frame_index,
                            "timestamp_sec": round(timestamp, 6),
                            "landmark_name": name,
                            **point,
                        }
                    )

                core_visibility = mean(
                    frame_landmarks[name]["visibility"]
                    for name in CORE_LANDMARKS
                    if name in frame_landmarks
                )
                if core_visibility is not None and core_visibility >= 0.35:
                    valid_pose_frames += 1
                    feature_frames.append(
                        {
                            "frame_index": frame_index,
                            "timestamp_sec": timestamp,
                            "landmarks": frame_landmarks,
                        }
                    )

            frame_index += 1

    capture.release()

    pose_detection_rate = valid_pose_frames / processed_frames if processed_frames else 0.0
    quality_warning = "low_pose_detection_rate" if pose_detection_rate < 0.50 else ""
    quality = {
        "total_frames": total_frames,
        "processed_frames": processed_frames,
        "valid_pose_frames": valid_pose_frames,
        "pose_detection_rate": finite_or_none(pose_detection_rate, 6),
        "duration_seconds": finite_or_none(duration, 3),
        "fps": finite_or_none(fps, 3),
        "width": width,
        "height": height,
        "valid_for_training": pose_detection_rate >= 0.50,
        "quality_warning": quality_warning,
    }

    if save_landmarks:
        landmarks_path.parent.mkdir(parents=True, exist_ok=True)
        with landmarks_path.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=[
                    "frame_index",
                    "timestamp_sec",
                    "landmark_name",
                    "x",
                    "y",
                    "z",
                    "visibility",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    feature_row = build_feature_row(metadata, feature_frames, quality, landmarks_path)
    return ExtractionResult(feature_row, quality, None)


def empty_quality(error: bool = False) -> dict[str, Any]:
    return {
        "total_frames": 0,
        "processed_frames": 0,
        "valid_pose_frames": 0,
        "pose_detection_rate": 0.0,
        "duration_seconds": 0.0,
        "fps": 0.0,
        "width": 0,
        "height": 0,
        "valid_for_training": False,
        "quality_warning": "video_read_error" if error else "no_pose_frames",
    }


def read_landmarks_for_features(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frames_by_index: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as input_file:
        for row in csv.DictReader(input_file):
            frame_index = int(float(row["frame_index"]))
            frame = frames_by_index.setdefault(
                frame_index,
                {
                    "frame_index": frame_index,
                    "timestamp_sec": float(row.get("timestamp_sec") or 0.0),
                    "landmarks": {},
                },
            )
            frame["landmarks"][row["landmark_name"]] = {
                "x": float(row["x"]),
                "y": float(row["y"]),
                "z": float(row.get("z") or 0.0),
                "visibility": float(row.get("visibility") or 0.0),
            }

    frames = [
        frame
        for frame in sorted(frames_by_index.values(), key=lambda item: item["frame_index"])
        if all(name in frame["landmarks"] for name in CORE_LANDMARKS)
    ]
    total_frames = len(frames_by_index)
    valid_pose_frames = len(frames)
    duration = 0.0
    if frames_by_index:
        timestamps = [frame["timestamp_sec"] for frame in frames_by_index.values()]
        duration = max(timestamps) - min(timestamps)
    quality = {
        "total_frames": total_frames,
        "processed_frames": total_frames,
        "valid_pose_frames": valid_pose_frames,
        "pose_detection_rate": valid_pose_frames / total_frames if total_frames else 0.0,
        "duration_seconds": duration,
        "fps": total_frames / duration if duration > 0 else 0.0,
        "width": "",
        "height": "",
        "valid_for_training": (valid_pose_frames / total_frames) >= 0.50 if total_frames else False,
        "quality_warning": "" if total_frames and (valid_pose_frames / total_frames) >= 0.50 else "low_pose_detection_rate",
    }
    return frames, quality


def write_rows(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

