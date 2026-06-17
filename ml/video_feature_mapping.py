VIDEO_COMPATIBLE_FEATURE_COLUMNS = [
    "estimated_cadence_steps_per_min",
    "mean_force_asymmetry_index",
    "left_contact_ratio",
    "right_contact_ratio",
    "double_support_ratio",
    "mean_left_stance_time_sec",
    "mean_right_stance_time_sec",
]

VIDEO_FEATURE_MAPPING = {
    "estimated_cadence_steps_per_min": {
        "video_key": "cadence_visual",
        "fallback_keys": ["estimated_cadence_steps_per_min"],
        "description": "Cadencia estimada desde oscilaciones visuales de tobillos.",
    },
    "mean_force_asymmetry_index": {
        "video_key": "leg_asymmetry_visual",
        "fallback_keys": ["left_right_asymmetry"],
        "description": "Proxy visual de asimetria entre piernas; no es fuerza plantar.",
    },
    "left_contact_ratio": {
        "video_key": "estimated_left_contact_proxy",
        "fallback_keys": [],
        "description": "Proporcion de cuadros con proxy visual de contacto del pie izquierdo.",
    },
    "right_contact_ratio": {
        "video_key": "estimated_right_contact_proxy",
        "fallback_keys": [],
        "description": "Proporcion de cuadros con proxy visual de contacto del pie derecho.",
    },
    "double_support_ratio": {
        "video_key": "estimated_double_support_proxy",
        "fallback_keys": [],
        "description": "Proxy visual de soporte doble, derivado de contacto simultaneo.",
    },
    "mean_left_stance_time_sec": {
        "video_key": "mean_left_stance_time_proxy",
        "fallback_keys": [],
        "description": "Proxy visual de tiempo medio de apoyo izquierdo.",
    },
    "mean_right_stance_time_sec": {
        "video_key": "mean_right_stance_time_proxy",
        "fallback_keys": [],
        "description": "Proxy visual de tiempo medio de apoyo derecho.",
    },
}

MIN_REQUIRED_VIDEO_FEATURES = 5

