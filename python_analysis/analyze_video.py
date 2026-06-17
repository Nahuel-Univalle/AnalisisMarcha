import argparse
import importlib
import json
import sys
from math import atan2, degrees
from pathlib import Path


MAX_FRAMES_ANALYZED = 300
LOW_POSE_RATE = 0.40


def write_json(payload, output_path=None):
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(text, encoding="utf-8")
    print(text)


def error_payload(message, warnings=None):
    return {
        "success": False,
        "error": message,
        "warnings": warnings or [],
    }


def import_dependencies():
    modules = {}
    missing = []

    for module_name in ("cv2", "mediapipe", "numpy", "pandas"):
        try:
            modules[module_name] = importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)

    return modules, missing


def nullable_float(value, digits=6):
    if value is None:
        return None
    try:
        if value != value:
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def point(landmarks, pose_landmark, name):
    landmark = landmarks[pose_landmark[name].value]
    return {
        "x": float(landmark.x),
        "y": float(landmark.y),
        "z": float(getattr(landmark, "z", 0.0)),
        "visibility": float(getattr(landmark, "visibility", 0.0)),
    }


def center(left, right):
    return {
        "x": (left["x"] + right["x"]) / 2,
        "y": (left["y"] + right["y"]) / 2,
    }


def mean_visibility(*points):
    if not points:
        return 0.0
    return sum(item["visibility"] for item in points) / len(points)


def trunk_angle(shoulder_center, hip_center):
    dx = shoulder_center["x"] - hip_center["x"]
    dy = hip_center["y"] - shoulder_center["y"]
    if dy == 0:
        return 0.0
    return abs(degrees(atan2(dx, dy)))


def signal_peaks(values, np, min_distance=1):
    if len(values) < 5:
        return 0

    mean_value = float(np.mean(values))
    std_value = float(np.std(values))
    threshold = mean_value + (std_value * 0.25)
    peaks = 0
    last_peak_index = -min_distance

    for index in range(1, len(values) - 1):
        if (
            index - last_peak_index >= min_distance
            and values[index] > values[index - 1]
            and values[index] > values[index + 1]
            and values[index] >= threshold
        ):
            peaks += 1
            last_peak_index = index

    return peaks


def build_signals(metrics):
    signals = []

    if metrics["pose_detection_rate"] < LOW_POSE_RATE:
        signals.append("pose_insuficiente")
    if metrics["left_right_asymmetry"] is not None and metrics["left_right_asymmetry"] > 0.18:
        signals.append("asimetria_lateral_orientativa")
    if metrics["trunk_stability_score"] is not None and metrics["trunk_stability_score"] < 0.55:
        signals.append("estabilidad_tronco_reducida")
    if metrics["arm_swing_asymmetry"] is not None and metrics["arm_swing_asymmetry"] > 0.2:
        signals.append("balanceo_brazos_asimetrico")
    if metrics["movement_variability"] is not None and metrics["movement_variability"] > 0.08:
        signals.append("variabilidad_movimiento_alta")

    return signals


def make_writer(cv2, output_video, width, height, fps):
    output_path = Path(output_video)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for codec in ("avc1", "mp4v", "H264"):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(str(output_path), fourcc, max(fps, 1.0), (width, height))
        if writer.isOpened():
            return writer
        writer.release()

    return cv2.VideoWriter(str(output_path), 0, max(fps, 1.0), (width, height))


