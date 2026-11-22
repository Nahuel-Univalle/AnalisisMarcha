import { readFileSync } from "node:fs";
import path from "node:path";
import { jsPDF } from "jspdf";
import type { ReportModel } from "./reportModel";

/**
 * PDF A4 del informe médico. Reproduce la plantilla de `MedicalReport.tsx`
 * (mismos textos, orden, tokens de color, jerarquía y proporciones: 1 px de la
 * pantalla = 0,75 pt) con texto vectorial seleccionable. Solo dibuja el
 * `ReportModel`; no calcula ni modifica ningún dato.
 */

const PX = 0.75; // pt por px CSS (A4: 794 px = 595 pt)
const px = (v: number) => v * PX;

// Tokens de src/app/globals.css (ya mezclados sobre blanco donde llevan alfa).
const C = {
  ink: "#124F48",
  muted: "#366963", // ink 85 %
  subtle: "#507D78", // ink 74 %
  line: "#E0E8E7", // ink 13 %
  lineStrong: "#A2D7D1", // line-strong
  primary: "#0B9586",
  navy: "#124F48",
  subtleBg: "#F1FEFB", // surface-subtle
  warning: "#A15C07",
  warningBg: "#FDF3E2",
  warningLine: "#F1D29A",
};

const PAGE_W = 793.7 * PX; // 595.28 pt
const PAGE_H = 1122.5 * PX; // 841.89 pt
const MARGIN_X = px(56);
const MARGIN_TOP = px(48);
const MARGIN_BOTTOM = px(56);
const CONTENT_W = PAGE_W - 2 * MARGIN_X;
const BOTTOM = PAGE_H - MARGIN_BOTTOM;

type FontKey = "sans" | "sansSemi" | "sansBold" | "mono" | "monoMed";
const FONT_FILES: Record<FontKey, { file: string; family: string; style: string }> = {
  sans: { file: "Manrope-Regular.ttf", family: "Manrope", style: "normal" },
  sansSemi: { file: "Manrope-SemiBold.ttf", family: "ManropeSemi", style: "normal" },
  sansBold: { file: "Manrope-Bold.ttf", family: "Manrope", style: "bold" },
  mono: { file: "IBMPlexMono-Regular.ttf", family: "PlexMono", style: "normal" },
  monoMed: { file: "IBMPlexMono-Medium.ttf", family: "PlexMonoMed", style: "normal" },
};

const fontCache = new Map<string, string>();
function fontBase64(file: string) {
  let data = fontCache.get(file);
  if (!data) {
    data = readFileSync(path.join(/* turbopackIgnore: true */ process.cwd(), "assets", "pdf-fonts", file)).toString("base64");
    fontCache.set(file, data);
  }
  return data;
}

// Las fuentes incluidas son el subconjunto latino que usa la interfaz: lo que no
// exista se sustituye por un espacio en lugar de dibujar un glifo vacío.
function safe(text: string) {
  return text
    .replace(/[‐‑‒]/g, "-")
    .replace(/[^\u0000-ÿ–—‘’“”•…€™−]/g, " ")
    .replace(/[ \t]+/g, " ")
    .trim();
}

class Doc {
  pdf: jsPDF;
  y = MARGIN_TOP;
  pageTop = true;

  constructor() {
    this.pdf = new jsPDF({ unit: "pt", format: "a4", compress: true });
    for (const key of Object.keys(FONT_FILES) as FontKey[]) {
      const f = FONT_FILES[key];
      this.pdf.addFileToVFS(f.file, fontBase64(f.file));
      this.pdf.addFont(f.file, f.family, f.style);
    }
  }

  font(key: FontKey, sizePx: number, color: string, tracking = 0) {
    const f = FONT_FILES[key];
    this.pdf.setFont(f.family, f.style);
    this.pdf.setFontSize(px(sizePx));
    this.pdf.setTextColor(color);
    this.pdf.setCharSpace(tracking ? px(tracking) : 0);
  }

  wrap(text: string, key: FontKey, sizePx: number, widthPx: number, tracking = 0): string[] {
    this.font(key, sizePx, C.ink, tracking);
    return this.pdf.splitTextToSize(safe(text), px(widthPx)) as string[];
  }

