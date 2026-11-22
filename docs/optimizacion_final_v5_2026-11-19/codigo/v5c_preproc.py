"""V5-C: copia de V5-P con caracteristicas invariantes a la traslacion horizontal global (camara que sigue a la persona).
No modifica v5_preproc ni ningun archivo de V5-P."""
import sys
from pathlib import Path
import numpy as np
OLD = Path(__file__).resolve().parents[2] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"
sys.path.insert(0, str(OLD))
import v5_preproc as V
DROP = ["hip_center_motion_mean", "shoulder_center_motion_mean", "horizontal_motion_mean"]
KEEP_IDX = [i for i, n in enumerate(V.FEATURES_V5) if n not in DROP]
FEATURES_C = [V.FEATURES_V5[i] for i in KEEP_IDX]
assert len(FEATURES_C) == 33


def features_C(Pg, s):
    f = V.features_from_grid(Pg, s).copy()
    g = lambda n: Pg[:, V.IDX[n]]
    H = (g("LEFT_HIP") + g("RIGHT_HIP")) / 2
    core = [g(n) - H for n in ("LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_KNEE", "RIGHT_KNEE", "LEFT_ANKLE", "RIGHT_ANKLE")]
    cm = np.concatenate([V._mot(c, s) for c in core])
    f[V.FEATURES_V5.index("body_motion_mean")] = V._mean(cm)
    f[V.FEATURES_V5.index("body_motion_std")] = V._std(cm)
    vh = np.abs(np.diff(H[:, 1])) / s
    jerk_std = V._std(np.diff(np.diff(vh))) if len(vh) >= 4 else float("nan")
    f[V.FEATURES_V5.index("motion_smoothness")] = 1.0 / (1.0 + jerk_std) if np.isfinite(jerk_std) else float("nan")
    mA_l = V._mot(g("LEFT_ANKLE") - H, s)
    mA_r = V._mot(g("RIGHT_ANKLE") - H, s)
    f[V.FEATURES_V5.index("gait_variability")] = V._mean([V._std(mA_l), V._std(mA_r), V._std(vh)])
    return f[KEEP_IDX]


def window_inputs_C(frames, t0, aspect, vis_min=V.VIS_MIN):
    ts, P = V.frames_to_points(frames, aspect, vis_min)
    if len(ts) == 0:
        return None
    m = (ts >= t0 - V.EPS) & (ts <= t0 + V.SPAN_S + V.EPS)
    if m.sum() < V.MIN_VALID:
        return None
    lo, hi = max(0, np.argmax(m) - 1), min(len(ts), len(m) - np.argmax(m[::-1]) + 1)
    Pg = V.resample_grid(ts[lo:hi], P[lo:hi], t0)
    sc = V.body_scale(Pg, "torso")
    if not np.isfinite(sc) or sc < 1e-4:
        return None
    return V.sequence_from_grid(Pg, sc), features_C(Pg, sc).astype(np.float32), {"t0": t0, "n_valid": int(m.sum()), "scale": sc}
