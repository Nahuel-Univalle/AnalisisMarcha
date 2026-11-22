"""Package the frozen V5-CR artifact. Never trains or writes research originals."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERSION = "gait_deep_v5exp_V5CR_7e9ed60965fe"
SHA = "7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade"


def prepare():
    source = ROOT / "docs/optimizacion_final_v5_2026-11-19"
    dest = ROOT / "models/gait_deep_v5cr"
    cfg = json.loads((source / f"checkpoints/{VERSION}_config.json").read_text(encoding="utf-8"))
    scaler = json.loads((source / f"checkpoints/{VERSION}_feature_scaler.json").read_text(encoding="utf-8"))
    # The bank records the actual training order; do not truncate the 36 names.
    import numpy as np
    bank = np.load(source / "resultados/dataset_v5cr_bank.npz", allow_pickle=False)
    names = bank["feature_names"].tolist()
    assert names == cfg["feature_names"] and len(names) == 33
    assert all(len(scaler[k]) == 33 for k in ("medians", "means", "stds"))
    weights = source / f"checkpoints/{VERSION}.pt"
    assert hashlib.sha256(weights.read_bytes()).hexdigest() == SHA
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(weights, dest / weights.name)
    shutil.copyfile(source / f"checkpoints/{VERSION}_label_map.json", dest / f"{VERSION}_label_map.json")
    scaler["columns"] = names
    cfg["status"] = "EXPERIMENTAL V5-CR; prototipo orientativo, sin validacion clinica; entrenado con 117 videos"
    for suffix, value in (("config", cfg), ("feature_scaler", scaler)):
        (dest / f"{VERSION}_{suffix}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Vendor only preprocessing. Computation remains byte-for-byte identical;
    # replace research-directory bootstrap with local imports.
    old = ROOT / "docs/mejora_modelo_v5_experimental_2026-11-19/codigo/v5_preproc.py"
    target = ROOT / "scripts/video_training/deep/v5cr"
    target.mkdir(exist_ok=True)
    v = old.read_text(encoding="utf-8")
    v = v.replace('ROOT = Path(__file__).resolve().parents[3]', 'ROOT = Path(__file__).resolve().parents[4]')
    (target / "v5_preproc.py").write_text(v, encoding="utf-8")
    c = (source / "codigo/v5c_preproc.py").read_text(encoding="utf-8")
    c = c.replace('OLD = Path(__file__).resolve().parents[2] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"\nsys.path.insert(0, str(OLD))\nimport v5_preproc as V', 'from . import v5_preproc as V')
    (target / "v5c_preproc.py").write_text(c, encoding="utf-8")
    cr = (source / "codigo/v5cr_preproc.py").read_text(encoding="utf-8")
    start = cr.index('HERE = Path(__file__)')
    end = cr.index('FEATURES_C =')
    cr = cr[:start] + 'from . import v5_preproc as V\nfrom . import v5c_preproc as C\n' + cr[end:]
    (target / "v5cr_preproc.py").write_text(cr, encoding="utf-8")
    (target / "__init__.py").write_text('"""Frozen V5-CR preprocessing; see deployment provenance."""\n', encoding="utf-8")
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.iterdir()) if p.suffix in (".json", ".pt") and p.name != "deployment_manifest.json"}
    (dest / "deployment_manifest.json").write_text(json.dumps({"version": VERSION, "sha256": manifest, "metadata_changes": ["scaler.columns from bank.feature_names (33)", "config.status V5-CR"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "weights_sha256": SHA, "features": len(names), "destination": str(dest)}))


if __name__ == "__main__":
    prepare()
