import type { VideoGaitMetrics } from "@/lib/analysis/gaitEvaluation";

export type ObservedSignalSeverity = "info" | "bajo" | "medio" | "alto";
export type ObservedSignalSource = "model" | "feature" | "fallback";

export type RuleSignalInput = {
  name: string;
  relevance: string;
  description: string;
};

export type ObservedSignal = {
  title: string;
  description: string;
  severity: ObservedSignalSeverity;
  source: ObservedSignalSource;
  reason: string;
};

export type ObservedSignalInput = {
  modelSource?: string | null;
  probabilityParkinson?: number | null;
  probabilityNormal?: number | null;
  riskLevel?: string | null;
  confidence?: number | null;
  poseDetectionRate?: number | null;
  framesAnalyzed?: number | null;
  framesWithPose?: number | null;
  videoMetrics?: VideoGaitMetrics | null;
  ruleSignals?: RuleSignalInput[];
};

export type ObservedSignalResult = {
  signals: ObservedSignal[];
  emptyMessage: string | null;
  signalDecision: string;
};

const VIDEO_MODEL_SOURCE = "video_parkinson_model";
const LOW_RISK_EMPTY_MESSAGE =
  "No se detectaron señales relevantes en la marcha analizada.";
const QUALITY_EMPTY_MESSAGE =
  "Calidad del video insuficiente para interpretar señales de marcha con confianza.";
const NO_EVIDENCE_EMPTY_MESSAGE =
  "No se detectaron señales relevantes asociadas a patrones de Parkinson en este análisis.";

