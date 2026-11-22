import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { canonicalDocument } from "./canonicalPdf";
import { canonicalAnalysisPath } from "./canonicalAnalysis";
import { PDF_PRESENTATION_RENDERER } from "./pdfPresentation";
import { HISTORICAL_PDF_UNAVAILABLE_MESSAGE, PDF_NOT_GENERATED_MESSAGE, ReportPdfAvailability } from "./reportPdfStatus";

export function reportPdfFiles(id: string, hash: string, renderer = PDF_PRESENTATION_RENDERER) {
  const root = path.join(process.env.REPORT_PDF_STORAGE_DIR || path.join(/* turbopackIgnore: true */ process.cwd(), "tmp", "reports"), renderer);
  const dir = path.join(root, `${id}-${hash}`);
  return { root, dir, pdf: path.join(dir, "document.pdf"), meta: path.join(dir, "manifest.json") };
}

async function readCached(id: string, sourceHash: string, allowLegacy: boolean) {
  for (const renderer of allowLegacy ? [PDF_PRESENTATION_RENDERER, "canonical-v4"] : [PDF_PRESENTATION_RENDERER]) {
    const files = reportPdfFiles(id, sourceHash, renderer);
    try {
      const data = await readFile(files.pdf);
      const meta = JSON.parse(await readFile(files.meta, "utf8"));
      if (meta.sourceHash === sourceHash && meta.pdfHash === createHash("sha256").update(data).digest("hex") && meta.renderer === renderer && data.subarray(0, 5).toString() === "%PDF-") return data;
    } catch { /* Try only the other explicitly supported cache namespace. */ }
  }
  return null;
}

export async function readValidatedReportPdf(id: string, userId: string, allowLegacy = true) {
  const doc = await canonicalDocument(id, userId);
  if (!doc) throw new Error("No encontrado");
  const data = await readCached(id, doc.hash, allowLegacy);
  if (!data) throw new Error("PDF no disponible");
  return data;
}

/** Computed response metadata only: never changes MedicalReport or its analysis. */
export async function reportPdfAvailability(id: string, userId: string, analysisId: string): Promise<ReportPdfAvailability> {
  const unavailable: ReportPdfAvailability = { status: "unavailable", message: HISTORICAL_PDF_UNAVAILABLE_MESSAGE };
  try {
    if (!existsSync(canonicalAnalysisPath(analysisId))) return unavailable;
    const doc = await canonicalDocument(id, userId);
    if (!doc) return unavailable;
    return await readCached(id, doc.hash, true)
      ? { status: "available", message: "PDF disponible" }
      : { status: "not_generated", message: PDF_NOT_GENERATED_MESSAGE };
  } catch { return unavailable; }
}
