import { CSSProperties } from "react";
import { AlertBadge } from "@/components/ui/AlertBadge";

export type TraceFinding = {
  key: string;
  title: string;
  relevance: string;
  text: string;
  severity: string;
};

/**
 * "¿Por qué el sistema identificó este patrón?": hallazgos numerados unidos
 * por una línea vertical (observación → relevancia → explicación). Usa solo
 * los hallazgos y textos que ya produce resultPresentation.ts.
 */
export function FindingsTrace({ findings }: { findings: TraceFinding[] }) {
  return (
    <ol className="relative">
      {findings.map((finding, index) => {
        const last = index === findings.length - 1;
        return (
          <li
            key={finding.key}
            className="reveal relative grid grid-cols-[40px_1fr] gap-x-4"
            style={{ "--i": index + 1 } as CSSProperties}
          >
            <div className="relative flex justify-center">
              <span className="relative z-10 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-primary-soft font-mono text-xs font-medium text-ink">
                {String(index + 1).padStart(2, "0")}
              </span>
              {!last && (
                <span className="fill-y absolute bottom-0 top-9 w-px bg-line" aria-hidden />
              )}
            </div>
            <div className={last ? "pb-1" : "pb-7"}>
              <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 pt-1.5">
                <div className="min-w-0">
                  <h3 className="text-base font-semibold leading-6 text-ink">{finding.title}</h3>
                  <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.08em] text-ink-subtle">
                    {finding.relevance}
                  </p>
                </div>
                <AlertBadge level={finding.severity} size="sm" />
              </div>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-muted">{finding.text}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
