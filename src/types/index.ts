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

export type AnalysisResult = {
  id?: string;
  alertLevel: AlertLevel;
  title?: string;
  summary: string;
  signals: Signal[];
  parameters: GaitParameter[];
  conditions: ConditionEvaluation[];
  recommendations?: string[];
  datasetWarnings?: string[];
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
  probabilityParkinson?: number | null;
  probabilityNormal?: number | null;
  riskLevel?: string | null;
  confidence?: number | null;
  predictionLabel?: "possible_parkinson" | "rule_based_orientation" | string | null;
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

