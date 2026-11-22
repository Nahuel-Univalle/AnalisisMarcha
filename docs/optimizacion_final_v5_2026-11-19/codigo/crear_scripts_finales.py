"""Genera fase8_robustez_cr.py y fase8_comparar_final.py (con V5-CR) a partir de los scripts de V5-C, sin tocar los originales."""
from pathlib import Path
H = Path(__file__).resolve().parent
r = (H / "fase8_robustez_c.py").read_text(encoding="utf-8")
r = r.replace('"--version", "v5C"', '"--version", "v5CR"').replace('"v5C"]', '"v5C", "v5CR"]').replace('choices=["v4", "v5P", "v5S", "v5C"]', 'choices=["v4", "v5P", "v5S", "v5C", "v5CR"]')
r = r.replace("dataset_v5c_bank", "dataset_v5cr_bank").replace('tag = "V5C"', 'tag = "V5CR"').replace("import v5c_preproc as CP", "import v5cr_preproc as CP")
assert "v5cr_preproc as CP" in r and "dataset_v5cr_bank" in r and 'tag = "V5CR"' in r
(H / "fase8_robustez_cr.py").write_text(r, encoding="utf-8")
c = (H / "fase8_comparar.py").read_text(encoding="utf-8")
c = c.replace('pc = np.load(NEW / "oof_V5C.npz")', 'pc = np.load(NEW / "oof_V5C.npz"); pr = np.load(NEW / "oof_V5CR.npz")')
c = c.replace('"V5-C": np.stack([pc[f"p{s}"] for s in SEEDS])}\nCAL', '"V5-C": np.stack([pc[f"p{s}"] for s in SEEDS]), "V5-CR": np.stack([pr[f"p{s}"] for s in SEEDS])}\nCAL')
c = c.replace('"V5-C": np.stack([pc[f"c{s}"] for s in SEEDS])}', '"V5-C": np.stack([pc[f"c{s}"] for s in SEEDS]), "V5-CR": np.stack([pr[f"c{s}"] for s in SEEDS])}')
c = c.replace('(("V5-C", "V5-P"), ("V5-C", "V4 BN (activo)"), ("V5-C", "V4 base"), ("V5-P", "V4 BN (activo)"))',
              '(("V5-C", "V5-P"), ("V5-C", "V4 BN (activo)"), ("V5-C", "V4 base"), ("V5-P", "V4 BN (activo)"), ("V5-CR", "V5-C"), ("V5-CR", "V5-P"), ("V5-CR", "V4 BN (activo)"), ("V5-CR", "V4 base"))')
extra = '''
robR = json.load(open(NEW / "fase4_robustez_v5CR.json", encoding="utf-8"))
trR = [x for x in robR["pruebas"] if x["prueba"].startswith("camara que sigue a la persona (100")][0]
dRC = OUT["diferencias"]["V5-CR - V5-C"]; pR = json.load(open(NEW / "fase8_prueba_cr.json", encoding="utf-8"))
critR = {"1_prueba_numerica_633_ventanas": {"ventanas_con_fuga": pR["ventanas_con_diferencia_bajo_camara_que_sigue(>1e-6)"], "cumple": bool(pR["criterio_1_cumple"])},
         "2_robustez_camara_sigue>=-0.05": {"valor": trR["delta_macro_f1"], "IC95": trR["IC95_delta_(bootstrap por sujeto)"], "cumple": bool(trR["delta_macro_f1"] >= -0.05)},
         "3a_lim_inf_IC(V5CR-V5C)_macroF1>-0.05": {"valor": dRC["mf1"]["lo"], "cumple": bool(dRC["mf1"]["lo"] > -0.05)},
         "3b_ninguna_clase_pierde>0.10_vs_V5C": {"dF1_por_clase": dRC["F"]["obs"], "cumple": bool(min(dRC["F"]["obs"]) >= -0.10)}}
critR["TODOS_LOS_CRITERIOS"] = bool(all(v["cumple"] for v in critR.values() if isinstance(v, dict)))
OUT["criterios_adenda1_V5CR"] = critR; print(json.dumps(critR, ensure_ascii=False, indent=1))
(NEW / "comparacion_final.json").write_text'''
c = c.replace('(NEW / "comparacion_final.json").write_text', extra, 1)
c = c.replace('(NEW / "comparacion_final.json").write_text(json.dumps(OUT', '(NEW / "comparacion_final_con_CR.json").write_text(json.dumps(OUT') if c.count('comparacion_final.json') > 1 else c
# figura con V5-CR
c = c.replace('vals["V5-C"] = [r["delta_macro_f1"] for r in rob["pruebas"] if r["prueba"].startswith("camara que sigue")]',
              'vals["V5-C"] = [r["delta_macro_f1"] for r in rob["pruebas"] if r["prueba"].startswith("camara que sigue")]\nvals["V5-CR"] = [r["delta_macro_f1"] for r in robR["pruebas"] if r["prueba"].startswith("camara que sigue")]')
c = c.replace('(("V4 base", "#6b7280"), ("V5-P", "#c2410c"), ("V5-C", "#0f766e"))', '(("V4 base", "#6b7280"), ("V5-P", "#c2410c"), ("V5-C", "#0f766e"), ("V5-CR", "#1d4ed8"))')
c = c.replace("ax.bar(xs + (i - 1) * 0.26, vals[nm], 0.26, color=c, label=nm)", "ax.bar(xs + (i - 1.5) * 0.2, vals[nm], 0.2, color=c, label=nm)")
c = c.replace("fase8_camara_que_sigue.png", "fase8_camara_que_sigue_con_CR.png").replace("fig8_camara_que_sigue.png", "fig9_camara_que_sigue_con_CR.png")
(H / "fase8_comparar_final.py").write_text(c, encoding="utf-8")
print("ok")
