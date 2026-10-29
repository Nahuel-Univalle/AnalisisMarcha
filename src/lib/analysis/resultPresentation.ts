// Capa de PRESENTACIÓN de resultados de marcha.
//
// No calcula nada nuevo ni cambia la predicción: traduce los datos que ya
// produce el análisis (clase detectada, coincidencia, calidad, 36 features,
// señales) a dos niveles de lectura:
//
//   Nivel 1  -> "Resumen del análisis"     (usuario general, lenguaje simple)
//   Nivel 2  -> "Análisis detallado"       (profesional, valores cuantitativos)
//
// Ambos niveles parten del MISMO objeto AnalysisResult.

import { AnalysisResult, ModelWarning, SignalSeverity } from "@/types";
import {
  GAIT_CLASS_INFO,
  GAIT_CLASS_ORDER,
  GaitClassKey,
  isGaitClassKey,
} from "@/lib/analysis/conditionLabels";

function normalizeSeverity(value: string | null | undefined): SignalSeverity {
  if (value === "Alto" || value === "Medio" || value === "Bajo") return value;
  return "Info";
}

// ---------------------------------------------------------------------------
//  Textos fijos
// ---------------------------------------------------------------------------

export const ORIENTATION_DISCLAIMER =
  "Este resultado es orientativo y no constituye un diagnóstico médico.";

export const ORIENTATION_DISCLAIMER_LONG =
  "Este resultado es orientativo y no constituye un diagnóstico médico. El análisis se basa exclusivamente en patrones de movimiento observados en el video.";

export const MEDICAL_VIEW_DISCLAIMER =
  "Los resultados corresponden al análisis automatizado de patrones de movimiento y no constituyen un diagnóstico médico. La interpretación clínica debe ser realizada por un profesional.";

// Cierre del PDF: ORIENTATION_DISCLAIMER_LONG ya aparece al inicio del mismo
// documento, así que el cierre se mantiene corto y no redundante en vez de
// repetir el texto completo (usado solo en MedicalReport.tsx).
export const MEDICAL_PDF_CLOSING_DISCLAIMER =
  "Este informe no sustituye una evaluación clínica presencial.";

export const MATCH_LEVEL_NOTE =
  "Este porcentaje representa el grado de coincidencia del análisis con los patrones aprendidos por el modelo. No representa una probabilidad de padecer una enfermedad.";

export const MODEL_DISTRIBUTION_NOTE =
  "Estos porcentajes representan la salida del modelo de clasificación y no corresponden a probabilidades clínicas de padecer una enfermedad.";

// Frase orientativa por categoría (espec. sección 19). Nunca dice "diagnóstico".
export const PATTERN_PHRASE: Record<GaitClassKey, string> = {
  normal: "Marcha sin alteraciones específicas identificadas por el modelo.",
  parkinson: "Patrón compatible con alteración asociada a Parkinson.",
  esclerosis_multiple:
    "Patrón compatible con alteración asociada a Esclerosis Múltiple.",
  riesgo_caida:
    "Patrón compatible con características asociadas a riesgo de caída.",
};

// ---------------------------------------------------------------------------
//  Utilidades numéricas
// ---------------------------------------------------------------------------

export function isReliable(result: AnalysisResult): boolean {
  return result.analysisReliable !== false;
}

function toFraction(value: number | null | undefined): number | null {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }
  if (value < 0) return null;
  const normalized = value > 1 ? value / 100 : value;
  return normalized <= 1 ? normalized : null;
}

export function formatPct(value: number | null | undefined): string {
  const fraction = toFraction(value);
  return fraction === null ? "—" : `${Math.round(fraction * 100)}%`;
}

function num(
  value: number | string | null | undefined
): number | null {
  if (value === null || value === undefined) return null;
  const parsed = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(parsed) ? (parsed as number) : null;
}

function formatNumber(
  value: number | string | null | undefined,
  digits = 3
): string {
  const parsed = num(value);
  if (parsed === null) return "Sin dato";
  const factor = 10 ** digits;
  return String(Math.round(parsed * factor) / factor);
}

// ---------------------------------------------------------------------------
//  Nivel 1 y 2 · Patrón identificado
// ---------------------------------------------------------------------------

export type PatternPresentation = {
  reliable: boolean;
  isNormal: boolean;
  classKey: GaitClassKey | null;
  // Nombre corto orientativo ("Esclerosis Múltiple", "Marcha normal"...).
  orientationName: string;
  // Frase para el usuario ("Patrón compatible con alteración asociada a ...").
  phrase: string;
};

