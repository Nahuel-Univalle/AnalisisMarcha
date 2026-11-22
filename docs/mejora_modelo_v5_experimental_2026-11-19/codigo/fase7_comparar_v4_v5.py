"""Fase 7 -- comparacion V4 vs V5 sobre los MISMOS 117 videos, grupos y particiones externas (StratifiedGroupKFold semillas 42-46).
Incertidumbre: bootstrap por GRUPO DE SUJETO (67 grupos); las 5 semillas NO se tratan como conjuntos independientes (el estadistico es la media de las 5).
Salidas: resultados/comparacion_v4_v5.json, comparacion_v4_v5.csv y figuras/*.png (300 dpi)."""
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from data_v5 import V4
OUT = HERE.parent / "resultados"; FIG = HERE.parent / "figuras"
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]; CLS = ["Normal", "Parkinson", "Esclerosis\nmúltiple", "Riesgo\nde caída"]
SEEDS = [42, 43, 44, 45, 46]
z = np.load(V4 / "dataset_v4_preview.npz", allow_pickle=False); y = z["y"]; g = z["split_group"].astype(str); N = len(y)
pz = np.load(V4 / "step18_bn/oof_probabilities.npz")
M = {"V4 base (M1)": np.stack([pz[f"A_{s}"] for s in SEEDS]), "V4 BN (candidato)": np.stack([pz[f"B_{s}"] for s in SEEDS])}
for tag, nm in (("V5P", "V5-P (principal)"), ("V5S", "V5-S (sensibilidad)")):
    f = OUT / f"oof_{tag}.npz"
    if f.exists():
        d = np.load(f); M[nm] = np.stack([d[f"p{s}"] for s in SEEDS])
def conf(P):  # P [N,4]
    c = np.zeros((4, 4), int)
    for t, p in zip(y, P.argmax(1)): c[t, p] += 1
    return c
def prf(c):
    tp = np.diag(c).astype(float); P = tp / np.maximum(c.sum(0), 1); R = tp / np.maximum(c.sum(1), 1); F = np.where(P + R > 0, 2 * P * R / np.maximum(P + R, 1e-12), 0); return P, R, F
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
        Pr, Rc, F = prf(c); r.append(dict(acc=np.trace(c) / c.sum(), mf1=F.mean(), F=F, R=Rc, Pr=Pr, brier=np.mean(((P - np.eye(4)[yy]) ** 2).sum(1)),
                                          nll=-np.mean(np.log(np.clip(P[np.arange(len(yy)), yy], 1e-12, 1))), ece=ece(P, yy)))
    return {k: np.mean([x[k] for x in r], 0) for k in r[0]}, r
full = np.arange(N); S = {k: stats(v, full) for k, v in M.items()}
ug = np.unique(g); gi = {u: np.where(g == u)[0] for u in ug}; brng = np.random.default_rng(20261119)
BOOT = [np.concatenate([gi[u] for u in brng.choice(ug, len(ug))]) for _ in range(2000)]
BS = {k: [stats(v, b)[0] for b in BOOT] for k, v in M.items()}
def diff(a, b, key):  # a - b
    d = np.array([x[key] - w[key] for x, w in zip(BS[a], BS[b])]); obs = S[a][0][key] - S[b][0][key]
    return {"obs": np.round(obs, 4).tolist(), "lo": np.round(np.percentile(d, 2.5, 0), 4).tolist(), "hi": np.round(np.percentile(d, 97.5, 0), 4).tolist(),
            "p_bootstrap_2colas": np.round(np.minimum(1, 2 * np.minimum((d <= 0).mean(0), (d >= 0).mean(0))), 3).tolist()}
