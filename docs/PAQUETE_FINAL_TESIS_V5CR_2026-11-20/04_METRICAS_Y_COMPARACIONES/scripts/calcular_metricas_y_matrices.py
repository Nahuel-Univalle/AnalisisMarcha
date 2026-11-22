"""Recalcula, SOLO LEYENDO las predicciones fuera de partición (OOF) originales, las métricas de V4 base, V4 activo (BN recalibrada),
V5-P, V5-C y V5-CR, las contrasta con los resultados originales guardados y genera las matrices de confusión.

Entradas originales (solo lectura):
  outputs/dataset_v4_4class/dataset_v4_preview.npz           -> y (117), split_group
  outputs/dataset_v4_4class/step18_bn/oof_probabilities.npz  -> A_<semilla> (V4 base), B_<semilla> (V4 activo)
  docs/mejora_modelo_v5_experimental_2026-11-19/resultados/oof_V5P.npz
  docs/optimizacion_final_v5_2026-11-19/resultados/oof_V5C.npz, oof_V5CR.npz   (p<semilla>: probabilidades; c<semilla>: calibradas por partición)
  docs/optimizacion_final_v5_2026-11-19/resultados/comparacion_final.json      (valores originales para contrastar)

Protocolo (idéntico al original de fase8_comparar.py): 5 semillas de partición x 5 particiones externas; cada semilla produce UNA predicción
fuera de partición por video (117). Cada métrica es el promedio de las 5 métricas por semilla. Las 5 semillas NO son muestras independientes.
"""
import csv
import json
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
V4 = REPO / "outputs" / "dataset_v4_4class"
OLD = REPO / "docs" / "mejora_modelo_v5_experimental_2026-11-19" / "resultados"
NEW = REPO / "docs" / "optimizacion_final_v5_2026-11-19" / "resultados"
OUT_M = PKG / "04_METRICAS_Y_COMPARACIONES"
OUT_C = PKG / "05_MATRICES_DE_CONFUSION" / "datos"
SEEDS = [42, 43, 44, 45, 46]
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
CL_ES = ["Normal", "Parkinson", "Esclerosis múltiple", "Riesgo de caída"]

d = np.load(V4 / "dataset_v4_preview.npz")
y = d["y"].astype(int)
g = d["split_group"].astype(str)
bank = np.load(NEW / "dataset_v5cr_bank.npz")
assert (bank["y"] == y).all() and (bank["group"].astype(str) == g).all(), "Las etiquetas/grupos del banco V5 no coinciden con V4"
N = len(y)
pz = np.load(V4 / "step18_bn" / "oof_probabilities.npz")
pp, pc, pr = np.load(OLD / "oof_V5P.npz"), np.load(NEW / "oof_V5C.npz"), np.load(NEW / "oof_V5CR.npz")
MODELS = {
    "V4 base": np.stack([pz[f"A_{s}"] for s in SEEDS]),
    "V4 activo (BN recalibrada)": np.stack([pz[f"B_{s}"] for s in SEEDS]),
    "V5-P": np.stack([pp[f"p{s}"] for s in SEEDS]),
    "V5-C": np.stack([pc[f"p{s}"] for s in SEEDS]),
    "V5-CR": np.stack([pr[f"p{s}"] for s in SEEDS]),
}
CAL = {"V5-P": np.stack([pp[f"c{s}"] for s in SEEDS]), "V5-C": np.stack([pc[f"c{s}"] for s in SEEDS]), "V5-CR": np.stack([pr[f"c{s}"] for s in SEEDS])}
for k, v in MODELS.items():
    assert v.shape == (5, N, 4) and np.allclose(v.sum(-1), 1, atol=1e-4), k


def ece(P, yy, nb=10):
    cf = P.max(1)
    ok = P.argmax(1) == yy
    e = 0.0
    for lo in np.linspace(0, 1, nb, endpoint=False):
        m = (cf > lo) & (cf <= lo + 1 / nb)
        if m.any():
            e += m.mean() * abs(ok[m].mean() - cf[m].mean())
    return e


def conf(P, yy):
    c = np.zeros((4, 4), int)
    for t, p in zip(yy, P.argmax(1)):
        c[t, p] += 1
    return c


