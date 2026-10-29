"""
Division TRAIN / VALIDATION / TEST por sujeto (subject-level split), con
verificacion automatica de fuga (leakage) de sujeto entre particiones.

Contexto: 11_train_deep_model.py ya usaba un split por grupo de 2 vias
(grouped_inner_split) para el train/val interno de cada fold de CV. Este
modulo generaliza esa misma idea (GroupShuffleSplit de sklearn, la misma
libreria y el mismo patron que el resto del proyecto) a 3 vias
(TRAIN/VALIDATION/TEST), pensado para el dataset temporal de preparacion del
Dataset V3 (normal+parkinson), donde por ahora no se hace CV sino un split
fijo reproducible.

No se importa desde ningun script de entrenamiento todavia: es un modulo
nuevo, standalone, que se puede invocar como CLI para verificar el split
antes de decidir usarlo en un entrenamiento real.

Uso (verificacion, no entrena nada):
    .venv311\\Scripts\\python.exe scripts\\video_training\\deep\\subject_split.py \\
        --dataset outputs\\dataset_v3\\dataset_v3_normal_parkinson_preview.npz \\
        --seed 42 --val-frac 0.15 --test-frac 0.15
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


class SubjectLeakageError(RuntimeError):
    """Se lanza si dos particiones comparten al menos un sujeto. El pipeline
    de entrenamiento debe detenerse ante este error, nunca intentar
    'arreglarlo' automaticamente moviendo muestras."""


def grouped_subject_split(
    y: np.ndarray,
    groups: np.ndarray,
    seed: int,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    max_attempts: int = 200,
) -> dict[str, np.ndarray]:
    """Divide por SUJETO (nunca por video) en TRAIN / VALIDATION / TEST.

    Garantiza (por construccion, no por casualidad):
      - un sujeto pertenece a exactamente una particion.
      - TRAIN y VALIDATION no comparten sujetos.
      - TRAIN y TEST no comparten sujetos.
      - VALIDATION y TEST no comparten sujetos.

    Es reproducible: la misma `seed` produce siempre el mismo split para el
    mismo (y, groups).

    Estrategia: dos GroupShuffleSplit encadenados (la misma primitiva de
    sklearn que ya usa grouped_inner_split() en 11_train_deep_model.py):
      1) TRAIN+VAL  vs  TEST         (test_frac de los SUJETOS)
      2) TRAIN      vs  VALIDATION   (val_frac / (1-test_frac) del resto)

    Intenta (mejor esfuerzo, sobre `max_attempts` semillas derivadas) que las
    clases presentes en el dataset completo aparezcan tambien en cada
    particion; si el numero de sujetos de alguna clase es demasiado chico
    para lograrlo (p. ej. muy pocos sujetos), NO lo fuerza ni inventa datos:
    devuelve el mejor split encontrado y dispone `warnings` en el resultado
    para que quien llama decida.
    """
    from sklearn.model_selection import GroupShuffleSplit

    y = np.asarray(y)
    groups = np.asarray(groups).astype(str)
    all_idx = np.arange(len(y))
    classes = sorted(set(y.tolist()))

    best = None
    for attempt in range(max_attempts):
        s = seed + attempt
        gss1 = GroupShuffleSplit(n_splits=1, test_size=test_frac, random_state=s)
        trainval_rel, test_rel = next(gss1.split(all_idx, y, groups))

        inner_val_frac = val_frac / max(1e-9, (1.0 - test_frac))
        inner_val_frac = min(max(inner_val_frac, 1e-6), 0.9)
        gss2 = GroupShuffleSplit(n_splits=1, test_size=inner_val_frac, random_state=s + 100000)
        train_rel, val_rel = next(gss2.split(trainval_rel, y[trainval_rel], groups[trainval_rel]))

        train_idx = trainval_rel[train_rel]
        val_idx = trainval_rel[val_rel]
        test_idx = all_idx[test_rel]

        classes_train = set(y[train_idx].tolist())
        classes_val = set(y[val_idx].tolist())
        classes_test = set(y[test_idx].tolist())
        all_covered = classes_train == set(classes) and classes_val == set(classes) and classes_test == set(classes)

        candidate = {
            "seed_used": s,
            "train_idx": train_idx, "val_idx": val_idx, "test_idx": test_idx,
            "all_classes_covered": all_covered,
        }
        if best is None:
            best = candidate
        if all_covered:
            best = candidate
            break

    assert best is not None
    train_idx, val_idx, test_idx = best["train_idx"], best["val_idx"], best["test_idx"]

    train_subjects = set(groups[train_idx].tolist())
    val_subjects = set(groups[val_idx].tolist())
    test_subjects = set(groups[test_idx].tolist())

    warnings: list[str] = []
    if not best["all_classes_covered"]:
        warnings.append(
            f"No se encontro (en {max_attempts} intentos) un split donde las {len(classes)} clases "
            f"esten presentes en las 3 particiones a la vez. Se devuelve el mejor split encontrado; "
            f"revisar manualmente si alguna particion queda sin ejemplos de alguna clase."
        )
    for name, idx in [("TRAIN", train_idx), ("VALIDATION", val_idx), ("TEST", test_idx)]:
        present = set(y[idx].tolist())
        missing = set(classes) - present
        if missing:
            warnings.append(f"{name} no contiene ninguna muestra de las clases: {sorted(missing)}")

    return {
        "seed_requested": seed,
        "seed_used": best["seed_used"],
        "train_idx": train_idx,
        "val_idx": val_idx,
        "test_idx": test_idx,
        "train_subjects": train_subjects,
        "val_subjects": val_subjects,
        "test_subjects": test_subjects,
        "warnings": warnings,
    }


def check_subject_leakage(
    train_subjects: set[str], val_subjects: set[str], test_subjects: set[str], raise_on_leak: bool = True
) -> dict[str, Any]:
    """Comprueba que ninguna particion comparta sujetos con otra. Imprime un
    reporte con el mismo formato solicitado y, si `raise_on_leak` es True
    (por defecto), lanza SubjectLeakageError ante cualquier interseccion no
    vacia -- el pipeline de entrenamiento debe detenerse, no continuar."""
    inter_tv = sorted(train_subjects & val_subjects)
    inter_tt = sorted(train_subjects & test_subjects)
    inter_vt = sorted(val_subjects & test_subjects)

    print("Subject leakage check:")
    print(f"TRAIN subjects: {sorted(train_subjects)}")
    print(f"VALIDATION subjects: {sorted(val_subjects)}")
    print(f"TEST subjects: {sorted(test_subjects)}")
    print()
    print(f"Intersection TRAIN/VALIDATION: {len(inter_tv)}")
    print(f"Intersection TRAIN/TEST: {len(inter_tt)}")
    print(f"Intersection VALIDATION/TEST: {len(inter_vt)}")

    result = {
        "train_subjects": sorted(train_subjects),
        "val_subjects": sorted(val_subjects),
        "test_subjects": sorted(test_subjects),
        "intersection_train_validation": inter_tv,
        "intersection_train_test": inter_tt,
        "intersection_validation_test": inter_vt,
        "ok": not (inter_tv or inter_tt or inter_vt),
    }
    if not result["ok"] and raise_on_leak:
        raise SubjectLeakageError(
            f"FUGA DE SUJETO DETECTADA -- TRAIN/VAL={inter_tv} TRAIN/TEST={inter_tt} VAL/TEST={inter_vt}. "
            "El pipeline se detiene: no se genera ningun split con sujetos compartidos."
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica (sin entrenar) un split TRAIN/VALIDATION/TEST por sujeto sobre un dataset.npz."
    )
    parser.add_argument("--dataset", required=True, help="Ruta a un dataset.npz (con arrays 'y'/'subject_id'/'condition').")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-frac", type=float, default=0.15)
    parser.add_argument("--test-frac", type=float, default=0.15)
    parser.add_argument("--output-json", default=None, help="Si se indica, escribe el reporte completo ahi.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = np.load(args.dataset, allow_pickle=True)
    y = data["y"]
    groups = data["subject_id"]
    conditions = data["condition"] if "condition" in data.files else None
    class_names = list(data["class_names"]) if "class_names" in data.files else None

    print(f"Dataset: {args.dataset}")
    print(f"Muestras: {len(y)}  |  Sujetos unicos: {len(set(groups.tolist()))}")
    if class_names:
        print(f"Clases: {class_names}")
    print()

    split = grouped_subject_split(y, groups, seed=args.seed, val_frac=args.val_frac, test_frac=args.test_frac)
    for w in split["warnings"]:
        print(f"AVISO: {w}")

    leak = check_subject_leakage(split["train_subjects"], split["val_subjects"], split["test_subjects"])

    def _counts(idx):
        vals, counts = np.unique(y[idx], return_counts=True)
        if class_names:
            return {class_names[int(v)]: int(c) for v, c in zip(vals, counts)}
        return {int(v): int(c) for v, c in zip(vals, counts)}

    print()
    print(f"TRAIN      : {len(split['train_idx'])} videos, {len(split['train_subjects'])} sujetos, por clase = {_counts(split['train_idx'])}")
    print(f"VALIDATION : {len(split['val_idx'])} videos, {len(split['val_subjects'])} sujetos, por clase = {_counts(split['val_idx'])}")
    print(f"TEST       : {len(split['test_idx'])} videos, {len(split['test_subjects'])} sujetos, por clase = {_counts(split['test_idx'])}")

    if args.output_json:
        report = {
            "dataset": str(args.dataset),
            "seed_requested": split["seed_requested"],
            "seed_used": split["seed_used"],
            "val_frac": args.val_frac,
            "test_frac": args.test_frac,
            "n_samples": int(len(y)),
            "n_subjects": int(len(set(groups.tolist()))),
            "class_names": class_names,
            "train": {"n_videos": int(len(split["train_idx"])), "subjects": leak["train_subjects"], "per_class": _counts(split["train_idx"])},
            "validation": {"n_videos": int(len(split["val_idx"])), "subjects": leak["val_subjects"], "per_class": _counts(split["val_idx"])},
            "test": {"n_videos": int(len(split["test_idx"])), "subjects": leak["test_subjects"], "per_class": _counts(split["test_idx"])},
            "leakage_check": {
                "intersection_train_validation": leak["intersection_train_validation"],
                "intersection_train_test": leak["intersection_train_test"],
                "intersection_validation_test": leak["intersection_validation_test"],
                "ok": leak["ok"],
            },
            "warnings": split["warnings"],
        }
        Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReporte escrito en {args.output_json}")

    return 0 if leak["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