def analyze_video(video_path, output_video):
    modules, missing = import_dependencies()
    if missing:
        return error_payload(
            "Faltan dependencias Python para análisis de video: "
            + ", ".join(missing)
            + ". Instale el entorno con: pip install -r requirements.txt",
            warnings=[],
        )

    cv2 = modules["cv2"]
    mp = modules["mediapipe"]
    np = modules["numpy"]

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return error_payload(
            "No se pudo abrir el video. Verifique que el archivo exista, sea un video válido y no esté dañado.",
            warnings=[],
        )

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_seconds = frame_count / fps if fps > 0 else 0.0
    stride = max(1, frame_count // MAX_FRAMES_ANALYZED) if frame_count > MAX_FRAMES_ANALYZED else 1
    output_fps = fps / stride if fps > 0 else 10.0

    writer = make_writer(cv2, output_video, width, height, output_fps)
    if not writer.isOpened():
        capture.release()
        return error_payload(
            "No se pudo crear el video procesado con puntos clave.",
            warnings=[],
        )

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose_landmark = mp_pose.PoseLandmark
    landmark_spec = mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=4, circle_radius=4)
    connection_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=3, circle_radius=2)

    frames_analyzed = 0
    frames_with_pose = 0
    ankle_distances = []
    hip_centers = []
    trunk_angles = []
    left_wrist_offsets = []
    right_wrist_offsets = []
    left_ankle_y_values = []
    right_ankle_y_values = []
    left_ankle_x_values = []
    right_ankle_x_values = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        frame_index = 0
        while capture.isOpened() and frames_analyzed < MAX_FRAMES_ANALYZED:
            ok, frame = capture.read()
            if not ok:
                break

            if frame_index % stride != 0:
                frame_index += 1
                continue

            frames_analyzed += 1
            annotated = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    annotated,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=landmark_spec,
                    connection_drawing_spec=connection_spec,
                )

                landmarks = results.pose_landmarks.landmark
                left_ankle = point(landmarks, pose_landmark, "LEFT_ANKLE")
                right_ankle = point(landmarks, pose_landmark, "RIGHT_ANKLE")
                left_hip = point(landmarks, pose_landmark, "LEFT_HIP")
                right_hip = point(landmarks, pose_landmark, "RIGHT_HIP")
                left_shoulder = point(landmarks, pose_landmark, "LEFT_SHOULDER")
                right_shoulder = point(landmarks, pose_landmark, "RIGHT_SHOULDER")
                left_wrist = point(landmarks, pose_landmark, "LEFT_WRIST")
                right_wrist = point(landmarks, pose_landmark, "RIGHT_WRIST")

                core_visibility = mean_visibility(
                    left_ankle,
                    right_ankle,
                    left_hip,
                    right_hip,
                    left_shoulder,
                    right_shoulder,
                )

                if core_visibility >= 0.35:
                    frames_with_pose += 1
                    hip_center = center(left_hip, right_hip)
                    shoulder_center = center(left_shoulder, right_shoulder)
                    hip_centers.append(hip_center)
                    ankle_distances.append(abs(left_ankle["x"] - right_ankle["x"]))
                    left_ankle_y_values.append(left_ankle["y"])
                    right_ankle_y_values.append(right_ankle["y"])
                    left_ankle_x_values.append(left_ankle["x"])
                    right_ankle_x_values.append(right_ankle["x"])
                    trunk_angles.append(trunk_angle(shoulder_center, hip_center))
                    left_wrist_offsets.append(left_wrist["x"] - left_shoulder["x"])
                    right_wrist_offsets.append(right_wrist["x"] - right_shoulder["x"])

            writer.write(annotated)
            frame_index += 1

    capture.release()
    writer.release()

    ankle_values = np.array(ankle_distances, dtype=float)
    trunk_values = np.array(trunk_angles, dtype=float)
    left_wrist_values = np.array(left_wrist_offsets, dtype=float)
    right_wrist_values = np.array(right_wrist_offsets, dtype=float)
    left_ankle_y = np.array(left_ankle_y_values, dtype=float)
    right_ankle_y = np.array(right_ankle_y_values, dtype=float)
    left_ankle_x = np.array(left_ankle_x_values, dtype=float)
    right_ankle_x = np.array(right_ankle_x_values, dtype=float)
    hip_y_values = np.array([item["y"] for item in hip_centers], dtype=float)
    hip_x_values = np.array([item["x"] for item in hip_centers], dtype=float)

    pose_detection_rate = frames_with_pose / frames_analyzed if frames_analyzed else 0.0
    hip_variability = None
    if len(hip_centers) > 1:
        hip_variability = float(np.std(hip_y_values) + np.std(hip_x_values))

    ankle_mean = float(np.mean(ankle_values)) if len(ankle_values) else None
    ankle_std = float(np.std(ankle_values)) if len(ankle_values) else None
    left_swing = float(np.ptp(left_wrist_values)) if len(left_wrist_values) > 1 else None
    right_swing = float(np.ptp(right_wrist_values)) if len(right_wrist_values) > 1 else None

    arm_swing_asymmetry = None
    if left_swing is not None and right_swing is not None:
        arm_swing_asymmetry = abs(left_swing - right_swing) / max(left_swing, right_swing, 0.001)

    cadence = None
    if duration_seconds > 0 and len(ankle_values) >= 5:
        # Cadencia (Sprint 4 Iteración 7): cada pico de la separación entre tobillos
        # equivale a ~1 paso. La distancia mínima entre picos es un periodo refractario
        # de ~0.30 s (cota superior ~200 pasos/min) escalado a la tasa efectiva de
        # muestreo, para no contar ruido/oscilaciones como pasos. Esto evita cadencias
        # irreales (p. ej. 452) que el frontend descartaba por estar fuera de [40, 220].
        analyzed_fps = len(ankle_values) / duration_seconds
        min_peak_distance = max(2, int(round(analyzed_fps * 0.30)))
        step_events = signal_peaks(ankle_values, np, min_peak_distance)
        cadence = (step_events / duration_seconds) * 60

    def contact_proxy(ankle_y):
        if len(ankle_y) < 6:
            return None, None

        velocity = np.abs(np.diff(ankle_y, prepend=ankle_y[0]))
        low_motion_threshold = float(np.percentile(velocity, 45))
        low_position_threshold = float(np.percentile(ankle_y, 55))
        contact = (ankle_y >= low_position_threshold) & (velocity <= low_motion_threshold)
        return contact, float(np.mean(contact))

    left_contact_mask, left_contact_ratio = contact_proxy(left_ankle_y)
    right_contact_mask, right_contact_ratio = contact_proxy(right_ankle_y)
    double_support_ratio = None
    if left_contact_mask is not None and right_contact_mask is not None:
        double_support_ratio = float(np.mean(left_contact_mask & right_contact_mask))

    left_stance_time = None
    right_stance_time = None
    if duration_seconds > 0 and len(left_ankle_y) > 0:
        frame_duration = duration_seconds / max(len(left_ankle_y), 1)
        if left_contact_mask is not None:
            left_stance_time = float(np.mean(left_contact_mask) * frame_duration)
        if right_contact_mask is not None:
            right_stance_time = float(np.mean(right_contact_mask) * frame_duration)

    step_symmetry_visual = None
    leg_asymmetry_visual = None
    if left_contact_ratio is not None and right_contact_ratio is not None:
        leg_asymmetry_visual = abs(left_contact_ratio - right_contact_ratio) / max(
            left_contact_ratio,
            right_contact_ratio,
            0.001,
        )
        step_symmetry_visual = max(0.0, min(1.0, 1.0 - leg_asymmetry_visual))

    ankle_path_variability = None
    if len(left_ankle_x) > 2 and len(right_ankle_x) > 2:
        ankle_path_variability = float(
            np.std(np.diff(left_ankle_x)) + np.std(np.diff(right_ankle_x))
        )

    posture_inclination = float(np.mean(trunk_values)) if len(trunk_values) else None
    trunk_stability_score = None
    if len(trunk_values) > 1:
        trunk_stability_score = max(0.0, min(1.0, 1.0 - (float(np.std(trunk_values)) / 25)))

    movement_variability = None
    if ankle_std is not None and hip_variability is not None:
        movement_variability = ankle_std + hip_variability

    gait_variability = movement_variability
    if ankle_path_variability is not None:
        gait_variability = (
            ankle_path_variability
            if gait_variability is None
            else float((gait_variability + ankle_path_variability) / 2)
        )

    movement_regularity = None
    if gait_variability is not None:
        movement_regularity = max(0.0, min(1.0, 1.0 - (gait_variability * 4)))

    speed_proxy = None
    if hip_variability is not None and duration_seconds > 0:
        speed_proxy = hip_variability / duration_seconds

    metrics = {
        "pose_detection_rate": nullable_float(pose_detection_rate),
        "estimated_cadence_steps_per_min": nullable_float(cadence),
        "cadence_visual": nullable_float(cadence),
        "gait_speed_proxy": nullable_float(speed_proxy),
        "ankle_distance_mean": nullable_float(ankle_mean),
        "ankle_distance_std": nullable_float(ankle_std),
        "hip_center_variability": nullable_float(hip_variability),
        "left_right_asymmetry": nullable_float(ankle_std),
        "step_symmetry_visual": nullable_float(step_symmetry_visual),
        "leg_asymmetry_visual": nullable_float(leg_asymmetry_visual),
        "trunk_stability_score": nullable_float(trunk_stability_score),
        "trunk_stability": nullable_float(trunk_stability_score),
        "arm_swing_left": nullable_float(left_swing),
        "arm_swing_right": nullable_float(right_swing),
        "arm_swing_asymmetry": nullable_float(arm_swing_asymmetry),
        "posture_inclination": nullable_float(posture_inclination),
        "movement_variability": nullable_float(movement_variability),
        "gait_variability": nullable_float(gait_variability),
        "movement_regularity": nullable_float(movement_regularity),
        "estimated_double_support_proxy": nullable_float(double_support_ratio),
        "estimated_left_contact_proxy": nullable_float(left_contact_ratio),
        "estimated_right_contact_proxy": nullable_float(right_contact_ratio),
        "mean_left_stance_time_proxy": nullable_float(left_stance_time),
        "mean_right_stance_time_proxy": nullable_float(right_stance_time),
    }

    warnings = [
        "Resultado orientativo: no constituye diagnóstico médico y requiere valoración profesional."
    ]
    if pose_detection_rate < LOW_POSE_RATE:
        warnings.insert(
            0,
            "La detección de pose fue baja. El resultado puede no ser confiable. Se recomienda subir un video con cuerpo completo, buena iluminación y cámara estable.",
        )

    return {
        "success": True,
        "video_file": str(video_path),
        "annotated_video_file": str(output_video),
        "duration_seconds": nullable_float(duration_seconds, 3),
        "fps": nullable_float(fps, 3),
        "width": width,
        "height": height,
        "total_frames": frame_count,
        "sampling_stride": stride,
        "frames_analyzed": frames_analyzed,
        "frames_with_pose": frames_with_pose,
        **metrics,
        "signals": build_signals(metrics),
        "warnings": warnings,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Análisis orientativo de marcha humana desde video."
    )
    parser.add_argument("--video", required=True, help="Ruta del archivo de video a analizar.")
    parser.add_argument(
        "--output-json",
        "--output",
        dest="output_json",
        help="Ruta del archivo JSON de salida.",
    )
    parser.add_argument(
        "--output-video",
        help="Ruta del video anotado con landmarks.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    video_path = Path(args.video)
    output_video = Path(args.output_video) if args.output_video else None

    if not video_path.exists():
        payload = error_payload(f"No se encontró el video: {video_path}", warnings=[])
        write_json(payload, args.output_json)
        return 1

    if not output_video:
        payload = error_payload("Debe proporcionar --output-video para guardar el video procesado.", warnings=[])
        write_json(payload, args.output_json)
        return 1

    try:
        payload = analyze_video(video_path, output_video)
        write_json(payload, args.output_json)
        return 0 if payload.get("success") else 1
    except Exception as exc:
        payload = error_payload(f"No se pudo completar el análisis de video: {exc}", warnings=[])
        write_json(payload, args.output_json)
        return 1


if __name__ == "__main__":
    sys.exit(main())
