"""Tabla de las 33 características de V5-CR. Se verifica contra la configuración real del checkpoint (nombres y orden) y contra el código.
Las fórmulas se redactaron leyendo scripts/video_training/deep/v5cr/{v5_preproc.py, v5c_preproc.py} y FORMULAS_CARACTERISTICAS_V5.md.
No calcula valores clínicos: todas son aproximaciones adimensionales (en «longitudes de torso») o ángulos/conteos de una ventana de 2,6 s."""
import csv
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
sys.path.insert(0, str(REPO / "scripts" / "video_training" / "deep"))
sys.path.insert(0, str(REPO / "scripts" / "video_training"))
from v5cr import v5_preproc as V  # noqa: E402
from v5cr.v5c_preproc import FEATURES_C  # noqa: E402

cfg = json.load(open(REPO / "models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe_config.json", encoding="utf-8"))
assert cfg["feature_names"] == FEATURES_C and len(FEATURES_C) == 33, "El orden de características del checkpoint no coincide con el código"

F5 = "scripts/video_training/deep/v5cr/v5_preproc.py::features_from_grid (l. 214)"
FC = "scripts/video_training/deep/v5cr/v5c_preproc.py::features_C (l. 13)"
N = "adimensional (en longitudes de torso s)"
D = {
    "body_motion_mean": ("Movimiento medio de los puntos del cuerpo relativo a la cadera", "media de |Δ(p−H)|/s sobre hombros, rodillas y tobillos (6 puntos), por paso de 1/15 s", "Cantidad media de movimiento de las extremidades y hombros respecto a la pelvis", N, "hombros, rodillas, tobillos, centro de caderas", "escala torso s", "No es velocidad en m/s; sobrescribe la definición V5-P (que incluía la traslación global) para ser invariante a la cámara", FC),
    "body_motion_std": ("Variabilidad del movimiento relativo a la cadera", "desviación estándar de los mismos |Δ(p−H)|/s", "Mezcla variación temporal y diferencias entre articulaciones", N, "ídem", "escala torso s", "No separa variabilidad temporal de heterogeneidad entre articulaciones", FC),
    "vertical_motion_mean": ("Oscilación vertical de la pelvis", "media de |ΔH_y|/s", "Movimiento vertical del centro de caderas", N, "centro de caderas", "escala torso s", "Depende de la inclinación de la cámara; no es oscilación en cm", F5),
    "left_ankle_rel_motion_mean": ("Movimiento del tobillo izquierdo relativo a la pelvis", "media de |Δ(A_izq−H)|/s", "Movimiento de la pierna respecto a la pelvis", N, "tobillo izq., caderas", "escala torso s", "Aproximación 2D; sensible a la vista", F5),
    "right_ankle_rel_motion_mean": ("Movimiento del tobillo derecho relativo a la pelvis", "media de |Δ(A_der−H)|/s", "ídem lado derecho", N, "tobillo der., caderas", "escala torso s", "ídem", F5),
    "left_knee_rel_motion_mean": ("Movimiento de la rodilla izquierda relativo a la pelvis", "media de |Δ(K_izq−H)|/s", "ídem", N, "rodilla izq., caderas", "escala torso s", "ídem", F5),
    "right_knee_rel_motion_mean": ("Movimiento de la rodilla derecha relativo a la pelvis", "media de |Δ(K_der−H)|/s", "ídem", N, "rodilla der., caderas", "escala torso s", "ídem", F5),
    "leg_rel_motion_asymmetry": ("Asimetría del movimiento relativo de las piernas", "|a−b|/max(|a|,|b|,1e-6) con a,b = movimiento relativo de tobillos izq./der.", "0 = igualdad; 1 = máxima asimetría", "adimensional (0–1)", "tobillos, caderas", "cociente", "Sin umbral clínico", F5),
    "ankle_rel_vrange_left": ("Rango vertical del tobillo izquierdo respecto a la pelvis", "rng((A_izq,y−H_y)/s), rng = percentil 95 − percentil 5", "Elevación vertical del tobillo respecto a la pelvis", N, "tobillo izq., caderas", "escala torso s", "No es altura del paso en cm", F5),
    "ankle_rel_vrange_right": ("Rango vertical del tobillo derecho respecto a la pelvis", "rng((A_der,y−H_y)/s)", "ídem", N, "tobillo der., caderas", "escala torso s", "ídem", F5),
    "ankle_rel_vrange_asymmetry": ("Asimetría de la elevación de tobillos", "asim(rango izq., rango der.)", "0 = igualdad", "adimensional (0–1)", "tobillos", "cociente", "Sin umbral clínico", F5),
    "knee_rel_vrange_left": ("Rango vertical de la rodilla izquierda respecto a la pelvis", "rng((K_izq,y−H_y)/s)", "Elevación vertical de la rodilla", N, "rodilla izq., caderas", "escala torso s", "Aproximación 2D", F5),
    "knee_rel_vrange_right": ("Rango vertical de la rodilla derecha respecto a la pelvis", "rng((K_der,y−H_y)/s)", "ídem", N, "rodilla der., caderas", "escala torso s", "ídem", F5),
    "step_regularity_score": ("Regularidad del ritmo de pasos", "1/(1+CV de los intervalos entre picos de altura relativa de los tobillos); NaN si hay <3 picos", "Regularidad temporal de los eventos de paso", "adimensional (0–1)", "tobillos, caderas", "—", "NaN si hay <3 picos (1 de 633 ventanas del banco); se imputa con la mediana del entrenamiento", F5),
    "left_wrist_rel_motion_mean": ("Movimiento de la muñeca izquierda relativo al hombro", "media de |Δ(W_izq−S_izq)|/s", "Movimiento de la mano respecto a su hombro", N, "muñeca izq., hombro izq.", "escala torso s", "NaN si la muñeca izquierda no es visible (102 de 633 ventanas del banco); se imputa con la mediana del entrenamiento", F5),
    "right_wrist_rel_motion_mean": ("Movimiento de la muñeca derecha relativo al hombro", "media de |Δ(W_der−S_der)|/s", "ídem", N, "muñeca der., hombro der.", "escala torso s", "NaN si la muñeca derecha no es visible (43 de 633 ventanas del banco); se imputa con la mediana", F5),
    "arm_swing_angle_mean": ("Amplitud angular media del balanceo de brazos", "media de los rangos angulares izq. y der.", "Balanceo de brazos respecto al eje del tronco", "radianes", "hombros, muñecas, caderas", "ángulo (no requiere escala)", "En vista frontal el balanceo no se proyecta; no es un ángulo articular clínico; NaN en 7 de 633 ventanas (muñecas no visibles)", F5),
    "arm_swing_angle_asymmetry": ("Asimetría del balanceo angular de brazos", "asim(rango izq., rango der.)", "0 = igualdad", "adimensional (0–1)", "ídem", "cociente", "Sin umbral clínico; NaN en 138 de 633 ventanas (basta que una muñeca no sea visible)", F5),
    "left_arm_swing_angle": ("Rango angular del brazo izquierdo", "rng(θ_izq), θ = ángulo con signo entre el eje S→H del tronco y el vector hombro→muñeca", "Balanceo angular del brazo izquierdo", "radianes", "hombro izq., muñeca izq., caderas", "ángulo", "Proyección 2D; NaN si la muñeca no es visible (102 de 633 ventanas)", F5),
    "right_arm_swing_angle": ("Rango angular del brazo derecho", "rng(θ_der)", "ídem", "radianes", "hombro der., muñeca der., caderas", "ángulo", "ídem; NaN en 43 de 633 ventanas", F5),
    "shoulder_width_mean": ("Ancho medio de hombros", "media de |LS−RS|/s", "Proxy de la VISTA (frontal ≈ grande, lateral ≈ pequeño), no de la marcha", N, "hombros", "escala torso s", "Se conserva en V5-CR; su permutación apenas cambia el F1 macro (ΔF1 −0,003)", F5),
    "hip_width_mean": ("Ancho medio de caderas", "media de |LH−RH|/s", "Proxy de la vista", N, "caderas", "escala torso s", "ídem", F5),
    "trunk_inclination_mean": ("Inclinación media del tronco", "media de |atan2(S_x−H_x, H_y−S_y)| en grados (coordenadas isotrópicas)", "Inclinación del tronco respecto a la vertical de la imagen", "grados (sobre la imagen)", "hombros, caderas", "—", "Depende de la inclinación de la cámara; no es inclinación postural clínica", F5),
    "trunk_inclination_std": ("Variabilidad de la inclinación del tronco", "desviación estándar de la inclinación", "ídem", "grados (sobre la imagen)", "ídem", "—", "ídem", F5),
    "trunk_sway_mean": ("Desplazamiento lateral medio hombros–caderas", "media de |S_x−H_x|/s", "Oscilación lateral del tronco", N, "hombros, caderas", "escala torso s", "Depende de la vista", F5),
    "trunk_sway_std": ("Variabilidad del desplazamiento lateral del tronco", "desviación estándar de |S_x−H_x|/s", "ídem", N, "ídem", "escala torso s", "ídem", F5),
    "posture_stability_score": ("Índice de estabilidad postural", "1/(1 + std(sway) + std(inclinación)/45)", "Resumen de variabilidad del tronco", "adimensional (0–1)", "hombros, caderas", "—", "Índice heurístico del proyecto, no validado clínicamente", F5),
    "estimated_step_count": ("Número estimado de eventos de paso", "suma de los picos de la altura relativa (A_y−H_y) de cada tobillo; un pico supera media+0,2·sd y dista ≥3 muestras (int(15·0,25)=3 → 0,2 s) del anterior (find_signal_peaks)", "Eventos de paso aproximados en 2,6 s", "conteo (picos)", "tobillos, caderas", "—", "No es un conteo de pasos validado clínicamente", F5),
    "estimated_cadence_steps_per_min": ("Ritmo estimado por picos", "picos / (40/15 s) × 60", "Cadencia aproximada de los picos de tobillo", "picos/min", "tobillos, caderas", "duración fija de 2,6 s", "No es cadencia clínica; el informe la rotula «picos/min»", F5),
    "step_frequency_hz": ("Frecuencia de picos", "picos / (40/15 s)", "= cadencia/60 (redundante con la anterior)", "Hz (picos/s)", "tobillos, caderas", "duración fija de 2,6 s", "Redundante", F5),
    "gait_variability": ("Variabilidad del movimiento de la marcha", "media de [std(mov. relativo tobillo izq.), std(mov. relativo tobillo der.), std(|ΔH_y|/s)]", "Variabilidad de movimiento de piernas y oscilación vertical de la pelvis", N, "tobillos, caderas", "escala torso s", "Redefinida en V5-CR: ya no usa el avance horizontal de la cadera", FC),
    "motion_smoothness": ("Suavidad del movimiento vertical de la pelvis", "1/(1 + std(jerk de |ΔH_y|/s)), jerk = segunda diferencia", "Suavidad (valores mayores = menos sacudidas)", "adimensional (0–1)", "caderas", "escala torso s", "Redefinida en V5-CR (solo componente vertical)", FC),
    "rhythm_variability": ("Variabilidad del ritmo (CV de intervalos entre picos)", "desviación/media de los intervalos entre picos; NaN si <3 picos", "Irregularidad temporal", "adimensional", "tobillos, caderas", "—", "NaN si hay <3 picos (1 de 633 ventanas del banco); se imputa con la mediana del entrenamiento", F5),
}
assert list(D) == FEATURES_C, "El orden/claves de la tabla no coincide con las características del modelo"
rows = []
for i, name in enumerate(FEATURES_C, 1):
    v4 = V.FEATURES_V4[V.FEATURES_V5.index(name)]
    es, fo, sig, un, lm, no, lim, fn = D[name]
    rows.append([i, name, es, fo, sig, un, lm, no, lim, fn, v4, "igual nombre" if v4 == name else "renombrada y redefinida (relativa a la pelvis/hombro/tronco)"])
