import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ProcessingTimelineProps = {
  steps: string[];
  /** Etapa resaltada por la secuencia existente de la página. */
  current: number;
  /** true mientras la petición al servidor sigue en curso. */
  processing: boolean;
  /** true solo cuando el servidor respondió con éxito. */
  completed: boolean;
  failed: boolean;
};

/**
 * Etapas del análisis sobre superficie clara. No inventa progreso: no hay
 * porcentajes, y la última etapa sigue "en curso" hasta que el servidor
 * responde de verdad (aunque la secuencia visual ya haya llegado al final).
 */
export function ProcessingTimeline({ steps, current, processing, completed, failed }: ProcessingTimelineProps) {
  return (
    <ol className="relative" aria-label="Etapas del análisis">
      {steps.map((step, index) => {
        const isFirst = index === 0;
        const state: "done" | "passed" | "active" | "error" | "pending" = completed
          ? "done"
          : failed && index === Math.min(current, steps.length - 1)
            ? "error"
            : isFirst
              ? "done"
              : index < current
                ? "passed"
                : index === current && (processing || current < steps.length - 1)
                  ? "active"
                  : "pending";
        const last = index === steps.length - 1;

        return (
          <li key={step} className="relative flex gap-3.5 pb-5 last:pb-0">
            {!last && (
              <span className="absolute left-[11px] top-7 bottom-0 w-px bg-line" aria-hidden>
                {(state === "done" || state === "passed") && (
                  <span className="fill-y block h-full w-full bg-primary/40" />
                )}
              </span>
            )}
            <span
              className={cn(
                "relative z-10 mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition-colors duration-200",
                state === "done" && "border-primary bg-primary text-white",
                state === "passed" && "border-primary/40 bg-primary-soft text-primary-dark",
                state === "active" && "ring-pulse border-primary bg-surface",
                state === "error" && "border-danger bg-danger text-white",
                state === "pending" && "border-line-strong bg-surface"
              )}
              aria-hidden
            >
              {(state === "done" || state === "passed") && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
              {state === "active" && <span className="h-2 w-2 rounded-full bg-primary" />}
              {state === "error" && <X className="h-3.5 w-3.5" strokeWidth={3} />}
            </span>
            <div className="min-w-0 pt-0.5">
              <p
                className={cn(
                  "text-sm leading-5",
                  state === "active" ? "font-semibold text-ink" : "font-medium",
                  (state === "done" || state === "passed") && "text-ink-muted",
                  state === "pending" && "text-ink-subtle",
                  state === "error" && "font-semibold text-danger"
                )}
              >
                {step}
              </p>
              {state === "active" && (
                <p className="mt-0.5 text-xs text-ink-muted">en curso</p>
              )}
              {state === "error" && (
                <p className="mt-0.5 text-xs text-danger">no se pudo completar</p>
              )}
              <span className="sr-only">
                {state === "done" ? "completada" : state === "passed" ? "realizada" : state === "active" ? "en curso" : state === "error" ? "con error" : "pendiente"}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