  /** Texto de una línea; `top` y `lineH` en px (caja de línea CSS). */
  line(text: string, x: number, top: number, lineH: number, sizePx: number, align: "left" | "right" = "left") {
    const baseline = top + px(lineH) / 2 + px(sizePx) * 0.36;
    this.pdf.text(safe(text), x, baseline, { align });
  }

  newPage() {
    this.pdf.addPage();
    this.y = MARGIN_TOP;
    this.pageTop = true;
  }

  ensure(h: number) {
    if (this.y + h > BOTTOM) this.newPage();
  }
}

function hairline(doc: Doc, y: number, w: number, color: string, x = MARGIN_X) {
  doc.pdf.setDrawColor(color);
  doc.pdf.setLineWidth(px(1));
  doc.pdf.line(x, y, x + w, y);
}

function upper(s: string) {
  return s.toLocaleUpperCase("es");
}

function drawActivityIcon(doc: Doc, x: number, y: number, sizePx: number) {
  const s = px(sizePx) / 24;
  const pts: Array<[number, number]> = [
    [22, 12], [19.52, 12], [18.59, 13.46], [16.24, 21.82], [15.76, 21.82], [9.24, 2.18], [8.76, 2.18], [6.41, 10.54], [4.49, 12], [2, 12],
  ];
  doc.pdf.setDrawColor(C.ink);
  doc.pdf.setLineWidth(2 * s);
  doc.pdf.setLineCap("round");
  doc.pdf.setLineJoin("round");
  for (let i = 0; i < pts.length - 1; i++) {
    doc.pdf.line(x + pts[i][0] * s, y + pts[i][1] * s, x + pts[i + 1][0] * s, y + pts[i + 1][1] * s);
  }
}

// ---------------------------------------------------------------------------
//  Bloques
// ---------------------------------------------------------------------------

type Block = { h: number; draw: (top: number) => void };

function textBlock(doc: Doc, text: string, key: FontKey, size: number, lineH: number, color: string, widthPx: number, marginTop = 0): Block {
  const lines = doc.wrap(text, key, size, widthPx);
  return {
    h: px(marginTop) + lines.length * px(lineH),
    draw: (top) => {
      doc.font(key, size, color);
      lines.forEach((ln, i) => doc.line(ln, MARGIN_X, top + px(marginTop) + i * px(lineH), lineH, size));
    },
  };
}

function labelText(doc: Doc, text: string, x: number, top: number) {
  doc.font("sansBold", 11, C.subtle, 0.88);
  doc.line(upper(text), x, top, 16, 11);
}

function sectionHeading(doc: Doc, n: number, title: string, top: number) {
  doc.font("monoMed", 13, C.ink);
  doc.line(`${n}.`, MARGIN_X, top, 20, 13);
  const numW = doc.pdf.getTextWidth(`${n}.`);
  doc.font("sansBold", 13, C.ink, 1.04);
  doc.line(upper(title), MARGIN_X + numW + px(12), top, 20, 13);
}

const HEADING_H = px(20);

/** Sección numerada; título + primer bloque nunca quedan separados por un salto de página. */
function section(doc: Doc, n: number, title: string, blocks: Block[]) {
  const padTop = px(24);
  const gap = px(12);
  // Una sección corta se mantiene entera en una página; una larga reserva al menos título + primer bloque.
  const total = blocks.reduce((sum, b) => sum + b.h, 0);
  const reserve = total <= px(320) ? total : Math.min(blocks[0]?.h ?? 0, px(600));
  doc.ensure(padTop + HEADING_H + gap + reserve);
  if (!doc.pageTop) {
    hairline(doc, doc.y, CONTENT_W, C.line);
    doc.y += padTop;
  }
  sectionHeading(doc, n, title, doc.y);
  doc.y += HEADING_H + gap;
  blocks.forEach((block, i) => {
    if (i > 0) doc.ensure(block.h);
    block.draw(doc.y);
    doc.y += block.h;
    doc.pageTop = false;
  });
  doc.pageTop = false;
  doc.y += px(24);
}

// ---------------------------------------------------------------------------
//  Informe
// ---------------------------------------------------------------------------

