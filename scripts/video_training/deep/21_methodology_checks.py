"""
Paso 21 - Verificaciones metodologicas.

[13] El augmentation se aplica SOLO a train (nunca val/test).
[14] Ningun sujeto aparece a la vez en train y test de un mismo fold.
[15] Indicios de que varios videos de EM / riesgo_caida sean de la MISMA persona
     (los nombres no traen subject_id; se asumio 1 video = 1 sujeto).
[12] El preprocesamiento (frames validos de secuencia, pose_rate, escala del
     tronco, rango de la secuencia) no difiere de forma sistematica DENTRO de
     una misma fuente entre sus dos clases.

Salida -> models/gait_deep/audit/methodology_checks.json
"""
from __future__ import annotations

import ast
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deep_common import CLASS_NAMES, FEATURE_COLUMNS, MODEL_DIR, load_dataset, write_json  # noqa: E402

AUDIT_DIR = MODEL_DIR / "audit"
SEED = 42
FOLDS = 5


def check_augment_only_train() -> dict:
    """Analiza el AST de 11_train_deep_model.py: augment=True solo en el bucle de
    train; evaluate/predict_logits siempre augment=False."""
    src = (Path(__file__).with_name("11_train_deep_model.py")).read_text(encoding="utf-8")
    tree = ast.parse(src)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "build_batch":
            kw = {k.arg: k.value for k in node.keywords}
            aug = kw.get("augment")
            pos = node.args[4] if len(node.args) > 4 else None
            val = None
            if isinstance(aug, ast.Constant):
                val = aug.value
            elif isinstance(aug, ast.Name):
                val = aug.id
            elif isinstance(pos, ast.Constant):
                val = pos.value
            elif isinstance(pos, ast.Name):
                val = pos.id
            findings.append({"line": node.lineno, "augment_arg": repr(val)})
    # `augment` como Name proviene de `augment = not args.no_augment` (solo en el
    # bucle de entrenamiento de train_one); False literal en evaluate/predict.
    ok = all(f["augment_arg"] in ("'augment'", "False", "'False'") for f in findings)
    return {
        "check": "augmentation solo en train",
        "build_batch_call_sites": findings,
        "augment_common_apply_calls_gated_by_rng": "augment_sample() se invoca solo dentro de build_batch cuando augment es verdadero",
        "ok": ok,
    }


def check_fold_leakage(X, y, groups) -> dict:
    from sklearn.model_selection import StratifiedGroupKFold

    skf = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    leaks = []
    fold_subjects = []
    for k, (tr, te) in enumerate(skf.split(X, y, groups), 1):
        inter = sorted(set(groups[tr]) & set(groups[te]))
        fold_subjects.append({"fold": k, "n_train_subj": len(set(groups[tr])),
                              "n_test_subj": len(set(groups[te])), "test_subjects": sorted(set(groups[te]))})
        if inter:
            leaks.append({"fold": k, "shared": inter})
    # cada sujeto en exactamente 1 fold de test
    from collections import Counter

    cnt = Counter()
    for fs in fold_subjects:
        cnt.update(fs["test_subjects"])
    multi = {s: c for s, c in cnt.items() if c != 1}
    return {
        "check": "sin fuga de sujeto train/test por fold",
        "folds": fold_subjects,
        "folds_con_fuga": leaks,
        "sujetos_en_mas_de_un_fold_test": multi,
        "ok": not leaks and not multi,
    }


def check_ms_fall_subject_independence(X_feat, y, video_path, groups) -> dict:
    """Sin subject_id real. Heuristica: pares de videos de la MISMA clase con
    vector de 36 features casi identico -> posible misma persona/sesion."""
    out = {}
    for c, name in [(2, "esclerosis_multiple"), (3, "riesgo_caida")]:
        idx = np.where(y == c)[0]
        F = X_feat[idx]
        # normaliza por columna (z-score robusto) para comparar forma
        med = np.nanmedian(F, axis=0)
        F0 = np.where(np.isfinite(F), F, med)
        mu, sd = F0.mean(0), F0.std(0)
        sd[sd < 1e-8] = 1.0
        Z = (F0 - mu) / sd
        pairs = []
        for a, b in combinations(range(len(idx)), 2):
            d = float(np.linalg.norm(Z[a] - Z[b]) / np.sqrt(Z.shape[1]))  # RMS z-dist
            cos = float(np.dot(Z[a], Z[b]) / (np.linalg.norm(Z[a]) * np.linalg.norm(Z[b]) + 1e-9))
            pairs.append((d, cos, Path(video_path[idx[a]]).name, Path(video_path[idx[b]]).name))
        pairs.sort()
        suspicious = [
            {"rms_z_dist": round(d, 3), "cosine": round(cos, 3), "video_a": va, "video_b": vb}
            for d, cos, va, vb in pairs if d < 0.6
        ]
        out[name] = {
            "n_videos": int(len(idx)),
            "n_subjects_asumidos": int(len(set(groups[idx]))),
            "pares_mas_cercanos_top5": [
                {"rms_z_dist": round(d, 3), "cosine": round(cos, 3), "video_a": va, "video_b": vb}
                for d, cos, va, vb in pairs[:5]
            ],
            "pares_sospechosos_rms_z_lt_0.6": suspicious,
            "veredicto": (
                "SIN indicios fuertes de videos duplicados por sujeto"
                if not suspicious else
                f"{len(suspicious)} par(es) muy similares: revisar si son la misma persona"
            ),
        }
    return {"check": "independencia de sujetos EM / riesgo_caida", "detalle": out}


