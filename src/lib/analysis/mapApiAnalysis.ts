import { AlertLevel, AnalysisResult, ModelWarning, SignalSeverity } from "@/types";
import { buildObservedSignals, observedSeverityToAlertLabel } from "@/lib/analysis/observedSignals";
type ApiAnalysis = {
  id?: string;
  videoRecordId?: string | null;
  provider?: string;
  annotatedVideoUrl?: string | null;
  originalVideoUrl?: string | null;
  originalVideoPublicId?: string | null;
  processedVideoUrl?: string | null;
  processedVideoPublicId?: string | null;
  localOriginalVideoUrl?: string | null;
  localProcessedVideoUrl?: string | null;
  cloudinaryUploadOk?: boolean;
  savedToDatabase?: boolean;
  visualAnalysisCompleted?: boolean;
  modelUsed?: boolean;
  modelUsedForVideo?: boolean;
  predictionLabel?: string | null;
  predictionConfidence?: number | null;
  classProbabilities?: {
    control: number | null;
    parkinson: number | null;
  } | null;
  predictionBasis?: string | null;
  modelPredictionMessage?: string | null;
  decisionSource?: string;
  modelControlProbability?: number | null;
  modelParkinsonProbability?: number | null;
  modelKind?: string | null;
  modelVersion?: string | null;
  analysisReliable?: boolean;
  qualityMessage?: string | null;
  detectedClass?: string | null;
  detectedClassLabel?: string | null;
  classProbabilitiesByName?: Record<string, number> | null;
  classProbabilitiesList?: Array<{
    key: string;
    label: string;
    shortLabel: string;
    probability: number;
  }> | null;
  alteredProbability?: number | null;
  orientationText?: string | null;
  featureHighlights?: Array<{
    concept: string;
    label: string;
    values: Record<string, number>;
    note: string;
  }> | null;
  gaitFeatures?: Record<string, number | null> | null;
  modelMacroF1?: number | null;
  modelAvailable?: boolean;
  modelMetricsAvailable?: boolean;
  modelAccuracy?: number | null;
  modelPrecision?: number | null;
  modelRecall?: number | null;
  modelF1Score?: number | null;
  modelWarning?: string | null;
  validationMethod?: string | null;
  modelSamples?: number | null;
  modelControlSamples?: number | null;
  modelParkinsonSamples?: number | null;
  modelTrainSize?: number | null;
  modelTestSize?: number | null;
  modelMessage?: string;
  poseDetectionRate?: number | null;
  poseQuality?: string;
  framesAnalyzed?: number;
  framesWithPose?: number;
  metrics?: Record<string, unknown>;
  signals?: string[];
  visualSignals?: string[];
  warnings?: string[];
  videoMetrics?: Record<string, number | null>;
  modelSource?: string | null;
  probabilityParkinson?: number | null;
  probabilityNormal?: number | null;
  riskLevel?: string | null;
  confidence?: number | null;
  experimentalClassification?: boolean;
  modelVariant?: string | null;
  modelWarnings?: ModelWarning[];
  confidenceMeaning?: string | null;
  modelDisclaimer?: string | null;
  observedSignals?: Array<{
    title: string;
    description: string;
    severity: "info" | "bajo" | "medio" | "alto";
    source?: "model" | "feature" | "fallback";
    reason?: string;
  }>;
  signalEmptyMessage?: string | null;
  signalDecision?: string | null;
  evaluation: {
    alertLevel: string;
    title: string;
    summary: string;
    detectedSignals: Array<{
      name: string;
      relevance: string;
      description: string;
    }>;
    recommendations: string[];
    possibleCondition: string;
  };
};

function toAlertLevel(level: string): AlertLevel {
  if (level === "ALTO") return "Alto";
  if (level === "MEDIO") return "Medio";
  return "Bajo";
}

function toSignalSeverity(level: string): SignalSeverity {
  if (level === "Info") return "Info";
  if (level === "Alto") return "Alto";
  if (level === "Medio") return "Medio";
  return "Bajo";
}

function metricLabel(value?: number | null) {
  if (value === null || value === undefined) return "Sin dato";
  return `${Math.round(value * 1000) / 1000}`;
}

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

