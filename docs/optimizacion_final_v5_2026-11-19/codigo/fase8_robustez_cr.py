"""Bateria de robustez/dependencia (la MISMA de V4 y V5-P) aplicada a V5-C con modelos congelados de sus 25 folds, mas la prueba de camara que sigue.
Ejecuta el codigo original fase4_dependencia_movimiento.py con parches minimos de rutas/version (el original no se modifica)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
OLDDIR = HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"
src = (OLDDIR / "fase4_dependencia_movimiento.py").read_text(encoding="utf-8")


def rep(old, new, cnt=1):
    global src
    assert src.count(old) >= 1, old
    src = src.replace(old, new)


sys.argv = [sys.argv[0], "--version", "v5CR"]
rep('choices=["v4", "v5P", "v5S"]', 'choices=["v4", "v5P", "v5S", "v5C", "v5CR"]')
rep('zb = np.load(OUT / "dataset_v5_bank.npz", allow_pickle=False)\n    keep = list(range(36)) if a.version == "v5P" else V.S_KEEP_IDX',
    'zb = np.load(NEW / "dataset_v5cr_bank.npz", allow_pickle=False)\n    keep = list(range(33))')
rep('C.names = [V.FEATURES_V5[i] for i in keep]; C.groups = V.GROUPS', 'C.names = [str(n) for n in zb["feature_names"]]; C.groups = V.GROUPS')
rep('tag = "V5P" if a.version == "v5P" else "V5S"', 'tag = "V5CR"')
rep('OUT / f"modelos_cv_{tag}"', 'NEW / f"modelos_cv_{tag}"')
rep("TC.set_feature_columns(keep)", "TC.FPERM = np.asarray(_fperm(C.names))")
rep('pz = np.load(OUT / f"oof_{tag}.npz")', 'pz = np.load(NEW / f"oof_{tag}.npz")')
rep("r = V.window_inputs(fr, float(C.t0[w]), v[\"aspect\"] / aspect_k)", "r = CP.window_inputs_C(fr, float(C.t0[w]), v[\"aspect\"] / aspect_k)")
rep("Xs[w] = r[0]; Xf[w] = r[1][keep_idx]", "Xs[w] = r[0]; Xf[w] = r[1]")
rep('(OUT / f"fase4_robustez_{a.version}.json")', '(NEW / f"fase4_robustez_{a.version}.json")')
track = '''
def f_track(frac):
    def fn(fr, rng):
        hx = lambda f: (f["landmarks"]["LEFT_HIP"]["x"] + f["landmarks"]["RIGHT_HIP"]["x"]) / 2
        h0 = hx(fr[0]); return [{**f, "landmarks": {n: {**p, "x": p["x"] - frac * (hx(f) - h0)} for n, p in f["landmarks"].items()}} for f in fr]
    return fn
for name, frac in (("camara que sigue a la persona (50 % del avance horizontal compensado)", 0.5), ("camara que sigue a la persona (100 %: la cadera no se desplaza en la imagen)", 1.0)):
    xs, xf = rb(f_track(frac), 1.0); record(name, "grabacion", run(Xs=xs, Xf=xf)[0], "camara en mano / acompanando")
RES["pruebas"] = rows'''
rep('RES["pruebas"] = rows', track)
pre = '''
import v5cr_preproc as CP
NEW = Path(r"%s")
def _fperm(names):
    p = list(range(len(names)))
    for l, r in V._FLR:
        if l in names and r in names:
            i, j = names.index(l), names.index(r); p[i], p[j] = p[j], p[i]
    return p
''' % str(HERE.parent / "resultados")
rep("OUT = HERE.parent / \"resultados\"", "OUT = HERE.parent / \"resultados\"" + pre)
sys.path.insert(0, str(OLDDIR)); sys.path.insert(0, str(HERE))
g = {"__name__": "__main__", "__file__": str(OLDDIR / "fase4_dependencia_movimiento.py")}
exec(compile(src, "fase4_parcheado", "exec"), g)