function finiteNumber(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function normalizeRiskLevel(value: string | null | undefined) {
  const normalized = (value ?? "").trim().toLowerCase();
  if (normalized === "alto" || normalized === "high") return "alto";
  if (normalized === "medio" || normalized === "medium") return "medio";
  if (normalized === "bajo" || normalized === "low") return "bajo";
  return null;
}

function severityFromRule(value: string): ObservedSignalSeverity {
  const normalized = value.trim().toLowerCase();
  if (normalized === "alto" || normalized === "high") return "alto";
  if (normalized === "medio" || normalized === "medium") return "medio";
  if (normalized === "bajo" || normalized === "low") return "bajo";
  return "info";
}

function capSeverity(
  severity: ObservedSignalSeverity,
  maxSeverity: ObservedSignalSeverity
) {
  const order: Record<ObservedSignalSeverity, number> = {
    info: 0,
    bajo: 1,
    medio: 2,
    alto: 3,
  };

  return order[severity] <= order[maxSeverity] ? severity : maxSeverity;
}

function hasAnyMetric(metrics: VideoGaitMetrics | null | undefined) {
  if (!metrics) return false;
  return Object.values(metrics).some((value) => finiteNumber(value) !== null);
}

function hasFeatureSupport(signalName: string, metrics: VideoGaitMetrics | null | undefined) {
  if (!metrics) return false;

  const normalizedName = signalName.toLowerCase();

  if (normalizedName.includes("marcha lenta")) {
    return finiteNumber(metrics.walkingSpeed) !== null;
  }

  if (normalizedName.includes("asimetr")) {
    return finiteNumber(metrics.asymmetryIndex) !== null;
  }

  if (normalizedName.includes("ritmo") || normalizedName.includes("paso")) {
    return (
      finiteNumber(metrics.cadence) !== null ||
      finiteNumber(metrics.stepRegularity) !== null ||
      finiteNumber(metrics.rigidityScore) !== null
    );
  }

  if (normalizedName.includes("brazo")) {
    return (
      finiteNumber(metrics.armSwingScore) !== null ||
      finiteNumber(metrics.armSwingAsymmetry) !== null
    );
  }

  if (normalizedName.includes("estabilidad")) {
    return (
      finiteNumber(metrics.doubleSupportRatio) !== null ||
      finiteNumber(metrics.stepRegularity) !== null
    );
  }

  if (normalizedName.includes("postura")) {
    return finiteNumber(metrics.postureInclinationDeg) !== null;
  }

  return hasAnyMetric(metrics);
}

function videoQualityIsInsufficient(input: ObservedSignalInput) {
  const poseDetectionRate = finiteNumber(input.poseDetectionRate);
  const framesAnalyzed = finiteNumber(input.framesAnalyzed);
  const framesWithPose = finiteNumber(input.framesWithPose);
  const poseRatio =
    framesAnalyzed !== null && framesAnalyzed > 0 && framesWithPose !== null
      ? framesWithPose / framesAnalyzed
      : null;

  return (
    (poseDetectionRate !== null && poseDetectionRate < 0.55) ||
    (poseRatio !== null && poseRatio < 0.45) ||
    (framesAnalyzed !== null && framesAnalyzed > 0 && framesAnalyzed < 30) ||
    (framesWithPose !== null && framesWithPose > 0 && framesWithPose < 18)
  );
}

function maxSeverityForModel(
  modelSource: string | null | undefined,
  probabilityParkinson: number | null,
  riskLevel: string | null
): ObservedSignalSeverity | null {
  if (modelSource !== VIDEO_MODEL_SOURCE) return null;
  if (riskLevel === "bajo" || (probabilityParkinson !== null && probabilityParkinson < 0.4)) {
    return null;
  }
  if (
    riskLevel === "medio" ||
    (probabilityParkinson !== null && probabilityParkinson <= 0.7)
  ) {
    return "medio";
  }
  return probabilityParkinson !== null && probabilityParkinson > 0.7 ? "alto" : "medio";
}

export function observedSeverityToAlertLabel(severity: ObservedSignalSeverity) {
  if (severity === "alto") return "Alto";
  if (severity === "medio") return "Medio";
  if (severity === "bajo") return "Bajo";
  return "Info";
}

export function buildObservedSignals(input: ObservedSignalInput): ObservedSignalResult {
  const probabilityParkinson = finiteNumber(input.probabilityParkinson);
  const probabilityNormal = finiteNumber(input.probabilityNormal);
  const riskLevel = normalizeRiskLevel(input.riskLevel);
  const ruleSignals = input.ruleSignals ?? [];

  if (videoQualityIsInsufficient(input)) {
    return {
      signals: [],
      emptyMessage: QUALITY_EMPTY_MESSAGE,
      signalDecision: "No clinical signals because video quality is insufficient",
    };
  }

  const modelMaxSeverity = maxSeverityForModel(
    input.modelSource,
    probabilityParkinson,
    riskLevel
  );

  if (input.modelSource === VIDEO_MODEL_SOURCE && modelMaxSeverity === null) {
    const normalConfidence =
      probabilityNormal !== null && probabilityNormal >= 0.8
        ? " Modelo con alta coincidencia normal."
        : "";

    return {
      signals: [],
      emptyMessage: `${LOW_RISK_EMPTY_MESSAGE}${normalConfidence}`,
      signalDecision: "No high signals because model risk is low",
    };
  }

  const maxSeverity = modelMaxSeverity ?? "alto";
  const source: ObservedSignalSource =
    input.modelSource === VIDEO_MODEL_SOURCE ? "model" : "fallback";
  const signals = ruleSignals
    .filter((signal) => hasFeatureSupport(signal.name, input.videoMetrics))
    .map<ObservedSignal>((signal) => {
      const originalSeverity = severityFromRule(signal.relevance);
      const severity = capSeverity(originalSeverity, maxSeverity);
      return {
        title: signal.name,
        description: signal.description,
        severity,
        source,
        reason:
          input.modelSource === VIDEO_MODEL_SOURCE
            ? `Feature respaldada por métricas reales y limitada por riesgo global ${riskLevel ?? "sin dato"}.`
            : "Señal generada por reglas de respaldo al no estar disponible el modelo de video.",
      };
    })
    .filter((signal) => signal.severity !== "info");

  if (signals.length === 0) {
    return {
      signals,
      emptyMessage: NO_EVIDENCE_EMPTY_MESSAGE,
      signalDecision: "No signals because feature evidence is insufficient after model gating",
    };
  }

  return {
    signals,
    emptyMessage: null,
    signalDecision:
      input.modelSource === VIDEO_MODEL_SOURCE
        ? "Signals generated from feature evidence and capped by video model risk"
        : "Signals generated from fallback gait rules",
  };
}
