"""Diagramas de V5-CR. Las dimensiones y capas se LEEN del checkpoint y de la configuración reales (no es una CNN genérica).
Salida: PNG 300 dpi + SVG en 06_FIGURAS_Y_GRAFICAS/ y datos (capas y parámetros) en datos/arquitectura_capas_V5CR.csv."""
import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import torch

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
FIG = PKG / "06_FIGURAS_Y_GRAFICAS"
sys.path.insert(0, str(REPO / "scripts" / "video_training" / "deep"))
sys.path.insert(0, str(REPO / "scripts" / "video_training"))
import deep_common as DC  # noqa: E402

MD = REPO / "models" / "gait_deep_v5cr"
VER = "gait_deep_v5exp_V5CR_7e9ed60965fe"
cfg = json.load(open(MD / f"{VER}_config.json", encoding="utf-8"))
model, _ = DC.build_model({k: cfg[k] for k in DC.default_model_config(4)})
sd = torch.load(MD / f"{VER}.pt", map_location="cpu", weights_only=True)
model.load_state_dict(sd)
P = {n: p.numel() for n, p in model.named_parameters()}
total = sum(P.values())
assert total == 17788 and cfg["in_channels"] == 68 and cfg["num_features"] == 33 and cfg["sequence_length"] == 40
T = str(cfg["temperature"]).replace(".", ",")
TEAL, TEAL_D, TEAL_L, ORANGE, BLUE, GREY = "#0B9586", "#124F48", "#E3F7F3", "#C2650A", "#3D7EA6", "#8A9A98"
plt.rcParams.update({"font.size": 9, "savefig.dpi": 300, "text.color": "#0B2B27"})
SRC = "Fuente: Elaboración propia (2026), a partir de la configuración y los pesos del checkpoint gait_deep_v5exp_V5CR_7e9ed60965fe."


def box(ax, x, y, w, h, text, fc="white", ec=TEAL_D, fs=8.2, bold=False, tc="#0B2B27", lw=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color=TEAL_D, rad=0.0, lw=1.3):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11, color=color, lw=lw, connectionstyle=f"arc3,rad={rad}"))


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("figura", name)


