"""
Nucleo del pipeline de Deep Learning para analisis de marcha.

Contiene TODO lo compartido entre preparacion de dataset, entrenamiento,
evaluacion e inferencia, de modo que el video nuevo pase EXACTAMENTE por el
mismo preprocesamiento que se uso al entrenar:

    video -> pose (MediaPipe) -> landmarks por frame -> normalizacion
          -> secuencia temporal de tamano fijo (+ velocidades)
          -> [ rama temporal CNN ]  +  [ rama de 36 features de marcha ]
          -> cabeza de fusion -> softmax (4 clases)

Clases: normal | parkinson | esclerosis_multiple | riesgo_caida

Este modulo NO elimina las 36 caracteristicas de marcha existentes: las usa
como segunda rama (informacion complementaria) del modelo profundo, y ademas
las expone para el informe medico.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# --- imports del pipeline historico (mismo directorio padre) -----------------
_PARENT = Path(__file__).resolve().parents[1]
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from video_training_common import (  # noqa: E402
    CLASS_HUMAN_LABEL,
    CLASS_NAMES,
    CLASS_TO_LABEL,
    CORE_LANDMARKS,
    FEATURE_COLUMNS,
    LABEL_TO_CLASS,
    NO_DIAGNOSIS_NOTE,
    NUM_CLASSES,
    PROJECT_ROOT,
    SELECTED_LANDMARKS,
    build_feature_row,
    read_landmarks_for_features,
)

# ---------------------------------------------------------------------------
#  Rutas
# ---------------------------------------------------------------------------
DEEP_DATA_DIR = PROJECT_ROOT / "data" / "video_training" / "deep"
DATASET_PATH = DEEP_DATA_DIR / "dataset.npz"
DATASET_META_PATH = DEEP_DATA_DIR / "dataset_meta.json"
OOF_PATH = DEEP_DATA_DIR / "oof_predictions.npz"

MODEL_DIR = PROJECT_ROOT / "models" / "gait_deep"
MODEL_WEIGHTS_PATH = MODEL_DIR / "gait_deep_model.pt"
MODEL_CONFIG_PATH = MODEL_DIR / "gait_deep_config.json"
FEATURE_SCALER_PATH = MODEL_DIR / "gait_deep_feature_scaler.json"
LABEL_MAP_PATH = MODEL_DIR / "gait_deep_label_map.json"
CV_METRICS_PATH = MODEL_DIR / "gait_deep_cv_metrics.json"
TRAINING_HISTORY_PATH = MODEL_DIR / "gait_deep_training_history.json"
EVAL_REPORT_JSON_PATH = MODEL_DIR / "gait_deep_evaluation_report.json"
EVAL_REPORT_MD_PATH = MODEL_DIR / "gait_deep_evaluation_report.md"
PLOTS_DIR = MODEL_DIR / "plots"

MANIFEST_PATH = PROJECT_ROOT / "data" / "video_training" / "manifest.csv"

# ---------------------------------------------------------------------------
#  Hiperparametros de la representacion temporal
# ---------------------------------------------------------------------------
SEQUENCE_LENGTH = 96          # frames tras remuestreo temporal
MIN_VALID_FRAMES = 12         # menos que esto -> clip no utilizable
FRAME_STEP = 2                # submuestreo al leer el video (coincide con 02_)
MIN_LANDMARK_VISIBILITY = 0.2
SEED = 42

# Canales: (x, y) normalizados por 17 landmarks + sus velocidades (delta t).
POSITION_CHANNELS = [f"{name}_{axis}" for name in SELECTED_LANDMARKS for axis in ("x", "y")]
VELOCITY_CHANNELS = [f"{name}_v{axis}" for name in SELECTED_LANDMARKS for axis in ("x", "y")]
CHANNEL_NAMES = POSITION_CHANNELS + VELOCITY_CHANNELS
NUM_CHANNELS = len(CHANNEL_NAMES)  # 68

# Pares izquierda/derecha para el espejo horizontal (augmentation en train).
_LR_LANDMARK_PAIRS = [
    ("LEFT_SHOULDER", "RIGHT_SHOULDER"),
    ("LEFT_ELBOW", "RIGHT_ELBOW"),
    ("LEFT_WRIST", "RIGHT_WRIST"),
    ("LEFT_HIP", "RIGHT_HIP"),
    ("LEFT_KNEE", "RIGHT_KNEE"),
    ("LEFT_ANKLE", "RIGHT_ANKLE"),
    ("LEFT_HEEL", "RIGHT_HEEL"),
    ("LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX"),
]

_FEATURE_LR_PAIRS = [
    ("left_ankle_motion_mean", "right_ankle_motion_mean"),
    ("left_knee_motion_mean", "right_knee_motion_mean"),
    ("ankle_vertical_range_left", "ankle_vertical_range_right"),
    ("knee_vertical_range_left", "knee_vertical_range_right"),
    ("left_wrist_motion_mean", "right_wrist_motion_mean"),
    ("left_arm_range", "right_arm_range"),
]

# Concepto de marcha -> features que lo respaldan (para el informe medico).
GAIT_CONCEPTS: dict[str, dict[str, Any]] = {
    "velocidad": {
        "label": "Velocidad de desplazamiento",
        "features": ["horizontal_motion_mean", "hip_center_motion_mean"],
        "higher_is": "mayor desplazamiento observado",
    },
    "cadencia": {
        "label": "Cadencia (pasos por minuto)",
        "features": ["estimated_cadence_steps_per_min", "step_frequency_hz"],
        "higher_is": "mas pasos por minuto",
    },
    "simetria": {
        "label": "Simetria izquierda/derecha",
        "features": ["leg_motion_asymmetry", "ankle_vertical_asymmetry", "arm_swing_asymmetry"],
        "higher_is": "mayor asimetria (peor)",
    },
    "estabilidad": {
        "label": "Estabilidad postural",
        "features": ["posture_stability_score", "trunk_sway_std"],
        "higher_is": "score alto = mas estable; sway alto = menos estable",
    },
    "variabilidad": {
        "label": "Variabilidad de la marcha",
        "features": ["gait_variability", "rhythm_variability"],
        "higher_is": "mayor variabilidad/irregularidad",
    },
    "movimiento_brazos": {
        "label": "Movimiento de brazos",
        "features": ["arm_swing_mean", "left_arm_range", "right_arm_range"],
        "higher_is": "mayor balanceo de brazos",
    },
    "amplitud_movimiento": {
        "label": "Amplitud de movimiento de piernas",
        "features": [
            "ankle_vertical_range_left",
            "ankle_vertical_range_right",
            "knee_vertical_range_left",
            "knee_vertical_range_right",
        ],
        "higher_is": "mayor amplitud de zancada",
    },
    "coordinacion": {
        "label": "Coordinacion y suavidad",
        "features": ["motion_smoothness", "step_regularity_score"],
        "higher_is": "score alto = mas coordinado/regular",
    },
    "postura": {
        "label": "Postura del tronco",
        "features": ["trunk_inclination_mean", "trunk_inclination_std"],
        "higher_is": "mayor inclinacion / mas variacion postural",
    },
    "parametros_temporales": {
        "label": "Parametros temporales de la marcha",
        "features": ["estimated_step_count", "step_frequency_hz", "rhythm_variability"],
        "higher_is": "descriptores temporales del ciclo de marcha",
    },
}


# ---------------------------------------------------------------------------
#  Lectura y normalizacion de landmarks -> secuencia temporal
# ---------------------------------------------------------------------------
def _raw_point(frame: dict[str, Any], name: str) -> tuple[float, float] | None:
    """Posicion (x, y) del landmark si la clave existe. NO filtra por visibility:
    la fiabilidad de 'visibility' de MediaPipe es baja en video domestico y
    descartar frames por ese valor vaciaba clips validos."""
    point = frame.get("landmarks", {}).get(name)
    if not point:
        return None
    try:
        return float(point["x"]), float(point["y"])
    except (KeyError, TypeError, ValueError):
        return None


def _center(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0


def _interpolate_nan_columns(matrix: np.ndarray) -> np.ndarray:
    """Rellena NaN por columna con interpolacion lineal temporal (extremos = vecino)."""
    out = matrix.copy()
    n = out.shape[0]
    x = np.arange(n)
    for col in range(out.shape[1]):
        column = out[:, col]
        good = np.isfinite(column)
        if good.all():
            continue
        if not good.any():
            out[:, col] = 0.0
            continue
        out[:, col] = np.interp(x, x[good], column[good])
    return out


def frames_to_sequence(frames: list[dict[str, Any]]) -> tuple[np.ndarray | None, float, int]:
    """Convierte frames de landmarks a una secuencia [NUM_CHANNELS, SEQUENCE_LENGTH].

    Normalizacion invariante a traslacion y escala:
      - origen  = centro de caderas por frame
      - escala  = mediana (por clip) de la distancia centro-hombros / centro-caderas
    Los landmarks ausentes en un frame se marcan NaN y luego se interpolan en el
    tiempo (los pies suelen tener baja visibilidad). Un frame se usa si tiene los
    4 puntos de tronco (hombros + caderas) para poder anclar origen y escala.
    Devuelve (secuencia | None, pose_rate, n_frames_utiles).
    """
    raw_times: list[float] = []
    raw_positions: list[list[float]] = []
    scales: list[float] = []

    for index, frame in enumerate(frames):
        hip_l = _raw_point(frame, "LEFT_HIP")
        hip_r = _raw_point(frame, "RIGHT_HIP")
        sho_l = _raw_point(frame, "LEFT_SHOULDER")
        sho_r = _raw_point(frame, "RIGHT_SHOULDER")
        if not (hip_l and hip_r and sho_l and sho_r):
            continue

        hip_center = _center(hip_l, hip_r)
        sho_center = _center(sho_l, sho_r)
        torso = math.hypot(sho_center[0] - hip_center[0], sho_center[1] - hip_center[1])
        shoulder_w = math.hypot(sho_l[0] - sho_r[0], sho_l[1] - sho_r[1])
        hip_w = math.hypot(hip_l[0] - hip_r[0], hip_l[1] - hip_r[1])
        scale = max(torso, shoulder_w, hip_w)
        if scale <= 1e-4:
            continue

        row: list[float] = []
        for name in SELECTED_LANDMARKS:
            point = _raw_point(frame, name)
            if point is None:
                row.extend([np.nan, np.nan])
            else:
                row.append(point[0] - hip_center[0])
                row.append(point[1] - hip_center[1])

        raw_times.append(float(frame.get("timestamp_sec", index)))
        raw_positions.append(row)
        scales.append(scale)

    n_valid = len(raw_positions)
    total = max(len(frames), 1)
    pose_rate = n_valid / total
    if n_valid < MIN_VALID_FRAMES:
        return None, pose_rate, n_valid

    positions = np.asarray(raw_positions, dtype=np.float64)  # [n_valid, 34], con NaN
    positions = _interpolate_nan_columns(positions)
    clip_scale = float(np.median(scales)) or 1.0
    positions /= clip_scale

    times = np.asarray(raw_times, dtype=np.float64)
    if not np.all(np.diff(times) > 0):
        times = np.arange(n_valid, dtype=np.float64)
    t_norm = (times - times[0]) / max(times[-1] - times[0], 1e-6)
    target_t = np.linspace(0.0, 1.0, SEQUENCE_LENGTH)

    pos_resampled = np.empty((SEQUENCE_LENGTH, positions.shape[1]), dtype=np.float64)
    for channel in range(positions.shape[1]):
        pos_resampled[:, channel] = np.interp(target_t, t_norm, positions[:, channel])

    # velocidades = diferencia temporal (primer valor = 0)
    velocity = np.zeros_like(pos_resampled)
    velocity[1:] = np.diff(pos_resampled, axis=0)

    sequence = np.concatenate([pos_resampled, velocity], axis=1).T  # [68, T]
    sequence = np.nan_to_num(sequence, nan=0.0, posinf=0.0, neginf=0.0)
    return sequence.astype(np.float32), pose_rate, n_valid


def load_landmark_frames(csv_path: Path) -> list[dict[str, Any]]:
    """Reutiliza el lector del pipeline historico (agrupa filas por frame)."""
    frames, _quality = read_landmarks_for_features(Path(csv_path))
    return frames


def sequence_from_landmark_csv(csv_path: Path) -> tuple[np.ndarray | None, float, int]:
    return frames_to_sequence(load_landmark_frames(Path(csv_path)))


def feature_row_from_landmark_csv(csv_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    frames, quality = read_landmarks_for_features(Path(csv_path))
    return build_feature_row(metadata, frames, quality, Path(csv_path))


def extract_feature_vector(feature_row: dict[str, Any]) -> np.ndarray:
    values = []
    for column in FEATURE_COLUMNS:
        raw = feature_row.get(column)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = np.nan
        values.append(value if np.isfinite(value) else np.nan)
    return np.asarray(values, dtype=np.float32)


# ---------------------------------------------------------------------------
#  Escalado de las 36 features (mediana-imputacion + estandarizacion)
# ---------------------------------------------------------------------------
@dataclass
class FeatureScaler:
    medians: np.ndarray
    means: np.ndarray
    stds: np.ndarray
    columns: list[str] = field(default_factory=lambda: list(FEATURE_COLUMNS))

    @classmethod
    def fit(cls, matrix: np.ndarray) -> "FeatureScaler":
        medians = np.nanmedian(matrix, axis=0)
        medians = np.where(np.isfinite(medians), medians, 0.0)
        filled = np.where(np.isfinite(matrix), matrix, medians)
        means = filled.mean(axis=0)
        stds = filled.std(axis=0)
        stds = np.where(stds < 1e-8, 1.0, stds)
        return cls(medians=medians, means=means, stds=stds)

    def transform(self, matrix: np.ndarray) -> np.ndarray:
        arr = np.atleast_2d(np.asarray(matrix, dtype=np.float64))
        filled = np.where(np.isfinite(arr), arr, self.medians)
        return ((filled - self.means) / self.stds).astype(np.float32)

    def to_json(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "medians": self.medians.tolist(),
            "means": self.means.tolist(),
            "stds": self.stds.tolist(),
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "FeatureScaler":
        return cls(
            medians=np.asarray(payload["medians"], dtype=np.float64),
            means=np.asarray(payload["means"], dtype=np.float64),
            stds=np.asarray(payload["stds"], dtype=np.float64),
            columns=list(payload.get("columns", FEATURE_COLUMNS)),
        )


# ---------------------------------------------------------------------------
#  Augmentation (SOLO entrenamiento). Nunca en val/test. Nunca crea sujetos.
# ---------------------------------------------------------------------------
_POS_X_IDX = np.array([i for i, name in enumerate(CHANNEL_NAMES) if name.endswith("_x")])
_POS_IDX = np.array([i for i, name in enumerate(CHANNEL_NAMES) if name.endswith(("_x", "_y"))])
_MIRROR_PERM = None
_FEATURE_MIRROR_PERM = None


def _build_mirror_perms() -> None:
    global _MIRROR_PERM, _FEATURE_MIRROR_PERM
    perm = list(range(NUM_CHANNELS))
    name_to_idx = {name: i for i, name in enumerate(CHANNEL_NAMES)}
    for left, right in _LR_LANDMARK_PAIRS:
        for prefix in ("", "v"):
            for axis in ("x", "y"):
                li = name_to_idx[f"{left}_{prefix}{axis}"]
                ri = name_to_idx[f"{right}_{prefix}{axis}"]
                perm[li], perm[ri] = perm[ri], perm[li]
    _MIRROR_PERM = np.asarray(perm)

    fperm = list(range(len(FEATURE_COLUMNS)))
    fidx = {name: i for i, name in enumerate(FEATURE_COLUMNS)}
    for left, right in _FEATURE_LR_PAIRS:
        if left in fidx and right in fidx:
            fperm[fidx[left]], fperm[fidx[right]] = fperm[fidx[right]], fperm[fidx[left]]
    _FEATURE_MIRROR_PERM = np.asarray(fperm)


_build_mirror_perms()


def augment_sample(
    seq: np.ndarray,
    feat: np.ndarray,
    rng: np.random.Generator,
    noise_std: float = 0.02,
    scale_range: tuple[float, float] = (0.9, 1.1),
    crop_min: float = 0.8,
    mirror_prob: float = 0.5,
    shift_frac: float = 0.06,
) -> tuple[np.ndarray, np.ndarray]:
    """seq: [C, T] ya normalizada; feat: [36] ya escalada."""
    seq = seq.copy()
    feat = feat.copy()
    t = seq.shape[1]

    # 1) recorte temporal + reinterpolacion (simula variacion de velocidad)
    if rng.random() < 0.7:
        span = rng.uniform(crop_min, 1.0)
        start = rng.uniform(0.0, 1.0 - span)
        src = np.linspace(start, start + span, t)
        base = np.linspace(0.0, 1.0, t)
        seq = np.stack([np.interp(src, base, seq[c]) for c in range(seq.shape[0])], axis=0)

    # 2) desplazamiento temporal (roll)
    if rng.random() < 0.5:
        shift = int(rng.integers(-int(t * shift_frac), int(t * shift_frac) + 1))
        if shift:
            seq = np.roll(seq, shift, axis=1)

    # 3) escala de amplitud (solo posiciones + sus velocidades)
    if rng.random() < 0.6:
        factor = rng.uniform(*scale_range)
        seq *= factor

    # 4) ruido gaussiano en posiciones
    if rng.random() < 0.6:
        seq[_POS_IDX] += rng.normal(0.0, noise_std, size=seq[_POS_IDX].shape).astype(seq.dtype)

    # 5) espejo horizontal + swap izquierda/derecha (coherente en seq y feat)
    if rng.random() < mirror_prob:
        seq = seq[_MIRROR_PERM]
        seq[_POS_X_IDX] *= -1.0
        feat = feat[_FEATURE_MIRROR_PERM]

    return seq.astype(np.float32), feat.astype(np.float32)


# ---------------------------------------------------------------------------
#  Modelo Deep Learning (temporal CNN dilatada + rama de features + fusion)
# ---------------------------------------------------------------------------
def build_model(config: dict[str, Any] | None = None):
    import torch
    from torch import nn

    cfg = default_model_config()
    if config:
        cfg.update(config)

    class GaitTemporalModel(nn.Module):
        def __init__(self, c: dict[str, Any]):
            super().__init__()
            self.use_seq = bool(c["use_seq_branch"])
            self.use_feat = bool(c["use_feat_branch"])
            ch = c["seq_channels"]
            p_seq = c["dropout_seq"]

            if self.use_seq:
                self.seq_net = nn.Sequential(
                    nn.Conv1d(c["in_channels"], ch[0], kernel_size=5, padding=2),
                    nn.BatchNorm1d(ch[0]), nn.GELU(), nn.Dropout(p_seq),
                    nn.Conv1d(ch[0], ch[1], kernel_size=3, padding=2, dilation=2),
                    nn.BatchNorm1d(ch[1]), nn.GELU(), nn.Dropout(p_seq),
                    nn.Conv1d(ch[1], ch[2], kernel_size=3, padding=4, dilation=4),
                    nn.BatchNorm1d(ch[2]), nn.GELU(),
                )
                seq_out = ch[2] * 2  # avg + max pooling
            else:
                seq_out = 0

            if self.use_feat:
                self.feat_net = nn.Sequential(
                    nn.Linear(c["num_features"], c["feat_hidden"][0]),
                    nn.BatchNorm1d(c["feat_hidden"][0]), nn.GELU(), nn.Dropout(c["dropout_feat"]),
                    nn.Linear(c["feat_hidden"][0], c["feat_hidden"][1]), nn.GELU(),
                )
                feat_out = c["feat_hidden"][1]
            else:
                feat_out = 0

            fused = seq_out + feat_out
            self.head = nn.Sequential(
                nn.Dropout(c["dropout_head"]),
                nn.Linear(fused, c["head_hidden"]), nn.GELU(),
                nn.Linear(c["head_hidden"], c["num_classes"]),
            )

        def forward(self, seq, feat):
            parts = []
            if self.use_seq:
                h = self.seq_net(seq)
                parts.append(torch.cat([h.mean(dim=-1), h.amax(dim=-1)], dim=-1))
            if self.use_feat:
                parts.append(self.feat_net(feat))
            return self.head(torch.cat(parts, dim=-1))

    return GaitTemporalModel(cfg), cfg


def default_model_config(num_classes: int | None = None) -> dict[str, Any]:
    """Config por defecto del modelo. `num_classes` es opcional: si no se pasa,
    usa el numero de clases completo del proyecto (NUM_CLASSES, hoy 4 — el
    mismo valor que usa el modelo ya desplegado). Pasar un valor explicito
    (p. ej. 2 para el dataset temporal normal+parkinson de la preparacion del
    Dataset V3) NO cambia nada para quien no lo pasa: build_model() ya lee
    este campo del dict de config, no de un global, por lo que este parametro
    es la unica pieza que faltaba para poder variar el numero de clases sin
    tocar la arquitectura en si."""
    return {
        "in_channels": NUM_CHANNELS,
        "num_features": len(FEATURE_COLUMNS),
        "num_classes": int(num_classes) if num_classes is not None else NUM_CLASSES,
        "seq_channels": [24, 32, 32],
        "feat_hidden": [24, 16],
        "head_hidden": 32,
        "dropout_seq": 0.3,
        "dropout_feat": 0.3,
        "dropout_head": 0.4,
        "use_seq_branch": True,
        "use_feat_branch": True,
        "sequence_length": SEQUENCE_LENGTH,
    }


# ---------------------------------------------------------------------------
#  Metricas
# ---------------------------------------------------------------------------
def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None,
    class_names: list[str] | None = None,
) -> dict[str, Any]:
    """`class_names` es opcional: por defecto usa CLASS_NAMES (las 4 clases del
    proyecto), igual que antes de agregar este parametro. Pasar una lista mas
    corta (p. ej. ["normal", "parkinson"]) permite calcular metricas para un
    subconjunto de clases -- necesario para el dataset temporal de 2 clases de
    la preparacion del Dataset V3, sin afectar a ningun llamador existente que
    no pase este argumento (incluida toda la inferencia en produccion)."""
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
        roc_auc_score,
    )

    names = list(class_names) if class_names is not None else CLASS_NAMES
    num_classes = len(names)
    labels = list(range(num_classes))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    per_class = {}
    for idx, name in enumerate(names):
        tp = int(cm[idx, idx])
        fn = int(cm[idx, :].sum() - tp)
        fp = int(cm[:, idx].sum() - tp)
        tn = int(cm.sum() - tp - fn - fp)
        sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
        specificity = tn / (tn + fp) if (tn + fp) else 0.0
        auc = None
        if y_proba is not None and len(np.unique(y_true)) > 1:
            try:
                auc = float(roc_auc_score((y_true == idx).astype(int), y_proba[:, idx]))
            except ValueError:
                auc = None
        per_class[name] = {
            "precision": float(precision[idx]),
            "recall": float(recall[idx]),
            "f1": float(f1[idx]),
            "support": int(support[idx]),
            "sensitivity": float(sensitivity),
            "specificity": float(specificity),
            "roc_auc_ovr": auc,
        }

    macro_auc = None
    if y_proba is not None and len(np.unique(y_true)) == num_classes:
        try:
            macro_auc = float(
                roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro", labels=labels)
            )
        except ValueError:
            macro_auc = None

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
        "macro_precision": float(np.mean(precision)),
        "macro_recall": float(np.mean(recall)),
        "macro_roc_auc_ovr": macro_auc,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": names,
        "per_class": per_class,
        "n_samples": int(len(y_true)),
    }


# ---------------------------------------------------------------------------
#  Utilidades varias
# ---------------------------------------------------------------------------
def seed_everything(seed: int = SEED) -> None:
    import random as _random

    _random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.use_deterministic_algorithms(False)
    except Exception:  # pragma: no cover - torch opcional al importar
        pass


def load_dataset(path: Path | str | None = None) -> dict[str, Any]:
    target = Path(path) if path else DATASET_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"No existe {target}. Ejecute primero "
            "scripts/video_training/deep/10_build_sequence_dataset.py"
        )
    data = np.load(target, allow_pickle=True)
    return {key: data[key] for key in data.files}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gait_feature_highlights(feature_row: dict[str, Any], top_k: int = 6) -> list[dict[str, Any]]:
    """Resume las 36 features en conceptos legibles para el informe."""
    highlights: list[dict[str, Any]] = []
    for concept, meta in GAIT_CONCEPTS.items():
        values = []
        for column in meta["features"]:
            try:
                value = float(feature_row.get(column))
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                values.append((column, round(value, 4)))
        if not values:
            continue
        highlights.append(
            {
                "concept": concept,
                "label": meta["label"],
                "values": {column: value for column, value in values},
                "note": meta["higher_is"],
            }
        )
    return highlights


def load_active_class_names(path: Path | str) -> list[str]:
    """Lee un archivo de configuracion de 'clases activas' para un entrenamiento
    temporal (Dataset V3 en preparacion, p. ej. solo normal+parkinson mientras
    esclerosis_multiple/riesgo_caida esten excluidas por la auditoria).

    Formato esperado (JSON): {"active_class_names": ["normal", "parkinson"]}

    No se llama automaticamente desde ningun sitio: cada script debe invocarla
    explicitamente (p. ej. via un argumento --active-classes-config). Por eso
    NO afecta a video_training_common.CLASS_NAMES ni a la inferencia en
    produccion (13_predict_deep_video.py nunca la invoca).

    Valida que todos los nombres pertenezcan a CLASS_NAMES (el taxonomy
    completo de 4 clases) y que la lista no este vacia; si no, lanza ValueError
    en vez de devolver una configuracion inconsistente en silencio.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    names = data.get("active_class_names")
    if not isinstance(names, list) or not names:
        raise ValueError(f"{path}: 'active_class_names' debe ser una lista no vacia.")
    unknown = [n for n in names if n not in CLASS_NAMES]
    if unknown:
        raise ValueError(
            f"{path}: clases desconocidas {unknown}; deben estar en CLASS_NAMES={CLASS_NAMES}."
        )
    return list(names)


