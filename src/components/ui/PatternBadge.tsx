import { cn } from "@/lib/utils";
import { STORED_PATTERN_LABEL, StoredPattern } from "@/lib/analysis/conditionLabels";

/**
 * Patrón de marcha que asignó el modelo experimental (4 clases) o
 * "No concluyente". Es una CLASE, no un nivel: usa estilo neutro a propósito,
 * sin los colores de estado Bajo/Medio/Alto (reservados a AlertBadge).
 */
export function PatternBadge({
  pattern,
  className,
}: {
  pattern: StoredPattern | null | undefined;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 shrink-0 items-center rounded-md border border-line bg-surface-subtle px-1.5 text-[11px] font-semibold whitespace-nowrap text-ink-muted",
        className
      )}
    >
      {pattern ? STORED_PATTERN_LABEL[pattern] : "Sin clasificar"}
    </span>
  );
}
