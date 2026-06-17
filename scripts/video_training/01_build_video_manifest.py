from __future__ import annotations

from video_training_common import MANIFEST_PATH, discover_videos, manifest_summary, write_manifest


def main() -> int:
    rows, warnings = discover_videos()
    write_manifest(rows)
    summary = manifest_summary(rows)

    print(f"Manifest generado: {MANIFEST_PATH}")
    for key, value in summary.items():
        print(f"{key}: {value}")

    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if not rows:
        print("No se encontraron videos reales en videos/normal ni videos/parkinson/*.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

