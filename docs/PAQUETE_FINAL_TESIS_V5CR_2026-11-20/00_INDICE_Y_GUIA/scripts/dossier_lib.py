"""Utilidades para construir el dossier Word: conversión Markdown -> DOCX, tablas con formato, figuras con pie y sustitución de nombres internos por nombres académicos.
No calcula métricas ni modifica datos: solo presenta contenido ya verificado del paquete."""
import csv
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

PKG = Path(__file__).resolve().parents[2]
TEAL = "124F48"
HEAD_FILL = "D9EFEA"
NOTE_FILL = "F1FEFB"
WARN_FILL = "FDF3E2"

REG_FIG, REG_TAB = [], []  # registros: (id, título, sección del dossier)
_counters = {"fig": 0, "tab": 0}
CURRENT_SECTION = [""]


# ----------------------------------------------------------------------------- nombres académicos
def _cap(rep, text, pos):
    before = text[:pos].rstrip()
    if not before or before[-1] in ".:|•\n#*>-—(¿":
        return rep[0].upper() + rep[1:]
    return rep


RULES = [
    ("V4 activo (BN recalibrada)", "modelo preliminar activo (con BatchNorm recalibrada)"),
    ("V4 BN (activo)", "modelo preliminar activo"),
    ("V4 BN", "modelo preliminar activo"),
    ("V4 activo", "modelo preliminar activo"),
    ("V4 base", "modelo preliminar base"),
    ("modelo V5-CR", "modelo final"),
    ("modelo V4", "modelo preliminar"),
    ("modelos V4", "modelos preliminares"),
    ("versión V5-CR", "versión final"),
    ("versión V4", "versión preliminar"),
    ("V5-CR", "modelo final"),
    ("V5-P", "versión intermedia P"),
    ("V5-C", "versión intermedia C"),
    ("V5-S", "versión intermedia S"),
    ("V4", "modelo preliminar"),
    ("V5", "versión corregida"),
]
_RX = re.compile("|".join(re.escape(a) for a, _ in RULES))
_MAP = dict(RULES)


def academic(text: str) -> str:
    """Sustituye nombres internos por nombres académicos fuera de los fragmentos entre comillas invertidas."""
    parts = re.split(r"(`[^`]*`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            inner = part[1:-1]
            m = re.match(r"(0\d|1[0-4])_[A-Za-z_]+/", inner)
            if m and not inner.startswith(("scripts/", "docs/", "src/", "models/", "outputs/")):
                out.append(FOLDER_MAP[m.group(1)])  # el dossier es autocontenido: se remite a su propia sección
            else:
                out.append(part)
            continue
        part = re.sub(r"gait_deep_v5exp_V5CR_[0-9a-f]{12}", "el identificador técnico del modelo final (sección 14.1)", part)
        res, last = [], 0
        for m in _RX.finditer(part):
            s, e = m.span()
            if s > 0 and (part[s - 1].isalnum() or part[s - 1] in "_-"):
                continue  # parte de otro identificador
            if e < len(part) and (part[e].isalnum() and part[e] != " " or part[e] in "_") :
                continue
            res.append(part[last:s])
            res.append(_cap(_MAP[m.group(0)], part, s))
            last = e
        res.append(part[last:])
        out.append("".join(res))
    r = "".join(out)
    return re.sub(r"\b([Mm]odelo) modelo\b", r"\1", r)


FOLDER_MAP = {"01": "la sección 10 de este dossier", "02": "las secciones 1 y 2 de este dossier", "03": "la sección 4 de este dossier", "04": "las secciones 5 y 8 de este dossier", "05": "la sección 6 de este dossier",
              "06": "la sección 7 de este dossier", "07": "las secciones 2 y 3 de este dossier", "08": "la sección 9 de este dossier", "09": "la sección 11 de este dossier", "10": "la sección 10 de este dossier",
              "11": "la sección 13 de este dossier", "12": "la sección 12 de este dossier", "13": "la sección 14 de este dossier", "14": "la sección 14.6 de este dossier"}
ACAD_MODEL = {"V4 base": "Modelo preliminar base", "V4 activo (BN recalibrada)": "Modelo preliminar activo", "V5-P": "Versión intermedia P", "V5-C": "Versión intermedia C", "V5-CR": "Modelo final"}


def num(s: str) -> str:
    """Formato español de números con punto decimal."""
    return re.sub(r"(?<=\d)\.(?=\d)", ",", s) if isinstance(s, str) else s


# ----------------------------------------------------------------------------- documento y estilos
def new_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    st.paragraph_format.space_after = Pt(5)
    for name, size, color in (("Heading 1", 18, TEAL), ("Heading 2", 14, TEAL), ("Heading 3", 12, TEAL), ("Heading 4", 11, "333333")):
        h = doc.styles[name]
        h.font.name = "Calibri"
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = RGBColor.from_string(color)
        h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        h.paragraph_format.space_before = Pt(14 if name != "Heading 4" else 8)
        h.paragraph_format.space_after = Pt(5)
        h.paragraph_format.keep_with_next = True
    cap = doc.styles["Caption"]
    cap.font.size = Pt(9.5)
    cap.font.italic = False
    cap.font.bold = False
    cap.font.color.rgb = RGBColor.from_string("222222")
    return doc


def usable_width_cm(doc):
    s = doc.sections[-1]
    return (s.page_width - s.left_margin - s.right_margin) / 360000


def set_orientation(doc, landscape: bool):
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    w, h = (Cm(29.7), Cm(21.0)) if landscape else (Cm(21.0), Cm(29.7))
    sec.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = w, h
    sec.left_margin = sec.right_margin = Cm(1.6 if landscape else 2.0)
    sec.top_margin = sec.bottom_margin = Cm(1.8 if landscape else 2.0)
    return sec


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def no_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*\s][^*]*?\*)")


