"""
Pruebas del pipeline Deep Learning de marcha (ejecutable directo, sin pytest).

    .venv311\\Scripts\\python.exe scripts\\video_training\\deep\\test_deep_pipeline.py

Cubre:
  1. Carga del modelo y artefactos (config, scaler, label_map, cv_metrics).
  2. Consistencia entrenamiento<->inferencia: nº de canales, longitud de
     secuencia, orden y nº de features, label_map, temperatura.
  3. Inferencia real con 1 video por clase -> probabilidades suman 1,
     detectedClass presente, confidence en [0,1], orientationText y disclaimer.
  4. Manejo de entrada inválida: video corrupto y video sin persona ->
     modelUsed False (no se emite prediccion con falsa confianza).

Sale con codigo 0 si todo pasa, 1 si algo falla.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "video_training"))
sys.path.insert(0, str(ROOT / "scripts" / "video_training" / "deep"))

PY = sys.executable
PREDICT = ROOT / "scripts" / "video_training" / "deep" / "13_predict_deep_video.py"

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not cond else ""))


def run_predict(video: Path) -> dict:
    out = subprocess.run(
        [PY, str(PREDICT), "--video", str(video)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=240,
    )
    for line in reversed(out.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"sin JSON en la salida de 13_predict:\n{out.stdout[-500:]}\n{out.stderr[-500:]}")


def make_bad_videos(tmp: Path) -> dict[str, Path]:
    import cv2

    corrupt = tmp / "corrupt.mp4"
    corrupt.write_bytes(b"not a video" * 40)
    noperson = tmp / "noperson.mp4"
    vw = cv2.VideoWriter(str(noperson), cv2.VideoWriter_fourcc(*"mp4v"), 30, (320, 240))
    for _ in range(90):
        vw.write((np.random.rand(240, 320, 3) * 255).astype(np.uint8))
    vw.release()
    return {"corrupt": corrupt, "noperson": noperson}


def sample_videos() -> dict[str, Path]:
    v = ROOT / "videos"
    out: dict[str, Path] = {}
    for cls, folder, pat in [
        ("normal", v / "normal", "*.MOV"),
        ("parkinson", v / "parkinson", "*.MOV"),
        ("esclerosis_multiple", v / "esclerosis_multiple", "*.mp4"),
        ("riesgo_caida", v / "riesgo_caida", "*.mp4"),
    ]:
        files = sorted(folder.rglob(pat))
        if files:
            out[cls] = files[len(files) // 2]
    return out


def main() -> int:
    print("=" * 64)
    print("  PRUEBAS DEL PIPELINE DEEP LEARNING DE MARCHA")
    print("=" * 64)

    # ---- 1 + 2. artefactos y consistencia ----
    print("\n[1-2] Artefactos y consistencia entrenamiento<->inferencia")
    from deep_common import (
        CHANNEL_NAMES, CLASS_NAMES, FEATURE_COLUMNS, NUM_CHANNELS, SEQUENCE_LENGTH,
        FeatureScaler, MODEL_CONFIG_PATH, MODEL_WEIGHTS_PATH, FEATURE_SCALER_PATH,
        LABEL_MAP_PATH, CV_METRICS_PATH, build_model, read_json,
    )
    import torch

    for p in (MODEL_WEIGHTS_PATH, MODEL_CONFIG_PATH, FEATURE_SCALER_PATH, LABEL_MAP_PATH, CV_METRICS_PATH):
        check(f"existe {p.name}", p.exists())

    cfg = read_json(MODEL_CONFIG_PATH)
    lm = read_json(LABEL_MAP_PATH)
    scaler = FeatureScaler.from_json(read_json(FEATURE_SCALER_PATH))
    cvm = read_json(CV_METRICS_PATH)

    check("config.in_channels == NUM_CHANNELS (68)", cfg["in_channels"] == NUM_CHANNELS == 68, str(cfg["in_channels"]))
    check("config.sequence_length == 96", cfg["sequence_length"] == SEQUENCE_LENGTH == 96, str(cfg["sequence_length"]))
    check("config.num_features == 36 == len(FEATURE_COLUMNS)", cfg["num_features"] == 36 == len(FEATURE_COLUMNS))
    check("config.num_classes == 4", cfg["num_classes"] == 4)
    check("label_map coincide con CLASS_NAMES", lm["class_names"] == CLASS_NAMES)
    check("label_map.label_to_class 0..3 correcto",
          lm["label_to_class"] == {str(i): n for i, n in enumerate(CLASS_NAMES)})
    check("scaler.columns == FEATURE_COLUMNS (mismo orden)", list(scaler.columns) == list(FEATURE_COLUMNS))
    check("scaler tiene 36 medianas/medias/desv", len(scaler.medians) == len(scaler.means) == len(scaler.stds) == 36)
    check("CHANNEL_NAMES tiene 68 entradas", len(CHANNEL_NAMES) == 68)
    check("config.temperature en [0.5, 3.0]", 0.5 <= float(cfg.get("temperature", 0)) <= 3.0, str(cfg.get("temperature")))
    check("config tiene model_version", bool(cfg.get("model_version")))
    check("config registra exclusiones", "VideoEscleorosis7.mp4" in (cfg.get("dataset_excluded") or []))
    check("cv_metrics tiene estabilidad multi-semilla", "cv_stability_multiseed" in cvm)

    model, mcfg = build_model(cfg)
    model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location="cpu"))
    model.eval()
    with torch.no_grad():
        out = torch.softmax(
            model(torch.randn(2, 68, 96), torch.randn(2, 36)) / float(cfg["temperature"]), dim=-1
        )
    check("forward: salida [2, 4] que suma 1", tuple(out.shape) == (2, 4) and abs(float(out.sum()) - 2.0) < 1e-3)

    # ---- 3. inferencia real, 1 video por clase ----
    print("\n[3] Inferencia real (1 video por clase)")
    samples = sample_videos()
    check("hay video de las 4 clases disponible", len(samples) == 4, str(list(samples)))
    for cls, video in samples.items():
        d = run_predict(video)
        probs = d.get("classProbabilities") or {}
        s = sum(probs.values())
        check(f"{cls}: modelUsed True y modelSource gait_deep_model",
              d.get("modelUsed") is True and d.get("modelSource") == "gait_deep_model")
        check(f"{cls}: 4 probabilidades que suman ~1", len(probs) == 4 and abs(s - 1.0) < 1e-3, f"sum={s:.4f}")
        check(f"{cls}: detectedClass valido", d.get("detectedClass") in CLASS_NAMES)
        conf = d.get("confidence")
        check(f"{cls}: confidence en [0,1]", isinstance(conf, (int, float)) and 0.0 <= conf <= 1.0)
        check(f"{cls}: orientationText y disclaimer presentes", bool(d.get("orientationText")) and bool(d.get("disclaimer")))
        check(f"{cls}: featureHighlights no vacio", len(d.get("featureHighlights") or []) > 0)
        check(f"{cls}: modelVersion presente", bool(d.get("modelVersion")))

    # ---- 4. entrada invalida ----
    print("\n[4] Manejo de entrada invalida")
    with tempfile.TemporaryDirectory() as td:
        bad = make_bad_videos(Path(td))
        dc = run_predict(bad["corrupt"])
        check("video corrupto -> modelUsed False", dc.get("modelUsed") is False, json.dumps(dc)[:160])
        check("video corrupto -> mensaje presente", bool(dc.get("message")))
        dn = run_predict(bad["noperson"])
        check("video sin persona -> modelUsed False (sin falsa confianza)", dn.get("modelUsed") is False, json.dumps(dn)[:160])
        check("video sin persona -> mensaje de calidad", "insuficiente" in (dn.get("message") or "").lower())

    # ---- resumen ----
    print("\n" + "=" * 64)
    print(f"  RESULTADO: {len(PASS)} OK, {len(FAIL)} FALLOS")
    if FAIL:
        print("  FALLOS:", ", ".join(FAIL))
    print("=" * 64)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