H = ["n", "nombre_en_codigo", "nombre_en_espanol", "formula", "significado", "unidad_o_naturaleza", "puntos_corporales", "normalizacion", "limitaciones_de_interpretacion", "archivo_y_funcion", "equivalente_en_V4", "relacion_con_V4"]
out = PKG / "07_PREPROCESAMIENTO_Y_FORMULAS"
with open(out / "TABLA_33_CARACTERISTICAS_V5CR.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(H)
    w.writerows(rows)

# V4 (36) -> V5-CR (33)
dropped = [n for n in V.FEATURES_V5 if n not in FEATURES_C]
m = []
for i, n5 in enumerate(V.FEATURES_V5):
    n4 = V.FEATURES_V4[i]
    estado = "ELIMINADA en V5-CR (dependía del desplazamiento global de la imagen / de la cámara)" if n5 in dropped else ("redefinida en V5-CR (relativa a la cadera; sin avance horizontal)" if n5 in ("body_motion_mean", "body_motion_std", "gait_variability", "motion_smoothness") else ("renombrada y redefinida respecto a V4" if n4 != n5 else "se conserva (cálculo en tiempo físico, coordenadas isotrópicas)"))
    m.append([i + 1, n4, n5, estado])
with open(out / "CORRESPONDENCIA_36_V4_A_33_V5CR.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["posicion_en_V4", "nombre_V4", "nombre_V5_(P)", "estado_en_V5-CR"])
    w.writerows(m)
print("OK", len(rows), "características;", "eliminadas:", dropped)
