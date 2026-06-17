import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";

export type ModelMetrics = {
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1Score: number | null;
  confusionMatrix?: unknown;
  samples?: number | null;
  controlSamples?: number | null;
  parkinsonSamples?: number | null;
  validationMethod?: string | null;
  trainSize?: number | null;
  testSize?: number | null;
  controlTrain?: number | null;
  parkinsonTrain?: number | null;
  controlTest?: number | null;
  parkinsonTest?: number | null;
  warning?: string | null;
};

export type ModelStatusDetails = ModelMetrics & {
  modelAvailable: boolean;
  metricsAvailable: boolean;
};

function projectPath(...segments: string[]) {
  return path.join(/* turbopackIgnore: true */ process.cwd(), ...segments);
}

function videoMetricPath() {
  return projectPath("models", "video_parkinson", "video_parkinson_metrics.json");
}

function legacyMetricPath() {
  return projectPath("ml", "models", "parkinson_model_metrics.json");
}

function metricPath() {
  return existsSync(videoMetricPath()) ? videoMetricPath() : legacyMetricPath();
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
    hasVideoTrainedModel() ||
    existsSync(projectPath("ml", "models", "parkinson_model.pkl")) ||
    existsSync(projectPath("ml", "models", "parkinson_model.joblib"))
  );
}

export function hasModelMetrics() {
  return existsSync(metricPath());
}

export async function readModelMetrics(): Promise<ModelMetrics | null> {
  if (!hasModelMetrics()) return null;

  const raw = await readFile(metricPath(), "utf8");
  const parsed = JSON.parse(raw) as Record<string, unknown>;

  return {
    accuracy: numberOrNull(parsed.accuracy),
    precision: numberOrNull(parsed.precision),
    recall: numberOrNull(parsed.recall),
    f1Score: numberOrNull(parsed.f1_score ?? parsed.f1Score),
    confusionMatrix: parsed.confusion_matrix ?? parsed.confusionMatrix,
    samples: numberOrNull(parsed.samples),
    controlSamples: numberOrNull(parsed.control_samples ?? parsed.controlSamples),
    parkinsonSamples: numberOrNull(
      parsed.parkinson_samples ?? parsed.parkinsonSamples
    ),
    validationMethod: stringOrNull(
      parsed.validation_method ?? parsed.validationMethod
    ),
    trainSize: numberOrNull(parsed.train_size ?? parsed.trainSize),
    testSize: numberOrNull(parsed.test_size ?? parsed.testSize),
    controlTrain: numberOrNull(parsed.control_train ?? parsed.controlTrain),
    parkinsonTrain: numberOrNull(
      parsed.parkinson_train ?? parsed.parkinsonTrain
    ),
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
    accuracy: metrics?.accuracy ?? null,
    precision: metrics?.precision ?? null,
    recall: metrics?.recall ?? null,
    f1Score: metrics?.f1Score ?? null,
    confusionMatrix: metrics?.confusionMatrix,
    samples: metrics?.samples ?? null,
    controlSamples: metrics?.controlSamples ?? null,
    parkinsonSamples: metrics?.parkinsonSamples ?? null,
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
