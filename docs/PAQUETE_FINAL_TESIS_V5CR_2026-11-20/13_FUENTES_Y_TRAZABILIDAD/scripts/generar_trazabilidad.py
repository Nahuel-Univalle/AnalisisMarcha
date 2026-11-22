"""Genera MATRIZ_TRAZABILIDAD_TESIS.csv y MANIFIESTO_ARCHIVOS_SHA256.txt.
La matriz une: cambios por capítulo, cada métrica importante (con su archivo original), cada figura (con su dato y script), cada batería de pruebas y los datos del dataset.
El manifiesto incluye los hashes de TODOS los archivos del paquete y las rutas+hash de los artefactos pesados referenciados (no copiados)."""
import csv
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
OUT = PKG / "13_FUENTES_Y_TRAZABILIDAD"
rows = []
H = ["Capitulo", "Apartado", "Contenido_anterior", "Cambio_necesario", "Dato_nuevo", "Figura_tabla_asociada", "Fuente_del_repositorio", "Estado_de_verificacion", "Observaciones"]


def add(*a):
    rows.append(list(a) + [""] * (len(H) - len(a)))


# 1) cambios por capítulo
for r in csv.DictReader(open(PKG / "11_CAMBIOS_POR_CAPITULO" / "CAMBIOS_POR_CAPITULO.csv", encoding="utf-8-sig")):
    add(r["capitulo"], r["apartado"], r["contenido_anterior_probable"], r["cambio_necesario"], "", r["figura_tabla_o_texto_nuevo"], r["fuente_del_repositorio"], "Contenido nuevo verificado en el repositorio; ubicación en el Word pendiente (Word no disponible)", r["conservar_V4_como_historico"])

# 2) métricas (cada una con su archivo original)
SRC = {"V4 base": "outputs/dataset_v4_4class/step18_bn/oof_probabilities.npz (A_<semilla>); docs/optimizacion_final_v5_2026-11-19/resultados/comparacion_final.json",
       "V4 activo (BN recalibrada)": "outputs/dataset_v4_4class/step18_bn/oof_probabilities.npz (B_<semilla>); comparacion_final.json",
       "V5-P": "docs/mejora_modelo_v5_experimental_2026-11-19/resultados/oof_V5P.npz; comparacion_final.json",
       "V5-C": "docs/optimizacion_final_v5_2026-11-19/resultados/oof_V5C.npz; comparacion_final.json",
       "V5-CR": "docs/optimizacion_final_v5_2026-11-19/resultados/oof_V5CR.npz; comparacion_final.json"}
met = list(csv.DictReader(open(PKG / "04_METRICAS_Y_COMPARACIONES" / "METRICAS_VERIFICADAS_POR_MODELO.csv", encoding="utf-8-sig")))
ver = {(r["modelo"], r["metrica"]): r for r in csv.DictReader(open(PKG / "04_METRICAS_Y_COMPARACIONES" / "VERIFICACION_CONTRA_ORIGINALES.csv", encoding="utf-8-sig"))}
for m in met:
    for key, label in [("exactitud", "Exactitud"), ("f1_macro", "F1 macro")] + [(f"f1_{c}", f"F1 {c}") for c in ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]] + [("ece_sin_calibrar", "ECE sin calibrar")]:
        v = ver.get((m["modelo"], key))
        add("IV", "4.4 Evaluación del modelo", "", "Presentar la métrica de la versión correcta", f"{m['modelo']}: {label} = {m[key]}", "METRICAS_VERIFICADAS_POR_MODELO.csv", SRC[m["modelo"]],
            "Recalculada desde las predicciones OOF y contrastada con el original: " + ("coincide" if v and v["coincide(<=0.0001)"] == "True" else "no contrastada"), "Evaluación interna; semillas no independientes")
    if m["ece_calibrado_por_particion"]:
        add("IV", "4.4 Calibración", "", "ECE calibrada solo para V5", f"{m['modelo']}: ECE calibrado por partición = {m['ece_calibrado_por_particion']}", "fig_calibracion_V5CR_diagrama_fiabilidad", SRC[m["modelo"]], "Recalculada y contrastada", "V4 no tiene OOF calibrado bajo el mismo protocolo")