OUTJ = {"modelos": {}, "diferencias": {}, "n_bootstrap": len(BOOT), "nota": "IC95 percentil por grupo de sujeto (67 grupos); las 5 semillas se promedian, no se tratan como independientes"}
for k in M:
    st, per = S[k]
    OUTJ["modelos"][k] = {"accuracy": round(float(st["acc"]), 4), "macro_f1": round(float(st["mf1"]), 4), "macro_f1_por_semilla": [round(float(x["mf1"]), 4) for x in per],
                          "f1_por_clase": np.round(st["F"], 4).tolist(), "recall_por_clase": np.round(st["R"], 4).tolist(), "precision_por_clase": np.round(st["Pr"], 4).tolist(),
                          "brier": round(float(st["brier"]), 4), "nll": round(float(st["nll"]), 4), "ece": round(float(st["ece"]), 4),
                          "matriz_confusion_suma_5_semillas": np.sum([conf(P) for P in M[k]], 0).tolist()}
for new in [k for k in M if k.startswith("V5")]:
    for ref in ("V4 base (M1)", "V4 BN (candidato)"):
        OUTJ["diferencias"][f"{new} - {ref}"] = {key: diff(new, ref, key) for key in ("mf1", "acc", "F", "R", "brier", "nll", "ece")}
# voto mayoritario por video + McNemar exacto
from math import comb
def maj(P): return np.array([np.bincount(P[:, i].argmax(1), minlength=4).argmax() for i in range(N)])
for new in [k for k in M if k.startswith("V5")]:
    for ref in ("V4 base (M1)", "V4 BN (candidato)"):
        a, b = maj(M[new]) == y, maj(M[ref]) == y; n01, n10 = int((a & ~b).sum()), int((~a & b).sum()); n = n01 + n10
        pm = min(1, 2 * sum(comb(n, k) for k in range(min(n01, n10) + 1)) / 2 ** n) if n else 1
        OUTJ["diferencias"][f"{new} - {ref}"]["mcnemar_voto_mayoritario"] = {"solo_nuevo_acierta": n01, "solo_referencia_acierta": n10, "p_exacto": round(pm, 4), "aciertos_nuevo": int(a.sum()), "aciertos_ref": int(b.sum())}
lab = np.isin(y, [0, 1])
for k in M:
    OUTJ["modelos"][k]["accuracy_normal+parkinson"] = round(float(np.mean([(P[lab].argmax(1) == y[lab]).mean() for P in M[k]])), 4)
    OUTJ["modelos"][k]["accuracy_EM+riesgo"] = round(float(np.mean([(P[~lab].argmax(1) == y[~lab]).mean() for P in M[k]])), 4)
(OUT / "comparacion_v4_v5.json").write_text(json.dumps(OUTJ, indent=1, ensure_ascii=False), encoding="utf-8")
with open(OUT / "comparacion_v4_v5.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["modelo", "accuracy", "macro_f1", "F1_normal", "F1_parkinson", "F1_EM", "F1_riesgo", "R_normal", "R_parkinson", "R_EM", "R_riesgo", "brier", "nll", "ece"])
    for k, v in OUTJ["modelos"].items(): w.writerow([k, v["accuracy"], v["macro_f1"], *v["f1_por_clase"], *v["recall_por_clase"], v["brier"], v["nll"], v["ece"]])
print(json.dumps({k: {x: v[x] for x in ("accuracy", "macro_f1", "f1_por_clase", "recall_por_clase", "ece", "brier")} for k, v in OUTJ["modelos"].items()}, ensure_ascii=False, indent=0))
for k, v in OUTJ["diferencias"].items():
    print(k, "dF1macro", v["mf1"], "dAcc", v["acc"]["obs"], v["acc"]["lo"], v["acc"]["hi"], "| F1 clase", v["F"]["obs"], "| McNemar", v.get("mcnemar_voto_mayoritario"))
# ----------------------------------------------------------------------------------------------------------- figuras
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100})
col = {"V4 base (M1)": "#6b7280", "V4 BN (candidato)": "#2563eb", "V5-P (principal)": "#c2410c", "V5-S (sensibilidad)": "#16a34a"}
fig, ax = plt.subplots(figsize=(7.5, 4)); xs = np.arange(len(M));
for i, (k, v) in enumerate(OUTJ["modelos"].items()):
    ax.scatter([i] * 5, v["macro_f1_por_semilla"], color=col[k], s=28, zorder=3); ax.hlines(v["macro_f1"], i - .3, i + .3, color="black", lw=2)
