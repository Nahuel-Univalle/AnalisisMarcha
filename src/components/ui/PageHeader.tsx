import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
};

/** Cabecera única de página: un solo h1 por pantalla. */
export function PageHeader({ eyebrow, title, description, actions, className }: PageHeaderProps) {
  return (
    <header
      className={cn(
        "reveal flex flex-col gap-5 md:flex-row md:flex-wrap md:items-end md:justify-between",
        className
      )}
    >
      <div className="min-w-0 md:flex-1 md:basis-[420px]">
        {eyebrow && (
          <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.1em] text-primary-dark">
            {eyebrow}
          </p>
        )}
        <h1 className="text-[28px] font-bold leading-9 tracking-[-0.03em] text-ink md:text-[32px] md:leading-[40px]">
          {title}
        </h1>
        {description && (
          <p className="mt-2.5 max-w-2xl text-[14px] leading-6 text-ink-muted">{description}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

type SectionHeaderProps = {
  index?: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
  as?: "h2" | "h3";
};

/** Encabezado de sección con índice opcional (01, 02…) para páginas largas. */
export function SectionHeader({
  index,
  title,
  description,
  action,
  className,
  as: Heading = "h2",
}: SectionHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div className="min-w-0">
        <Heading className="flex items-baseline gap-3 text-lg font-bold leading-7 text-ink">
          {index && (
            <span className="font-mono text-[13px] font-medium text-accent-cyan-ink">{index}</span>
          )}
          <span>{title}</span>
        </Heading>
        {description && (
          <p className={cn("mt-0.5 text-sm leading-6 text-ink-muted", index && "md:pl-[34px]")}>
            {description}
          </p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

/** Etiqueta pequeña en mayúsculas (rótulos de grupos y medidas). */
export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p className={cn("text-[11px] font-bold uppercase tracking-[0.09em] text-ink-subtle", className)}>
      {children}
    </p>
  );
}
