import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";

export type PerClassMetric = {
  precision: number | null;
  recall: number | null;
  f1: number | null;
  support: number | null;
  sensitivity?: number | null;
  specificity?: number | null;
  rocAucOvr?: number | null;
};

export type ModelMetrics = {
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1Score: number | null;
  macroF1?: number | null;
  balancedAccuracy?: number | null;
  confusionMatrix?: unknown;
  classNames?: string[] | null;
  perClass?: Record<string, PerClassMetric> | null;
  samples?: number | null;
  controlSamples?: number | null;
  parkinsonSamples?: number | null;
  videosPerClass?: Record<string, number> | null;
  validationMethod?: string | null;
  trainSize?: number | null;
  testSize?: number | null;
  controlTrain?: number | null;
  parkinsonTrain?: number | null;
  controlTest?: number | null;
  parkinsonTest?: number | null;
  warning?: string | null;
  modelKind: "deep_multiclass" | "video_binary" | "legacy_tabular" | "none";
};

export type ModelStatusDetails = ModelMetrics & {
  modelAvailable: boolean;
  metricsAvailable: boolean;
};

function projectPath(...segments: string[]) {
  return path.join(/* turbopackIgnore: true */ process.cwd(), ...segments);
}

function deepMetricPath() {
  return projectPath("models", "gait_deep", "gait_deep_cv_metrics.json");
}

function videoMetricPath() {
  return projectPath("models", "video_parkinson", "video_parkinson_metrics.json");
}

function legacyMetricPath() {
  return projectPath("ml", "models", "parkinson_model_metrics.json");
}

function hasDeepModel() {
  return (
    existsSync(projectPath("models", "gait_deep", "gait_deep_model.pt")) &&
    existsSync(projectPath("models", "gait_deep", "gait_deep_config.json")) &&
    existsSync(projectPath("models", "gait_deep", "gait_deep_feature_scaler.json"))
  );
}

function hasVideoTrainedModel() {
  return (
    existsSync(projectPath("models", "video_parkinson", "video_parkinson_model.joblib")) &&
    existsSync(projectPath("models", "video_parkinson", "video_parkinson_scaler.joblib")) &&
    existsSync(projectPath("models", "video_parkinson", "video_parkinson_feature_schema.json"))
  );
}

