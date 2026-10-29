import { cn } from "@/lib/utils";
import type { ClassificationRow } from "@/lib/analysis/resultPresentation";

type ClassificationBreakdownProps = {
  rows: ClassificationRow[];
  className?: string;
};

/**
 * Distribución de la clasificación experimental entre las 4 clases, en orden
 * fijo. La clase predicha se marca con color primario y peso; el porcentaje
 * va siempre en texto (la barra es solo apoyo visual). Solo tokens HEX y sin
 * modificadores de opacidad: también se usa en el informe PDF.
 */
export function ClassificationBreakdown({ rows, className }: ClassificationBreakdownProps) {
  return (
    <ul className={cn("space-y-3", className)}>
      {rows.map((row) => (
        <li key={row.key}>
          <div className="flex items-baseline justify-between gap-3 text-sm">
            <span className={cn("min-w-0", row.predicted ? "font-semibold text-ink" : "text-ink-muted")}>
              {row.shortLabel}
              {row.predicted && <span className="sr-only"> (clase indicada por el modelo)</span>}
            </span>
            <span
              className={cn(
                "shrink-0 font-mono text-[13px] tabular-nums",
                row.predicted ? "font-semibold text-ink" : "text-ink-subtle"
              )}
            >
              {row.percent}%
            </span>
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-sm bg-surface-subtle" aria-hidden>
            <div
              className={cn("h-full rounded-sm", row.predicted ? "bg-primary" : "bg-line-strong")}
              style={{ width: `${row.percent}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
