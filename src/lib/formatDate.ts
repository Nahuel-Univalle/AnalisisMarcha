// Formato de fechas "YYYY-MM-DD" que ya entrega la API, solo para mostrar.
// Se parsea a mano para evitar desfases de zona horaria de `new Date(str)`.

const MONTHS_SHORT = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MONTHS_LONG = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

function parts(value: string | null | undefined) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value ?? "");
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]) - 1, day: Number(match[3]) };
}

export function formatDayMonth(value: string) {
  const p = parts(value);
  if (!p) return { day: "—", month: "" };
  return { day: String(p.day).padStart(2, "0"), month: MONTHS_SHORT[p.month] };
}

export function formatLongDate(value: string) {
  const p = parts(value);
  if (!p) return value;
  return `${p.day} de ${MONTHS_LONG[p.month]} de ${p.year}`;
}

/** Clave y etiqueta de mes para agrupar ("2026-10" → "Octubre 2026"). */
export function monthGroup(value: string) {
  const p = parts(value);
  if (!p) return { key: "sin-fecha", label: "Sin fecha" };
  const label = MONTHS_LONG[p.month];
  return {
    key: `${p.year}-${String(p.month + 1).padStart(2, "0")}`,
    label: `${label.charAt(0).toUpperCase()}${label.slice(1)} ${p.year}`,
  };
}
