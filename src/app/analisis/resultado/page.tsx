"use client";

import { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { FileDown, Plus, ShieldCheck, Stethoscope } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";
import { MetricBlock } from "@/components/ui/MetricBlock";
import { SectionHeader, Eyebrow } from "@/components/ui/PageHeader";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { ClassificationBreakdown } from "@/components/analysis/ClassificationBreakdown";
import { FindingsTrace } from "@/components/analysis/FindingsTrace";
import { ModelWarningsPanel } from "@/components/analysis/ModelWarningsPanel";
import { MovementProfile } from "@/components/analysis/MovementProfile";
import { VideoStage } from "@/components/analysis/VideoStage";
import { NoAnalysisState, isPlaceholderResult } from "@/components/analysis/NoAnalysisState";
import { useAnalysis } from "@/context/AnalysisContext";
import { cn } from "@/lib/utils";
import {
  EXPERIMENTAL_DISCLAIMER,
  MODEL_CONFIDENCE_NOTE,
  ORIENTATION_DISCLAIMER,
  ORIENTATION_DISCLAIMER_LONG,
  analysisQuality,
  experimentalClassification,
  modelQualityWarnings,
  isReliable,
  keyGaitMetrics,
  patternPresentation,
  presentedFindings,
  NO_FINDINGS_TEXT,
  userCharacteristicCards,
} from "@/lib/analysis/resultPresentation";

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

const delay = (i: number) => ({ "--i": i }) as CSSProperties;

export default function ResultPage() {
  const router = useRouter();
  const { result } = useAnalysis();

  const reliable = isReliable(result);
  const pattern = patternPresentation(result);
  const quality = analysisQuality(result);
  const findings = presentedFindings(result);
  const characteristicCards = userCharacteristicCards(result);
  const keyMetrics = keyGaitMetrics(result);
  const classification = experimentalClassification(result);
  const qualityWarnings = modelQualityWarnings(result);

  // Solo advertencias del analisis del video; las de la base de referencia
  // son metadatos internos y no se muestran en la vista medica.
  const observations = dedupeStrings(result.analysisWarnings ?? []);
  const processedVideoUrl =
    result.processedVideoUrl ||
    result.annotatedVideoUrl ||
    result.localProcessedVideoUrl;

  if (isPlaceholderResult(result)) {
    return (
      <AppShell>
        <NoAnalysisState
          title="Aún no hay un resultado para mostrar"
          description="El resultado aparece aquí al terminar un análisis. Para revisar análisis anteriores, abre tu seguimiento."
        />
      </AppShell>
    );
  }

  let sectionIndex = 0;
  const nextIndex = () => String(++sectionIndex).padStart(2, "0");

  return (
    <AppShell>
      <div className="grid gap-8">
        <StepIndicator current={3} />

        {/* ================= Resultado principal ================= */}
        <header className="reveal result-summary overflow-hidden rounded-xl border border-line bg-surface shadow-raised">
          <div className="grid gap-6 p-6 md:p-8 lg:grid-cols-[minmax(0,1fr)_250px] lg:gap-10">
            <div className="min-w-0">
              <Eyebrow className="text-primary-dark">
                {classification.available ? "Clasificación experimental" : "Resultado orientativo"}
              </Eyebrow>
              <h1 className="mt-3 text-[26px] font-semibold leading-[34px] tracking-[-0.03em] text-ink md:text-[30px] md:leading-[38px]">
                {reliable ? pattern.phrase : "Análisis no concluyente por calidad del video"}
              </h1>
              {classification.caveat && (
                <InlineAlert tone="warning" className="mt-4 max-w-3xl">
                  {classification.caveat}
                </InlineAlert>
              )}
              <p className="mt-3 max-w-3xl text-[15px] leading-7 text-ink-muted">{result.summary}</p>
              {reliable && result.orientationText && !result.summary.includes(result.orientationText.trim()) && (
                <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-muted">{result.orientationText}</p>
              )}
              <p className="mt-4 flex items-start gap-2 text-[13px] font-medium text-ink">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" aria-hidden />
                {classification.available
                  ? EXPERIMENTAL_DISCLAIMER
                  : `${ORIENTATION_DISCLAIMER} Requiere valoración profesional.`}
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <Button onClick={() => router.push("/analisis/informe")} variant={reliable ? "primary" : "outline"}>
                  <FileDown aria-hidden />
                  Generar informe PDF
                </Button>
                <Button variant="outline" onClick={() => router.push("/analisis/evaluacion")}>
                  <Stethoscope aria-hidden />
                  Ver análisis detallado
                </Button>
                <Button variant={reliable ? "outline" : "primary"} onClick={() => router.push("/analisis/subir-video")}>
                  <Plus aria-hidden />
                  Nuevo análisis
                </Button>
              </div>
            </div>

            <div className="result-alert self-start">
              <Eyebrow>Confianza del modelo</Eyebrow>
              <p className="mt-3 font-mono text-[28px] font-bold leading-8 tabular-nums text-ink">
                {classification.confidenceText}
              </p>
              {classification.available ? (
                <ClassificationBreakdown rows={classification.rows} className="mt-4" />
              ) : (
                <p className="mt-2 text-sm leading-6 text-ink-muted">
                  No se realizó la clasificación experimental para este video.
                </p>
              )}
              <p className="mt-4 border-t border-line pt-3 text-xs leading-5 text-ink-muted">
                {MODEL_CONFIDENCE_NOTE}
              </p>
            </div>
          </div>
        </header>

        {reliable && <ModelWarningsPanel alerts={qualityWarnings.alerts} notes={qualityWarnings.notes} />}

        {!reliable && (
          <InlineAlert tone="warning">
            <p className="font-semibold">No fue posible realizar un análisis confiable</p>
            <p className="mt-1 font-normal">{quality.explanation}</p>
          </InlineAlert>
        )}

        <div className="grid items-start gap-8 lg:grid-cols-12">
          {/* ================= Columna principal ================= */}
          <div className="grid content-start gap-10 lg:col-span-8">
            {reliable && (
              <section className="reveal" style={delay(1)}>
                <SectionHeader
                  index={nextIndex()}
                  title="Observaciones del movimiento"
                  description="Señales observadas en la caminata. Son información complementaria y no explican por sí solas la clasificación del modelo."
                />
                <div className="mt-5 rounded-xl border border-line bg-surface p-6 shadow-raised">
                  {findings.length > 0 ? (
                    <FindingsTrace
                      findings={findings.map((finding) => ({
                        key: finding.kind,
                        title: finding.title,
                        relevance: finding.relevance,
                        text: finding.userText,
                        severity: finding.severity,
                      }))}
                    />
                  ) : (
                    <p className="text-sm text-ink-muted">{NO_FINDINGS_TEXT}</p>
                  )}
                </div>
              </section>
            )}

            {characteristicCards.length > 0 && (
              <section className="reveal" style={delay(2)}>
                <SectionHeader
                  index={nextIndex()}
                  title="Perfil de movimiento"
                  description="Qué observó el sistema en la caminata, en lenguaje sencillo."
                />
                <div className="mt-5">
                  <MovementProfile cards={characteristicCards} />
                </div>
              </section>
            )}

            {keyMetrics.length > 0 && (
              <section className="reveal" style={delay(3)}>
                <SectionHeader
                  index={nextIndex()}
                  title="Medidas relevantes"
                  description="Algunas medidas del movimiento observado durante la caminata. No constituyen un diagnóstico."
                />
                <div className="mt-5 grid overflow-hidden rounded-xl border border-line bg-surface sm:grid-cols-2">
                  {keyMetrics.map((metric, index) => (
                    <MetricBlock
                      key={metric.label}
                      label={metric.label}
                      value={metric.value}
                      unit={metric.unit}
                      explanation={metric.explanation}
                      size="lg"
                      className={cn("p-6", index > 0 && "border-t border-line sm:border-l sm:border-t-0")}
                    />
                  ))}
                </div>
              </section>
            )}

            {observations.length > 0 && (
              <details className="rounded-xl border border-warning-line bg-warning-bg px-4 py-3 text-sm text-warning">
                <summary className="cursor-pointer font-semibold">Observaciones del análisis</summary>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {observations.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>

          {/* ================= Columna lateral ================= */}
          <aside className="grid content-start gap-6 lg:col-span-4">
            {result.recommendations && result.recommendations.length > 0 && (
              <section className="reveal rounded-xl border border-line bg-surface p-6" style={delay(2)}>
                <h2 className="text-base font-bold text-ink">Recomendaciones</h2>
                <ul className="mt-3 space-y-2.5">
                  {result.recommendations.map((recommendation) => (
                    <li key={recommendation} className="flex gap-2.5 text-sm leading-6 text-ink-muted">
                      <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-navy-700" aria-hidden />
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <div className="reveal" style={delay(3)}>
              <MedicalDisclaimer title="Aviso" text={ORIENTATION_DISCLAIMER_LONG} />
            </div>

            {processedVideoUrl && (
              <section className="reveal" style={delay(4)}>
                <h2 className="mb-3 text-base font-bold text-ink">Video con puntos clave</h2>
                <VideoStage sources={[{ label: "Puntos clave", src: processedVideoUrl }]} size="md" />
                <p className="mt-2 text-xs leading-5 text-ink-subtle">
                  Material de apoyo con los puntos del cuerpo detectados por el sistema.
                </p>
              </section>
            )}
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