export function renderReportPdf(model: ReportModel, meta: { createdAt: Date; fileId: string }): Buffer {
  const doc = new Doc();
  const pdf = doc.pdf;
  pdf.setProperties({ title: "Informe de análisis de marcha", subject: "Documento orientativo", creator: "Análisis de Marcha IA" });
  pdf.setLanguage("es");
  pdf.setCreationDate(meta.createdAt);
  pdf.setFileId(meta.fileId);

  // --- Membrete ---------------------------------------------------------
  const headTop = doc.y;
  drawActivityIcon(doc, MARGIN_X, headTop + px(2), 16);
  doc.font("sansBold", 13, C.navy);
  doc.line("Análisis de Marcha IA", MARGIN_X + px(24), headTop, 20, 13);
  doc.font("sansBold", 24, C.ink);
  doc.line("Informe de análisis de marcha", MARGIN_X, headTop + px(33), 32, 24);
  doc.font("sans", 13, C.muted);
  doc.line("Documento orientativo para profesionales de salud", MARGIN_X, headTop + px(69), 21, 13);
  // distintivo
  doc.font("sansBold", 11, C.muted, 0.88);
  const badgeText = safe(upper(model.badge));
  const badgeW = pdf.getTextWidth(badgeText) + px(0.88 * badgeText.length) + px(18);
  const badgeX = PAGE_W - MARGIN_X - badgeW;
  pdf.setDrawColor(C.line);
  pdf.setLineWidth(px(1));
  pdf.roundedRect(badgeX, headTop, badgeW, px(26), px(6), px(6), "S");
  doc.font("sansBold", 11, C.muted, 0.88);
  doc.line(badgeText, badgeX + px(9), headTop + px(1), 24, 11);
  const headBottom = headTop + px(110);
  pdf.setDrawColor(C.navy);
  pdf.setLineWidth(px(2));
  pdf.line(MARGIN_X, headBottom, MARGIN_X + CONTENT_W, headBottom);
  doc.y = headBottom + px(2);
  doc.pageTop = false;
  let n = 0;

  // --- 1. Datos del análisis --------------------------------------------
  const colW = (682 - 2 * 16) / 3;
  section(doc, ++n, "Datos del análisis", [
    {
      h: px(16 + 4 + 24),
      draw: (top) => {
        const cols: Array<[string, string, "sansSemi" | "monoMed", number]> = [
          ["Usuario evaluado", model.userName, "sansSemi", 15],
          ["Fecha de emisión", model.issuedAt, "monoMed", 14],
          ["Confianza del modelo", model.confidenceText, "monoMed", 15],
        ];
        cols.forEach(([label, value, key, size], i) => {
          const x = MARGIN_X + px(i * (colW + 16));
          labelText(doc, label, x, top);
          doc.font(key, size, C.ink);
          const shown = doc.wrap(value, key, size, colW)[0] ?? "";
          doc.line(shown, x, top + px(20), 24, size);
        });
      },
    },
  ]);

  // --- 2. Resultado ------------------------------------------------------
  const result: Block[] = [];
  {
    const label = model.resultLabel;
    const headLines = doc.wrap(model.headline, "sansSemi", 18, 682);
    result.push({
      h: px(16) + px(4) + headLines.length * px(28),
      draw: (top) => {
        labelText(doc, label, MARGIN_X, top);
        doc.font("sansSemi", 18, C.ink);
        headLines.forEach((ln, i) => doc.line(ln, MARGIN_X, top + px(20) + i * px(28), 28, 18));
      },
    });
  }
  if (model.caveat) {
    const lines = doc.wrap(model.caveat, "sansSemi", 13, 682 - 2 - 24);
    const boxH = lines.length * px(24) + px(16);
    result.push({
      h: px(12) + boxH,
      draw: (top) => {
        const y0 = top + px(12);
        pdf.setFillColor(C.warningBg);
        pdf.rect(MARGIN_X, y0, CONTENT_W, boxH, "F");
        pdf.setFillColor(C.warningLine);
        pdf.rect(MARGIN_X, y0, px(2), boxH, "F");
        doc.font("sansSemi", 13, C.warning);
        lines.forEach((ln, i) => doc.line(ln, MARGIN_X + px(14), y0 + px(8) + i * px(24), 24, 13));
      },
    });
  }
  if (model.showBreakdown) {
    const barW = 448; // max-w-md
    const n = model.rows.length;
    result.push({
      h: px(16 + n * 33 + (n - 1) * 12),
      draw: (top) => {
        let y = top + px(16);
        for (const row of model.rows) {
          doc.font(row.predicted ? "sansSemi" : "sans", 14, row.predicted ? C.ink : C.muted);
          doc.line(row.shortLabel, MARGIN_X, y, 21, 14);
          doc.font(row.predicted ? "monoMed" : "mono", 13, row.predicted ? C.ink : C.subtle);
          doc.line(`${row.percent}%`, MARGIN_X + px(barW), y, 21, 13, "right");
          const barY = y + px(21 + 6);
          pdf.setFillColor(C.subtleBg);
          pdf.roundedRect(MARGIN_X, barY, px(barW), px(6), px(2), px(2), "F");
          const w = (Math.max(0, Math.min(100, row.percent)) / 100) * px(barW);
          if (w > 0) {
            pdf.setFillColor(row.predicted ? C.primary : C.lineStrong);
            pdf.roundedRect(MARGIN_X, barY, Math.max(w, px(2)), px(6), px(2), px(2), "F");
          }
          y += px(33 + 12);
        }
      },
    });
  }
  result.push(textBlock(doc, model.confidenceNote, "sans", 13, 24, C.muted, 682, 12));
  if (model.warnings.length > 0) {
    const items = model.warnings.map((w) => {
      const title = `${w.title}.`;
      // El título va en semibold (más ancho): se descuenta esa diferencia para que ninguna línea se pase del margen.
      doc.font("sansSemi", 13, C.ink);
      const semi = pdf.getTextWidth(title) / PX;
      doc.font("sans", 13, C.ink);
      const regular = pdf.getTextWidth(title) / PX;
      return { title, lines: doc.wrap(`${title} ${w.message}`, "sans", 13, 682 - Math.ceil(semi - regular) - 1) };
    });
    result.push({
      h: px(16 + 16 + 6) + items.reduce((sum, it, i) => sum + it.lines.length * px(24) + (i ? px(4) : 0), 0),
      draw: (top) => {
        labelText(doc, model.warningsTitle, MARGIN_X, top + px(16));
        let y = top + px(16 + 16 + 6);
        items.forEach((it, i) => {
          if (i) y += px(4);
          it.lines.forEach((ln, li) => {
            if (li === 0 && ln.startsWith(it.title)) {
              // título en semibold + resto en regular, sobre la misma línea
              doc.font("sansSemi", 13, C.ink);
              doc.line(it.title, MARGIN_X, y, 24, 13);
              const tw = pdf.getTextWidth(`${it.title} `);
              doc.font("sans", 13, C.muted);
              doc.line(ln.slice(it.title.length).trimStart(), MARGIN_X + tw, y, 24, 13);
            } else {
              doc.font("sans", 13, C.muted);
              doc.line(ln, MARGIN_X, y, 24, 13);
            }
            y += px(24);
          });
        });
      },
    });
  }
  section(doc, ++n, "Resultado", result);

  if (model.reliable) {
    // --- 3. Observaciones -------------------------------------------------
    if (model.findings.length > 0) {
      const last = model.findings.length - 1;
      const blocks: Block[] = model.findings.map((f, i) => {
        const lines = doc.wrap(f.text, "sans", 13, 682 - 36);
        const lead = i > 0 ? 13 : 0; // borde + padding superior
        const h = px(lead + 24 + 16 + 4 + lines.length * 24 + (i === last ? 0 : 12));
        return {
          h,
          draw: (top) => {
            if (i > 0) hairline(doc, top, CONTENT_W, C.line);
            const t = top + px(lead);
            doc.font("mono", 13, C.subtle);
            doc.line(String(i + 1).padStart(2, "0"), MARGIN_X, t, 24, 13);
            doc.font("sansSemi", 15, C.ink);
            doc.line(f.title, MARGIN_X + px(36), t, 24, 15);
            doc.font("sansBold", 11, C.subtle, 0.88);
            doc.line(upper(f.relevance), MARGIN_X + px(36), t + px(24), 16, 11);
            doc.font("sans", 13, C.muted);
            lines.forEach((ln, li) => doc.line(ln, MARGIN_X + px(36), t + px(24 + 16 + 4) + li * px(24), 24, 13));
          },
        };
      });
      section(doc, ++n, "Observaciones del movimiento", blocks);
    } else {
      section(doc, ++n, "Observaciones del movimiento", [textBlock(doc, model.noFindingsText, "sans", 13, 24, C.muted, 682)]);
    }

    // --- 4. Parámetros de marcha -----------------------------------------
    if (model.metrics.length > 0) {
      const w = { p: 150, v: 144 };
      const wd = 682 - w.p - w.v;
      const head: Block = {
        h: px(16 + 8 + 1),
        draw: (top) => {
          doc.font("sansBold", 11, C.subtle, 0.88);
          doc.line("PARÁMETRO", MARGIN_X, top, 16, 11);
          doc.line("DESCRIPCIÓN", MARGIN_X + px(w.p), top, 16, 11);
          doc.line("VALOR", MARGIN_X + px(682), top, 16, 11, "right");
          hairline(doc, top + px(24), CONTENT_W, C.line);
        },
      };
      const rows: Block[] = model.metrics.map((m, i) => {
        const pl = doc.wrap(m.label, "sansSemi", 13, w.p - 16);
        const dl = doc.wrap(m.explanation, "sans", 13, wd - 16);
        const lines = Math.max(pl.length, dl.length);
        const last = i === model.metrics.length - 1;
        const h = px(20 + lines * 21 + (last ? 0 : 1));
        return {
          h,
          draw: (top) => {
            const t = top + px(10);
            doc.font("sansSemi", 13, C.ink);
            pl.forEach((ln, li) => doc.line(ln, MARGIN_X, t + li * px(21), 21, 13));
            doc.font("sans", 13, C.muted);
            dl.forEach((ln, li) => doc.line(ln, MARGIN_X + px(w.p), t + li * px(21), 21, 13));
            doc.font("monoMed", 13, C.ink);
            doc.line(m.value, MARGIN_X + px(682), t, 21, 13, "right");
            if (!last) hairline(doc, top + h - px(1), CONTENT_W, C.line);
          },
        };
      });
      section(doc, ++n, "Parámetros de marcha", [head, ...rows]);
    }

    // --- 5. Interpretación ------------------------------------------------
    const interp: Block[] = [];
    if (model.contextNote) interp.push(textBlock(doc, model.contextNote, "sans", 14, 28, C.ink, 682));
    interp.push(textBlock(doc, "Este resultado no confirma una enfermedad y requiere valoración por un profesional de salud.", "sans", 14, 28, C.muted, 682, 8));
    section(doc, ++n, "Interpretación", interp);

    // --- 6. Recomendaciones ----------------------------------------------
    const recs = model.recommendations.length > 0 ? model.recommendations : [];
    if (recs.length > 0) {
      const blocks: Block[] = recs.map((rec, i) => {
        const lines = doc.wrap(rec, "sans", 14, 682 - 14);
        return {
          h: lines.length * px(24) + (i < recs.length - 1 ? px(6) : 0),
          draw: (top) => {
            pdf.setFillColor(C.navy);
            pdf.circle(MARGIN_X + px(2), top + px(12), px(2), "F");
            doc.font("sans", 14, C.muted);
            lines.forEach((ln, li) => doc.line(ln, MARGIN_X + px(14), top + li * px(24), 24, 14));
          },
        };
      });
      section(doc, ++n, "Recomendaciones", blocks);
    } else {
      section(doc, ++n, "Recomendaciones", [textBlock(doc, model.fallbackRecommendation, "sans", 14, 24, C.muted, 682)]);
    }
  }

  // --- 7. Advertencia ------------------------------------------------------
  {
    const lines = doc.wrap(model.closing, "sans", 13, 682 - 2 - 32);
    const boxH = lines.length * px(24) + px(24);
    section(doc, ++n, "Advertencia", [
      {
        h: boxH,
        draw: (top) => {
          pdf.setFillColor(C.subtleBg);
          pdf.rect(MARGIN_X, top, CONTENT_W, boxH, "F");
          pdf.setFillColor(C.navy);
          pdf.rect(MARGIN_X, top, px(2), boxH, "F");
          doc.font("sans", 13, C.ink);
          lines.forEach((ln, i) => doc.line(ln, MARGIN_X + px(18), top + px(12) + i * px(24), 24, 13));
        },
      },
    ]);
  }

  // Numeración de páginas (solo si hay más de una).
  const total = pdf.getNumberOfPages();
  if (total > 1) {
    for (let p = 1; p <= total; p++) {
      pdf.setPage(p);
      doc.font("mono", 10, C.subtle);
      pdf.text(`${p} / ${total}`, PAGE_W - MARGIN_X, PAGE_H - px(28), { align: "right" });
    }
  }
  return Buffer.from(pdf.output("arraybuffer"));
}
