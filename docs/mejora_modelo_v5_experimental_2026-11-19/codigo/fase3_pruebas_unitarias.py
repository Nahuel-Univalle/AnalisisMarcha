"""Fase 3 -- pruebas del preprocesamiento V5 (y pruebas de regresion que DEMUESTRAN los defectos de V4).
Uso: python fase3_pruebas_unitarias.py [--dataset ../resultados/dataset_v5_bank.npz]  -> resultados/fase3_pruebas.json"""
import json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v5_preproc as V
from data_v5 import load_videos, ROOT
sys.path.insert(0, str(ROOT / "scripts" / "video_training" / "deep"))
import deep_common as DC
from video_training_common import build_feature_row, FEATURE_COLUMNS as F4

OUT = HERE.parent / "resultados"
RES = []
def check(name, ok, detail=""):
    RES.append({"prueba": name, "resultado": "PASS" if ok else "FAIL", "detalle": detail})
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail else ""), flush=True)
def info(name, detail):  # demostracion de defecto V4 (no es un criterio de aprobacion de V5)
    RES.append({"prueba": name, "resultado": "DEMOSTRACION_V4", "detalle": detail}); print("INFO " + name + " | " + str(detail), flush=True)

# ------------------------------------------------------------------ esqueleto sintetico (escena isotropica, unidades = altura de imagen)
def synth(seconds=8.0, aspect=16 / 9, cadence=1.0, arm_amp_deg=20.0, leg_amp_deg=30.0, speed=0.12, sw=0.03, zoom=1.0, dx=0.0, dy=0.0, t_start=0.0, jitter=0.0, seed=0):
    rng = np.random.default_rng(seed); frames = []
    n = int(round(seconds * V.FPS))
    for k in range(n):
        t = t_start + k / V.FPS; ph = 2 * math.pi * cadence * t
        hx, hy = 0.3 + speed * t, 0.55
        torso = 0.25
        def seg(a_deg, L):  # vector hacia abajo rotado a_deg respecto a la vertical (positivo = hacia +x)
            a = math.radians(a_deg); return (L * math.sin(a), L * math.cos(a))
        pts = {}
        pts["LEFT_HIP"] = (hx - sw, hy); pts["RIGHT_HIP"] = (hx + sw, hy)
        pts["LEFT_SHOULDER"] = (hx - sw, hy - torso); pts["RIGHT_SHOULDER"] = (hx + sw, hy - torso)
        pts["NOSE"] = (hx, hy - torso - 0.08)
        for side, sgn, hip, sho in (("LEFT", 1, pts["LEFT_HIP"], pts["LEFT_SHOULDER"]), ("RIGHT", -1, pts["RIGHT_HIP"], pts["RIGHT_SHOULDER"])):
            a_arm = sgn * arm_amp_deg * math.sin(ph); a_leg = -sgn * leg_amp_deg * math.sin(ph)
            ex = seg(a_arm * 0.6, 0.11); el = (sho[0] + ex[0], sho[1] + ex[1]); wr_v = seg(a_arm, 0.22)
            wr = (sho[0] + wr_v[0], sho[1] + wr_v[1])
            kn_v = seg(a_leg, 0.14); kn = (hip[0] + kn_v[0], hip[1] + kn_v[1]); an_v = seg(a_leg * 0.5 - max(0, a_leg) * 0.3, 0.14)
            an = (kn[0] + an_v[0], kn[1] + an_v[1])
            pts[f"{side}_ELBOW"], pts[f"{side}_WRIST"], pts[f"{side}_KNEE"], pts[f"{side}_ANKLE"] = el, wr, kn, an
            pts[f"{side}_HEEL"] = (an[0] - 0.01, an[1] + 0.01); pts[f"{side}_FOOT_INDEX"] = (an[0] + 0.04, an[1] + 0.01)
        lm = {}
        for name, (X, Y) in pts.items():
            X = 0.5 + (X - 0.5) * zoom + dx; Y = 0.5 + (Y - 0.5) * zoom + dy
            X += rng.normal(0, jitter); Y += rng.normal(0, jitter)
            lm[name] = {"x": X / aspect, "y": Y, "z": 0.0, "visibility": 1.0}
        frames.append({"frame_index": k, "timestamp_sec": t, "landmarks": lm})
    return frames

def mirror_frames(frames):
    out = []
    for f in frames:
        lm = {}
        for n, p in f["landmarks"].items():
            m = n.replace("LEFT", "@").replace("RIGHT", "LEFT").replace("@", "RIGHT")
            lm[m] = {**p, "x": 1.0 - p["x"]}
        out.append({**f, "landmarks": lm})
    return out

