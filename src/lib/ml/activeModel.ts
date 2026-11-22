import { existsSync } from "node:fs";
import path from "node:path";

// Accepted by the V5-CR integration tests. GAIT_MODEL_VERSION=v4 is an explicit
// rollback; inference never switches models automatically after an error.
export const DEFAULT_GAIT_MODEL: "v4" | "v5cr" = "v5cr";

const MODELS = {
  v4: {
    version: "gait_deep_v4exp_M1_BN_recalibrated_candidate_v1",
    directory: "gait_deep_v4exp_bn_candidate_v1",
    predictor: "14_predict_deep_video_v4exp.py",
    weightsSha256: "7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d",
    accuracy: 0.851, macroF1: 0.744, trainingVideos: 117, trainingSubjects: 67,
  },
  v5cr: {
    version: "gait_deep_v5exp_V5CR_7e9ed60965fe",
    directory: "gait_deep_v5cr",
    predictor: "15_predict_deep_video_v5cr.py",
    weightsSha256: "7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade",
    accuracy: 0.8598, macroF1: 0.7852, trainingVideos: 117, trainingSubjects: 67,
  },
} as const;

export function activeGaitModel() {
  const key = process.env.GAIT_MODEL_VERSION ?? DEFAULT_GAIT_MODEL;
  if (key !== "v4" && key !== "v5cr") throw new Error("GAIT_MODEL_VERSION debe ser v4 o v5cr");
  return { key, ...MODELS[key] };
}

export function activeGaitModelArtifactPaths() {
  const model = activeGaitModel();
  const suffixes = [".pt", "_config.json", "_feature_scaler.json", "_label_map.json"];
  const files = suffixes.map(suffix => path.join(/* turbopackIgnore: true */ process.cwd(), "models", model.directory, `${model.version}${suffix}`));
  if (model.key === "v5cr") files.push(path.join(/* turbopackIgnore: true */ process.cwd(), "models", model.directory, "deployment_manifest.json"));
  return files;
}

export function hasActiveGaitModel() {
  return activeGaitModelArtifactPaths().every(file => existsSync(file));
}
