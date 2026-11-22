"""Compila el inventario de baterías de pruebas REALMENTE ejecutadas leyendo sus archivos de evidencia (conteos y fechas tomados de los archivos).
Una batería ejecutada varias veces se cuenta UNA vez (se indica en cuántas evidencias aparece). No suma las mismas comprobaciones de informes distintos."""
import csv
import json
import os
import re
import time
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
D = PKG.parents[0]


ORIG = {
    "PAQUETE_FINAL_TESIS_V5CR_2026-11-20/08_PRUEBAS_DEL_SISTEMA/evidencias/navegador_reproductor_sin_aviso_23_de_23.json": "../tmp/player/out/result_full_mov_sinaviso.json",
    "PAQUETE_FINAL_TESIS_V5CR_2026-11-20/08_PRUEBAS_DEL_SISTEMA/evidencias/navegador_descarga_pdf_boton_real_8_de_8.json": "../tmp/report/out/result_despues.json",
    "correccion_inferencia_v5cr_2026-11-19/LOG_DEV_HABITUAL_FALLO_ORIGINAL.log": "../.next/dev/logs/next-development.log",
}  # fecha de la ejecución original (los archivos del paquete son copias)


def mt(p):
    q = D / ORIG.get(p, p)
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(q)))


def jl(p):
    return json.load(open(D / p, encoding="utf-8-sig"))


def checks(p):
    c = jl(p)["checks"]
    return len(c), sum(1 for x in c if x.get("passed")), sum(1 for x in c if not x.get("passed"))


def lst(p):
    c = jl(p)
    return len(c), sum(1 for x in c if x.get("resultado") == "PASS"), sum(1 for x in c if x.get("resultado") not in ("PASS", "DEMOSTRACION_V4"))


def logc(p):
    t = open(D / p, encoding="utf-8", errors="ignore").read()
    return len(re.findall(r"^PASS|^FAIL", t, re.M)), len(re.findall(r"^PASS", t, re.M)), len(re.findall(r"^FAIL", t, re.M))


AISL = "Entorno aislado: PostgreSQL técnico (contenedor, puerto 55432), cuentas @example.invalid, Cloudinary desactivado"
rows = []


def add(n, tipo, fin, ent, ev, fecha, tot, ok, fail, noej, lim, rep=""):
    rows.append([n, tipo, fin, ent, fecha, tot, ok, fail, noej, ev, lim, rep])


F3 = "mejora_modelo_v5_experimental_2026-11-19/resultados/fase3_pruebas.json"
t, o, f = lst(F3)
add("Pruebas numéricas del preprocesamiento V5 (espejo, velocidades, invariancias, ventana, NaN)", "unitaria / numérica", "Verificar el preprocesamiento antes de entrenar; incluye demostraciones de defectos de V4", "Python local; ventanas reales del dataset y señales sintéticas SOLO para verificar código", F3, mt(F3), t, o, f, 0,
    f"De las {t} filas, {o} son pruebas de V5 y {t - o} son demostraciones de defectos de V4 (no son pruebas aprobadas de V5). Corresponde a V5-P; V5-CR reutiliza ese preprocesamiento")
FC = "optimizacion_final_v5_2026-11-19/resultados/fase8_pruebas_c.json"
t, o, f = lst(FC)
add("Pruebas numéricas V5-C (33 características, invariancia a cámara que sigue, aspecto, zoom, 633 ventanas reales)", "unitaria / numérica", "Verificar la invariancia a la traslación global", "Python local; ventanas reales", FC, mt(FC), t, o, f, 0, "V5-C es el antecesor directo de V5-CR; la interpolación relativa a la cadera se prueba en la fila siguiente")
FR = "optimizacion_final_v5_2026-11-19/resultados/fase8_prueba_cr.json"
c = jl(FR)
add("Prueba numérica V5-CR sobre 633 ventanas reales (fuga de traslación por interpolación)", "numérica", "Criterio 1 de la Adenda 1: 0 ventanas cambian con cámara que sigue; 137/137 ventanas sin enmascarados idénticas a V5-C", "Python local", FR, mt(FR), 1, int(c["criterio_1_cumple"]), int(not c["criterio_1_cumple"]), 0,
    f"{c['ventanas']} ventanas; ventanas con diferencia: {c['ventanas_con_diferencia_bajo_camara_que_sigue(>1e-6)']}; diferencia máxima de secuencia {c['max_dif_secuencia']:.1e}. Es un criterio único, no 633 pruebas")
FB = "optimizacion_final_v5_2026-11-19/resultados/fase4_robustez_v5CR.json"
add("Análisis de robustez/dependencia sobre los 25 modelos de validación congelados de V5-CR", "análisis experimental", "Medir el cambio de F1 macro ante ablaciones y perturbaciones", "Python local sobre modelos y OOF guardados", FB, mt(FB), len(jl(FB)["pruebas"]), "n/a", "n/a", 0,
    "No es una batería aprobado/fallido: informa ΔF1 con IC95 por sujeto (ver 04_METRICAS_Y_COMPARACIONES/ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv)")
