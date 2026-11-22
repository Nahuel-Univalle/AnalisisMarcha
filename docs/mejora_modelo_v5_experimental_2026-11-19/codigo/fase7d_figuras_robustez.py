"""Figuras de robustez y dependencia (V4 vs V5-P vs V5-S) desde resultados/fase4_robustez_*.json. Tabla CSV por prueba."""
import csv, json, re
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = Path(__file__).resolve().parents[1]; OUT = R / "resultados"; FIG = R / "figuras"
D = {k: json.load(open(OUT / f"fase4_robustez_{k}.json", encoding="utf-8")) for k in ("v4", "v5P", "v5S")}
def key(p): return re.sub(r" \(\d+ caract\.\)", "", p)
tab = {}
for k, d in D.items():
    for r in d["pruebas"]:
        kk = key(r["prueba"])
        if kk.startswith("espejo"): kk = "espejo horizontal fisicamente correcto" if "correcto" in kk else ("espejo horizontal (transformacion V4)" if k == "v4" else "espejo horizontal fisicamente correcto")
        tab.setdefault(kk, {})[k] = r
with open(OUT / "robustez_v4_v5_tabla.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["prueba", "tipo", "V4_dF1", "V4_IC95", "V5P_dF1", "V5P_IC95", "V5S_dF1", "V5S_IC95"])
    for kk, v in tab.items():
        row = [kk, next(iter(v.values()))["tipo"]]
        for k in ("v4", "v5P", "v5S"):
            row += [v[k]["delta_macro_f1"], v[k]["IC95_delta_(bootstrap por sujeto)"]] if k in v else ["", ""]
        w.writerow(row)
def bars(names, fname, title):
    fig, ax = plt.subplots(figsize=(8.5, 0.55 * len(names) + 1.8)); yy = np.arange(len(names))[::-1]
    for off, (k, c, lab) in zip((0.22, 0, -0.22), (("v4", "#6b7280", "V4 base (M1)"), ("v5P", "#c2410c", "V5-P"), ("v5S", "#16a34a", "V5-S"))):
        o = [tab[n][k]["delta_macro_f1"] if k in tab[n] else np.nan for n in names]
        lo = [tab[n][k]["IC95_delta_(bootstrap por sujeto)"][0] if k in tab[n] else np.nan for n in names]; hi = [tab[n][k]["IC95_delta_(bootstrap por sujeto)"][1] if k in tab[n] else np.nan for n in names]
        ax.errorbar(o, yy + off, xerr=[np.array(o) - np.array(lo), np.array(hi) - np.array(o)], fmt="o", ms=4, color=c, capsize=2.5, label=lab)
    ax.axvline(0, color="black", lw=1); ax.set_yticks(yy); ax.set_yticklabels([n.replace("(", "\n(") if len(n) > 52 else n for n in names], fontsize=8); ax.set_xlabel("Cambio de F1 macro respecto a la entrada sin perturbar (IC 95 % por sujeto)")
    ax.set_title(title, fontsize=10, loc="left"); ax.legend(fontsize=8, loc="lower left"); fig.tight_layout(); fig.savefig(FIG / fname, dpi=300); plt.close(fig)
rec = [n for n, v in tab.items() if next(iter(v.values()))["tipo"] == "grabacion"]
bars(rec, "fig5_robustez_grabacion.png", "Sensibilidad a la grabación (landmarks perturbados)")
per = [n for n, v in tab.items() if next(iter(v.values()))["tipo"] in ("permutacion", "ablacion")]
bars(per, "fig6_dependencia_grupos_ramas.png", "Dependencia de ramas y grupos de características")
tmp = [n for n, v in tab.items() if next(iter(v.values()))["tipo"] in ("perturbacion temporal", "espejo")]
bars(tmp, "fig7_perturbaciones_temporales.png", "Perturbaciones temporales y espejo (velocidades recalculadas)")
print("OK", len(tab))
