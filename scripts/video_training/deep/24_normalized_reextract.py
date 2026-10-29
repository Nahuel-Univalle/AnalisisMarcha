"""
Paso 24 - Re-extraccion de pose con GRABACION NORMALIZADA (control de sesgo de fuente).

La auditoria detecto que las clases son separables por metadatos de grabacion
(fps, resolucion, duracion, nitidez...) y no solo por la marcha. Este script
neutraliza los confounds mas directos ANTES de estimar la pose:

  - remuestreo temporal de TODOS los videos a una MISMA tasa (TARGET_FPS)
  - reescalado a una MISMA dimension maxima (MAX_DIM)

Luego reconstruye la secuencia [68, 96] y las 36 features con el MISMO
preprocesamiento que produccion (frames_to_sequence / build_feature_row).

Salida -> data/video_training/deep/dataset_norm.npz
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_NAMES,
    DEEP_DATA_DIR,
    FEATURE_COLUMNS,
    NUM_CHANNELS,
    SEQUENCE_LENGTH,
    extract_feature_vector,
    frames_to_sequence,
    write_json,
)
from video_training_common import (  # noqa: E402
    CORE_LANDMARKS,
    PROJECT_ROOT,
    SELECTED_LANDMARKS,
    build_feature_row,
    read_manifest,
)

TARGET_FPS = 15.0
MAX_DIM = 720
MAX_OUT_FRAMES = 400
DATASET_NORM_PATH = DEEP_DATA_DIR / "dataset_norm.npz"
DATASET_NORM_META = DEEP_DATA_DIR / "dataset_norm_meta.json"


def extract_normalized(video_path: Path):
    """Lectura SECUENCIAL (sin cap.set/seek, que es patologicamente lento en .MOV):
    se recorren todos los frames y se conserva uno cada vez que su timestamp
    cruza el siguiente instante de la rejilla comun de TARGET_FPS. Ademas se
    reescala a MAX_DIM. Asi la densidad temporal efectiva es identica en las 4
    clases antes de estimar la pose (control del confound de fps)."""
    import cv2
    import mediapipe as mp

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None, None, "no_open"
    src_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    n_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if src_fps <= 0:
        cap.release()
        return None, None, "bad_meta"
    duration = n_src / src_fps if n_src > 0 else 0.0
    scale = MAX_DIM / max(w, h) if max(w, h) > MAX_DIM else 1.0

    mp_pose = mp.solutions.pose
    pose_landmark = mp_pose.PoseLandmark
    frames = []
    processed = 0
    valid = 0
    step = 1.0 / TARGET_FPS
    next_t = 0.0
    out_k = 0
    with mp_pose.Pose(static_image_mode=False, model_complexity=1,
                      min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t = idx / src_fps
            idx += 1
            if t + 1e-9 < next_t:
                continue
            next_t += step
            if out_k >= MAX_OUT_FRAMES:
                break
            processed += 1
            if scale != 1.0:
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            res = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ts = out_k * step
            out_k += 1
            if not res.pose_landmarks:
                continue
            lms = res.pose_landmarks.landmark
            fl = {}
            for name in SELECTED_LANDMARKS:
                lm = lms[pose_landmark[name].value]
                fl[name] = {"x": float(lm.x), "y": float(lm.y),
                            "z": float(getattr(lm, "z", 0.0)),
                            "visibility": float(getattr(lm, "visibility", 0.0))}
            if all(n in fl for n in CORE_LANDMARKS):
                valid += 1
                frames.append({"frame_index": out_k - 1, "timestamp_sec": ts, "landmarks": fl})
    cap.release()
    quality = {
        "total_frames": out_k, "processed_frames": processed, "valid_pose_frames": valid,
        "pose_detection_rate": valid / processed if processed else 0.0,
        "duration_seconds": duration, "fps": TARGET_FPS, "width": int(w * scale), "height": int(h * scale),
        "valid_for_training": (valid / processed if processed else 0.0) >= 0.5, "quality_warning": "",
    }
    return frames, quality, None


def main() -> int:
    rows = read_manifest()
    if not rows:
        print("manifest vacio"); return 1
    DEEP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    X_seq, X_feat, y = [], [], []
    subj, docs, vpaths, conds, sevs, prates = [], [], [], [], [], []
    excluded = []
    per_class_frames = defaultdict(list)
    t0 = time.time()

    for i, row in enumerate(rows, 1):
        vp = PROJECT_ROOT / str(row["video_path"]).replace("\\", "/")
        try:
            label = int(float(row["label"]))
        except (TypeError, ValueError):
            excluded.append({"filename": row.get("filename"), "reason": "label"}); continue
        frames, quality, err = extract_normalized(vp)
        if err or not frames:
            excluded.append({"filename": row.get("filename"), "reason": err or "no_frames"}); continue
        seq, _seq_pr, n_valid = frames_to_sequence(frames)
        pose_rate = float(quality.get("pose_detection_rate") or 0.0)  # real: detectados/procesados
        if seq is None:
            excluded.append({"filename": row.get("filename"), "condition": row.get("condition"),
                             "reason": f"frames_validos={n_valid}"}); continue
        feat_row = build_feature_row(row, frames, quality, None)
        X_seq.append(seq)
        X_feat.append(extract_feature_vector(feat_row))
        y.append(label)
        subj.append(str(row["subject_id"]))
        docs.append(str(row.get("subject_documented")).lower() == "true")
        vpaths.append(str(row["video_path"]))
        conds.append(str(row["condition"]))
        sevs.append(str(row.get("severity")))
        prates.append(round(float(pose_rate), 4))
        per_class_frames[str(row["condition"])].append(n_valid)
        if i % 20 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}  ({time.time() - t0:.0f}s)")

    X_seq = np.stack(X_seq).astype(np.float32)
    X_feat = np.stack(X_feat).astype(np.float32)
    y = np.asarray(y, dtype=np.int64)
    np.savez_compressed(
        DATASET_NORM_PATH, X_seq=X_seq, X_feat=X_feat, y=y,
        subject_id=np.asarray(subj), subject_documented=np.asarray(docs),
        video_path=np.asarray(vpaths), condition=np.asarray(conds), severity=np.asarray(sevs),
        pose_rate=np.asarray(prates, dtype=np.float32), class_names=np.asarray(CLASS_NAMES),
        feature_names=np.asarray(FEATURE_COLUMNS), channel_count=np.asarray([NUM_CHANNELS]),
        sequence_length=np.asarray([SEQUENCE_LENGTH]),
    )
    conds_arr = np.asarray(conds)
    prates_arr = np.asarray(prates, dtype=float)
    meta = {
        "purpose": "Control del sesgo de fuente: igualar las caracteristicas tecnicas "
                   "de grabacion en las 4 clases ANTES de estimar la pose, para medir "
                   "cuanto del rendimiento del modelo depende de la marcha y cuanto de "
                   "artefactos de la fuente (fps, resolucion, densidad temporal).",
        "normalizacion_aplicada": {
            "1_remuestreo_temporal": f"lectura secuencial; se conserva 1 frame por cada "
                f"1/{int(TARGET_FPS)} s -> densidad temporal efectiva = {int(TARGET_FPS)} fps "
                "identica en todas las clases (antes: normal 32.7fps, parkinson 40fps, EM/fall 24fps).",
            "2_resolucion": f"reescalado a dimension maxima {MAX_DIM}px (antes: 1920x1080 vs 1280x720).",
            "3_ventana_maxima": f"{MAX_OUT_FRAMES} frames de salida ({MAX_OUT_FRAMES / TARGET_FPS:.0f}s) "
                "para acotar clips muy largos (parkinson ~13.5s).",
            "4_igual_que_produccion": "tras esto se aplica el MISMO preprocesamiento: "
                "hip-centrado + escala por longitud de tronco + remuestreo a T=96 + velocidades; "
                "y las MISMAS 36 features (build_feature_row).",
            "NO_se_normaliza": "no se altera la geometria de la marcha (amplitudes, asimetrias, "
                "ritmo, coordinacion): solo se igualan fps y resolucion. La normalizacion "
                "hip-centrado + escala de tronco ya es identica a produccion y NO elimina "
                "informacion clinica (son distancias relativas al cuerpo).",
        },
        "n_samples": int(len(y)), "n_excluded": len(excluded), "excluded": excluded,
        "videos_per_class": {c: int((conds_arr == c).sum()) for c in CLASS_NAMES},
        "subjects_per_class": {c: int(len(set(np.asarray(subj)[conds_arr == c]))) for c in CLASS_NAMES},
        "real_pose_rate_per_class_after_norm": {
            c: round(float(prates_arr[conds_arr == c].mean()), 4)
            for c in CLASS_NAMES if (conds_arr == c).any()
        },
        "valid_frames_per_class": {
            c: {"min": int(np.min(per_class_frames[c])), "median": int(np.median(per_class_frames[c])),
                "max": int(np.max(per_class_frames[c]))}
            for c in CLASS_NAMES if per_class_frames.get(c)
        },
        "excluded_from_dataset": list(getattr(__import__("video_training_common"), "MANIFEST_EXCLUDE", {}).keys()),
    }
    write_json(DATASET_NORM_META, meta)
    print(f"\ndataset_norm -> {DATASET_NORM_PATH}  ({len(y)} muestras, {len(excluded)} excluidas)")
    print(f"videos/clase: {meta['videos_per_class']}")
    print(f"frames validos/clase: {meta['valid_frames_per_class']}")
    print(f"tiempo: {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
