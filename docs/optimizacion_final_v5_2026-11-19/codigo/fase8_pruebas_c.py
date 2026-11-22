"""Pruebas numericas de V5-C (antes de entrenar). Reutiliza el generador sintetico de las pruebas V5
(solo verificacion matematica; NO son datos de entrenamiento)."""
import json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19" / "codigo"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(OLD))
import v5_preproc as V
import v5c_preproc as C
from data_v5 import load_videos
R = []


def chk(n, ok, d=""):
    R.append({"prueba": n, "resultado": "PASS" if ok else "FAIL", "detalle": str(d)})
    print(("PASS " if ok else "FAIL ") + n, "|", d, flush=True)


src = (OLD / "fase3_pruebas_unitarias.py").read_text(encoding="utf-8")
ns = {"math": math, "np": np, "V": V}
exec(compile(src[src.index("def synth("):src.index("base = synth()")], "gen", "exec"), ns)
synth, mirror_frames, shift_frames = ns["synth"], ns["mirror_frames"], ns["shift_frames"]
A = 16 / 9
base = synth()
s5, f5, _ = V.window_inputs(base, 0.0, A)
sC, fC, _ = C.window_inputs_C(base, 0.0, A)
chk("secuencia V5-C identica a V5-P", float(np.abs(s5 - sC).max()) == 0.0)
chk("33 caracteristicas y nombres coherentes", len(fC) == 33 == len(C.FEATURES_C))
keepers = [n for n in C.FEATURES_C if n not in ("body_motion_mean", "body_motion_std", "motion_smoothness", "gait_variability")]
same = max(abs(fC[C.FEATURES_C.index(n)] - f5[V.FEATURES_V5.index(n)]) for n in keepers)
chk("caracteristicas no redefinidas identicas a V5-P", same < 1e-6, same)


def track(frames, frac=1.0):
    h = lambda f: (f["landmarks"]["LEFT_HIP"]["x"] + f["landmarks"]["RIGHT_HIP"]["x"]) / 2
    h0 = h(frames[0])
    return [{**f, "landmarks": {n: {**p, "x": p["x"] - frac * (h(f) - h0)} for n, p in f["landmarks"].items()}} for f in frames]


for frac in (0.5, 1.0):
    _, ft, _ = C.window_inputs_C(track(base, frac), 0.0, A)
    d = float(np.nanmax(np.abs(ft - fC)))
    chk(f"V5-C invariante a camara que sigue (compensacion {int(frac * 100)} %)", d < 1e-5, d)
_, ft5, _ = V.window_inputs(track(base, 1.0), 0.0, A)
chk("DEMOSTRACION: V5-P NO es invariante (umbral inicial 0.05 era arbitrario y demasiado alto para la velocidad sintetica; se usa >1e-3 = cualquier cambio real)", float(np.abs(ft5 - f5).max()) > 1e-3, round(float(np.abs(ft5 - f5).max()), 3))
mf = mirror_frames(base)
_, fm, _ = C.window_inputs_C(mf, 0.0, A)
names = C.FEATURES_C
perm = list(range(33))
for l, r in V._FLR:
    if l in names and r in names:
        i, j = names.index(l), names.index(r)
        perm[i], perm[j] = perm[j], perm[i]
chk("espejo: caracteristicas de landmarks reflejados == permutacion L/R de las originales", float(np.nanmax(np.abs(fm - fC[perm]))) < 1e-5)
_, fz, _ = C.window_inputs_C(shift_frames(base, sx=1.3, sy=1.3), 0.0, A)
chk("invariante al zoom", float(np.nanmax(np.abs(fz - fC))) < 1e-5)
_, fa, _ = C.window_inputs_C(synth(aspect=9 / 16), 0.0, 9 / 16)
chk("invariante a la relacion de aspecto", float(np.nanmax(np.abs(fa - fC))) < 1e-5)
_, f0, _ = C.window_inputs_C(synth(leg_amp_deg=0, arm_amp_deg=0, speed=0.5), 0.0, A)
chk("persona rigida (sin piernas ni brazos): body_motion_mean ~ 0 aunque avance", f0[names.index("body_motion_mean")] < 0.02, round(float(f0[names.index("body_motion_mean")]), 4))
bad = n = 0
for v in load_videos():
    for s in np.arange(0, max(v["w_eff"] - V.SPAN_S, 0) + 1e-9, 0.4):
        r = C.window_inputs_C(v["frames"], v["t0"] + s, v["aspect"])
        if r is None:
            continue
        n += 1
        bad += int((not np.isfinite(r[0]).all()) or np.isinf(r[1]).any())
chk(f"sin NaN/inf invalidos en {n} ventanas reales", bad == 0, bad)
ok = all(r["resultado"] == "PASS" for r in R)
chk("conjunto completo sin FAIL", ok)
(HERE.parent / "resultados" / "fase8_pruebas_c.json").write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding="utf-8")
sys.exit(0 if ok else 1)
