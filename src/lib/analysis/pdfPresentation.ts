import { MODEL_CLASS_PARAMETER, MODEL_CONFIDENCE_PARAMETER } from "./conditionLabels";

/** Display only: never replaces values in a stored analysis or model input. */
export function formatPdfValue(value: string, digits = 3): string {
  const match = value.trim().match(/^([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:e[+-]?\d+)?)(\s*%?)$/i);
  if (!match) return value;
  const number = Number(match[1]);
  if (!Number.isFinite(number)) return value;
  const small = number !== 0 && Math.abs(number) < 10 ** -digits;
  const formatted = new Intl.NumberFormat("es", small
    ? { maximumSignificantDigits: 3, useGrouping: false }
    : { maximumFractionDigits: digits, useGrouping: false }).format(number);
  return formatted + (match[2].includes("%") ? "%" : "");
}

export function pdfParameterLine(parameter: { name: string; value: string; state: string }) {
  const digits = /ritmo|cadencia/i.test(parameter.name) ? 1 : 3;
  const value = formatPdfValue(parameter.value, digits);
  // Machine class identifiers are retained in the record, not repeated as prose.
  const state = parameter.name === MODEL_CLASS_PARAMETER || parameter.name === MODEL_CONFIDENCE_PARAMETER
    ? "" : parameter.state.trim();
  return `${parameter.name}: ${value}${state && state.toLowerCase() !== value.toLowerCase() ? `. ${state}` : ""}`;
}

// New cache namespace (report layout shared with MedicalReport). Previous namespaces are never
// overwritten or deleted; only `canonical-v4` remains readable for old, attested downloads.
export const PDF_PRESENTATION_RENDERER = "canonical-v6-report";