def add_runs(par, text, size=None, bold=False, color=None, italic=False):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = par.add_run(tok[2:-2])
            r.bold = True
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            r = par.add_run(tok[1:-1])
            r.font.name = "Consolas"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
            r.font.size = Pt((size or 10.5) - 1)
            if bold:
                r.bold = True
            if color:
                r.font.color.rgb = RGBColor.from_string(color)
            continue
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = par.add_run(tok[1:-1])
            r.italic = True
        else:
            r = par.add_run(tok)
            if bold:
                r.bold = True
        if italic:
            r.italic = True
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return par


def para(doc, text, style=None, subst=True, size=None, bold=False, align=None, italic=False, color=None, space_after=None, left_indent=None):
    p = doc.add_paragraph(style=style)
    add_runs(p, academic(text) if subst else text, size=size, bold=bold, italic=italic, color=color)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if left_indent:
        p.paragraph_format.left_indent = Cm(left_indent)
    return p


def heading(doc, text, level, subst=True):
    h = doc.add_heading(level=level)
    add_runs(h, academic(text) if subst else text)
    if level == 1:
        CURRENT_SECTION[0] = text
    return h


def bullet(doc, text, subst=True, numbered=False, level=0):
    p = doc.add_paragraph(style="List Number" if numbered else "List Bullet")
    add_runs(p, academic(text) if subst else text)
    p.paragraph_format.space_after = Pt(2)
    if level:
        p.paragraph_format.left_indent = Cm(1.2 + 0.6 * level)
    return p


