"""Fase 6 -- entrenamiento y validacion cruzada V5 (protocolo comparable con V4 paso 12).
Uso: python fase6_entrenar_v5.py --variant P|S [--smoke] [--final]
P = V5 principal (36 caracteristicas, pre-registrada). S = sensibilidad (33 caracteristicas: sin anchos de hombros/caderas ni step_frequency_hz).
Particiones externas: IDENTICAS a V4 (StratifiedGroupKFold por sujeto, semillas 42-46, 5 folds) porque y/grupos/orden coinciden.
Escalador, BatchNorm, temperatura y E* se ajustan SOLO con datos de entrenamiento de cada fold."""
import argparse, csv, hashlib, json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v5_train_core as TC
import v5_preproc as V
T11, DC, CFG = TC.T11, TC.DC, TC.CFG
OUT = HERE.parent / "resultados"
ap = argparse.ArgumentParser(); ap.add_argument("--variant", required=True, choices=["P", "S"]); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--final", action="store_true")
a = ap.parse_args()
T11.enable_determinism()
z = np.load(OUT / "dataset_v5_bank.npz", allow_pickle=False)
y, g, videos = z["y"].astype(np.int64), z["group"].astype(str), [str(v) for v in dict.fromkeys(z["video"])]
keep = list(range(36)) if a.variant == "P" else V.S_KEEP_IDX
TC.set_feature_columns(keep)
bank = TC.Bank(z["X_seq"], z["X_feat"][:, keep], z["vid"], len(y), CFG["K_eval_windows"])
cfg_model = DC.default_model_config(num_classes=4); cfg_model["num_features"] = len(keep); cfg_model["sequence_length"] = V.T
T11.CLASS_NAMES, T11.NUM_CLASSES = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"], 4
tag = f"V5{a.variant}"
mdir = OUT / f"modelos_cv_{tag}"; mdir.mkdir(exist_ok=True)
CFG["max_epochs"] = 6 if a.smoke else CFG["max_epochs"]


def cv():
    oof, oofc, rows = {}, {}, []
    seeds = CFG["partition_seeds"][:1] if a.smoke else CFG["partition_seeds"]
    for p in seeds:
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
            rows.append({"variant": tag, "partition_seed": p, "fold": k, "E_star": E, "temperature": temp, "n_test": len(te), "accuracy": round(m["accuracy"], 4),
                         "macro_f1": round(m["macro_f1"], 4), "seconds": round(time.time() - t0, 1), "test_classes": np.bincount(y[te], minlength=4).tolist()})
            print(f"[{tag} p{p} f{k}] E*={E} T={temp} acc={rows[-1]['accuracy']} mf1={rows[-1]['macro_f1']} ({rows[-1]['seconds']}s)", flush=True)
        oof[f"p{p}"], oofc[f"c{p}"] = P, Pc
    np.savez(OUT / f"oof_{tag}{'_smoke' if a.smoke else ''}.npz", **oof, **oofc)
    with open(OUT / f"folds_{tag}{'_smoke' if a.smoke else ''}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def final():
    all_idx = np.arange(len(y)); curves, sizes, vlog, vlab = [], [], [], []
    for j, (itr, iva) in enumerate(TC.sgkf(y, g, 3, 4200), start=1):
        _, _, c, lg = TC.train_fixed(bank, y, itr, CFG["max_epochs"], cfg_model, 4200 + j, val=iva)
        curves.append(c); sizes.append(len(iva)); vlog.append(lg); vlab.append(y[iva])
    E, mc, sm = TC.choose_epoch(curves, sizes)
    temp = T11.fit_temperature(np.concatenate([lg[E - 1] for lg in vlog]), np.concatenate(vlab))
    model, scaler, oc, _ = TC.train_fixed(bank, y, all_idx, E, cfg_model, 4200)
    import torch
    d = OUT.parent / "checkpoints"; d.mkdir(exist_ok=True)
    tmp = d / "_tmp.pt"; torch.save(model.state_dict(), tmp); sha = hashlib.sha256(tmp.read_bytes()).hexdigest()
    ver = f"gait_deep_v5exp_{tag}_{sha[:12]}"; tmp.rename(d / f"{ver}.pt")
    DC.write_json(d / f"{ver}_config.json", {**cfg_model, "model_version": ver, "weights_sha256": sha, "E_star": E, "temperature": temp, "protocol": CFG,
                                              "feature_names": [V.FEATURES_V5[i] for i in keep], "window_s": V.SPAN_S, "fps": V.FPS,
                                              "status": "EXPERIMENTAL V5 - NO integrado en produccion, no diagnostico; entrenado con los 117 videos (no usar para estimar exactitud)"})
    DC.write_json(d / f"{ver}_feature_scaler.json", scaler.to_json())
    DC.write_json(d / f"{ver}_label_map.json", {"class_names": T11.CLASS_NAMES})
    print("final", ver, "E*", E, "T", temp)


if a.final:
    final()
else:
    cv()
