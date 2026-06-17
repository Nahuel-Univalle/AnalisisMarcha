"use client";

import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";
import { SignalCard } from "@/components/analysis/SignalCard";
import { ConditionEvaluation } from "@/components/analysis/ConditionEvaluation";
import { ModelPerformanceCard } from "@/components/analysis/ModelPerformanceCard";
import { useAnalysis } from "@/context/AnalysisContext";
import { Card } from "@/components/ui/Card";

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

function riskStyles(level: string) {
  if (level === "Alto") {
    return "border-red-200 from-red-50 to-white text-red-700";
  }

  if (level === "Medio") {
    return "border-amber-200 from-amber-50 to-white text-amber-700";
  }

  return "border-emerald-200 from-emerald-50 to-white text-emerald-700";
}

export default function ResultPage() {
  const router = useRouter();
  const { result } = useAnalysis();
  const posePercent =
    result.poseDetectionRate === null || result.poseDetectionRate === undefined
      ? "Sin dato"
      : `${Math.round(result.poseDetectionRate * 100)}%`;
  const displayedAlert = result.alertLevel;
  const displayedSummary = result.summary;
  const observations = dedupeStrings([
    ...(result.analysisWarnings ?? []),
    ...(result.datasetWarnings ?? []),
  ]);
  const processedVideoUrl =
    result.processedVideoUrl ||
    result.annotatedVideoUrl ||
    result.localProcessedVideoUrl;

  return (
    <AppShell>
      <section className="grid gap-6 animate-fadeIn">
        <Card className={`bg-linear-to-br ${riskStyles(displayedAlert)}`}>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-4xl font-black text-slate-900">
                Resultado orientativo del análisis visual
              </h1>

              <p className="mt-3 max-w-3xl text-slate-600">
                {displayedSummary}
              </p>
            </div>

            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-lg backdrop-blur">
              <p className="mb-2 text-sm font-bold text-slate-500">
                Nivel de alerta
              </p>
              <AlertBadge level={displayedAlert} />
            </div>
          </div>
        </Card>

        <MedicalDisclaimer />

        <ModelPerformanceCard result={result} />

        <Card>
          <h2 className="text-2xl font-black text-slate-900">
            Calidad del video
          </h2>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {[
              ["Cuerpo detectado en el video", posePercent],
              ["Momentos analizados", String(result.framesAnalyzed ?? 0)],
              [
                "Momentos con seguimiento correcto",
                String(result.framesWithPose ?? 0),
              ],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-slate-100 bg-slate-50 p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-1 font-bold text-slate-950">{value}</p>
              </div>
            ))}
          </div>

          {processedVideoUrl && (
            <video
              src={processedVideoUrl}
              controls
              className="mt-5 w-full rounded-2xl shadow-lg"
            />
          )}
        </Card>

        {observations.length > 0 && (
          <details className="animate-slideIn rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 shadow-md">
            <summary className="cursor-pointer font-bold">
              Observaciones del análisis
            </summary>
            <ul className="mt-3 space-y-2">
              {observations.map((warning) => (
                <li key={warning}>• {warning}</li>
              ))}
            </ul>
          </details>
        )}

        <section>
          <h2 className="text-2xl font-black text-slate-900">
            Señales observadas
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {result.signals.length > 0 ? (
              result.signals.map((signal) => (
                <SignalCard key={signal.name} signal={signal} />
              ))
            ) : (
              <Card className="md:col-span-2">
                <p className="text-slate-600">
                  {result.signalEmptyMessage ||
                    "No se detectaron señales relevantes en este análisis."}
                </p>
              </Card>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-black text-slate-900">
            Posible patrón asociado
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {result.conditions.map((condition) => (
              <ConditionEvaluation
                key={condition.condition}
                condition={condition}
              />
            ))}
          </div>
        </section>

        {result.recommendations && result.recommendations.length > 0 && (
          <Card>
            <h2 className="text-2xl font-black text-slate-900">
              Recomendaciones
            </h2>
            <ul className="mt-4 space-y-2 text-slate-700">
              {result.recommendations.map((recommendation) => (
                <li key={recommendation}>• {recommendation}</li>
              ))}
            </ul>
          </Card>
        )}

        <div className="flex flex-col gap-3 md:flex-row">
          <Button onClick={() => router.push("/analisis/evaluacion")}>
            Ver evaluación completa
          </Button>

          <Button
            variant="secondary"
            onClick={() => router.push("/analisis/informe")}
          >
            Generar informe PDF
          </Button>

          <Button
            variant="outline"
            onClick={() => router.push("/analisis/subir-video")}
          >
            Nuevo análisis
          </Button>
        </div>
      </section>
    </AppShell>
  );
}
