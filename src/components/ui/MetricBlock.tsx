import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type MetricBlockProps = {
  label: string;
  value: ReactNode;
  unit?: string;
  explanation?: string;
  size?: "md" | "lg";
  className?: string;
};

/**
 * Bloque de medida: rótulo → valor + unidad (mono) → explicación.
 * Varios bloques se agrupan en una misma superficie con divisores,
 * nunca como tarjetas independientes.
 */
export function MetricBlock({ label, value, unit, explanation, size = "md", className }: MetricBlockProps) {
  return (
    <div className={cn("min-w-0", className)}>
      <p className="text-[11px] font-bold uppercase tracking-[0.09em] text-ink-subtle">{label}</p>
      <p className="mt-2 flex items-baseline gap-1.5">
        <span
          className={cn(
            "tabular font-extrabold tracking-[-0.02em] text-ink",
            size === "lg" ? "text-[40px] leading-[44px]" : "text-[28px] leading-8"
          )}
        >
          {value}
        </span>
        {unit && <span className="font-mono text-[13px] font-medium text-ink-muted">{unit}</span>}
      </p>
      {explanation && <p className="mt-2 text-[13px] leading-5 text-ink-muted">{explanation}</p>}
    </div>
  );
}
