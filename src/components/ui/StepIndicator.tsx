import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

const WORKFLOW = ["Video", "Revisión", "Análisis", "Resultado"];

/**
 * Indicador del flujo de trabajo de 4 pasos (subir → revisar → analizar →
 * resultado). Solo comunica en qué pantalla está el usuario; no es progreso
 * del procesamiento.
 */
export function StepIndicator({ current }: { current: number }) {
  return (
    <nav aria-label="Pasos del análisis" className="reveal min-w-0 border-b border-line pb-5">
      <ol className="flex max-w-[780px] items-center justify-between gap-2 overflow-x-auto pb-1">
        {WORKFLOW.map((step, index) => {
          const done = index < current;
          const active = index === current;
          return (
            <li key={step} className="flex shrink-0 items-center gap-2">
              <span
                aria-current={active ? "step" : undefined}
                className={cn(
                  "inline-flex items-center gap-2 text-[13px] font-semibold",
                  active ? "text-primary-dark" : done ? "text-ink-muted" : "text-ink-subtle"
                )}
              >
                <span
                  className={cn(
                    "inline-flex h-7 w-7 items-center justify-center rounded-full border font-mono text-[11px]",
                    active && "border-primary bg-primary text-white",
                    done && "border-primary bg-primary-soft text-primary",
                    !active && !done && "border-line-strong bg-surface text-ink-subtle"
                  )}
                >
                  {done ? <Check className="h-3.5 w-3.5" aria-hidden /> : index + 1}
                </span>
                {step}
                {done && <span className="sr-only">(completado)</span>}
              </span>
              {index < WORKFLOW.length - 1 && (
                <span className={cn("h-px w-8 md:w-14", done ? "bg-primary" : "bg-line-strong")} aria-hidden />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
