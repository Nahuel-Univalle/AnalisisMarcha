// Etiquetas legibles de las 4 clases del modelo de marcha.
// Espejo de CLASS_HUMAN_LABEL en scripts/video_training/video_training_common.py.
// El sistema NO emite diagnostico: todo texto es orientativo.

export type GaitClassKey =
  | "normal"
  | "parkinson"
  | "esclerosis_multiple"
  | "riesgo_caida";

export const GAIT_CLASS_ORDER: GaitClassKey[] = [
  "normal",
  "parkinson",
  "esclerosis_multiple",
  "riesgo_caida",
];

type GaitClassInfo = {
  key: GaitClassKey;
  shortLabel: string;
  label: string;
  patternPhrase: string;
  description: string;
};

export const GAIT_CLASS_INFO: Record<GaitClassKey, GaitClassInfo> = {
  normal: {
    key: "normal",
    shortLabel: "Marcha normal",
    label: "Marcha dentro de patrones esperados",
    patternPhrase:
      "El análisis identificó patrones de marcha dentro de lo esperado para una marcha normal.",
    description:
      "No se identificaron señales claras de alteración en la estabilidad, la simetría, la coordinación ni el ritmo de la marcha.",
  },
  parkinson: {
    key: "parkinson",
    shortLabel: "Parkinson",
    label: "Patrón compatible con alteración asociada a Parkinson",
    patternPhrase:
      "El análisis identificó patrones de marcha compatibles con una alteración asociada a Parkinson.",
    description:
      "Se observaron señales que pueden aparecer en patrones asociados a Parkinson, como reducción de amplitud del movimiento, cambios de ritmo o menor balanceo de brazos.",
  },
  esclerosis_multiple: {
    key: "esclerosis_multiple",
    shortLabel: "Esclerosis múltiple",
    label: "Patrón compatible con alteración asociada a Esclerosis Múltiple",
    patternPhrase:
      "El análisis identificó patrones de marcha compatibles con una alteración asociada a Esclerosis Múltiple.",
    description:
      "Se observaron señales que pueden aparecer en patrones asociados a Esclerosis Múltiple, como alteraciones del equilibrio, cambios en la coordinación y patrones de movimiento variables.",
  },
  riesgo_caida: {
    key: "riesgo_caida",
    shortLabel: "Riesgo de caída",
    label: "Patrón compatible con inestabilidad / riesgo de caída",
    patternPhrase:
      "El análisis identificó patrones de marcha compatibles con inestabilidad de la marcha o riesgo de caída.",
    description:
      "Se observaron señales de inestabilidad, cambios en el equilibrio y variaciones del patrón normal de la marcha que pueden asociarse a un mayor riesgo de caída.",
  },
};

// Texto que se persiste en AssociatedCondition.condition (vista de seguimiento
// e historial). Debe depender de la clase realmente detectada, nunca fijo a
// Parkinson.
export const ASSOCIATED_CONDITION_TEXT: Record<GaitClassKey, string> = {
  normal: "Sin alerta específica",
  parkinson: "Posible patrón asociado a Parkinson",
  esclerosis_multiple: "Posible patrón asociado a Esclerosis Múltiple",
  riesgo_caida: "Posible patrón asociado a inestabilidad / riesgo de caída",
};

export function associatedConditionText(key: string | null | undefined): string {
  return isGaitClassKey(key)
    ? ASSOCIATED_CONDITION_TEXT[key]
    : ASSOCIATED_CONDITION_TEXT.normal;
}

export function isGaitClassKey(value: unknown): value is GaitClassKey {
  return (
    typeof value === "string" &&
    (GAIT_CLASS_ORDER as string[]).includes(value)
  );
}

export function gaitClassInfo(key: string | null | undefined): GaitClassInfo {
  return isGaitClassKey(key) ? GAIT_CLASS_INFO[key] : GAIT_CLASS_INFO.normal;
}

export type ClassProbabilities = Partial<Record<GaitClassKey, number>>;

export function normalizeClassProbabilities(
  raw: unknown
): ClassProbabilities | null {
  if (!raw || typeof raw !== "object") return null;
  const source = raw as Record<string, unknown>;
  const out: ClassProbabilities = {};
  let found = false;
  for (const key of GAIT_CLASS_ORDER) {
    const value = Number(source[key]);
    if (Number.isFinite(value)) {
      out[key] = value;
      found = true;
    }
  }
  // compat: modelo binario -> {control, parkinson}
  if (!found) {
    const control = Number(source.control);
    const parkinson = Number(source.parkinson);
    if (Number.isFinite(control) || Number.isFinite(parkinson)) {
      if (Number.isFinite(control)) out.normal = control;
      if (Number.isFinite(parkinson)) out.parkinson = parkinson;
      found = true;
    }
  }
  return found ? out : null;
}

export function detectedClassFrom(
  probabilities: ClassProbabilities | null | undefined
): GaitClassKey {
  if (!probabilities) return "normal";
  let best: GaitClassKey = "normal";
  let bestValue = -Infinity;
  for (const key of GAIT_CLASS_ORDER) {
    const value = probabilities[key];
    if (typeof value === "number" && value > bestValue) {
      bestValue = value;
      best = key;
    }
  }
  return best;
}

export function sortedClassProbabilities(
  probabilities: ClassProbabilities | null | undefined
): Array<{ key: GaitClassKey; label: string; shortLabel: string; probability: number }> {
  if (!probabilities) return [];
  return GAIT_CLASS_ORDER.filter((key) => typeof probabilities[key] === "number")
    .map((key) => ({
      key,
      label: GAIT_CLASS_INFO[key].label,
      shortLabel: GAIT_CLASS_INFO[key].shortLabel,
      probability: probabilities[key] as number,
    }))
    .sort((a, b) => b.probability - a.probability);
}

export function alteredProbabilityFrom(
  probabilities: ClassProbabilities | null | undefined
): number | null {
  if (!probabilities || typeof probabilities.normal !== "number") return null;
  return Math.max(0, Math.min(1, 1 - probabilities.normal));
}