def metrics_one(P, idx):
    yy = y[idx]
    P = P[idx]
    c = conf(P, yy)
    tp = np.diag(c).astype(float)
    pr_ = tp / np.maximum(c.sum(0), 1)
    rc = tp / np.maximum(c.sum(1), 1)
    f1 = np.where(pr_ + rc > 0, 2 * pr_ * rc / np.maximum(pr_ + rc, 1e-12), 0)
    return dict(acc=tp.sum() / c.sum(), mf1=f1.mean(), P=pr_, R=rc, F=f1, brier=np.mean(((P - np.eye(4)[yy]) ** 2).sum(1)), ece=ece(P, yy), c=c)


def metrics(PP, idx):
    r = [metrics_one(P, idx) for P in PP]
    return {k: np.mean([x[k] for x in r], 0) for k in r[0]}, r


full = np.arange(N)
S, PER_SEED = {}, {}
for k, v in MODELS.items():
    S[k], PER_SEED[k] = metrics(v, full)

# ---------------------------------------------------------------- 1) métricas por modelo (CSV)
rows = []
for k in MODELS:
    s = S[k]
    cal = k.split(" ")[0] in CAL and k in CAL
    row = {"modelo": k, "exactitud": round(float(s["acc"]), 4), "f1_macro": round(float(s["mf1"]), 4)}
    for i, c in enumerate(CL):
        row[f"precision_{c}"] = round(float(s["P"][i]), 4)
    for i, c in enumerate(CL):
        row[f"sensibilidad_{c}"] = round(float(s["R"][i]), 4)
    for i, c in enumerate(CL):
        row[f"f1_{c}"] = round(float(s["F"][i]), 4)
    row["ece_sin_calibrar"] = round(float(s["ece"]), 4)
    row["ece_calibrado_por_particion"] = round(float(np.mean([ece(p, y) for p in CAL[k]])), 4) if k in CAL else ""
    row["brier_sin_calibrar"] = round(float(s["brier"]), 4)
    row["brier_calibrado_por_particion"] = round(float(np.mean([np.mean(((p - np.eye(4)[y]) ** 2).sum(1)) for p in CAL[k]])), 4) if k in CAL else ""
    row["f1_macro_por_semilla"] = json.dumps([round(float(x["mf1"]), 4) for x in PER_SEED[k]])
    rows.append(row)