def callout(doc, title, lines, fill=NOTE_FILL, subst=True):
    """Recuadro de una celda (p. ej. 'Corresponde a los apartados…')."""
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    shade(c, fill)
    c.paragraphs[0].paragraph_format.space_after = Pt(2)
    add_runs(c.paragraphs[0], title, bold=True, size=10)
    for ln in lines:
        p = c.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        add_runs(p, academic(ln) if subst else ln, size=9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def table(doc, header, rows, widths=None, size=9, caption=None, subst=True, bold_first_col=False, zebra=True, align_right_from=None):
    """Tabla real de Word con encabezado repetido y sombreado."""
    if caption:
        _counters["tab"] += 1
        tid = f"Tabla D.{_counters['tab']}"
        REG_TAB.append((tid, caption, CURRENT_SECTION[0]))
        cp = doc.add_paragraph(style="Caption")
        add_runs(cp, f"**{tid}.** {academic(caption) if subst else caption}")
        cp.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    hdr = t.rows[0]
    repeat_header(hdr)
    for i, h in enumerate(header):
        c = hdr.cells[i]
        shade(c, HEAD_FILL)
        c.paragraphs[0].paragraph_format.space_after = Pt(0)
        add_runs(c.paragraphs[0], academic(str(h)) if subst else str(h), size=size, bold=True)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        no_split(t.rows[-1])
        for i, v in enumerate(row):
            c = cells[i]
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            txt = str(v) if v is not None else ""
            add_runs(p, academic(txt) if subst else txt, size=size, bold=(bold_first_col and i == 0))
            if align_right_from is not None and i >= align_right_from:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if zebra and ri % 2 == 1:
                shade(c, "F7FBFA")
    if widths:
        total = sum(widths)
        avail = usable_width_cm(doc)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(avail * w / total)
    doc.add_paragraph().paragraph_format.space_after = Pt(3)
    return t


def figure(doc, path, caption, source_line=None, width_cm=16.0, internal_note=True, registry_note=""):
    """Imagen incrustada (PNG original) + pie."""
    p = Path(path)
    assert p.exists(), p
    _counters["fig"] += 1
    fid = f"Figura D.{_counters['fig']}"
    REG_FIG.append((fid, caption, CURRENT_SECTION[0], p.name))
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(str(p), width=Cm(min(width_cm, usable_width_cm(doc))))
    cp = doc.add_paragraph(style="Caption")
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(cp, f"**{fid}.** {academic(caption)}" + (f" {source_line}" if source_line else ""))
    if internal_note:
        np_ = doc.add_paragraph()
        np_.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(np_, f"Archivo original: `{p.name}`. Los rótulos de la imagen son internos: sus equivalencias académicas están en la Tabla D.1.", size=8, italic=True, color="555555")
    return fid


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ----------------------------------------------------------------------------- Markdown -> docx
def read_md(rel):
    return (PKG / rel).read_text(encoding="utf-8")


def md_section(text, start, stop_prefix="## "):
    """Devuelve el fragmento que empieza en la línea que comienza con `start` y termina antes del siguiente encabezado del mismo nivel."""
    lines = text.split("\n")
    out, on = [], False
    for ln in lines:
        if not on and ln.startswith(start):
            on = True
            continue
        if on and ln.startswith(stop_prefix):
            break
        if on:
            out.append(ln)
    return "\n".join(out).strip("\n")


def parse_table(block):
    rows = []
    for ln in block:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def md_to_docx(doc, text, base_level=3, subst=True, table_caption_prefix=None, skip_headings=False, size=9):
    lines = text.split("\n")
    i = 0
    tcount = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s or s == "---":
            i += 1
            continue
        if s.startswith("#"):
            m = re.match(r"(#+)\s+(.*)", s)
            lvl = min(len(m.group(1)) - 1 + base_level, 4)
            if not skip_headings:
                heading(doc, m.group(2), max(lvl, base_level), subst=subst)
            i += 1
            continue
        if s.startswith("|"):
            blk = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                blk.append(lines[i])
                i += 1
            rows = parse_table(blk)
            if len(rows) >= 2 and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in rows[1]):
                header, body = rows[0], rows[2:]
            else:
                header, body = rows[0], rows[1:]
            n = len(header)
            body = [(r + [""] * n)[:n] for r in body]
            widths = [max(1.0, min(6.0, max(len(str(r[k])) for r in [header] + body) ** 0.6)) for k in range(n)]
            table(doc, header, body, widths=widths, size=size, subst=subst)
            continue
        if s.startswith(">"):
            para(doc, s.lstrip("> ").strip(), subst=subst, italic=True, left_indent=0.6, size=9.5)
            i += 1
            continue
        m = re.match(r"^(\s*)([-*])\s+(.*)", ln)
        if m:
            bullet(doc, m.group(3), subst=subst, level=1 if len(m.group(1)) >= 2 else 0)
            i += 1
            continue
        m = re.match(r"^\s*(\d+)\.\s+(.*)", ln)
        if m and not s.startswith("**"):
            # lista numerada: se escribe el número para conservar la referencia del texto original
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.9)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            p.paragraph_format.space_after = Pt(2)
            add_runs(p, f"{m.group(1)}. " + (academic(m.group(2)) if subst else m.group(2)))
            i += 1
            continue
        # párrafo (une líneas consecutivas no vacías que no sean estructura)
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^\s*(#|\||>|[-*]\s|\d+\.\s)", lines[i]) and lines[i].strip() != "---":
            buf.append(lines[i].strip())
            i += 1
        para(doc, " ".join(buf), subst=subst)


def csv_rows(rel):
    return list(csv.DictReader(open(PKG / rel, encoding="utf-8-sig")))
