"""Auditoría automática del paquete: carpetas con contenido, archivos vacíos, imágenes legibles, privacidad (correos, rutas de usuario, secretos), coherencia de cifras clave
y comprobación de que la aplicación, los modelos y la configuración no cambiaron respecto a la instantánea tomada antes de crear el paquete."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
out = {}
# 1) carpetas con contenido
folders = sorted(p for p in PKG.iterdir() if p.is_dir())
out["carpetas"] = {p.name: sum(1 for f in p.rglob("*") if f.is_file()) for p in folders}
out["carpetas_vacias"] = [k for k, v in out["carpetas"].items() if v == 0 and not k.startswith("14_")]
# 2) archivos vacíos
files = [f for f in PKG.rglob("*") if f.is_file() and "__pycache__" not in f.parts]
out["archivos_totales"] = len(files)
out["archivos_vacios"] = [f.relative_to(PKG).as_posix() for f in files if f.stat().st_size == 0]
# 3) imágenes
bad, imgs = [], 0
for f in files:
    if f.suffix.lower() == ".png":
        imgs += 1
        try:
            with Image.open(f) as im:
                im.verify()
            with Image.open(f) as im:
                w, h = im.size
                if w < 300 or h < 200:
                    bad.append((f.name, "muy pequeña", w, h))
        except Exception as e:  # noqa: BLE001
            bad.append((f.name, str(e)))
out["png_total"] = imgs
out["png_con_problemas"] = bad
dpi = []
for f in (PKG / "05_MATRICES_DE_CONFUSION").glob("*.png"):
    with Image.open(f) as im:
        dpi.append((f.name, im.info.get("dpi")))
out["dpi_matrices"] = dpi
out["svg_pares"] = {"matrices": len(list((PKG / "05_MATRICES_DE_CONFUSION").glob("*.svg"))), "figuras": len(list((PKG / "06_FIGURAS_Y_GRAFICAS").glob("*.svg")))}
# 4) privacidad
pat = {"correo_real": re.compile(r"[\w.+-]+@(?!example\.invalid)[\w-]+\.[a-z]{2,}", re.I), "ruta_usuario": re.compile(r"C:[\\/]+Users[\\/]+\w+", re.I), "secreto": re.compile(r"(AUTH_SESSION_SECRET|CLOUDINARY_API_SECRET|DATABASE_URL=)\s*[=:]\s*\S{6,}", re.I)}
hits = {k: [] for k in pat}
for f in files:
    if f.suffix.lower() in (".md", ".csv", ".json", ".txt", ".py", ".mjs"):
        t = f.read_text(encoding="utf-8", errors="ignore")
        for k, rg in pat.items():
            for m in rg.finditer(t):
                hits[k].append((f.relative_to(PKG).as_posix(), m.group(0)[:60]))
out["privacidad"] = {k: v[:12] for k, v in hits.items()}
out["privacidad_conteos"] = {k: len(v) for k, v in hits.items()}
videos = [f.name for f in files if f.suffix.lower() in (".mp4", ".mov", ".webm", ".avi", ".pt", ".npz", ".pkl", ".env")]
out["binarios_pesados_o_videos"] = videos
out["tamano_total_MB"] = round(sum(f.stat().st_size for f in files) / 1e6, 1)
# 5) coherencia de cifras clave
m = {r.split(",")[0].strip("﻿"): r for r in (PKG / "04_METRICAS_Y_COMPARACIONES/METRICAS_VERIFICADAS_POR_MODELO.csv").read_text(encoding="utf-8-sig").splitlines()}
v5 = m["V5-CR"].split(",")
out["V5CR_exactitud_f1macro_csv"] = (v5[1], v5[2])
ver = (PKG / "04_METRICAS_Y_COMPARACIONES/VERIFICACION_CONTRA_ORIGINALES.csv").read_text(encoding="utf-8-sig").splitlines()
out["verificacion_metricas"] = {"filas": len(ver) - 1, "no_coinciden": sum(1 for r in ver[1:] if r.rstrip().endswith("False"))}
# textos: ¿atribuyen a V5-CR cifras de V5-P (0,800 / 0,880)?
txt = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in (PKG / "12_TEXTOS_PROPUESTOS_PARA_TESIS").glob("*.md"))
out["textos_V5CR_con_0_880_o_0_800"] = len(re.findall(r"0,880|0,800", txt))
out["textos_mencionan_no_concluyente"] = len(re.findall(r"concluyente", txt))
out["textos_mencionan_validacion_interna"] = len(re.findall(r"validación interna|evaluación interna", txt))
# 6) aplicación sin cambios
snap = REPO / "tmp" / "snapshot_aplicacion_antes.txt"
changed = []
if snap.exists():
    for line in snap.read_text(encoding="utf-8").splitlines():
        h, rel = line.split(None, 1)
        rel = rel.lstrip("*").strip()
        p = REPO / rel
        if not p.exists():
            changed.append((rel, "ausente"))
        elif hashlib.sha256(p.read_bytes()).hexdigest() != h:
            changed.append((rel, "modificado"))
    out["aplicacion_snapshot_archivos"] = len(snap.read_text(encoding="utf-8").splitlines())
out["aplicacion_cambios_desde_la_instantanea"] = changed
# 7) git (solo lectura)
try:
    g = subprocess.run(["git", "status", "--short"], cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    out["git_modificados_tracked"] = [l[3:] for l in g if not l.startswith("??")]
except Exception as e:  # noqa: BLE001
    out["git"] = str(e)
(PKG / "14_AUDITORIA_FINAL" / "AUDITORIA_AUTOMATICA.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: out[k] for k in ["archivos_totales", "archivos_vacios", "png_total", "png_con_problemas", "carpetas_vacias", "privacidad_conteos", "binarios_pesados_o_videos", "tamano_total_MB", "verificacion_metricas", "aplicacion_cambios_desde_la_instantanea", "textos_V5CR_con_0_880_o_0_800"]}, ensure_ascii=False, indent=1))
sys.exit(0)