export function patternPresentation(
  result: AnalysisResult
): PatternPresentation {
  const reliable = isReliable(result);
  const classKey = isGaitClassKey(result.detectedClass)
    ? result.detectedClass
    : null;

  if (!reliable || !classKey) {
    return {
      reliable,
      isNormal: false,
      classKey,
      orientationName: reliable
        ? result.detectedClassLabel || "Resultado orientativo"
        : "Análisis no concluyente por calidad del video",
      phrase: reliable
        ? result.detectedClassLabel ||
          "El sistema no pudo asociar la marcha a un patrón específico."
        : "El video no aportó información de marcha suficiente para identificar un patrón.",
    };
  }

  return {
    reliable,
    isNormal: classKey === "normal",
    classKey,
    orientationName: GAIT_CLASS_INFO[classKey].shortLabel,
    phrase: PATTERN_PHRASE[classKey],
  };
}

// ---------------------------------------------------------------------------
//  Nivel de coincidencia con el patrón (reemplaza "confianza del modelo")
// ---------------------------------------------------------------------------

export type MatchLevel = {
  available: boolean;
  fraction: number | null;
  percentText: string; // "96%" | "—"
  label: "Alto" | "Medio" | "Bajo" | "Sin dato";
  note: string;
};

export function matchLevel(result: AnalysisResult): MatchLevel {
  if (!isReliable(result)) {
    return {
      available: false,
      fraction: null,
      percentText: "—",
      label: "Sin dato",
      note: MATCH_LEVEL_NOTE,
    };
  }

  const fraction = toFraction(
    result.confidence ?? result.predictionConfidence
  );

  if (fraction === null) {
    return {
      available: false,
      fraction: null,
      percentText: "—",
      label: "Sin dato",
      note: MATCH_LEVEL_NOTE,
    };
  }

  const label =
    fraction >= 0.8 ? "Alto" : fraction >= 0.5 ? "Medio" : "Bajo";

  return {
    available: true,
    fraction,
    percentText: `${Math.round(fraction * 100)}%`,
    label,
    note: MATCH_LEVEL_NOTE,
  };
}

// ---------------------------------------------------------------------------
//  Calidad del análisis (traduce analysisReliable)
// ---------------------------------------------------------------------------

export type AnalysisQuality = {
  reliable: boolean;
  label: "Adecuada" | "Limitada";
  explanation: string;
};

export function analysisQuality(result: AnalysisResult): AnalysisQuality {
  const reliable = isReliable(result);
  return {
    reliable,
    label: reliable ? "Adecuada" : "Limitada",
    explanation: reliable
      ? "El video presentó condiciones suficientes para realizar el análisis de la marcha."
      : result.qualityMessage ||
        "No fue posible obtener información suficiente de la marcha para realizar un análisis confiable.",
  };
}

// ---------------------------------------------------------------------------
//  Distribución de la predicción del modelo (vista médica)
// ---------------------------------------------------------------------------

export type ClassDistributionRow = {
  key: string;
  shortLabel: string;
  percent: number; // 0..100 redondeado
  fraction: number; // 0..1
};

export function classDistribution(
  result: AnalysisResult
): ClassDistributionRow[] {
  if (!isReliable(result)) return [];

  const list = result.classProbabilitiesList;
  if (list && list.length > 0) {
    return list
      .map((item) => ({
        key: item.key,
        shortLabel:
          item.shortLabel ||
          (isGaitClassKey(item.key)
            ? GAIT_CLASS_INFO[item.key].shortLabel
            : item.label || item.key),
        fraction: Math.max(0, Math.min(1, item.probability)),
        percent: Math.round(Math.max(0, Math.min(1, item.probability)) * 100),
      }))
      .sort((a, b) => b.fraction - a.fraction);
  }

  const byName = result.classProbabilitiesByName;
  if (byName) {
    return Object.entries(byName)
      .map(([key, value]) => {
        const fraction = Math.max(0, Math.min(1, num(value) ?? 0));
        return {
          key,
          shortLabel: isGaitClassKey(key)
            ? GAIT_CLASS_INFO[key].shortLabel
            : key,
          fraction,
          percent: Math.round(fraction * 100),
        };
      })
      .sort((a, b) => b.fraction - a.fraction);
  }

  return [];
}