# ------------------------------------------------------------------ 1) Arquitectura
layers = [
    ("seq_net.0 Conv1d(68→24, k=5, pad=2)", P["seq_net.0.weight"] + P["seq_net.0.bias"]), ("seq_net.1 BatchNorm1d(24)", P["seq_net.1.weight"] + P["seq_net.1.bias"]),
    ("seq_net.4 Conv1d(24→32, k=3, dilación=2)", P["seq_net.4.weight"] + P["seq_net.4.bias"]), ("seq_net.5 BatchNorm1d(32)", P["seq_net.5.weight"] + P["seq_net.5.bias"]),
    ("seq_net.8 Conv1d(32→32, k=3, dilación=4)", P["seq_net.8.weight"] + P["seq_net.8.bias"]), ("seq_net.9 BatchNorm1d(32)", P["seq_net.9.weight"] + P["seq_net.9.bias"]),
    ("feat_net.0 Linear(33→24)", P["feat_net.0.weight"] + P["feat_net.0.bias"]), ("feat_net.1 BatchNorm1d(24)", P["feat_net.1.weight"] + P["feat_net.1.bias"]),
    ("feat_net.4 Linear(24→16)", P["feat_net.4.weight"] + P["feat_net.4.bias"]), ("head.1 Linear(80→32)", P["head.1.weight"] + P["head.1.bias"]), ("head.3 Linear(32→4)", P["head.3.weight"] + P["head.3.bias"]),
]
assert sum(n for _, n in layers) == total
with open(FIG / "datos" / "arquitectura_capas_V5CR.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["capa", "parametros_entrenables"])
    w.writerows(layers)
    w.writerow(["TOTAL", total])

fig, ax = plt.subplots(figsize=(11.5, 6.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis("off")
ax.set_title("Arquitectura de GaitTemporalModel (V5-CR): CNN 1D de dos ramas", fontsize=12, fontweight="bold", pad=6)
# rama secuencial
box(ax, 1, 40, 15, 12, "Secuencia\n[B, 68, 40]\n34 posiciones + 34\nvelocidades × 40\nmuestras (2,6 s)", fc=TEAL_L, bold=False)
blocks = [("Conv1d 68→24\nk=5, pad 2\nBatchNorm · GELU\nDropout 0,3", P["seq_net.0.weight"] + P["seq_net.0.bias"] + P["seq_net.1.weight"] + P["seq_net.1.bias"]),
          ("Conv1d 24→32\nk=3, dilación 2\nBatchNorm · GELU\nDropout 0,3", P["seq_net.4.weight"] + P["seq_net.4.bias"] + P["seq_net.5.weight"] + P["seq_net.5.bias"]),
          ("Conv1d 32→32\nk=3, dilación 4\nBatchNorm · GELU", P["seq_net.8.weight"] + P["seq_net.8.bias"] + P["seq_net.9.weight"] + P["seq_net.9.bias"])]
x0 = 20
for i, (t, n) in enumerate(blocks):
    box(ax, x0 + i * 17, 40, 14.5, 12, t, fc="white", ec=TEAL)
    ax.text(x0 + i * 17 + 7.25, 38, f"{n:,} par.", ha="center", fontsize=7.5, color=TEAL_D)
    arrow(ax, x0 + i * 17 - 3.2 if i else 16.5, 46, x0 + i * 17 - 0.3, 46)
box(ax, 72, 40, 13, 12, "Agrupación temporal\nmedia y máximo\nsobre las 40\nmuestras\n[B, 32+32 = 64]", fc=TEAL_L)
arrow(ax, 65.7, 46, 71.7, 46)
# rama tabular
box(ax, 1, 18, 15, 12, "Características\n[B, 33]\nescalador (mediana,\nmedia, desv.)", fc=TEAL_L)
box(ax, 20, 18, 14.5, 12, "Linear 33→24\nBatchNorm · GELU\nDropout 0,3", fc="white", ec=BLUE)
ax.text(27.25, 16, f"{P['feat_net.0.weight'] + P['feat_net.0.bias'] + P['feat_net.1.weight'] + P['feat_net.1.bias']:,} par.", ha="center", fontsize=7.5, color=BLUE)
box(ax, 37, 18, 14.5, 12, "Linear 24→16\nGELU", fc="white", ec=BLUE)
ax.text(44.25, 16, f"{P['feat_net.4.weight'] + P['feat_net.4.bias']:,} par.", ha="center", fontsize=7.5, color=BLUE)
arrow(ax, 16.5, 24, 19.7, 24)
arrow(ax, 34.8, 24, 36.7, 24)
box(ax, 54, 18, 11, 12, "Salida de la\nrama tabular\n[B, 16]", fc=TEAL_L)
arrow(ax, 51.8, 24, 53.7, 24)
# fusión y cabeza
box(ax, 72, 24.5, 13, 8, "Concatenación\n64 + 16 = 80", fc="#FFF3E0", ec=ORANGE)
arrow(ax, 78.5, 39.6, 78.5, 33, color=ORANGE)
arrow(ax, 65.8, 24, 71.7, 27.5, color=ORANGE)
box(ax, 87, 40, 12, 12, "Dropout 0,4\nLinear 80→32\nGELU\nLinear 32→4", fc="white", ec=ORANGE)
ax.text(93, 53.4, f"{P['head.1.weight'] + P['head.1.bias'] + P['head.3.weight'] + P['head.3.bias']:,} par.", ha="center", fontsize=7.5, color=ORANGE)
arrow(ax, 85.3, 29, 90, 39.6, color=ORANGE)
box(ax, 87, 18, 12, 14, f"Logits [B,4]\n(media de las\nK ≤ 5 ventanas)\n÷ T = {T}\nsoftmax →\n4 probabilidades", fc="#FFF3E0", ec=ORANGE, fs=7.8)
arrow(ax, 93, 39.6, 93, 32.4, color=ORANGE)
ax.text(1, 56.5, "Rama de secuencia (convoluciones temporales dilatadas)", fontsize=9, fontweight="bold", color=TEAL_D)
ax.text(1, 34, "Rama de características de marcha (perceptrón)", fontsize=9, fontweight="bold", color=BLUE)
ax.text(86.5, 57.2, "Cabeza de clasificación", fontsize=9, fontweight="bold", color=ORANGE)
ax.text(50, 8.5, f"Parámetros entrenables: {total:,}  ·  Framework: PyTorch (CPU)  ·  Clases (orden): normal, parkinson, esclerosis_multiple, riesgo_caida", ha="center", fontsize=9, fontweight="bold")
ax.text(50, 4.2, "B = tamaño de lote; K = ventanas de 2,6 s seleccionadas por video (máx. 5). Los pesos de BatchNorm incluyen escala y desplazamiento (no las estadísticas en ejecución, que no son entrenables).", ha="center", fontsize=7.5)
ax.text(50, 0.6, SRC, ha="center", fontsize=7.5, color="#334")
save(fig, "fig_arquitectura_GaitTemporalModel_V5CR")

# ------------------------------------------------------------------ 2) Flujo completo
fig, ax = plt.subplots(figsize=(12, 6.6))
ax.set_xlim(0, 100)
ax.set_ylim(0, 66)
ax.axis("off")
ax.set_title("Flujo completo de análisis: del video al resultado orientativo (V5-CR)", fontsize=12, fontweight="bold", pad=6)
steps = [
    (1, 44, "1. Video cargado\npor el usuario\n(MP4, MOV, WEBM)", TEAL_L, TEAL_D),
    (17, 44, "2. MediaPipe Pose\n(red PREENTRENADA,\nno entrenada aquí)\n17 puntos · 15 fps\n≤ 720 px", "#FFF3E0", ORANGE),
    (33, 44, "3. Filtro de calidad\nseguimiento corporal\ninsuficiente →\nANÁLISIS NO\nCONCLUYENTE", "white", "#B3261E"),
    (49, 44, "4. Tramo de análisis\nancla = 1.er cuadro\ncon pose; hasta 5,03 s\nventanas de 2,6 s\ncada 0,4 s (K ≤ 5)", TEAL_L, TEAL_D),
    (65, 44, "5. Preprocesamiento\nV5-CR por ventana\n(ver diagrama)\n→ 68×40 y 33\ncaracterísticas", TEAL_L, TEAL_D),
    (81, 44, "6. Escalador\nmediana (imputa NaN),\nmedia y desviación\ndel entrenamiento", "white", TEAL_D),
]
for x, y, t, fc, ec in steps:
    box(ax, x, y, 14.5, 14, t, fc=fc, ec=ec, fs=7.8)
for x in (15.5, 31.5, 47.5, 63.5, 79.5):
    arrow(ax, x, 51, x + 1.2, 51)
box(ax, 81, 22, 14.5, 14, "7. GaitTemporalModel\nV5-CR (17 788 par.)\nCNN 1D de dos ramas\nentrenado en este\nproyecto", fc="#FFF3E0", ec=ORANGE, fs=7.8)
arrow(ax, 88.25, 43.5, 88.25, 36.5)
box(ax, 65, 22, 14.5, 14, f"8. Media de logits\nde las K ventanas\n÷ T = {T}\nsoftmax →\n4 probabilidades", fc="white", ec=TEAL_D, fs=7.8)
arrow(ax, 80.8, 29, 79.7, 29)
box(ax, 49, 22, 14.5, 14, "9. Resultado\norientativo:\nclase de mayor\nprobabilidad +\nadvertencias de\ncalidad y de clase", fc=TEAL_L, ec=TEAL_D, fs=7.8)
arrow(ax, 64.8, 29, 63.7, 29)
box(ax, 33, 22, 14.5, 14, "10. Registro en\nPostgreSQL:\nanálisis, versión del\nmodelo, parámetros,\nseñales y condición", fc="white", ec=TEAL_D, fs=7.8)
arrow(ax, 48.8, 29, 47.7, 29)
box(ax, 17, 22, 14.5, 14, "11. Informe en\npantalla y PDF A4\n(mismo modelo de\ndatos); historial\ny descarga", fc=TEAL_L, ec=TEAL_D, fs=7.8)
arrow(ax, 32.8, 29, 31.7, 29)
box(ax, 1, 22, 14.5, 14, "12. Administración:\nestado del modelo,\nversión y métricas\ninternas", fc="white", ec=TEAL_D, fs=7.8)
arrow(ax, 16.8, 29, 15.7, 29)
ax.text(1, 14, "Notas: (a) V4 permanece instalado como respaldo y no se utiliza automáticamente si V5-CR falla (se informa el error). (b) La salida es una clasificación experimental de patrones de marcha,", fontsize=8)
ax.text(1, 10.5, "no un diagnóstico; la validación es interna (117 videos, 67 grupos de sujeto) y no existe validación clínica. (c) Un video con pose insuficiente no recibe clase ni probabilidades.", fontsize=8)
ax.text(1, 5, SRC.replace("a partir de la configuración y los pesos del checkpoint gait_deep_v5exp_V5CR_7e9ed60965fe", "a partir del código del sistema (route.ts, 15_predict_deep_video_v5cr.py)"), fontsize=7.5, color="#334")
save(fig, "fig_flujo_completo_sistema_V5CR")

# ------------------------------------------------------------------ 3) Preprocesamiento
fig, ax = plt.subplots(figsize=(12, 6.8))
ax.set_xlim(0, 100)
ax.set_ylim(0, 68)
ax.axis("off")
ax.set_title("Preprocesamiento V5-CR de una ventana de 2,6 s", fontsize=12, fontweight="bold", pad=6)
pre = [
    (1, 46, "A. Landmarks por cuadro\nx·(ancho/alto), y\n(corrección de aspecto)\nse descartan puntos con\nvisibilidad < 0,2; el\ncuadro exige hombros\ny caderas", TEAL_L),
    (22, 46, "B. Ventana fija\n40 muestras a 15 Hz\n(t0 … t0+2,6 s)\nmínimo 20 cuadros con\npose; si no, la\nventana se descarta", "white"),
    (43, 46, "C. Interpolación\nRELATIVA A LA CADERA\ncadera H interpolada;\ncada punto interpolado\ncomo (p − H); luego\np = (p − H) + H", "#FFF3E0"),
    (64, 46, "D. Escala corporal s\nmediana de |S − H|\n(longitud del torso)\nen la ventana\n(descarta s < 10⁻⁴)", "white"),
]
for x, y, t, fc in pre:
    box(ax, x, y, 19, 17, t, fc=fc, ec=ORANGE if fc == "#FFF3E0" else TEAL_D, fs=7.8)
for x in (20.7, 41.7, 62.7):
    arrow(ax, x, 54.5, x + 1.0, 54.5)
box(ax, 64, 22, 19, 17, "E1. Secuencia [68×40]\n(p − H)/s : 34 canales\n+ velocidad Δ de las\nmismas posiciones\n(paso 1/15 s;\nprimera muestra = 0)", fc=TEAL_L, ec=TEAL_D, fs=7.8)
box(ax, 43, 22, 19, 17, "E2. Características [33]\nrelativas a H, S y al\ntronco, escala s;\n(se omiten traslación\nglobal: sin avance\nhorizontal)", fc=TEAL_L, ec=TEAL_D, fs=7.8)
arrow(ax, 73.5, 45.5, 73.5, 39.5)
arrow(ax, 70, 45.5, 54, 39.5, rad=0.1)
box(ax, 22, 22, 19, 17, "F. Imputación y\nnormalización\nNaN → mediana del\nentrenamiento;\n(x − media)/desv.\n(solo del entrenamiento)", fc="white", ec=TEAL_D, fs=7.8)
arrow(ax, 42.8, 30.5, 41.2, 30.5)
box(ax, 1, 22, 19, 17, "G. Al modelo\nsecuencia [68×40] y\ncaracterísticas [33]\n(hasta 5 ventanas\npor video)", fc="#FFF3E0", ec=ORANGE, fs=7.8)
arrow(ax, 22.8, 30.5, 20.2, 30.5)
ax.text(1, 15, "Invariancias verificadas: en 633 ventanas reales una cámara que sigue a la persona no altera la entrada (0 ventanas con diferencia); con paneo, relación de aspecto y zoom el F1 macro no cambia (ΔF1 = 0).", fontsize=8)
ax.text(1, 11.5, "Limitaciones: todo es 2D (no se corrigen perspectiva ni rotación); las longitudes son relativas al torso (sin metros); ruido de landmarks y pérdida de fotogramas no mejoran respecto a V4.", fontsize=8)
ax.text(1, 6, "Fuente: Elaboración propia (2026), a partir de scripts/video_training/deep/v5cr/ (v5_preproc.py, v5c_preproc.py, v5cr_preproc.py).", fontsize=7.5, color="#334")
save(fig, "fig_diagrama_preprocesamiento_V5CR")

# ------------------------------------------------------------------ 4) Características V4 vs V5-CR por grupo
groups = ["Desplazamiento\nglobal", "Piernas\n(relativas)", "Brazos", "Tronco y\npostura", "Ritmo de\npasos", "Proxies\nde vista"]
v4n = [7, 11, 6, 5, 5, 2]
v5n = [4, 11, 6, 5, 5, 2]
assert sum(v4n) == 36 and sum(v5n) == 33
chg = ["−3 eliminadas (cadera, hombros,\navance horizontal); 4 relativas", "relativas a la pelvis (V4 incluía\ntraslación global)", "ángulo respecto al tronco\n(V4: rango de x absoluta)", "ángulo en coordenadas\nisotrópicas", "ventana fija 2,6 s;\ncadencia en picos/min", "se conservan (proxy de vista)"]
fig, ax = plt.subplots(figsize=(10.5, 4.8))
yv = list(range(len(groups)))[::-1]
ax.barh([v + 0.19 for v in yv], v4n, 0.36, color="#9AA7A5", label="V4 (36 características)")
ax.barh([v - 0.19 for v in yv], v5n, 0.36, color=TEAL, label="V5-CR (33 características)")
for v, a, b, c in zip(yv, v4n, v5n, chg):
    ax.text(a + 0.2, v + 0.19, str(a), va="center", fontsize=8)
    ax.text(b + 0.2, v - 0.19, str(b), va="center", fontsize=8)
    ax.text(12.3, v, c, va="center", fontsize=7.6)
ax.set_yticks(yv, groups, fontsize=8.5)
ax.set_xlim(0, 21)
ax.set_xlabel("Número de características")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8)
ax.set_title("Características de marcha: V4 frente a V5-CR, por grupo funcional", fontsize=11, fontweight="bold")
fig.text(0.01, -0.12, "Grupos definidos en v5_preproc.py (GROUPS / V4_GROUPS). Eliminadas: hip_center_motion_mean, shoulder_center_motion_mean, horizontal_motion_mean. Cambia además la ventana (5,03 s → 2,6 s)\ny la secuencia (68×96 → 68×40). Fuente: Elaboración propia (2026), a partir del código del proyecto.", fontsize=7.5)
with open(FIG / "datos" / "fig_caracteristicas_V4_vs_V5CR.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["grupo", "caracteristicas_V4", "caracteristicas_V5CR", "cambio"])
    for g_, a, b, c in zip(groups, v4n, v5n, chg):
        w.writerow([g_.replace("\n", " "), a, b, c.replace("\n", " ")])
save(fig, "fig_comparacion_caracteristicas_V4_vs_V5CR")
print("OK diagramas")
