"""Construye DOSSIER_COMPLETO_PARA_CLAUDE_WORD.docx a partir de lo ya verificado en el paquete (no recalcula nada).
Uso: PYTHONPATH=<carpeta con python-docx> python construir_dossier_word.py"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dossier_lib import *  # noqa: F401,F403
import dossier_lib as L

PKG = L.PKG
OUT = PKG / "DOSSIER_COMPLETO_PARA_CLAUDE_WORD.docx"
F = PKG / "06_FIGURAS_Y_GRAFICAS"
M = PKG / "05_MATRICES_DE_CONFUSION"
C = PKG / "09_CAPTURAS_Y_EVIDENCIAS" / "capturas_nuevas"
R = PKG / "09_CAPTURAS_Y_EVIDENCIAS" / "reutilizadas"
E = PKG / "10_INFORMES_PDF_E_HISTORIAL" / "ejemplos"
FUENTE = "Fuente: Elaboración propia (2026)."
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
CLN = {"normal": "normal", "parkinson": "Parkinson", "esclerosis_multiple": "esclerosis múltiple", "riesgo_caida": "riesgo de caída"}

doc = new_document()
met = {r["modelo"]: r for r in csv_rows("04_METRICAS_Y_COMPARACIONES/METRICAS_VERIFICADAS_POR_MODELO.csv")}
ci = {(r["modelo"], r["metrica"]): r for r in csv_rows("04_METRICAS_Y_COMPARACIONES/INTERVALOS_CONFIANZA_BOOTSTRAP_POR_GRUPO.csv")}
MODELS = ["V4 base", "V4 activo (BN recalibrada)", "V5-P", "V5-C", "V5-CR"]
A = ACAD_MODEL


def f4(x):
    return num(f"{float(x):.4f}") if x not in ("", None) else "—"


def f3(x):
    return num(f"{float(x):.3f}")


# =============================================================================== PORTADA
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(t, "DOSSIER COMPLETO PARA CLAUDE EN WORD", size=24, bold=True, color=TEAL)
para(doc, "Documento auxiliar de consulta para actualizar la tesis «Sistema inteligente basado en Deep Learning para el análisis de la marcha humana orientado a la identificación temprana de alteraciones motoras»", subst=False, align="center", size=12, space_after=4)
para(doc, "Fecha de elaboración: 20 de noviembre de 2026 · Contenido verificado contra los archivos originales del repositorio · Sin modificaciones al software, a los datos ni a la tesis", subst=False, align="center", size=9.5, italic=True)
callout(doc, "Cómo debe usar este documento (instrucciones para Claude en Word)", [
    "1. **Es la fuente única y autocontenida**: reúne los datos, tablas, figuras, capturas, textos propuestos y la lista de cambios. No depende de archivos externos; las rutas que aparecen son solo procedencia (trazabilidad).",
    "2. **No invente ni recalcule**: use las cifras, matrices y fórmulas tal como están. Si falta un dato, indíquelo; no lo complete.",
    "3. **Terminología académica**: en la redacción use «modelo preliminar» (versión anterior, documentada en la tesis actual), «modelo implementado» o «modelo final» (el modelo ahora instalado). Los nombres internos (V4, V5-P, V5-C, V5-CR) solo se usan en la trazabilidad técnica (sección 14) y como términos de búsqueda en la sección 13.",
    "4. **No reemplace indiscriminadamente**: el modelo preliminar se conserva como antecedente y versión de respaldo; cambian la descripción del modelo implementado y sus resultados actuales.",
    "5. **Carácter científico**: todos los resultados son validación interna sobre 117 videos y 67 grupos técnicos de sujeto; no hay validación clínica ni externa; la salida es orientativa y no diagnóstica. La mejora global del modelo final sobre el modelo preliminar activo **no es estadísticamente concluyente**.",
    "6. **Numeración**: las figuras y tablas de este dossier se numeran «D.n»; los números «x» de los pies sugeridos deben ajustarse a la numeración real de la tesis. Las figuras 4.9–4.11 y las tablas 4.3–4.4 de la tesis actual no pudieron verificarse (el Word no estaba disponible): compruebe su contenido antes de sustituirlas.",
    "7. **Rótulos dentro de las imágenes**: algunas figuras conservan los rótulos internos de los modelos. Equivalencias en la Tabla D.1.",
], subst=False)

heading(doc, "Equivalencia de rótulos internos de las figuras", 3, subst=False)
table(doc, ["Rótulo interno (en figuras y archivos)", "Nombre académico para la tesis", "Qué es"], [
    ["V4 base", "Modelo preliminar base", "Versión anterior sin recalibración de BatchNorm"],
    ["V4 activo / V4 BN", "Modelo preliminar activo", "Versión anterior con BatchNorm recalibrada; era el modelo de la aplicación antes del modelo final"],
    ["V5-P", "Versión intermedia P", "Primera corrección del preprocesamiento (36 características)"],
    ["V5-C", "Versión intermedia C", "Versión sin características de desplazamiento global (33 características)"],
    ["V5-CR", "Modelo final (modelo implementado)", "V5-C con interpolación relativa a la cadera; modelo principal de la aplicación"],
], widths=[3, 3.4, 8], caption="Equivalencia entre rótulos internos y nombres académicos", subst=False)

heading(doc, "Contenido y apartados de la tesis a los que corresponde", 3, subst=False)
table(doc, ["Sección del dossier", "Contenido", "Apartados de la tesis que alimenta"], [
    ["1", "Resumen técnico del modelo implementado", "Resumen, Abstract, 3.3.6, 3.4"],
    ["2", "Arquitectura real y preprocesamiento", "Propuesta tecnológica, 3.3.5, 3.3.6, arquitectura"],
    ["3", "Las 33 características y sus fórmulas", "3.3.6, apéndice técnico"],
    ["4", "Dataset, metodología y limitaciones", "Población y muestra, metodología, 3.3.6.1, Apéndice 8, limitaciones"],
    ["5", "Métricas definitivas del modelo final", "4.4 Evaluación del modelo"],
    ["6", "Matrices de confusión verificadas", "4.4 (Figuras 4.9–4.11: verificar)"],
    ["7", "Gráficas académicas para sustituir las antiguas", "4.4 y 3.3.6"],
    ["8", "Tablas comparativas modelo preliminar – modelo final", "4.4 (Tablas 4.3–4.4: verificar)"],
    ["9", "Pruebas reales del software", "4.3 Pruebas del sistema, 4.6"],
    ["10", "Mejoras de integración, reproductor, PDF e historial", "3.3.5, 3.4, requerimientos"],
    ["11", "Capturas reales de la aplicación", "3.3.4 Capturas de interfaz"],
    ["12", "Textos propuestos por capítulo (A/B/C/D/E)", "Resumen, alcance, 3.3.5, 3.3.6, 4.3, 4.4, limitaciones, conclusiones, recomendaciones, Apéndice 8"],
    ["13", "Lista exacta de figuras, tablas y párrafos a actualizar", "Todos los capítulos"],
    ["14", "Referencias a archivos originales y evidencias", "Trazabilidad, anexos técnicos"],
], widths=[2, 8, 7], caption="Mapa del dossier", subst=False)
page_break(doc)

# =============================================================================== 1. RESUMEN TÉCNICO
heading(doc, "1. Resumen técnico del modelo de Deep Learning implementado", 1)
callout(doc, "Corresponde a:", ["Resumen, Abstract, 3.3.6 (construcción del modelo), 3.4 (transición). El identificador técnico y los hashes están en la sección 14."])
para(doc, "El sistema clasifica el patrón de marcha de un video en cuatro categorías experimentales (normal, Parkinson, esclerosis múltiple y riesgo de caída). La estimación de los 17 puntos corporales la realiza **MediaPipe Pose, una red preentrenada que no fue entrenada ni ajustada en este proyecto**. El clasificador es **propio del proyecto** (PyTorch): una red convolucional unidimensional de dos ramas, entrenada con los 117 videos del dataset, con 17 788 parámetros entrenables, seguida de una calibración por temperatura.")
table(doc, ["Concepto", "Valor verificado"], [
    ["Entrada de secuencia", "68 canales × 40 muestras (34 posiciones y 34 velocidades de 17 puntos, relativas a la cadera y escaladas por la longitud del torso)"],
    ["Entrada de características", "33 características de marcha (orden y fórmulas en la sección 3)"],
    ["Frecuencia y ventana", "15 Hz; ventana de 2,6 s (40 muestras); tramo analizado de hasta 5,03 s desde el primer cuadro con pose; ventanas cada 0,4 s; hasta 5 ventanas equiespaciadas por video"],
    ["Arquitectura", "Red convolucional 1D de dos ramas (secuencia y características) con cabeza de clasificación; 17 788 parámetros entrenables; PyTorch (CPU)"],
    ["Salida", "4 logits por ventana → media de los logits de las ventanas → división por la temperatura de calibración (T = 0,6615) → softmax → 4 probabilidades"],
    ["Clases (orden)", "normal, parkinson, esclerosis_multiple, riesgo_caida"],
    ["Imputación y escalado", "Mediana del entrenamiento para valores faltantes; media y desviación del entrenamiento; ajustados solo con datos de entrenamiento de cada partición"],
    ["Entrenamiento del modelo final", "117 videos; época óptima 73 elegida por validación cruzada interna agrupada; Adam (tasa 1·10⁻³, decaimiento 2·10⁻⁴), pérdida con pesos de clase y suavizado de etiquetas 0,05"],
    ["Rendimiento interno", "Exactitud 0,8598; F1 macro 0,7852 (validación cruzada agrupada por sujeto, 5 semillas); sin validación clínica ni externa"],
    ["Análisis no concluyente", "Si el seguimiento corporal es insuficiente (tasa de detección < 0,45, < 15 cuadros con pose o ninguna ventana válida) no se presentan clase, probabilidades ni confianza"],
    ["Modelo preliminar", "Se conserva instalado como respaldo; no se usa automáticamente si el modelo final falla (se informa el error)"],
], widths=[4, 12], caption="Ficha resumida del modelo implementado", size=9)
para(doc, "**Diferencia entre componentes.** MediaPipe Pose (preentrenado, externo) convierte cada cuadro en 17 puntos corporales; el clasificador propio (entrenado aquí) convierte la secuencia y las características en las cuatro probabilidades. El informe y la tesis deben mantener esa distinción.")

# =============================================================================== 2. ARQUITECTURA Y PREPROCESAMIENTO
heading(doc, "2. Arquitectura real y preprocesamiento", 1)
callout(doc, "Corresponde a:", ["Propuesta tecnológica desarrollada, arquitectura y componentes, 3.3.5 (flujo), 3.3.6 (modelo y preprocesamiento), diagramas UML afectados."])
heading(doc, "2.1 Arquitectura del clasificador", 2)
ficha = read_md("02_MODELO_V5CR_Y_ARQUITECTURA/FICHA_TECNICA_MODELO_V5CR.md")
md_to_docx(doc, md_section(ficha, "## 3."), base_level=3, size=9)
rows = [[r["capa"], r["parametros_entrenables"]] for r in csv_rows("02_MODELO_V5CR_Y_ARQUITECTURA/arquitectura_capas_V5CR.csv")]
table(doc, ["Capa", "Parámetros entrenables"], rows, widths=[10, 4], caption="Capas del clasificador y sus parámetros (calculados del checkpoint)", size=9, subst=False, align_right_from=1)
figure(doc, F / "fig_arquitectura_GaitTemporalModel_V5CR.png", "Arquitectura del clasificador de marcha del modelo final: red convolucional unidimensional de dos ramas (17 788 parámetros entrenables).", FUENTE, width_cm=17)
figure(doc, F / "fig_flujo_completo_sistema_V5CR.png", "Flujo de análisis del video al resultado orientativo. MediaPipe Pose es una red preentrenada; el clasificador es propio.", FUENTE, width_cm=17)
heading(doc, "2.2 Entradas, tiempo y orden", 2)
md_to_docx(doc, md_section(ficha, "## 4."), base_level=3, size=9)
heading(doc, "2.3 Preprocesamiento del modelo final", 2)
pre = read_md("07_PREPROCESAMIENTO_Y_FORMULAS/PREPROCESAMIENTO_V5CR.md")
para(doc, "**Procedimiento por ventana de 2,6 s.**")
md_to_docx(doc, md_section(pre, "## 1."), base_level=3, size=9)
figure(doc, F / "fig_diagrama_preprocesamiento_V5CR.png", "Preprocesamiento de una ventana de 2,6 s del modelo final.", FUENTE, width_cm=17)
heading(doc, "2.4 Defectos del modelo preliminar corregidos", 2)
md_to_docx(doc, md_section(pre, "## 2."), base_level=3, size=9)
heading(doc, "2.5 Valores faltantes (NaN), normalización e imputación", 2)
md_to_docx(doc, md_section(pre, "## 3."), base_level=3, size=9)
md_to_docx(doc, md_section(ficha, "## 6."), base_level=3, size=9)
heading(doc, "2.6 Logits, calibración, entrenamiento y criterios de no concluyente", 2)
md_to_docx(doc, md_section(ficha, "## 7."), base_level=3, size=9)
md_to_docx(doc, md_section(ficha, "## 8."), base_level=3, size=9)
md_to_docx(doc, md_section(ficha, "## 9."), base_level=3, size=9)
heading(doc, "2.7 Limitaciones geométricas declaradas", 2)
md_to_docx(doc, md_section(pre, "## 4."), base_level=3, size=9)

# =============================================================================== 3. CARACTERÍSTICAS
heading(doc, "3. Las 33 características y sus fórmulas", 1)
callout(doc, "Corresponde a:", ["3.3.6 (extracción de características), apéndice técnico de características. Todas son aproximaciones adimensionales (en longitudes de torso), ángulos o conteos de una ventana de 2,6 s; **no son mediciones clínicas en metros, segundos o grados**."])
para(doc, "Notación: **H** centro de caderas, **S** centro de hombros, **s** longitud del torso (mediana de |S−H| en la ventana), **Δ** diferencia entre muestras consecutivas (1/15 s), **rng** = percentil 95 − percentil 5, **asim(a,b)** = |a−b| / máx(|a|,|b|,10⁻⁶). El orden de la tabla es el del modelo.")
set_orientation(doc, True)
feat = csv_rows("07_PREPROCESAMIENTO_Y_FORMULAS/TABLA_33_CARACTERISTICAS_V5CR.csv")
table(doc, ["N.º", "Nombre en el código", "Nombre en español", "Fórmula", "Significado", "Unidad / naturaleza", "Puntos corporales", "Limitaciones de interpretación", "Equivalente en el modelo preliminar"],
      [[r["n"], r["nombre_en_codigo"], r["nombre_en_espanol"], r["formula"], r["significado"], r["unidad_o_naturaleza"], r["puntos_corporales"], r["limitaciones_de_interpretacion"], r["equivalente_en_V4"]] for r in feat],
      widths=[0.8, 3, 3.2, 4.2, 3.2, 2.2, 2.4, 4.2, 3], caption="Las 33 características del modelo final (fórmulas, unidades y limitaciones)", size=7, subst=True)
corr = csv_rows("07_PREPROCESAMIENTO_Y_FORMULAS/CORRESPONDENCIA_36_V4_A_33_V5CR.csv")
table(doc, ["Posición", "Nombre en el modelo preliminar (36)", "Nombre en la versión intermedia P", "Estado en el modelo final (33)"],
      [[r["posicion_en_V4"], r["nombre_V4"], r["nombre_V5_(P)"], r["estado_en_V5-CR"]] for r in corr], widths=[1.4, 5, 5, 9], caption="Correspondencia entre las 36 características del modelo preliminar y las 33 del modelo final (3 eliminadas, 4 redefinidas)", size=8, subst=True)
set_orientation(doc, False)
figure(doc, F / "fig_comparacion_caracteristicas_V4_vs_V5CR.png", "Características de marcha por grupo funcional: modelo preliminar (36) frente a modelo final (33).", FUENTE, width_cm=17)
para(doc, "**Eliminadas** respecto al modelo preliminar: `hip_center_motion_mean`, `shoulder_center_motion_mean` y `horizontal_motion_mean` (dependían del desplazamiento global en la imagen y, por tanto, de la cámara). **Redefinidas sin avance horizontal** respecto a la versión intermedia P: `body_motion_mean`, `body_motion_std`, `motion_smoothness` y `gait_variability`. Frente al modelo preliminar cambian además los cálculos de piernas, brazos, tronco y ritmo (ver «Estado» en la tabla de correspondencia).", subst=True)

# =============================================================================== 4. DATASET
heading(doc, "4. Dataset, metodología y limitaciones", 1)
callout(doc, "Corresponde a:", ["Población y muestra, metodología de investigación, 3.3.6.1 (dataset), Apéndice 8 (ficha técnica e inventario), limitaciones de 4.4."])
ds = read_md("03_DATASET_Y_METODOLOGIA/DATASET_Y_METODOLOGIA.md")
# se renderiza el documento completo (sin su título) con encabezados de nivel 2
body = ds.split("\n", 1)[1]
body = re.sub(r"^>.*\n", "", body, flags=re.M)
md_to_docx(doc, body, base_level=2, size=9)
res = csv_rows("03_DATASET_Y_METODOLOGIA/RESUMEN_DATASET_POR_CLASE.csv")
table(doc, ["Clase", "Videos", "Grupos", "Grupos provisionales", "Grupos con identidad registrada", "Duración media (s)", "Duración mín.–máx. (s)"],
      [[CLN.get(r["clase"], r["clase"].upper()), r["videos"], r["grupos"], r["grupos_provisionales"], r["grupos_con_identidad_registrada"], num(r.get("duracion_media_s", "") or "—"), (num(r["duracion_min_s"]) + " – " + num(r["duracion_max_s"])) if r.get("duracion_min_s") else "—"] for r in res],
      widths=[3, 1.6, 1.6, 2.4, 3, 2.4, 3], caption="Resumen del dataset por clase (117 videos, 67 grupos técnicos de sujeto)", size=9, subst=False)
figure(doc, F / "fig_distribucion_dataset.png", "Distribución del conjunto de 117 videos por clase, grupo de sujeto y fuente de grabación.", "«Provisional»: la fuente no identifica a la persona. " + FUENTE, width_cm=17)
exc = csv_rows("03_DATASET_Y_METODOLOGIA/VIDEOS_EXCLUIDOS_20_CON_MOTIVO.csv")
table(doc, ["ID del video", "Categoría", "Decisión", "Motivo"], [[r["ID video"], r["Categoría"], r["Decisión"], r["Motivo"]] for r in exc], widths=[3, 3, 2.5, 10], caption="Videos excluidos del entrenamiento y la evaluación (20)", size=8, subst=True)
para(doc, "El inventario completo de los 117 videos (identificador, grupo técnico, estado, fuente, orientación, vista, cámara, duración, fps y resolución) está en el Apéndice A de este dossier, para el Apéndice 8 de la tesis.", subst=False)

# =============================================================================== 5. MÉTRICAS DEFINITIVAS
heading(doc, "5. Métricas definitivas del modelo final", 1)
callout(doc, "Corresponde a:", ["4.4 Evaluación del modelo. Las 63 métricas fueron recalculadas desde las predicciones fuera de partición y coinciden con los resultados originales (63/63)."])
mt = read_md("04_METRICAS_Y_COMPARACIONES/METRICAS_Y_COMPARACIONES.md")
heading(doc, "5.1 Protocolo (leer antes de citar cualquier cifra)", 2)
md_to_docx(doc, md_section(mt, "## 0."), base_level=3, size=9)
heading(doc, "5.2 Métricas del modelo final", 2)
fm = met["V5-CR"]
rows = [["Exactitud", f4(fm["exactitud"]), f"[{f4(ci[('V5-CR','exactitud')]['IC95_inf'])}; {f4(ci[('V5-CR','exactitud')]['IC95_sup'])}]", "", ""],
        ["F1 macro", f4(fm["f1_macro"]), f"[{f4(ci[('V5-CR','f1_macro')]['IC95_inf'])}; {f4(ci[('V5-CR','f1_macro')]['IC95_sup'])}]", "", ""]]
tab_rows = []
for c in CL:
    k = ci[("V5-CR", f"f1_{c}")]
    s = ci[("V5-CR", f"sensibilidad_{c}")]
    tab_rows.append([CLN[c].capitalize(), f4(fm[f"precision_{c}"]), f"{f4(fm[f'sensibilidad_{c}'])} [{f4(s['IC95_inf'])}; {f4(s['IC95_sup'])}]", f"{f4(fm[f'f1_{c}'])} [{f4(k['IC95_inf'])}; {f4(k['IC95_sup'])}]"])
table(doc, ["Medida global", "Valor", "IC95 % (bootstrap por grupo)"], [r[:3] for r in rows], widths=[4, 3, 6], caption="Métricas globales del modelo final (promedio de 5 semillas)", size=9, subst=False)
table(doc, ["Clase", "Precisión", "Sensibilidad [IC95 %]", "F1 [IC95 %]"], tab_rows, widths=[3.5, 2.6, 5.4, 5.4], caption="Precisión, sensibilidad y F1 por clase del modelo final", size=9, subst=False)
table(doc, ["Calibración del modelo final", "Valor"], [["ECE sin calibrar", f4(fm["ece_sin_calibrar"])], ["ECE calibrado (temperatura por partición)", f4(fm["ece_calibrado_por_particion"])], ["Brier sin calibrar", f4(fm["brier_sin_calibrar"])], ["Brier calibrado", f4(fm["brier_calibrado_por_particion"])],
                                              ["F1 macro por semilla (42–46)", num(", ".join(f"{x:.4f}" for x in json.loads(fm["f1_macro_por_semilla"])))]], widths=[8, 6], caption="Calibración y variabilidad por semilla del modelo final", size=9, subst=False)
heading(doc, "5.3 Calibración", 2)
_c = md_section(mt, "## 4.")
md_to_docx(doc, _c[_c.index("**Comparación válida"):], base_level=3, size=9)
heading(doc, "5.4 Referencia de sesgo de adquisición", 2)
md_to_docx(doc, md_section(mt, "## 8."), base_level=3, size=9)
heading(doc, "5.5 Lo que no se puede decir", 2)
md_to_docx(doc, md_section(mt, "## 7."), base_level=3, size=9)

# =============================================================================== 6. MATRICES
heading(doc, "6. Matrices de confusión verificadas", 1)
callout(doc, "Corresponde a:", ["4.4 (matriz de confusión; sustituye a las matrices de la versión anterior; Figuras 4.9–4.11 de la tesis: verificar su contenido). Generadas a 300 dpi desde las predicciones originales; los datos en CSV están en el repositorio."])
lm = read_md("05_MATRICES_DE_CONFUSION/LEEME_MATRICES.md")
md_to_docx(doc, lm.split("\n", 1)[1], base_level=2, size=9)
SRCM = "Evaluación interna; 117 videos, 5 semillas. " + FUENTE
figure(doc, M / "matriz_confusion_V5CR_A_absoluta_suma5.png", "Matriz de confusión del modelo final en valores absolutos (suma de 5 repeticiones: 585 predicciones, no 585 videos).", SRCM, width_cm=12)
figure(doc, M / "matriz_confusion_V5CR_B_normalizada.png", "Matriz de confusión del modelo final normalizada por clase verdadera (%).", SRCM, width_cm=12)
figure(doc, M / "matriz_confusion_V5CR_C_voto_mayoritario.png", "Matriz de confusión del modelo final por voto mayoritario de las 5 semillas (117 videos).", SRCM, width_cm=12)
figure(doc, M / "matriz_confusion_V4activo_A_absoluta_suma5.png", "Matriz de confusión del modelo preliminar activo en valores absolutos (suma de 5 repeticiones).", SRCM, width_cm=12)
figure(doc, M / "matriz_confusion_V4activo_B_normalizada.png", "Matriz de confusión del modelo preliminar activo normalizada por clase verdadera (%).", SRCM, width_cm=12)
figure(doc, M / "matriz_confusion_V4activo_C_voto_mayoritario.png", "Matriz de confusión del modelo preliminar activo por voto mayoritario (117 videos).", SRCM, width_cm=12)
figure(doc, M / "matriz_confusion_D_comparacion_V4activo_vs_V5CR.png", "Comparación de matrices normalizadas del modelo preliminar activo y del modelo final, y su diferencia en puntos porcentuales (mismas particiones y videos).", SRCM, width_cm=17)
cm = json.load(open(M / "datos" / "matrices_resumen.json", encoding="utf-8"))
for key, titulo in (("V5-CR", "modelo final"), ("V4 activo (BN recalibrada)", "modelo preliminar activo")):
    mm = cm[key]["suma"]
    table(doc, ["Clase verdadera \\ predicha", "Normal", "Parkinson", "Esclerosis múltiple", "Riesgo de caída", "Total"], [[CLN[c].capitalize(), *mm[i], sum(mm[i])] for i, c in enumerate(CL)], widths=[4, 2.2, 2.2, 2.8, 2.6, 2], caption=f"Matriz de confusión del {titulo}: suma de 5 repeticiones (585 predicciones; datos numéricos de la figura)", size=9, subst=False, align_right_from=1)
    vm = cm[key]["voto"]
    table(doc, ["Clase verdadera \\ predicha", "Normal", "Parkinson", "Esclerosis múltiple", "Riesgo de caída", "Total"], [[CLN[c].capitalize(), *vm[i], sum(vm[i])] for i, c in enumerate(CL)], widths=[4, 2.2, 2.2, 2.8, 2.6, 2], caption=f"Matriz de confusión del {titulo}: voto mayoritario por video (117 videos)", size=9, subst=False, align_right_from=1)

# =============================================================================== 7. GRÁFICAS
heading(doc, "7. Gráficas académicas para sustituir las antiguas", 1)
callout(doc, "Corresponde a:", ["4.4 (comparación de versiones, desempeño por clase, variabilidad, calibración, robustez). Las curvas de entrenamiento NO existen (no se guardaron) y por eso no se incluyen; no deben reconstruirse."])
figure(doc, F / "fig_comparacion_exactitud_f1macro_por_version.png", "Exactitud y F1 macro por versión del modelo (validación cruzada agrupada por sujeto, 5 semillas; IC95 % por remuestreo de grupos). Evaluación interna.", FUENTE, width_cm=15)
figure(doc, F / "fig_V5CR_precision_sensibilidad_f1_por_clase.png", "Precisión, sensibilidad y F1 por clase del modelo final.", FUENTE, width_cm=15)
figure(doc, F / "fig_f1_macro_por_semilla.png", "F1 macro por semilla de partición.", FUENTE, width_cm=14)
figure(doc, F / "fig_calibracion_V5CR_diagrama_fiabilidad.png", "Diagrama de fiabilidad del modelo final (sin calibrar y con temperatura) y del modelo preliminar activo (sin calibrar). Predicciones agrupadas de las 5 repeticiones.", FUENTE, width_cm=12.5)
figure(doc, F / "fig_robustez_camara_ruido_perdida_fotogramas.png", "Cambio del F1 macro ante perturbaciones de la grabación (modelos congelados). El modelo preliminar corresponde a la versión base.", FUENTE, width_cm=16.5)

# =============================================================================== 8. COMPARACIONES
heading(doc, "8. Tablas comparativas: modelo preliminar y modelo implementado", 1)
callout(doc, "Corresponde a:", ["4.4 (Tablas 4.3–4.4 de la tesis: verificar su contenido). Mismos 117 videos, grupos y particiones para todas las versiones (comparación pareada). «Modelo preliminar activo» es el que operaba antes del modelo final."])
heading(doc, "8.1 Métricas globales y por clase de las cinco versiones", 2)
table(doc, ["Modelo", "Exactitud", "F1 macro", "F1 normal", "F1 Parkinson", "F1 esclerosis múltiple", "F1 riesgo de caída"],
      [[A[m], f4(met[m]["exactitud"]), f4(met[m]["f1_macro"]), f4(met[m]["f1_normal"]), f4(met[m]["f1_parkinson"]), f4(met[m]["f1_esclerosis_multiple"]), f4(met[m]["f1_riesgo_caida"])] for m in MODELS],
      widths=[4.6, 1.9, 1.9, 1.9, 2, 2.4, 2.2], caption="Comparación de exactitud, F1 macro y F1 por clase por versión del modelo", size=8.5, subst=False, bold_first_col=True, align_right_from=1)
table(doc, ["Modelo", "Exactitud [IC95 %]", "F1 macro [IC95 %]"],
      [[A[m], f"{f4(ci[(m,'exactitud')]['valor'])} [{f4(ci[(m,'exactitud')]['IC95_inf'])}; {f4(ci[(m,'exactitud')]['IC95_sup'])}]", f"{f4(ci[(m,'f1_macro')]['valor'])} [{f4(ci[(m,'f1_macro')]['IC95_inf'])}; {f4(ci[(m,'f1_macro')]['IC95_sup'])}]"] for m in MODELS],
      widths=[5, 5.5, 5.5], caption="Intervalos de confianza (95 %, bootstrap por grupo de sujeto, 2000 remuestreos) de exactitud y F1 macro", size=9, subst=False, bold_first_col=True)
heading(doc, "8.2 Precisión y sensibilidad por clase: modelo preliminar activo y modelo final", 2)
rows = []
for c in CL:
    rows.append([CLN[c].capitalize(), f4(met["V4 activo (BN recalibrada)"][f"precision_{c}"]), f4(met["V5-CR"][f"precision_{c}"]), f4(met["V4 activo (BN recalibrada)"][f"sensibilidad_{c}"]), f4(met["V5-CR"][f"sensibilidad_{c}"])])
table(doc, ["Clase", "Precisión: modelo preliminar activo", "Precisión: modelo final", "Sensibilidad: modelo preliminar activo", "Sensibilidad: modelo final"], rows, widths=[3.4, 3.2, 3, 3.6, 3], caption="Precisión y sensibilidad por clase del modelo preliminar activo y del modelo final", size=9, subst=False, align_right_from=1)
heading(doc, "8.3 Diferencias con intervalos de confianza", 2)
dif = csv_rows("04_METRICAS_Y_COMPARACIONES/DIFERENCIAS_V5CR_VS_OTROS.csv")
NAME = {"V4 BN (activo)": "modelo preliminar activo", "V4 base": "modelo preliminar base", "V5-P": "versión intermedia P", "V5-C": "versión intermedia C", "V5-CR": "modelo final"}
MET = {"exactitud": "Exactitud", "f1_macro": "F1 macro", "ece_sin_calibrar": "ECE sin calibrar"}
for c in CL:
    MET[f"f1_{c}"] = f"F1 {CLN[c]}"
    MET[f"sensibilidad_{c}"] = f"Sensibilidad {CLN[c]}"


def difrows(comp, keys=None):
    out = []
    for r in dif:
        if r["comparacion (primero - segundo)"] != comp:
            continue
        mname = r["metrica"]
        if keys and mname not in keys:
            continue
        if mname.startswith("mcnemar"):
            out.append(["McNemar sobre voto mayoritario", f"{r['diferencia_observada']} videos (solo el primero/solo el segundo)", "—", r["interpretacion_IC"]])
            continue
        inc = "excluye 0" if r["interpretacion_IC"] == "excluye 0" else "incluye 0 (no concluyente)"
        out.append([MET.get(mname, mname), num(r["diferencia_observada"]), f"[{num(r['IC95_inf'])}; {num(r['IC95_sup'])}]", inc])
    return out


a, b = "V5-CR", "V4 BN (activo)"
table(doc, ["Métrica", "Diferencia (modelo final − modelo preliminar activo)", "IC95 %", "¿El intervalo excluye 0?"], difrows(f"{a} - {b}"), widths=[5, 5.4, 3.6, 4], caption="Diferencias entre el modelo final y el modelo preliminar activo (positivo = mejora del modelo final; para la ECE positivo = peor calibración)", size=8.5, subst=False, align_right_from=None)
for comp, ttl in (("V5-CR - V4 base", "modelo final − modelo preliminar base"), ("V5-CR - V5-P", "modelo final − versión intermedia P"), ("V5-CR - V5-C", "modelo final − versión intermedia C")):
    table(doc, ["Métrica", f"Diferencia ({ttl})", "IC95 %", "¿El intervalo excluye 0?"], difrows(comp, ["exactitud", "f1_macro", "f1_normal", "f1_riesgo_caida", "ece_sin_calibrar"]), widths=[5, 5.4, 3.6, 4], caption=f"Diferencias seleccionadas: {ttl}", size=8.5, subst=False)
heading(doc, "8.4 Calibración", 2)
cal_rows = [[A[m], f4(met[m]["ece_sin_calibrar"]), f4(met[m]["ece_calibrado_por_particion"]) if met[m]["ece_calibrado_por_particion"] else ("0,0762 (solo esta versión)" if m == "V4 base" else "no disponible"), f4(met[m]["brier_sin_calibrar"]), f4(met[m]["brier_calibrado_por_particion"]) if met[m]["brier_calibrado_por_particion"] else ("0,2691 (solo esta versión)" if m == "V4 base" else "no disponible")] for m in MODELS]
table(doc, ["Modelo", "ECE sin calibrar", "ECE calibrado por partición", "Brier sin calibrar", "Brier calibrado"], cal_rows, widths=[4.6, 2.4, 3.6, 2.6, 3.2], caption="Calibración de las cinco versiones (la calibración por partición existe para las versiones intermedias, el modelo final y solo el modelo preliminar base)", size=8.5, subst=False, align_right_from=1)
para(doc, "Solo es válida la comparación **sin calibrar** con el modelo preliminar activo, en la que el modelo final es significativamente peor (+0,064; IC95 0,022 a 0,085). El modelo preliminar base calibrado (0,076) es la única referencia calibrada bajo el mismo protocolo; la diferencia con el modelo final calibrado (0,064) no tiene intervalo calculado. El modelo preliminar activo usa una temperatura global de 0,9022 y el modelo final de 0,6615.", subst=True)
heading(doc, "8.5 Robustez frente a perturbaciones de la grabación", 2)
rob = csv_rows("04_METRICAS_Y_COMPARACIONES/ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv")
piv, order = {}, []
for r in rob:
    if r["prueba"] not in piv:
        piv[r["prueba"]] = {}
        order.append(r["prueba"])
    piv[r["prueba"]][r["modelo"]] = r["delta_f1_macro"]
table(doc, ["Perturbación (cambio del F1 macro respecto a la línea base de cada modelo)", "Modelo preliminar base", "Versión intermedia P", "Versión intermedia C", "Modelo final"],
      [[p] + [(num(f"{float(piv[p][m]):+.3f}") if m in piv[p] else "—") for m in ("V4 base", "V5-P", "V5-C", "V5-CR")] for p in order], widths=[7, 2.6, 2.6, 2.6, 2.4], caption="Cambio del F1 macro ante perturbaciones (modelos congelados; el modelo preliminar corresponde a la versión base)", size=8.5, subst=False, align_right_from=1)
para(doc, "El modelo final es invariante por construcción a la cámara que sigue a la persona, al paneo, a la relación de aspecto y al zoom (verificado numéricamente en 633 ventanas reales). No mejora el ruido en los puntos corporales ni la pérdida de fotogramas. Un filtro pasa-bajos reduce su F1 macro en 0,336 y aleatorizar las fases en 0,609; desordenar bloques temporales apenas lo cambia (−0,009).")
heading(doc, "8.6 Interpretación", 2)
for t_ in ["La mejora global del modelo final sobre el modelo preliminar activo **no es estadísticamente concluyente** (F1 macro +0,041 [−0,029; 0,102]).",
           "La única mejora respaldada es la de la clase riesgo de caída (F1 +0,203 [0,023; 0,356]; sensibilidad +0,327 [0,125; 0,525]), con 11 videos y 9 grupos.",
           "La esclerosis múltiple empeora (F1 −0,072, no concluyente) y la confusión predominante es esclerosis múltiple ↔ riesgo de caída.",
           "El F1 macro del modelo final es del mismo orden que el de una sonda que solo utiliza 7 metadatos técnicos del video (0,777–0,786).",
           "Todos los resultados son internos; no constituyen rendimiento clínico."]:
    bullet(doc, t_)

# =============================================================================== 9. PRUEBAS
heading(doc, "9. Pruebas reales del software", 1)
callout(doc, "Corresponde a:", ["4.3 Pruebas del sistema y 4.6 Conclusión de pruebas. Cada batería se cuenta una sola vez (no se suman las mismas comprobaciones de informes distintos). Las automatizadas se distinguen de las manuales del propietario."])
pr = csv_rows("08_PRUEBAS_DEL_SISTEMA/PRUEBAS_EJECUTADAS_RESUMEN.csv")
set_orientation(doc, True)
table(doc, ["Batería", "Tipo", "Fecha de la evidencia", "Total", "Aprobadas", "Fallidas", "Entorno", "Limitaciones"],
      [[r["bateria"], r["tipo"], r["fecha_de_la_evidencia"], r["total"], r["aprobadas"], r["fallidas"], r["entorno"], r["limitaciones"]] for r in pr], widths=[6, 2.4, 2.2, 1.1, 1.5, 1.3, 4.2, 7], caption="Baterías de pruebas realmente ejecutadas (18)", size=7.5, subst=True)
set_orientation(doc, False)
for t_ in ["**Resultado:** todas las baterías con aprobado/fallido terminaron sin comprobaciones fallidas en su versión final (las 7 filas de demostración de defectos del modelo preliminar no son pruebas aprobadas de la versión corregida).",
           "**Equivalencia con el evaluador:** el predictor desplegado reproduce las secuencias, características, logits y probabilidades del evaluador en 117 de 117 videos (error máximo 0).",
           "**Defectos encontrados y corregidos durante las pruebas:** límite de tiempo del modelo que se presentaba como «modelo no disponible»; reproductor que dejaba de funcionar al repetir el video; PDF de texto plano con identificadores internos y contenido distinto del informe en pantalla.",
           "**Alcance:** el entorno de las pruebas automatizadas fue aislado (base técnica local, cuentas de prueba, Cloudinary desactivado); sobre la base habitual solo hubo lecturas y pruebas manuales del propietario; solo se usó Chrome; no se probaron dispositivos móviles reales ni otros navegadores.",
           "**No ejecutadas en esta serie:** la prueba legada del pipeline del modelo preliminar, el retroceso explícito al modelo preliminar con un video, y los fallos por caída nativa o salida inválida."]:
    bullet(doc, t_)

# =============================================================================== 10. INTEGRACIÓN, REPRODUCTOR, PDF, HISTORIAL
heading(doc, "10. Mejoras de integración, reproductor de video, informe PDF e historial", 1)
callout(doc, "Corresponde a:", ["3.3.5 Construcción e implementación, 3.4 Fase de transición, requerimientos de análisis, resultado, informe, historial y administración."])
est = read_md("01_ESTADO_FINAL_DEL_SOFTWARE/ESTADO_FINAL_DEL_SOFTWARE.md")
heading(doc, "10.1 Funcionalidades implementadas, comprobadas y pendientes", 2)
md_to_docx(doc, md_section(est, "## 2."), base_level=3, size=8)
heading(doc, "10.2 Qué está demostrado, qué es experimental y qué sigue pendiente", 2)
md_to_docx(doc, md_section(est, "## 3."), base_level=3, size=9)
heading(doc, "10.3 Limitaciones técnicas conocidas", 2)
md_to_docx(doc, md_section(est, "## 4."), base_level=3, size=9)
heading(doc, "10.4 Gestión de informes PDF y del historial", 2)
gp = read_md("10_INFORMES_PDF_E_HISTORIAL/GESTION_DE_INFORMES_PDF_E_HISTORIAL.md")
md_to_docx(doc, gp.split("\n", 1)[1], base_level=3, size=9)

# =============================================================================== 11. CAPTURAS
heading(doc, "11. Capturas reales de la aplicación", 1)
callout(doc, "Corresponde a:", ["3.3.4 Capturas de interfaz. Capturas reales de la aplicación (versión de producción) en un entorno aislado con cuentas técnicas; **los fotogramas de video se ocultaron por privacidad** y en las pantallas de procesamiento aparece «no se pudo guardar el video en la nube» porque Cloudinary estaba desactivado en la prueba. No se publicaron nombres, correos ni videos de usuarios."])
CAP = [
    ("01_inicio_de_sesion.png", "Pantalla de inicio de sesión.", "RF de autenticación"),
    ("02_registro.png", "Pantalla de registro de usuario.", "RF de registro"),
    ("03_panel_principal_usuario.png", "Panel principal del usuario.", "Panel principal"),
    ("04_carga_de_video_vacia.png", "Carga de video: estado inicial.", "RF de carga de video"),
    ("05_carga_de_video_con_vista_previa.png", "Carga de video con vista previa (el fotograma se oculta por privacidad).", "RF de carga de video"),
    ("06_revision_del_video.png", "Revisión del video antes del análisis.", "Revisión previa"),
    ("07_procesamiento_en_curso.png", "Procesamiento del video en curso, con el reproductor independiente del análisis.", "Procesamiento"),
    ("08_procesamiento_completado.png", "Procesamiento completado.", "Procesamiento"),
    ("09_resultado_V5CR_probabilidades_y_advertencias.png", "Resultado del análisis: clase indicada, probabilidades de las cuatro categorías, advertencias, observaciones y parámetros de marcha.", "Resultado"),
    ("10_evaluacion_detallada.png", "Análisis detallado de la marcha.", "Evaluación detallada"),
    ("12_informe_visual.png", "Informe visual (vista previa del informe en formato A4).", "Informe"),
    ("13_informe_guardado_e_historial_de_informes.png", "Informe guardado y lista de informes con los botones «Ver informe» y «Descargar PDF».", "Informe e historial"),
    ("11_informes_guardados_tras_recargar.png", "Pantalla de informes guardados leídos de la base de datos.", "Historial de informes"),
    ("14_seguimiento_historial_de_analisis.png", "Seguimiento: historial de análisis del usuario.", "Historial"),
    ("15_movil_panel_principal.png", "Vista móvil (390 px): panel principal.", "Diseño adaptable"),
    ("16_movil_historial.png", "Vista móvil (390 px): historial.", "Diseño adaptable"),
    ("20_administracion_inicio_estado_del_modelo.png", "Panel de administración: estado del sistema y tarjeta del modelo actual (versión, clases, videos, grupos, macro-F1 y exactitud internos).", "Administración"),
    ("17_administracion_estado_del_modelo.png", "Administración: usuarios registrados.", "Administración"),
    ("18_administracion_analisis.png", "Administración: análisis del sistema.", "Administración"),
    ("19_administracion_informes_guardados.png", "Administración: informes guardados del sistema.", "Administración"),
]
for fn, cap, ap in CAP:
    p = C / fn
    w = 7.5 if fn.startswith(("15_", "16_")) else (15.5 if fn.split("_")[0] in ("09", "10", "12", "13") else 14.5)
    figure(doc, p, cap, "Captura de la aplicación (entorno de prueba aislado). " + FUENTE, width_cm=w, internal_note=False)
heading(doc, "11.1 Informe PDF descargado (diseño unificado con la pantalla)", 2)
figure(doc, R / "pdf_DESPUES_pagina1.png", "Informe PDF descargado con el botón de la aplicación: página 1 de 2 (formato A4, texto seleccionable).", "Cuenta técnica de prueba. " + FUENTE, width_cm=12.5, internal_note=False)
figure(doc, R / "pdf_DESPUES_pagina2.png", "Informe PDF descargado: página 2 de 2.", "Cuenta técnica de prueba. " + FUENTE, width_cm=12.5, internal_note=False)
figure(doc, R / "comparacion_pantalla_vs_pdf.png", "Comparación entre el informe visual de la aplicación (izquierda) y las dos páginas del PDF descargado.", FUENTE, width_cm=17, internal_note=False)
figure(doc, E / "variante_riesgo.png", "Informe PDF de un resultado con clase «riesgo de caída» (con aviso de clase experimental y observaciones).", "Ejemplo generado con datos de una prueba. " + FUENTE, width_cm=17, internal_note=False)
figure(doc, E / "variante_noconcluyente.png", "Informe PDF de un análisis no concluyente por calidad del video (sin clasificación ni confianza).", "Ejemplo generado con datos de una prueba. " + FUENTE, width_cm=10, internal_note=False)
ic = read_md("09_CAPTURAS_Y_EVIDENCIAS/INDICE_CAPTURAS.md")
heading(doc, "11.2 Capturas pendientes", 2)
md_to_docx(doc, md_section(ic, "## Pendientes"), base_level=3, size=8.5)

# =============================================================================== 12. TEXTOS PROPUESTOS
heading(doc, "12. Textos propuestos para cada capítulo de la tesis", 1)
callout(doc, "Cómo leer esta sección", ["Cada texto se organiza en: **A** texto nuevo propuesto (usar con nombres académicos), **B** información histórica que debe conservarse, **C** texto anterior que debe reemplazarse (se transcriben los términos tal como aparecen en la tesis actual), **D** figuras y tablas que deben insertarse (referencias a este dossier) y **E** fuentes técnicas. Ubique cada apartado en su Word antes de pegar."], subst=False)
TEXTOS = [("01_RESUMEN_Y_ABSTRACT.md", "12.1"), ("02_ALCANCE_Y_METODOLOGIA.md", "12.2"), ("03_PROPUESTA_TECNOLOGICA_Y_ARQUITECTURA.md", "12.3"), ("04_CONSTRUCCION_DEL_MODELO_3_3_6.md", "12.4"), ("05_INTEGRACION_FINAL_3_3_5.md", "12.5"),
          ("06_PRUEBAS_4_3_Y_4_6.md", "12.6"), ("07_EVALUACION_Y_RESULTADOS_4_4.md", "12.7"), ("08_LIMITACIONES.md", "12.8"), ("09_CONCLUSIONES_Y_RECOMENDACIONES.md", "12.9"), ("10_APENDICE_8_DATASET.md", "12.10")]
for fn, num_ in TEXTOS:
    txt = read_md("12_TEXTOS_PROPUESTOS_PARA_TESIS/" + fn)
    title = txt.split("\n", 1)[0].lstrip("# ").strip()
    heading(doc, f"{num_} {title}", 2)
    blocks = re.split(r"(?m)^(?=## )", txt.split("\n", 1)[1])
    for blk in blocks:
        if not blk.strip():
            continue
        first = blk.split("\n", 1)[0]
        keep_literal = bool(re.match(r"## (C\.|D\.|E\.)", first))
        h = re.match(r"##\s+(.*)", first)
        if h:
            heading(doc, h.group(1), 3, subst=not keep_literal)
            blk = blk.split("\n", 1)[1] if "\n" in blk else ""
        md_to_docx(doc, blk, base_level=4, subst=not keep_literal, size=9)

# =============================================================================== 13. LISTA EXACTA DE CAMBIOS
heading(doc, "13. Lista exacta de figuras, tablas y párrafos que necesitan actualizarse", 1)
callout(doc, "Importante", ["Esta sección conserva los **términos tal como aparecen en la tesis actual** (V4, 36 características, etc.) para que pueda buscarlos con la función de búsqueda de Word. El Word no estaba disponible: las ubicaciones son probables y deben verificarse. V4 se conserva como antecedente; no se reemplaza de forma indiscriminada."], fill=WARN_FILL, subst=False)
heading(doc, "13.1 Apartados y párrafos por capítulo", 2)
set_orientation(doc, True)
cam = csv_rows("11_CAMBIOS_POR_CAPITULO/CAMBIOS_POR_CAPITULO.csv")
table(doc, ["Capítulo", "Apartado", "Contenido anterior (probable)", "Cambio necesario", "V4 como histórico", "Texto/figura nuevo", "Fuente"],
      [[r["capitulo"], r["apartado"], r["contenido_anterior_probable"], r["cambio_necesario"], r["conservar_V4_como_historico"], r["figura_tabla_o_texto_nuevo"], r["fuente_del_repositorio"]] for r in cam], widths=[2, 3, 4, 8, 3, 3.5, 3], caption="Apartados de la tesis que deben actualizarse (23)", size=7.5, subst=False)
set_orientation(doc, False)
heading(doc, "13.2 Términos y valores obsoletos que deben buscarse en todo el documento", 2)
cm_md = read_md("11_CAMBIOS_POR_CAPITULO/CAMBIOS_POR_CAPITULO.md")
md_to_docx(doc, cm_md.split("## Términos y valores obsoletos que deben buscarse en todo el documento (Ctrl+B)")[1], base_level=3, subst=False, size=8.5)
heading(doc, "13.3 Figuras que deben insertarse o sustituir a las antiguas", 2)
table(doc, ["N.º en este dossier", "Título propuesto para la tesis", "Sección del dossier", "Archivo original"], [[f[0], f[1], f[2], f[3]] for f in L.REG_FIG if f[3].startswith(("fig_", "matriz"))], widths=[2.2, 10, 3.6, 5], caption="Figuras que deben insertarse o sustituir (sin las capturas de interfaz, listadas en 13.4)", size=8, subst=False)
caps_ = [f for f in L.REG_FIG if not f[3].startswith(("fig_", "matriz"))]
table(doc, ["N.º en este dossier", "Captura", "Archivo original"], [[f[0], f[1], f[3]] for f in caps_], widths=[2.2, 11, 6], caption="Capturas de interfaz para el apartado 3.3.4", size=8, subst=False)
heading(doc, "13.4 Tablas que deben insertarse o actualizar", 2)
table(doc, ["N.º en este dossier", "Título", "Sección del dossier"], [[t_[0], t_[1], t_[2]] for t_ in L.REG_TAB], widths=[2.2, 11, 5], caption="Tablas del dossier disponibles para la tesis", size=8, subst=False)

# =============================================================================== 14. REFERENCIAS
heading(doc, "14. Referencias a los archivos originales del repositorio y sus evidencias", 1)
callout(doc, "Nota", ["Las rutas son relativas a la raíz del repositorio del proyecto y sirven solo como procedencia; no es necesario abrirlas. Aquí sí se emplean los nombres internos de las versiones."], subst=False)
heading(doc, "14.1 Identificación técnica del modelo implementado", 2)
fd = json.load(open(PKG / "02_MODELO_V5CR_Y_ARQUITECTURA/FICHA_TECNICA_V5CR_DATOS.json", encoding="utf-8"))
table(doc, ["Concepto", "Valor"], [["Identificador del modelo final", fd["modelo"]], ["SHA-256 del checkpoint (.pt)", fd["sha256_checkpoint"]]] + [[f"SHA-256 de {k.replace(fd['modelo'], '…')}", v] for k, v in fd["hashes_archivos"].items() if not k.endswith(".pt")] +
      [["Modelo preliminar activo (respaldo)", "gait_deep_v4exp_M1_BN_recalibrated_candidate_v1 — SHA-256 7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d"], ["Parámetros entrenables", "17 788 (preliminar: 17 860)"], ["Temperatura / época", f"T = {fd['temperatura']}; E* = {fd['epoca_E_star']}"], ["Nota", "Los pesos y el mapa de etiquetas coinciden byte a byte con el checkpoint original; la copia desplegada difiere solo en dos archivos de metadatos (estado y columnas del escalador)."]],
      widths=[5.5, 11], caption="Identificación técnica y hashes del modelo", size=8, subst=False)
heading(doc, "14.2 Carpetas históricas consultadas", 2)
fu = read_md("13_FUENTES_Y_TRAZABILIDAD/FUENTES_Y_DISCREPANCIAS.md")
md_to_docx(doc, md_section(fu, "## 1."), base_level=3, subst=False, size=8.5)
md_to_docx(doc, md_section(fu, "## 2."), base_level=3, subst=False, size=9)
heading(doc, "14.3 Discrepancias entre documentos y su resolución", 2)
md_to_docx(doc, md_section(fu, "## 3."), base_level=3, subst=False, size=8)
heading(doc, "14.4 Información no localizable", 2)
md_to_docx(doc, md_section(fu, "## 4."), base_level=3, subst=False, size=9)
heading(doc, "14.5 Archivos originales clave y su SHA-256", 2)
man = (PKG / "13_FUENTES_Y_TRAZABILIDAD/MANIFIESTO_ARCHIVOS_SHA256.txt").read_text(encoding="utf-8").split("# Artefactos pesados o externos al paquete")[1].splitlines()[1:]
rows = [[ln.split("  ", 1)[1].replace("../../", ""), ln.split("  ", 1)[0]] for ln in man if "  " in ln and ln.strip()]
table(doc, ["Archivo (relativo a la raíz del repositorio)", "SHA-256"], rows, widths=[9, 8], caption="Artefactos originales referenciados y sus hashes (no se copian)", size=7.5, subst=False)
heading(doc, "14.6 Pendientes y evidencias faltantes", 2)
pdn = read_md("14_AUDITORIA_FINAL/PENDIENTES_Y_EVIDENCIAS_FALTANTES.md")
md_to_docx(doc, pdn.split("\n", 1)[1], base_level=3, subst=True, size=8.5)
heading(doc, "14.7 Matriz de trazabilidad condensada", 2)
set_orientation(doc, True)
tr = csv_rows("13_FUENTES_Y_TRAZABILIDAD/MATRIZ_TRAZABILIDAD_TESIS.csv")
table(doc, ["Capítulo", "Apartado", "Dato nuevo / cambio", "Fuente del repositorio", "Estado de verificación"], [[r["Capitulo"], r["Apartado"], r["Dato_nuevo"] or r["Cambio_necesario"], r["Fuente_del_repositorio"], r["Estado_de_verificacion"]] for r in tr], widths=[2, 3.5, 8, 9, 6], caption="Matriz de trazabilidad: cada cifra, figura y prueba con su fuente", size=7, subst=False)

# =============================================================================== APÉNDICE A
heading(doc, "Apéndice A. Inventario de los 117 videos del dataset (para el Apéndice 8)", 1)
para(doc, "Sin rutas ni datos personales. «Grupo técnico» es un identificador de agrupación, no una persona verificada; «provisional» indica que la fuente no identifica a la persona. Ninguna etiqueta cuenta con validación clínica individual.", subst=False, size=9)
mf = csv_rows("03_DATASET_Y_METODOLOGIA/MANIFIESTO_TRAZABILIDAD_117_VIDEOS.csv")
table(doc, ["Índice", "ID del video", "Clase registrada", "Grupo técnico", "Estado del grupo", "Fuente de grabación", "Orientación", "Vista", "Cámara", "Duración (s)", "fps", "Resolución"],
      [[r["indice_en_OOF"], r["id_video"], CLN.get(r["clase_registrada"], r["clase_registrada"]), r["grupo_tecnico_de_sujeto"], "provisional" if r["estado_del_grupo"] == "provisional" else "registrado", r["fuente_de_grabacion"], r["orientacion"], r["vista"], r["estilo_de_camara"], num(r["duracion_s"]), num(r["fps"]), r["resolucion"]] for r in mf],
      widths=[1, 2.8, 2.4, 3, 1.8, 4, 1.8, 2.4, 3, 1.6, 1.1, 1.8], caption="Inventario de los 117 videos (trazabilidad anonimizada)", size=7, subst=False)

# =============================================================================== guardado
doc.core_properties.title = "Dossier completo para Claude en Word — actualización de la tesis"
doc.core_properties.author = "Elaboración propia (2026)"
doc.core_properties.subject = "Documento auxiliar de consulta (no sustituye a la tesis)"
doc.save(str(OUT))
print("DOCX guardado:", OUT, round(OUT.stat().st_size / 1e6, 1), "MB; figuras:", len(L.REG_FIG), "; tablas:", len(L.REG_TAB))