with open(OUT_M / "METRICAS_VERIFICADAS_POR_MODELO.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---------------------------------------------------------------- 2) contraste con los resultados originales
orig = json.load(open(NEW / "comparacion_final.json", encoding="utf-8"))["modelos"]
MAP = {"V4 base": "V4 base", "V4 activo (BN recalibrada)": "V4 BN (activo)", "V5-P": "V5-P", "V5-C": "V5-C", "V5-CR": "V5-CR"}
ver = []
for k in MODELS:
    o = orig[MAP[k]]
    s = S[k]
    pairs = [("exactitud", s["acc"], o["accuracy"]), ("f1_macro", s["mf1"], o["macro_f1"]), ("ece_sin_calibrar", s["ece"], o["ece_crudo"]), ("brier_sin_calibrar", s["brier"], o["brier"])]
    pairs += [(f"f1_{c}", s["F"][i], o["f1"][i]) for i, c in enumerate(CL)] + [(f"sensibilidad_{c}", s["R"][i], o["recall"][i]) for i, c in enumerate(CL)]
    if k in CAL:
        pairs.append(("ece_calibrado_por_particion", np.mean([ece(p, y) for p in CAL[k]]), o["ece_calibrado_por_fold"]))
    for name, mine, theirs in pairs:
        ver.append({"modelo": k, "metrica": name, "recalculado_desde_OOF": round(float(mine), 4), "original_comparacion_final_json": theirs,
                    "diferencia_abs": round(abs(round(float(mine), 4) - theirs), 4), "coincide(<=0.0001)": abs(round(float(mine), 4) - theirs) <= 1.0001e-4})
with open(OUT_M / "VERIFICACION_CONTRA_ORIGINALES.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(ver[0].keys()))
    w.writeheader()
    w.writerows(ver)
n_ok = sum(r["coincide(<=0.0001)"] for r in ver)
print(f"verificación: {n_ok}/{len(ver)} valores coinciden con los resultados originales")

# ---------------------------------------------------------------- 3) intervalos bootstrap por grupo de sujeto (semilla fija, 2000 remuestreos)
ug = np.unique(g)
gi = {u: np.where(g == u)[0] for u in ug}
rng = np.random.default_rng(20261120)
BOOT = [np.concatenate([gi[u] for u in rng.choice(ug, len(ug))]) for _ in range(2000)]
ci_rows = []
BS = {}
for k, v in MODELS.items():
    BS[k] = [metrics(v, b)[0] for b in BOOT]
    for name, key, ix in [("exactitud", "acc", None), ("f1_macro", "mf1", None)] + [(f"f1_{c}", "F", i) for i, c in enumerate(CL)] + [(f"sensibilidad_{c}", "R", i) for i, c in enumerate(CL)]:
        vals = np.array([(b[key] if ix is None else b[key][ix]) for b in BS[k]])
        obs = S[k][key] if ix is None else S[k][key][ix]
        ci_rows.append({"modelo": k, "metrica": name, "valor": round(float(obs), 4), "IC95_inf": round(float(np.percentile(vals, 2.5)), 4), "IC95_sup": round(float(np.percentile(vals, 97.5)), 4)})
with open(OUT_M / "INTERVALOS_CONFIANZA_BOOTSTRAP_POR_GRUPO.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(ci_rows[0].keys()))
    w.writeheader()
    w.writerows(ci_rows)

# ---------------------------------------------------------------- 4) matrices de confusión
def maj_vote(P):
    return np.array([np.bincount(P[:, i].argmax(1), minlength=4).argmax() for i in range(N)])


cm_info = {}
for k in ["V4 base", "V4 activo (BN recalibrada)", "V5-P", "V5-C", "V5-CR"]:
    per = np.stack([x["c"] for x in PER_SEED[k]])  # [5,4,4], cada una suma 117
    tag = k.replace(" ", "_").replace("(", "").replace(")", "")
    suma = per.sum(0)  # 585 predicciones (5 por video): enteros reales, NO independientes
    media = per.mean(0)  # promedio por semilla (suma 117; fraccionario)
    tasa = np.mean([c / np.maximum(c.sum(1, keepdims=True), 1) for c in per], 0)  # promedio de matrices normalizadas por clase verdadera
    vm = np.zeros((4, 4), int)
    for t, p in zip(y, maj_vote(MODELS[k])):
        vm[t, p] += 1
    cm_info[k] = dict(suma=suma, media=media, tasa=tasa, voto=vm, tag=tag)
    for name, mat, fmt in [("suma5semillas_enteros", suma, "%d"), ("promedio_por_semilla", media, "%.2f"), ("tasa_por_clase_verdadera", tasa, "%.4f"), ("voto_mayoritario_por_video_enteros", vm, "%d")]:
        with open(OUT_C / f"cm_{tag}__{name}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["clase_verdadera \\ clase_predicha"] + CL)
            for i, c in enumerate(CL):
                w.writerow([c] + [fmt % x for x in mat[i]])
# denominadores
n_cls = np.bincount(y, minlength=4)
with open(OUT_C / "denominadores_y_procedimiento.json", "w", encoding="utf-8") as f:
    json.dump({"videos_por_clase": dict(zip(CL, n_cls.tolist())), "videos_total": int(N), "semillas": SEEDS,
               "predicciones_por_video": 5, "predicciones_totales_en_suma": int(N * 5),
               "suma5semillas_enteros": "suma de las 5 matrices por semilla; denominadores por clase = videos_por_clase x 5; las 5 predicciones de un video NO son independientes",
               "promedio_por_semilla": "media de las 5 matrices (cada una suma 117); valores fraccionarios, no son conteos de videos",
               "tasa_por_clase_verdadera": "media de las 5 matrices normalizadas por fila (clase verdadera); coincide con la sensibilidad media por clase",
               "voto_mayoritario_por_video_enteros": "cada video recibe la clase más votada por las 5 semillas (desempate: menor índice de clase); 117 videos, conteos enteros reales",
               "regla": "no se crean conteos enteros a partir de promedios"}, f, ensure_ascii=False, indent=1)

json.dump({k: {"suma": v["suma"].tolist(), "voto": v["voto"].tolist()} for k, v in cm_info.items()}, open(OUT_C / "matrices_resumen.json", "w", encoding="utf-8"), indent=1)
np.savez(PKG / "06_FIGURAS_Y_GRAFICAS" / "datos" / "_cache_metricas.npz", y=y, g=g)  # solo etiquetas, para otros scripts
print("OK métricas y matrices")
