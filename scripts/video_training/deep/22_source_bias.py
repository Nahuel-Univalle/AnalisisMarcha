"""
Paso 22 - ANALISIS DE SESGO DE FUENTE / DATASET.

Pregunta: ¿el modelo separa las clases por el PATRON DE MARCHA o por
caracteristicas accidentales de la grabacion (resolucion, fps, duracion,
relacion de aspecto, iluminacion, nitidez, encuadre, nº de frames, fondo)?

Contexto: normal + parkinson provienen de una coleccion (.MOV, 1920x1080,
nombres NNN_NM/PD); esclerosis_multiple + riesgo_caida de otra (.mp4,
VideoEscleorosis* / RiesgoCaida*). Son DOS FUENTES.

Hace:
  1. Extrae metadatos tecnicos por video (OpenCV): ancho, alto, fps, nº frames,
     duracion, relacion de aspecto, brillo medio/std, nitidez (varianza del
     Laplaciano), saturacion, densidad de bordes (proxy de fondo), y el tamano
     relativo de la persona en el encuadre (desde los landmarks ya extraidos).
  2. Resume esos metadatos por CLASE y por FUENTE (A vs B).
  3. Sondas de clasificacion usando SOLO metadatos (sin marcha), validacion por
     sujeto:
        - 4 clases         -> si acierta mucho, hay confusion con la fuente
        - normal vs parkinson (misma fuente A)  -> deberia ser ~azar
        - EM vs riesgo_caida (misma fuente B)   -> deberia ser ~azar
        - fuente A vs B     -> cuantifica el tamano del confound (sera ~perfecto)
  4. Verifica que el preprocesamiento (nº de frames validos de secuencia,
     pose_rate, escala) no difiera sistematicamente entre clases de una MISMA
     fuente.

Salida -> models/gait_deep/audit/source_bias_report.json  (+ CSV de metadatos)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import CLASS_NAMES, MODEL_DIR, load_dataset, write_json  # noqa: E402
from video_training_common import PROJECT_ROOT, read_landmarks_for_features  # noqa: E402

AUDIT_DIR = MODEL_DIR / "audit"
SOURCE_A = {"normal", "parkinson"}      # .MOV, coleccion NNN_NM/PD
SOURCE_B = {"esclerosis_multiple", "riesgo_caida"}  # .mp4, VideoEscleorosis*/RiesgoCaida*
N_SAMPLE_FRAMES = 12

META_COLS = [
    "width", "height", "aspect_ratio", "fps", "frame_count", "duration_s",
    "brightness_mean", "brightness_std", "sharpness_lap_var", "saturation_mean",
    "edge_density", "person_bbox_height_frac", "person_bbox_width_frac",
    "valid_seq_frames", "pose_rate",
]


def video_metadata(path: Path) -> dict:
    import cv2

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {c: np.nan for c in META_COLS}
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur = n / fps if fps > 0 else 0.0

    idxs = np.linspace(0, max(n - 1, 0), min(N_SAMPLE_FRAMES, max(n, 1)), dtype=int)
    bright, sat, sharp, edges = [], [], [], []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        bright.append(float(gray.mean()))
        sat.append(float(hsv[:, :, 1].mean()))
        sharp.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        e = cv2.Canny(gray, 80, 160)
        edges.append(float((e > 0).mean()))
    cap.release()
    return {
        "width": w, "height": h,
        "aspect_ratio": round(w / h, 4) if h else np.nan,
        "fps": round(fps, 3), "frame_count": n, "duration_s": round(dur, 3),
        "brightness_mean": round(float(np.mean(bright)), 3) if bright else np.nan,
        "brightness_std": round(float(np.std(bright)), 3) if bright else np.nan,
        "sharpness_lap_var": round(float(np.mean(sharp)), 3) if sharp else np.nan,
        "saturation_mean": round(float(np.mean(sat)), 3) if sat else np.nan,
        "edge_density": round(float(np.mean(edges)), 5) if edges else np.nan,
    }


def person_bbox_frac(landmark_csv: Path) -> tuple[float, float, int, float]:
    """Fraccion media del alto/ancho del frame que ocupa el cuerpo (encuadre)."""
    frames, quality = read_landmarks_for_features(landmark_csv)
    hs, ws = [], []
    for fr in frames:
        pts = fr.get("landmarks", {})
        xs = [p["x"] for p in pts.values()]
        ys = [p["y"] for p in pts.values()]
        if len(xs) >= 6:
            hs.append(max(ys) - min(ys))
            ws.append(max(xs) - min(xs))
    vf = len(frames)
    pr = quality.get("pose_detection_rate", 0.0)
    return (
        round(float(np.mean(hs)), 4) if hs else np.nan,
        round(float(np.mean(ws)), 4) if ws else np.nan,
        vf,
        round(float(pr), 4) if pr else 0.0,
    )


def grouped_probe(X, y, groups, n_classes, label):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    res = {}
    for kind, clf in [
        ("logreg", LogisticRegression(max_iter=3000, class_weight="balanced", C=0.5)),
        ("rf", RandomForestClassifier(n_estimators=400, max_depth=6,
                                      class_weight="balanced_subsample", random_state=42)),
    ]:
        pred = np.full(len(y), -1)
        for tr, te in skf.split(X, y, groups):
            pipe = Pipeline([("imp", SimpleImputer(strategy="median")),
                             ("sc", StandardScaler()), ("clf", clf)])
            pipe.fit(X[tr], y[tr])
            pred[te] = pipe.predict(X[te])
        res[kind] = {
            "accuracy": round(float(accuracy_score(y, pred)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(y, pred)), 4),
            "macro_f1": round(float(f1_score(y, pred, average="macro", zero_division=0)), 4),
        }
    chance = round(1.0 / n_classes, 4)
    print(f"  [{label}] chance={chance}  logreg acc={res['logreg']['accuracy']}  rf acc={res['rf']['accuracy']}")
    res["chance_level"] = chance
    return res


def cohens_d(a, b):
    a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return None
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return round(float((a.mean() - b.mean()) / sp), 3) if sp > 0 else None


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_dataset()
    video_path = data["video_path"].astype(str)
    y = data["y"].astype(np.int64)
    groups = data["subject_id"].astype(str)
    conditions = data["condition"].astype(str)

    from video_training_common import landmark_output_path

    print(f"Extrayendo metadatos de {len(video_path)} videos...")
    meta_rows = []
    M = np.full((len(video_path), len(META_COLS)), np.nan)
    for i, vp in enumerate(video_path):
        p = (PROJECT_ROOT / vp.replace("\\", "/"))
        md = video_metadata(p)
        lc = landmark_output_path({"filename": p.name, "video_path": str(p)})
        bh, bw, vf, pr = person_bbox_frac(lc) if lc.exists() else (np.nan, np.nan, 0, 0.0)
        md.update({"person_bbox_height_frac": bh, "person_bbox_width_frac": bw,
                   "valid_seq_frames": vf, "pose_rate": pr})
        for j, c in enumerate(META_COLS):
            M[i, j] = md.get(c, np.nan)
        meta_rows.append({"video": p.name, "subject_id": groups[i],
                          "clase_real": conditions[i], "fuente": "A" if conditions[i] in SOURCE_A else "B", **md})
        if (i + 1) % 40 == 0:
            print(f"  {i + 1}/{len(video_path)}")

    with (AUDIT_DIR / "video_technical_metadata.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(meta_rows[0].keys()))
        w.writeheader(); w.writerows(meta_rows)

    # ---- resumen por clase y por fuente ----
    by_class = {}
    for c, name in enumerate(CLASS_NAMES):
        idx = y == c
        by_class[name] = {col: round(float(np.nanmean(M[idx, j])), 4) for j, col in enumerate(META_COLS)}
    src_a = np.isin(conditions, list(SOURCE_A))
    src_b = np.isin(conditions, list(SOURCE_B))
    by_source = {
        "A_normal_parkinson": {col: round(float(np.nanmean(M[src_a, j])), 4) for j, col in enumerate(META_COLS)},
        "B_esclerosis_riesgo": {col: round(float(np.nanmean(M[src_b, j])), 4) for j, col in enumerate(META_COLS)},
        "cohens_d_A_vs_B": {col: cohens_d(M[src_a, j], M[src_b, j]) for j, col in enumerate(META_COLS)},
    }

    # diferencias DENTRO de fuente (deberian ser pequenas)
    within_diffs = {}
    for pair, (c1, c2) in {
        "normal_vs_parkinson": (0, 1),
        "esclerosis_vs_riesgo": (2, 3),
    }.items():
        within_diffs[pair] = {
            col: cohens_d(M[y == c1, j], M[y == c2, j]) for j, col in enumerate(META_COLS)
        }

    # ---- sondas con SOLO metadatos ----
    print("\nSondas de clasificacion usando SOLO metadatos tecnicos (sin marcha):")
    # excluye pose_rate y valid_seq_frames del set de 'grabacion pura'? -> se
    # incluyen igual porque tambien son proxies de calidad; se reporta aparte.
    probes = {}
    probes["4_clases"] = grouped_probe(M, y, groups, 4, "4 clases / metadatos")
    ab = np.where(src_a, 0, 1)
    probes["fuente_A_vs_B"] = grouped_probe(M, ab, groups, 2, "fuente A vs B / metadatos")
    mA = np.isin(y, [0, 1])
    probes["normal_vs_parkinson_solo_fuenteA"] = grouped_probe(
        M[mA], (y[mA] == 1).astype(int), groups[mA], 2, "normal vs parkinson (fuente A) / metadatos")
    mB = np.isin(y, [2, 3])
    probes["EM_vs_riesgo_solo_fuenteB"] = grouped_probe(
        M[mB], (y[mB] == 3).astype(int), groups[mB], 2, "EM vs riesgo (fuente B) / metadatos")

    report = {
        "contexto": "normal+parkinson = fuente A (.MOV). esclerosis_multiple+riesgo_caida = fuente B (.mp4).",
        "metadatos_por_clase": by_class,
        "metadatos_por_fuente": by_source,
        "diferencias_dentro_de_fuente_cohens_d": within_diffs,
        "sondas_solo_metadatos": probes,
        "lectura": {
            "fuente_A_vs_B": "Se espera ~perfecto: confirma y mide el confound de fuente.",
            "4_clases": "Si acierta MUCHO por encima del azar (0.25) -> parte de la separacion 4-clases se explica por la fuente, no por la marcha.",
            "dentro_de_fuente": "normal-vs-parkinson y EM-vs-riesgo con SOLO metadatos deberian quedar cerca del azar (0.5); si asi es, dentro de una fuente la clase NO se lee de la grabacion y el modelo profundo debe usar la marcha.",
            "preprocesamiento": "person_bbox_*_frac, valid_seq_frames y pose_rate: si difieren fuerte DENTRO de una fuente, habria sesgo de preprocesamiento; entre fuentes distintas es esperable.",
        },
    }
    write_json(AUDIT_DIR / "source_bias_report.json", report)

    print("\nRESUMEN metadatos por fuente (medias):")
    for col in META_COLS:
        a = by_source["A_normal_parkinson"][col]; b = by_source["B_esclerosis_riesgo"][col]
        d = by_source["cohens_d_A_vs_B"][col]
        print(f"  {col:26s} A={a:>12}  B={b:>12}  cohen_d={d}")
    print(f"\n-> {AUDIT_DIR / 'source_bias_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
