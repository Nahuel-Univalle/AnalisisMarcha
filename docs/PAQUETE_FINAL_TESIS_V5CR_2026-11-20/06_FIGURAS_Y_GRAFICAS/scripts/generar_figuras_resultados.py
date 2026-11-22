"""Figuras de resultados de V5-CR generadas SOLO a partir de datos existentes (OOF originales + CSV/JSON del paquete).
No entrena, no modifica resultados. Salida: PNG 300 dpi + SVG + CSV de datos en 06_FIGURAS_Y_GRAFICAS/datos/ y matrices en 05_MATRICES_DE_CONFUSION/.
Ejecutar primero 04_METRICAS_Y_COMPARACIONES/scripts/calcular_metricas_y_matrices.py.
"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
FIG = PKG / "06_FIGURAS_Y_GRAFICAS"
DAT = FIG / "datos"
M05 = PKG / "05_MATRICES_DE_CONFUSION"
M04 = PKG / "04_METRICAS_Y_COMPARACIONES"
OLD = REPO / "docs" / "mejora_modelo_v5_experimental_2026-11-19" / "resultados"
NEW = REPO / "docs" / "optimizacion_final_v5_2026-11-19" / "resultados"
V4D = REPO / "outputs" / "dataset_v4_4class"
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
CL_ES = ["Normal", "Parkinson", "Esclerosis\nmúltiple", "Riesgo de\ncaída"]
CL_ES1 = ["Normal", "Parkinson", "Esclerosis múltiple", "Riesgo de caída"]
SEEDS = [42, 43, 44, 45, 46]
TEAL, TEAL_D, TEAL_L, GREY, ORANGE = "#0B9586", "#124F48", "#CCFCF0", "#8A9A98", "#C2650A"
COLORS = {"V4 base": "#9AA7A5", "V4 activo (BN recalibrada)": "#5E7471", "V5-P": "#C2650A", "V5-C": "#6A9FB5", "V5-CR": TEAL}
plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 100, "savefig.dpi": 300, "axes.edgecolor": "#40605C", "text.color": "#0B2B27", "axes.labelcolor": "#0B2B27"})
SRC = "Fuente: Elaboración propia (2026), a partir de las predicciones fuera de partición guardadas."


def save(fig, name, folder=FIG):
    fig.savefig(folder / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(folder / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("figura", name)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


metrics = {r["modelo"]: r for r in read_csv(M04 / "METRICAS_VERIFICADAS_POR_MODELO.csv")}
ci = {(r["modelo"], r["metrica"]): r for r in read_csv(M04 / "INTERVALOS_CONFIANZA_BOOTSTRAP_POR_GRUPO.csv")}
MODELS = list(metrics)


def cm(model, kind):
    tag = model.replace(" ", "_").replace("(", "").replace(")", "")
    return np.loadtxt(M05 / "datos" / f"cm_{tag}__{kind}.csv", delimiter=",", skiprows=1, usecols=range(1, 5), encoding="utf-8-sig")


y = np.load(DAT / "_cache_metricas.npz")["y"]
n_cls = np.bincount(y, minlength=4)

# ------------------------------------------------------------------ matrices de confusión
def draw_cm(ax, mat, fmt, title, xlabels=CL_ES, ylabels=None, vmax=None, cmap="Greens", pct=False):
    vmax = vmax or mat.max()
    ax.imshow(mat, cmap=cmap, vmin=0, vmax=vmax)
    ax.set_xticks(range(4), xlabels, fontsize=8.5)
    ax.set_yticks(range(4), ylabels or CL_ES1, fontsize=8.5)
    ax.set_xlabel("Clase predicha")
    ax.set_ylabel("Clase verdadera")
    ax.set_title(title, fontsize=10)
    for i in range(4):
        for j in range(4):
            v = mat[i, j]
            ax.text(j, i, (fmt % v) + ("%" if pct else ""), ha="center", va="center", fontsize=10, fontweight="bold" if i == j else "normal",
                    color="white" if v > 0.55 * vmax else "#0B2B27")
    for s in ax.spines.values():
        s.set_visible(True)


def note(fig, text, y0=-0.02):
    fig.text(0.01, y0, text, fontsize=7.5, ha="left", va="top", wrap=True, color="#334")


for model, label in [("V5-CR", "V5-CR"), ("V4 activo (BN recalibrada)", "V4 activo (BN recalibrada)")]:
    tag = "V5CR" if model == "V5-CR" else "V4activo"
    suma, tasa, voto = cm(model, "suma5semillas_enteros"), cm(model, "tasa_por_clase_verdadera") * 100, cm(model, "voto_mayoritario_por_video_enteros")
    ylab = [f"{c}\n(n={n} videos)" for c, n in zip(CL_ES1, n_cls)]
    # A. absoluta (suma de 5 repeticiones)
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    draw_cm(ax, suma, "%d", f"Matriz de confusión de {label}\nvalores absolutos (suma de 5 repeticiones)", ylabels=[f"{c}\n({n*5} pred.)" for c, n in zip(CL_ES1, n_cls)])
    note(fig, "Cada video se predice una vez por semilla (5 semillas de partición, validación cruzada de 5 particiones agrupada por sujeto):\n585 predicciones fuera de partición (117 x 5). Las 5 predicciones de un video NO son independientes;\nlos valores no equivalen a 585 videos ni personas.  " + SRC, -0.03)
    save(fig, f"matriz_confusion_{tag}_A_absoluta_suma5", M05)
    # B. normalizada por clase verdadera
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    draw_cm(ax, tasa, "%.1f", f"Matriz de confusión de {label}\nnormalizada por clase verdadera (%)", ylabels=ylab, vmax=100, pct=True)
    note(fig, "Cada fila es el promedio de las 5 matrices por semilla normalizadas por clase verdadera (la diagonal es la sensibilidad media por clase).\nDenominadores por clase: " + ", ".join(f"{c}={n}" for c, n in zip(CL_ES1, n_cls)) + " videos por semilla.  " + SRC, -0.03)
    save(fig, f"matriz_confusion_{tag}_B_normalizada", M05)
    # C. voto mayoritario por video (117 enteros)
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    draw_cm(ax, voto, "%d", f"Matriz de confusión de {label}\nvoto mayoritario de las 5 semillas (117 videos)", ylabels=ylab)
    note(fig, "Cada video recibe la clase más votada entre sus 5 predicciones fuera de partición (desempate: menor índice de clase).\nConteos enteros de videos (117), pero las predicciones provienen de un mismo conjunto de 67 grupos; evaluación interna.  " + SRC, -0.03)
    save(fig, f"matriz_confusion_{tag}_C_voto_mayoritario", M05)

# D. comparación V4 activo vs V5-CR (mismas particiones y videos)
t4, t5 = cm("V4 activo (BN recalibrada)", "tasa_por_clase_verdadera") * 100, cm("V5-CR", "tasa_por_clase_verdadera") * 100
fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.9))
draw_cm(axs[0], t4, "%.1f", "V4 activo (BN recalibrada)", ylabels=[f"{c}\n(n={n})" for c, n in zip(CL_ES1, n_cls)], vmax=100, pct=True)
draw_cm(axs[1], t5, "%.1f", "V5-CR", ylabels=[f"{c}\n(n={n})" for c, n in zip(CL_ES1, n_cls)], vmax=100, pct=True)
diff = t5 - t4
ax = axs[2]
ax.imshow(diff, cmap="RdBu", vmin=-40, vmax=40)
ax.set_xticks(range(4), CL_ES, fontsize=8.5)
ax.set_yticks(range(4), CL_ES1, fontsize=8.5)
ax.set_xlabel("Clase predicha")
ax.set_ylabel("Clase verdadera")
ax.set_title("Diferencia V5-CR − V4 activo\n(puntos porcentuales)", fontsize=10)
for i in range(4):
    for j in range(4):
        ax.text(j, i, f"{diff[i, j]:+.1f}", ha="center", va="center", fontsize=10, fontweight="bold" if i == j else "normal", color="white" if abs(diff[i, j]) > 24 else "#0B2B27")
for a in axs[1:]:
    a.set_yticklabels([])
    a.set_ylabel("")
fig.subplots_adjust(wspace=0.12)
fig.suptitle("Comparación de matrices de confusión normalizadas por clase verdadera (mismas particiones, semillas y 117 videos)", fontsize=11, fontweight="bold", y=1.03)
note(fig, "Cada matriz es el promedio de las 5 matrices por semilla normalizadas por fila. Las diferencias NO son estadísticamente concluyentes en la mayoría de celdas\n(ver DIFERENCIAS_V5CR_VS_OTROS.csv): solo la mejora de riesgo de caída tiene intervalo que excluye 0. Evaluación interna, sin validación clínica.  " + SRC, -0.02)
save(fig, "matriz_confusion_D_comparacion_V4activo_vs_V5CR", M05)
write_csv(M05 / "datos" / "diferencia_tasas_V5CR_menos_V4activo_puntos_porcentuales.csv", ["clase_verdadera"] + CL, [[CL[i]] + [f"{diff[i, j]:.2f}" for j in range(4)] for i in range(4)])

# ------------------------------------------------------------------ Fig. comparación de exactitud y F1 macro por versión
fig, ax = plt.subplots(figsize=(8.4, 4.4))
x = np.arange(len(MODELS))
rows = []
for k, (name, metric) in enumerate([("Exactitud", "exactitud"), ("F1 macro", "f1_macro")]):
    vals = [float(ci[(m, metric)]["valor"]) for m in MODELS]
    lo = [float(ci[(m, metric)]["IC95_inf"]) for m in MODELS]
    hi = [float(ci[(m, metric)]["IC95_sup"]) for m in MODELS]
    b = ax.bar(x + (k - 0.5) * 0.36, vals, 0.34, color=[COLORS[m] for m in MODELS], alpha=1 if k == 0 else 0.62, edgecolor="white", label=name, hatch="" if k == 0 else "//")
    ax.errorbar(x + (k - 0.5) * 0.36, vals, yerr=[np.array(vals) - lo, np.array(hi) - vals], fmt="none", ecolor="#223", capsize=3, lw=1)
    for xi, v in zip(x + (k - 0.5) * 0.36, vals):
        ax.text(xi, 0.405, f"{v:.3f}", ha="center", fontsize=8, color="white", fontweight="bold", rotation=90)
    for m, v, l, h in zip(MODELS, vals, lo, hi):
        rows.append([m, name, v, l, h])
ax.set_xticks(x, [m.replace(" (", "\n(") for m in MODELS], fontsize=8.5)
ax.set_ylim(0.4, 1.0)
ax.set_ylabel("Valor (promedio de 5 semillas)")
ax.set_title("Exactitud y F1 macro por versión del modelo")
h1 = plt.Rectangle((0, 0), 1, 1, fc="#777")
h2 = plt.Rectangle((0, 0), 1, 1, fc="#777", alpha=0.62, hatch="//")
ax.legend([h1, h2], ["Exactitud", "F1 macro (rayado)"], frameon=False, loc="upper left", fontsize=8.5)
note(fig, "Barras de error: IC95 % por remuestreo (bootstrap) de grupos de sujeto (2000 remuestreos). Validación cruzada agrupada por sujeto, 5 semillas;\nlas semillas no son independientes. La mejora de V5-CR sobre el V4 activo no es estadísticamente concluyente.  " + SRC, -0.02)
save(fig, "fig_comparacion_exactitud_f1macro_por_version")
write_csv(DAT / "fig_comparacion_exactitud_f1macro_por_version.csv", ["modelo", "metrica", "valor", "IC95_inf", "IC95_sup"], rows)

# ------------------------------------------------------------------ Fig. P/R/F1 por clase V5-CR
fig, ax = plt.subplots(figsize=(8, 4.2))
rows = []
for k, (lab, key, col) in enumerate([("Precisión", "precision", "#6A9FB5"), ("Sensibilidad", "sensibilidad", "#C2650A"), ("F1", "f1", TEAL)]):
    vals = [float(metrics["V5-CR"][f"{key}_{c}"]) for c in CL]
    ax.bar(np.arange(4) + (k - 1) * 0.27, vals, 0.26, color=col, label=lab, edgecolor="white")
    for xi, v in zip(np.arange(4) + (k - 1) * 0.27, vals):
        ax.text(xi, v + 0.012, f"{v:.3f}", ha="center", fontsize=7.5)
    for c, v in zip(CL, vals):
        rows.append(["V5-CR", lab, c, v])
ax.set_xticks(range(4), [f"{c}\n(n={n})" for c, n in zip(CL_ES, n_cls)], fontsize=8.5)
ax.set_ylim(0, 1.12)
ax.set_title("V5-CR: precisión, sensibilidad y F1 por clase")
ax.legend(frameon=False, ncol=3, loc="upper right", fontsize=8.5)
note(fig, "Promedio de 5 semillas (validación cruzada agrupada por sujeto, 117 videos). Las clases de esclerosis múltiple y riesgo de caída tienen menor desempeño y\nmás confusión entre sí; los grupos de esas clases son en gran parte provisionales.  " + SRC, -0.02)
save(fig, "fig_V5CR_precision_sensibilidad_f1_por_clase")
write_csv(DAT / "fig_V5CR_precision_sensibilidad_f1_por_clase.csv", ["modelo", "metrica", "clase", "valor"], rows)

# ------------------------------------------------------------------ Fig. F1 macro por semilla
fig, ax = plt.subplots(figsize=(7.4, 4))
rows = []
for i, m in enumerate(MODELS):
    v = json.loads(metrics[m]["f1_macro_por_semilla"])
    ax.scatter([i] * 5 + np.linspace(-0.12, 0.12, 5), v, color=COLORS[m], s=36, zorder=3)
    ax.hlines(np.mean(v), i - 0.25, i + 0.25, color="#111", lw=1.5, zorder=4)
    for s, val in zip(SEEDS, v):
        rows.append([m, s, val])
ax.set_xticks(range(len(MODELS)), [m.replace(" (", "\n(") for m in MODELS], fontsize=8.5)
ax.set_ylabel("F1 macro")
ax.set_title("F1 macro por semilla de partición (línea = promedio)")
note(fig, "Cada punto es una semilla de partición (misma evaluación sobre los 117 videos); la dispersión muestra la variabilidad por partición. " + SRC, -0.02)
save(fig, "fig_f1_macro_por_semilla")
write_csv(DAT / "fig_f1_macro_por_semilla.csv", ["modelo", "semilla", "f1_macro"], rows)

# ------------------------------------------------------------------ Fig. calibración (diagrama de fiabilidad)
d = np.load(V4D / "dataset_v4_preview.npz")
pz = np.load(V4D / "step18_bn" / "oof_probabilities.npz")
pr = np.load(NEW / "oof_V5CR.npz")
sets = {"V5-CR sin calibrar": np.concatenate([pr[f"p{s}"] for s in SEEDS]), "V5-CR calibrado (temperatura por partición)": np.concatenate([pr[f"c{s}"] for s in SEEDS]),
        "V4 activo (probabilidades OOF guardadas)": np.concatenate([pz[f"B_{s}"] for s in SEEDS])}
yy = np.tile(y, 5)
fig, ax = plt.subplots(figsize=(5.6, 5.2))
ax.plot([0, 1], [0, 1], "--", color="#999", lw=1, label="Calibración perfecta")
rows = []
bins = np.linspace(0, 1, 11)
for (lab, P), col, mk in zip(sets.items(), [ORANGE, TEAL, "#5E7471"], ["o", "s", "^"]):
    cf, ok = P.max(1), P.argmax(1) == yy
    xs, ys = [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mm = (cf > lo) & (cf <= hi)
        if mm.sum() >= 10:
            xs.append(cf[mm].mean())
            ys.append(ok[mm].mean())
            rows.append([lab, f"{lo:.1f}-{hi:.1f}", int(mm.sum()), round(float(cf[mm].mean()), 4), round(float(ok[mm].mean()), 4)])
    ax.plot(xs, ys, marker=mk, color=col, lw=1.6, label=lab)
ax.set_xlabel("Confianza media del modelo en el intervalo")
ax.set_ylabel("Exactitud observada en el intervalo")
ax.set_xlim(0.2, 1.02)
ax.set_ylim(0.2, 1.02)
ax.set_title("Diagrama de fiabilidad (predicciones fuera de partición)")
ax.legend(frameon=False, fontsize=8, loc="upper left")
ece_txt = {k: metrics[k] for k in ["V5-CR", "V4 activo (BN recalibrada)"]}
note(fig, f"ECE promedio por semilla: V5-CR sin calibrar {float(ece_txt['V5-CR']['ece_sin_calibrar']):.3f}; V5-CR calibrado {float(ece_txt['V5-CR']['ece_calibrado_por_particion']):.3f}; V4 activo {float(ece_txt['V4 activo (BN recalibrada)']['ece_sin_calibrar']):.3f}.\n"
          "Se agrupan las 5 repeticiones (585 predicciones; intervalos con ≥10 predicciones). Para V4 activo no existen probabilidades calibradas por partición (solo para V4 base: ECE 0,076);\nla comparación directa con V4 activo es solo sin calibrar. " + SRC, -0.02)
save(fig, "fig_calibracion_V5CR_diagrama_fiabilidad")
write_csv(DAT / "fig_calibracion_V5CR_diagrama_fiabilidad.csv", ["serie", "intervalo_confianza", "n_predicciones", "confianza_media", "exactitud_observada"], rows)

# ------------------------------------------------------------------ Robustez
def load_tests(path):
    return json.load(open(path, encoding="utf-8"))["pruebas"]


R = {
    "V4 base": load_tests(OLD / "fase4_robustez_v4.json") + load_tests(NEW / "fase8_evidencia_v4.json"),
    "V5-P": load_tests(OLD / "fase4_robustez_v5P.json") + load_tests(NEW / "fase8_evidencia_v5P.json"),
    "V5-C": load_tests(NEW / "fase4_robustez_v5C.json"),
    "V5-CR": load_tests(NEW / "fase4_robustez_v5CR.json"),
}
TESTS = [("Cámara que sigue a la persona (50 %)", "camara que sigue a la persona (50"), ("Cámara que sigue a la persona (100 %)", "camara que sigue a la persona (100"),
         ("Paneo de cámara 0,05 /s", "paneo de camara"), ("Relación de aspecto ×0,75", "aspecto: x * 0.75"), ("Zoom ×1,3", "zoom x1.3"),
         ("Ruido de landmarks σ=0,005", "jitter de landmarks sigma=0.005"), ("Ruido de landmarks σ=0,01", "jitter de landmarks sigma=0.01"),
         ("Pérdida aleatoria del 20 % de fotogramas", "perdida aleatoria del 20")]
rows, tab = [], {}
for label, key in TESTS:
    for m, tests in R.items():
        hit = [t for t in tests if key in t["prueba"]]
        if hit:
            t = hit[0]
            ic = t.get("IC95_delta_(bootstrap por sujeto)", ["", ""])
            tab[(label, m)] = t["delta_macro_f1"]
            rows.append([label, m, t["macro_f1"], t["delta_macro_f1"], ic[0], ic[1]])
write_csv(M04 / "ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv", ["prueba", "modelo", "f1_macro_con_perturbacion", "delta_f1_macro", "IC95_inf", "IC95_sup"], rows)
shutil_rows = rows
write_csv(DAT / "fig_robustez_delta_f1_macro.csv", ["prueba", "modelo", "f1_macro_con_perturbacion", "delta_f1_macro", "IC95_inf", "IC95_sup"], rows)
fig, ax = plt.subplots(figsize=(9.6, 5))
mods = ["V4 base", "V5-P", "V5-C", "V5-CR"]
yl = np.arange(len(TESTS))
for k, m in enumerate(mods):
    vals = [tab.get((lb, m), np.nan) for lb, _ in TESTS]
    ax.barh(yl + (k - 1.5) * 0.2, vals, 0.19, color=COLORS[m], label=m, edgecolor="white")
    for yi, v in zip(yl + (k - 1.5) * 0.2, vals):
        if np.isnan(v):
            ax.text(0.002, yi, "no evaluado", va="center", fontsize=6.5, color="#777")
        elif abs(v) < 5e-4:
            ax.text(0.002, yi, f"{m}: 0,000", va="center", fontsize=6.5, color=COLORS[m] if m != "V4 base" else "#555", fontweight="bold")
ax.set_yticks(yl, [lb for lb, _ in TESTS], fontsize=8.5)
ax.invert_yaxis()
ax.axvline(0, color="#222", lw=0.8)
ax.set_xlabel("Cambio del F1 macro respecto a la línea base de cada modelo (ΔF1)")
ax.set_xlim(None, 0.075)
ax.set_title("Robustez a perturbaciones de la grabación (modelos congelados)")
ax.legend(frameon=False, fontsize=8.5, loc="lower left")
note(fig, "V4 base = modelo sin recalibración de BatchNorm (V4 activo no fue evaluado con estas perturbaciones). Cada ΔF1 compara el modelo consigo mismo. V5-CR es invariante por construcción\na la traslación global de la cámara, aspecto y zoom (verificado numéricamente), pero no mejora el ruido de landmarks ni la pérdida de fotogramas. " + SRC, -0.02)
save(fig, "fig_robustez_camara_ruido_perdida_fotogramas")

# ------------------------------------------------------------------ Distribución del dataset
man = [r for r in csv.DictReader(open(V4D / "manifest_v4_preview.csv", encoding="utf-8")) if r["include_in_preview"] == "true"]
cnt_v, grp, prov = {c: 0 for c in CL}, {c: set() for c in CL}, {c: set() for c in CL}
src = {}
for r in man:
    cnt_v[r["class"]] += 1
    grp[r["class"]].add(r["split_group"])
    if r["subject_status"] == "provisional":
        prov[r["class"]].add(r["split_group"])
    key = r["source"].split(" ")[0]
    src[(r["class"], key)] = src.get((r["class"], key), 0) + 1
fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.4))
axs[0].set_ylim(0, 66)
axs[0].bar(range(4), [cnt_v[c] for c in CL], color=TEAL)
for i, c in enumerate(CL):
    axs[0].text(i, cnt_v[c] + 1, str(cnt_v[c]), ha="center", fontsize=9)
axs[0].set_title("Videos por clase (117)")
axs[1].bar(np.arange(4) - 0.2, [len(grp[c]) - len(prov[c]) for c in CL], 0.4, color=TEAL, label="Grupos con identidad registrada")
axs[1].bar(np.arange(4) + 0.0 - 0.2, [len(prov[c]) for c in CL], 0.4, bottom=[len(grp[c]) - len(prov[c]) for c in CL], color="#E0A458", label="Grupos provisionales")
for i, c in enumerate(CL):
    axs[1].text(i - 0.2, len(grp[c]) + 0.6, str(len(grp[c])), ha="center", fontsize=9)
axs[1].set_xlim(-0.7, 3.5)
axs[1].set_ylim(0, 36)
axs[1].set_title("Grupos de sujeto por clase (67)")
axs[1].legend(frameon=False, fontsize=7.5, loc="upper right", bbox_to_anchor=(1.0, 1.0))
srcs = ["lab_A", "social_vertical", "clinic_848x478_60fps"]
srcl = ["Laboratorio\n(trípode, 1920×1080)", "Redes sociales\n(vertical)", "Clínica\n(848×478, 60 fps)"]
bot = np.zeros(4)
for s, lab, col in zip(srcs, srcl, [TEAL, "#C2650A", "#6A9FB5"]):
    v = np.array([src.get((c, s), 0) for c in CL])
    axs[2].bar(range(4), v, bottom=bot, color=col, label=lab.replace("\n", " "))
    bot += v
axs[2].set_ylim(0, 72)
axs[2].set_title("Fuente de grabación por clase")
axs[2].legend(frameon=False, fontsize=7.5)
for a in axs:
    a.set_xticks(range(4), CL_ES, fontsize=8)
note(fig, "«Provisional»: la fuente no identifica a la persona; el grupo es un identificador técnico, no un sujeto verificado. La fuente de grabación está casi totalmente asociada a la clase\n(normal y Parkinson: laboratorio), lo que impide separar el efecto de la fuente del de la clase. Ningún video cuenta con validación clínica individual.  Fuente: Elaboración propia (2026), manifiesto del dataset V4.", -0.02)
save(fig, "fig_distribucion_dataset")
write_csv(DAT / "fig_distribucion_dataset.csv", ["clase", "videos", "grupos", "grupos_provisionales"] + srcs, [[c, cnt_v[c], len(grp[c]), len(prov[c])] + [src.get((c, s), 0) for s in srcs] for c in CL])
print("OK figuras de resultados")
