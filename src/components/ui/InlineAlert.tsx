import { HTMLAttributes } from "react";
import { CircleCheck, Info, ShieldAlert, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "error" | "warning" | "success" | "info";

const TONE_CLASSES: Record<Tone, string> = {
  error: "border-danger-line bg-danger-bg text-danger",
  warning: "border-warning-line bg-warning-bg text-warning",
  success: "border-success-line bg-success-bg text-success",
  info: "border-line bg-surface-subtle text-ink-muted",
};

const TONE_ICON: Record<Tone, typeof TriangleAlert> = {
  error: ShieldAlert,
  warning: TriangleAlert,
  success: CircleCheck,
  info: Info,
};

type InlineAlertProps = HTMLAttributes<HTMLDivElement> & {
  tone?: Tone;
  icon?: boolean;
};

/** Mensaje de feedback en línea (error, confirmación, advertencia). */
export function InlineAlert({ tone = "info", icon = true, className, children, ...props }: InlineAlertProps) {
  const Icon = TONE_ICON[tone];

  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "fade-in flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm font-medium",
        TONE_CLASSES[tone],
        className
      )}
      {...props}
    >
      {icon && <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />}
      <div className="min-w-0">{children}</div>
    </div>
  );
}
