"""
Paso 10 - Construccion del dataset de secuencias temporales para Deep Learning.

Lee data/video_training/manifest.csv (137 videos, 4 clases) y, por cada video:

  1. Ubica su CSV de landmarks (data/video_training/pose_landmarks/<stem>_landmarks.csv).
     Si no existe, ejecuta la extraccion de pose (MediaPipe) para ese video.
  2. Normaliza los landmarks y genera una secuencia temporal de tamano fijo
     [NUM_CHANNELS, SEQUENCE_LENGTH]  (posiciones + velocidades).
  3. Calcula el vector de 36 caracteristicas de marcha (build_feature_row).
  4. Conserva subject_id (para dividir train/val/test SIN fuga por sujeto) y la
     marca subject_documented.

Salida:
  data/video_training/deep/dataset.npz      (X_seq, X_feat, y, subject_id, ...)
  data/video_training/deep/dataset_meta.json (resumen + limitaciones + exclusiones)

No inventa sujetos ni etiquetas. Los clips que no alcanzan MIN_VALID_FRAMES
frames con pose valida se excluyen y quedan documentados.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import (  # noqa: E402
    CLASS_NAMES,
    DATASET_META_PATH,
    DATASET_PATH,
    DEEP_DATA_DIR,
    FEATURE_COLUMNS,
    FRAME_STEP,
    MANIFEST_PATH,
    NUM_CHANNELS,
    SEQUENCE_LENGTH,
    extract_feature_vector,
    feature_row_from_landmark_csv,
    frames_to_sequence,
    load_active_class_names,
    load_training_eligibility,
    write_json,
)
from video_training_common import (  # noqa: E402
    PROJECT_ROOT,
    extract_video_features,
    landmark_output_path,
    read_landmarks_for_features,
    read_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construye dataset.npz de secuencias temporales para Deep Learning. "
        "Sin argumentos: mismas 4 clases y misma salida de siempre "
        "(data/video_training/deep/dataset.npz), con UNA correccion de comportamiento "
        "respecto a versiones anteriores: los videos marcados valid_for_training=False en "
        "pose_quality_report.csv (hoy solo 011_NM_01.MOV) se excluyen automaticamente en "
        "vez de colarse en el dataset (usar --ignore-quality-gate para el comportamiento "
        "antiguo, solo con fines de depuracion/comparacion)."
    )
    parser.add_argument(
        "--output", default=None,
        help="Ruta del .npz de salida. Por defecto: data/video_training/deep/dataset.npz "
             "(el mismo que usa el modelo desplegado -- usar --output distinto para no "
             "sobrescribirlo, p. ej. al construir un dataset temporal de prueba).",
    )
    parser.add_argument(
        "--meta-output", default=None,
        help="Ruta del dataset_meta.json de salida. Por defecto junto a --output.",
    )
    parser.add_argument(
        "--active-classes-config", default=None,
        help="JSON con {'active_class_names': [...]} para restringir el dataset a un "
             "subconjunto de las 4 clases (p. ej. dataset temporal normal+parkinson de la "
             "preparacion del Dataset V3). Sin este argumento se incluyen las 4 clases, "
             "igual que siempre.",
    )
    parser.add_argument(
        "--training-eligibility-csv", default=None,
        help="Manifest V3 (columnas 'filename' y 'training_status') para excluir "
             "explicitamente videos marcados TRAINING_EXCLUDED por la auditoria del "
             "dataset (p. ej. outputs/dataset_v3/dataset_v3_manifest.csv). Opcional.",
    )
    parser.add_argument(
        "--ignore-quality-gate", action="store_true",
        help="Desactiva el filtro (activado por defecto) que excluye videos marcados "
             "valid_for_training=False en pose_quality_report.csv. Solo para depuracion; "
             "NO usar para construir el dataset de entrenamiento real.",
    )
    return parser.parse_args()


QUALITY_REPORT_PATH = PROJECT_ROOT / "data" / "video_training" / "reports" / "pose_quality_report.csv"


def _ensure_landmarks(row: dict) -> Path:
    path = landmark_output_path(row)
    if path.exists():
        return path
    print(f"  · extrayendo pose (faltaba): {row['filename']}")
    extract_video_features(row, frame_step=FRAME_STEP, force=False, save_landmarks=True)
    return path


def _load_quality_by_filename() -> dict:
    """pose_detection_rate real (detectados/procesados) + metadatos tecnicos por
    video, desde el reporte que genera 02_extract_pose_features.py."""
    out: dict[str, dict] = {}
    if not QUALITY_REPORT_PATH.exists():
        return out
    with QUALITY_REPORT_PATH.open("r", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[str(r.get("filename"))] = r
    return out


def main() -> int:
    args = parse_args()
    rows = read_manifest(MANIFEST_PATH)
    if not rows:
        print("manifest.csv vacio. Ejecute 01_build_video_manifest.py.")
        return 1

    output_path = Path(args.output) if args.output else DATASET_PATH
    meta_path = Path(args.meta_output) if args.meta_output else (
        output_path.parent / (output_path.stem + "_meta.json")
        if args.output else DATASET_META_PATH
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    active_classes = (
        load_active_class_names(args.active_classes_config)
        if args.active_classes_config else list(CLASS_NAMES)
    )
    active_label_of = {name: idx for idx, name in enumerate(active_classes)}
    eligibility = (
        load_training_eligibility(args.training_eligibility_csv)
        if args.training_eligibility_csv else None
    )

    print(f"  clases activas para esta corrida: {active_classes}")
    if args.output and args.output != str(DATASET_PATH):
        print(f"  salida: {output_path}  (NO sobrescribe el dataset.npz del modelo desplegado)")
    if eligibility is not None:
        print(f"  manifest de elegibilidad: {args.training_eligibility_csv} ({len(eligibility)} filas)")

    DEEP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    quality_by_file = _load_quality_by_filename()

    X_seq: list[np.ndarray] = []
    X_feat: list[np.ndarray] = []
    y: list[int] = []
    subject_ids: list[str] = []
    subject_documented: list[bool] = []
    video_paths: list[str] = []
    conditions: list[str] = []
    severities: list[str] = []
    pose_rates: list[float] = []
    tech: dict[str, list[float]] = {k: [] for k in (
        "duration_seconds", "fps", "width", "height", "total_frames",
        "processed_frames", "valid_pose_frames",
    )}

    excluded: list[dict] = []
    per_class_frames: dict[str, list[int]] = defaultdict(list)

    for index, row in enumerate(rows, start=1):
        condition = str(row.get("condition"))
        filename = str(row.get("filename"))

        if condition not in active_label_of:
            excluded.append({
                "filename": filename, "condition": condition,
                "reason": f"clase '{condition}' no esta en active_class_names {active_classes}",
            })
            continue

        if eligibility is not None:
            status = eligibility.get(filename)
            if status != "TRAINING_ELIGIBLE":
                excluded.append({
                    "filename": filename, "condition": condition,
                    "reason": f"training_status='{status}' en {args.training_eligibility_csv} (no es TRAINING_ELIGIBLE)",
                })
                continue

        if not args.ignore_quality_gate:
            q_flag = quality_by_file.get(filename, {}).get("valid_for_training", "")
            if str(q_flag).strip().lower() == "false":
                excluded.append({
                    "filename": filename, "condition": condition,
                    "reason": (
                        f"pose_quality_report.csv marca valid_for_training=False "
                        f"(quality_warning={quality_by_file.get(filename, {}).get('quality_warning')}, "
                        f"pose_detection_rate={quality_by_file.get(filename, {}).get('pose_detection_rate')})"
                    ),
                })
                continue

        label = active_label_of[condition]

        landmark_csv = _ensure_landmarks(row)
        if not landmark_csv.exists():
            excluded.append({"filename": row.get("filename"), "reason": "sin landmarks"})
            continue

        frames, _quality = read_landmarks_for_features(landmark_csv)
        # pose_detection_rate REAL (frames con pose / frames procesados) desde el
        # reporte de 02_. El CSV de landmarks solo guarda frames con pose, asi que
        # read_landmarks_for_features / frames_to_sequence devuelven ~1.0.
        q = quality_by_file.get(str(row.get("filename")), {})
        def _qf(key, default=0.0):
            try:
                return float(q.get(key))
            except (TypeError, ValueError):
                return default
        real_pose_rate = _qf("pose_detection_rate", 1.0)
        sequence, _seq_pose_rate, n_valid = frames_to_sequence(frames)
        pose_rate = real_pose_rate
        if sequence is None:
            excluded.append(
                {
                    "filename": row.get("filename"),
                    "condition": condition,
                    "reason": f"frames validos insuficientes ({n_valid})",
                }
            )
            continue

        # 36 features de marcha (reutiliza build_feature_row del pipeline historico)
        feature_row = feature_row_from_landmark_csv(landmark_csv, row)
        feat_vector = extract_feature_vector(feature_row)

        X_seq.append(sequence)
        X_feat.append(feat_vector)
        y.append(label)
        subject_ids.append(str(row.get("subject_id")))
        subject_documented.append(str(row.get("subject_documented")).lower() == "true")
        video_paths.append(str(row.get("video_path")))
        conditions.append(condition)
        severities.append(str(row.get("severity")))
        pose_rates.append(round(float(pose_rate), 4))
        for key in tech:
            tech[key].append(_qf(key))
        per_class_frames[condition].append(n_valid)

        if index % 20 == 0 or index == len(rows):
            print(f"  procesados {index}/{len(rows)}")

    if not X_seq:
        print("No se pudo construir ninguna secuencia.")
        return 1

    X_seq_arr = np.stack(X_seq).astype(np.float32)          # [N, C, T]
    X_feat_arr = np.stack(X_feat).astype(np.float32)        # [N, 36]
    y_arr = np.asarray(y, dtype=np.int64)
    subj_arr = np.asarray(subject_ids)
    subj_doc_arr = np.asarray(subject_documented)

    np.savez_compressed(
        output_path,
        X_seq=X_seq_arr,
        X_feat=X_feat_arr,
        y=y_arr,
        subject_id=subj_arr,
        subject_documented=subj_doc_arr,
        video_path=np.asarray(video_paths),
        condition=np.asarray(conditions),
        severity=np.asarray(severities),
        pose_rate=np.asarray(pose_rates, dtype=np.float32),
        tech_duration_s=np.asarray(tech["duration_seconds"], dtype=np.float32),
        tech_fps=np.asarray(tech["fps"], dtype=np.float32),
        tech_width=np.asarray(tech["width"], dtype=np.float32),
        tech_height=np.asarray(tech["height"], dtype=np.float32),
        tech_total_frames=np.asarray(tech["total_frames"], dtype=np.float32),
        tech_processed_frames=np.asarray(tech["processed_frames"], dtype=np.float32),
        tech_valid_pose_frames=np.asarray(tech["valid_pose_frames"], dtype=np.float32),
        class_names=np.asarray(active_classes),
        feature_names=np.asarray(FEATURE_COLUMNS),
        channel_count=np.asarray([NUM_CHANNELS]),
        sequence_length=np.asarray([SEQUENCE_LENGTH]),
    )

    # ---- resumen y limitaciones ----
    class_counts = Counter(conditions)
    subj_by_class = defaultdict(set)
    for cond, subj in zip(conditions, subject_ids):
        subj_by_class[cond].add(subj)

    meta = {
        "dataset_path": str(output_path.relative_to(PROJECT_ROOT)) if output_path.is_relative_to(PROJECT_ROOT) else str(output_path),
        "n_samples": int(X_seq_arr.shape[0]),
        "sequence_shape": [int(X_seq_arr.shape[1]), int(X_seq_arr.shape[2])],
        "n_features": int(X_feat_arr.shape[1]),
        "frame_step": FRAME_STEP,
        "class_names": active_classes,
        "class_names_full_taxonomy": list(CLASS_NAMES),
        "active_classes_config": args.active_classes_config,
        "training_eligibility_csv": args.training_eligibility_csv,
        "videos_per_class": {name: int(class_counts.get(name, 0)) for name in active_classes},
        "subjects_per_class": {name: len(subj_by_class.get(name, set())) for name in active_classes},
        "documented_subjects_per_class": {
            name: len(
                {
                    s
                    for s, c, d in zip(subject_ids, conditions, subject_documented)
                    if c == name and d
                }
            )
            for name in active_classes
        },
        "valid_frames_per_class": {
            name: {
                "min": int(np.min(per_class_frames[name])) if per_class_frames.get(name) else 0,
                "median": int(np.median(per_class_frames[name])) if per_class_frames.get(name) else 0,
                "max": int(np.max(per_class_frames[name])) if per_class_frames.get(name) else 0,
            }
            for name in active_classes
        },
        "mean_pose_rate": round(float(np.mean(pose_rates)), 4),
        "real_pose_rate_per_class": {
            name: {
                "mean": round(float(np.mean([pr for pr, c in zip(pose_rates, conditions) if c == name])), 4),
                "min": round(float(np.min([pr for pr, c in zip(pose_rates, conditions) if c == name])), 4),
            }
            for name in active_classes
        },
        "tech_per_class": {
            name: {
                key: round(float(np.mean([v for v, c in zip(tech[key], conditions) if c == name])), 3)
                for key in tech
            }
            for name in active_classes
        },
        "excluded": excluded,
        "n_excluded": len(excluded),
        "exclusiones": [{"filename": k, "motivo": v} for k, v in
                        getattr(__import__("video_training_common"), "MANIFEST_EXCLUDE", {}).items()],
        "limitations": [
            "esclerosis_multiple y riesgo_caida: los nombres de archivo NO contienen "
            "identificador de sujeto; se asume 1 video == 1 sujeto (subject_documented=False). "
            "Si varios videos correspondieran a la misma persona, la validacion por "
            "sujeto podria ser optimista para esas dos clases.",
            "parkinson: 28 videos de solo 7 sujetos documentados; los niveles PD_ML "
            "(6 sujetos), PD_MD (7 sujetos) y PD_SV (1 sujeto / 2 videos) comparten "
            "numeracion de sujeto y se tratan como el mismo sujeto. La severidad se "
            "conserva como METADATO, NO como objetivo del modelo: con 1 solo sujeto "
            "'severe' no es defendible una cabeza de clasificacion de severidad.",
            "riesgo_caida NO es una enfermedad mutuamente excluyente de Parkinson o "
            "Esclerosis Multiple. Con este dataset (carpetas disjuntas, 1 etiqueta por "
            "video, sin anotaciones multi-etiqueta) la clasificacion en 4 clases "
            "excluyentes es una APROXIMACION operativa: el sistema devuelve el patron "
            "mas compatible y expone las 4 probabilidades (una persona podria mostrar "
            "P(parkinson) y P(riesgo_caida) altas a la vez). No se afirma exclusividad clinica.",
            "Fuente de grabacion: normal+parkinson (.MOV, 1920x1080, ~33-40 fps) y "
            "esclerosis_multiple+riesgo_caida (.mp4, 1280x720, 24 fps) provienen de "
            "colecciones distintas. Un clasificador que usa SOLO metadatos tecnicos "
            "(sin marcha) separa las 4 clases con ~89% -> parte de la separacion "
            "entre-fuentes puede deberse a artefactos de grabacion. Ver auditoria de "
            "sesgo de fuente (models/gait_deep/audit/source_bias_report.json) y los "
            "modelos dentro-de-fuente (23_experiments) que si controlan ese confound.",
            "Dataset pequeno (136 videos / 86 sujetos): la metrica de un unico split "
            "de validacion cruzada tiene varianza alta (~±0.04 macro-F1); se reporta "
            "media±desv sobre 5 semillas de particion.",
        ],
    }
    write_json(meta_path, meta)

    print("\n=== DATASET DE SECUENCIAS CONSTRUIDO ===")
    print(f"  archivo         : {output_path}")
    print(f"  meta            : {meta_path}")
    print(f"  clases activas  : {active_classes}")
    print(f"  muestras        : {meta['n_samples']}  (excluidas: {meta['n_excluded']})")
    print(f"  forma secuencia : {meta['sequence_shape']}  (+ {meta['n_features']} features)")
    print(f"  videos/clase    : {meta['videos_per_class']}")
    print(f"  sujetos/clase   : {meta['subjects_per_class']}")
    print(f"  sujetos docs.   : {meta['documented_subjects_per_class']}")
    print(f"  pose_rate medio : {meta['mean_pose_rate']}")
    if excluded:
        print("  EXCLUIDOS:")
        for item in excluded:
            print(f"    - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
