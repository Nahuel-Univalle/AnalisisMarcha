"""
Sprint 2 - Validación mínima de video con OpenCV
Autor: Jared Quinteros García

Objetivo:
    Comprobar que el entorno Python puede abrir un video de marcha real,
    leerlo y extraer su metadata básica. NO hace estimación de pose ni IA;
    es solo la prueba técnica de que el pipeline de video funciona.

Uso:
    python scripts/test_video.py
    python scripts/test_video.py videos/prueba.mp4

Si no se pasa una ruta, usa por defecto: videos/prueba.mp4
"""

import sys
from pathlib import Path

import cv2

# Evita caracteres ilegibles (mojibake) con las tildes en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ruta por defecto del video (relativa a la raíz del proyecto)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO = PROJECT_ROOT / "videos" / "prueba.mp4"


def main() -> int:
    # 1. Resolver la ruta del video (argumento opcional o valor por defecto)
    if len(sys.argv) > 1:
        video_path = Path(sys.argv[1])
    else:
        video_path = DEFAULT_VIDEO

    print("=" * 60)
    print("  VALIDACIÓN DE VIDEO - Sprint 2 (OpenCV)")
    print("=" * 60)
    print(f"Ruta del video: {video_path}")

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

    # 4. Extraer metadata básica
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps and fps > 0 else 0.0

    print("\n[OK] Video abierto correctamente. Metadata:")
    print(f"     - Frames totales : {frame_count}")
    print(f"     - FPS            : {fps:.2f}")
    print(f"     - Ancho (px)     : {width}")
    print(f"     - Alto (px)      : {height}")
    print(f"     - Duración aprox.: {duration:.2f} s")

    # 5. Leer el primer frame
    success, frame = capture.read()

    if not success or frame is None:
        print("\n[ERROR] No se pudo leer el primer frame del video.")
        capture.release()
        return 1

    # 6. Guardar el primer frame como evidencia
    evidence_path = video_path.parent / "frame_1.jpg"
    saved = cv2.imwrite(str(evidence_path), frame)
    capture.release()

    if not saved:
        print(f"\n[ERROR] No se pudo guardar la evidencia en: {evidence_path}")
        return 1

    print("\n[OK] Primer frame leído y guardado como evidencia:")
    print(f"     {evidence_path}")
    print("\n[EXITO] El entorno puede abrir y procesar el video correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
