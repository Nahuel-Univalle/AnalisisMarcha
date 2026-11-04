import type { StoredPattern } from "@/lib/analysis/conditionLabels";

export type AlertLevel = "Bajo" | "Medio" | "Alto";
export type SignalSeverity = AlertLevel | "Info";

export type User = {
  name: string;
  age?: string | number | null;
  email: string;
  role: "USER" | "ADMIN";
};

export type VideoMeta = {
  name: string;
  size: string;
  type: string;
  duration: string;
};

export type Signal = {
  name: string;
  relevance: SignalSeverity;
  description: string;
  source?: "model" | "feature" | "fallback";
  reason?: string;
};

export type ConditionEvaluation = {
  condition: string;
  status: string;
  description: string;
};

export type GaitParameter = {
  name: string;
  value: string;
  state: string;
};

/** Advertencia de calidad o de clase emitida por el script de inferencia. */
export type ModelWarning = {
  code: string;
  severity: "alta" | "media" | "info";
  message: string;
};

export type AnalysisResult = {
  id?: string;
  alertLevel: AlertLevel;
  title?: string;
  summary: string;
  signals: Signal[];
  parameters: GaitParameter[];
  conditions: ConditionEvaluation[];
  recommendations?: string[];
  videoMetrics?: Record<string, number | null>;
  annotatedVideoUrl?: string;
  originalVideoUrl?: string;
  originalVideoPublicId?: string;
  processedVideoUrl?: string;
  processedVideoPublicId?: string;
  localOriginalVideoUrl?: string | null;
  localProcessedVideoUrl?: string | null;
  videoProvider?: "local" | "cloudinary" | string;
  cloudinaryUploadOk?: boolean;
  savedToDatabase?: boolean;
  videoRecordId?: string | null;
  poseQuality?: string;
  poseDetectionRate?: number | null;
  framesAnalyzed?: number;
  framesWithPose?: number;
  analysisWarnings?: string[];
  rawSignals?: string[];
  visualSignals?: string[];
  visualAnalysisCompleted?: boolean;
  signalEmptyMessage?: string | null;
  signalDecision?: string | null;
  modelSource?: string | null;
  modelVersion?: string | null;
  modelKind?: string | null;
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
  probabilityParkinson?: number | null;
  probabilityNormal?: number | null;
  riskLevel?: string | null;
  confidence?: number | null;
  /** Resultado del modelo experimental de 4 clases (Dataset V4). */
  experimentalClassification?: boolean;
  modelVariant?: string | null;
  modelWarnings?: ModelWarning[];
  confidenceMeaning?: string | null;
  modelDisclaimer?: string | null;
  predictionLabel?:
    | "possible_parkinson"
    | "possible_esclerosis_multiple"
    | "possible_riesgo_caida"
    | "control"
    | "rule_based_orientation"
    | string
    | null;
  predictionConfidence?: number | null;
  modelAvailable?: boolean;
  modelMetricsAvailable?: boolean;
  modelAccuracy?: number | null;
  modelPrecision?: number | null;
  modelRecall?: number | null;
  modelF1Score?: number | null;
  modelMessage?: string;
  modelUsed?: boolean;
  classProbabilities?: {
    control: number | null;
    parkinson: number | null;
  } | null;
  modelUsedForVideo?: boolean;
  predictionBasis?: string | null;
  modelPredictionMessage?: string | null;
  decisionSource?: "modelo" | "observaciones" | string;
  modelControlProbability?: number | null;
  modelParkinsonProbability?: number | null;
  modelWarning?: string | null;
  validationMethod?: string | null;
  modelSamples?: number | null;
  modelControlSamples?: number | null;
  modelParkinsonSamples?: number | null;
  modelTrainSize?: number | null;
  modelTestSize?: number | null;
};

export type SavedReport = {
  id: string;
  date: string;
  alertLevel: AlertLevel;
  title: string;
  summary?: string;
  analysisType?: string;
  pattern?: string;
  patternStatus?: string;
  /** Clase del modelo (4 clases) o "no_concluyente"; null si el registro no permite saberlo. */
  patternKey?: StoredPattern | null;
  modelConfidence?: number | null;
  userEmail?: string;
  userName?: string;
  originalVideoUrl?: string;
  processedVideoUrl?: string;
  localOriginalVideoUrl?: string | null;
  localProcessedVideoUrl?: string | null;
  videoProvider?: string;
  videoRecordId?: string | null;
  analysisId?: string | null;
};