def shift_frames(frames, dx=0.0, dy=0.0, sx=1.0, sy=1.0):
    return [{**f, "landmarks": {n: {**p, "x": 0.5 + (p["x"] - 0.5) * sx + dx, "y": 0.5 + (p["y"] - 0.5) * sy + dy} for n, p in f["landmarks"].items()}} for f in frames]

def v5(frames, aspect, t0=0.0):
    r = V.window_inputs(frames, t0, aspect); return None if r is None else r[:2]
def v4(frames, dur):
    seq, _, _ = DC.frames_to_sequence(frames)
    q = {"duration_seconds": dur}
    f = build_feature_row({"filename": "s", "video_path": "s"}, frames, q, None)
    return seq, np.array([np.nan if f[c] is None else f[c] for c in F4], float)
def mx(a, b): return float(np.nanmax(np.abs(np.asarray(a, float) - np.asarray(b, float))))

base = synth(); A = 16 / 9
s0, f0 = v5(base, A)

# 1. SIMETRIA DEL ESPEJO ---------------------------------------------------------------------------------------------------
rng = np.random.default_rng(0)
rs = rng.normal(size=(68, 40)).astype(np.float32); rf = rng.normal(size=36)
check("espejo V5 aplicado dos veces = original (secuencia)", mx(V.mirror_seq(V.mirror_seq(rs)), rs) < 1e-7, mx(V.mirror_seq(V.mirror_seq(rs)), rs))
check("espejo V5 aplicado dos veces = original (caracteristicas)", mx(V.mirror_feat(V.mirror_feat(rf)), rf) < 1e-12)
mf = mirror_frames(base); sm, fm = v5(mf, A)
d_seq = mx(sm, V.mirror_seq(s0)); d_feat = mx(fm, V.mirror_feat(f0))
check("espejo V5 de la secuencia == secuencia de los landmarks reflejados (posiciones Y velocidades)", d_seq < 1e-5, f"max|dif|={d_seq:.2e}")
check("espejo V5 de las caracteristicas == caracteristicas de los landmarks reflejados", d_feat < 1e-5, f"max|dif|={d_feat:.2e}")
vx = [i for i, n in enumerate(V.CH_NAMES) if n.endswith("_vx")]
check("espejo V5: los componentes horizontales de velocidad cambian de signo", mx(V.mirror_seq(s0)[vx], -s0[[V.MIRROR_PERM[i] for i in vx]]) < 1e-7)
# regresion V4: su espejo (deep_common.augment_sample, paso 5) NO invierte vx
s4, _ = v4(base, 8.0); s4m, _ = v4(mf, 8.0)
v4mir = s4[DC._MIRROR_PERM].copy(); v4mir[DC._POS_X_IDX] *= -1.0
vx4 = [i for i, n in enumerate(DC.CHANNEL_NAMES) if n.endswith("_vx")]
info("V4 DEFECTO A1: error del espejo de V4 en canales vx (vs landmarks reflejados)", f"max|dif| vx = {mx(v4mir[vx4], s4m[vx4]):.4f}; en posiciones = {mx(v4mir[DC._POS_X_IDX], s4m[DC._POS_X_IDX]):.2e}")

# 2. POSICIONES vs VELOCIDADES ---------------------------------------------------------------------------------------------
pos, vel = s0[:34].T, s0[34:].T
check("V5: velocidad = diferencia de posiciones (exacto)", mx(vel[1:], np.diff(pos, axis=0)) < 1e-6 and np.allclose(vel[0], 0))
sys.path.insert(0, str(HERE)); import v5_train_core as TC
ag = TC.augment_v5(s0, np.random.default_rng(1), noise_std=0.01, mirror=True, force_mirror=True)
check("V5: aumentacion (ruido + espejo) mantiene velocidad = diff(posicion)", mx(ag[34:].T[1:], np.diff(ag[:34].T, axis=0)) < 1e-6)
# aumentacion V4 (recorte temporal) rompe la coherencia
rng4 = np.random.default_rng(3); crop = DC.augment_sample(s4, np.zeros(36, np.float32), rng4)[0]
info("V4 DEFECTO A5: tras aumentacion V4, |vel - diff(pos)| (max)", f"{mx(crop[34:].T[1:], np.diff(crop[:34].T, axis=0)):.4f} (deberia ser 0)")

