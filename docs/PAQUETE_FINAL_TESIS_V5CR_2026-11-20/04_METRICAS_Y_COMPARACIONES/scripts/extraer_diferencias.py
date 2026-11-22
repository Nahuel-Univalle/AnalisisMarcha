"""Extrae, sin modificar nada, las diferencias entre modelos con sus IC95 (bootstrap por grupo de sujeto, 2000 remuestreos) de comparacion_final.json."""
import csv, json
from pathlib import Path
PKG = Path(__file__).resolve().parents[2]; REPO = PKG.parents[1]
src = REPO / "docs/optimizacion_final_v5_2026-11-19/resultados/comparacion_final.json"
d = json.load(open(src, encoding="utf-8"))["diferencias"]
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
rows = []
for comp, v in d.items():
    for name, key in [("exactitud", "acc"), ("f1_macro", "mf1"), ("ece_sin_calibrar", "ece")]:
        if key in v: rows.append([comp, name, v[key]["obs"], v[key]["lo"], v[key]["hi"], "excluye 0" if (v[key]["lo"] > 0 or v[key]["hi"] < 0) else "incluye 0"])
    for key, label in [("F", "f1"), ("R", "sensibilidad")]:
        for i, c in enumerate(CL):
            lo, hi, o = v[key]["lo"][i], v[key]["hi"][i], v[key]["obs"][i]
            rows.append([comp, f"{label}_{c}", o, lo, hi, "excluye 0" if (lo > 0 or hi < 0) else "incluye 0"])
    if "mcnemar_voto" in v:
        m = v["mcnemar_voto"]; rows.append([comp, "mcnemar_voto_mayoritario(solo_primero/solo_segundo/p_exacto)", f"{m['solo_primero']}/{m['solo_segundo']}", "", "", f"p={m['p_exacto']}"])
with open(PKG / "04_METRICAS_Y_COMPARACIONES/DIFERENCIAS_V5CR_VS_OTROS.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["comparacion (primero - segundo)", "metrica", "diferencia_observada", "IC95_inf", "IC95_sup", "interpretacion_IC"]); w.writerows(rows)
print(len(rows), "filas")