// ---------------------------------------------------------------------------
//  Clasificación experimental de 4 clases (modelo V4)
// ---------------------------------------------------------------------------
//
//  La confianza se muestra tal cual la produce el modelo, SIN umbrales de
//  "alta/media/baja": la auditoría del modelo encontró errores con confianza
//  alta, así que ningún porcentaje se presenta como garantía.

export const EXPERIMENTAL_DISCLAIMER =
  "Este análisis constituye una orientación basada en patrones de movimiento y no representa un diagnóstico médico. Los resultados corresponden a una clasificación experimental de patrones de marcha y requieren valoración por un profesional de salud.";

export const MODEL_CONFIDENCE_NOTE =
  "Es la confianza del modelo en la clase indicada, no la probabilidad de tener una enfermedad. Una confianza alta no garantiza que la clasificación sea correcta.";

const CLASS_CAVEAT_CODES = new Set(["CLASE_EM_EXPERIMENTAL", "CLASE_RIESGO_NO_VALIDADA"]);

const WARNING_TITLES: Record<string, string> = {
  VIDEO_VERTICAL: "Video vertical",
  CAMARA_MOVIL: "Cámara en movimiento",
  CAMARA_POCO_ESTABLE: "Cámara poco estable",
  POSE_BAJA: "Cuerpo detectado de forma parcial",
  VISTA_NO_VERIFICADA: "Vista de la cámara no verificada",
};

export type ClassificationRow = {
  key: GaitClassKey;
  shortLabel: string;
  percent: number;
  predicted: boolean;
};

export type ExperimentalClassification = {
  available: boolean;
  classKey: GaitClassKey | null;
  shortLabel: string;
  confidenceText: string; // "78%" | "—"
  rows: ClassificationRow[]; // orden fijo de las 4 clases
  caveat: string | null; // texto adicional para EM y riesgo de caída
};

export function experimentalClassification(
  result: AnalysisResult
): ExperimentalClassification {
  const classKey = isGaitClassKey(result.detectedClass) ? result.detectedClass : null;
  const distribution = classDistribution(result);
  const available =
    isReliable(result) && result.experimentalClassification === true && classKey !== null && distribution.length > 0;

  if (!available || !classKey) {
    return { available: false, classKey: null, shortLabel: "", confidenceText: "—", rows: [], caveat: null };
  }

  const byKey = new Map(distribution.map((row) => [row.key, row]));
  const rows = GAIT_CLASS_ORDER.map((key) => ({
    key,
    shortLabel: GAIT_CLASS_INFO[key].shortLabel,
    percent: byKey.get(key)?.percent ?? 0,
    predicted: key === classKey,
  }));
  const caveatWarning = (result.modelWarnings ?? []).find((w) => CLASS_CAVEAT_CODES.has(w.code));

  return {
    available,
    classKey,
    shortLabel: GAIT_CLASS_INFO[classKey].shortLabel,
    confidenceText: formatPct(result.confidence ?? result.predictionConfidence),
    rows,
    caveat: caveatWarning?.message ?? null,
  };
}

export type PresentedModelWarning = {
  code: string;
  title: string;
  message: string;
};

/** Advertencias de calidad del video (las de clase se muestran junto al resultado). */
export function modelQualityWarnings(result: AnalysisResult): {
  alerts: PresentedModelWarning[];
  notes: PresentedModelWarning[];
} {
  const present = (w: ModelWarning): PresentedModelWarning => ({
    code: w.code,
    title: WARNING_TITLES[w.code] ?? "Advertencia",
    message: w.message,
  });
  const quality = (result.modelWarnings ?? []).filter((w) => !CLASS_CAVEAT_CODES.has(w.code));
  return {
    alerts: quality.filter((w) => w.severity !== "info").map(present),
    notes: quality.filter((w) => w.severity === "info").map(present),
  };
}

// ---------------------------------------------------------------------------
//  Hallazgos observados por el sistema (a partir de result.signals)
// ---------------------------------------------------------------------------
//
//  No se inventan hallazgos: se traducen las señales que el análisis ya
//  detectó (y que el gate de calidad / modelo ya filtró) a lenguaje humano.
//  La descripción es NEUTRAL: no atribuye la señal a una enfermedad concreta.

type FindingKind =
  | "marcha_lenta"
  | "ritmo_irregular"
  | "asimetria"
  | "brazos"
  | "estabilidad"
  | "postura";