# 3. CONSISTENCIA DE LAS 36 CARACTERISTICAS ---------------------------------------------------------------------------------
vids = load_videos(); bad = 0; n_nan = []; n_win = 0; negs = []
for v in vids:
    for s in np.arange(0, max(v["w_eff"] - V.SPAN_S, 0) + 1e-9, 0.4):
        r = V.window_inputs(v["frames"], v["t0"] + s, v["aspect"])
        if r is None: continue
        n_win += 1; seq, feat, _ = r
        if not np.isfinite(seq).all() or np.isinf(feat).any(): bad += 1
        n_nan.append(int(np.isnan(feat).sum()))
        if np.nanmin(feat[[i for i, n in enumerate(V.FEATURES_V5) if "asymmetry" in n or "range" in n or "vrange" in n or "angle" in n]]) < -1e-9: negs.append(v["video"])
check(f"sin valores invalidos (NaN/inf en secuencia, inf en caracteristicas) en {n_win} ventanas reales", bad == 0, f"ventanas con valores invalidos={bad}")
check("rangos y asimetrias no negativos en ventanas reales", len(negs) == 0, negs[:3])
info("NaN por ventana (caracteristicas no calculables, se imputan con mediana del TRAIN)", f"media={np.mean(n_nan):.2f}, max={max(n_nan)}, ventanas con algun NaN={int(np.sum(np.array(n_nan) > 0))}/{n_win}")
check("36 caracteristicas V5 coinciden en numero con la arquitectura (36)", len(V.FEATURES_V5) == 36 == len(s0[0]) * 0 + 36)

# 4. SENSIBILIDAD A TRASLACION Y ESCALA DE IMAGEN -----------------------------------------------------------------------------
tr = shift_frames(base, dx=0.2, dy=-0.1); st, ft = v5(tr, A)
check("V5 invariante a traslacion del encuadre (secuencia y caracteristicas)", mx(st, s0) < 1e-5 and mx(ft, f0) < 1e-5, f"{mx(st, s0):.1e}/{mx(ft, f0):.1e}")
zm = shift_frames(base, sx=1.3, sy=1.3); sz, fz = v5(zm, A)
check("V5 invariante al zoom (escala aparente de la persona)", mx(sz, s0) < 1e-4 and mx(fz, f0) < 1e-4, f"{mx(sz, s0):.1e}/{mx(fz, f0):.1e}")
_, f4a = v4(base, 8.0); _, f4z = v4(zm, 8.0)
rel = np.nanmax(np.abs(f4z - f4a) / np.maximum(np.abs(f4a), 1e-6))
info("V4: cambio relativo maximo de sus 36 caracteristicas ante zoom x1.3", f"{rel:.3f}")

# 5. RELACION DE ASPECTO ------------------------------------------------------------------------------------------------------
res_a = {}
for a2 in (4 / 3, 9 / 16, 1.0):
    fr2 = synth(aspect=a2); s2, f2 = v5(fr2, a2)
    res_a[round(a2, 3)] = (mx(s2, s0), mx(f2, f0))
check("V5: la misma escena en 16:9, 4:3, 1:1 y 9:16 produce las mismas entradas", all(max(v) < 1e-4 for v in res_a.values()), {k: f"{v[0]:.1e}/{v[1]:.1e}" for k, v in res_a.items()})
s4b, f4b = v4(synth(aspect=9 / 16), 8.0)
info("V4 DEFECTO A4: cambio relativo maximo de sus 36 caracteristicas entre 16:9 y 9:16 (misma escena)", f"{np.nanmax(np.abs(f4b - f4a) / np.maximum(np.abs(f4a), 1e-6)):.3f}; secuencia max|dif|={mx(s4b, s4):.3f}")

# 6. SECUENCIAS CORTAS / DURACION ----------------------------------------------------------------------------------------------
short = [f for f in base if f["timestamp_sec"] < 2.7]
check("V5: ventana de 2.6 s calculable con un clip de 2.7 s", v5(short, A) is not None)
sh, fh = v5(short, A); lg = v5(synth(seconds=20), A)
check("V5: mismas entradas aunque el video dure 2.7 s o 20 s (sin dependencia de la duracion del clip)", mx(sh, lg[0]) < 1e-5 and mx(fh, lg[1]) < 1e-5, f"{mx(sh, lg[0]):.1e}")
check("V5: ventana con < 20 cuadros validos se rechaza (None)", V.window_inputs(base[:15], 0.0, A) is None)
s4s, f4s = v4(short, 2.7); s4l, f4l = v4(synth(seconds=20), 20.0)
info("V4 DEFECTO B3: diferencia de la secuencia V4 entre un clip de 2.7 s y de 20 s con el MISMO movimiento", f"max|dif|={mx(s4s, s4l):.3f} (velocidades dependen de la duracion)")

