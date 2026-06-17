"use client";

import { AlertBadge } from "@/components/ui/AlertBadge";
import { useAnalysis } from "@/context/AnalysisContext";
import { useAuth } from "@/context/AuthContext";
import { AnalysisResult, Signal } from "@/types";

const SUMMARY_TEXT =
  "El sistema analizó el movimiento observado en el video y encontró señales que podrían estar relacionadas con una alteración de la marcha. Este resultado no confirma una enfermedad y debe ser revisado por un profesional de salud.";
const MEDICAL_DISCLAIMER =
  "Este resultado no constituye diagnóstico médico. Debe ser revisado por un profesional de salud.";
const RECOMMENDATION =
  "Si estos signos se repiten o generan preocupación, se recomienda consultar con un profesional de salud. El sistema solo entrega una orientación inicial.";

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

function normalizedScore(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }

  if (value < 0) return null;
  const normalized = value > 1 ? value / 100 : value;
  return normalized <= 1 ? normalized : null;
}

function visualResultLabel(result: AnalysisResult) {
  const probabilityParkinson = normalizedScore(
    result.probabilityParkinson ?? result.modelParkinsonProbability
  );
  const riskLevel = result.riskLevel?.toLowerCase();

  if (result.modelSource === "video_parkinson_model") {
    if (riskLevel === "bajo" || (probabilityParkinson !== null && probabilityParkinson < 0.4)) {
      return "Sin señales relevantes";
    }

    if (
      riskLevel === "medio" ||
      (probabilityParkinson !== null && probabilityParkinson <= 0.7)
    ) {
      return "Señales moderadas";
    }

    return "Señales relevantes";
  }

  const { predictionConfidence: confidence, alertLevel } = result;
  const score = normalizedScore(confidence);

  if (score !== null) {
    if (score < 0.4) return "Señales leves";
    if (score < 0.7) return "Señales moderadas";
    return "Señales relevantes";
  }

  if (alertLevel === "Alto") return "Señales relevantes";
  if (alertLevel === "Medio") return "Señales moderadas";
  return "Señales leves";
}

function friendlySignalName(name: string) {
  const normalized = name.toLowerCase();

  if (normalized.includes("marcha lenta")) return "Marcha lenta o irregular";
  if (normalized.includes("asimetr")) {
    return "Movimiento desigual entre ambos lados del cuerpo";
  }
  if (normalized.includes("brazo")) {
    return "Balanceo de brazos reducido o desigual";
  }
  if (normalized.includes("ritmo") || normalized.includes("paso")) {
    return "Variación en el ritmo de los pasos";
  }
  if (normalized.includes("estabilidad") || normalized.includes("postura")) {
    return "Estabilidad corporal reducida";
  }

  return name;
}

function signalDetails(signal: Signal) {
  const name = signal.name.toLowerCase();

  if (name.includes("brazo")) {
    return "Se observó menor movimiento o diferencia entre ambos brazos durante la caminata.";
  }

  if (name.includes("asimetr")) {
    return "Se observaron diferencias entre el movimiento del lado izquierdo y derecho del cuerpo.";
  }

  if (name.includes("postura") || name.includes("estabilidad")) {
    return "Se observaron variaciones en la postura o en el control corporal.";
  }

  if (name.includes("marcha") || name.includes("paso") || name.includes("ritmo")) {
    return "Se observaron cambios en velocidad, ritmo o regularidad del paso.";
  }

  return signal.description;
}