const FINDING_LIBRARY: Record<
  FindingKind,
  { title: string; relevance: string; user: string; medical: string }
> = {
  marcha_lenta: {
    title: "Marcha lenta",
    relevance: "Velocidad de desplazamiento",
    user: "El sistema observó una velocidad de desplazamiento reducida.",
    medical:
      "El desplazamiento del cuerpo durante la caminata fue menor al de un patrón de marcha típico en el conjunto de referencia.",
  },
  ritmo_irregular: {
    title: "Ritmo de marcha irregular",
    relevance: "Regularidad temporal",
    user: "Se observaron variaciones en la regularidad de los pasos.",
    medical:
      "El intervalo entre pasos no se mantuvo constante a lo largo del video (mayor variabilidad de ritmo).",
  },
  asimetria: {
    title: "Movimiento desigual entre ambos lados",
    relevance: "Simetría izquierda/derecha",
    user:
      "Se observaron diferencias entre el movimiento del lado izquierdo y derecho del cuerpo.",
    medical:
      "Se observó una diferencia entre el movimiento de las extremidades del lado izquierdo y del derecho.",
  },
  brazos: {
    title: "Movimiento de brazos reducido o asimétrico",
    relevance: "Movimiento de brazos",
    user:
      "Se observó menor movimiento o diferencia entre ambos brazos. Esta característica puede presentarse en diferentes alteraciones de la marcha.",
    medical:
      "El balanceo de los brazos fue reducido o desigual entre ambos lados durante la caminata.",
  },
  estabilidad: {
    title: "Estabilidad corporal reducida",
    relevance: "Estabilidad y control postural",
    user:
      "Se observaron variaciones en el control del cuerpo durante la caminata.",
    medical:
      "Se observaron oscilaciones del tronco y variaciones del apoyo compatibles con un control postural menos estable.",
  },
  postura: {
    title: "Postura alterada",
    relevance: "Postura del tronco",
    user: "Se observó una inclinación o cambio postural durante el desplazamiento.",
    medical:
      "Se observó una inclinación del tronco mantenida o variable durante el desplazamiento.",
  },
};

function findingKindFor(name: string): FindingKind | null {
  const n = name.toLowerCase();
  if (n.includes("marcha lenta") || n.includes("lenta")) return "marcha_lenta";
  if (n.includes("ritmo") || n.includes("paso irregular") || n.includes("pasos irregular"))
    return "ritmo_irregular";
  if (n.includes("asimetr")) return "asimetria";
  if (n.includes("brazo")) return "brazos";
  if (n.includes("estabilidad") || n.includes("soltura")) return "estabilidad";
  if (n.includes("postura")) return "postura";
  return null;
}

export type PresentedFinding = {
  kind: FindingKind;
  title: string;
  relevance: string;
  userText: string;
  medicalText: string;
  severity: SignalSeverity; // "Alto" | "Medio" | "Bajo" | "Info"
};

export function presentedFindings(result: AnalysisResult): PresentedFinding[] {
  if (!isReliable(result)) return [];

  const seen = new Set<FindingKind>();
  const out: PresentedFinding[] = [];

  for (const signal of result.signals ?? []) {
    const kind = findingKindFor(signal.name);
    if (!kind || seen.has(kind)) continue;
    seen.add(kind);
    const lib = FINDING_LIBRARY[kind];
    out.push({
      kind,
      title: lib.title,
      relevance: lib.relevance,
      userText: lib.user,
      medicalText: lib.medical,
      severity: normalizeSeverity(signal.relevance),
    });
  }

  return out;
}

export const NO_FINDINGS_TEXT =
  "No se identificaron hallazgos relevantes en la marcha analizada.";

// ---------------------------------------------------------------------------
//  Nivel 1 · Tarjetas "Características observadas" (interpretación, sin cifras)
// ---------------------------------------------------------------------------

export type UserCharacteristicCard = {
  icon: string;
  title: string;
  description: string;
};

function hasFinding(findings: PresentedFinding[], kind: FindingKind): boolean {
  return findings.some((f) => f.kind === kind);
}

