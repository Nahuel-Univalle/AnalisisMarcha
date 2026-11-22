"""Final read-only integrity audit; writes only new integration evidence."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/integracion_v5cr_2026-11-19"
VERSION = "gait_deep_v5exp_V5CR_7e9ed60965fe"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    allowed = {"src/app/api/analysis/video/route.ts", "src/app/api/admin/summary/route.ts", "src/lib/ml/modelMetrics.ts"}
    hashes, checks = [], []
    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
    for line in (OUT / "MANIFIESTO_SHA256_PREVIO.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"([a-f0-9]{64}) \*(.+)", line)
        if not match: continue
        before, name = match.groups(); after = sha(ROOT / name)
        hashes.append({"path": name, "before": before, "after": after, "changed": before != after})
        check(f"original protected: {name}", name in allowed or before == after)
    extras = [("src/lib/analysis/resultPresentation.ts", "resultPresentation.ts"), ("package.json", "package.json")]
    for name, backup in extras:
        hashes.append({"path": name, "before": sha(OUT / "respaldo_adicional" / backup), "after": sha(ROOT / name), "changed": True})
    backups = {"route.ts": "src/app/api/admin/summary/route.ts", "src_app_api_analysis_video/route.ts": "src/app/api/analysis/video/route.ts", "src_lib_ml/modelMetrics.ts": "src/lib/ml/modelMetrics.ts", "scripts_deep/14_predict_deep_video_v4exp.py": "scripts/video_training/deep/14_predict_deep_video_v4exp.py"}
    for backup, name in backups.items():
        expected = next(h["before"] for h in hashes if h["path"] == name)
        check(f"Claude backup: {backup}", sha(OUT / "respaldo_previo" / backup) == expected)
    source = ROOT / "docs/optimizacion_final_v5_2026-11-19/checkpoints"
    deployed = ROOT / "models/gait_deep_v5cr"
    for suffix, field in (("config", "status"), ("feature_scaler", "columns")):
        original = json.loads((source / f"{VERSION}_{suffix}.json").read_text(encoding="utf-8"))
        final = json.loads((deployed / f"{VERSION}_{suffix}.json").read_text(encoding="utf-8"))
        check(f"deployment metadata: only {suffix}.{field} changed", {k for k in original if original[k] != final[k]} == {field} and original.keys() == final.keys())
    for suffix in (".pt", "_label_map.json"):
        check(f"deployment exact copy: {suffix}", sha(source / f"{VERSION}{suffix}") == sha(deployed / f"{VERSION}{suffix}"))
    for name, folder in [("v5_preproc.py", "mejora_modelo_v5_experimental_2026-11-19"), ("v5c_preproc.py", "optimizacion_final_v5_2026-11-19"), ("v5cr_preproc.py", "optimizacion_final_v5_2026-11-19")]:
        def functions(path):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        check(f"preprocessor AST: all original functions unchanged in {name}", functions(ROOT / f"docs/{folder}/codigo/{name}") == functions(ROOT / f"scripts/video_training/deep/v5cr/{name}"))
    for folder in (ROOT / "models/gait_deep_v5cr", ROOT / "scripts/video_training/deep/v5cr"):
        for p in sorted(folder.iterdir()):
            if p.is_file(): hashes.append({"path": p.relative_to(ROOT).as_posix(), "before": None, "after": sha(p)})
    for name in ["src/lib/ml/activeModel.ts", "scripts/test-v5cr-e2e.mjs", "scripts/test-v5cr-presentation.ts", "scripts/run-v5cr-check.mjs", "scripts/audit-v5cr-integration.py", "scripts/video_training/deep/15_predict_deep_video_v5cr.py", "scripts/video_training/deep/prepare_v5cr_deployment.py", "scripts/video_training/deep/test_v5cr_deployment.py"]:
        hashes.append({"path": name, "before": None, "after": sha(ROOT / name)})
    (OUT / "MANIFIESTO_SHA256_POSTERIOR.json").write_text(json.dumps({"previous_manifest_sha256": sha(OUT / "MANIFIESTO_SHA256_PREVIO.txt"), "files": hashes}, indent=2), encoding="utf-8")
    report = {"checks": checks, "passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks)}
    (OUT / "AUDITORIA_INTEGRIDAD.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "failed": report["failed"], "changed_preexisting_files": [h["path"] for h in hashes if h.get("changed")]}))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
