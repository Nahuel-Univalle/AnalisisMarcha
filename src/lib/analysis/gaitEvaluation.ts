import { getParkinsonDatasetStatsForEvaluation } from "@/lib/datasets/parkinsonDataset";

export type VideoGaitMetrics = {
  walkingSpeed?: number | null;
  asymmetryIndex?: number | null;
  cadence?: number | null;
  doubleSupportRatio?: number | null;
  armSwingScore?: number | null;
  armSwingAsymmetry?: number | null;
  postureInclinationDeg?: number | null;
  rigidityScore?: number | null;
  stepRegularity?: number | null;
};

export type GaitEvaluationResult = {
  alertLevel: "BAJO" | "MEDIO" | "ALTO";
  possibleCondition:
    | "sin_alerta"
    | "posible_parkinson"
    | "posible_alteracion_marcha";
  title: string;
  summary: string;
  detectedSignals: Array<{
    name: string;
    relevance: "BAJO" | "MEDIO" | "ALTO";
    description: string;
  }>;
  explanation: string;
  recommendations: string[];
  datasetWarnings: string[];
};

const FALLBACK_CONTROL = {
  averageSpeed: 1,
  averageAsymmetry: 0.12,
  averageCadence: 105,
  averageDoubleSupport: 0.22,
};

function valueOrFallback(value: number | null | undefined, fallback: number) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function dedupeStrings(values: string[]) {
  return Array.from(new Set(values.filter(Boolean).map((value) => value.trim())));
}

function pushSignal(
  signals: GaitEvaluationResult["detectedSignals"],
  name: string,
  relevance: "BAJO" | "MEDIO" | "ALTO",
  description: string
) {
  if (signals.some((signal) => signal.name === name)) return;
  signals.push({ name, relevance, description });
}

export async function evaluateGaitAgainstParkinsonDataset(
  metrics: VideoGaitMetrics
): Promise<GaitEvaluationResult> {
  const datasetStats = await getParkinsonDatasetStatsForEvaluation();
  const reference = datasetStats.control ?? datasetStats.overall ?? FALLBACK_CONTROL;
  const datasetWarnings = [...datasetStats.warnings];

  if (datasetStats.totalRecords === 0) {
    datasetWarnings.push(
      "El análisis se basa en patrones de referencia disponibles. Para una valoración más precisa, el resultado debe ser revisado por un profesional de salud."
    );
  }

  const averageSpeed = valueOrFallback(
    reference.averageSpeed,
    FALLBACK_CONTROL.averageSpeed
  );
  const averageAsymmetry = valueOrFallback(
    reference.averageAsymmetry,
    FALLBACK_CONTROL.averageAsymmetry
  );
  const averageCadence = valueOrFallback(
    reference.averageCadence,
    FALLBACK_CONTROL.averageCadence
  );
  const averageDoubleSupport = valueOrFallback(
    reference.averageDoubleSupport,
    FALLBACK_CONTROL.averageDoubleSupport
  );

  const signals: GaitEvaluationResult["detectedSignals"] = [];
  const walkingSpeed = metrics.walkingSpeed ?? null;
  const asymmetry = metrics.asymmetryIndex ?? null;
  const cadence = metrics.cadence ?? null;
  const doubleSupport = metrics.doubleSupportRatio ?? null;
  const reducedArmSwing =
    metrics.armSwingScore !== null &&
    metrics.armSwingScore !== undefined &&
    metrics.armSwingScore < 0.45;
  const asymmetricArmSwing =
    metrics.armSwingAsymmetry !== null &&
    metrics.armSwingAsymmetry !== undefined &&
    metrics.armSwingAsymmetry > 0.25;

  if (walkingSpeed !== null && walkingSpeed < averageSpeed * 0.82) {
    pushSignal(
      signals,
      "Marcha lenta",
      "ALTO",
      "El sistema observó una velocidad de desplazamiento reducida durante la caminata."
    );
  }

  if (asymmetry !== null && asymmetry > Math.max(averageAsymmetry * 1.5, 0.18)) {
    pushSignal(
      signals,
      "Asimetría de marcha",
      "MEDIO",
      "El sistema observó diferencias entre el movimiento del lado izquierdo y derecho del cuerpo."
    );
  }

  if (cadence !== null && cadence < averageCadence * 0.85) {
    pushSignal(
      signals,
      "Ritmo de marcha irregular",
      "MEDIO",
      "El sistema observó que el ritmo de la caminata no fue suficientemente regular."
    );
  }

  if (doubleSupport !== null && doubleSupport > averageDoubleSupport * 1.3) {
    pushSignal(
      signals,
      "Estabilidad reducida",
      "MEDIO",
      "El sistema observó variaciones en la postura o en el control del cuerpo durante la caminata."
    );
  }

  if (reducedArmSwing || asymmetricArmSwing) {
    pushSignal(
      signals,
      "Balanceo de brazos reducido o asimétrico",
      "ALTO",
      "El sistema observó menor movimiento o diferencia entre ambos brazos durante la caminata. Esta señal puede aparecer en patrones asociados a Parkinson."
    );
  }

  if (
    metrics.postureInclinationDeg !== null &&
    metrics.postureInclinationDeg !== undefined &&
    metrics.postureInclinationDeg > 12
  ) {
    pushSignal(
      signals,
      "Postura alterada",
      "MEDIO",
      "El sistema observó una inclinación o cambio postural durante el desplazamiento."
    );
  }

  if (
    metrics.rigidityScore !== null &&
    metrics.rigidityScore !== undefined &&
    metrics.rigidityScore > 0.65
  ) {
    pushSignal(
      signals,
      "Menor soltura del movimiento",
      "MEDIO",
      "El sistema observó menor soltura en algunos movimientos durante la caminata."
    );
  }

  if (
    metrics.stepRegularity !== null &&
    metrics.stepRegularity !== undefined &&
    metrics.stepRegularity < 0.55
  ) {
    pushSignal(
      signals,
      "Pasos irregulares",
      "MEDIO",
      "El sistema observó que los pasos no mantuvieron una regularidad constante."
    );
  }

  return {
    alertLevel: "BAJO",
    possibleCondition: "sin_alerta",
    title: "Observaciones detectadas durante la marcha",
    summary:
      "Las observaciones de marcha se presentan como información complementaria. No cambian la decisión final del modelo y requieren valoración profesional si generan preocupación.",
    detectedSignals: signals,
    explanation:
      "El sistema no diagnostica Parkinson ni otra enfermedad; solo identifica observaciones de la marcha que pueden orientar una revisión profesional.",
    recommendations: dedupeStrings([
      "Revisar el resultado con un profesional de salud.",
      "Repetir el análisis si el video no muestra el cuerpo completo o tiene mala iluminación.",
      "No tomar decisiones médicas ni iniciar tratamientos solo con este resultado.",
    ]),
    datasetWarnings: dedupeStrings(datasetWarnings),
  };
}
