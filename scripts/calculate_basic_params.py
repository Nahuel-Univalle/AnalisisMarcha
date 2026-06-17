"""
Sprint 3 (base) + Sprint 4 Iteración 7 - Parámetros de marcha desde el CSV de pose
Autor: Jared Quinteros García

------------------------------------------------------------------------------
BASE (Sprint 3) — comportamiento original INTACTO:
    Lee outputs/pose_landmarks.csv (landmarks exportados) y calcula DOS medidas
    simples por frame:
      1. ankle_distance : distancia euclidiana entre tobillo izq. (27) y der. (28)
                          sobre (x, y) normalizados.
      2. hip_center_x   : centro horizontal de las caderas = promedio de x de
                          cadera izq. (23) y der. (24).
    Salida por frame: outputs/basic_gait_params.csv

------------------------------------------------------------------------------
SPRINT 4 - ITERACIÓN 7 (añadido, no rompe lo anterior):
    A partir de esas series por frame, estima parámetros básicos de marcha por
    VIDEO y los guarda en un CSV estructurado de dataset:
      - estimated_steps                 = nº de picos de separación de tobillos
      - cadence_steps_per_min           = pasos / duración * 60
      - average_step_length_normalized  = separación media de tobillos en los picos
      - estimated_velocity_normalized   = desplazamiento del centro de cadera / tiempo
    Salida por video: outputs/gait_basic_parameters.csv  (upsert por video_id)
    Categoría (control | parkinson | multiple_sclerosis | fall_risk) tomada de
    data/dataset_metadata.csv o del argumento --category.

    FÓRMULAS (todas NORMALIZADAS, ver LIMITACIÓN):
      duración_s          = (frame_max - frame_min) / fps
      estimated_steps     = picos en la señal ankle_distance (cada pico ≈ 1 paso)
      cadence_steps_min   = estimated_steps / duración_s * 60
      step_length_norm    = media de ankle_distance en los frames-pico
      velocity_norm       = |hip_center_x[fin] - hip_center_x[inicio]| / duración_s

    LIMITACIÓN: el video RGB monocular NO aporta escala real (metros) ni FPS dentro
    del CSV de landmarks. Por eso:
      * Las longitudes/velocidades son NORMALIZADAS (fracción del ancho/alto de
        imagen, 0–1), no metros ni m/s.
      * La cadencia depende del FPS; si no se conoce, se asume --fps 30 (configurable).
      * La velocidad usa el desplazamiento horizontal de la cadera; si la persona
        camina hacia la cámara o en el sitio, queda subestimada.

Uso (entorno Python 3.11):
    # comportamiento base (igual que en Sprint 3):
    .venv311\\Scripts\\python.exe scripts\\calculate_basic_params.py

    # con identificador, fps y categoría (recomendado para el dataset):
    .venv311\\Scripts\\python.exe scripts\\calculate_basic_params.py ^
        --video-id demo_walk_01 --fps 30 --category control

Entrada : outputs/pose_landmarks.csv
Salidas : outputs/basic_gait_params.csv      (por frame, base Sprint 3)
          outputs/gait_basic_parameters.csv   (por video, Iteración 7)
"""

import argparse
import csv
import math
import sys
from pathlib import Path

# Evita caracteres ilegibles (mojibake) con las tildes en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Rutas por defecto (relativas a la raíz del proyecto)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "outputs" / "pose_landmarks.csv"
PERFRAME_OUTPUT_CSV = PROJECT_ROOT / "outputs" / "basic_gait_params.csv"
SUMMARY_OUTPUT_CSV = PROJECT_ROOT / "outputs" / "gait_basic_parameters.csv"
METADATA_CSV = PROJECT_ROOT / "data" / "dataset_metadata.csv"

# Índices de landmarks de MediaPipe Pose que necesitamos
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
REQUIRED = (LEFT_HIP, RIGHT_HIP, LEFT_ANKLE, RIGHT_ANKLE)
# Hombros (opcionales): se usan para estimar la estabilidad del tronco (Iteración 8).
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12

# Las cuatro categorías oficiales del proyecto (Sprint 4 Iteración 7).
VALID_CATEGORIES = ("control", "parkinson", "multiple_sclerosis", "fall_risk")
DEFAULT_FPS = 30.0

