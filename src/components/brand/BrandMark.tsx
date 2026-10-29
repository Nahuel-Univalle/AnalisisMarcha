import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

/** Logo: ícono de onda (marca existente) + nombre del producto. */
export function BrandMark({ tone = "dark", className }: { tone?: "dark" | "light"; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "inline-flex h-9 w-9 items-center justify-center rounded-[10px]",
          tone === "light" ? "bg-white/10 text-white" : "bg-primary-soft text-primary-dark"
        )}
      >
        <Activity className="h-[18px] w-[18px]" strokeWidth={2.25} aria-hidden />
      </span>
      <span
        className={cn(
          "text-[15px] font-bold leading-tight tracking-[-0.01em]",
          tone === "light" ? "text-white" : "text-ink"
        )}
      >
        Análisis de Marcha <span className={tone === "light" ? "text-accent-cyan" : "text-primary"}>IA</span>
      </span>
    </span>
  );
}
