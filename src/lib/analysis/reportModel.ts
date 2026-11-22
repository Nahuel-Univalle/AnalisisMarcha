import type { AnalysisResult } from "@/types";
import {
  EXPERIMENTAL_DISCLAIMER,
  MODEL_CONFIDENCE_NOTE,
  NO_FINDINGS_TEXT,
  ORIENTATION_DISCLAIMER,
  analysisQuality,
  experimentalClassification,
  isReliable,
  keyGaitMetricGroups,
  medicalContextNote,
  modelQualityWarnings,
  patternPresentation,
  presentedFindings,
  type ClassificationRow,
} from "./resultPresentation";

/**
 * ÚNICA fuente de datos del informe médico. La vista en pantalla
 * (`MedicalReport.tsx`) y el PDF descargable (`reportPdf.ts`) se alimentan de
 * este modelo, de modo que no pueden mostrar información distinta. Es una
 * función pura (sin React ni acceso a datos): solo presenta los valores del
 * análisis; no recalcula ni altera ninguna probabilidad.
 */
export type ReportModel = {
  badge: string;
  userName: string;
  issuedAt: string;
  confidenceText: string;
  reliable: boolean;
  resultLabel: string;
  headline: string;
  caveat: string | null;
  showBreakdown: boolean;
  rows: ClassificationRow[];
  confidenceNote: string;
  warningsTitle: string;
  warnings: Array<{ title: string; message: string }>;
  findings: Array<{ title: string; relevance: string; text: string }>;
  noFindingsText: string;
  metrics: Array<{ label: string; explanation: string; value: string }>;
  contextNote: string;
  recommendations: string[];
  fallbackRecommendation: string;
  closing: string;
};

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

export function buildReportModel(
  result: AnalysisResult,
  context: { userName: string; issuedAt: string }
): ReportModel {
  const reliable = isReliable(result);
  const pattern = patternPresentation(result);
  const quality = analysisQuality(result);
  const classification = experimentalClassification(result);
  const qualityWarnings = modelQualityWarnings(result);

  return {
    badge: classification.available ? "Clasificación experimental" : "Resultado orientativo",
    userName: context.userName,
    issuedAt: context.issuedAt,
    confidenceText: classification.confidenceText,
    reliable,
    resultLabel: classification.available
      ? "Clasificación experimental de patrones de marcha"
      : "Patrón de marcha observado",
    headline: reliable ? pattern.phrase : "Análisis no concluyente por calidad del video",
    caveat: classification.caveat,
    showBreakdown: classification.available,
    rows: classification.rows,
    confidenceNote: reliable ? MODEL_CONFIDENCE_NOTE : quality.explanation,
    warningsTitle: "Advertencias sobre el video",
    warnings: reliable
      ? [...qualityWarnings.alerts, ...qualityWarnings.notes].map((warning) => ({
          title: warning.title,
          message: warning.message,
        }))
      : [],
    findings: presentedFindings(result).map((finding) => ({
      title: finding.title,
      relevance: finding.relevance,
      text: finding.medicalText,
    })),
    noFindingsText: NO_FINDINGS_TEXT,
    metrics: keyGaitMetricGroups(result)
      .flatMap((group) => group.params)
      .map((param) => ({
        label: param.label,
        explanation: param.explanation,
        value: `${param.value}${param.unit ? ` ${param.unit}` : ""}`,
      })),
    contextNote: reliable ? medicalContextNote(pattern.classKey) : "",
    recommendations: dedupeStrings(result.recommendations ?? []),
    fallbackRecommendation: "Se recomienda que un profesional de salud revise este resultado.",
    closing: classification.available
      ? EXPERIMENTAL_DISCLAIMER
      : `${ORIENTATION_DISCLAIMER} La interpretación clínica debe ser realizada por un profesional de salud.`,
  };
}
