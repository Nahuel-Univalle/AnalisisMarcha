"""
Sprint 3 (base) - Prueba de MediaPipe Pose sobre un video de marcha
Autor: Jared Quinteros García

Objetivo:
    Comprobar que MediaPipe Pose puede DETECTAR landmarks (puntos del cuerpo)
    en los frames de un video real. NO calcula parámetros de marcha ni exporta
    datos; es solo la prueba técnica que habilita el Sprint 3.

Uso (IMPORTANTE: usar el entorno Python 3.11, ver nota al final):
    .venv311\\Scripts\\python.exe scripts\\test_pose.py
    .venv311\\Scripts\\python.exe scripts\\test_pose.py videos\\prueba.mp4

Si no se pasa una ruta, usa por defecto: videos/prueba.mp4

NOTA DE ENTORNO:
    MediaPipe NO tiene binarios para Python 3.14 (el de la `.venv` original),
    por lo que la pose NO corre ahí. Este script requiere el entorno
    `.venv311` (Python 3.11) con: mediapipe, opencv-python, numpy.
"""

import os
import sys
from pathlib import Path

# Reduce el ruido de logs de MediaPipe/glog antes de importarlo
os.environ.setdefault("GLOG_minloglevel", "2")

import cv2
import mediapipe as mp

# Evita caracteres ilegibles (mojibake) con las tildes en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ruta por defecto del video (relativa a la raíz del proyecto)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO = PROJECT_ROOT / "videos" / "prueba.mp4"

# Cuántos frames muestrear como máximo (ligero, no procesa todo el video)
TARGET_SAMPLES = 20


def main() -> int:
    # 1. Resolver la ruta del video (argumento opcional o valor por defecto)
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VIDEO

    print("=" * 60)
    print("  PRUEBA DE MEDIAPIPE POSE - Base Sprint 3")
    print("=" * 60)
    print(f"Video: {video_path}")

    # 2. Validar que el archivo existe
    if not video_path.exists():
        print("\nNo existe video de prueba local. Esta prueba se omite.")
        print(f"Ruta esperada: {DEFAULT_VIDEO}")
        return 0

    # 3. Abrir el video con OpenCV
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        print("\n[ERROR] OpenCV no pudo abrir el video.")
        print("        Verifica que el formato sea válido (ej. .mp4) y no esté dañado.")
        capture.release()
        return 1

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    # Paso de muestreo: tomamos ~TARGET_SAMPLES frames repartidos en el video
    step = max(1, total_frames // TARGET_SAMPLES) if total_frames > 0 else 1
    print(f"Frames totales: {total_frames}  |  muestreando 1 de cada {step}")

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    sampled = 0
    detected = 0
    evidence_path = video_path.parent / "pose_frame_1.jpg"
    evidence_saved = False

    print("\nProcesando frames muestreados con MediaPipe Pose...")

    # static_image_mode=True: cada frame muestreado se analiza de forma
    # independiente (no asumimos continuidad entre frames salteados).
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.5,
    ) as pose:
        frame_index = 0
        while sampled < TARGET_SAMPLES:
            ok, frame = capture.read()
            if not ok:
                break  # fin del video

            if frame_index % step == 0:
                sampled += 1
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)

                if results.pose_landmarks:
                    detected += 1
                    print(f"  - Frame {frame_index}: pose detectada [OK]")

                    # Guardamos el PRIMER frame con pose como evidencia visual
                    if not evidence_saved:
                        annotated = frame.copy()
                        mp_drawing.draw_landmarks(
                            annotated,
                            results.pose_landmarks,
                            mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
                        )
                        evidence_saved = cv2.imwrite(str(evidence_path), annotated)
                else:
                    print(f"  - Frame {frame_index}: sin pose")

            frame_index += 1

    capture.release()

    # 4. Resumen final
    print("\n" + "-" * 60)
    print("RESUMEN")
    print(f"  Frames muestreados : {sampled}")
    print(f"  Frames con pose    : {detected}")
    print("-" * 60)

    if sampled == 0:
        print("\n[ERROR] No se pudo muestrear ningún frame del video.")
        return 1

    if detected == 0:
        print("\n[FALLO] MediaPipe se ejecutó correctamente, pero NO detectó ninguna")
        print("        pose en los frames muestreados.")
        print("        Posibles causas: el cuerpo no es visible/completo, poca luz,")
        print("        o el video no muestra una persona con claridad.")
        print("        Sugerencia: usa un video de marcha con la persona de cuerpo")
        print("        entero y bien iluminada.")
        return 1

    print("\n[EXITO] MediaPipe Pose detectó landmarks del cuerpo en el video.")
    if evidence_saved:
        print(f"        Evidencia con landmarks dibujados: {evidence_path}")
    print("        Base lista para el Sprint 3 (extracción de parámetros).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
