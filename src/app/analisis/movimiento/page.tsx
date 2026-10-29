"use client";

import { CSSProperties, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CircleCheck, RotateCcw } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { LinkButton } from "@/components/ui/LinkButton";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { PageHeader } from "@/components/ui/PageHeader";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { EmptyState } from "@/components/ui/EmptyState";
import { ProcessingTimeline } from "@/components/analysis/ProcessingTimeline";
import { VideoStage } from "@/components/analysis/VideoStage";
import { GaitFigure } from "@/components/brand/GaitFigure";
import { useAnalysis } from "@/context/AnalysisContext";
import { useAuth } from "@/context/AuthContext";
import {
  buildObservedSignals,
  observedSeverityToAlertLabel,
} from "@/lib/analysis/observedSignals";
import { AlertLevel, AnalysisResult, ModelWarning, SignalSeverity } from "@/types";

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
  const [, setAnnotatedVideoFailed] = useState(false);
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
  // Los datos técnicos de seguimiento (porcentaje de cuerpo detectado,
  // calidad, cantidad de momentos analizados) se siguen recibiendo y
  // guardando en el resultado, pero ya no se muestran al usuario.
  const succeeded = completed && !apiError;
  const originalPlaybackUrl =
    result.originalVideoUrl || result.localOriginalVideoUrl || videoUrl;
  const processedPlaybackUrl =
    result.processedVideoUrl ||
    result.annotatedVideoUrl ||
    result.localProcessedVideoUrl;

  const failed = Boolean(apiError);
  const noVideo = !videoFile && !processing && !failed;

  return (
    <AppShell>
      <div className="grid gap-8">
        <StepIndicator current={succeeded ? 3 : 2} />

        <PageHeader
          eyebrow="Procesamiento"
          title={
            succeeded
              ? "Análisis completado"
              : failed
                ? "No se pudo completar el análisis"
                : "Analizando patrones de movimiento"
          }
          description="El sistema evalúa señales observadas en la marcha. Este análisis no reemplaza una evaluación médica."
        />

        {noVideo ? (
          <div className="reveal rounded-xl border border-line bg-surface p-6">
            <EmptyState
              visual={
                <div className="w-20 rounded-lg bg-navy-900 p-2">
                  <GaitFigure guides={false} />
                </div>
              }
              title="No hay video cargado para analizar"
              description="Sube un video caminando para iniciar un nuevo análisis."
              action={<LinkButton href="/analisis/subir-video">Subir video</LinkButton>}
            />
          </div>
        ) : (
          <section
            className="reveal processing-workspace"
            style={{ "--i": 1 } as CSSProperties}
            aria-label="Panel de análisis"
          >
            <div className="grid lg:grid-cols-12">
              <div className="border-b border-line bg-surface-subtle p-4 sm:p-6 lg:col-span-7 lg:border-b-0 lg:border-r">
                {originalPlaybackUrl || processedPlaybackUrl ? (
                  <VideoStage
                    key={processedPlaybackUrl ? "processed" : "original"}
                    sources={[
                      { label: "Puntos clave", src: processedPlaybackUrl ?? "" },
                      { label: "Original", src: originalPlaybackUrl ?? "" },
                    ]}
                    initial={processedPlaybackUrl ? "Puntos clave" : "Original"}
                    size="lg"
                    scanning={processing}
                    className="fade-in border border-navy-800"
                  />
                ) : (
                  <div className="flex min-h-[300px] items-center justify-center rounded-xl bg-navy-950 p-6 text-sm text-on-navy">
                    No hay video cargado para analizar.
                  </div>
                )}
              </div>

              <div className="flex flex-col p-6 sm:p-8 lg:col-span-5">
                <div className="flex items-start gap-4">
                  <div className="w-[64px] shrink-0 rounded-lg bg-primary-soft p-2">
                    <GaitFigure tone="light" active={processing} guides={false} />
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-xl font-semibold text-ink">
                      {succeeded ? "Análisis completado" : failed ? "Análisis interrumpido" : "Analizando tu video"}
                    </h2>
                    <p className="mt-2 text-sm leading-6 text-ink-muted" aria-live="polite">
                      {apiStatus}
                    </p>
                  </div>
                </div>

                <div className="mt-7 border-t border-line pt-6">
                  <ProcessingTimeline
                    steps={steps}
                    current={currentStep}
                    processing={processing}
                    completed={succeeded}
                    failed={failed}
                  />
                </div>

                {!succeeded && !failed && (
                  <p className="mt-6 text-xs text-ink-subtle">
                    El tiempo depende de la duración del video.
                  </p>
                )}

                {succeeded && (
                  <p className="fade-in mt-6 flex items-center gap-2 text-sm font-medium text-ink">
                    <CircleCheck className="h-4 w-4 text-primary" aria-hidden />
                    El resultado está listo para revisar.
                  </p>
                )}
              </div>
            </div>
          </section>
        )}

        {apiError && <InlineAlert tone="error">{apiError}</InlineAlert>}

        {result.analysisWarnings && result.analysisWarnings.length > 0 && (
          <details className="group rounded-xl border border-warning-line bg-warning-bg px-4 py-3 text-sm text-warning">
            <summary className="cursor-pointer font-semibold">Observaciones del análisis</summary>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {result.analysisWarnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </details>
        )}

        {!noVideo && (
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-end">
            {failed && (
              <LinkButton href="/analisis/subir-video" variant="outline" size="lg">
                <RotateCcw aria-hidden />
                Subir otro video
              </LinkButton>
            )}
            <Button size="lg" disabled={!succeeded} onClick={() => router.push("/analisis/resultado")}>
              Ver resultado
              <ArrowRight aria-hidden />
            </Button>
          </div>
        )}
      </div>
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
    return "El sistema observó menor movimiento o diferencia entre ambos brazos durante la caminata. Esta señal puede aparecer en distintas alteraciones de la marcha.";
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
