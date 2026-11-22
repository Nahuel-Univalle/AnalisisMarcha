"""Preprocesamiento V5 EXPERIMENTAL (aislado de V4; no modifica ningun archivo de produccion).

Entrada comun a entrenamiento e inferencia: `window_inputs(frames, t0, aspect)` -> (X_seq [68, T], X_feat [N], info)
donde `frames` son los cuadros con pose (lista de dicts {timestamp_sec, landmarks{nombre:{x,y,z,visibility}}}) a 15 fps,
`aspect` = ancho/alto del video (relacion de aspecto del cuadro) y `t0` el inicio de la ventana en segundos.

Correcciones frente a V4 (ver informe):
  A  espejo: se invierte el signo de x en posiciones Y velocidades (V4 solo en posiciones, deep_common.py:422).
  B  escala corporal: longitud del torso (centro cadera -> centro hombros), mediana en la ventana, en coordenadas isotropicas.
  C  nueve caracteristicas con coordenadas absolutas -> referenciadas a la cadera / al hombro (angulo del brazo respecto al tronco).
  D  coordenadas isotropicas: x*aspecto, y (V4 usaba x/ancho e y/alto sin corregir).
  E  ventana temporal fija en tiempo fisico (2.6 s, 40 muestras a 15 fps), velocidades por paso de 1/15 s, sin reescalar el tiempo.
Todo en tiempo FISICO: ninguna funcion usa la duracion del video.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "video_training"))
from video_training_common import SELECTED_LANDMARKS, find_signal_peaks, regularity_from_peaks  # noqa: E402

LM = list(SELECTED_LANDMARKS)
IDX = {n: i for i, n in enumerate(LM)}
FPS = 15.0
T = 40                       # muestras por ventana
SPAN_S = (T - 1) / FPS       # 2.6 s
MIN_VALID = 20               # >= 50 % de la rejilla con pose real
VIS_MIN = 0.2
EPS = 1e-6

POS_NAMES = [f"{n}_{a}" for n in LM for a in ("x", "y")]
CH_NAMES = POS_NAMES + [f"{n}_v{a}" for n in LM for a in ("x", "y")]
NCH = len(CH_NAMES)  # 68

FEATURES_V5 = [
    "body_motion_mean", "body_motion_std", "hip_center_motion_mean", "shoulder_center_motion_mean",
    "vertical_motion_mean", "horizontal_motion_mean",
    "left_ankle_rel_motion_mean", "right_ankle_rel_motion_mean", "left_knee_rel_motion_mean", "right_knee_rel_motion_mean",
    "leg_rel_motion_asymmetry",
    "ankle_rel_vrange_left", "ankle_rel_vrange_right", "ankle_rel_vrange_asymmetry",
    "knee_rel_vrange_left", "knee_rel_vrange_right",
    "step_regularity_score",
    "left_wrist_rel_motion_mean", "right_wrist_rel_motion_mean",
    "arm_swing_angle_mean", "arm_swing_angle_asymmetry", "left_arm_swing_angle", "right_arm_swing_angle",
    "shoulder_width_mean", "hip_width_mean",
    "trunk_inclination_mean", "trunk_inclination_std", "trunk_sway_mean", "trunk_sway_std", "posture_stability_score",
    "estimated_step_count", "estimated_cadence_steps_per_min", "step_frequency_hz",
    "gait_variability", "motion_smoothness", "rhythm_variability",
]
assert len(FEATURES_V5) == 36
# correspondencia con V4 (mismo orden/ranura): permite comparar por grupos
FEATURES_V4 = ["body_motion_mean", "body_motion_std", "hip_center_motion_mean", "shoulder_center_motion_mean", "vertical_motion_mean",
               "horizontal_motion_mean", "left_ankle_motion_mean", "right_ankle_motion_mean", "left_knee_motion_mean", "right_knee_motion_mean",
               "leg_motion_asymmetry", "ankle_vertical_range_left", "ankle_vertical_range_right", "ankle_vertical_asymmetry",
               "knee_vertical_range_left", "knee_vertical_range_right", "step_regularity_score", "left_wrist_motion_mean",
               "right_wrist_motion_mean", "arm_swing_mean", "arm_swing_asymmetry", "left_arm_range", "right_arm_range",
               "shoulder_width_mean", "hip_width_mean", "trunk_inclination_mean", "trunk_inclination_std", "trunk_sway_mean",
               "trunk_sway_std", "posture_stability_score", "estimated_step_count", "estimated_cadence_steps_per_min",
               "step_frequency_hz", "gait_variability", "motion_smoothness", "rhythm_variability"]
# Variante secundaria V5-S: quita proxies de vista (anchos) y la columna redundante step_frequency_hz (= cadencia / 60)
S_DROP = ["shoulder_width_mean", "hip_width_mean", "step_frequency_hz"]
S_KEEP_IDX = [i for i, n in enumerate(FEATURES_V5) if n not in S_DROP]

GROUPS = {  # grupos para importancia por permutacion (indices sobre FEATURES_V5)
    "desplazamiento_global": ["body_motion_mean", "body_motion_std", "hip_center_motion_mean", "shoulder_center_motion_mean",
                              "vertical_motion_mean", "horizontal_motion_mean", "motion_smoothness"],
    "piernas_relativas": ["left_ankle_rel_motion_mean", "right_ankle_rel_motion_mean", "left_knee_rel_motion_mean",
                          "right_knee_rel_motion_mean", "leg_rel_motion_asymmetry", "ankle_rel_vrange_left", "ankle_rel_vrange_right",
                          "ankle_rel_vrange_asymmetry", "knee_rel_vrange_left", "knee_rel_vrange_right", "gait_variability"],
    "brazos": ["left_wrist_rel_motion_mean", "right_wrist_rel_motion_mean", "arm_swing_angle_mean", "arm_swing_angle_asymmetry",
               "left_arm_swing_angle", "right_arm_swing_angle"],
    "tronco_postura": ["trunk_inclination_mean", "trunk_inclination_std", "trunk_sway_mean", "trunk_sway_std", "posture_stability_score"],
    "ritmo_pasos": ["step_regularity_score", "estimated_step_count", "estimated_cadence_steps_per_min", "step_frequency_hz",
                    "rhythm_variability"],
    "proxies_de_vista": ["shoulder_width_mean", "hip_width_mean"],
}
V4_GROUPS = {  # mismo agrupamiento sobre nombres V4
    "desplazamiento_global": ["body_motion_mean", "body_motion_std", "hip_center_motion_mean", "shoulder_center_motion_mean",
                              "vertical_motion_mean", "horizontal_motion_mean", "motion_smoothness"],
    "piernas_relativas": ["left_ankle_motion_mean", "right_ankle_motion_mean", "left_knee_motion_mean", "right_knee_motion_mean",
                          "leg_motion_asymmetry", "ankle_vertical_range_left", "ankle_vertical_range_right", "ankle_vertical_asymmetry",
                          "knee_vertical_range_left", "knee_vertical_range_right", "gait_variability"],
    "brazos": ["left_wrist_motion_mean", "right_wrist_motion_mean", "arm_swing_mean", "arm_swing_asymmetry", "left_arm_range",
               "right_arm_range"],
    "tronco_postura": GROUPS["tronco_postura"], "ritmo_pasos": GROUPS["ritmo_pasos"], "proxies_de_vista": GROUPS["proxies_de_vista"],
}

_LR = [("LEFT_SHOULDER", "RIGHT_SHOULDER"), ("LEFT_ELBOW", "RIGHT_ELBOW"), ("LEFT_WRIST", "RIGHT_WRIST"), ("LEFT_HIP", "RIGHT_HIP"),
       ("LEFT_KNEE", "RIGHT_KNEE"), ("LEFT_ANKLE", "RIGHT_ANKLE"), ("LEFT_HEEL", "RIGHT_HEEL"), ("LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX")]
_FLR = [("left_ankle_rel_motion_mean", "right_ankle_rel_motion_mean"), ("left_knee_rel_motion_mean", "right_knee_rel_motion_mean"),
        ("ankle_rel_vrange_left", "ankle_rel_vrange_right"), ("knee_rel_vrange_left", "knee_rel_vrange_right"),
        ("left_wrist_rel_motion_mean", "right_wrist_rel_motion_mean"), ("left_arm_swing_angle", "right_arm_swing_angle")]


def _mirror_perm():
    p = list(range(NCH)); ix = {n: i for i, n in enumerate(CH_NAMES)}
    for l, r in _LR:
        for pre in ("", "v"):
            for a in ("x", "y"):
                li, ri = ix[f"{l}_{pre}{a}"], ix[f"{r}_{pre}{a}"]
                p[li], p[ri] = p[ri], p[li]
    f = list(range(36)); fi = {n: i for i, n in enumerate(FEATURES_V5)}
    for l, r in _FLR:
        f[fi[l]], f[fi[r]] = f[fi[r]], f[fi[l]]
    return np.asarray(p), np.asarray(f)


MIRROR_PERM, FEAT_MIRROR_PERM = _mirror_perm()
X_CH = np.array([i for i, n in enumerate(CH_NAMES) if n.endswith("_x") or n.endswith("_vx")])  # posiciones Y velocidades en x


def mirror_seq(seq: np.ndarray) -> np.ndarray:
    """Espejo horizontal fisicamente correcto: intercambia izquierda/derecha y niega x en posiciones Y velocidades."""
    out = np.array(seq, copy=True)[MIRROR_PERM]
    out[X_CH] *= -1.0
    return out


def mirror_feat(feat: np.ndarray) -> np.ndarray:
    return np.asarray(feat)[..., FEAT_MIRROR_PERM]


def v4_mirror_seq(seq: np.ndarray, v4_perm, v4_pos_x_idx) -> np.ndarray:
    """Replica del espejo de V4 (deep_common.py:420-423) solo para pruebas de regresion: niega x de posiciones, NO de velocidades."""
    out = seq[v4_perm].copy(); out[v4_pos_x_idx] *= -1.0
    return out


# ---------------------------------------------------------------------------------------------------------
def frames_to_points(frames, aspect: float, vis_min: float = VIS_MIN):
    """-> times [n], P [n,17,2] en coordenadas ISOTROPICAS (x*aspecto, y), NaN si falta o visibilidad < vis_min.
    Un cuadro se usa solo si tiene los 4 puntos de tronco (igual que V4)."""
    ts, pts = [], []
    for f in frames:
        lm = f.get("landmarks", {})
        row = np.full((17, 2), np.nan)
        for n, i in IDX.items():
            p = lm.get(n)
            if p is None:
                continue
            if vis_min > 0 and p.get("visibility", 1.0) < vis_min:
                continue
            row[i] = (float(p["x"]) * aspect, float(p["y"]))
        if np.isnan(row[[IDX["LEFT_HIP"], IDX["RIGHT_HIP"], IDX["LEFT_SHOULDER"], IDX["RIGHT_SHOULDER"]]]).any():
            continue
        ts.append(float(f["timestamp_sec"])); pts.append(row)
    return np.asarray(ts), (np.asarray(pts) if pts else np.zeros((0, 17, 2)))


def resample_grid(ts: np.ndarray, P: np.ndarray, t0: float):
    """Interpola linealmente cada coordenada a la rejilla fija t0 + k/15 s (k=0..T-1). Columnas sin >=2 datos -> NaN."""
    grid = t0 + np.arange(T) / FPS
    out = np.full((T, 17, 2), np.nan)
    for i in range(17):
        for a in range(2):
            m = np.isfinite(P[:, i, a])
            if m.sum() >= 2:
                out[:, i, a] = np.interp(grid, ts[m], P[m, i, a])
    return out


def body_scale(Pg: np.ndarray, kind: str = "torso") -> float:
    """Mediana en la ventana de la escala corporal. `kind` solo para el analisis comparativo de alternativas."""
    LS, RS, LH, RH = (Pg[:, IDX[n]] for n in ("LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_HIP", "RIGHT_HIP"))
    S, H = (LS + RS) / 2, (LH + RH) / 2
    torso = np.linalg.norm(S - H, axis=-1); sw = np.linalg.norm(LS - RS, axis=-1); hw = np.linalg.norm(LH - RH, axis=-1)
    if kind == "torso":
        v = torso
    elif kind == "v4_seq_max":
        v = np.maximum(np.maximum(torso, sw), hw)
    elif kind == "v4_feat_median3":
        v = np.median(np.stack([sw, hw, torso]), axis=0)
    elif kind == "torso_plus_thigh":
        thigh = (np.linalg.norm(Pg[:, IDX["LEFT_KNEE"]] - LH, axis=-1) + np.linalg.norm(Pg[:, IDX["RIGHT_KNEE"]] - RH, axis=-1)) / 2
        v = torso + thigh
    elif kind == "torso_shoulder_hip_mean":
        v = (torso + sw + hw) / 3
    else:
        raise ValueError(kind)
    v = v[np.isfinite(v) & (v > 0)]
    return float(np.median(v)) if len(v) else float("nan")


def _mean(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.mean()) if len(x) else float("nan")


def _std(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.std()) if len(x) > 1 else (0.0 if len(x) == 1 else float("nan"))


def _rng(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(np.percentile(x, 95) - np.percentile(x, 5)) if len(x) else float("nan")


def _asym(a, b):
    if not (np.isfinite(a) and np.isfinite(b)):
        return float("nan")
    return abs(a - b) / max(abs(a), abs(b), 1e-6)


def _mot(series, s):
    return np.linalg.norm(np.diff(series, axis=0), axis=-1) / s


def features_from_grid(Pg: np.ndarray, scale: float) -> np.ndarray:
    """36 caracteristicas V5 desde la ventana remuestreada Pg [T,17,2] (coordenadas isotropicas). Formulas en el informe."""
    g = lambda n: Pg[:, IDX[n]]
    LS, RS, LH, RH = g("LEFT_SHOULDER"), g("RIGHT_SHOULDER"), g("LEFT_HIP"), g("RIGHT_HIP")
    H, S = (LH + RH) / 2, (LS + RS) / 2
    s = scale
    core = [g(n) for n in ("LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_HIP", "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE", "LEFT_ANKLE", "RIGHT_ANKLE")]
    core_m = np.concatenate([_mot(c, s) for c in core])
    hip_m, sho_m = _mot(H, s), _mot(S, s)
    # piernas RELATIVAS a la cadera
    rel = {n: g(n) - H for n in ("LEFT_ANKLE", "RIGHT_ANKLE", "LEFT_KNEE", "RIGHT_KNEE")}
    mA_l, mA_r = _mot(rel["LEFT_ANKLE"], s), _mot(rel["RIGHT_ANKLE"], s)
    mK_l, mK_r = _mot(rel["LEFT_KNEE"], s), _mot(rel["RIGHT_KNEE"], s)
    vr = lambda n: _rng(rel[n][:, 1] / s)
    rA_l, rA_r, rK_l, rK_r = vr("LEFT_ANKLE"), vr("RIGHT_ANKLE"), vr("LEFT_KNEE"), vr("RIGHT_KNEE")
    # brazos: muneca relativa al hombro del mismo lado; angulo del brazo respecto al eje del tronco (hombro->cadera)
    down = H - S
    def arm_angle(sh, wr):
        v = wr - sh
        cross = down[:, 0] * v[:, 1] - down[:, 1] * v[:, 0]; dot = (down * v).sum(-1)
        return np.arctan2(cross, dot)
    th_l, th_r = arm_angle(LS, g("LEFT_WRIST")), arm_angle(RS, g("RIGHT_WRIST"))
    aL, aR = _rng(th_l), _rng(th_r)
    wL, wR = _mean(_mot(g("LEFT_WRIST") - LS, s)), _mean(_mot(g("RIGHT_WRIST") - RS, s))
    # tronco
    dx, dy = S[:, 0] - H[:, 0], H[:, 1] - S[:, 1]
    incl = np.abs(np.degrees(np.arctan2(dx, dy)))
    sway = np.abs(dx) / s
    sway_std, incl_std = _std(sway), _std(incl)
    posture = 1.0 / (1.0 + (0 if not np.isfinite(sway_std) else sway_std) + (0 if not np.isfinite(incl_std) else incl_std) / 45.0)
    # ritmo: picos de la altura de cada tobillo relativa a la cadera (rejilla uniforme a 15 fps)
    pk_l = find_signal_peaks(list(rel["LEFT_ANKLE"][:, 1]), FPS)
    pk_r = find_signal_peaks(list(rel["RIGHT_ANKLE"][:, 1]), FPS)
    comb = sorted(pk_l + pk_r)
    dur = T / FPS
    steps = len(comb)
    reg, rvar = regularity_from_peaks(comb, FPS)
    cad = steps / dur * 60.0 if steps > 0 else float("nan")
    freq = steps / dur if steps > 0 else float("nan")
    # suavidad (jerk) del centro de cadera
    jerk_std = float("nan")
    if len(hip_m) >= 3:
        acc = np.diff(hip_m); jerk = np.diff(acc)
        jerk_std = _std(jerk) if len(jerk) else float("nan")
    smooth = 1.0 / (1.0 + jerk_std) if np.isfinite(jerk_std) else float("nan")
    gv = _mean([_std(mA_l), _std(mA_r), _std(hip_m)])
    row = [
        _mean(core_m), _std(core_m), _mean(hip_m), _mean(sho_m), _mean(np.abs(np.diff(H[:, 1])) / s), _mean(np.abs(np.diff(H[:, 0])) / s),
        _mean(mA_l), _mean(mA_r), _mean(mK_l), _mean(mK_r), _asym(_mean(mA_l), _mean(mA_r)),
        rA_l, rA_r, _asym(rA_l, rA_r), rK_l, rK_r,
        float(reg) if reg is not None else float("nan"),
        wL, wR, _mean([aL, aR]), _asym(aL, aR), aL, aR,
        _mean(np.linalg.norm(LS - RS, axis=-1) / s), _mean(np.linalg.norm(LH - RH, axis=-1) / s),
        _mean(incl), incl_std, _mean(sway), sway_std, posture,
        float(steps), cad, freq, gv, smooth, float(rvar) if rvar is not None else float("nan"),
    ]
    return np.asarray(row, dtype=np.float64)


def sequence_from_grid(Pg: np.ndarray, scale: float) -> np.ndarray:
    """[68, T]: posiciones relativas a la cadera / escala (x,y por landmark) + velocidades por paso de 1/15 s (diferencia de las MISMAS posiciones)."""
    H = (Pg[:, IDX["LEFT_HIP"]] + Pg[:, IDX["RIGHT_HIP"]]) / 2
    pos = ((Pg - H[:, None, :]) / scale).reshape(T, 34)
    pos = np.where(np.isfinite(pos), pos, 0.0)
    return positions_to_sequence(pos)


def positions_to_sequence(pos: np.ndarray) -> np.ndarray:
    vel = np.zeros_like(pos); vel[1:] = np.diff(pos, axis=0)
    return np.concatenate([pos, vel], axis=1).T.astype(np.float32)


def window_inputs(frames, t0: float, aspect: float, scale_kind: str = "torso", vis_min: float = VIS_MIN):
    """UNICA funcion de construccion de entradas (entrenamiento e inferencia). None si la ventana no tiene >= MIN_VALID cuadros con pose."""
    ts, P = frames_to_points(frames, aspect, vis_min)
    if len(ts) == 0:
        return None
    m = (ts >= t0 - EPS) & (ts <= t0 + SPAN_S + EPS)
    if m.sum() < MIN_VALID:
        return None
    # para interpolar en los bordes se usan tambien los vecinos inmediatos fuera de la ventana (no cambian su duracion)
    lo, hi = max(0, np.argmax(m) - 1), min(len(ts), len(m) - np.argmax(m[::-1]) + 1)
    Pg = resample_grid(ts[lo:hi], P[lo:hi], t0)
    sc = body_scale(Pg, scale_kind)
    if not np.isfinite(sc) or sc < 1e-4:
        return None
    feat = features_from_grid(Pg, sc)
    seq = sequence_from_grid(Pg, sc)
    info = {"t0": t0, "n_valid": int(m.sum()), "interp_frac": 1.0 - m.sum() / T, "scale": sc}
    return seq, feat.astype(np.float32), info