TD = "correccion_inferencia_v5cr_2026-11-19/test_deep.log"
t, o, f = logc(TD)
add("Python de despliegue (test_v5cr_deployment.py --real-videos): artefactos, hashes, orden, escalador, imputación, ventanas, logits/probabilidades frente al evaluador (117/117 videos), videos reales de las 4 clases y casos negativos", "unitaria + integración",
    "Comprobar que el predictor desplegado reproduce al evaluador y rechaza entradas inválidas", "Python local (.venv311)", TD + "; integracion_v5cr_2026-11-19/PRUEBAS_PYTHON.json", mt(TD), t, o, f, 0,
    "Misma batería en 2 evidencias (integración y corrección de inferencia); se cuenta una vez. Los 4 videos reales no son pacientes nuevos ni evaluación independiente", "2")
TS = "integracion_v5cr_2026-11-19/PRUEBAS_TYPESCRIPT.json"
t, o, f = checks(TS)
add("TypeScript/tsx de presentación (test-v5cr-presentation.ts): selección de modelo, cuatro probabilidades, pose insuficiente, identidad histórica V4", "unitaria", "Comprobar que la presentación usa cantidades reales y conserva versiones históricas", "Node/tsx local", TS, mt(TS), t, o, f, 0,
    "Se volvió a ejecutar el 2026-11-19 en trabajos posteriores con el mismo resultado de 12 aprobadas")
TE = "pdf_informe_unificado_2026-11-19/e2e/PRUEBAS_E2E.json"
t, o, f = checks(TE)
add("HTTP extremo a extremo (test-v5cr-e2e.mjs): login, carga, pose, inferencia V5-CR, PostgreSQL, historial, informe, PDF, administración, permisos, entradas negativas", "integración / E2E HTTP", "Verificar el flujo completo y los controles de acceso", AISL,
    TE + " (última); también revision_defensa…/e2e, correccion_inferencia…/e2e, correccion_reproductor…/e2e_http, historial_informes_botones…/e2e", mt(TE), t, o, f, 0,
    "La batería creció de 18 a 20 y a 21 comprobaciones; se ejecutó al menos 6 veces con resultado final 21/21 (se cuenta una sola vez). NO es una prueba sobre el servidor habitual ni con Cloudinary", "≥6")
TH = "recuperacion_pdf_historicos_2026-11-19/PRUEBAS_HTTP_AISLADAS.json"
t, o, f = checks(TH)
add("HTTP aislado de PDF e historial (test-historical-pdf-recovery.mjs): 404 explícito de históricos, propiedad, caché antigua byte a byte, PDF nuevo, administración", "integración HTTP / seguridad", "Verificar la gestión de PDF históricos y los controles de propiedad",
    AISL + " (esquema nuevo por ejecución, copia de registros técnicos)", TH, mt(TH), t, o, f, 0, "Ejecutada 4 veces con 22/22 (se cuenta una vez)", "4")
TC = "recuperacion_pdf_historicos_2026-11-19/PRUEBAS_DESCARGA_CLIENTE.json"
t, o, f = checks(TC)
add("Descarga en el cliente (test-historical-pdf-download.ts): rechaza JSON/HTML/vacíos como PDF", "unitaria", "Garantizar que un error nunca se guarde como PDF", "Node/tsx local", TC, mt(TC), t, o, f, 0, "")
TI = "integracion_v5cr_2026-11-19/AUDITORIA_INTEGRIDAD.json"
t, o, f = checks(TI)
add("Auditoría de integridad de la integración (conservación de artefactos y metadatos)", "auditoría", "Comprobar que V4/V5 y sus artefactos no se alteraron", "Local", TI, mt(TI), t, o, f, 0,
    "Verifica los artefactos de modelos contra el manifiesto previo (repetido con verify-defense-preservation.mjs: 26/26 sin cambios)")
TP = "revision_defensa_2026-11-19/PRUEBAS_PRESENTACION_PDF.json"
t, o, f = checks(TP)
add("Presentación del PDF anterior (redondeo, identificadores, ausencia de texto redundante)", "unitaria", "Verificar el PDF de texto previo", "Node/tsx local", TP, mt(TP), t, o, f, 0,
    "OBSOLETA para el diseño: el generador de PDF se reemplazó después por el diseño unificado (reportPdf.ts); no usar como prueba del PDF final")
TN = "historial_informes_botones_2026-11-19/navegador_resultado.json"
t, o, f = checks(TN)
add("Navegador (Chrome/CDP): historial con «Ver informe»/«Descargar PDF», registro sin PDF, filtro, clic real, propiedad", "E2E visual / navegador", "Comprobar los botones del historial", AISL,
    TN + "; 08…/evidencias/navegador_historial_botones_17_de_17.json", mt(TN), t, o, f, 0, "Chrome sin ventana: no tiene visor de PDF; se comprobó que la pestaña recibe el documento, no su pintado")
