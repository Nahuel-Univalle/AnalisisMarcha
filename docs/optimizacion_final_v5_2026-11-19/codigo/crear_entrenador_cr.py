"""Genera fase8_entrenar_cr.py a partir de fase8_entrenar_c.py (mismo protocolo; solo cambia el modulo de preprocesamiento y los nombres de salida)."""
from pathlib import Path
H = Path(__file__).resolve().parent
s = (H / "fase8_entrenar_c.py").read_text(encoding="utf-8")
s = s.replace("V5C", "V5CR").replace("v5c_bank", "v5cr_bank").replace("import v5c_preproc as C", "import v5cr_preproc as C")
# el banco CR debe contener la secuencia CR (no la de V5-P): se construye desde los frames
s = s.replace("    assert worst == 0.0, worst\n", "    pass\n")
s = s.replace("worst = max(worst, float(np.abs(r[0] - zb[\"X_seq\"][j]).max())); Xf[j] = r[1]", "worst = max(worst, float(np.abs(r[0] - zb[\"X_seq\"][j]).max())); Xf[j] = r[1]; Xs_new[j] = r[0]")
s = s.replace("vids = load_videos(); Xf = np.zeros((len(zb[\"vid\"]), 33), np.float32); worst = 0.0", "vids = load_videos(); Xf = np.zeros((len(zb[\"vid\"]), 33), np.float32); Xs_new = np.zeros_like(zb[\"X_seq\"]); worst = 0.0")
s = s.replace("np.savez_compressed(BANK, X_seq=zb[\"X_seq\"]", "np.savez_compressed(BANK, X_seq=Xs_new")
s = s.replace("secuencia identica a V5-P (max dif %.1e)", "max dif de secuencia vs V5-P/V5-C (esperada > 0 donde habia huecos): %.2f")
(H / "fase8_entrenar_cr.py").write_text(s, encoding="utf-8")
print("ok", s.count("V5CR"), "Xs_new" in s)
