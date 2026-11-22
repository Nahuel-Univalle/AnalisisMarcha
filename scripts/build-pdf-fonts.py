"""Genera los TTF estáticos que usa el PDF del informe a partir de las MISMAS fuentes que carga la interfaz
(Manrope variable e IBM Plex Mono, subconjunto latino que next/font autoaloja). Solo conversión de formato:
woff2 -> ttf, y para Manrope instancias estáticas de peso 400/600/700. Requiere fontTools + brotli.
Uso: python scripts/build-pdf-fonts.py <manrope.woff2> <plexmono-400.woff2> <plexmono-500.woff2>"""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

out = Path(__file__).resolve().parent.parent / "assets" / "pdf-fonts"
out.mkdir(parents=True, exist_ok=True)
manrope, mono400, mono500 = sys.argv[1:4]

def save(font, name, family, style):
    for rec in font["name"].names:
        if rec.nameID in (1, 16): rec.string = family
        elif rec.nameID in (2, 17): rec.string = style
        elif rec.nameID == 4: rec.string = f"{family} {style}"
        elif rec.nameID == 6: rec.string = f"{family}-{style}".replace(" ", "")
    font.flavor = None
    font.save(out / name); print("ok", name, len(font.getGlyphOrder()), "glifos")

for wght, style in ((400, "Regular"), (600, "SemiBold"), (700, "Bold")):
    f = TTFont(manrope); f.flavor = None
    inst = instancer.instantiateVariableFont(f, {"wght": wght}, inplace=False)
    save(inst, f"Manrope-{style}.ttf", "Manrope", style)
for path, style in ((mono400, "Regular"), (mono500, "Medium")):
    f = TTFont(path); save(f, f"IBMPlexMono-{style}.ttf", "IBM Plex Mono", style)
