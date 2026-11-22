import { mapEvaluationToAnalysisResult } from "./mapApiAnalysis";
import { keyGaitMetricGroups, modelQualityWarnings, analysisQuality, experimentalClassification } from "./resultPresentation";
import { buildReportModel } from "./reportModel";
import { renderReportPdf } from "./reportPdf";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { canonicalAnalysisPath } from "./canonicalAnalysis";
import { prisma } from "@/lib/prisma";

export async function canonicalDocument(reportId: string, userId: string) {
 const report = await prisma.medicalReport.findFirst({ where: { id: reportId, userId }, include: { user: true, analysis: { include: { parameters: true, signals: true, conditions: true } } } });
 if (!report || report.analysis.userId !== userId) return null;
 const parsed = JSON.parse(await readFile(canonicalAnalysisPath(report.analysisId), "utf8"));
 const analysis: { id: string; detectedClass: string | null; confidence: number | null; analysisReliable: boolean; evaluation: { summary: string; recommendations?: string[] }; videoMetrics?: Record<string, number | null>; classProbabilitiesList: Array<{ key: string; shortLabel: string; probability: number }>; modelWarnings: Array<{ code: string; message: string }> } = parsed.analysis;
 const storedClass = report.analysis.parameters.find(p => p.name === "Clase predicha por el modelo experimental");
 const storedConfidence = report.analysis.parameters.find(p => p.name === "Confianza del modelo");
 if (analysis.id !== report.analysisId || analysis.evaluation.summary !== report.analysis.summary || (storedClass?.state ?? null) !== analysis.detectedClass) throw new Error("El archivo canónico no coincide con el registro");
 if (analysis.analysisReliable && (analysis.confidence === null || storedConfidence?.value !== `${Math.round(analysis.confidence * 100)}%` || analysis.classProbabilitiesList.length !== 4 || analysis.classProbabilitiesList.some(p => !Number.isFinite(p.probability) || p.probability < 0 || p.probability > 1) || Math.abs(analysis.classProbabilitiesList.reduce((s,p)=>s+p.probability,0)-1)>0.001)) throw new Error("Probabilidades canónicas incompletas");
 if (analysis.analysisReliable) {
  const expected = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"];
  if (new Set(analysis.classProbabilitiesList.map(p => p.key)).size !== 4 || expected.some(k => !analysis.classProbabilitiesList.some(p => p.key === k))) throw new Error("Clases inconsistentes");
  const best = [...analysis.classProbabilitiesList].sort((a,b) => b.probability-a.probability)[0];
  if (best.key !== analysis.detectedClass || Math.abs(best.probability-(analysis.confidence ?? -1))>1e-6) throw new Error("Clase o confianza inconsistente");
 } else if (analysis.detectedClass !== null || analysis.confidence !== null || analysis.classProbabilitiesList.length !== 0) throw new Error("Resultado no concluyente inconsistente");
 const ui = mapEvaluationToAnalysisResult(parsed.analysis);
 const qualityWarnings = modelQualityWarnings(ui);
 const uiData = { metrics: keyGaitMetricGroups(ui), warnings: [...qualityWarnings.alerts, ...qualityWarnings.notes], confidence: experimentalClassification(ui).confidenceText, caveat: experimentalClassification(ui).caveat, quality: analysisQuality(ui).explanation };
 const data = { version: "canonical-v4", ui: uiData, reportId, analysisId: report.analysisId, name: report.user.name, date: report.createdAt.toISOString(), summary: report.analysis.summary, parameters: [...report.analysis.parameters].sort((a,b)=>a.name.localeCompare(b.name)), signals: [...report.analysis.signals].sort((a,b)=>a.name.localeCompare(b.name)), conditions: report.analysis.conditions, analysis };
 const hash = createHash("sha256").update(JSON.stringify(data)).digest("hex"); return { data, hash };
}
export function renderCanonicalPdf(doc: NonNullable<Awaited<ReturnType<typeof canonicalDocument>>>) {
 // Misma fuente de datos y misma plantilla que el informe en pantalla (MedicalReport):
 // el PDF solo presenta el análisis guardado; no recalcula nada ni añade datos técnicos.
 const result = mapEvaluationToAnalysisResult(doc.data.analysis as unknown as Parameters<typeof mapEvaluationToAnalysisResult>[0]);
 const created = new Date(doc.data.date);
 const model = buildReportModel(result, {
  userName: doc.data.name || "Usuario",
  issuedAt: created.toLocaleDateString("es-BO", { timeZone: "America/La_Paz" }),
 });
 return renderReportPdf(model, { createdAt: created, fileId: doc.hash.slice(0, 32) });
}