export function userCharacteristicCards(
  result: AnalysisResult
): UserCharacteristicCard[] {
  if (!isReliable(result)) return [];

  const findings = presentedFindings(result);
  const features = result.gaitFeatures ?? {};
  const cadence = num(features["estimated_cadence_steps_per_min"]);

  const cards: UserCharacteristicCard[] = [
    {
      icon: "🚶",
      title: "Velocidad al caminar",
      description: hasFinding(findings, "marcha_lenta")
        ? "Se observó una velocidad de desplazamiento reducida durante la caminata."
        : "El desplazamiento del cuerpo durante la caminata se observó dentro de lo esperado.",
    },
    {
      icon: "🔄",
      title: "Ritmo de la caminata",
      description:
        (cadence !== null
          ? `Ritmo estimado de aproximadamente ${Math.round(cadence)} pasos por minuto. `
          : "") +
        (hasFinding(findings, "ritmo_irregular")
          ? "Se observaron variaciones en la regularidad de los pasos."
          : "El ritmo de los pasos se observó regular."),
    },
    {
      icon: "⚖️",
      title: "Estabilidad corporal",
      description: hasFinding(findings, "estabilidad")
        ? "Se observaron variaciones en el control del cuerpo durante la caminata."
        : "El control del cuerpo durante la caminata se observó estable.",
    },
    {
      icon: "↔️",
      title: "Simetría del movimiento",
      description: hasFinding(findings, "asimetria")
        ? "Se observaron diferencias entre el lado izquierdo y el derecho del cuerpo."
        : "Los movimientos de ambos lados del cuerpo se observaron similares.",
    },
    {
      icon: "💪",
      title: "Movimiento de los brazos",
      description: hasFinding(findings, "brazos")
        ? "Se observó una diferencia o una reducción en el movimiento de ambos brazos."
        : "El movimiento de ambos brazos se observó sin diferencias marcadas.",
    },
    {
      icon: "🦵",
      title: "Movimiento de las piernas",
      description: hasFinding(findings, "asimetria")
        ? "Se observaron diferencias en el movimiento de ambas piernas durante la caminata."
        : "El movimiento de ambas piernas se observó dentro de lo esperado.",
    },
    {
      icon: "⏱️",
      title: "Regularidad de la marcha",
      description:
        hasFinding(findings, "ritmo_irregular") ||
        hasFinding(findings, "estabilidad")
          ? "Se observaron variaciones en el patrón de movimiento entre pasos."
          : "El patrón de movimiento se repitió de forma regular entre pasos.",
    },
  ];

  return cards;
}

// ---------------------------------------------------------------------------
//  Nivel 2 · Parámetros cuantitativos de marcha (agrupados + explicación)
// ---------------------------------------------------------------------------

export type QuantParam = {
  label: string;
  value: string;
  unit: string;
  explanation: string;
};

export type QuantGroup = {
  title: string;
  params: QuantParam[];
};

type ParamSpec = {
  feature: string;
  label: string;
  unit: string;
  digits?: number;
  explanation: string;
};

