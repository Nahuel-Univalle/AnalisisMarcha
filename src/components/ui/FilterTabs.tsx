"use client";

import { cn } from "@/lib/utils";

type Option = { value: string; label: string; count?: number };

type FilterTabsProps = {
  label: string;
  options: Option[];
  value: string;
  onChange: (value: string) => void;
};

/** Control segmentado para filtros excluyentes (p. ej. nivel de alerta). */
export function FilterTabs({ label, options, value, onChange }: FilterTabsProps) {
  return (
    <div role="group" aria-label={label} className="inline-flex max-w-full flex-wrap gap-1 rounded-lg bg-surface-subtle p-1">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={cn(
              "inline-flex h-8 items-center gap-2 rounded-md px-3 text-[13px] font-semibold transition-colors duration-150",
              active
                ? "bg-primary-soft text-primary-dark"
                : "text-ink-muted hover:text-ink"
            )}
          >
            {option.label}
            {option.count !== undefined && (
              <span className={cn("rounded px-1 font-mono text-[11px]", active ? "bg-surface text-primary" : "text-ink-subtle")}>
                {option.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
