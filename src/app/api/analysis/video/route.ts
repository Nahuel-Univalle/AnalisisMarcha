import { spawn, spawnSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import {
  copyFile,
  mkdir,
  readFile,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import path from "node:path";
import { AlertLevel as PrismaAlertLevel, VideoStatus } from "@prisma/client";
import { NextRequest } from "next/server";
import {
  evaluateGaitAgainstParkinsonDataset,
  GaitEvaluationResult,
  VideoGaitMetrics,
} from "@/lib/analysis/gaitEvaluation";
import {
  buildObservedSignals,
  observedSeverityToAlertLabel,
} from "@/lib/analysis/observedSignals";
import {
  alteredProbabilityFrom,
  associatedConditionText,
  detectedClassFrom,
  gaitClassInfo,
  GaitClassKey,
  normalizeClassProbabilities,
  sortedClassProbabilities,
} from "@/lib/analysis/conditionLabels";
import {
  CloudinaryVideoUpload,
  CloudinaryVideoUploadOk,
  deleteCloudinaryVideo,
  uploadVideoToCloudinary,
} from "@/lib/cloudinary";
import { getModelStatusDetails } from "@/lib/ml/modelMetrics";
import { requireUser } from "@/lib/auth/guards";
import { getSessionUser } from "@/lib/auth/session";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";

const ALLOWED_VIDEO_TYPES = new Set([
  "video/mp4",
  "video/webm",
  "video/quicktime",
]);
const MAX_VIDEO_BYTES = 120 * 1024 * 1024;
const DEEP_GAIT_MODEL_SOURCE = "gait_deep_model";
const VIDEO_PARKINSON_MODEL_SOURCE = "video_parkinson_model";
const FALLBACK_GAIT_RULES_SOURCE = "fallback_gait_rules";
const MODEL_SOURCES_WITH_MODEL = new Set([
  DEEP_GAIT_MODEL_SOURCE,
  VIDEO_PARKINSON_MODEL_SOURCE,
]);
const PYTHON_TIMEOUT_MS = 90_000;
const PYTHON_SCRIPT_NOT_FOUND =
  "No se encontró python_analysis/analyze_video.py. Verifique que el módulo Python esté instalado.";
const PYTHON_EXECUTABLE_NOT_FOUND =
  "No se encontró un ejecutable Python válido. Instale Python 3.11, recree .venv311 e instale requirements.txt.";
const PYTHON_ANALYSIS_FAILED =
  "No se pudo completar el análisis de movimiento. Revise que el video sea claro y vuelva a intentarlo.";
const CLOUDINARY_FALLBACK_WARNING =
  "El análisis se completó, pero no se pudo guardar el video en la nube. Se mostrará una versión temporal.";
const SENSOR_VIDEO_MODEL_MESSAGE =
  "El modelo de referencia usa datos de sensores de marcha. El video actual se evaluó mediante análisis visual.";
const VIDEO_FEATURE_PREDICTION_FAILED =
  "No se pudieron extraer suficientes métricas visuales compatibles para aplicar el modelo.";
const DEEP_GAIT_V4EXP_VERSION =
  "gait_deep_v4exp_protocolV2_M1_20261029_162234_d7323250d26f";
const EXPERIMENTAL_MODEL_UNAVAILABLE =
  "No fue posible realizar la clasificación experimental de patrones de marcha: el modelo de 4 clases no está disponible en este momento. No se utilizó ningún otro modelo en su lugar. Intente nuevamente más tarde.";

function projectPath(...segments: string[]) {
  return path.join(/* turbopackIgnore: true */ process.cwd(), ...segments);
}

function findPythonScript() {
  return projectPath("python_analysis", "analyze_video.py");
}

// Modelo experimental de 4 clases (Dataset V4, M1, protocolo V2). Su script
// reproduce el preprocesamiento de entrenamiento; 13_predict_deep_video.py NO
// debe usarse con este modelo (usa otro pipeline de entrada).
function findDeepGaitPredictionScript() {
  return projectPath(
    "scripts",
    "video_training",
    "deep",
    "14_predict_deep_video_v4exp.py"
  );
}

function deepGaitModelArtifactPaths() {
  return [
    `${DEEP_GAIT_V4EXP_VERSION}.pt`,
    `${DEEP_GAIT_V4EXP_VERSION}_config.json`,
    `${DEEP_GAIT_V4EXP_VERSION}_feature_scaler.json`,
    `${DEEP_GAIT_V4EXP_VERSION}_label_map.json`,
  ].map((fileName) => projectPath("models", "gait_deep_v4exp", fileName));
}

function hasDeepGaitModelArtifacts() {
  return deepGaitModelArtifactPaths().every((filePath) => existsSync(filePath));
}

function normalizeExecutable(value: string) {
  return value.trim().replace(/^["']|["']$/g, "");
}

function canRunPython(command: string) {
  const result = spawnSync(command, ["--version"], {
    encoding: "utf8",
    timeout: 3000,
    windowsHide: true,
  });

  return !result.error && result.status === 0;
}

function findPythonCommand() {
  const candidates: string[] = [];
  const configuredPython = process.env.PYTHON_ANALYSIS_EXECUTABLE;

  if (configuredPython) candidates.push(normalizeExecutable(configuredPython));
  if (process.env.PYTHON_BIN) {
    candidates.push(normalizeExecutable(process.env.PYTHON_BIN));
  }

  const venv311 = projectPath(".venv311", "Scripts", "python.exe");
  const venv = projectPath(".venv", "Scripts", "python.exe");

  if (existsSync(venv311)) candidates.push(venv311);
  if (existsSync(venv)) candidates.push(venv);
  candidates.push(process.platform === "win32" ? "python" : "python3");

  return candidates.find(canRunPython) ?? null;
}

async function parseJsonFile(filePath: string) {
  const content = await readFile(filePath, "utf8");
  return JSON.parse(content) as Record<string, unknown>;
}

function numberFrom(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

function reliableCadence(value: number | null) {
  if (value === null) return null;
  return value >= 40 && value <= 220 ? value : null;
}

function normalizePythonMetrics(payload: Record<string, unknown>): VideoGaitMetrics {
  const cadence = numberFrom(payload.estimated_cadence_steps_per_min);

  return {
    walkingSpeed: numberFrom(payload.gait_speed_proxy),
    asymmetryIndex: numberFrom(
      payload.leg_asymmetry_visual ?? payload.left_right_asymmetry
    ),
    cadence: reliableCadence(cadence),
    doubleSupportRatio: numberFrom(payload.estimated_double_support_proxy),
    armSwingScore: numberFrom(payload.arm_swing_left ?? payload.arm_swing_right),
    armSwingAsymmetry: numberFrom(payload.arm_swing_asymmetry),
    postureInclinationDeg: numberFrom(payload.posture_inclination),
    rigidityScore: numberFrom(payload.gait_variability ?? payload.movement_variability),
    stepRegularity: numberFrom(
      payload.movement_regularity ?? payload.trunk_stability_score
    ),
  };
}

function debugMetricValue(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function buildDebugMetrics(
  pythonOutput: Record<string, unknown>,
  videoMetrics: VideoGaitMetrics
) {
  return {
    walkingSpeed: videoMetrics.walkingSpeed ?? null,
    cadence: videoMetrics.cadence ?? null,
    stepLength: debugMetricValue(pythonOutput.ankle_distance_mean),
    armSwing:
      videoMetrics.armSwingScore ??
      debugMetricValue(pythonOutput.arm_swing_left) ??
      debugMetricValue(pythonOutput.arm_swing_right),
    symmetry:
      debugMetricValue(pythonOutput.step_symmetry_visual) ??
      videoMetrics.asymmetryIndex ??
      null,
    gaitVariability:
      debugMetricValue(pythonOutput.gait_variability) ??
      debugMetricValue(pythonOutput.movement_variability),
  };
}

function metricAuditIssues(metrics: Record<string, number | null>) {
  const ranges: Record<string, { min: number; max: number; unit: string }> = {
    walkingSpeed: { min: 0, max: 3, unit: "proxy visual normalizado/seg" },
    cadence: { min: 40, max: 220, unit: "pasos/min" },
    stepLength: { min: 0, max: 1, unit: "proxy visual normalizado" },
    armSwing: { min: 0, max: 1, unit: "proxy visual normalizado" },
    symmetry: { min: 0, max: 1, unit: "índice 0-1" },
    gaitVariability: { min: 0, max: 1, unit: "proxy visual normalizado" },
  };
  type MetricAuditIssue = {
    metric: string;
    issue: "missing" | "not_finite" | "outside_expected_human_range";
    value: number | null;
    expectedRange?: number[];
    unit?: string;
  };

  return Object.entries(metrics).flatMap<MetricAuditIssue>(([name, value]) => {
    if (value === null) {
      return [{ metric: name, issue: "missing", value, unit: ranges[name]?.unit }];
    }

    if (!Number.isFinite(value)) {
      return [{ metric: name, issue: "not_finite", value, unit: ranges[name]?.unit }];
    }

    const range = ranges[name];
    if (range && (value < range.min || value > range.max)) {
      return [
        {
          metric: name,
          issue: "outside_expected_human_range",
          value,
          expectedRange: [range.min, range.max],
          unit: range.unit,
        },
      ];
    }

    return [];
  });
}

async function writeDebugLastAnalysis(payload: unknown) {
  const debugPath = projectPath("tmp", "debug_last_analysis.json");
  await mkdir(path.dirname(debugPath), { recursive: true });
  await writeFile(debugPath, JSON.stringify(payload, null, 2), "utf8");
}

async function hasNonEmptyFile(filePath: string) {
  try {
    const fileStat = await stat(filePath);
    return fileStat.size > 0;
  } catch {
    return false;
  }
}

function qualityLabel(rate: number | null) {
  if (rate === null) return "Sin dato";
  if (rate < 0.4) return "Baja";
  if (rate < 0.7) return "Media";
  return "Alta";
}

function runPythonAnalysis({
  videoPath,
  outputJsonPath,
  outputVideoPath,
}: {
  videoPath: string;
  outputJsonPath: string;
  outputVideoPath: string;
}) {
  return new Promise<Record<string, unknown>>((resolve, reject) => {
    const scriptPath = findPythonScript();
    if (!existsSync(scriptPath)) {
      reject(new Error(PYTHON_SCRIPT_NOT_FOUND));
      return;
    }

    const pythonCommand = findPythonCommand();
    if (!pythonCommand) {
      reject(new Error(PYTHON_EXECUTABLE_NOT_FOUND));
      return;
    }

    const child = spawn(
      pythonCommand,
      [
        scriptPath,
        "--video",
        videoPath,
        "--output-json",
        outputJsonPath,
        "--output-video",
        outputVideoPath,
      ],
      {
        cwd: projectPath(),
        windowsHide: true,
      }
    );

    let stderr = "";
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      reject(
        new Error(
          "El análisis de video superó el tiempo máximo. Intente con un video más corto o de menor resolución."
        )
      );
    }, PYTHON_TIMEOUT_MS);

    child.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    child.on("error", (error) => {
      clearTimeout(timeout);
      reject(error);
    });

    child.on("close", async (code) => {
      clearTimeout(timeout);

      if (existsSync(outputJsonPath)) {
        try {
          const parsed = await parseJsonFile(outputJsonPath);
          if (parsed.success === false) {
            reject(new Error(String(parsed.error || PYTHON_ANALYSIS_FAILED)));
            return;
          }

          resolve(parsed);
          return;
        } catch {
          // Continue with process status handling below.
        }
      }

      if (code !== 0) {
        reject(new Error(stderr.trim() || PYTHON_ANALYSIS_FAILED));
        return;
      }

      reject(new Error(PYTHON_ANALYSIS_FAILED));
    });
  });
}

function unavailableVideoPrediction(message = VIDEO_FEATURE_PREDICTION_FAILED) {
  return {
    modelSource: FALLBACK_GAIT_RULES_SOURCE,
    modelUsed: false,
    modelUsedForVideo: false,
    predictionConfidence: null,
    message,
  };
}

function parsePredictionStdout(stdout: string) {
  const trimmed = stdout.trim();
  if (!trimmed) throw new Error("empty prediction output");

  try {
    return JSON.parse(trimmed) as Record<string, unknown>;
  } catch {
    const jsonLine = trimmed
      .split(/\r?\n/)
      .reverse()
      .find((line) => line.trim().startsWith("{"));

    if (!jsonLine) throw new Error("prediction output did not include JSON");
    return JSON.parse(jsonLine) as Record<string, unknown>;
  }
}

function runDeepGaitPrediction(videoPath: string, predictionJsonPath: string) {
  return new Promise<Record<string, unknown> | null>((resolve) => {
    const scriptPath = findDeepGaitPredictionScript();
    const pythonCommand = findPythonCommand();

    if (!existsSync(scriptPath) || !pythonCommand || !hasDeepGaitModelArtifacts()) {
      resolve(null);
      return;
    }

    const child = spawn(
      pythonCommand,
      [
        scriptPath,
        "--video",
        videoPath,
        "--output-json",
        predictionJsonPath,
      ],
      { cwd: projectPath(), windowsHide: true }
    );

    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      resolve(null);
    }, SPRINT4_TIMEOUT_MS);

    child.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    child.stderr.on("data", (data) => {
      stderr += data.toString();
    });
    child.on("error", () => {
      clearTimeout(timeout);
      resolve(null);
    });
    child.on("close", () => {
      clearTimeout(timeout);
      try {
        const parsed = parsePredictionStdout(stdout);
        resolve({
          ...parsed,
          modelSource: parsed.modelSource ?? DEEP_GAIT_MODEL_SOURCE,
        });
      } catch {
        console.error("DEEP_GAIT_MODEL_ERROR", stderr.trim());
        resolve(null);
      }
    });
  });
}

// Clasificación experimental de 4 clases. Si falla, NO se recurre al modelo
// binario histórico ni a reglas: se devuelve un fallo controlado y la ruta
// responde con un error explícito (salvo pose insuficiente, que sigue el flujo
// existente de "análisis no concluyente").
async function runVideoFeaturePrediction(videoPath: string, predictionJsonPath: string) {
  const deepPrediction = await runDeepGaitPrediction(videoPath, predictionJsonPath);
  if (deepPrediction && deepPrediction.modelUsed) {
    return deepPrediction;
  }
  console.error(
    "EXPERIMENTAL_GAIT_MODEL_FAILED",
    deepPrediction && typeof deepPrediction.message === "string"
      ? deepPrediction.message
      : "sin respuesta del script de inferencia"
  );
  return {
    ...unavailableVideoPrediction(EXPERIMENTAL_MODEL_UNAVAILABLE),
    failureKind:
      deepPrediction && typeof deepPrediction.failureKind === "string"
        ? deepPrediction.failureKind
        : "model_unavailable",
  };
}

function safeFileStem(name: string) {
  const stem = path.parse(name).name || "video";
  return stem
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function formString(formData: FormData, field: string) {
  const value = formData.get(field);
  return typeof value === "string" ? value.trim() : "";
}

function toPrismaAlertLevel(level: string): PrismaAlertLevel {
  if (level === "ALTO") return PrismaAlertLevel.ALTO;
  if (level === "MEDIO") return PrismaAlertLevel.MEDIO;
  return PrismaAlertLevel.BAJO;
}

function probabilityFrom(
  classProbabilities: unknown,
  label: "control" | "parkinson"
) {
  if (
    typeof classProbabilities !== "object" ||
    classProbabilities === null ||
    !(label in classProbabilities)
  ) {
    return null;
  }

  return numberFrom((classProbabilities as Record<string, unknown>)[label]);
}

function riskLevelFromProbability(parkinsonProbability: number | null) {
  if (parkinsonProbability === null) return null;
  if (parkinsonProbability < 0.4) return "bajo";
  if (parkinsonProbability <= 0.7) return "medio";
  return "alto";
}

function riskLevelFromAlert(alertLevel: string) {
  if (alertLevel === "ALTO") return "alto";
  if (alertLevel === "MEDIO") return "medio";
  return "bajo";
}

function normalizeModelSource(videoPrediction: Record<string, unknown>) {
  const source = String(videoPrediction.modelSource ?? "");
  if (Boolean(videoPrediction.modelUsed) && MODEL_SOURCES_WITH_MODEL.has(source)) {
    return source;
  }
  return FALLBACK_GAIT_RULES_SOURCE;
}

function observedSeverityToApiLevel(severity: string): "BAJO" | "MEDIO" | "ALTO" {
  if (severity === "alto") return "ALTO";
  if (severity === "medio") return "MEDIO";
  return "BAJO";
}

function alteredAlertLevel(alteredProbability: number | null) {
  if (alteredProbability === null) return "BAJO";
  if (alteredProbability >= 0.7) return "ALTO";
  if (alteredProbability >= 0.5) return "MEDIO";
  return "BAJO";
}

type ModelDrivenEvaluation = GaitEvaluationResult & {
  decisionSource: "modelo" | "observaciones";
  modelControlProbability: number | null;
  modelParkinsonProbability: number | null;
  detectedCondition: GaitClassKey | null;
  detectedConditionLabel: string | null;
  alteredProbability: number | null;
  classProbabilitiesByName: Record<string, number> | null;
};

function buildModelDrivenEvaluation(
  evaluation: GaitEvaluationResult,
  videoPrediction: Record<string, unknown>
): ModelDrivenEvaluation {
  const source = String(videoPrediction.modelSource ?? "");
  const modelUsed =
    Boolean(videoPrediction.modelUsed) && MODEL_SOURCES_WITH_MODEL.has(source);

  const probsByName = normalizeClassProbabilities(videoPrediction.classProbabilities);
  const controlProbability =
    probsByName?.normal ?? probabilityFrom(videoPrediction.classProbabilities, "control");
  const parkinsonProbability =
    probsByName?.parkinson ??
    probabilityFrom(videoPrediction.classProbabilities, "parkinson");

  const base: ModelDrivenEvaluation = {
    ...evaluation,
    decisionSource: "observaciones",
    modelControlProbability: controlProbability,
    modelParkinsonProbability: parkinsonProbability,
    detectedCondition: null,
    detectedConditionLabel: null,
    alteredProbability: null,
    classProbabilitiesByName: probsByName
      ? (Object.fromEntries(
          Object.entries(probsByName).filter(([, v]) => typeof v === "number")
        ) as Record<string, number>)
      : null,
  };

  if (!modelUsed || !probsByName) {
    return base;
  }

  const detected =
    (typeof videoPrediction.detectedClass === "string" &&
      (videoPrediction.detectedClass as GaitClassKey)) ||
    detectedClassFrom(probsByName);
  const info = gaitClassInfo(detected);
  const isNormal = detected === "normal";
  const altered =
    alteredProbabilityFrom(probsByName) ??
    (parkinsonProbability !== null ? parkinsonProbability : null);

  const orientationText =
    typeof videoPrediction.orientationText === "string" &&
    videoPrediction.orientationText.trim()
      ? (videoPrediction.orientationText as string)
      : `${info.patternPhrase} ${info.description}`;

  return {
    ...base,
    alertLevel: isNormal ? "BAJO" : alteredAlertLevel(altered),
    possibleCondition: isNormal
      ? "sin_alerta"
      : detected === "parkinson"
        ? "posible_parkinson"
        : "posible_alteracion_marcha",
    title: isNormal
      ? "Resultado orientativo sin alerta principal en la marcha"
      : `Resultado orientativo: ${info.label}`,
    summary: isNormal
      ? "El modelo identificó patrones de marcha dentro de lo esperado. Las observaciones se presentan solo como información complementaria y no constituyen un diagnóstico."
      : `${orientationText} Este resultado no confirma una enfermedad y requiere valoración por un profesional de salud.`,
    decisionSource: "modelo",
    detectedCondition: detected,
    detectedConditionLabel: info.label,
    alteredProbability: altered,
  };
}

function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined) return "Sin dato";
  return `${Math.round(value * 1000) / 1000}`;
}

function buildStoredParameters({
  poseDetectionRate,
  framesAnalyzed,
  framesWithPose,
  videoMetrics,
}: {
  poseDetectionRate: number | null;
  framesAnalyzed: number;
  framesWithPose: number;
  videoMetrics: VideoGaitMetrics;
}) {
  return [
    {
      name: "Cuerpo detectado en el video",
      value:
        poseDetectionRate === null
          ? "Sin dato"
          : `${Math.round(poseDetectionRate * 100)}%`,
      state: "Seguimiento visual del cuerpo durante el video",
    },
    {
      name: "Momentos analizados",
      value: String(framesAnalyzed),
      state: `${framesWithPose} momentos con seguimiento correcto`,
    },
    {
      name: "Velocidad de marcha",
      value: formatMetric(videoMetrics.walkingSpeed),
      state: "Medición orientativa del desplazamiento observado",
    },
    {
      name: "Asimetría",
      value: formatMetric(videoMetrics.asymmetryIndex),
      state: "Diferencia lateral observada",
    },
    {
      name: "Ritmo de la marcha",
      value: formatMetric(videoMetrics.cadence),
      state: "Medición usada solo como apoyo si el movimiento fue estable",
    },
  ];
}

type SaveAnalysisInput = {
  userEmail: string;
  video: File;
  provider: "cloudinary" | "local-fallback";
  originalUpload: CloudinaryVideoUploadOk | null;
  processedUpload: CloudinaryVideoUploadOk | null;
  localOriginalVideoUrl: string | null;
  localProcessedVideoUrl: string | null;
  evaluation: GaitEvaluationResult & {
    detectedCondition?: GaitClassKey | null;
  };
  poseDetectionRate: number | null;
  framesAnalyzed: number;
  framesWithPose: number;
  videoMetrics: VideoGaitMetrics;
};

async function saveAnalysisToDatabase({
  userEmail,
  video,
  provider,
  originalUpload,
  processedUpload,
  localOriginalVideoUrl,
  localProcessedVideoUrl,
  evaluation,
  poseDetectionRate,
  framesAnalyzed,
  framesWithPose,
  videoMetrics,
}: SaveAnalysisInput) {
  if (!userEmail) return null;

  const user = await prisma.user.findUnique({
    where: { email: userEmail.toLowerCase() },
    select: { id: true },
  });

  if (!user) return null;

  const effectiveOriginalUrl =
    originalUpload?.secureUrl ?? localOriginalVideoUrl ?? null;
  const effectiveProcessedUrl =
    processedUpload?.secureUrl ?? localProcessedVideoUrl ?? null;
  const parameters = buildStoredParameters({
    poseDetectionRate,
    framesAnalyzed,
    framesWithPose,
    videoMetrics,
  });

  const videoRecord = await prisma.videoMarcha.create({
    data: {
      userId: user.id,
      originalName: video.name,
      storedName: originalUpload?.publicId ?? null,
      url: effectiveOriginalUrl,
      mimeType: video.type,
      sizeBytes: video.size,
      validationStatus: VideoStatus.FINALIZADO,
      originalVideoUrl: effectiveOriginalUrl,
      originalVideoPublicId: originalUpload?.publicId ?? null,
      processedVideoUrl: effectiveProcessedUrl,
      processedVideoPublicId: processedUpload?.publicId ?? null,
      localOriginalVideoUrl,
      localProcessedVideoUrl,
      videoProvider: provider,
      originalFileName: video.name,
      processedFileName: processedUpload?.publicId
        ? `${processedUpload.publicId}.${processedUpload.format ?? "mp4"}`
        : localProcessedVideoUrl
          ? path.basename(localProcessedVideoUrl)
          : null,
      cloudinaryOriginalBytes: originalUpload?.bytes ?? null,
      cloudinaryProcessedBytes: processedUpload?.bytes ?? null,
      cloudinaryOriginalFormat: originalUpload?.format ?? null,
      cloudinaryProcessedFormat: processedUpload?.format ?? null,
    },
    select: { id: true },
  });

  const gaitAnalysis = await prisma.gaitAnalysis.create({
    data: {
      userId: user.id,
      videoId: videoRecord.id,
      alert: toPrismaAlertLevel(evaluation.alertLevel),
      summary: evaluation.summary,
      parameters: { create: parameters },
      signals: {
        create: evaluation.detectedSignals.map((signal) => ({
          name: signal.name,
          relevance: toPrismaAlertLevel(signal.relevance),
          description: signal.description,
        })),
      },
      conditions: {
        create: [
          {
            // Texto dependiente de la CLASE REALMENTE DETECTADA por el modelo
            // (normal / parkinson / esclerosis_multiple / riesgo_caida).
            condition:
              evaluation.possibleCondition === "sin_alerta"
                ? "Sin alerta específica"
                : associatedConditionText(evaluation.detectedCondition),
            status:
              evaluation.possibleCondition === "sin_alerta"
                ? "Sin alerta específica"
                : "Alerta orientativa",
            description: evaluation.summary,
          },
        ],
      },
    },
    select: { id: true },
  });

  return {
    videoId: videoRecord.id,
    analysisId: gaitAnalysis.id,
  };
}

function uploadFailureDetails(...uploads: CloudinaryVideoUpload[]) {
  return uploads
    .filter((upload) => !upload.ok)
    .map((upload) => `${upload.errorCode || "cloudinary"}: ${upload.errorMessage}`)
    .join(" | ");
}

// ---------------------------------------------------------------------------
//  Sprint 4 (Iteraciones 7 y 8): pipeline de dataset sobre el video SUBIDO.
//  Reutiliza los scripts de terminal (no se duplica lógica) y es NO FATAL:
//  si algo falla, el análisis principal (Sprint 3 + métricas) igual responde 200.
// ---------------------------------------------------------------------------
const SPRINT4_VALID_CATEGORIES = new Set([
  "control",
  "parkinson",
  "multiple_sclerosis",
  "fall_risk",
]);
const SPRINT4_POSE_SAMPLES = "300";
const SPRINT4_TIMEOUT_MS = 150_000;

function scriptPath(name: string) {
  return projectPath("scripts", name);
}

function normalizeDatasetCategory(value: unknown) {
  const raw = typeof value === "string" ? value.trim().toLowerCase() : "";
  return SPRINT4_VALID_CATEGORIES.has(raw) ? raw : "control";
}

function toProjectRelative(absPath: string) {
  return path.relative(projectPath(), absPath).split(path.sep).join("/");
}

function runPythonScript(
  pythonCommand: string,
  args: string[],
  timeoutMs = SPRINT4_TIMEOUT_MS
) {
  return new Promise<{ code: number | null; stdout: string; stderr: string }>(
    (resolve) => {
      const child = spawn(pythonCommand, args, {
        cwd: projectPath(),
        windowsHide: true,
      });
      let stdout = "";
      let stderr = "";
      const timeout = setTimeout(() => {
        child.kill("SIGTERM");
        resolve({ code: null, stdout, stderr: `${stderr}\n[timeout]` });
      }, timeoutMs);
      child.stdout.on("data", (data) => (stdout += data.toString()));
      child.stderr.on("data", (data) => (stderr += data.toString()));
      child.on("error", (error) => {
        clearTimeout(timeout);
        resolve({ code: null, stdout, stderr: `${stderr}${error}` });
      });
      child.on("close", (code) => {
        clearTimeout(timeout);
        resolve({ code, stdout, stderr });
      });
    }
  );
}

async function readOverallStatus(jsonPath: string) {
  try {
    const parsed = await parseJsonFile(jsonPath);
    return typeof parsed.overall_status === "string"
      ? parsed.overall_status
      : null;
  } catch {
    return null;
  }
}

async function runSprint4Pipeline({
  pythonCommand,
  analysisId,
  uploadedVideoPath,
  fps,
  category,
}: {
  pythonCommand: string;
  analysisId: string;
  uploadedVideoPath: string;
  fps: number;
  category: string;
}) {
  const evidence = {
    ran: false,
    category,
    iteration7: {
      status: null as string | null,
      poseLandmarksFile: null as string | null,
      gaitBasicParametersFile: null as string | null,
      validationReportFile: null as string | null,
    },
    iteration8: {
      status: null as string | null,
      gaitFeaturesDatasetFile: null as string | null,
      trainFile: null as string | null,
      validationFile: null as string | null,
      testFile: null as string | null,
      validationReportFile: null as string | null,
    },
    error: null as string | null,
  };

  try {
    const analysisDir = projectPath("outputs", "analysis", analysisId);
    await mkdir(analysisDir, { recursive: true });

    const poseCsv = path.join(analysisDir, "pose_landmarks.csv");
    const perFrameCsv = path.join(analysisDir, "basic_gait_params.csv");
    const gaitParamsCsv = path.join(analysisDir, "gait_basic_parameters.csv");
    const it7Report = path.join(analysisDir, "iteration7_validation_report.json");
    const it8Report = path.join(analysisDir, "iteration8_validation_report.json");

    const globalDataset = projectPath("outputs", "gait_features_dataset.csv");
    const trainCsv = projectPath("data", "train.csv");
    const valCsv = projectPath("data", "validation.csv");
    const testCsv = projectPath("data", "test.csv");
    const fpsArg = String(fps > 0 ? fps : 30);

    // --- Iteración 7: landmarks -> parámetros -> validación de coordenadas ---
    const exportRes = await runPythonScript(pythonCommand, [
      scriptPath("export_pose_csv.py"),
      "--video", uploadedVideoPath,
      "--output", poseCsv,
      "--samples", SPRINT4_POSE_SAMPLES,
    ]);
    if (!existsSync(poseCsv)) {
      evidence.error = `export_pose_csv no generó landmarks (code ${exportRes.code}). ${exportRes.stderr.slice(-300)}`;
      return evidence;
    }
    evidence.iteration7.poseLandmarksFile = toProjectRelative(poseCsv);

    await runPythonScript(pythonCommand, [
      scriptPath("calculate_basic_params.py"),
      "--input", poseCsv,
      "--output", gaitParamsCsv,
      "--perframe-output", perFrameCsv,
      "--video-id", analysisId,
      "--source-file", uploadedVideoPath,
      "--fps", fpsArg,
      "--category", category,
    ]);
    if (existsSync(gaitParamsCsv)) {
      evidence.iteration7.gaitBasicParametersFile = toProjectRelative(gaitParamsCsv);
    }

    await runPythonScript(pythonCommand, [
      scriptPath("validate_iteration7.py"),
      "--input", poseCsv,
      "--output", it7Report,
    ]);
    if (existsSync(it7Report)) {
      evidence.iteration7.validationReportFile = toProjectRelative(it7Report);
      evidence.iteration7.status = await readOverallStatus(it7Report);
    }

    // --- Iteración 8: upsert al dataset global + particiones + validación ---
    if (existsSync(gaitParamsCsv)) {
      await runPythonScript(pythonCommand, [
        scriptPath("prepare_iteration8_dataset.py"),
        "--input", gaitParamsCsv,
        "--global-output", globalDataset,
        "--train", trainCsv,
        "--validation", valCsv,
        "--test", testCsv,
      ]);
    }
    if (existsSync(globalDataset)) {
      evidence.iteration8.gaitFeaturesDatasetFile = toProjectRelative(globalDataset);
      evidence.iteration8.trainFile = existsSync(trainCsv) ? toProjectRelative(trainCsv) : null;
      evidence.iteration8.validationFile = existsSync(valCsv) ? toProjectRelative(valCsv) : null;
      evidence.iteration8.testFile = existsSync(testCsv) ? toProjectRelative(testCsv) : null;

      await runPythonScript(pythonCommand, [
        scriptPath("validate_iteration8.py"),
        "--input", globalDataset,
        "--output", it8Report,
      ]);
      if (existsSync(it8Report)) {
        evidence.iteration8.validationReportFile = toProjectRelative(it8Report);
        evidence.iteration8.status = await readOverallStatus(it8Report);
      }
    }

    evidence.ran = true;
    return evidence;
  } catch (error) {
    evidence.error = error instanceof Error ? error.message : String(error);
    return evidence;
  }
}

export async function POST(request: NextRequest) {
  let tempVideoPath: string | null = null;
  let outputJsonPath: string | null = null;
  let videoPredictionJsonPath: string | null = null;
  let outputVideoPath: string | null = null;
  let localOriginalPublicPath: string | null = null;
  let preserveLocalFallback = false;
  let cloudinaryUploadOk = false;

  try {
    const sessionUser = await getSessionUser();

    if (!sessionUser) {
      return Response.json(
        {
          success: false,
          message: "Debes iniciar sesiÃ³n para guardar y analizar videos.",
          analysis: null,
        },
        { status: 401 }
      );
    }

    if (sessionUser.role === "ADMIN") {
      return Response.json(
        {
          success: false,
          message: "Los administradores no pueden crear analisis de paciente.",
          analysis: null,
        },
        { status: 403 }
      );
    }

    // Verifica en la base de datos que la identidad existe y su rol real,
    // antes de cualquier procesamiento, subida o escritura.
    const authResult = await requireUser();

    if ("error" in authResult) {
      return authResult.error;
    }

    if (authResult.user.role === "ADMIN") {
      return Response.json(
        {
          success: false,
          message: "Los administradores no pueden crear analisis de paciente.",
          analysis: null,
        },
        { status: 403 }
      );
    }

    const contentType = request.headers.get("content-type") ?? "";
    if (!contentType.includes("multipart/form-data")) {
      return Response.json(
        {
          success: false,
          message:
            "Debes enviar un formulario con un archivo de video para iniciar el análisis.",
        },
        { status: 400 }
      );
    }

    const formData = await request.formData();
    const video = formData.get("video");

    if (!(video instanceof File)) {
      return Response.json(
        {
          success: false,
          message: "Debes enviar un archivo de video para iniciar el análisis.",
        },
        { status: 400 }
      );
    }

    if (!ALLOWED_VIDEO_TYPES.has(video.type)) {
      return Response.json(
        {
          success: false,
          message: "El archivo debe ser un video válido.",
        },
        { status: 400 }
      );
    }

    if (video.size > MAX_VIDEO_BYTES) {
      return Response.json(
        {
          success: false,
          message:
            "El video es demasiado pesado. Intente subir uno más corto o comprimido.",
        },
        { status: 413 }
      );
    }

    // Categoría del dataset (Sprint 4 Iteración 8). Solo etiqueta organizativa, no
    // diagnóstico. Por defecto "control" si no llega o no es válida.
    const datasetCategory = normalizeDatasetCategory(formData.get("category"));

    if (!existsSync(findPythonScript())) {
      return Response.json(
        {
          success: false,
          message: PYTHON_SCRIPT_NOT_FOUND,
        },
        { status: 500 }
      );
    }

    if (!findPythonCommand()) {
      return Response.json(
        {
          success: false,
          message: PYTHON_EXECUTABLE_NOT_FOUND,
        },
        { status: 500 }
      );
    }

    const analysisId = randomUUID();
    const extension = path.extname(video.name) || ".mp4";
    const originalStem = `${safeFileStem(video.name)}-${analysisId}`;
    const tempUploadDir = projectPath("tmp", "uploads");
    const resultDir = projectPath("tmp", "results");
    const processedDir = projectPath("public", "processed-videos");
    const localOriginalDir = projectPath("public", "uploads-temp");

    await Promise.all([
      mkdir(tempUploadDir, { recursive: true }),
      mkdir(resultDir, { recursive: true }),
      mkdir(processedDir, { recursive: true }),
      mkdir(localOriginalDir, { recursive: true }),
    ]);

    tempVideoPath = path.join(tempUploadDir, `analysis_${analysisId}${extension}`);
    outputJsonPath = path.join(resultDir, `analysis_${analysisId}.json`);
    videoPredictionJsonPath = path.join(
      resultDir,
      `analysis_${analysisId}_video_model.json`
    );
    const outputVideoFile = `analysis_${analysisId}_pose.mp4`;
    outputVideoPath = path.join(processedDir, outputVideoFile);

    await writeFile(tempVideoPath, Buffer.from(await video.arrayBuffer()));

    let pythonOutput: Record<string, unknown>;
    try {
      pythonOutput = await runPythonAnalysis({
        videoPath: tempVideoPath,
        outputJsonPath,
        outputVideoPath,
      });
    } catch (error) {
      console.error("PYTHON_VIDEO_ANALYSIS_ERROR", error);
      const detail = error instanceof Error ? error.message : "";
      // Distingue entrada inválida (video dañado / no es un video / vacío) de un
      // fallo interno: en el primer caso es un 400 con mensaje claro para el usuario.
      const badInput =
        /no se pudo abrir el video|no es un video|dañad|corrupt|invalid|moov atom|could not|formato/i.test(
          detail
        );
      return Response.json(
        {
          success: false,
          message: badInput
            ? "El archivo no es un video válido o está dañado. Suba un video MP4, MOV o WEBM con una persona caminando de cuerpo completo."
            : PYTHON_ANALYSIS_FAILED,
          analysis: null,
        },
        { status: badInput ? 400 : 500 }
      );
    }

    if (!(await hasNonEmptyFile(outputJsonPath))) {
      return Response.json(
        {
          success: false,
          message: PYTHON_ANALYSIS_FAILED,
          analysis: null,
        },
        { status: 500 }
      );
    }

    if (!(await hasNonEmptyFile(outputVideoPath))) {
      return Response.json(
        {
          success: false,
          message: PYTHON_ANALYSIS_FAILED,
          analysis: null,
        },
        { status: 500 }
      );
    }

    // Sprint 4 (Iteraciones 7 y 8) sobre el VIDEO SUBIDO (no fatal: si falla, el
    // análisis principal igual responde 200). tempVideoPath es el video del usuario.
    const sprint4Evidence = await runSprint4Pipeline({
      pythonCommand: findPythonCommand() as string,
      analysisId,
      uploadedVideoPath: tempVideoPath,
      fps: numberFrom(pythonOutput.fps) ?? 30,
      category: datasetCategory,
    });
    console.log(
      "SPRINT4_DATASET_EVIDENCE",
      JSON.stringify({
        analysisId,
        category: datasetCategory,
        iteration7Status: sprint4Evidence.iteration7.status,
        iteration8Status: sprint4Evidence.iteration8.status,
        datasetFile: sprint4Evidence.iteration8.gaitFeaturesDatasetFile,
        error: sprint4Evidence.error,
      })
    );

    const localProcessedVideoUrl = `/processed-videos/${outputVideoFile}`;
    const originalUpload = await uploadVideoToCloudinary(tempVideoPath, {
      folder: "originales",
      publicId: originalStem,
      tags: ["analisis-marcha", "original"],
    });
    const processedUpload = await uploadVideoToCloudinary(outputVideoPath, {
      folder: "procesados",
      publicId: `${originalStem}-pose`,
      tags: ["analisis-marcha", "procesado"],
    });

    cloudinaryUploadOk = originalUpload.ok && processedUpload.ok;
    const provider = cloudinaryUploadOk ? "cloudinary" : "local-fallback";
    let localOriginalVideoUrl: string | null = null;

    if (!cloudinaryUploadOk) {
      preserveLocalFallback = true;
      const localOriginalFile = `analysis_${analysisId}${extension}`;
      localOriginalPublicPath = path.join(localOriginalDir, localOriginalFile);
      await copyFile(tempVideoPath, localOriginalPublicPath);
      localOriginalVideoUrl = `/uploads-temp/${localOriginalFile}`;

      if (originalUpload.ok && !processedUpload.ok) {
        await deleteCloudinaryVideo(originalUpload.publicId);
      }

      console.error(
        "CLOUDINARY_VIDEO_UPLOAD_FALLBACK",
        uploadFailureDetails(originalUpload, processedUpload)
      );
    }

    const originalVideoUrl = cloudinaryUploadOk
      ? (originalUpload as CloudinaryVideoUploadOk).secureUrl
      : localOriginalVideoUrl;
    const processedVideoUrl = cloudinaryUploadOk
      ? (processedUpload as CloudinaryVideoUploadOk).secureUrl
      : localProcessedVideoUrl;
    const originalPublicId = cloudinaryUploadOk
      ? (originalUpload as CloudinaryVideoUploadOk).publicId
      : null;
    const processedPublicId = cloudinaryUploadOk
      ? (processedUpload as CloudinaryVideoUploadOk).publicId
      : null;
    const videoMetrics = normalizePythonMetrics(pythonOutput);
    const [evaluation, modelStatus, videoPrediction] = await Promise.all([
      evaluateGaitAgainstParkinsonDataset(videoMetrics),
      getModelStatusDetails(),
      runVideoFeaturePrediction(tempVideoPath, videoPredictionJsonPath),
    ]);

    // Fallo del modelo experimental: error controlado (sin modelo de respaldo).
    // La pose insuficiente NO es un fallo del modelo: sigue el flujo existente
    // de "análisis no concluyente" mediante el gate de calidad de más abajo.
    const experimentalFailureKind = videoPrediction.modelUsed
      ? null
      : String(videoPrediction.failureKind ?? "model_unavailable");
    if (experimentalFailureKind && experimentalFailureKind !== "pose_insufficient") {
      if (originalUpload.ok) await deleteCloudinaryVideo(originalUpload.publicId);
      if (processedUpload.ok) await deleteCloudinaryVideo(processedUpload.publicId);
      preserveLocalFallback = false;
      if (outputVideoPath) await rm(outputVideoPath, { force: true }).catch(() => undefined);
      return Response.json(
        {
          success: false,
          errorCode: "EXPERIMENTAL_MODEL_UNAVAILABLE",
          message: EXPERIMENTAL_MODEL_UNAVAILABLE,
          analysis: null,
        },
        { status: 503 }
      );
    }

    const finalEvaluation = buildModelDrivenEvaluation(evaluation, videoPrediction);
    const modelSource = normalizeModelSource(videoPrediction);
    const classProbabilitiesByName = finalEvaluation.classProbabilitiesByName;
    const detectedCondition = finalEvaluation.detectedCondition;
    const detectedConditionLabel = finalEvaluation.detectedConditionLabel;
    const classProbabilitiesList = sortedClassProbabilities(
      normalizeClassProbabilities(videoPrediction.classProbabilities)
    );
    const alteredProbability =
      finalEvaluation.alteredProbability ??
      alteredProbabilityFrom(
        normalizeClassProbabilities(videoPrediction.classProbabilities)
      );
    const featureHighlights = Array.isArray(videoPrediction.featureHighlights)
      ? videoPrediction.featureHighlights
      : [];
    const gaitFeatures =
      videoPrediction.gaitFeatures &&
      typeof videoPrediction.gaitFeatures === "object"
        ? (videoPrediction.gaitFeatures as Record<string, unknown>)
        : null;
    const orientationText =
      typeof videoPrediction.orientationText === "string"
        ? videoPrediction.orientationText
        : null;
    const probabilityParkinson =
      numberFrom(videoPrediction.probability_parkinson) ??
      finalEvaluation.modelParkinsonProbability;
    const probabilityNormal =
      numberFrom(videoPrediction.probability_normal) ??
      finalEvaluation.modelControlProbability;
    const riskLevel =
      (typeof videoPrediction.risk_level === "string"
        ? videoPrediction.risk_level
        : null) ??
      riskLevelFromProbability(alteredProbability ?? probabilityParkinson) ??
      riskLevelFromAlert(finalEvaluation.alertLevel);
    const confidence =
      numberFrom(videoPrediction.confidence) ??
      numberFrom(videoPrediction.predictionConfidence);
    const poseDetectionRate = numberFrom(pythonOutput.pose_detection_rate);
    const framesAnalyzed = Number(pythonOutput.frames_analyzed ?? 0);
    const framesWithPose = Number(pythonOutput.frames_with_pose ?? 0);

    // --- Gate de calidad de pose (obligatorio) --------------------------------
    // Si el video no contiene suficiente información corporal, NINGÚN modelo debe
    // devolver una predicción con falsa confianza. Se anula la clase detectada y
    // se marca el análisis como NO concluyente.
    const poseRatio =
      framesAnalyzed > 0 ? framesWithPose / framesAnalyzed : null;
    const poseQualityInsufficient =
      (poseDetectionRate !== null && poseDetectionRate < 0.45) ||
      (poseRatio !== null && poseRatio < 0.45) ||
      framesWithPose < 15 ||
      experimentalFailureKind === "pose_insufficient";
    const UNRELIABLE_MESSAGE =
      "El video no contiene información corporal suficiente para un análisis confiable. Suba un video con la persona de cuerpo completo, buena iluminación, cámara estable y varios pasos visibles.";
    const analysisReliable = !poseQualityInsufficient;

    const observedSignalResult = buildObservedSignals({
      modelSource,
      probabilityParkinson,
      probabilityNormal,
      alteredProbability,
      detectedClass: detectedCondition,
      riskLevel,
      confidence,
      poseDetectionRate,
      framesAnalyzed,
      framesWithPose,
      videoMetrics,
      ruleSignals: finalEvaluation.detectedSignals,
    });
    const modelAlignedEvaluation = {
      ...finalEvaluation,
      ...(analysisReliable
        ? {}
        : {
            alertLevel: "BAJO" as const,
            possibleCondition: "sin_alerta" as const,
            detectedCondition: null,
            detectedConditionLabel: null,
            title: "Análisis no concluyente por calidad del video",
            summary: UNRELIABLE_MESSAGE,
            decisionSource: "observaciones" as const,
          }),
      detectedSignals: analysisReliable
        ? observedSignalResult.signals
            .filter((signal) => signal.severity !== "info")
            .map((signal) => ({
              name: signal.title,
              relevance: observedSeverityToApiLevel(signal.severity),
              description: signal.description,
            }))
        : [],
    };

    // Valores "efectivos": si la calidad de pose es insuficiente se anulan la
    // clase, las probabilidades y la confianza para no mostrar un resultado
    // aparentemente válido.
    const effModelSource = analysisReliable ? modelSource : FALLBACK_GAIT_RULES_SOURCE;
    const effDetectedCondition = analysisReliable ? detectedCondition : null;
    const effDetectedConditionLabel = analysisReliable ? detectedConditionLabel : null;
    const effClassProbabilitiesByName = analysisReliable ? classProbabilitiesByName : null;
    const effClassProbabilitiesList = analysisReliable ? classProbabilitiesList : [];
    const effOrientationText = analysisReliable ? orientationText : UNRELIABLE_MESSAGE;
    const effAlteredProbability = analysisReliable ? alteredProbability : null;
    const effConfidence = analysisReliable ? confidence : null;
    const effProbabilityParkinson = analysisReliable ? probabilityParkinson : null;
    const effProbabilityNormal = analysisReliable ? probabilityNormal : null;
    const effRiskLevel = analysisReliable ? riskLevel : "bajo";
    const effModelUsed = analysisReliable && Boolean(videoPrediction.modelUsed);
    const rawCadence = numberFrom(pythonOutput.estimated_cadence_steps_per_min);
    const cadenceWarning =
      rawCadence !== null && reliableCadence(rawCadence) === null
        ? "Algunas mediciones del movimiento no fueron concluyentes. El resultado se basa principalmente en las señales más consistentes observadas en el video."
        : null;
    const warnings = dedupeStrings(
      [
        ...((pythonOutput.warnings as string[] | undefined) ?? []),
        ...modelAlignedEvaluation.datasetWarnings,
        cadenceWarning,
        cloudinaryUploadOk ? null : CLOUDINARY_FALLBACK_WARNING,
      ].filter((warning): warning is string => Boolean(warning))
    );

    let databaseRecord: { videoId: string; analysisId: string } | null = null;
    const databaseWarnings: string[] = [];
    const formUserEmail = formString(formData, "userEmail").toLowerCase();
    const userEmail = sessionUser.email;

    if (formUserEmail && formUserEmail !== sessionUser.email) {
      return Response.json(
        {
          success: false,
          message: "El video no pertenece al usuario autenticado.",
          analysis: null,
        },
        { status: 403 }
      );
    }

    try {
      databaseRecord = await saveAnalysisToDatabase({
        userEmail,
        video,
        provider,
        originalUpload: cloudinaryUploadOk
          ? (originalUpload as CloudinaryVideoUploadOk)
          : null,
        processedUpload: cloudinaryUploadOk
          ? (processedUpload as CloudinaryVideoUploadOk)
          : null,
        localOriginalVideoUrl,
        localProcessedVideoUrl: cloudinaryUploadOk ? null : localProcessedVideoUrl,
        evaluation: modelAlignedEvaluation,
        poseDetectionRate,
        framesAnalyzed,
        framesWithPose,
        videoMetrics,
      });

      if (userEmail && !databaseRecord) {
        databaseWarnings.push(
          "No se encontró el usuario para guardar el análisis en seguimiento."
        );
      }

      // Trazabilidad: qué modelo produjo este resultado.
      if (databaseRecord) {
        await prisma.systemLog
          .create({
            data: {
              userId: userEmail || null,
              action: "GAIT_ANALYSIS_MODEL",
              detail: JSON.stringify({
                analysisId: databaseRecord.analysisId,
                videoId: databaseRecord.videoId,
                modelSource: effModelSource,
                modelVersion:
                  typeof videoPrediction.modelVersion === "string"
                    ? videoPrediction.modelVersion
                    : null,
                detectedClass: effDetectedCondition,
                analysisReliable,
                poseDetectionRate,
                framesWithPose,
              }),
            },
          })
          .catch(() => undefined);
      }
    } catch (error) {
      console.error("VIDEO_ANALYSIS_DB_SAVE_ERROR", error);
      databaseWarnings.push(
        "El análisis se completó, pero no se pudo guardar en PostgreSQL."
      );
    }

    const allWarnings = dedupeStrings([...warnings, ...databaseWarnings]);
    const analysis = {
      id: databaseRecord?.analysisId ?? analysisId,
      videoRecordId: databaseRecord?.videoId ?? null,
      provider,
      cloudinaryUploadOk,
      originalVideoUrl,
      originalVideoPublicId: originalPublicId,
      processedVideoUrl,
      processedVideoPublicId: processedPublicId,
      localOriginalVideoUrl,
      localProcessedVideoUrl: cloudinaryUploadOk ? null : localProcessedVideoUrl,
      annotatedVideoUrl: processedVideoUrl,
      poseDetectionRate,
      poseQuality: qualityLabel(poseDetectionRate),
      framesAnalyzed,
      framesWithPose,
      metrics: pythonOutput,
      signals: (pythonOutput.signals as string[] | undefined) ?? [],
      warnings: allWarnings,
      videoMetrics,
      visualAnalysisCompleted: true,
      analysisReliable,
      qualityMessage: analysisReliable ? null : UNRELIABLE_MESSAGE,
      modelSource: effModelSource,
      modelVersion:
        analysisReliable && typeof videoPrediction.modelVersion === "string"
          ? videoPrediction.modelVersion
          : null,
      modelKind: modelStatus.modelKind,
      // Clasificación experimental (modelo V4): advertencias estructuradas y
      // textos de contexto. Se anulan si el análisis no es concluyente.
      experimentalClassification: effModelUsed && videoPrediction.experimental === true,
      modelVariant:
        typeof videoPrediction.modelVariant === "string" ? videoPrediction.modelVariant : null,
      modelWarnings:
        analysisReliable && Array.isArray(videoPrediction.warnings)
          ? videoPrediction.warnings
          : [],
      confidenceMeaning:
        typeof videoPrediction.confidenceMeaning === "string"
          ? videoPrediction.confidenceMeaning
          : null,
      modelDisclaimer:
        typeof videoPrediction.disclaimer === "string" ? videoPrediction.disclaimer : null,
      detectedClass: effDetectedCondition,
      detectedClassLabel: effDetectedConditionLabel,
      classProbabilitiesByName: effClassProbabilitiesByName,
      classProbabilitiesList: effClassProbabilitiesList,
      alteredProbability: effAlteredProbability,
      orientationText: effOrientationText,
      featureHighlights,
      gaitFeatures,
      probabilityParkinson: effProbabilityParkinson,
      probabilityNormal: effProbabilityNormal,
      riskLevel: effRiskLevel,
      confidence: effConfidence,
      modelMacroF1:
        numberFrom(videoPrediction.modelMacroF1) ??
        (modelStatus.metricsAvailable ? modelStatus.macroF1 ?? null : null),
      modelUsed: effModelUsed,
      modelUsedForVideo: effModelUsed && Boolean(videoPrediction.modelUsedForVideo ?? videoPrediction.modelUsed),
      predictionLabel:
        typeof videoPrediction.predictionLabel === "string"
          ? videoPrediction.predictionLabel
          : null,
      predictionConfidence: numberFrom(videoPrediction.predictionConfidence),
      classProbabilities:
        typeof videoPrediction.classProbabilities === "object" &&
        videoPrediction.classProbabilities !== null
          ? videoPrediction.classProbabilities
          : null,
      predictionBasis:
        typeof videoPrediction.predictionBasis === "string"
          ? videoPrediction.predictionBasis
          : null,
      modelPredictionMessage:
        typeof videoPrediction.message === "string"
          ? videoPrediction.message
          : Boolean(videoPrediction.modelUsed)
            ? null
            : SENSOR_VIDEO_MODEL_MESSAGE,
      modelAccuracy:
        numberFrom(videoPrediction.modelAccuracy) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.accuracy
          : null),
      modelPrecision:
        numberFrom(videoPrediction.modelPrecision) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.precision
          : null),
      modelRecall:
        numberFrom(videoPrediction.modelRecall) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.recall
          : null),
      modelF1Score:
        numberFrom(videoPrediction.modelF1Score) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.f1Score
          : null),
      modelWarning:
        (typeof videoPrediction.modelWarning === "string"
          ? videoPrediction.modelWarning
          : null) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.warning
          : null),
      validationMethod:
        (typeof videoPrediction.validationMethod === "string"
          ? videoPrediction.validationMethod
          : null) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.validationMethod
          : null),
      modelSamples:
        numberFrom(videoPrediction.modelSamples) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.samples
          : null),
      modelControlSamples:
        numberFrom(videoPrediction.modelControlSamples) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.controlSamples
          : null),
      modelParkinsonSamples:
        numberFrom(videoPrediction.modelParkinsonSamples) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.parkinsonSamples
          : null),
      modelTrainSize:
        numberFrom(videoPrediction.modelTrainSize) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.trainSize
          : null),
      modelTestSize:
        numberFrom(videoPrediction.modelTestSize) ??
        (modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? modelStatus.testSize
          : null),
      modelMetricsAvailable:
        modelStatus.modelAvailable && modelStatus.metricsAvailable,
      modelAvailable: modelStatus.modelAvailable,
      modelMessage:
        modelStatus.modelAvailable && modelStatus.metricsAvailable
          ? "Modelo inicial entrenado con datos de referencia."
          : modelStatus.modelAvailable
            ? "El modelo aún no tiene métricas de entrenamiento disponibles."
            : "Aún no existe modelo entrenado disponible.",
      evaluation: modelAlignedEvaluation,
      observedSignals: observedSignalResult.signals,
      signalEmptyMessage: observedSignalResult.emptyMessage,
      signalDecision: observedSignalResult.signalDecision,
      reasonForEachSignal: observedSignalResult.signals.map((signal) => ({
        title: signal.title,
        severity: observedSeverityToAlertLabel(signal.severity),
        reason: signal.reason,
      })),
      decisionSource: modelAlignedEvaluation.decisionSource,
      modelControlProbability: modelAlignedEvaluation.modelControlProbability,
      modelParkinsonProbability: modelAlignedEvaluation.modelParkinsonProbability,
      datasetWarnings: modelAlignedEvaluation.datasetWarnings,
      savedToDatabase: Boolean(databaseRecord),
      rawPythonOutput: pythonOutput,
    };
    const debugMetrics = buildDebugMetrics(pythonOutput, videoMetrics);
    const modelControlProbability = numberFrom(
      (analysis.classProbabilities as Record<string, unknown> | null)?.control
    );
    const modelParkinsonProbability = numberFrom(
      (analysis.classProbabilities as Record<string, unknown> | null)?.parkinson
    );
    const finalDecision =
      modelAlignedEvaluation.title;
    const debugPayload = {
      metrics: debugMetrics,
      metricAuditIssues: metricAuditIssues(debugMetrics),
      modelOutput: {
        modelSource: analysis.modelSource,
        modelVersion: analysis.modelVersion,
        analysisReliable: analysis.analysisReliable,
        detectedClass: analysis.detectedClass,
        modelUsed: analysis.modelUsed,
        modelUsedForVideo: analysis.modelUsedForVideo,
        predictionLabel: analysis.predictionLabel,
        predictionConfidence: analysis.predictionConfidence,
        controlProbability: modelControlProbability,
        parkinsonProbability: modelParkinsonProbability,
        riskLevel: analysis.riskLevel,
        predictionBasis: analysis.predictionBasis,
      },
      rulesTriggered: evaluation.detectedSignals.map((signal) => ({
        name: signal.name,
        relevance: signal.relevance,
        description: signal.description,
      })),
      pythonSignals: analysis.signals,
      iteration7: sprint4Evidence.iteration7,
      iteration8: sprint4Evidence.iteration8,
      datasetCategory: sprint4Evidence.category,
      comparison: {
        modelSuggestsParkinson: analysis.predictionLabel === "possible_parkinson",
        observationsSuggestParkinson:
          evaluation.possibleCondition === "posible_parkinson",
        evaluationPossibleCondition: modelAlignedEvaluation.possibleCondition,
        finalDecisionSource: modelAlignedEvaluation.decisionSource,
      },
      finalDecision,
      generatedSignals: observedSignalResult.signals,
      signalDecision: observedSignalResult.signalDecision,
      alertLevel: modelAlignedEvaluation.alertLevel,
    };

    await writeDebugLastAnalysis(debugPayload);
    console.log("GAIT_DEBUG_LAST_ANALYSIS", JSON.stringify(debugPayload));

    return Response.json({
      success: true,
      provider,
      cloudinaryUploadOk,
      originalVideoUrl,
      processedVideoUrl,
      annotatedVideoUrl: processedVideoUrl,
      localOriginalVideoUrl,
      localProcessedVideoUrl: cloudinaryUploadOk ? null : localProcessedVideoUrl,
      metrics: pythonOutput,
      signals: analysis.signals,
      warnings: allWarnings,
      poseDetectionRate,
      framesAnalyzed,
      framesWithPose,
      visualAnalysisCompleted: analysis.visualAnalysisCompleted,
      analysisReliable: analysis.analysisReliable,
      qualityMessage: analysis.qualityMessage,
      message: analysis.analysisReliable ? null : UNRELIABLE_MESSAGE,
      modelSource: analysis.modelSource,
      modelVersion: analysis.modelVersion,
      probabilityParkinson: analysis.probabilityParkinson,
      probabilityNormal: analysis.probabilityNormal,
      riskLevel: analysis.riskLevel,
      confidence: analysis.confidence,
      generatedSignals: analysis.observedSignals,
      signalEmptyMessage: analysis.signalEmptyMessage,
      signalDecision: analysis.signalDecision,
      reasonForEachSignal: analysis.reasonForEachSignal,
      modelUsedForVideo: analysis.modelUsedForVideo,
      predictionConfidence: analysis.predictionConfidence,
      classProbabilities: analysis.classProbabilities,
      classProbabilitiesByName: analysis.classProbabilitiesByName,
      classProbabilitiesList: analysis.classProbabilitiesList,
      detectedClass: analysis.detectedClass,
      detectedClassLabel: analysis.detectedClassLabel,
      alteredProbability: analysis.alteredProbability,
      orientationText: analysis.orientationText,
      featureHighlights: analysis.featureHighlights,
      gaitFeatures: analysis.gaitFeatures,
      modelKind: analysis.modelKind,
      modelMacroF1: analysis.modelMacroF1,
      predictionLabel: analysis.predictionLabel,
      visualSignals: analysis.signals,
      modelAccuracy: analysis.modelAccuracy,
      modelPrecision: analysis.modelPrecision,
      modelRecall: analysis.modelRecall,
      modelF1Score: analysis.modelF1Score,
      datasetCategory: sprint4Evidence.category,
      iteration7: sprint4Evidence.iteration7,
      iteration8: sprint4Evidence.iteration8,
      analysis,
    });
  } catch (error) {
    console.error("VIDEO_ANALYSIS_ROUTE_ERROR", error);
    return Response.json(
      {
        success: false,
        message:
          error instanceof Error ? error.message : PYTHON_ANALYSIS_FAILED,
        analysis: null,
      },
      { status: 500 }
    );
  } finally {
    await Promise.all([
      tempVideoPath ? rm(tempVideoPath, { force: true }).catch(() => undefined) : Promise.resolve(),
      outputJsonPath ? rm(outputJsonPath, { force: true }).catch(() => undefined) : Promise.resolve(),
      videoPredictionJsonPath ? rm(videoPredictionJsonPath, { force: true }).catch(() => undefined) : Promise.resolve(),
      cloudinaryUploadOk && outputVideoPath
        ? rm(outputVideoPath, { force: true }).catch(() => undefined)
        : Promise.resolve(),
      cloudinaryUploadOk && localOriginalPublicPath
        ? rm(localOriginalPublicPath, { force: true }).catch(() => undefined)
        : Promise.resolve(),
    ]);

    if (!preserveLocalFallback && localOriginalPublicPath) {
      await rm(localOriginalPublicPath, { force: true }).catch(() => undefined);
    }
  }
}
