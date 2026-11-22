"""V5-C: construccion del banco de ventanas, validacion cruzada y modelo final. Protocolo IDENTICO a V5-P
(../mejora_modelo_v5_experimental_2026-11-19/codigo/fase6_entrenar_v5.py): mismas particiones por sujeto, semillas, arquitectura, epocas,
escalador/temperatura/E* solo con entrenamiento. Unico cambio: las 33 caracteristicas de v5c_preproc.
Uso: --build | --cv | --final [--smoke]"""
import argparse, csv, hashlib, json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / "mejora_modelo_v5_experimental_2026-11-19"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(OLD / "codigo"))
import v5_preproc as V
import v5_train_core as TC
import v5cr_preproc as C
from data_v5 import load_videos
T11, DC, CFG = TC.T11, TC.DC, TC.CFG
OUT = HERE.parent / "resultados"
ap = argparse.ArgumentParser()
ap.add_argument("--build", action="store_true"); ap.add_argument("--cv", action="store_true"); ap.add_argument("--final", action="store_true"); ap.add_argument("--smoke", action="store_true")
a = ap.parse_args()
BANK = OUT / "dataset_v5cr_bank.npz"

if a.build:
    zb = np.load(OLD / "resultados" / "dataset_v5_bank.npz", allow_pickle=False)
    vids = load_videos(); Xf = np.zeros((len(zb["vid"]), 33), np.float32); Xs_new = np.zeros_like(zb["X_seq"]); worst = 0.0
    for j, (i, t0) in enumerate(zip(zb["vid"], zb["t0"])):
        r = C.window_inputs_C(vids[i]["frames"], float(t0), vids[i]["aspect"])
        assert r is not None
        worst = max(worst, float(np.abs(r[0] - zb["X_seq"][j]).max())); Xf[j] = r[1]; Xs_new[j] = r[0]
    pass
    np.savez_compressed(BANK, X_seq=Xs_new, X_feat=Xf, vid=zb["vid"], t0=zb["t0"], y=zb["y"], group=zb["group"], video=zb["video"], feature_names=np.array(C.FEATURES_C))
    print("banco V5-C", Xf.shape, "NaN:", int(np.isnan(Xf).sum()), "ventanas con NaN:", int(np.isnan(Xf).any(1).sum()), "max dif de secuencia vs V5-P/V5-C (esperada > 0 donde habia huecos): %.2f" % worst)
    sys.exit(0)

T11.enable_determinism()
z = np.load(BANK, allow_pickle=False)
y, g = z["y"].astype(np.int64), z["group"].astype(str)
bank = TC.Bank(z["X_seq"], z["X_feat"], z["vid"], len(y), CFG["K_eval_windows"])
names = [str(n) for n in z["feature_names"]]
perm = list(range(len(names)))
for l, r in V._FLR:
    if l in names and r in names:
        i, j = names.index(l), names.index(r); perm[i], perm[j] = perm[j], perm[i]
TC.FPERM = np.asarray(perm)
cfg_model = DC.default_model_config(num_classes=4); cfg_model["num_features"] = len(names); cfg_model["sequence_length"] = V.T
T11.CLASS_NAMES, T11.NUM_CLASSES = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"], 4
mdir = OUT / "modelos_cv_V5CR"; mdir.mkdir(exist_ok=True)
if a.smoke: CFG["max_epochs"] = 6