def load_training_eligibility(csv_path: Path | str) -> dict[str, str]:
    """Lee un manifest V3 (p. ej. outputs/dataset_v3/dataset_v3_manifest.csv) y
    devuelve {filename: training_status}. Se usa para que la construccion del
    dataset (10_build_sequence_dataset.py) pueda excluir explicitamente los
    videos marcados TRAINING_EXCLUDED por la auditoria, ademas del filtro de
    clase activa. Requiere las columnas 'filename' y 'training_status'.
    """
    import csv as _csv

    out: dict[str, str] = {}
    with Path(csv_path).open("r", encoding="utf-8", newline="") as fh:
        reader = _csv.DictReader(fh)
        if reader.fieldnames is None or "filename" not in reader.fieldnames or "training_status" not in reader.fieldnames:
            raise ValueError(
                f"{csv_path}: se esperaban las columnas 'filename' y 'training_status'."
            )
        for row in reader:
            out[row["filename"]] = row["training_status"]
    return out


__all__ = [
    "CLASS_NAMES",
    "CLASS_HUMAN_LABEL",
    "CLASS_TO_LABEL",
    "LABEL_TO_CLASS",
    "NUM_CLASSES",
    "NUM_CHANNELS",
    "CHANNEL_NAMES",
    "SEQUENCE_LENGTH",
    "FRAME_STEP",
    "MANIFEST_PATH",
    "DATASET_META_PATH",
    "OOF_PATH",
    "FEATURE_COLUMNS",
    "NO_DIAGNOSIS_NOTE",
    "GAIT_CONCEPTS",
    "DEEP_DATA_DIR",
    "DATASET_PATH",
    "MODEL_DIR",
    "MODEL_WEIGHTS_PATH",
    "MODEL_CONFIG_PATH",
    "FEATURE_SCALER_PATH",
    "LABEL_MAP_PATH",
    "CV_METRICS_PATH",
    "TRAINING_HISTORY_PATH",
    "PLOTS_DIR",
    "FeatureScaler",
    "augment_sample",
    "build_model",
    "default_model_config",
    "classification_metrics",
    "frames_to_sequence",
    "sequence_from_landmark_csv",
    "feature_row_from_landmark_csv",
    "extract_feature_vector",
    "gait_feature_highlights",
    "seed_everything",
    "load_dataset",
    "write_json",
    "read_json",
    "load_active_class_names",
    "load_training_eligibility",
]