const PARAM_GROUPS: Array<{ title: string; specs: ParamSpec[] }> = [
  {
    title: "Desplazamiento",
    specs: [
      {
        feature: "horizontal_motion_mean",
        label: "Velocidad de desplazamiento (relativa)",
        unit: "",
        explanation:
          "Avance horizontal del cuerpo durante la caminata, normalizado al tamaño de la persona.",
      },
      {
        feature: "hip_center_motion_mean",
        label: "Movimiento del centro de la cadera",
        unit: "",
        explanation:
          "Cantidad de desplazamiento del centro de la pelvis, usado como referencia del avance corporal.",
      },
      {
        feature: "vertical_motion_mean",
        label: "Movimiento vertical del cuerpo",
        unit: "",
        explanation:
          "Oscilación arriba–abajo del cuerpo durante el ciclo de la marcha.",
      },
    ],
  },
  {
    title: "Ritmo y temporalidad",
    specs: [
      {
        feature: "estimated_cadence_steps_per_min",
        label: "Cadencia",
        unit: "pasos/min",
        digits: 0,
        explanation: "Número estimado de pasos realizados por minuto.",
      },
      {
        feature: "step_frequency_hz",
        label: "Frecuencia de pasos",
        unit: "pasos/s",
        digits: 2,
        explanation: "Número estimado de pasos por segundo.",
      },
      {
        feature: "estimated_step_count",
        label: "Pasos estimados en el video",
        unit: "pasos",
        digits: 0,
        explanation: "Cantidad aproximada de pasos detectados en el fragmento analizado.",
      },
      {
        feature: "step_regularity_score",
        label: "Regularidad del paso",
        unit: "",
        explanation:
          "Indica qué tan repetitivo fue el patrón de pasos (valores altos = más regular).",
      },
      {
        feature: "rhythm_variability",
        label: "Variabilidad del ritmo",
        unit: "",
        explanation: "Cuánto varió el tiempo entre pasos a lo largo del video.",
      },
      {
        feature: "gait_variability",
        label: "Variabilidad de la marcha",
        unit: "",
        explanation:
          "Representa cuánto cambia el patrón de movimiento entre los diferentes pasos.",
      },
    ],
  },
  {
    title: "Simetría",
    specs: [
      {
        feature: "leg_motion_asymmetry",
        label: "Asimetría del movimiento de piernas",
        unit: "",
        explanation:
          "Diferencia observada entre el movimiento de la pierna izquierda y la derecha (0 = simétrico).",
      },
      {
        feature: "ankle_vertical_asymmetry",
        label: "Asimetría vertical de tobillos",
        unit: "",
        explanation:
          "Diferencia en la elevación del tobillo izquierdo respecto del derecho.",
      },
      {
        feature: "arm_swing_asymmetry",
        label: "Asimetría del balanceo de brazos",
        unit: "",
        explanation:
          "Diferencia observada entre el balanceo del brazo izquierdo y el derecho.",
      },
    ],
  },
  {
    title: "Estabilidad y postura",
    specs: [
      {
        feature: "posture_stability_score",
        label: "Estabilidad postural",
        unit: "",
        explanation:
          "Indicador calculado a partir del comportamiento del cuerpo durante la caminata (valores altos = más estable).",
      },
      {
        feature: "trunk_sway_mean",
        label: "Balanceo del tronco (medio)",
        unit: "",
        explanation: "Oscilación lateral media del tronco durante la caminata.",
      },
      {
        feature: "trunk_sway_std",
        label: "Balanceo del tronco (variabilidad)",
        unit: "",
        explanation: "Cuánto varió la oscilación lateral del tronco.",
      },
      {
        feature: "trunk_inclination_mean",
        label: "Inclinación media del tronco",
        unit: "",
        explanation: "Inclinación promedio del tronco respecto de la vertical.",
      },
      {
        feature: "trunk_inclination_std",
        label: "Variabilidad de la inclinación del tronco",
        unit: "",
        explanation: "Cuánto varió la inclinación del tronco durante el video.",
      },
    ],
  },
  {
    title: "Movimiento de brazos",
    specs: [
      {
        feature: "arm_swing_mean",
        label: "Amplitud del balanceo de brazos",
        unit: "",
        explanation: "Amplitud media del balanceo de los brazos durante la marcha.",
      },
      {
        feature: "left_arm_range",
        label: "Rango de movimiento del brazo izquierdo",
        unit: "",
        explanation: "Recorrido del brazo izquierdo entre sus posiciones extremas.",
      },
      {
        feature: "right_arm_range",
        label: "Rango de movimiento del brazo derecho",
        unit: "",
        explanation: "Recorrido del brazo derecho entre sus posiciones extremas.",
      },
      {
        feature: "left_wrist_motion_mean",
        label: "Movimiento de la muñeca izquierda",
        unit: "",
        explanation: "Cantidad de movimiento de la muñeca izquierda durante la marcha.",
      },
      {
        feature: "right_wrist_motion_mean",
        label: "Movimiento de la muñeca derecha",
        unit: "",
        explanation: "Cantidad de movimiento de la muñeca derecha durante la marcha.",
      },
    ],
  },
  {
    title: "Movimiento de piernas",
    specs: [
      {
        feature: "ankle_vertical_range_left",
        label: "Elevación del tobillo izquierdo",
        unit: "",
        explanation: "Recorrido vertical del tobillo izquierdo durante el paso.",
      },
      {
        feature: "ankle_vertical_range_right",
        label: "Elevación del tobillo derecho",
        unit: "",
        explanation: "Recorrido vertical del tobillo derecho durante el paso.",
      },
      {
        feature: "knee_vertical_range_left",
        label: "Elevación de la rodilla izquierda",
        unit: "",
        explanation: "Recorrido vertical de la rodilla izquierda durante el paso.",
      },
      {
        feature: "knee_vertical_range_right",
        label: "Elevación de la rodilla derecha",
        unit: "",
        explanation: "Recorrido vertical de la rodilla derecha durante el paso.",
      },
      {
        feature: "left_ankle_motion_mean",
        label: "Movimiento del tobillo izquierdo",
        unit: "",
        explanation: "Cantidad total de movimiento del tobillo izquierdo.",
      },
      {
        feature: "right_ankle_motion_mean",
        label: "Movimiento del tobillo derecho",
        unit: "",
        explanation: "Cantidad total de movimiento del tobillo derecho.",
      },
      {
        feature: "left_knee_motion_mean",
        label: "Movimiento de la rodilla izquierda",
        unit: "",
        explanation: "Cantidad total de movimiento de la rodilla izquierda.",
      },
      {
        feature: "right_knee_motion_mean",
        label: "Movimiento de la rodilla derecha",
        unit: "",
        explanation: "Cantidad total de movimiento de la rodilla derecha.",
      },
    ],
  },
  {
    title: "Coordinación",
    specs: [
      {
        feature: "motion_smoothness",
        label: "Suavidad del movimiento",
        unit: "",
        explanation:
          "Indica qué tan continuo y sin interrupciones fue el movimiento del cuerpo.",
      },
      {
        feature: "body_motion_mean",
        label: "Movimiento corporal global (medio)",
        unit: "",
        explanation: "Cantidad media de movimiento del conjunto del cuerpo.",
      },
      {
        feature: "body_motion_std",
        label: "Movimiento corporal global (variabilidad)",
        unit: "",
        explanation: "Cuánto varió la cantidad de movimiento del cuerpo entre instantes.",
      },
      {
        feature: "shoulder_center_motion_mean",
        label: "Movimiento del centro de los hombros",
        unit: "",
        explanation: "Desplazamiento del punto medio entre ambos hombros.",
      },
    ],
  },
  {
    title: "Medidas corporales de referencia",
    specs: [
      {
        feature: "shoulder_width_mean",
        label: "Ancho de hombros (referencia)",
        unit: "",
        explanation:
          "Medida de referencia usada para normalizar el resto de parámetros; no es un hallazgo clínico.",
      },
      {
        feature: "hip_width_mean",
        label: "Ancho de cadera (referencia)",
        unit: "",
        explanation:
          "Medida de referencia usada para normalizar el resto de parámetros; no es un hallazgo clínico.",
      },
    ],
  },
];