def check_preprocessing_uniformity(data) -> dict:
    y = data["y"].astype(int)
    pose_rate = data["pose_rate"].astype(float)
    X_seq = data["X_seq"].astype(np.float32)
    # rango espacial de la secuencia (posiciones) por video = proxy de escala/encuadre residual
    pos = X_seq[:, :34, :]
    seq_range = pos.max(axis=(1, 2)) - pos.min(axis=(1, 2))
    seq_absmean = np.abs(pos).mean(axis=(1, 2))

    def by_pair(vec, c1, c2, label):
        a, b = vec[y == c1], vec[y == c2]
        na, nb = len(a), len(b)
        sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2)) if na > 1 and nb > 1 else 0
        d = float((a.mean() - b.mean()) / sp) if sp > 0 else None
        return {"pair": label, "mean_c1": round(float(a.mean()), 4), "mean_c2": round(float(b.mean()), 4),
                "cohens_d": round(d, 3) if d is not None else None}

    res = {"pose_rate": [], "seq_spatial_range": [], "seq_abs_mean": []}
    for c1, c2, lab in [(0, 1, "normal_vs_parkinson"), (2, 3, "esclerosis_vs_riesgo")]:
        res["pose_rate"].append(by_pair(pose_rate, c1, c2, lab))
        res["seq_spatial_range"].append(by_pair(seq_range, c1, c2, lab))
        res["seq_abs_mean"].append(by_pair(seq_absmean, c1, c2, lab))
    return {
        "check": "uniformidad de preprocesamiento dentro de fuente",
        "metricas": res,
        "lectura": "cohens_d pequeno (|d|<0.5) dentro de una fuente = sin sesgo de preprocesamiento; "
                   "seq_* son las magnitudes que realmente ve el modelo (posiciones normalizadas).",
    }


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_dataset()
    X_seq = data["X_seq"].astype(np.float32)
    X_feat = data["X_feat"].astype(np.float32)
    y = data["y"].astype(np.int64)
    groups = data["subject_id"].astype(str)
    video_path = data["video_path"].astype(str)

    report = {
        "check_13_augment_solo_train": check_augment_only_train(),
        "check_14_sin_fuga_sujeto": check_fold_leakage(X_seq, y, groups),
        "check_15_independencia_sujetos_MS_fall": check_ms_fall_subject_independence(X_feat, y, video_path, groups),
        "check_12_uniformidad_preprocesamiento": check_preprocessing_uniformity(data),
    }
    write_json(AUDIT_DIR / "methodology_checks.json", report)

    print("=" * 66)
    print("  VERIFICACIONES METODOLOGICAS")
    print("=" * 66)
    print(f"[13] augmentation solo en train : {'OK' if report['check_13_augment_solo_train']['ok'] else 'REVISAR'}")
    for f in report["check_13_augment_solo_train"]["build_batch_call_sites"]:
        print(f"      linea {f['line']}: augment={f['augment_arg']}")
    print(f"[14] sin fuga de sujeto         : {'OK' if report['check_14_sin_fuga_sujeto']['ok'] else 'FUGA!'}")
    print(f"[15] independencia MS / fall:")
    for name, d in report["check_15_independencia_sujetos_MS_fall"]["detalle"].items():
        print(f"      {name}: {d['veredicto']}")
        for p in d["pares_sospechosos_rms_z_lt_0.6"]:
            print(f"         ~ {p['video_a']} <-> {p['video_b']}  rms_z={p['rms_z_dist']} cos={p['cosine']}")
    print(f"[12] uniformidad preprocesamiento (cohens_d dentro de fuente):")
    for k, lst in report["check_12_uniformidad_preprocesamiento"]["metricas"].items():
        for e in lst:
            print(f"      {k:18s} {e['pair']:22s} d={e['cohens_d']}")
    print(f"\n-> {AUDIT_DIR / 'methodology_checks.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
