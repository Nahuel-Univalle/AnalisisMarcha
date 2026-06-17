export function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "No disponible";
  }

  if (value < 0) return "No disponible";

  const normalized = value <= 1 ? value * 100 : value;
  if (normalized > 100) return "No disponible";

  return `${Math.round(normalized)}%`;
}