function mapSignalDescription(name: string, description: string) {
  if (name === "Balanceo de brazos reducido o asimétrico") {
    return "El sistema observó menor movimiento o diferencia entre ambos brazos durante la caminata. Esta señal puede aparecer en distintas alteraciones de la marcha.";
  }

  if (name === "Postura alterada") {
    return "El sistema observó una inclinación o cambio postural durante el desplazamiento.";
  }

  return description;
}

export function mapEvaluationToAnalysisResult(analysis: ApiAnalysis): AnalysisResult {
  const evaluation = analysis.evaluation;
  const alertLevel = toAlertLevel(evaluation.alertLevel);
  const warnings = dedupeStrings(analysis.warnings ?? []);
  const modelDetectedAlteration =
    analysis.modelUsed === true &&
    evaluation.possibleCondition !== "sin_alerta" &&
    (analysis.detectedClass ?? "normal") !== "normal";
  const detectedLabel =
    analysis.detectedClassLabel ||
    (modelDetectedAlteration
      ? "Patrón de marcha con posible alteración"
      : "Marcha dentro de patrones esperados");
  const parkinsonCondition = {
    condition: modelDetectedAlteration
      ? `Resultado orientativo: ${detectedLabel}`
      : "Sin alerta principal en la marcha",
    status: modelDetectedAlteration
      ? "Requiere valoración profesional"
      : "Sin alerta principal",
    description: analysis.orientationText || evaluation.summary,
  };
  const observedSignalResult =
    analysis.observedSignals && analysis.observedSignals.length > 0
      ? {
          signals: analysis.observedSignals,
          emptyMessage: analysis.signalEmptyMessage ?? null,
          signalDecision:
            analysis.signalDecision ?? "Signals provided by analysis API",
        }
      : buildObservedSignals({
          modelSource: analysis.modelSource,
          probabilityParkinson:
            analysis.probabilityParkinson ??
            analysis.modelParkinsonProbability ??
            analysis.classProbabilities?.parkinson,
          probabilityNormal:
            analysis.probabilityNormal ??
            analysis.modelControlProbability ??
            analysis.classProbabilities?.control,
          riskLevel: analysis.riskLevel,
          confidence: analysis.confidence ?? analysis.predictionConfidence,
          poseDetectionRate: analysis.poseDetectionRate,
          framesAnalyzed: analysis.framesAnalyzed,
          framesWithPose: analysis.framesWithPose,
          videoMetrics: analysis.videoMetrics,
          ruleSignals: evaluation.detectedSignals,
        });

  return {
    id: analysis.id,
    videoRecordId: analysis.videoRecordId ?? null,
    alertLevel,
    title: evaluation.title,
    summary: evaluation.summary,
    annotatedVideoUrl: analysis.annotatedVideoUrl ?? undefined,
    originalVideoUrl: analysis.originalVideoUrl ?? undefined,
    originalVideoPublicId: analysis.originalVideoPublicId ?? undefined,
    processedVideoUrl: analysis.processedVideoUrl ?? undefined,
    processedVideoPublicId: analysis.processedVideoPublicId ?? undefined,
    localOriginalVideoUrl: analysis.localOriginalVideoUrl ?? null,
    localProcessedVideoUrl: analysis.localProcessedVideoUrl ?? null,
    videoProvider: analysis.provider,
    cloudinaryUploadOk: analysis.cloudinaryUploadOk,
    savedToDatabase: analysis.savedToDatabase,
    visualAnalysisCompleted: analysis.visualAnalysisCompleted ?? true,
    analysisReliable: analysis.analysisReliable ?? true,
    qualityMessage: analysis.qualityMessage ?? null,
    modelSource: analysis.modelSource ?? null,
    modelVersion: analysis.modelVersion ?? null,
    modelKind: analysis.modelKind ?? null,
    detectedClass: analysis.detectedClass ?? null,
    detectedClassLabel: analysis.detectedClassLabel ?? null,
    classProbabilitiesByName: analysis.classProbabilitiesByName ?? null,
    classProbabilitiesList: analysis.classProbabilitiesList ?? null,
    alteredProbability: analysis.alteredProbability ?? null,
    orientationText: analysis.orientationText ?? null,
    featureHighlights: analysis.featureHighlights ?? null,
    gaitFeatures: analysis.gaitFeatures ?? null,
    modelMacroF1: analysis.modelMacroF1 ?? null,
    probabilityParkinson: analysis.probabilityParkinson ?? null,
    probabilityNormal: analysis.probabilityNormal ?? null,
    riskLevel: analysis.riskLevel ?? null,
    confidence: analysis.confidence ?? null,
    experimentalClassification: analysis.experimentalClassification ?? false,
    modelVariant: analysis.modelVariant ?? null,
    modelWarnings: analysis.modelWarnings ?? [],
    confidenceMeaning: analysis.confidenceMeaning ?? null,
    modelDisclaimer: analysis.modelDisclaimer ?? null,
    modelUsed: analysis.modelUsed ?? false,
    modelUsedForVideo: analysis.modelUsedForVideo ?? analysis.modelUsed ?? false,
    predictionLabel: analysis.predictionLabel,
    predictionConfidence: analysis.predictionConfidence ?? null,
    classProbabilities: analysis.classProbabilities ?? null,
    predictionBasis: analysis.predictionBasis ?? null,
    modelPredictionMessage: analysis.modelPredictionMessage ?? null,
    decisionSource: analysis.decisionSource,
    modelControlProbability: analysis.modelControlProbability ?? null,
    modelParkinsonProbability: analysis.modelParkinsonProbability ?? null,
    modelAvailable: analysis.modelAvailable,
    modelMetricsAvailable: analysis.modelMetricsAvailable,
    modelAccuracy: analysis.modelAccuracy ?? null,
    modelPrecision: analysis.modelPrecision ?? null,
    modelRecall: analysis.modelRecall ?? null,
    modelF1Score: analysis.modelF1Score ?? null,
    modelWarning: analysis.modelWarning ?? null,
    validationMethod: analysis.validationMethod ?? null,
    modelSamples: analysis.modelSamples ?? null,
    modelControlSamples: analysis.modelControlSamples ?? null,
    modelParkinsonSamples: analysis.modelParkinsonSamples ?? null,
    modelTrainSize: analysis.modelTrainSize ?? null,
    modelTestSize: analysis.modelTestSize ?? null,
    modelMessage: analysis.modelMessage,
    poseQuality: analysis.poseQuality,
    poseDetectionRate: analysis.poseDetectionRate ?? null,
    framesAnalyzed: analysis.framesAnalyzed ?? 0,
    framesWithPose: analysis.framesWithPose ?? 0,
    videoMetrics: analysis.videoMetrics,
    rawSignals: analysis.signals ?? [],
    visualSignals: analysis.visualSignals ?? analysis.signals ?? [],
    signalEmptyMessage: observedSignalResult.emptyMessage,
    signalDecision: observedSignalResult.signalDecision,
    analysisWarnings: warnings,
    recommendations: dedupeStrings(evaluation.recommendations ?? []),
    signals: observedSignalResult.signals.map((signal) => ({
      name: signal.title,
      relevance: toSignalSeverity(observedSeverityToAlertLabel(signal.severity)),
      description: mapSignalDescription(signal.title, signal.description),
      source: signal.source,
      reason: signal.reason,
    })),
    parameters: [
      {
        name: "Cuerpo detectado en el video",
        value:
          analysis.poseDetectionRate === null || analysis.poseDetectionRate === undefined
            ? "Sin dato"
            : `${Math.round(analysis.poseDetectionRate * 100)}%`,
        state: "Seguimiento visual del cuerpo durante el video",
      },
      {
        name: "Momentos analizados",
        value: String(analysis.framesAnalyzed ?? 0),
        state: `${analysis.framesWithPose ?? 0} momentos con seguimiento correcto`,
      },
      {
        name: "Velocidad de marcha",
        value: metricLabel(analysis.videoMetrics?.walkingSpeed),
        state: "Medición orientativa del desplazamiento observado",
      },
      {
        name: "Asimetría",
        value: metricLabel(analysis.videoMetrics?.asymmetryIndex),
        state: "Diferencia lateral observada",
      },
      {
        name: "Ritmo de la marcha",
        value: metricLabel(analysis.videoMetrics?.cadence),
        state: "Medición usada solo como apoyo si el movimiento fue estable",
      },
    ],
    conditions: [parkinsonCondition],
  };
}
