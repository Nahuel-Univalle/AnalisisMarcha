"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ProgressSteps } from "@/components/ui/ProgressSteps";
import { useAnalysis } from "@/context/AnalysisContext";
import { useAuth } from "@/context/AuthContext";
import {
  buildObservedSignals,
  observedSeverityToAlertLabel,
} from "@/lib/analysis/observedSignals";
import { AlertLevel, AnalysisResult, SignalSeverity } from "@/types";

const steps = [
  "Video cargado",
  "Guardando video",
  "Detectando puntos",
  "Analizando postura",
  "Evaluando marcha",
  "Preparando informe",
];

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
    datasetWarnings: string[];
    possibleCondition: string;
  };
};

export default function MovementAnalysisPage() {
  const router = useRouter();
  const { user, ready } = useAuth();
  const { videoFile, videoUrl, result, setResult, category } = useAnalysis();
  const [currentStep, setCurrentStep] = useState(0);
  const [apiStatus, setApiStatus] = useState("Esperando inicio del análisis.");
  const [apiError, setApiError] = useState<string | null>(null);
  const [annotatedVideoFailed, setAnnotatedVideoFailed] = useState(false);
  const [processing, setProcessing] = useState(false);
  const analyzedRef = useRef(false);

  useEffect(() => {
    if (currentStep >= steps.length - 1) return;

    const timeout = setTimeout(() => {
      setCurrentStep((prev) => prev + 1);
    }, 900);

    return () => clearTimeout(timeout);
  }, [currentStep]);

  useEffect(() => {
    if (!ready || !videoFile || analyzedRef.current) return;

    analyzedRef.current = true;

    async function analyzeVideo() {
      setProcessing(true);
      setApiStatus("Guardando el video y analizando el movimiento.");
      setApiError(null);

      const formData = new FormData();
      formData.append("video", videoFile as File);
      if (user?.email) formData.append("userEmail", user.email);
      if (user?.name) formData.append("userName", user.name);
      // Sprint 4 Iteración 8: categoría del dataset elegida en la subida.
      formData.append("category", category || "control");

      try {
        const response = await fetch("/api/analysis/video", {
          method: "POST",
          body: formData,
        });
        const payload = await response.json();

        if (!response.ok || !payload.success) {
          throw new Error(
            payload.message || "No se pudo completar el análisis del video."
          );
        }

        setResult(mapEvaluationToAnalysisResult(payload.analysis));
        setAnnotatedVideoFailed(false);
        setApiStatus(
          payload.analysis?.cloudinaryUploadOk === false
            ? "El análisis se completó, pero no se pudo guardar el video en la nube. Se mostrará una versión temporal."
            : "Análisis completado. Video con puntos clave generado y guardado correctamente."
        );
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "No se pudo completar el análisis del video.";

        setApiError(message);
        setApiStatus(
          "No se pudo completar el análisis de movimiento. Revise que el video sea claro y vuelva a intentarlo."
        );
      } finally {
        setProcessing(false);
      }
    }

    analyzeVideo();
  }, [ready, user, videoFile, setResult, category]);

  const completed = currentStep === steps.length - 1 && !processing;
  const posePercent =
    result.poseDetectionRate === null || result.poseDetectionRate === undefined
      ? "Sin dato"
      : `${Math.round(result.poseDetectionRate * 100)}%`;
  const statusDetail =
    result.poseDetectionRate !== null &&
    result.poseDetectionRate !== undefined &&
    result.poseDetectionRate >= 0.95
      ? "El seguimiento corporal fue adecuado para realizar el análisis orientativo."
      : "El sistema logró seguir el cuerpo durante el video y generar una lectura inicial del movimiento.";
  const originalPlaybackUrl =
    result.originalVideoUrl || result.localOriginalVideoUrl || videoUrl;
  const processedPlaybackUrl =
    result.processedVideoUrl ||
    result.annotatedVideoUrl ||
    result.localProcessedVideoUrl;

  return (
    <AppShell>
      <section className="grid gap-6 animate-fadeIn">
        <div>
          <h1 className="text-4xl font-black text-slate-900">
            Analizando patrones de movimiento
          </h1>

          <p className="mt-2 text-slate-500">
            El sistema evalúa señales observadas en la marcha. Este análisis no
            reemplaza una evaluación médica.
          </p>
        </div>

        <ProgressSteps steps={steps} current={currentStep} />

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <h2 className="text-xl font-black text-slate-950">
              Video original
            </h2>
            {originalPlaybackUrl ? (
              <video
                src={originalPlaybackUrl}
                controls
                className="mt-4 w-full rounded-2xl"
              />
            ) : (
              <p className="mt-4 text-slate-600">
                No hay video cargado para analizar.
              </p>
            )}
          </Card>

          <Card>
            <h2 className="text-xl font-black text-slate-950">
              Video con puntos clave
            </h2>
            {processedPlaybackUrl ? (
              annotatedVideoFailed ? (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-800">
                  El video anotado se generó, pero no pudo reproducirse.
                </div>
              ) : (
                <video
                  src={processedPlaybackUrl}
                  controls
                  className="mt-4 w-full rounded-2xl"
                  onError={() => setAnnotatedVideoFailed(true)}
                />
              )
            ) : (
              <p className="mt-4 text-slate-600">
                Todavía no se generó el video con puntos clave. Inicie el
                análisis para procesarlo.
              </p>
            )}
          </Card>
        </div>

        <Card>
          <h2 className="text-xl font-black text-slate-950">
            Estado del análisis
          </h2>

          <p className={`mt-3 flex items-center gap-2 text-sm font-semibold text-slate-700 ${processing ? "animate-pulse" : ""}`}>
            {processing && <Loader2 className="h-4 w-4 animate-spin text-accent" />}
            {apiStatus}
          </p>

          {!apiError && completed && (
            <p className="mt-2 text-sm text-slate-600">{statusDetail}</p>
          )}

          {apiError && (
            <div className="mt-4 animate-slideIn rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-800 shadow-md">
              {apiError}
            </div>
          )}

          {result.analysisWarnings && result.analysisWarnings.length > 0 && (
            <details className="mt-4 animate-slideIn rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 shadow-md">
              <summary className="cursor-pointer font-bold">
                Observaciones del análisis
              </summary>
              <ul className="mt-3 space-y-2">
                {result.analysisWarnings.map((warning) => (
                  <li key={warning}>• {warning}</li>
                ))}
              </ul>
            </details>
          )}

          <div className="mt-5 grid gap-4 md:grid-cols-4">
            {[
              ["Cuerpo detectado en el video", posePercent],
              ["Calidad", result.poseQuality || "Sin dato"],
              ["Momentos analizados", String(result.framesAnalyzed ?? 0)],
              [
                "Momentos con seguimiento correcto",
                String(result.framesWithPose ?? 0),
              ],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-blue-100 bg-blue-50 p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
                <p className="text-sm text-primary">{label}</p>
                <p className="mt-1 font-bold text-slate-900">{value}</p>
              </div>
            ))}
          </div>

          <Button
            className="mt-6 w-full"
            disabled={!completed}
            onClick={() => router.push("/analisis/resultado")}
          >
            Ver resultado
          </Button>
        </Card>
      </section>
    </AppShell>
  );
}

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
  if (name === "Marcha lenta") {
    return "El sistema observó una velocidad de desplazamiento reducida durante la caminata.";
  }

  if (name === "Balanceo de brazos reducido o asimétrico") {
    return "El sistema observó menor movimiento o diferencia entre ambos brazos durante la caminata. Esta señal puede aparecer en patrones asociados a Parkinson.";
  }

  if (name === "Asimetría de marcha") {
    return "El sistema observó diferencias entre el movimiento del lado izquierdo y derecho del cuerpo.";
  }

  if (name === "Estabilidad reducida") {
    return "El sistema observó variaciones en la postura o en el control del cuerpo durante la caminata.";
  }

  if (name === "Postura alterada") {
    return "El sistema observó una inclinación o cambio postural durante el desplazamiento.";
  }

  return description;
}

function mapEvaluationToAnalysisResult(analysis: ApiAnalysis): AnalysisResult {
  const evaluation = analysis.evaluation;
  const alertLevel = toAlertLevel(evaluation.alertLevel);
  const warnings = dedupeStrings(analysis.warnings ?? []);
  const datasetWarnings = dedupeStrings(evaluation.datasetWarnings ?? []);
  const modelSuggestsParkinson =
    analysis.modelUsed === true &&
    evaluation.possibleCondition === "posible_parkinson";
  const parkinsonCondition = {
    condition: modelSuggestsParkinson
      ? "Resultado orientativo compatible con posible patrón asociado a Parkinson"
      : "Sin alerta principal asociada a Parkinson",
    status: modelSuggestsParkinson
      ? "Requiere valoración profesional"
      : "Sin alerta principal",
    description: evaluation.summary,
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
    modelSource: analysis.modelSource ?? null,
    probabilityParkinson: analysis.probabilityParkinson ?? null,
    probabilityNormal: analysis.probabilityNormal ?? null,
    riskLevel: analysis.riskLevel ?? null,
    confidence: analysis.confidence ?? null,
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
    analysisWarnings: warnings.filter((warning) => !datasetWarnings.includes(warning)),
    datasetWarnings,
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