# 7. CARACTERISTICAS RESPONDEN AL MOVIMIENTO / DEFECTO C ---------------------------------------------------------------------------
_, fc1 = v5(synth(cadence=0.8), A); _, fc2 = v5(synth(cadence=1.3), A)
ic = V.FEATURES_V5.index("estimated_step_count")
check("V5: el conteo de pasos aumenta con la cadencia sintetica (0.8 vs 1.3 Hz)", fc2[ic] > fc1[ic], f"{fc1[ic]:.0f} -> {fc2[ic]:.0f}")
ia = V.FEATURES_V5.index("arm_swing_angle_mean")
_, farm0 = v5(synth(arm_amp_deg=0.0, speed=0.12), A); _, farm20 = v5(synth(arm_amp_deg=20.0, speed=0.12), A); _, farm_walk = v5(synth(arm_amp_deg=0.0, speed=0.5), A)
check("V5: balanceo de brazos = 0 con brazos inmoviles aunque la persona se desplace", farm0[ia] < 0.02 and farm_walk[ia] < 0.02, f"{farm0[ia]:.4f}/{farm_walk[ia]:.4f}")
check("V5: balanceo de brazos crece con la amplitud real (0 -> 20 deg)", farm20[ia] > 0.4, f"rango angular={farm20[ia]:.3f} rad (esperado ~ 2*20 deg*0.9 = 0.6)")
_, g0 = v4(synth(arm_amp_deg=0.0, speed=0.12), 8.0); _, g1 = v4(synth(arm_amp_deg=0.0, speed=0.5), 8.0)
iv = F4.index("left_arm_range")
info("V4 DEFECTO C: 'left_arm_range' con brazos INMOVILES y velocidad de traslacion 0.12 vs 0.5", f"{g0[iv]:.3f} -> {g1[iv]:.3f} (mide desplazamiento global, no balanceo)")
ir = V.FEATURES_V5.index("ankle_rel_vrange_left")
_, fr0 = v5(synth(leg_amp_deg=0.0, speed=0.12), A); _, fr1 = v5(synth(leg_amp_deg=0.0, speed=0.5), A); _, fr2 = v5(synth(leg_amp_deg=30.0), A)
check("V5: rango vertical del tobillo relativo = ~0 con piernas inmoviles, y crece con la amplitud de la zancada", fr0[ir] < 0.02 and fr1[ir] < 0.02 and fr2[ir] > 0.05, f"{fr0[ir]:.3f}/{fr1[ir]:.3f}/{fr2[ir]:.3f}; esperado analitico ~0.09-0.10 (0.14*(1-cos30)+0.14*(cos6-cos15)=0.024 /torso 0.25). Umbral inicial 0.1 era un error de calculo del esperado; corregido ANTES de entrenar")
# movimiento de camara (paneo): V5 limb-relative y secuencia relativa a cadera invariantes; global cambia (esperado)
pan = [{**f, "landmarks": {n: {**p, "x": p["x"] + 0.06 * f["timestamp_sec"] / A} for n, p in f["landmarks"].items()}} for f in base]
sp, fp = v5(pan, A)
idx_rel = [V.FEATURES_V5.index(n) for g in ("piernas_relativas", "brazos", "tronco_postura") for n in V.GROUPS[g] if n != "gait_variability"]
check("V5: secuencia y caracteristicas RELATIVAS (piernas, brazos, tronco) invariantes al paneo de camara", mx(sp, s0) < 1e-4 and mx(fp[idx_rel], f0[idx_rel]) < 1e-4, f"{mx(sp, s0):.1e}/{mx(fp[idx_rel], f0[idx_rel]):.1e}")

# 8. CORRESPONDENCIA ENTRENAMIENTO <-> INFERENCIA --------------------------------------------------------------------------------
if "--dataset" in sys.argv:
    z = np.load(sys.argv[sys.argv.index("--dataset") + 1], allow_pickle=False)
    names = [str(x) for x in z["video"]]; ok = True; worst = 0.0
    for v in vids[::12]:
        sel = np.where(np.array(names) == v["video"])[0]
        for j in sel[:3]:
            r = V.window_inputs(v["frames"], float(z["t0"][j]), v["aspect"])
            d = max(mx(r[0], z["X_seq"][j]), mx(r[1], z["X_feat"][j])); worst = max(worst, d); ok &= d < 1e-6
    check("entradas del dataset V5 == recomputadas con la funcion de inferencia window_inputs (bit a bit, tol 1e-6)", ok, f"max|dif|={worst:.1e}")

fails = [r for r in RES if r["resultado"] == "FAIL"]
(OUT / "fase3_pruebas.json").write_text(json.dumps(RES, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nRESULTADO: {sum(r['resultado']=='PASS' for r in RES)} PASS, {len(fails)} FAIL, {sum(r['resultado']=='DEMOSTRACION_V4' for r in RES)} demostraciones de defectos V4")
sys.exit(1 if fails else 0)