export function MedicalReport() {
  const { user } = useAuth();
  const { result, videoMeta } = useAnalysis();
  const posePercent =
    result.poseDetectionRate === null || result.poseDetectionRate === undefined
      ? "Sin dato"
      : `${Math.round(result.poseDetectionRate * 100)}%`;
  const observations = dedupeStrings([
    ...(result.analysisWarnings ?? []),
    ...(result.datasetWarnings ?? []),
  ]);
  const recommendations = dedupeStrings(result.recommendations ?? []);
  const analysisCompleted = Boolean(
    result.visualAnalysisCompleted ?? (result.framesAnalyzed ?? 0) > 0
  );
  const summaryText =
    result.signals.length === 0
      ? result.signalEmptyMessage ||
        "No se detectaron señales relevantes asociadas a patrones de Parkinson en este análisis. Resultado orientativo: patrón compatible con marcha normal."
      : SUMMARY_TEXT;

  return (
    <div
      id="medical-report-content"
      className="mx-auto max-w-4xl rounded-2xl border border-slate-200 border-l-4 border-l-primary bg-white p-8 text-slate-900 shadow-xl shadow-slate-200/80 md:p-12"
    >
      <div className="border-b-2 border-slate-900 pb-6">
        <h1 className="text-3xl font-bold uppercase">
          Informe de análisis de marcha
        </h1>
        <p className="mt-2 text-slate-600">Análisis de Marcha IA</p>
      </div>

      <section className="mt-8">
        <h2 className="text-xl font-bold">Resumen del análisis</h2>
        <div className="mt-4 grid gap-4 rounded-2xl bg-slate-50 p-5 md:grid-cols-2">
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Usuario evaluado
            </p>
            <p className="mt-1 font-semibold">{user?.name || "Usuario"}</p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Fecha del análisis
            </p>
            <p className="mt-1 font-semibold">
              {new Date().toLocaleDateString("es-BO")}
            </p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Video analizado
            </p>
            <p className="mt-1 font-semibold">
              {videoMeta?.name || "Video cargado por el usuario"}
            </p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase text-slate-500">
              Nivel de alerta
            </p>
            <div className="mt-1">
              <AlertBadge level={result.alertLevel} />
            </div>
          </div>
        </div>
        <p className="mt-4 rounded-2xl border border-blue-100 bg-blue-50 p-5 leading-7 text-blue-950 shadow-sm">
          {summaryText}
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-bold">Calidad del video</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          {[
            ["Estado del análisis", analysisCompleted ? "Completado" : "No completado"],
            ["Cuerpo detectado en el video", posePercent],
            ["Momentos analizados", String(result.framesAnalyzed ?? 0)],
            ["Calidad general", result.poseQuality || "Sin dato"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-slate-200 p-4 shadow-sm">
              <p className="text-xs font-bold uppercase text-slate-500">
                {label}
              </p>
              <p className="mt-1 font-semibold">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-bold">Movimiento observado</h2>
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
          <p className="text-xs font-bold uppercase text-slate-500">
            Resultado del análisis visual
          </p>
          <p className="mt-1 text-2xl font-bold">
            {visualResultLabel(result)}
          </p>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-bold">Señales detectadas</h2>
        {result.signals.length > 0 ? (
          <div className="mt-4 space-y-4">
            {result.signals.map((signal) => (
              <div key={signal.name} className="rounded-2xl border border-slate-200 p-4 shadow-sm">
                <h3 className="font-bold">{friendlySignalName(signal.name)}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {signalDetails(signal)}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-3 leading-7 text-slate-700">
            {result.signalEmptyMessage ||
              "No se detectaron señales relevantes en este análisis."}
          </p>
        )}
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-bold">Resultado orientativo</h2>
        <p className="mt-3 leading-7 text-slate-700">
          El sistema puede identificar combinaciones de señales de marcha que
          podrían ser compatibles con un posible patrón asociado a Parkinson.
          Este resultado no confirma una enfermedad y requiere valoración por
          un profesional de salud.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-bold">Recomendaciones</h2>
        <p className="mt-3 leading-7 text-slate-700">{RECOMMENDATION}</p>
        {recommendations.length > 0 && (
          <ul className="mt-3 space-y-2 text-slate-700">
            {recommendations.map((recommendation) => (
              <li key={recommendation}>• {recommendation}</li>
            ))}
          </ul>
        )}
      </section>

      {observations.length > 0 && (
        <section className="mt-8">
          <h2 className="text-xl font-bold">Observaciones</h2>
          <ul className="mt-3 space-y-2 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            {observations.map((warning) => (
              <li key={warning}>• {warning}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <h2 className="text-xl font-bold text-amber-900">
          Advertencia médica
        </h2>
        <p className="mt-3 leading-7 text-amber-800">{MEDICAL_DISCLAIMER}</p>
      </section>
    </div>
  );
}
