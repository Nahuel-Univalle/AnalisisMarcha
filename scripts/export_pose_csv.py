"""
Sprint 3 (base) - Exportación de landmarks de pose a CSV
Autor: Jared Quinteros García

Objetivo:
    Reutilizar la detección de MediaPipe Pose ya probada y EXPORTAR las
    coordenadas de los landmarks a un CSV estructurado. NO calcula parámetros
    de marcha ni persiste en base de datos; es solo el paso "pose -> datos".

Uso (usar el entorno Python 3.11):
    .venv311\\Scripts\\python.exe scripts\\export_pose_csv.py
    .venv311\\Scripts\\python.exe scripts\\export_pose_csv.py videos\\prueba.mp4

Si no se pasa una ruta, usa por defecto: videos/prueba.mp4
Salida: outputs/pose_landmarks.csv

NOTA DE ENTORNO:
    MediaPipe NO tiene binarios para Python 3.14 (el de la `.venv` original).
    Este script requiere `.venv311` (Python 3.11) con: mediapipe, opencv-python.
"""

import argparse
import csv
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

# Rutas por defecto (relativas a la raíz del proyecto)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO = PROJECT_ROOT / "videos" / "prueba.mp4"
OUTPUT_CSV = PROJECT_ROOT / "outputs" / "pose_landmarks.csv"

# Cuántos frames muestrear como máximo (por defecto ligero, no procesa todo el video).
# Sprint 4 (Iteración 7): se puede pasar un 2º argumento opcional para muestrear más
# frames y obtener una señal de marcha más densa (mejor cadencia / longitud de paso).
DEFAULT_TARGET_SAMPLES = 20

CSV_HEADER = [
    "frame_index",
    "landmark_index",
    "x",
    "y",
    "z",
    "visibility",
    "image_width",
    "image_height",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Exporta landmarks de MediaPipe Pose a CSV (Sprint 3 base + Sprint 4)."
    )
    # Posicionales opcionales (retrocompatibilidad: <video> <samples>)
    parser.add_argument("video_pos", nargs="?", default=None, help="Ruta del video (posicional, opcional).")
    parser.add_argument("samples_pos", nargs="?", default=None, help="Nº de muestras (posicional, opcional).")
    # Flags (interfaz nueva, usada por la API / flujo dinámico)
    parser.add_argument("--video", default=None, help="Ruta del video a procesar.")
    parser.add_argument("--output", default=None, help="Ruta del CSV de salida (pose_landmarks.csv).")
    parser.add_argument("--samples", type=int, default=None, help="Nº de frames a muestrear.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 1. Resolver la ruta del video: --video > posicional > valor por defecto
    raw_video = args.video or args.video_pos
    video_path = Path(raw_video) if raw_video else DEFAULT_VIDEO

    # 1b. Nº de frames a muestrear: --samples > posicional > por defecto (20).
    #     Sin argumento se mantiene el comportamiento original.
    raw_samples = args.samples if args.samples is not None else args.samples_pos
    try:
        target_samples = int(raw_samples) if raw_samples is not None else DEFAULT_TARGET_SAMPLES
    except (ValueError, TypeError):
        target_samples = DEFAULT_TARGET_SAMPLES
    target_samples = max(1, target_samples)

    # 1c. Ruta del CSV de salida: --output > por defecto (outputs/pose_landmarks.csv)
    output_csv = Path(args.output) if args.output else OUTPUT_CSV

    print("=" * 60)
    print("  EXPORTACIÓN DE LANDMARKS A CSV - Base Sprint 3")
    print("=" * 60)
    print(f"Video: {video_path}")

    # 2. Validar que el archivo existe
    if not video_path.exists():
        print("\n[ERROR] El archivo de video no existe.")
        print(f"        Coloca un video en: {DEFAULT_VIDEO}")
        print("        O ejecuta:  python scripts/export_pose_csv.py <ruta_del_video>")
        return 1

    # 3. Abrir el video con OpenCV
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        print("\n[ERROR] OpenCV no pudo abrir el video.")
        print("        Verifica que el formato sea válido (ej. .mp4) y no esté dañado.")
        capture.release()
        return 1

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total_frames // target_samples) if total_frames > 0 else 1
    print(f"Frames totales: {total_frames}  |  objetivo {target_samples} muestras  |  1 de cada {step}")

    mp_pose = mp.solutions.pose

    sampled = 0
    detected = 0
    rows = []  # filas a escribir en el CSV

    print("\nProcesando frames muestreados con MediaPipe Pose...")

    # static_image_mode=True: cada frame muestreado se analiza por separado.
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.5,
    ) as pose:
        frame_index = 0
        while sampled < target_samples:
            ok, frame = capture.read()
            if not ok:
                break  # fin del video

            if frame_index % step == 0:
                sampled += 1
                height, width = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb)

                if results.pose_landmarks:
                    detected += 1
                    for landmark_index, lm in enumerate(
                        results.pose_landmarks.landmark
                    ):
                        rows.append(
                            [
                                frame_index,
                                landmark_index,
                                lm.x,
                                lm.y,
                                lm.z,
                                lm.visibility,
                                width,
                                height,
                            ]
                        )

            frame_index += 1

    capture.release()

    print(f"  Frames muestreados : {sampled}")
    print(f"  Frames con pose    : {detected}")

    # 4. Si no se detectó nada, no generamos un CSV engañoso
    if detected == 0:
        print("\n[FALLO] MediaPipe se ejecutó, pero NO detectó pose en ningún frame")
        print("        muestreado. No se generó CSV para evitar datos engañosos.")
        print("        Sugerencia: usa un video con la persona de cuerpo entero y")
        print("        bien iluminada.")
        return 1

    # 5. Escribir el CSV (crea la carpeta de salida si no existe)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

    print("\n" + "-" * 60)
    print("RESUMEN")
    print(f"  Frames con pose    : {detected}")
    print(f"  Filas exportadas   : {len(rows)}")
    print(f"  Archivo CSV        : {output_csv}")
    print("-" * 60)
    print("\n[EXITO] Landmarks exportados a CSV correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