SUMMARY_HEADER = [
    "video_id",
    "source_file",
    "category",
    "total_frames",
    "fps",
    "frames_with_pose",
    "estimated_steps",
    "cadence_steps_per_min",
    "average_step_length_normalized",
    "estimated_velocity_normalized",
    "symmetry",
    "stability",
    "gait_variability",
    "notes",
]


def count_step_peaks(values, min_distance=2):
    """Cuenta picos en una señal 1D (separación de tobillos por frame).

    Cada pico ≈ un paso: cuando un pie se adelanta, la distancia entre tobillos
    alcanza un máximo local. Umbral = media + 0.25 * desviación típica; se respeta
    una distancia mínima entre picos para no contar ruido como pasos.

    Devuelve (n_picos, [indices_de_picos]).
    """
    n = len(values)
    if n < 5:
        return 0, []

    mean_v = sum(values) / n
    var_v = sum((v - mean_v) ** 2 for v in values) / n
    std_v = math.sqrt(var_v)
    threshold = mean_v + 0.25 * std_v

    peaks = []
    last = -min_distance
    for i in range(1, n - 1):
        if (
            i - last >= min_distance
            and values[i] > values[i - 1]
            and values[i] > values[i + 1]
            and values[i] >= threshold
        ):
            peaks.append(i)
            last = i
    return len(peaks), peaks


# ---------------------------------------------------------------------------
#  Sprint 4 - Iteración 8: parámetros adicionales (simetría, estabilidad,
#  variabilidad). Todos NORMALIZADOS y orientativos (RGB sin escala real).
# ---------------------------------------------------------------------------
def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _std(values):
    """Desviación típica poblacional (0 si hay menos de 2 valores)."""
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)


def _ptp(values):
    """Amplitud (máximo - mínimo)."""
    return (max(values) - min(values)) if values else 0.0


def _clamp01(value):
    return max(0.0, min(1.0, value))


def trunk_angle_from(shoulder_center, hip_center):
    """Inclinación del tronco respecto a la vertical, en grados (>= 0)."""
    dx = shoulder_center[0] - hip_center[0]
    dy = hip_center[1] - shoulder_center[1]
    if dy == 0:
        return 0.0
    return abs(math.degrees(math.atan2(dx, dy)))


def compute_symmetry(left_ankle_y, right_ankle_y):
    """Simetría (0–1; 1 = más simétrico).

    Compara la amplitud de movimiento vertical de cada tobillo (cuánto se eleva
    cada pie). 1 = ambos pies se mueven por igual; valores menores = más asimetría.
    """
    amp_left = _ptp(left_ankle_y)
    amp_right = _ptp(right_ankle_y)
    denom = max(amp_left, amp_right, 1e-6)
    return _clamp01(1.0 - abs(amp_left - amp_right) / denom)


def compute_stability(trunk_angles, hip_center_y_values):
    """Estabilidad (0–1; 1 = más estable).

    Menos variación de la inclinación del tronco = más estable. Si no hay hombros
    visibles, se usa como reserva el bamboleo vertical del centro de cadera.
    """
    if len(trunk_angles) >= 2:
        return _clamp01(1.0 - _std(trunk_angles) / 25.0)
    return _clamp01(1.0 - 8.0 * _std(hip_center_y_values))


def compute_variability(ankle_distance_series):
    """Variabilidad (>= 0; mayor = más irregular).

    Coeficiente de variación de la separación entre tobillos (std / media). Mide la
    irregularidad de la zancada de un paso a otro.
    """
    mean_v = _mean(ankle_distance_series)
    if mean_v <= 1e-6:
        return 0.0
    return _std(ankle_distance_series) / mean_v


