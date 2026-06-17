"use client";

import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";
import { ModelPerformanceCard } from "@/components/analysis/ModelPerformanceCard";
import { useAnalysis } from "@/context/AnalysisContext";

export default function FullEvaluationPage() {
  const router = useRouter();
  const { result } = useAnalysis();
  const posePercent =
    result.poseDetectionRate === null || result.poseDetectionRate === undefined
      ? "Sin dato"
      : `${Math.round(result.poseDetectionRate * 100)}%`;
  const processedVideoUrl =
    result.processedVideoUrl ||
    result.annotatedVideoUrl ||
    result.localProcessedVideoUrl;

  return (
    <AppShell>
      <section className="grid gap-6">
        <div>
          <h1 className="text-4xl font-black text-slate-950">
            Evaluación completa del análisis
          </h1>

          <p className="mt-2 max-w-3xl text-slate-600">
            {result.summary}
          </p>
        </div>

        <MedicalDisclaimer />

        <ModelPerformanceCard result={result} />

        <Card>
          <h2 className="text-2xl font-black text-slate-950">
            Calidad del procesamiento
          </h2>
          <div className="mt-5 grid gap-4 md:grid-cols-4">
            {[
              ["Calidad", result.poseQuality || "Sin dato"],
              ["Cuerpo detectado en el video", posePercent],
              ["Momentos analizados", String(result.framesAnalyzed ?? 0)],
              [
                "Momentos con seguimiento correcto",
                String(result.framesWithPose ?? 0),
              ],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-1 font-bold text-slate-950">{value}</p>
              </div>
            ))}
          </div>
        </Card>

        {processedVideoUrl && (
          <Card>
            <h2 className="text-2xl font-black text-slate-950">
              Video con puntos clave
            </h2>
            <video
              src={processedVideoUrl}
              controls
              className="mt-5 w-full rounded-2xl"
            />
          </Card>
        )}

        <Card>
          <h2 className="text-2xl font-black text-slate-950">
            Señales observadas
          </h2>

          {result.signals.length > 0 ? (
            <ul className="mt-5 space-y-3 text-slate-700">
              {result.signals.map((signal) => (
                <li key={signal.name}>
                  • {signal.name}: {signal.description}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-slate-600">
              {result.signalEmptyMessage ||
                "No se detectaron señales relevantes en este análisis."}
            </p>
          )}
        </Card>

        <Card>
          <h2 className="text-2xl font-black text-slate-950">
            Posible patrón asociado
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {result.conditions.map((condition) => (
              <div key={condition.condition} className="rounded-2xl bg-slate-50 p-4">
                <h3 className="font-bold text-slate-950">
                  {condition.condition}
                </h3>
                <p className="mt-1 text-sm font-semibold text-slate-500">
                  {condition.status}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {condition.description}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-2xl font-black text-slate-950">
            Qué significa este resultado
          </h2>

          <p className="mt-3 leading-7 text-slate-600">
            El sistema no confirma enfermedades. Solo identifica señales
            observadas en el video y las compara con patrones de marcha. La
            interpretación final corresponde a un profesional de salud.
          </p>
        </Card>

        <Card>
          <h2 className="text-2xl font-black text-slate-950">
            Recomendación
          </h2>

          <ul className="mt-4 space-y-2 text-slate-700">
            {(result.recommendations ?? [
              "Descargar el informe.",
              "Llevarlo a un médico o profesional de salud.",
              "Repetir el análisis si el video no fue claro.",
              "No sacar conclusiones sin valoración profesional.",
            ]).map((recommendation) => (
              <li key={recommendation}>• {recommendation}</li>
            ))}
          </ul>
        </Card>

        <Button onClick={() => router.push("/analisis/informe")}>
          Generar informe PDF
        </Button>
      </section>
    </AppShell>
  );
}
