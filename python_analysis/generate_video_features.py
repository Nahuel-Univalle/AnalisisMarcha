def nullable_float(value):
    if value is None:
        return None
    try:
        if value != value:
            return None
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def signal_peaks(values, np):
    if len(values) < 5:
        return 0

    mean_value = float(np.mean(values))
    std_value = float(np.std(values))
    threshold = mean_value + (std_value * 0.25)
    peaks = 0

    for index in range(1, len(values) - 1):
        if (
            values[index] > values[index - 1]
            and values[index] > values[index + 1]
            and values[index] >= threshold
        ):
            peaks += 1

    return peaks


def build_signals(metrics):
    signals = []

    if metrics["pose_detection_rate"] is not None and metrics["pose_detection_rate"] < 0.35:
        signals.append("pose_insuficiente")

    if (
        metrics["left_right_asymmetry"] is not None
        and metrics["left_right_asymmetry"] > 0.18
    ):
        signals.append("asimetria_lateral_orientativa")

    if (
        metrics["trunk_stability_score"] is not None
        and metrics["trunk_stability_score"] < 0.55
    ):
        signals.append("estabilidad_tronco_reducida")

    if (
        metrics["arm_swing_asymmetry"] is not None
        and metrics["arm_swing_asymmetry"] > 0.2
    ):
        signals.append("balanceo_brazos_asimetrico")

    if (
        metrics["movement_variability"] is not None
        and metrics["movement_variability"] > 0.08
    ):
        signals.append("variabilidad_movimiento_alta")

    return signals


def generate_features(series, np):
    ankle_distances = series["ankle_distances"]
    trunk_angles = series["trunk_angles"]
    left_wrist_offsets = series["left_wrist_offsets"]
    right_wrist_offsets = series["right_wrist_offsets"]
    hip_centers = series["hip_centers"]
    frames_analyzed = series["frames_analyzed"]
    frames_with_pose = series["frames_with_pose"]
    duration_seconds = series["duration_seconds"]

    pose_detection_rate = (
        frames_with_pose / frames_analyzed if frames_analyzed > 0 else 0.0
    )

    hip_y_values = np.array([point["y"] for point in hip_centers], dtype=float)
    hip_x_values = np.array([point["x"] for point in hip_centers], dtype=float)
    hip_variability = None
    if len(hip_centers) > 1:
        hip_variability = float(np.std(hip_y_values) + np.std(hip_x_values))

    ankle_mean = float(np.mean(ankle_distances)) if len(ankle_distances) else None
    ankle_std = float(np.std(ankle_distances)) if len(ankle_distances) else None
    left_swing = (
        float(np.ptp(left_wrist_offsets)) if len(left_wrist_offsets) > 1 else None
    )
    right_swing = (
        float(np.ptp(right_wrist_offsets)) if len(right_wrist_offsets) > 1 else None
    )
    arm_swing_asymmetry = None
    if left_swing is not None and right_swing is not None:
        denominator = max(left_swing, right_swing, 0.001)
        arm_swing_asymmetry = abs(left_swing - right_swing) / denominator

    cadence = None
    if duration_seconds > 0 and len(ankle_distances) >= 5:
        peaks = signal_peaks(ankle_distances, np)
        cadence = (peaks * 2 / duration_seconds) * 60

    posture_inclination = (
        float(np.mean(trunk_angles)) if len(trunk_angles) else None
    )
    trunk_stability_score = None
    if len(trunk_angles) > 1:
        trunk_stability_score = max(0.0, min(1.0, 1.0 - (float(np.std(trunk_angles)) / 25)))

    movement_variability = None
    if ankle_std is not None and hip_variability is not None:
        movement_variability = ankle_std + hip_variability

    speed_proxy = None
    if hip_variability is not None and duration_seconds > 0:
        speed_proxy = hip_variability / duration_seconds

    metrics = {
        "estimated_cadence_steps_per_min": nullable_float(cadence),
        "gait_speed_proxy": nullable_float(speed_proxy),
        "ankle_distance_mean": nullable_float(ankle_mean),
        "ankle_distance_std": nullable_float(ankle_std),
        "hip_center_variability": nullable_float(hip_variability),
        "left_right_asymmetry": nullable_float(ankle_std),
        "trunk_stability_score": nullable_float(trunk_stability_score),
        "arm_swing_left": nullable_float(left_swing),
        "arm_swing_right": nullable_float(right_swing),
        "arm_swing_asymmetry": nullable_float(arm_swing_asymmetry),
        "posture_inclination": nullable_float(posture_inclination),
        "movement_variability": nullable_float(movement_variability),
        "pose_detection_rate": nullable_float(pose_detection_rate),
    }

    metrics["signals"] = build_signals(metrics)
    return metrics