export function quantitativeGroups(
  result: AnalysisResult,
  excludeFeatures?: Set<string>
): QuantGroup[] {
  if (!isReliable(result)) return [];
  const features = result.gaitFeatures;
  if (!features || Object.keys(features).length === 0) return [];

  const groups: QuantGroup[] = [];
  for (const group of PARAM_GROUPS) {
    const params: QuantParam[] = [];
    for (const spec of group.specs) {
      if (!(spec.feature in features)) continue;
      if (excludeFeatures?.has(spec.feature)) continue;
      params.push({
        label: spec.label,
        value: formatNumber(features[spec.feature], spec.digits ?? 3),
        unit: spec.unit,
        explanation: spec.explanation,
      });
    }
    if (params.length > 0) {
      groups.push({ title: group.title, params });
    }
  }
  return groups;
}

// ---------------------------------------------------------------------------
//  Subconjunto comprensible de parámetros (para usuario general y como base
//  de la vista detallada). No inventa datos: selecciona, entre las mismas 36
//  gait features de siempre, solo las que tienen un significado directo
//  (unidad clara o dirección explicable — p. ej. "0 = simétrico"). El resto
//  de las features NO se excluyen del sistema: siguen llegando del backend
//  y siguen disponibles íntegras vía `quantitativeGroups()` (usada por la
//  sección de "información técnica" de la vista detallada en pantalla,
//  `/analisis/evaluacion`). El informe PDF NO usa `quantitativeGroups()`:
//  por decisión explícita del usuario, muestra únicamente el subconjunto
//  curado (`keyGaitMetricGroups`) y no incluye ningún anexo técnico.
// ---------------------------------------------------------------------------

