"""Comparacion final V4 base / V4 BN (activo) / V5-P / V5-C: mismos 117 videos, grupos y particiones. Bootstrap por grupo de sujeto (2000);
las 5 semillas se promedian, no se tratan como independientes. Aplica los criterios pre-registrados en PREREGISTRO_V5C.md."""
import json, sys
from math import comb
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19"
sys.path.insert(0, str(OLD / "codigo"))
from data_v5 import V4
NEW = HERE.parent / "resultados"; FIG = HERE.parent / "figuras"
SEEDS = [42, 43, 44, 45, 46]; CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
z = np.load(V4 / "dataset_v4_preview.npz"); y = z["y"]; g = z["split_group"].astype(str); N = len(y)
pz = np.load(V4 / "step18_bn/oof_probabilities.npz"); pp = np.load(OLD / "resultados/oof_V5P.npz"); pc = np.load(NEW / "oof_V5C.npz"); pr = np.load(NEW / "oof_V5CR.npz")
M = {"V4 base": np.stack([pz[f"A_{s}"] for s in SEEDS]), "V4 BN (activo)": np.stack([pz[f"B_{s}"] for s in SEEDS]),
     "V5-P": np.stack([pp[f"p{s}"] for s in SEEDS]), "V5-C": np.stack([pc[f"p{s}"] for s in SEEDS]), "V5-CR": np.stack([pr[f"p{s}"] for s in SEEDS])}
CAL = {"V5-P": np.stack([pp[f"c{s}"] for s in SEEDS]), "V5-C": np.stack([pc[f"c{s}"] for s in SEEDS]), "V5-CR": np.stack([pr[f"c{s}"] for s in SEEDS])}


def ece(P, yy, nb=10):
    cf = P.max(1); ok = P.argmax(1) == yy; e = 0
    for lo in np.linspace(0, 1, nb, endpoint=False):
        m = (cf > lo) & (cf <= lo + 1 / nb)
        if m.any(): e += m.mean() * abs(ok[m].mean() - cf[m].mean())
    return e


def stats(PP, idx):
    r = []
    for P in PP:
        P = P[idx]; yy = y[idx]; c = np.zeros((4, 4), int)
        for t, p in zip(yy, P.argmax(1)): c[t, p] += 1
        tp = np.diag(c).astype(float); Pr = tp / np.maximum(c.sum(0), 1); Rc = tp / np.maximum(c.sum(1), 1); F = np.where(Pr + Rc > 0, 2 * Pr * Rc / np.maximum(Pr + Rc, 1e-12), 0)
        r.append(dict(acc=tp.sum() / c.sum(), mf1=F.mean(), F=F, R=Rc, brier=np.mean(((P - np.eye(4)[yy]) ** 2).sum(1)), ece=ece(P, yy), c=c))
    return {k: np.mean([x[k] for x in r], 0) for k in r[0]}


full = np.arange(N); S = {k: stats(v, full) for k, v in M.items()}
ug = np.unique(g); gi = {u: np.where(g == u)[0] for u in ug}; rng = np.random.default_rng(20261119)
BOOT = [np.concatenate([gi[u] for u in rng.choice(ug, len(ug))]) for _ in range(2000)]
BS = {k: [stats(v, b) for b in BOOT] for k, v in M.items()}


def diff(a, b, key):
    d = np.array([x[key] - w[key] for x, w in zip(BS[a], BS[b])]); obs = S[a][key] - S[b][key]
    return {"obs": np.round(obs, 4).tolist(), "lo": np.round(np.percentile(d, 2.5, 0), 4).tolist(), "hi": np.round(np.percentile(d, 97.5, 0), 4).tolist()}


def maj(P): return np.array([np.bincount(P[:, i].argmax(1), minlength=4).argmax() for i in range(N)])


OUT = {"modelos": {}, "diferencias": {}}
for k in M:
    OUT["modelos"][k] = {"accuracy": round(float(S[k]["acc"]), 4), "macro_f1": round(float(S[k]["mf1"]), 4), "f1": np.round(S[k]["F"], 4).tolist(), "recall": np.round(S[k]["R"], 4).tolist(),
                         "brier": round(float(S[k]["brier"]), 4), "ece_crudo": round(float(S[k]["ece"]), 4), "matriz_confusion": np.sum([x for x in [np.array(c) for c in [S[k]["c"] * 5]]], 0).round().astype(int).tolist(),
                         "mf1_por_semilla": [round(float(stats(M[k][i:i + 1], full)["mf1"]), 4) for i in range(5)]}
for k, P in CAL.items():
    OUT["modelos"][k]["ece_calibrado_por_fold"] = round(float(np.mean([ece(p, y) for p in P])), 4)
    OUT["modelos"][k]["brier_calibrado"] = round(float(np.mean([np.mean(((p - np.eye(4)[y]) ** 2).sum(1)) for p in P])), 4)
for a_, b_ in (("V5-C", "V5-P"), ("V5-C", "V4 BN (activo)"), ("V5-C", "V4 base"), ("V5-P", "V4 BN (activo)"), ("V5-CR", "V5-C"), ("V5-CR", "V5-P"), ("V5-CR", "V4 BN (activo)"), ("V5-CR", "V4 base")):
    d = {key: diff(a_, b_, key) for key in ("mf1", "acc", "F", "R", "ece")}
    A_, B_ = maj(M[a_]) == y, maj(M[b_]) == y; n01, n10 = int((A_ & ~B_).sum()), int((~A_ & B_).sum()); n = n01 + n10
    d["mcnemar_voto"] = {"solo_primero": n01, "solo_segundo": n10, "p_exacto": round(min(1, 2 * sum(comb(n, k) for k in range(min(n01, n10) + 1)) / 2 ** n), 4) if n else 1}
    OUT["diferencias"][f"{a_} - {b_}"] = d
