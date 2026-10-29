"use client";

import { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileDown } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";
import { MetricBlock } from "@/components/ui/MetricBlock";
import { PageHeader, Eyebrow } from "@/components/ui/PageHeader";
import { VideoStage } from "@/components/analysis/VideoStage";
import { NoAnalysisState, isPlaceholderResult } from "@/components/analysis/NoAnalysisState";
import { useAnalysis } from "@/context/AnalysisContext";
import { cn } from "@/lib/utils";
import { ClassificationBreakdown } from "@/components/analysis/ClassificationBreakdown";
import { ModelWarningsPanel } from "@/components/analysis/ModelWarningsPanel";
import {
  EXPERIMENTAL_DISCLAIMER,
  MEDICAL_VIEW_DISCLAIMER,
  MODEL_CONFIDENCE_NOTE,
  analysisQuality,
  experimentalClassification,
  modelQualityWarnings,
  isReliable,
  keyGaitMetricGroups,
  medicalContextNote,
  patternPresentation,
  presentedFindings,
  NO_FINDINGS_TEXT,
} from "@/lib/analysis/resultPresentation";

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

const delay = (i: number) => ({ "--i": i }) as CSSProperties;

function DocSection({
  letter,
  title,
  children,
  index,
}: {
  letter: string;
  title: string;
  children: React.ReactNode;
  index: number;
}) {
  return (
    <section className="reveal border-t border-line px-6 py-7 md:px-8" style={delay(index)}>
      <h2 className="flex items-baseline gap-3 text-lg font-bold text-ink">
        <span className="font-mono text-[13px] font-medium text-accent-cyan-ink">{letter}</span>
        {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function DetailedAnalysisPage() {
  const router = useRouter();
  const { result } = useAnalysis();

  const reliable = isReliable(result);
  const pattern = patternPresentation(result);
  const quality = analysisQuality(result);
  const findings = presentedFindings(result);
  const keyGroups = keyGaitMetricGroups(result);
  const contextNote = reliable ? medicalContextNote(pattern.classKey) : "";
  const recommendations = dedupeStrings(result.recommendations ?? []);
  const classification = experimentalClassification(result);
  const qualityWarnings = modelQualityWarnings(result);

  const processedVideoUrl =
    result.processedVideoUrl ||
    result.annotatedVideoUrl ||
    result.localProcessedVideoUrl;

  if (isPlaceholderResult(result)) {
    return (
      <AppShell>
        <NoAnalysisState
          title="Aún no hay un análisis detallado para mostrar"
          description="La vista detallada se genera a partir de un análisis completado en esta sesión."
        />
      </AppShell>
    );
  }

  const letters = "ABCDEF";
  let sectionCount = 0;
  const nextLetter = () => letters[sectionCount++];

  return (
    <AppShell>
      <div className="grid gap-8">
        <PageHeader
          eyebrow="Vista para profesional"
          title="Análisis detallado de la marcha"
          description="Información cuantitativa del mismo análisis. El sistema identifica patrones y parámetros de movimiento; la interpretación clínica corresponde a un profesional."
          actions={
            <>
              <Button variant="outline" onClick={() => router.push("/analisis/resultado")}>
                <ArrowLeft aria-hidden />
                Volver al resultado
              </Button>
              <Button onClick={() => router.push("/analisis/informe")}>
                <FileDown aria-hidden />
                Generar informe PDF
              </Button>
            </>
          }
        />

        {!reliable && (
          <InlineAlert tone="warning">
            <p className="font-semibold">Análisis no concluyente por calidad del video</p>
            <p className="mt-1 font-normal">{quality.explanation}</p>
          </InlineAlert>
        )}

        <div className="grid items-start gap-8 lg:grid-cols-12">
          <article className="overflow-hidden rounded-xl border border-line bg-surface shadow-raised lg:col-span-8">
            {/* Resumen */}
            <div className="reveal grid gap-6 bg-surface-subtle px-6 py-7 md:grid-cols-[minmax(0,1fr)_auto] md:px-8">
              <div className="min-w-0">
                <Eyebrow>Patrón de marcha observado</Eyebrow>
                <p className="mt-2 text-xl font-bold leading-7 text-ink">
                  {reliable ? pattern.orientationName : "No concluyente"}
                </p>
                <p className="mt-1 text-sm leading-6 text-ink-muted">{pattern.phrase}</p>
              </div>
              <div className="md:text-right">
                <Eyebrow>Confianza del modelo</Eyebrow>
                <p className="mt-2 font-mono text-xl font-bold tabular-nums text-ink">
                  {classification.confidenceText}
                </p>
              </div>
              <p className="text-xs leading-5 text-ink-subtle md:col-span-2">{MODEL_CONFIDENCE_NOTE}</p>
            </div>

            {classification.available && (
              <DocSection letter={nextLetter()} title="Clasificación experimental del modelo" index={1}>
                <p className="-mt-2 mb-4 text-sm text-ink-muted">
                  Distribución de la salida del modelo entre las cuatro clases de patrones de marcha.
                  No son probabilidades clínicas de padecer una enfermedad.
                </p>
                {classification.caveat && (
                  <InlineAlert tone="warning" className="mb-4">
                    {classification.caveat}
                  </InlineAlert>
                )}
                <ClassificationBreakdown rows={classification.rows} className="max-w-xl" />
                <div className="mt-5">
                  <ModelWarningsPanel alerts={qualityWarnings.alerts} notes={qualityWarnings.notes} />
                </div>
              </DocSection>
            )}

            {reliable && (
              <DocSection letter={nextLetter()} title="Observaciones del movimiento" index={1}>
                {findings.length > 0 ? (
                  <div className="-mx-6 overflow-x-auto md:-mx-8">
                    <table className="w-full min-w-[560px] text-left text-sm">
                      <thead>
                        <tr className="border-y border-line bg-surface-subtle text-[11px] uppercase tracking-[0.08em] text-ink-subtle">
                          <th scope="col" className="px-6 py-2.5 font-bold md:px-8">Hallazgo</th>
                          <th scope="col" className="py-2.5 pr-4 font-bold">Relevancia</th>
                          <th scope="col" className="py-2.5 pr-4 font-bold">Explicación</th>
                          <th scope="col" className="py-2.5 pr-6 text-right font-bold md:pr-8">Nivel</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-line">
                        {findings.map((finding) => (
                          <tr key={finding.kind} className="align-top">
                            <td className="px-6 py-3.5 font-semibold text-ink md:px-8">{finding.title}</td>
                            <td className="py-3.5 pr-4 text-ink-muted">{finding.relevance}</td>
                            <td className="py-3.5 pr-4 leading-6 text-ink-muted">{finding.medicalText}</td>
                            <td className="py-3.5 pr-6 text-right md:pr-8">
                              <AlertBadge level={finding.severity} size="sm" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-ink-muted">{NO_FINDINGS_TEXT}</p>
                )}
              </DocSection>
            )}

            {reliable && keyGroups.length > 0 && (
              <DocSection letter={nextLetter()} title="Características de la marcha" index={2}>
                <p className="-mt-2 mb-4 text-sm text-ink-muted">
                  Medidas del movimiento observado en el video con una interpretación directa. No constituyen un diagnóstico.
                </p>
                <div className="grid overflow-hidden rounded-lg border border-line sm:grid-cols-2">
                  {keyGroups.flatMap((group) =>
                    group.params.map((param) => ({ group: group.title, param }))
                  ).map(({ group, param }, index) => (
                    <div key={param.label} className={cn("p-5", index > 0 && "border-t border-line sm:border-l sm:border-t-0")}>
                      <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.09em] text-accent-cyan-ink">{group}</p>
                      <MetricBlock label={param.label} value={param.value} unit={param.unit} explanation={param.explanation} />
                    </div>
                  ))}
                </div>
              </DocSection>
            )}

            {contextNote && (
              <DocSection letter={nextLetter()} title="Interpretación" index={3}>
                <div className="border-l-2 border-navy-700 pl-4">
                  <p className="text-[15px] leading-7 text-ink">{contextNote}</p>
                  <p className="mt-3 text-[15px] leading-7 text-ink-muted">
                    El sistema no confirma enfermedades: identifica señales de la
                    marcha y las compara con patrones aprendidos. La interpretación
                    final corresponde a un profesional de salud.
                  </p>
                </div>
              </DocSection>
            )}

            {reliable && recommendations.length > 0 && (
              <DocSection letter={nextLetter()} title="Recomendaciones" index={4}>
                <ul className="space-y-2">
                  {recommendations.map((recommendation) => (
                    <li key={recommendation} className="flex gap-2.5 text-[15px] leading-6 text-ink-muted">
                      <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-navy-700" aria-hidden />
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </DocSection>
            )}
          </article>

          <aside className="grid content-start gap-6 lg:col-span-4">
            <MedicalDisclaimer
              title="Advertencia"
              text={classification.available ? EXPERIMENTAL_DISCLAIMER : MEDICAL_VIEW_DISCLAIMER}
            />
            {processedVideoUrl && (
              <section>
                <h2 className="mb-3 text-base font-bold text-ink">Video con puntos clave</h2>
                <VideoStage sources={[{ label: "Puntos clave", src: processedVideoUrl }]} size="md" />
              </section>
            )}
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
