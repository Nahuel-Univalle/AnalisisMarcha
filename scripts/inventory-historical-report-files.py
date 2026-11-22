"""Bounded, read-only storage search; no model/dataset traversal or archive extraction."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = Path("C:/Users/fnahu")
OUT = ROOT / "docs/recuperacion_pdf_historicos_2026-11-19"
EXCLUDE = {"node_modules", ".next", ".git", ".venv311", ".venv", "videos", "private-videos", "pose_cache", "modelos_cv_V5CR", "modelos_cv_V5C", "modelos_cv_V5P", "modelos_cv_V5S"}
roots = [(ROOT, None), (HOME / "Downloads", 4), (HOME / "Documents", 5), (HOME / "Desktop", 0)]
roots.append((HOME / "Documents/Codex/2026-11-05/files-pasted-by-the-user-proyecto", None))
for name in ["Documentation", "QA_JMETER_2026_20261105_155207", "COMPARACION_MODELOS_MARCHA_2026-11-19"]:
    roots.append((HOME / "Desktop" / name, 5))
for name in ["OneDrive", "OneDrive - Personal"]:
    if (HOME / name).is_dir(): roots.append((HOME / name, 5))
files, errors, seen, visited = [], [], set(), 0
for root, depth in roots:
    if not root.exists(): continue
    for current, dirs, names in os.walk(root, followlinks=False, onerror=lambda e: errors.append(str(e))):
        visited += 1
        level = len(Path(current).relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in EXCLUDE and not (Path(current) / d).is_symlink() and not (Path(current) / d).is_junction()]
        if depth is not None and level >= depth: dirs[:] = []
        for name in names:
            p = Path(current) / name
            if p in seen: continue
            seen.add(p)
            suffix = p.suffix.lower()
            relevant = suffix == ".pdf" or suffix in (".sql", ".dump", ".bak", ".rar", ".zip", ".7z") or (suffix == ".json" and any(x in str(p).lower() for x in ("report", "informe", "analysis-record", "analysis_result", "debug_last_analysis")))
            if not relevant: continue
            try:
                s = p.stat()
                item = {"path": str(p), "suffix": suffix, "bytes": s.st_size, "modified": s.st_mtime}
                if suffix == ".pdf":
                    item["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
                    item["report_name_candidate"] = any(x in name.lower() for x in ("informe", "marcha", "report", "analisis", "análisis"))
                files.append(item)
            except OSError as exc: errors.append(str(exc))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "INVENTARIO_ARCHIVOS.json").write_text(json.dumps({"roots": [{"path": str(p), "max_depth": d} for p,d in roots], "visited_directories": visited, "files": files, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"directories": visited, "pdfs": sum(f["suffix"]==".pdf" for f in files), "report_pdf_name_candidates": [f["path"] for f in files if f.get("report_name_candidate")], "archives": sum(f["suffix"] in (".rar", ".zip", ".7z") for f in files), "errors": len(errors)}, ensure_ascii=False))