add("IV", "4.4 Diferencias", "", "Declarar que la mejora global no es concluyente", "V5-CR − V4 activo: F1 macro +0,041 [−0,029; 0,102]; F1 riesgo de caída +0,203 [0,023; 0,356]", "DIFERENCIAS_V5CR_VS_OTROS.csv", "docs/optimizacion_final_v5_2026-11-19/resultados/comparacion_final.json (bootstrap por grupo)", "Extraído sin modificar", "IC95 originales con semilla 20261119")
add("IV", "4.4 Matriz de confusión", "", "Presentar matriz con denominadores", "V5-CR (suma de 5 semillas): [[271,13,3,3],[0,126,1,3],[6,4,68,32],[0,1,16,38]]", "matriz_confusion_V5CR_A_absoluta_suma5", "oof_V5CR.npz + comparacion_final.json (matriz_confusion)", "Coincide con el original", "585 predicciones, no videos")
add("IV", "4.4 Sesgo de adquisición", "", "Citar la sonda de metadatos como referencia", "Sonda de 7 metadatos: F1 macro 0,777 (LR) / 0,786 (RF) frente a V5-CR 0,785", "—", "docs/evidencia_experimental_v4_2026-11-18/tabla_4_4_1_comparacion_v4.csv", "Heredado de V4 (mismos videos y particiones); no recalculado para V5-CR", "Pendiente repetir para V5-CR")
for t, f, src in [("Cámara que sigue (100 %)", "fig_robustez_camara_ruido_perdida_fotogramas", "fase4_robustez_v4.json, fase8_evidencia_v4/v5P.json, fase4_robustez_v5C/v5CR.json"), ("Ruido y pérdida de fotogramas", "fig_robustez_camara_ruido_perdida_fotogramas", "ídem")]:
    add("IV", "4.4 Robustez", "", f"Presentar ΔF1: {t}", "ver ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv", f, "docs/…/resultados/" + src, "Extraído sin modificar", "V4 base, no V4 activo")

# 3) modelo / arquitectura
cfg = json.load(open(REPO / "models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe_config.json", encoding="utf-8"))
for apart, dato, fig, fuente in [("3.3.6 Arquitectura", "GaitTemporalModel: CNN 1D de dos ramas, 17 788 parámetros entrenables", "fig_arquitectura_GaitTemporalModel_V5CR", "models/gait_deep_v5cr/…V5CR_7e9ed60965fe.pt + deep_common.py::build_model"),
                                 ("3.3.6 Entradas", "Secuencia 68 × 40; 33 características; ventana 2,6 s; 15 Hz", "fig_diagrama_preprocesamiento_V5CR", "models/gait_deep_v5cr/…_config.json"),
                                 ("3.3.6 Calibración", f"T = {cfg['temperature']}; E* = {cfg['E_star']}", "—", "models/gait_deep_v5cr/…_config.json"),
                                 ("3.3.6 Características", "33 características (3 eliminadas, 4 redefinidas respecto a V5-P)", "fig_comparacion_caracteristicas_V4_vs_V5CR", "scripts/video_training/deep/v5cr/v5c_preproc.py; TABLA_33_CARACTERISTICAS_V5CR.csv"),
                                 ("3.3.6 Identificador", "gait_deep_v5exp_V5CR_7e9ed60965fe; SHA-256 7e9ed60965fe…c9dade", "—", "models/gait_deep_v5cr/deployment_manifest.json")]:
    add("III", apart, "", "Describir el modelo final", dato, fig, fuente, "Verificado en el checkpoint/configuración/código")
# 4) dataset
for dato in ["117 videos: 58 / 26 / 22 / 11", "67 grupos técnicos: 30 / 7 / 21 / 9", "27 grupos provisionales (20 esclerosis múltiple, 7 riesgo de caída)", "20 videos excluidos (18 EXCLUDE, 2 MANUAL_REVIEW)", "633 ventanas de 2,6 s (1 a 7 por video)", "112 de 117 sin atribución de origen acreditada"]:
    add("III / Apéndice 8", "3.3.6.1 Dataset", "", "Actualizar cifras y terminología", dato, "fig_distribucion_dataset", "outputs/dataset_v4_4class/manifest_v4_preview.csv; dataset_v5cr_bank.npz; docs/inventario_dataset_v4_2026-11-18/", "Verificado por script (generar_manifiesto_dataset.py)", "")
# 5) figuras
FIGS = [("fig_arquitectura_GaitTemporalModel_V5CR", "datos/arquitectura_capas_V5CR.csv", "scripts/generar_diagramas.py"), ("fig_flujo_completo_sistema_V5CR", "código del sistema", "scripts/generar_diagramas.py"),
        ("fig_diagrama_preprocesamiento_V5CR", "v5cr/*.py", "scripts/generar_diagramas.py"), ("fig_comparacion_caracteristicas_V4_vs_V5CR", "datos/fig_caracteristicas_V4_vs_V5CR.csv", "scripts/generar_diagramas.py"),
        ("fig_distribucion_dataset", "datos/fig_distribucion_dataset.csv", "scripts/generar_figuras_resultados.py"), ("fig_comparacion_exactitud_f1macro_por_version", "datos/fig_comparacion_exactitud_f1macro_por_version.csv", "scripts/generar_figuras_resultados.py"),
        ("fig_V5CR_precision_sensibilidad_f1_por_clase", "datos/fig_V5CR_precision_sensibilidad_f1_por_clase.csv", "scripts/generar_figuras_resultados.py"), ("fig_f1_macro_por_semilla", "datos/fig_f1_macro_por_semilla.csv", "scripts/generar_figuras_resultados.py"),
        ("fig_calibracion_V5CR_diagrama_fiabilidad", "datos/fig_calibracion_V5CR_diagrama_fiabilidad.csv", "scripts/generar_figuras_resultados.py"), ("fig_robustez_camara_ruido_perdida_fotogramas", "datos/fig_robustez_delta_f1_macro.csv", "scripts/generar_figuras_resultados.py"),
        ("matriz_confusion_V5CR_A/B/C y V4activo_A/B/C", "05_MATRICES_DE_CONFUSION/datos/cm_*.csv", "scripts/calcular_metricas_y_matrices.py + generar_figuras_resultados.py"), ("matriz_confusion_D_comparacion_V4activo_vs_V5CR", "datos/diferencia_tasas_V5CR_menos_V4activo_puntos_porcentuales.csv", "scripts/generar_figuras_resultados.py")]