// Nota (revisión de comprensibilidad posterior): se auditó cada una de las 6
// features candidatas contra su cálculo real en
// `scripts/video_training/video_training_common.py` (`build_feature_row`,
// misma función usada en inferencia por
// `scripts/video_training/deep/13_predict_deep_video.py`). Resultado: se
// retiraron 3 de la vista de usuario porque no tienen una lectura directa sin
// inventar una interpretación —
//   - `step_frequency_hz`: redundante con la cadencia (mismo cálculo, otra unidad).
//   - `horizontal_motion_mean`: valor relativo por cuadro sin normalizar por
//     tiempo/FPS; no equivale a una velocidad real.
//   - `posture_stability_score`: score compuesto (1/(1+x)) sin unidad ni
//     umbral validado en el proyecto.
// Las tres features siguen produciéndose y disponibles en `gaitFeatures`
// (y en `quantitativeGroups()`, sin cambios) — esto solo afecta qué se
// destaca en la vista de usuario.
// Tambien se retiro `estimated_step_count` ("Pasos estimados"): es un conteo
// aproximado interno del fragmento, sin lectura clinica propia; la cadencia ya
// resume el ritmo. La feature sigue calculandose y disponible en `gaitFeatures`.
const KEY_METRIC_GROUPS: Array<{ title: string; specs: ParamSpec[] }> = [
  {
    title: "Ritmo",
    specs: [
      {
        feature: "estimated_cadence_steps_per_min",
        label: "Cadencia",
        unit: "pasos/min",
        digits: 0,
        explanation: "Número estimado de pasos realizados por minuto.",
      },
    ],
  },
  {
    title: "Simetría",
    specs: [
      {
        feature: "leg_motion_asymmetry",
        label: "Simetría del movimiento de las piernas",
        unit: "%",
        digits: 0,
        explanation:
          "Diferencia relativa observada entre el movimiento de ambas piernas.",
      },
    ],
  },
];

/** Versión agrupada (por categoría) del subconjunto comprensible — usada en `/analisis/evaluacion`. */
export function keyGaitMetricGroups(result: AnalysisResult): QuantGroup[] {
  if (!isReliable(result)) return [];
  const features = result.gaitFeatures;
  if (!features || Object.keys(features).length === 0) return [];

  const groups: QuantGroup[] = [];
  for (const group of KEY_METRIC_GROUPS) {
    const params: QuantParam[] = [];
    for (const spec of group.specs) {
      if (!(spec.feature in features)) continue;
      // `leg_motion_asymmetry` se calcula como una proporción (0-1); se
      // multiplica por 100 solo para mostrarla como porcentaje — es un
      // cambio de formato, no una interpretación clínica nueva.
      const rawValue =
        spec.feature === "leg_motion_asymmetry"
          ? (() => {
              const fraction = num(features[spec.feature]);
              return fraction === null ? null : fraction * 100;
            })()
          : features[spec.feature];
      params.push({
        label: spec.label,
        value: formatNumber(rawValue, spec.digits ?? 3),
        unit: spec.unit,
        explanation: spec.explanation,
      });
    }
    if (params.length > 0) {
      groups.push({ title: group.title, params });
    }
  }
  return groups;
}

/** Versión plana (sin categorías) del mismo subconjunto — usada en `/analisis/resultado`. */
export function keyGaitMetrics(result: AnalysisResult): QuantParam[] {
  return keyGaitMetricGroups(result).flatMap((group) => group.params);
}

/** Features ya cubiertas por el subconjunto comprensible — para no repetirlas en una lista técnica completa. */
export const KEY_METRIC_FEATURE_KEYS = new Set(
  KEY_METRIC_GROUPS.flatMap((group) => group.specs.map((spec) => spec.feature))
);

// Explicación por categoría para la vista médica (contexto, no diagnóstico).
export function medicalContextNote(classKey: GaitClassKey | null): string {
  switch (classKey) {
    case "parkinson":
      return "En patrones asociados a Parkinson suelen describirse reducción de amplitud del movimiento, disminución del balanceo de brazos y cambios de ritmo. La confirmación corresponde a una valoración clínica.";
    case "esclerosis_multiple":
      return "En patrones asociados a Esclerosis Múltiple suelen describirse alteraciones del equilibrio, cambios de coordinación y mayor variabilidad del movimiento. La confirmación corresponde a una valoración clínica.";
    case "riesgo_caida":
      return "En patrones asociados a riesgo de caída suelen describirse inestabilidad, mayor variabilidad de la marcha y cambios en el equilibrio. La confirmación corresponde a una valoración clínica.";
    case "normal":
      return "El modelo no identificó un patrón de alteración de la marcha. Esto no descarta condiciones que no se expresen en la marcha analizada.";
    default:
      return "";
  }
}
