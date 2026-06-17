import { Card } from "@/components/ui/Card";
import { formatPercent } from "@/lib/formatPercent";
import { AnalysisResult } from "@/types";

type ModelPerformanceCardProps = {
  result: AnalysisResult;
};

const SUMMARY_TEXT =
  "El sistema encontró señales de movimiento que pueden ser compatibles con un posible patrón asociado a Parkinson. Este resultado no confirma una enfermedad y debe ser revisado por un profesional de salud.";
const MEDICAL_DISCLAIMER =
  "Este resultado no constituye diagnóstico médico. Debe ser revisado por un profesional de salud.";
const RECOMMENDATION =
  "Si estos signos se repiten o generan preocupación, se recomienda consultar con un profesional de salud. El sistema solo entrega una orientación inicial.";
const ORIENTATION_NOTE =
  "Resultado orientativo: este análisis no reemplaza una evaluación médica profesional.";

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

  const score = normalizedScore(result.predictionConfidence);

  if (score !== null) {
    if (score < 0.4) return "Señales leves";
    if (score < 0.7) return "Señales moderadas";
    return "Señales relevantes";
  }

  if (result.alertLevel === "Alto") return "Señales relevantes";
  if (result.alertLevel === "Medio") return "Señales moderadas";
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

function validationMethodLabel(method: string | null | undefined) {
  if (method === "group_split_by_subject_id") {
    return "Validación separando personas evaluadas";
  }

  return method || "No disponible";
}

function validationMethodDescription(method: string | null | undefined) {
  if (method === "group_split_by_subject_id") {
    return "El modelo fue probado con personas distintas a las usadas durante el entrenamiento.";
  }

  return null;
}

function formatCount(value: number | null | undefined) {
  return value === null || value === undefined ? "No disponible" : String(value);
}

export function ModelPerformanceCard({ result }: ModelPerformanceCardProps) {
  const analysisCompleted = Boolean(
    result.visualAnalysisCompleted ?? (result.framesAnalyzed ?? 0) > 0
  );
  const modelProbability =
    result.probabilityParkinson ?? result.modelParkinsonProbability;
  const scoreLabel =
    result.modelSource === "video_parkinson_model"
      ? "Probabilidad Parkinson"
      : "Coincidencia visual orientativa";
  const scoreValue =
    result.modelSource === "video_parkinson_model"
      ? formatPercent(modelProbability)
      : formatPercent(result.predictionConfidence);
  const summaryText =
    result.signals.length === 0
      ? result.signalEmptyMessage ||
        "El sistema no detectó señales relevantes asociadas a patrones de Parkinson en este análisis. Este resultado no reemplaza una evaluación médica profesional."
      : SUMMARY_TEXT;

  return (
    <Card>
      <h2 className="text-2xl font-black text-slate-950">
        Resultado orientativo del análisis visual
      </h2>

      <p className="mt-3 max-w-3xl leading-7 text-slate-600">
        {summaryText}
      </p>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {[
          [
            scoreLabel,
            scoreValue,
          ],
          ["Nivel de alerta", result.alertLevel],
          [
            "Estado del análisis",
            analysisCompleted ? "Completado" : "No completado",
          ],
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl bg-cyan-50 p-4">
            <p className="text-sm font-semibold text-cyan-700">{label}</p>
            <p className="mt-1 text-2xl font-black text-slate-950">{value}</p>
          </div>
        ))}
      </div>

      <p className="mt-4 text-sm font-semibold text-slate-600">
        {ORIENTATION_NOTE}
      </p>

      <section className="mt-6">
        <h3 className="text-xl font-black text-slate-950">
          Señales observadas
        </h3>
        {result.signals.length > 0 ? (
          <ul className="mt-3 space-y-2 text-slate-700">
            {result.signals.map((signal) => (
              <li key={signal.name}>• {friendlySignalName(signal.name)}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-slate-600">
            {result.signalEmptyMessage ||
              "No se detectaron señales relevantes en este análisis."}
          </p>
        )}
      </section>

      <section className="mt-6 rounded-2xl bg-slate-50 p-4">
        <h3 className="font-black text-slate-950">Recomendación</h3>
        <p className="mt-2 leading-6 text-slate-700">{RECOMMENDATION}</p>
      </section>

      <p className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-800">
        {MEDICAL_DISCLAIMER}
      </p>

      <details className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
        <summary className="cursor-pointer font-bold text-slate-950">
          Ver detalles técnicos del modelo
        </summary>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {[
            ["Origen del análisis", result.modelSource || "No disponible"],
            [
              "Confianza",
              formatPercent(result.confidence ?? result.predictionConfidence),
            ],
            ["Probabilidad Parkinson", formatPercent(result.probabilityParkinson)],
            ["Probabilidad normal", formatPercent(result.probabilityNormal)],
            ["Nivel de riesgo", result.riskLevel || result.alertLevel],
            ["Exactitud interna del modelo", formatPercent(result.modelAccuracy)],
            ["Precisión interna", formatPercent(result.modelPrecision)],
            ["Sensibilidad", formatPercent(result.modelRecall)],
            ["F1-score", formatPercent(result.modelF1Score)],
            ["Datos usados", formatCount(result.modelSamples)],
            [
              "Control / Parkinson",
              `${formatCount(result.modelControlSamples)} / ${formatCount(
                result.modelParkinsonSamples
              )}`,
            ],
            [
              "Train / test",
              `${formatCount(result.modelTrainSize)} / ${formatCount(
                result.modelTestSize
              )}`,
            ],
            [
              "Método de validación",
              validationMethodLabel(result.validationMethod),
            ],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl bg-slate-50 p-3">
              <p className="font-semibold text-slate-500">{label}</p>
              <p className="mt-1 font-bold text-slate-950">{value}</p>
            </div>
          ))}
        </div>

        {validationMethodDescription(result.validationMethod) && (
          <p className="mt-4 leading-6 text-slate-600">
            {validationMethodDescription(result.validationMethod)}
          </p>
        )}

        <p className="mt-4 leading-6 text-slate-600">
          Resultado del análisis visual: {visualResultLabel(result)}.
        </p>

        {result.validationMethod && (
          <p className="mt-2 text-xs text-slate-500">
            Valor técnico original: {result.validationMethod}
          </p>
        )}
      </details>
    </Card>
  );
}
