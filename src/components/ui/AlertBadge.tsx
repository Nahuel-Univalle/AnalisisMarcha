import { CircleAlert, CircleCheck, Info, LucideIcon, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

type LevelKey = "Alto" | "Medio" | "Bajo" | "Info";

type LevelStyle = {
  label: string;
  bars: number;
  icon: LucideIcon;
  tag: string;
  fg: string;
  bar: string;
  rail: string;
};

/**
 * Único mapa nivel → color del producto. El nivel nunca depende solo del
 * color: siempre va con ícono, palabra y un medidor de 3 segmentos.
 */
export const LEVEL_STYLES: Record<LevelKey, LevelStyle> = {
  Alto: {
    label: "Alto",
    bars: 3,
    icon: TriangleAlert,
    tag: "border-danger-line bg-danger-bg text-danger",
    fg: "text-danger",
    bar: "bg-danger",
    rail: "bg-danger",
  },
  Medio: {
    label: "Medio",
    bars: 2,
    icon: CircleAlert,
    tag: "border-warning-line bg-warning-bg text-warning",
    fg: "text-warning",
    bar: "bg-warning",
    rail: "bg-warning",
  },
  Bajo: {
    label: "Bajo",
    bars: 1,
    icon: CircleCheck,
    tag: "border-success-line bg-success-bg text-success",
    fg: "text-success",
    bar: "bg-success",
    rail: "bg-success",
  },
  Info: {
    label: "Sin dato",
    bars: 0,
    icon: Info,
    tag: "border-line bg-surface-subtle text-ink-muted",
    fg: "text-ink-muted",
    bar: "bg-ink-subtle",
    rail: "bg-line-strong",
  },
};

export function levelKey(level: string | null | undefined): LevelKey {
  if (level === "Alto" || level === "Medio" || level === "Bajo") return level;
  return "Info";
}

export function LevelMeter({
  level,
  size = "sm",
  animated = false,
}: {
  level: string;
  size?: "sm" | "lg";
  animated?: boolean;
}) {
  const style = LEVEL_STYLES[levelKey(level)];

  return (
    <span className="inline-flex items-end gap-0.75" aria-hidden>
      {[0, 1, 2].map((index) => (
        <span
          key={index}
          className={cn(
            "overflow-hidden rounded-xs",
            size === "lg" ? "h-2 w-7" : "h-1.5 w-2.5",
            index < style.bars && !animated ? style.bar : "bg-line"
          )}
        >
          {animated && index < style.bars && (
            <span
              className={cn("fill-x block h-full w-full", style.bar)}
              style={{ animationDelay: `${300 + index * 90}ms` }}
            />
          )}
        </span>
      ))}
    </span>
  );
}

type AlertBadgeProps = {
  level: string;
  size?: "sm" | "md";
  className?: string;
};

export function AlertBadge({ level, size = "md", className }: AlertBadgeProps) {
  const key = levelKey(level);
  const style = LEVEL_STYLES[key];
  const Icon = style.icon;
  const text = key === "Info" ? (level && level !== "Info" ? level : style.label) : style.label;

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-md border font-bold whitespace-nowrap",
        size === "sm" ? "h-6 px-1.5 text-[11px]" : "h-7 px-2 text-xs",
        style.tag,
        className
      )}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} aria-hidden />
      <span>{text}</span>
      {style.bars > 0 && <LevelMeter level={key} />}
    </span>
  );
}