def cv():
    oof, oofc, rows = {}, {}, []
    for p in (CFG["partition_seeds"][:1] if a.smoke else CFG["partition_seeds"]):
        P = np.full((len(y), 4), np.nan); Pc = np.full_like(P, np.nan)
        for k, (tr, te) in enumerate(TC.sgkf(y, g, 5, p), start=1):
            if a.smoke and k > 1: P[te] = 0.25; Pc[te] = 0.25; continue
            assert not set(g[tr]) & set(g[te])
            inner = TC.sgkf(y[tr], g[tr], 3, 1000 * p + k)
            curves, sizes, vlog, vlab = [], [], [], []; t0 = time.time()
            for j, (itr, iva) in enumerate(inner, start=1):
                _, _, c, lg = TC.train_fixed(bank, y, tr[itr], CFG["max_epochs"], cfg_model, 1000 * p + 10 * k + j, val=tr[iva])
                curves.append(c); sizes.append(len(iva)); vlog.append(lg); vlab.append(y[tr[iva]])
            E, mc, sm = TC.choose_epoch(curves, sizes)
            temp = T11.fit_temperature(np.concatenate([lg[E - 1] for lg in vlog]), np.concatenate(vlab))
            model, scaler, oc, _ = TC.train_fixed(bank, y, tr, E, cfg_model, 1000 * p + 10 * k)
            lg = bank.video_logits(model, scaler, te)
            P[te] = T11.softmax_np(lg); Pc[te] = T11.softmax_np(lg / temp)
            import torch
            torch.save(model.state_dict(), mdir / f"p{p}_f{k}.pt"); (mdir / f"p{p}_f{k}_scaler.json").write_text(json.dumps(scaler.to_json()), encoding="utf-8")
            m = DC.classification_metrics(y[te], P[te].argmax(1), P[te], class_names=T11.CLASS_NAMES)
            rows.append({"variant": "V5CR", "partition_seed": p, "fold": k, "E_star": E, "temperature": temp, "n_test": len(te), "accuracy": round(m["accuracy"], 4), "macro_f1": round(m["macro_f1"], 4), "seconds": round(time.time() - t0, 1)})
            print(f"[V5CR p{p} f{k}] E*={E} T={temp} acc={rows[-1]['accuracy']} mf1={rows[-1]['macro_f1']} ({rows[-1]['seconds']}s)", flush=True)
        oof[f"p{p}"], oofc[f"c{p}"] = P, Pc
    np.savez(OUT / f"oof_V5CR{'_smoke' if a.smoke else ''}.npz", **oof, **oofc)
    with open(OUT / f"folds_V5CR{'_smoke' if a.smoke else ''}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def final():
    curves, sizes, vlog, vlab = [], [], [], []
    for j, (itr, iva) in enumerate(TC.sgkf(y, g, 3, 4200), start=1):
        _, _, c, lg = TC.train_fixed(bank, y, itr, CFG["max_epochs"], cfg_model, 4200 + j, val=iva)
        curves.append(c); sizes.append(len(iva)); vlog.append(lg); vlab.append(y[iva])
    E, mc, sm = TC.choose_epoch(curves, sizes)
    temp = T11.fit_temperature(np.concatenate([lg[E - 1] for lg in vlog]), np.concatenate(vlab))
    model, scaler, oc, _ = TC.train_fixed(bank, y, np.arange(len(y)), E, cfg_model, 4200)
    import torch
    d = OUT.parent / "checkpoints"; d.mkdir(exist_ok=True); tmp = d / "_tmp.pt"; torch.save(model.state_dict(), tmp)
    sha = hashlib.sha256(tmp.read_bytes()).hexdigest(); ver = f"gait_deep_v5exp_V5CR_{sha[:12]}"; tmp.rename(d / f"{ver}.pt")
    DC.write_json(d / f"{ver}_config.json", {**cfg_model, "model_version": ver, "weights_sha256": sha, "E_star": E, "temperature": temp, "protocol": CFG, "feature_names": names,
                                              "window_s": V.SPAN_S, "fps": V.FPS, "status": "EXPERIMENTAL V5-C - NO integrado, no diagnostico; entrenado con los 117 videos (no estima exactitud)"})
    DC.write_json(d / f"{ver}_feature_scaler.json", scaler.to_json()); DC.write_json(d / f"{ver}_label_map.json", {"class_names": T11.CLASS_NAMES})
    print("final", ver, "E*", E, "T", temp)


if a.final: final()
elif a.cv: cv()