lab = np.isin(y, [0, 1])
for k in M:
    OUT["modelos"][k]["acc_normal+parkinson"] = round(float(np.mean([(P[lab].argmax(1) == y[lab]).mean() for P in M[k]])), 4)
    OUT["modelos"][k]["acc_EM+riesgo"] = round(float(np.mean([(P[~lab].argmax(1) == y[~lab]).mean() for P in M[k]])), 4)
# criterios pre-registrados
rob = json.load(open(NEW / "fase4_robustez_v5C.json", encoding="utf-8"))
tr = [r for r in rob["pruebas"] if r["prueba"].startswith("camara que sigue a la persona (100")][0]
dC = OUT["diferencias"]["V5-C - V4 BN (activo)"]; dCP = OUT["diferencias"]["V5-C - V5-P"]
crit = {"1_robustez_camara_sigue_dF1>=-0.05": {"valor": tr["delta_macro_f1"], "IC95": tr["IC95_delta_(bootstrap por sujeto)"], "cumple": bool(tr["delta_macro_f1"] >= -0.05)},
        "2a_lim_inferior_IC(V5C-V4BN)_macroF1>-0.05": {"valor": dC["mf1"]["lo"], "cumple": bool(dC["mf1"]["lo"] > -0.05)},
        "2b_ninguna_clase_pierde>0.10_vs_V5P": {"dF1_por_clase": dCP["F"]["obs"], "cumple": bool(min(dCP["F"]["obs"]) >= -0.10)}}
p3 = json.load(open(NEW / "fase8_pruebas_c.json", encoding="utf-8")); crit["3_pruebas_numericas"] = {"cumple": all(r["resultado"] == "PASS" for r in p3)}
crit["TODOS_LOS_CRITERIOS"] = bool(all(v["cumple"] for v in crit.values() if isinstance(v, dict)))
OUT["criterios_preregistrados_V5C"] = crit

robR = json.load(open(NEW / "fase4_robustez_v5CR.json", encoding="utf-8"))
trR = [x for x in robR["pruebas"] if x["prueba"].startswith("camara que sigue a la persona (100")][0]
dRC = OUT["diferencias"]["V5-CR - V5-C"]; pR = json.load(open(NEW / "fase8_prueba_cr.json", encoding="utf-8"))
critR = {"1_prueba_numerica_633_ventanas": {"ventanas_con_fuga": pR["ventanas_con_diferencia_bajo_camara_que_sigue(>1e-6)"], "cumple": bool(pR["criterio_1_cumple"])},
         "2_robustez_camara_sigue>=-0.05": {"valor": trR["delta_macro_f1"], "IC95": trR["IC95_delta_(bootstrap por sujeto)"], "cumple": bool(trR["delta_macro_f1"] >= -0.05)},
         "3a_lim_inf_IC(V5CR-V5C)_macroF1>-0.05": {"valor": dRC["mf1"]["lo"], "cumple": bool(dRC["mf1"]["lo"] > -0.05)},
         "3b_ninguna_clase_pierde>0.10_vs_V5C": {"dF1_por_clase": dRC["F"]["obs"], "cumple": bool(min(dRC["F"]["obs"]) >= -0.10)}}
critR["TODOS_LOS_CRITERIOS"] = bool(all(v["cumple"] for v in critR.values() if isinstance(v, dict)))
OUT["criterios_adenda1_V5CR"] = critR; print(json.dumps(critR, ensure_ascii=False, indent=1))
(NEW / "comparacion_final.json").write_text(json.dumps(OUT, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: {x: v[x] for x in ("accuracy", "macro_f1", "f1", "recall", "ece_crudo", "brier", "mf1_por_semilla", "acc_normal+parkinson", "acc_EM+riesgo")} for k, v in OUT["modelos"].items()}, ensure_ascii=False))
print(json.dumps(OUT["diferencias"], ensure_ascii=False)); print(json.dumps(crit, ensure_ascii=False, indent=1))
# figura: tabla de robustez a camara que sigue
fig, ax = plt.subplots(figsize=(7, 3.4))
vals = {}
for nm, f in (("V4 base", "fase8_evidencia_v4.json"), ("V5-P", "fase8_evidencia_v5P.json")):
    d = json.load(open(NEW / f, encoding="utf-8")); vals[nm] = [r["delta_macro_f1"] for r in d["pruebas"]]
vals["V5-C"] = [r["delta_macro_f1"] for r in rob["pruebas"] if r["prueba"].startswith("camara que sigue")]
vals["V5-CR"] = [r["delta_macro_f1"] for r in robR["pruebas"] if r["prueba"].startswith("camara que sigue")]
xs = np.arange(2)
for i, (nm, c) in enumerate((("V4 base", "#6b7280"), ("V5-P", "#c2410c"), ("V5-C", "#0f766e"), ("V5-CR", "#1d4ed8"))):
    ax.bar(xs + (i - 1.5) * 0.2, vals[nm], 0.2, color=c, label=nm)
ax.set_xticks(xs); ax.set_xticklabels(["50 % del avance\ncompensado", "100 % (cámara\nsigue a la persona)"]); ax.axhline(0, color="black", lw=1); ax.set_ylabel("Cambio de F1 macro")
ax.set_title("Sensibilidad a una cámara que sigue a la persona", fontsize=10, loc="left"); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIG / "fig9_camara_que_sigue_con_CR.png", dpi=300)
