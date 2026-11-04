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
};

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

// Observaciones complementarias a partir de métricas del propio video. No
// intervienen en la clase ni en la confianza, que provienen solo del modelo.
export function evaluateVideoGaitObservations(
  metrics: VideoGaitMetrics
): GaitEvaluationResult {
  const signals: GaitEvaluationResult["detectedSignals"] = [];
  const reducedArmSwing =
    metrics.armSwingScore !== null &&
    metrics.armSwingScore !== undefined &&
    metrics.armSwingScore < 0.45;
  const asymmetricArmSwing =
    metrics.armSwingAsymmetry !== null &&
    metrics.armSwingAsymmetry !== undefined &&
    metrics.armSwingAsymmetry > 0.25;

  if (reducedArmSwing || asymmetricArmSwing) {
    pushSignal(
      signals,
      "Balanceo de brazos reducido o asimétrico",
      "ALTO",
      "El sistema observó menor movimiento o diferencia entre ambos brazos durante la caminata. Esta característica puede presentarse en diferentes alteraciones de la marcha."
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
  };
}
