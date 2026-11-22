"use client";

import { Activity } from "lucide-react";
import { ClassificationBreakdown } from "@/components/analysis/ClassificationBreakdown";
import { useAnalysis } from "@/context/AnalysisContext";
import { useAuth } from "@/context/AuthContext";
import {
  EXPERIMENTAL_DISCLAIMER,
  MODEL_CONFIDENCE_NOTE,
  ORIENTATION_DISCLAIMER,
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

function ReportSection({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line py-6">
      <h2 className="flex items-baseline gap-3 text-[13px] font-bold uppercase tracking-[0.08em] text-ink">
        <span className="font-mono font-medium text-accent-cyan-ink">{number}.</span>
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

// Informe de apoyo para el profesional de salud. Este mismo componente es el
// que se captura para el PDF (`downloadElementAsPdf`), por lo que la vista web
// y el PDF muestran exactamente la misma información. Solo usa tokens HEX
// (html2canvas no interpreta oklch()).
export function MedicalReport() {
  const { user } = useAuth();
  const { result } = useAnalysis();

  const reliable = isReliable(result);
  const pattern = patternPresentation(result);
  const quality = analysisQuality(result);
  const findings = presentedFindings(result);
  const keyMetricGroups = keyGaitMetricGroups(result);
  const contextNote = reliable ? medicalContextNote(pattern.classKey) : "";
  const recommendations = dedupeStrings(result.recommendations ?? []);
  const classification = experimentalClassification(result);
  const qualityWarnings = modelQualityWarnings(result);
  // El resultado en memoria no trae la fecha del análisis; la fecha mostrada
  // es la de emisión del documento.
  const issuedAt = new Date().toLocaleDateString("es-BO");

  let n = 0;
  const next = () => ++n;

  return (
    <div
      id="medical-report-content"
      className="mx-auto w-full max-w-[794px] border border-line bg-surface px-8 py-10 text-ink shadow-raised md:px-14 md:py-12"
    >
      {/* Membrete */}
      <header className="flex items-start justify-between gap-6 border-b-2 border-navy-900 pb-5">
        <div>
          <p className="flex items-center gap-2 text-[13px] font-bold text-navy-900">
            <Activity className="h-4 w-4 text-accent-cyan-ink" aria-hidden />
            Análisis de Marcha IA
          </p>
          <h1 className="mt-3 text-[24px] font-bold leading-8 tracking-[-0.01em] text-ink">
            Informe de análisis de marcha
          </h1>
          <p className="mt-1 text-[13px] text-ink-muted">Documento orientativo para profesionales de salud</p>
        </div>
        <p className="shrink-0 rounded-md border border-line px-2 py-1 text-[11px] font-bold uppercase tracking-[0.08em] text-ink-muted">
          {classification.available ? "Clasificación experimental" : "Resultado orientativo"}
        </p>
      </header>

      <ReportSection number={next()} title="Datos del análisis">
        <dl className="grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">Usuario evaluado</dt>
            <dd className="mt-1 text-[15px] font-semibold">{user?.name || "Usuario"}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">Fecha de emisión</dt>
            <dd className="mt-1 font-mono text-[14px] font-medium">{issuedAt}</dd>
          </div>
          <div>
            <dt className="text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">Confianza del modelo</dt>
            <dd className="mt-1 font-mono text-[15px] font-bold tabular-nums">{classification.confidenceText}</dd>
          </div>
        </dl>
      </ReportSection>

      <ReportSection number={next()} title="Resultado">
        <p className="text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">
          {classification.available ? "Clasificación experimental de patrones de marcha" : "Patrón de marcha observado"}
        </p>
        <p className="mt-1 text-[18px] font-semibold leading-7">
          {reliable ? pattern.phrase : "Análisis no concluyente por calidad del video"}
        </p>
        {classification.caveat && (
          <p className="mt-3 border-l-2 border-warning-line bg-warning-bg px-3 py-2 text-[13px] font-semibold leading-6 text-warning">
            {classification.caveat}
          </p>
        )}
        {classification.available && (
          <ClassificationBreakdown rows={classification.rows} className="mt-4 max-w-md" />
        )}
        <p className="mt-3 text-[13px] leading-6 text-ink-muted">
          {reliable ? MODEL_CONFIDENCE_NOTE : quality.explanation}
        </p>
        {reliable && (qualityWarnings.alerts.length > 0 || qualityWarnings.notes.length > 0) && (
          <div className="mt-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">Advertencias sobre el video</p>
            <ul className="mt-1.5 space-y-1">
              {[...qualityWarnings.alerts, ...qualityWarnings.notes].map((warning) => (
                <li key={warning.code} className="text-[13px] leading-6 text-ink-muted">
                  <span className="font-semibold text-ink">{warning.title}.</span> {warning.message}
                </li>
              ))}
            </ul>
          </div>
        )}
      </ReportSection>

      {reliable && (
        <>
          <ReportSection number={next()} title="Observaciones del movimiento">
            {findings.length > 0 ? (
              <ol className="divide-y divide-line">
                {findings.map((finding, index) => (
                  <li key={finding.kind} className="grid grid-cols-[28px_1fr] gap-x-2 py-3 first:pt-0 last:pb-0">
                    <span className="font-mono text-[13px] text-ink-subtle">{String(index + 1).padStart(2, "0")}</span>
                    <div>
                      <p className="text-[15px] font-semibold">{finding.title}</p>
                      <p className="text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">{finding.relevance}</p>
                      <p className="mt-1 text-[13px] leading-6 text-ink-muted">{finding.medicalText}</p>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-[13px] text-ink-muted">{NO_FINDINGS_TEXT}</p>
            )}
          </ReportSection>

          {keyMetricGroups.length > 0 && (
            <ReportSection number={next()} title="Parámetros de marcha">
              <table className="w-full text-left text-[13px]">
                <thead>
                  <tr className="border-b border-line text-[11px] uppercase tracking-[0.08em] text-ink-subtle">
                    <th scope="col" className="pb-2 pr-4 font-bold">Parámetro</th>
                    <th scope="col" className="pb-2 pr-4 font-bold">Descripción</th>
                    <th scope="col" className="pb-2 text-right font-bold">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {keyMetricGroups
                    .flatMap((group) => group.params)
                    .map((param) => (
                      <tr key={param.label} className="border-b border-line align-top last:border-b-0">
                        <td className="py-2.5 pr-4 font-semibold text-ink">{param.label}</td>
                        <td className="py-2.5 pr-4 text-ink-muted">{param.explanation}</td>
                        <td className="w-36 py-2.5 text-right font-mono font-medium text-ink">
                          {param.value}
                          {param.unit ? ` ${param.unit}` : ""}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </ReportSection>
          )}

          <ReportSection number={next()} title="Interpretación">
            {contextNote && <p className="text-[14px] leading-7 text-ink">{contextNote}</p>}
            <p className="mt-2 text-[14px] leading-7 text-ink-muted">
              Este resultado no confirma una enfermedad y requiere valoración
              por un profesional de salud.
            </p>
          </ReportSection>

          <ReportSection number={next()} title="Recomendaciones">
            {recommendations.length > 0 ? (
              <ul className="space-y-1.5">
                {recommendations.map((recommendation) => (
                  <li key={recommendation} className="flex gap-2.5 text-[14px] leading-6 text-ink-muted">
                    <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-navy-700" aria-hidden />
                    {recommendation}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[14px] leading-6 text-ink-muted">
                Se recomienda que un profesional de salud revise este resultado.
              </p>
            )}
          </ReportSection>
        </>
      )}

      <ReportSection number={next()} title="Advertencia">
        <p className="border-l-2 border-navy-900 bg-surface-subtle px-4 py-3 text-[13px] leading-6 text-ink">
          {classification.available
            ? EXPERIMENTAL_DISCLAIMER
            : `${ORIENTATION_DISCLAIMER} La interpretación clínica debe ser realizada por un profesional de salud.`}
        </p>
      </ReportSection>
    </div>
  );
}
