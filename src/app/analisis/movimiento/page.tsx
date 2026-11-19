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

import { mapEvaluationToAnalysisResult } from "@/lib/analysis/mapApiAnalysis";

const steps = [
  "Video cargado",
  "Guardando video",
  "Detectando puntos",
  "Analizando postura",
  "Evaluando marcha",
  "Preparando informe",
];

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

