"""Carga de los 117 videos del Dataset V4 desde pose_cache (SOLO LECTURA). Misma seleccion, segmentos y ancla que V4
(outputs/dataset_v4_4class/build_dataset_v4_preview.py:64-90). No se reextrae pose ni se tocan los videos."""
from __future__ import annotations
import csv, pickle
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
V4 = ROOT / "outputs" / "dataset_v4_4class"
CLASS_NAMES = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
W_V4, EPS = 5.03, 1e-6


def load_videos():
    man = [r for r in csv.DictReader(open(V4 / "manifest_v4_preview.csv", encoding="utf-8")) if r["include_in_preview"] == "true"]
    smp = {r["video"]: r for r in csv.DictReader(open(V4 / "samples_v4_preview.csv", encoding="utf-8"))}
    out = []
    for r in man:
        d = pickle.loads((V4 / "pose_cache" / f"{Path(r['filename']).stem}.pkl").read_bytes())
        frames, q = d["frames"], d["quality"]
        dur = float(q["duration_seconds"])
        start = float(r["start_s"]) if r["start_s"] else 0.0
        end = float(r["end_s"]) if r["end_s"] else dur
        seg = [f for f in frames if start - EPS <= f["timestamp_sec"] < end - EPS]
        if not seg or r["video"] not in smp:
            continue
        t0 = seg[0]["timestamp_sec"]
        s = smp[r["video"]]
        out.append(dict(video=r["video"], y=CLASS_NAMES.index(r["class"]), cls=r["class"], group=r["split_group"], frames=seg, t0=t0,
                        w_eff=min(W_V4, end - t0), aspect=float(q["width"]) / float(q["height"]), q=q, view=r["view"], source=r["source"],
                        orientation=r["orientation"], camera=r["camera_style"], status=r["subject_status"], src_w=float(r["width"]),
                        src_h=float(r["height"]), fps=r["fps"], row=s))
    return out