TR = "PAQUETE_FINAL_TESIS_V5CR_2026-11-20/08_PRUEBAS_DEL_SISTEMA/evidencias/navegador_reproductor_sin_aviso_23_de_23.json"
t, o, f = checks(TR)
add("Navegador (Chrome/CDP): reproductor durante el análisis (repetir, pausar, buscar, recuperación MEDIA_ERR_DECODE, Reintentar, fin del análisis, resultado)", "E2E visual / navegador", "Comprobar la independencia entre reproductor y análisis", AISL,
    "08…/evidencias/navegador_reproductor_sin_aviso_23_de_23.json; correccion_reproductor_video_2026-11-19/navegador/", mt(TR), t, o, f, 0,
    "Ejecutada con 3 videos (MOV horizontal, mp4 vertical, mp4 horizontal; 22/22 cada uno antes de retirar el aviso visual y 23/23 con el MOV después). Una ejecución previa a la corrección (7 de 8) reprodujo el defecto y se conserva. No se cuentan los 3 videos como baterías distintas")
TD2 = "PAQUETE_FINAL_TESIS_V5CR_2026-11-20/08_PRUEBAS_DEL_SISTEMA/evidencias/navegador_descarga_pdf_boton_real_8_de_8.json"
t, o, f = checks(TD2)
add("Navegador (Chrome/CDP): flujo hasta el informe y descarga del PDF con el botón real «Descargar PDF»", "E2E visual / navegador", "Comprobar la descarga del PDF con diseño unificado", AISL,
    "08…/evidencias/navegador_descarga_pdf_boton_real_8_de_8.json; pdf_informe_unificado_2026-11-19/", mt(TD2), t, o, f, 0, "Contenido del PDF contrastado contra la pantalla y las probabilidades guardadas por script (no es una revisión visual manual completa)")
add("Comprobación de solo lectura del entorno habitual: 79 informes históricos devuelven 404 explícito y la base habitual no se alteró", "lectura / regresión", "Verificar la indisponibilidad correcta de los PDF históricos sin escribir en la base habitual", "Base habitual (solo GET y consultas de lectura)",
    "recuperacion_pdf_historicos_2026-11-19/HTTP_79_INFORMES.json; CONSERVACION_BD_HABITUAL.json", mt("recuperacion_pdf_historicos_2026-11-19/HTTP_79_INFORMES.json"), 79, 79, 0, 0,
    "La integridad se reverificó tras las pruebas manuales del propietario: aparecen 2 informes y 4 análisis nuevos creados por el propietario; los 79 informes y 169 análisis históricos permanecen")
add("TypeScript (tsc --noEmit), ESLint y Next.js build", "calidad estática / compilación", "Regresión estática", "Node local",
    "EXIT_TYPESCRIPT/EXIT_LINT/EXIT_BUILD.json en integracion_v5cr…, recuperacion_pdf_historicos…, revision_defensa… (código 0); últimas ejecuciones descritas en los INFORMES de pdf_informe_unificado e historial_informes_botones", mt("integracion_v5cr_2026-11-19/EXIT_BUILD.json"), 3, 3, 0, 0,
    "tsc 0 errores; ESLint 0 errores y 3 avisos en scripts de prueba; build correcto con un aviso conocido de trazado de archivos. Las últimas ejecuciones no guardan un EXIT_*.json propio")
add("Pruebas manuales del propietario en la aplicación habitual (análisis V5-CR completo, reproductor, informes)", "manual (propietario)", "Verificación manual del flujo real", "Aplicación habitual (base habitual)",
    "correccion_inferencia_v5cr_2026-11-19/LOG_DEV_HABITUAL_FALLO_ORIGINAL.log (registro del servidor de desarrollo)", mt("correccion_inferencia_v5cr_2026-11-19/LOG_DEV_HABITUAL_FALLO_ORIGINAL.log"), "n/d", "n/d", "n/d", "n/d",
    "El registro conservado muestra, entre otros eventos, un análisis con gait_deep_v5exp_V5CR_7e9ed60965fe. Son pruebas manuales del propietario, sin capturas ni conteos formales; no se suman a las automatizadas")
add("test_deep_pipeline.py (V4 / pipeline anterior)", "unitaria", "Pruebas del pipeline V4 original", "Python local", "scripts/video_training/deep/test_deep_pipeline.py (script test:deep:legacy)", "", "n/d", "n/d", "n/d", "no ejecutada en esta serie", "No se reejecutó; no aplica al modelo V5-CR")
H = ["bateria", "tipo", "finalidad", "entorno", "fecha_de_la_evidencia", "total", "aprobadas", "fallidas", "no_ejecutadas", "evidencia", "limitaciones", "ejecuciones_registradas"]
with open(PKG / "08_PRUEBAS_DEL_SISTEMA" / "PRUEBAS_EJECUTADAS_RESUMEN.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(H)
    w.writerows(rows)
print(len(rows), "baterías")
