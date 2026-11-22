import { existsSync } from "node:fs";
import path from "node:path";

function projectPath(...segments: string[]) {
  return path.join(/* turbopackIgnore: true */ process.cwd(), ...segments);
}

// Modelo de producción (Paso 16): clasificación experimental de 4 clases.
// Debe coincidir con DEEP_GAIT_V4EXP_VERSION de /api/analysis/video.
const EXPERIMENTAL_V4_MODEL_VERSION =
  "gait_deep_v4exp_M1_BN_recalibrated_candidate_v1";

// OOF del modelo en producción (Paso 18: BatchNorm recalibrada por fold, validación
// agrupada por sujeto 5x5). Debe coincidir con OOF de 14_predict_deep_video_v4exp.py.
export const EXPERIMENTAL_V4_OOF_METRICS = {
  modelVersion: EXPERIMENTAL_V4_MODEL_VERSION,
  weightsSha256: "7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d",
  accuracy: 0.851,
  macroF1: 0.744,
  trainingVideos: 117,
  trainingSubjects: 67,
};

export function hasExperimentalV4Model() {
  return [".pt", "_config.json", "_feature_scaler.json", "_label_map.json"].every(
    (suffix) =>
      existsSync(
        projectPath("models", "gait_deep_v4exp_bn_candidate_v1", `${EXPERIMENTAL_V4_MODEL_VERSION}${suffix}`)
      )
  );
}