ax.set_xticks(xs); ax.set_xticklabels([k.replace(" (", "\n(") for k in M], fontsize=9); ax.set_ylabel("F1 macro OOF"); ax.set_title("F1 macro por repetición de partición (puntos) y media (línea)")
fig.tight_layout(); fig.savefig(FIG / "fig1_f1_macro_por_semilla.png", dpi=300); plt.close(fig)
if "V5-P (principal)" in M:
    d = OUTJ["diferencias"]["V5-P (principal) - V4 base (M1)"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2)); labs = ["F1 macro"] + [c.replace("\n", " ") for c in CLS]
    obs = [d["mf1"]["obs"]] + d["F"]["obs"]; lo = [d["mf1"]["lo"]] + d["F"]["lo"]; hi = [d["mf1"]["hi"]] + d["F"]["hi"]
    yy = np.arange(len(labs))[::-1]; ax.errorbar(obs, yy, xerr=[np.array(obs) - np.array(lo), np.array(hi) - np.array(obs)], fmt="o", color=col["V5-P (principal)"], capsize=4)
    ax.axvline(0, color="black", lw=1); ax.set_yticks(yy); ax.set_yticklabels(labs); ax.set_xlabel("Diferencia V5-P − V4 base (IC 95 % por sujeto)"); ax.set_title("Diferencias pareadas de F1")
    fig.tight_layout(); fig.savefig(FIG / "fig2_diferencias_f1_V5P_vs_V4.png", dpi=300); plt.close(fig)
    fig, axs = plt.subplots(1, 2, figsize=(9, 4))
    for ax, k in zip(axs, ["V4 base (M1)", "V5-P (principal)"]):
        c = np.array(OUTJ["modelos"][k]["matriz_confusion_suma_5_semillas"], float); cn = c / c.sum(1, keepdims=True)
        im = ax.imshow(cn, vmin=0, vmax=1, cmap="Blues"); ax.set_title(k)
        ax.set_xticks(range(4)); ax.set_yticks(range(4)); ax.set_xticklabels(["N", "P", "EM", "R"]); ax.set_yticklabels(["N", "P", "EM", "R"]); ax.set_xlabel("Predicha"); ax.set_ylabel("Real")
        for i in range(4):
            for j in range(4): ax.text(j, i, f"{cn[i, j]:.2f}", ha="center", va="center", color="white" if cn[i, j] > .5 else "black", fontsize=9)
    fig.suptitle("Matriz de confusión normalizada por fila (suma de 5 semillas)"); fig.tight_layout(); fig.savefig(FIG / "fig3_matrices_confusion.png", dpi=300); plt.close(fig)
    fig, ax = plt.subplots(figsize=(5.5, 5)); ax.plot([0, 1], [0, 1], "k--", lw=1)
    for k in ["V4 base (M1)", "V5-P (principal)"]:
        cf = np.concatenate([P.max(1) for P in M[k]]); ok = np.concatenate([P.argmax(1) == y for P in M[k]]); bins = np.linspace(0.25, 1, 7); xm, ym = [], []
        for lo_, hi_ in zip(bins[:-1], bins[1:]):
            m = (cf > lo_) & (cf <= hi_)
            if m.sum() >= 5: xm.append(cf[m].mean()); ym.append(ok[m].mean())
        ax.plot(xm, ym, "o-", color=col[k], label=f"{k} (ECE {OUTJ['modelos'][k]['ece']:.3f})")
    ax.set_xlabel("Confianza predicha"); ax.set_ylabel("Exactitud observada"); ax.legend(fontsize=8); ax.set_title("Diagrama de fiabilidad OOF (probabilidades crudas)")
    fig.tight_layout(); fig.savefig(FIG / "fig4_calibracion.png", dpi=300); plt.close(fig)
print("OK")
