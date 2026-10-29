import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const DEFAULT_TEXT =
  "Este sistema no reemplaza una valoración médica profesional. El resultado es una orientación inicial generada a partir del análisis visual de la marcha.";

type MedicalDisclaimerProps = {
  /** `inline`: una línea discreta. `block`: aviso con título. */
  variant?: "inline" | "block";
  title?: string;
  text?: string;
  className?: string;
};

/**
 * Aviso médico permanente. Tratamiento NEUTRO a propósito: aparece en todo
 * resultado (incluido "Bajo"); en ámbar diluiría el significado de "Medio".
 */
export function MedicalDisclaimer({
  variant = "block",
  title = "Advertencia médica",
  text = DEFAULT_TEXT,
  className,
}: MedicalDisclaimerProps) {
  if (variant === "inline") {
    return (
      <p className={cn("flex items-start gap-2 text-[13px] leading-5 text-ink-muted", className)}>
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" aria-hidden />
        <span>{text}</span>
      </p>
    );
  }

  return (
    <aside
      className={cn(
        "rounded-xl border border-line border-l-[3px] border-l-navy-700 bg-surface-subtle p-4",
        className
      )}
    >
      <p className="flex items-center gap-2 text-[13px] font-bold text-ink">
        <ShieldCheck className="h-4 w-4 text-navy-700" aria-hidden />
        {title}
      </p>
      <p className="mt-1.5 text-[13px] leading-5 text-ink-muted">{text}</p>
    </aside>
  );
}