def resolve_category(video_id, source_file, explicit, metadata_path):
    """Resuelve la categoría del registro.

    Prioridad:
      1. Argumento explícito --category.
      2. data/dataset_metadata.csv (por video_id o por nombre de archivo).
      3. "unknown" si no se encuentra.

    Devuelve (categoria, nota_opcional).
    """
    if explicit:
        cat = explicit.strip().lower()
        note = "" if cat in VALID_CATEGORIES else f"categoria '{cat}' fuera de las 4 oficiales"
        return cat, note

    if metadata_path.exists():
        try:
            with open(metadata_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    rid = (row.get("video_id") or "").strip()
                    rpath = (row.get("file_path") or "").strip()
                    matches_id = bool(video_id) and rid == video_id
                    matches_file = (
                        bool(source_file)
                        and bool(rpath)
                        and Path(rpath).name == Path(source_file).name
                    )
                    if matches_id or matches_file:
                        cat = (row.get("category") or "").strip().lower()
                        if cat:
                            note = "" if cat in VALID_CATEGORIES else f"categoria '{cat}' fuera de las 4 oficiales"
                            return cat, note
        except Exception as exc:  # lectura defensiva: nunca debe tumbar el cálculo
            return "unknown", f"no se pudo leer metadata: {exc}"

    return "unknown", "categoria no encontrada (use --category o data/dataset_metadata.csv)"


def read_landmarks(input_csv):
    """Lee pose_landmarks.csv y devuelve (frames, ok, mensaje_error).

    frames = { frame_index: { landmark_index: (x, y) } }.
    """
    needed_cols = {"frame_index", "landmark_index", "x", "y"}
    frames = {}
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not needed_cols.issubset(set(reader.fieldnames)):
            return None, False, f"El CSV no tiene las columnas requeridas {sorted(needed_cols)}."
        for row in reader:
            try:
                fi = int(row["frame_index"])
                li = int(row["landmark_index"])
                x = float(row["x"])
                y = float(row["y"])
            except (TypeError, ValueError):
                continue
            frames.setdefault(fi, {})[li] = (x, y)
    return frames, True, ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parámetros básicos de marcha (Sprint 3 base + Sprint 4 Iteración 7)."
    )
    parser.add_argument("--input", default=str(INPUT_CSV), help="CSV de landmarks (pose_landmarks.csv).")
    parser.add_argument("--perframe-output", default=str(PERFRAME_OUTPUT_CSV), help="CSV por frame (base Sprint 3).")
    parser.add_argument("--summary-output", "--output", dest="summary_output", default=str(SUMMARY_OUTPUT_CSV), help="CSV por video (Iteración 7/8).")
    parser.add_argument("--metadata", default=str(METADATA_CSV), help="CSV de metadatos de categorías.")
    parser.add_argument("--video-id", default=None, help="Identificador del video para el dataset.")
    parser.add_argument("--source-file", default=None, help="Ruta/nombre del video original (informativo).")
    parser.add_argument(
        "--category",
        default=None,
        help="Categoría: control | parkinson | multiple_sclerosis | fall_risk.",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=DEFAULT_FPS,
        help=f"FPS del video (por defecto {DEFAULT_FPS}; aproximado si se desconoce).",
    )
    args = parser.parse_args()

    input_csv = Path(args.input)
    perframe_out = Path(args.perframe_output)
    summary_out = Path(args.summary_output)
    metadata_path = Path(args.metadata)

    print("=" * 60)
    print("  PARÁMETROS DE MARCHA - Sprint 3 base + Sprint 4 Iteración 7")
    print("=" * 60)
    print(f"CSV de entrada: {input_csv}")

    # 1. Validar que el CSV de entrada existe
    if not input_csv.exists():
        print("\n[ERROR] No existe el CSV de landmarks de entrada.")
        print("        Genera primero los landmarks con:")
        print("        .venv311\\Scripts\\python.exe scripts\\export_pose_csv.py <video> <max_frames>")
        return 1

    # 2. Leer el CSV y agrupar (x, y) por frame_index -> landmark_index
    frames, ok, error = read_landmarks(input_csv)
    if not ok:
        print(f"\n[ERROR] {error}")
        return 1

    # 3. Cálculo POR FRAME (base Sprint 3, comportamiento intacto)
    perframe_rows = []
    ankle_series = []  # serie de ankle_distance ordenada por frame
    hip_series = []    # [(frame_index, hip_center_x), ...]
    # Series adicionales para Iteración 8 (simetría, estabilidad, variabilidad)
    left_ankle_y_series = []
    right_ankle_y_series = []
    hip_y_series = []
    trunk_angle_series = []
    skipped = 0

    for frame_index in sorted(frames):
        landmarks = frames[frame_index]

        # Si al frame le falta alguno de los puntos requeridos, lo saltamos
        if not all(idx in landmarks for idx in REQUIRED):
            skipped += 1
            continue

        lx_ankle, ly_ankle = landmarks[LEFT_ANKLE]
        rx_ankle, ry_ankle = landmarks[RIGHT_ANKLE]
        lx_hip, ly_hip = landmarks[LEFT_HIP]
        rx_hip, ry_hip = landmarks[RIGHT_HIP]

        # ankle_distance: distancia euclidiana entre ambos tobillos
        ankle_distance = math.hypot(lx_ankle - rx_ankle, ly_ankle - ry_ankle)
        # hip_center: promedio de las caderas (x base Sprint 3; y para Iteración 8)
        hip_center_x = (lx_hip + rx_hip) / 2
        hip_center_y = (ly_hip + ry_hip) / 2

        perframe_rows.append(
            {
                "frame_index": frame_index,
                "ankle_distance": round(ankle_distance, 6),
                "hip_center_x": round(hip_center_x, 6),
            }
        )
        ankle_series.append(ankle_distance)
        hip_series.append((frame_index, hip_center_x))

        # Series Iteración 8
        left_ankle_y_series.append(ly_ankle)
        right_ankle_y_series.append(ry_ankle)
        hip_y_series.append(hip_center_y)
        if LEFT_SHOULDER in landmarks and RIGHT_SHOULDER in landmarks:
            ls = landmarks[LEFT_SHOULDER]
            rs = landmarks[RIGHT_SHOULDER]
            shoulder_center = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
            trunk_angle_series.append(
                trunk_angle_from(shoulder_center, (hip_center_x, hip_center_y))
            )

    print(f"Frames en el CSV       : {len(frames)}")
    print(f"Frames procesados      : {len(perframe_rows)}")
    print(f"Frames saltados        : {skipped} (sin los landmarks requeridos)")

    # 4. Si ningún frame tenía los puntos necesarios, no generamos CSV vacío
    if not perframe_rows:
        print("\n[FALLO] Ningún frame tenía los landmarks requeridos (23, 24, 27, 28).")
        print("        No se generó CSV para evitar un archivo vacío/engañoso.")
        return 1

    # 5. Escribir el CSV POR FRAME (base Sprint 3, mismo esquema de siempre)
    perframe_out.parent.mkdir(parents=True, exist_ok=True)
    with open(perframe_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_index", "ankle_distance", "hip_center_x"])
        writer.writeheader()
        writer.writerows(perframe_rows)
    print(f"\n[OK] Parámetros por frame -> {perframe_out}")

    # =====================================================================
    #  SPRINT 4 - ITERACIÓN 7: parámetros de marcha agregados por video
    # =====================================================================
    notes = []
    frames_with_pose = len(perframe_rows)
    frame_indices = [r["frame_index"] for r in perframe_rows]
    min_fi, max_fi = min(frame_indices), max(frame_indices)
    total_frames = max_fi + 1  # aprox.: índice de frame muestreado más alto + 1

    fps = args.fps if (args.fps and args.fps > 0) else DEFAULT_FPS
    if not (args.fps and args.fps > 0):
        notes.append(f"fps invalido; se asumio {DEFAULT_FPS}")

    # Duración cubierta por las muestras (span de frames / fps)
    span_frames = max_fi - min_fi
    duration_seconds = span_frames / fps if (fps > 0 and span_frames > 0) else 0.0

    if frames_with_pose < 5:
        notes.append("muy pocos frames con pose; cadencia/longitud poco fiables")

    # Pasos estimados = picos de separación de tobillos.
    # Distancia mínima entre picos = periodo refractario ~0.30 s entre pasos
    # (cota superior de cadencia ~200 pasos/min), ajustada a la densidad de muestreo
    # (mediana del salto entre frames). Evita contar ruido/oscilaciones como pasos.
    gaps = [frame_indices[i] - frame_indices[i - 1] for i in range(1, len(frame_indices))]
    frame_gap = max(1, sorted(gaps)[len(gaps) // 2]) if gaps else 1
    min_peak_distance = max(1, round((fps * 0.30) / frame_gap))
    estimated_steps, peak_idx = count_step_peaks(ankle_series, min_distance=min_peak_distance)

    # Cadencia (pasos/min)
    if duration_seconds > 0 and estimated_steps > 0:
        cadence = (estimated_steps / duration_seconds) * 60.0
    else:
        cadence = 0.0
        if duration_seconds <= 0:
            notes.append("duracion no determinable (span de frames o fps insuficiente)")
        elif estimated_steps == 0:
            notes.append("no se detectaron picos de paso (muestreo escaso o marcha poco visible)")

    # Longitud de paso normalizada = separación media de tobillos en los picos
    if peak_idx:
        avg_step_length = sum(ankle_series[i] for i in peak_idx) / len(peak_idx)
    else:
        avg_step_length = sum(ankle_series) / len(ankle_series)
        notes.append("sin picos claros; longitud de paso = separacion media de tobillos")

    # Velocidad normalizada = desplazamiento horizontal del centro de cadera / tiempo
    hip_xs = [hx for _, hx in hip_series]
    net_disp = abs(hip_xs[-1] - hip_xs[0])
    velocity = net_disp / duration_seconds if duration_seconds > 0 else 0.0
    if net_disp < 0.02:
        notes.append("desplazamiento de cadera muy bajo (marcha en sitio o hacia camara); velocidad subestimada")

    # --- Sprint 4 Iteración 8: parámetros adicionales (normalizados) ---
    symmetry = compute_symmetry(left_ankle_y_series, right_ankle_y_series)
    stability = compute_stability(trunk_angle_series, hip_y_series)
    gait_variability = compute_variability(ankle_series)
    if not trunk_angle_series:
        notes.append("hombros no visibles; estabilidad estimada por bamboleo de cadera")

    # Categoría (clasificación de datos en las 4 categorías oficiales)
    category, cat_note = resolve_category(args.video_id, args.source_file, args.category, metadata_path)
    if cat_note:
        notes.append(cat_note)

    video_id = args.video_id or (
        Path(args.source_file).stem if args.source_file else input_csv.stem
    )
    source_file = args.source_file or ""

    notes.append("valores normalizados (RGB monocular sin escala real; no son metros)")

    summary_row = {
        "video_id": video_id,
        "source_file": source_file,
        "category": category,
        "total_frames": total_frames,
        "fps": round(fps, 3),
        "frames_with_pose": frames_with_pose,
        "estimated_steps": estimated_steps,
        "cadence_steps_per_min": round(cadence, 3),
        "average_step_length_normalized": round(avg_step_length, 6),
        "estimated_velocity_normalized": round(velocity, 6),
        "symmetry": round(symmetry, 6),
        "stability": round(stability, 6),
        "gait_variability": round(gait_variability, 6),
        "notes": "; ".join(notes),
    }

    # 6. Upsert por video_id en el CSV de dataset (acumula varios videos)
    existing = []
    if summary_out.exists():
        try:
            with open(summary_out, newline="", encoding="utf-8") as f:
                existing = [r for r in csv.DictReader(f) if r.get("video_id") != video_id]
        except Exception:
            existing = []

    summary_out.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_HEADER)
        writer.writeheader()
        for r in existing:
            writer.writerow({k: r.get(k, "") for k in SUMMARY_HEADER})
        writer.writerow(summary_row)

    print("\n" + "-" * 60)
    print("RESUMEN ITERACIÓN 7 (por video)")
    print(f"  video_id              : {video_id}")
    print(f"  category              : {category}")
    print(f"  total_frames (aprox.) : {total_frames}")
    print(f"  fps                   : {fps}")
    print(f"  frames_with_pose      : {frames_with_pose}")
    print(f"  estimated_steps       : {estimated_steps}")
    print(f"  cadence_steps_per_min : {cadence:.2f}")
    print(f"  step_length_norm      : {avg_step_length:.4f}")
    print(f"  velocity_norm         : {velocity:.4f}")
    print(f"  symmetry              : {symmetry:.4f}")
    print(f"  stability             : {stability:.4f}")
    print(f"  gait_variability      : {gait_variability:.4f}")
    if summary_row["notes"]:
        print(f"  notes                 : {summary_row['notes']}")
    print(f"  CSV dataset           -> {summary_out}")
    print("-" * 60)
    print("\n[EXITO] Parámetros de marcha calculados y guardados correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