function numberOrNull(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function stringOrNull(value: unknown) {
  return typeof value === "string" && value.trim() ? value : null;
}

export function hasTrainedModel() {
  return (
    hasDeepModel() ||
    hasVideoTrainedModel() ||
    existsSync(projectPath("ml", "models", "parkinson_model.pkl")) ||
    existsSync(projectPath("ml", "models", "parkinson_model.joblib"))
  );
}

function metricPath(): { path: string; kind: ModelMetrics["modelKind"] } | null {
  if (hasDeepModel() && existsSync(deepMetricPath())) {
    return { path: deepMetricPath(), kind: "deep_multiclass" };
  }
  if (existsSync(videoMetricPath())) {
    return { path: videoMetricPath(), kind: "video_binary" };
  }
  if (existsSync(legacyMetricPath())) {
    return { path: legacyMetricPath(), kind: "legacy_tabular" };
  }
  return null;
}

export function hasModelMetrics() {
  return metricPath() !== null;
}

function parsePerClass(raw: unknown): Record<string, PerClassMetric> | null {
  if (!raw || typeof raw !== "object") return null;
  const out: Record<string, PerClassMetric> = {};
  for (const [name, value] of Object.entries(raw as Record<string, unknown>)) {
    if (!value || typeof value !== "object") continue;
    const v = value as Record<string, unknown>;
    out[name] = {
      precision: numberOrNull(v.precision),
      recall: numberOrNull(v.recall),
      f1: numberOrNull(v.f1 ?? v["f1-score"]),
      support: numberOrNull(v.support),
      sensitivity: numberOrNull(v.sensitivity),
      specificity: numberOrNull(v.specificity),
      rocAucOvr: numberOrNull(v.roc_auc_ovr),
    };
  }
  return Object.keys(out).length ? out : null;
}

export async function readModelMetrics(): Promise<ModelMetrics | null> {
  const target = metricPath();
  if (!target) return null;

  const raw = await readFile(target.path, "utf8");
  const parsed = JSON.parse(raw) as Record<string, unknown>;
  const oof = (parsed.oof ?? {}) as Record<string, unknown>;

  return {
    modelKind: target.kind,
    accuracy: numberOrNull(parsed.accuracy ?? oof.accuracy),
    precision: numberOrNull(parsed.precision ?? oof.macro_precision),
    recall: numberOrNull(parsed.recall ?? oof.macro_recall),
    f1Score: numberOrNull(parsed.f1_score ?? parsed.f1Score ?? oof.macro_f1),
    macroF1: numberOrNull(parsed.macro_f1 ?? oof.macro_f1),
    balancedAccuracy: numberOrNull(parsed.balanced_accuracy ?? oof.balanced_accuracy),
    confusionMatrix:
      parsed.confusion_matrix ?? parsed.confusionMatrix ?? oof.confusion_matrix,
    classNames: Array.isArray(parsed.class_names)
      ? (parsed.class_names as string[])
      : null,
    perClass: parsePerClass(oof.per_class ?? parsed.per_class),
    samples: numberOrNull(parsed.samples ?? parsed.n_samples),
    controlSamples: numberOrNull(parsed.control_samples ?? parsed.controlSamples),
    parkinsonSamples: numberOrNull(
      parsed.parkinson_samples ?? parsed.parkinsonSamples
    ),
    videosPerClass:
      parsed.videos_per_class && typeof parsed.videos_per_class === "object"
        ? (parsed.videos_per_class as Record<string, number>)
        : null,
    validationMethod: stringOrNull(
      parsed.validation_method ?? parsed.validationMethod
    ),
    trainSize: numberOrNull(parsed.train_size ?? parsed.trainSize),
    testSize: numberOrNull(parsed.test_size ?? parsed.testSize),
    controlTrain: numberOrNull(parsed.control_train ?? parsed.controlTrain),
    parkinsonTrain: numberOrNull(parsed.parkinson_train ?? parsed.parkinsonTrain),
    controlTest: numberOrNull(parsed.control_test ?? parsed.controlTest),
    parkinsonTest: numberOrNull(parsed.parkinson_test ?? parsed.parkinsonTest),
    warning: stringOrNull(parsed.warning),
  };
}

export async function getModelStatusDetails(): Promise<ModelStatusDetails> {
  const modelAvailable = hasTrainedModel();
  const metrics = await readModelMetrics();

  return {
    modelAvailable,
    metricsAvailable: Boolean(metrics),
    modelKind: metrics?.modelKind ?? (modelAvailable ? "video_binary" : "none"),
    accuracy: metrics?.accuracy ?? null,
    precision: metrics?.precision ?? null,
    recall: metrics?.recall ?? null,
    f1Score: metrics?.f1Score ?? null,
    macroF1: metrics?.macroF1 ?? null,
    balancedAccuracy: metrics?.balancedAccuracy ?? null,
    confusionMatrix: metrics?.confusionMatrix,
    classNames: metrics?.classNames ?? null,
    perClass: metrics?.perClass ?? null,
    samples: metrics?.samples ?? null,
    controlSamples: metrics?.controlSamples ?? null,
    parkinsonSamples: metrics?.parkinsonSamples ?? null,
    videosPerClass: metrics?.videosPerClass ?? null,
    validationMethod: metrics?.validationMethod ?? null,
    trainSize: metrics?.trainSize ?? null,
    testSize: metrics?.testSize ?? null,
    controlTrain: metrics?.controlTrain ?? null,
    parkinsonTrain: metrics?.parkinsonTrain ?? null,
    controlTest: metrics?.controlTest ?? null,
    parkinsonTest: metrics?.parkinsonTest ?? null,
    warning: metrics?.warning ?? null,
  };
}
