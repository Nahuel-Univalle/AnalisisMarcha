"""V5-CR: V5-C con interpolacion de landmarks en coordenadas RELATIVAS a la cadera (corrige la fuga de traslacion por interpolacion absoluta).
No modifica v5_preproc ni v5c_preproc."""
import sys
from pathlib import Path
import numpy as np
from . import v5_preproc as V
from . import v5c_preproc as C
FEATURES_C = C.FEATURES_C


def resample_grid_rel(ts, P, t0):
    """P [n,17,2] absolutas (NaN = enmascarado). Interpola cadera (siempre valida) y landmarks relativos a la cadera; reconstruye absolutas."""
    grid = t0 + np.arange(V.T) / V.FPS
    H = (P[:, V.IDX["LEFT_HIP"]] + P[:, V.IDX["RIGHT_HIP"]]) / 2           # [n,2], sin NaN por construccion de frames_to_points
    Hg = np.stack([np.interp(grid, ts, H[:, a]) for a in range(2)], axis=1)  # [T,2]
    R = P - H[:, None, :]
    out = np.full((V.T, 17, 2), np.nan)
    for i in range(17):
        for a in range(2):
            m = np.isfinite(R[:, i, a])
            if m.sum() >= 2:
                out[:, i, a] = np.interp(grid, ts[m], R[m, i, a])
    return out + Hg[:, None, :]


def window_inputs_C(frames, t0, aspect, vis_min=V.VIS_MIN):
    ts, P = V.frames_to_points(frames, aspect, vis_min)
    if len(ts) == 0:
        return None
    m = (ts >= t0 - V.EPS) & (ts <= t0 + V.SPAN_S + V.EPS)
    if m.sum() < V.MIN_VALID:
        return None
    lo, hi = max(0, np.argmax(m) - 1), min(len(ts), len(m) - np.argmax(m[::-1]) + 1)
    Pg = resample_grid_rel(ts[lo:hi], P[lo:hi], t0)
    sc = V.body_scale(Pg, "torso")
    if not np.isfinite(sc) or sc < 1e-4:
        return None
    return V.sequence_from_grid(Pg, sc), C.features_C(Pg, sc).astype(np.float32), {"t0": t0, "n_valid": int(m.sum()), "scale": sc}
