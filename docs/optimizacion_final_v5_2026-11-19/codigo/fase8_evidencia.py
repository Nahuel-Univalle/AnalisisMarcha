"""Optimizacion final -- EVIDENCIA previa (modelos congelados; no se entrena ni se escribe en V4/V5-P).
Uso: python fase8_evidencia.py --version v4|v5P   (reutiliza la maquinaria de ../mejora_modelo_v5_experimental_2026-11-19/codigo/fase4_dependencia_movimiento.py)
Pruebas: (E) camara que SIGUE a la persona (se anula el desplazamiento horizontal global), parcial (50 %) y total; (F) consistencia entre ventanas
de un mismo video; (D) direccion de la mala calibracion."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"
src = (OLD / "fase4_dependencia_movimiento.py").read_text(encoding="utf-8")
head = src[:src.index("# 1. ablacion de ramas")]
defs = src[src.index("# 5. perturbaciones de GRABACION"):src.index("for name, fn, k, note in [")]
sys.path.insert(0, str(OLD))
__file__ = str(OLD / "fase4_dependencia_movimiento.py")  # para que HERE/OUT de la cabecera apunten al paquete V5
exec(compile(head, "fase4_head", "exec"))
exec(compile(defs, "fase4_defs", "exec"))
NEW = Path(HERE).parent / "resultados"
rows.clear()

def f_track(frac):
    def fn(fr, rng):
        def hx(f):
            lm = f["landmarks"]; return (lm["LEFT_HIP"]["x"] + lm["RIGHT_HIP"]["x"]) / 2
        h0 = hx(fr[0]); return [{**f, "landmarks": {n: {**p, "x": p["x"] - frac * (hx(f) - h0)} for n, p in f["landmarks"].items()}} for f in fr]
    return fn
for name, frac in (("camara que sigue a la persona (50 % del avance horizontal compensado)", 0.5), ("camara que sigue a la persona (100 %: la cadera no se desplaza en la imagen)", 1.0)):
    xs, xf = rb(f_track(frac), 1.0); record(name, "grabacion", run(Xs=xs, Xf=xf)[0], "camara en mano / acompanando")
out = {"version": a.version, "linea_base": RES["linea_base"], "pruebas": rows}
# consistencia entre ventanas (solo V5)
if a.version != "v4":
    import numpy as np
    stats = {"ventana_acc": [], "video_5v": [], "video_todas": [], "video_voto": []}
    dis = []
    for p in SEEDS:
        for k, (tr, te) in enumerate(FOLDS[p], start=1):
            sc = SCALERS[(p, k)]; m = MODELS[(p, k)]
            for i in te:
                allw = np.where(zb["vid"] == i)[0]
                with torch.no_grad():
                    lg = m(torch.from_numpy(C.Xs[allw]).float(), torch.from_numpy(sc.transform(C.Xf[allw])).float()).numpy()
                pw = lg.argmax(1); stats["ventana_acc"].append((pw == y[i]).mean())
                stats["video_todas"].append(float(lg.mean(0).argmax() == y[i])); stats["video_5v"].append(float(logits_for(m, sc, [i], C.Xs, C.Xf)[0].argmax() == y[i]))
                stats["video_voto"].append(float(np.bincount(pw, minlength=4).argmax() == y[i]))
                dis.append(float((pw != np.bincount(pw, minlength=4).argmax()).mean()))
    out["consistencia_ventanas"] = {"exactitud_por_ventana": round(float(np.mean(stats["ventana_acc"])), 4), "exactitud_video_5_ventanas (usada)": round(float(np.mean(stats["video_5v"])), 4),
        "exactitud_video_todas_las_ventanas": round(float(np.mean(stats["video_todas"])), 4), "exactitud_video_voto_mayoritario": round(float(np.mean(stats["video_voto"])), 4),
        "fraccion_media_de_ventanas_discrepantes_del_voto": round(float(np.mean(dis)), 4), "videos_con_ventanas_discrepantes": round(float(np.mean(np.array(dis) > 0)), 4)}
    c = np.load(NEW.parent.parent / "mejora_modelo_v5_experimental_2026-11-19" / "resultados" / f"oof_{tag}.npz")
else:
    c = None
# calibracion: confianza media vs exactitud
pz = np.load(OLD.parent.parent.parent / "outputs" / "dataset_v4_4class" / "step18_bn" / "oof_probabilities.npz") if a.version == "v4" else None
import numpy as np
if a.version == "v4": PP = [pz[f"A_{s}"] for s in SEEDS]
else: PP = [c[f"p{s}"] for s in SEEDS]; PC = [c[f"c{s}"] for s in SEEDS]
out["calibracion"] = {"confianza_media_cruda": round(float(np.mean([P.max(1).mean() for P in PP])), 4), "exactitud": round(float(np.mean([(P.argmax(1) == y).mean() for P in PP])), 4)}
if a.version != "v4": out["calibracion"]["confianza_media_calibrada"] = round(float(np.mean([P.max(1).mean() for P in PC])), 4)
(NEW / f"fase8_evidencia_{a.version}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False)[:3000])
