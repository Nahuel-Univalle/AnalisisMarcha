import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type EmptyStateProps = {
  visual?: ReactNode;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
};

export function EmptyState({ visual, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-start gap-4 py-2 sm:flex-row sm:items-center", className)}>
      {visual && <div className="shrink-0">{visual}</div>}
      <div className="min-w-0 flex-1">
        <p className="text-base font-semibold text-ink">{title}</p>
        {description && <p className="mt-1 max-w-xl text-sm leading-6 text-ink-muted">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

/** Bloque gris de carga (en lugar de "..."). */
export function Skeleton({ className }: { className?: string }) {
  return <span className={cn("block animate-pulse rounded-md bg-line/70", className)} aria-hidden />;
}
