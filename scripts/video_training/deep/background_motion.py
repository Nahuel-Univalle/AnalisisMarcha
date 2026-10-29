"""
Movimiento de fondo a 15 fps (`background_motion_15fps`) -- medida de control de calidad de camara.

COPIA LITERAL de bbox_px() y measure() de outputs/dataset_v4_4class/step6/d2_camera_measurement.py (Paso 6,
validada en el Paso 7 con camaras moviles/fijas conocidas). Se copia aqui para que el codigo de produccion no
dependa de outputs/. No modificar la logica sin re-validar: background_motion_15fps = bg_lk_median.

Uso en produccion: SOLO advertencias de calidad (nunca entrada del modelo).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[3]
GRID = 15.0
LK_W = 480
PC_W = 160
EPS = 1e-6


def bbox_px(lm, w, h):
    xs = np.array([p["x"] for p in lm.values()]) * w
    ys = np.array([p["y"] for p in lm.values()]) * h
    bw, bh = xs.max() - xs.min(), ys.max() - ys.min()
    return (xs.min() - 0.25 * bw, ys.min() - 0.15 * bh, xs.max() + 0.25 * bw, ys.max() + 0.15 * bh)


def measure(row, data, stats):
    path = ROOT / row["video_path"].replace("\\", "/")
    pose = {int(round(f["timestamp_sec"] * GRID)): f for f in data["frames"]}
    pk = np.array(sorted(pose))
    start = float(row["start_s"]) if row["start_s"] else 0.0
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    end = float(row["end_s"]) if row["end_s"] else n / fps
    k0, k1 = int(np.ceil(start * GRID - EPS)), int(np.floor(end * GRID - EPS))
    targets = {int(round(k * fps / GRID)): k for k in range(k0, k1 + 1)}
    grid = {}
    i = 0
    last = max(targets) if targets else -1
    while i <= last:
        ok = cap.grab()
        if not ok:
            break
        if i in targets:
            ok, fr = cap.retrieve()
            if ok:
                g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
                h = int(round(g.shape[0] * LK_W / g.shape[1]))
                grid[targets[i]] = cv2.resize(g, (LK_W, h), interpolation=cv2.INTER_AREA)
        i += 1
    cap.release()
    ks = sorted(grid)
    bg_lk, bg_pc, full_pc, subj, npts, nomask = [], [], [], [], [], 0
    for a, b in zip(ks, ks[1:]):
        if b - a != 1:
            continue
        A, B = grid[a], grid[b]
        H, W = A.shape
        mask = np.full((H, W), 255, np.uint8)
        boxes = []
        for k in (a, b):
            if pk.size:
                j = pk[np.argmin(np.abs(pk - k))]
                if abs(j - k) <= GRID / 2:
                    boxes.append(bbox_px(pose[j]["landmarks"], W, H))
        if boxes:
            x0 = int(max(0, min(bx[0] for bx in boxes))); y0 = int(max(0, min(bx[1] for bx in boxes)))
            x1 = int(min(W, max(bx[2] for bx in boxes))); y1 = int(min(H, max(bx[3] for bx in boxes)))
            mask[y0:y1, x0:x1] = 0
        else:
            nomask += 1
        pts = cv2.goodFeaturesToTrack(A, maxCorners=300, qualityLevel=0.01, minDistance=7, mask=mask)
        if pts is not None and len(pts) >= 8:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(A, B, pts, None)
            p0b, st2, _ = cv2.calcOpticalFlowPyrLK(B, A, p1, None)
            good = (st.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm((p0b - pts).reshape(-1, 2), axis=1) < 1.0)
            npts.append(int(good.sum()))
            if good.sum() >= 8:
                d = (p1 - pts).reshape(-1, 2)[good]
                bg_lk.append(float(np.hypot(*np.median(d, axis=0))) / W)
        else:
            npts.append(0 if pts is None else len(pts))
        sa = cv2.resize(A, (PC_W, int(round(H * PC_W / W))), interpolation=cv2.INTER_AREA).astype(np.float32)
        sb = cv2.resize(B, (PC_W, int(round(H * PC_W / W))), interpolation=cv2.INTER_AREA).astype(np.float32)
        (dx, dy), _ = cv2.phaseCorrelate(sa, sb)
        full_pc.append(float(np.hypot(dx, dy)) / PC_W)
        ms = cv2.resize(mask, (PC_W, sa.shape[0]), interpolation=cv2.INTER_NEAREST) == 0
        ma, mb = sa.copy(), sb.copy()
        ma[ms] = sa[~ms].mean() if (~ms).any() else 0
        mb[ms] = sb[~ms].mean() if (~ms).any() else 0
        (dx, dy), _ = cv2.phaseCorrelate(ma, mb)
        bg_pc.append(float(np.hypot(dx, dy)) / PC_W)
        if a in pose and b in pose:
            ha = [(pose[a]["landmarks"][s]["x"]) for s in ("LEFT_HIP", "RIGHT_HIP")]
            hb = [(pose[b]["landmarks"][s]["x"]) for s in ("LEFT_HIP", "RIGHT_HIP")]
            subj.append((len(full_pc) - 1, abs(np.mean(hb) - np.mean(ha))))
    full = np.asarray(full_pc)
    rho_follow = None
    if len(subj) >= 10:
        idx = [s[0] for s in subj]
        r = spearmanr(full[idx], [s[1] for s in subj])[0]
        rho_follow = None if np.isnan(r) else round(float(r), 3)
    q = lambda v, p: round(float(np.percentile(v, p)), 5) if len(v) else None
    st = stats.get(row["video"], {})
    try:
        orig = float(st["global_shift_px_p90"]) / float(row["width"])
    except (KeyError, ValueError):
        orig = None
    return {
        "video": row["video"], "class": row["class"], "source": row["source"].split(" ")[0],
        "camera_style": row["camera_style"], "view": row["view"], "fps": round(fps, 3),
        "width": row["width"], "height": row["height"], "aspect_ratio": row["aspect_ratio"],
        "analyzed_s": round(len(ks) / GRID, 2), "pairs": len(full_pc), "pairs_without_subject_box": nomask,
        "camera_motion_norm_original": round(orig, 5) if orig is not None else None,
        "fullframe_phase_grid15_median": q(full, 50), "fullframe_phase_grid15_p90": q(full, 90),
        "bg_lk_median": q(bg_lk, 50), "bg_lk_p90": q(bg_lk, 90), "bg_lk_valid_pairs": len(bg_lk),
        "bg_phase_masked_median": q(bg_pc, 50), "bg_phase_masked_p90": q(bg_pc, 90),
        "bg_points_median": int(np.median(npts)) if npts else 0,
        "subject_hip_motion_median": q([s[1] for s in subj], 50), "subject_hip_motion_p90": q([s[1] for s in subj], 90),
        "rho_fullframe_shift_vs_subject_motion": rho_follow,
    }