for f, d, s in FIGS:
    add("III / IV", "Figuras", "", "Insertar figura nueva", "", f, f"Datos: {d}; script: {s}", "Figura abierta y revisada; datos CSV junto a la figura", "Fuente: Elaboración propia (2026)")
# 6) pruebas
for r in csv.DictReader(open(PKG / "08_PRUEBAS_DEL_SISTEMA" / "PRUEBAS_EJECUTADAS_RESUMEN.csv", encoding="utf-8-sig")):
    add("IV", "4.3 Pruebas del sistema", "", "Registrar la batería", f"{r['total']} / {r['aprobadas']} aprobadas / {r['fallidas']} fallidas", "PRUEBAS_EJECUTADAS_RESUMEN.csv", r["evidencia"], f"Conteo leído del archivo de evidencia (fecha {r['fecha_de_la_evidencia']})", r["limitaciones"])
# 7) capturas
add("III", "3.3.4 Capturas de interfaz", "Capturas de V4", "Sustituir por capturas finales", "20 capturas nuevas + 4 reutilizadas", "09_CAPTURAS_Y_EVIDENCIAS/capturas_nuevas", "scripts/capturar_pantallas.mjs (entorno aislado, videos ocultos)", "Capturas reales de la aplicación (build de producción)", "Capturas pendientes en INDICE_CAPTURAS.md")
with open(OUT / "MATRIZ_TRAZABILIDAD_TESIS.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(H)
    w.writerows(rows)
print(len(rows), "filas de trazabilidad")

# manifiesto SHA-256
lines = ["# SHA-256 de los archivos del paquete (relativos a docs/PAQUETE_FINAL_TESIS_V5CR_2026-11-20/); generado por 13_FUENTES_Y_TRAZABILIDAD/scripts/generar_trazabilidad.py"]
for p in sorted(PKG.rglob("*")):
    if p.is_file() and p.name not in ("MANIFIESTO_ARCHIVOS_SHA256.txt",) and p.suffix != ".zip" and "__pycache__" not in p.parts:
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(PKG).as_posix()}")
lines.append("")
lines.append("# Artefactos pesados o externos al paquete (NO copiados): ruta relativa a la raíz del repositorio y SHA-256")
HEAVY = ["models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe.pt", "models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe_config.json", "models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe_feature_scaler.json",
         "models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe_label_map.json", "models/gait_deep_v5cr/deployment_manifest.json",
         "models/gait_deep_v4exp_bn_candidate_v1/gait_deep_v4exp_M1_BN_recalibrated_candidate_v1.pt",
         "docs/optimizacion_final_v5_2026-11-19/checkpoints/gait_deep_v5exp_V5CR_7e9ed60965fe.pt",
         "docs/optimizacion_final_v5_2026-11-19/resultados/oof_V5CR.npz", "docs/optimizacion_final_v5_2026-11-19/resultados/oof_V5C.npz", "docs/optimizacion_final_v5_2026-11-19/resultados/dataset_v5cr_bank.npz",
         "docs/optimizacion_final_v5_2026-11-19/resultados/comparacion_final.json", "docs/optimizacion_final_v5_2026-11-19/resultados/fase4_robustez_v5CR.json", "docs/optimizacion_final_v5_2026-11-19/resultados/fase4_robustez_v5C.json",
         "docs/mejora_modelo_v5_experimental_2026-11-19/resultados/oof_V5P.npz", "docs/mejora_modelo_v5_experimental_2026-11-19/resultados/fase4_robustez_v4.json", "docs/mejora_modelo_v5_experimental_2026-11-19/resultados/fase4_robustez_v5P.json",
         "outputs/dataset_v4_4class/step18_bn/oof_probabilities.npz", "outputs/dataset_v4_4class/dataset_v4_preview.npz", "outputs/dataset_v4_4class/manifest_v4_preview.csv",
         "scripts/video_training/deep/15_predict_deep_video_v5cr.py", "scripts/video_training/deep/deep_common.py", "scripts/video_training/deep/v5cr/v5_preproc.py", "scripts/video_training/deep/v5cr/v5c_preproc.py", "scripts/video_training/deep/v5cr/v5cr_preproc.py",
         "src/lib/ml/activeModel.ts", "src/lib/analysis/reportModel.ts", "src/lib/analysis/reportPdf.ts", "src/app/api/analysis/video/route.ts", "src/components/analysis/VideoStage.tsx", "src/components/analysis/SavedReportsList.tsx"]
for rel in HEAVY:
    p = REPO / rel
    lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  ../../{rel}" if p.exists() else f"NO ENCONTRADO  ../../{rel}")
(OUT / "MANIFIESTO_ARCHIVOS_SHA256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("manifiesto:", len(lines), "líneas")
