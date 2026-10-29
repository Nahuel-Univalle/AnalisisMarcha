import { ArrowRight, History } from "lucide-react";
import { LinkButton } from "@/components/ui/LinkButton";
import { GaitFigure } from "@/components/brand/GaitFigure";
import { mockAnalysisResult } from "@/data/mockAnalysis";
import type { AnalysisResult } from "@/types";

/**
 * AnalysisContext arranca con un resultado de ejemplo (mockAnalysisResult)
 * hasta que se completa un análisis real. Las vistas de resultado/informe lo
 * usan para no presentar ese ejemplo como si fuera un análisis del usuario.
 */
export function isPlaceholderResult(result: AnalysisResult) {
  return result === mockAnalysisResult;
}

export function NoAnalysisState({ title, description }: { title: string; description: string }) {
  return (
    <section className="reveal grid overflow-hidden rounded-xl border border-line bg-surface md:grid-cols-[minmax(0,1fr)_220px]">
      <div className="p-8 md:p-10">
        <p className="text-[11px] font-semibold uppercase tracking-[0.09em] text-ink-subtle">Sin análisis en curso</p>
        <h2 className="mt-3 text-2xl font-semibold tracking-[-0.02em] text-ink">{title}</h2>
        <p className="mt-3 max-w-lg text-sm leading-6 text-ink-muted">{description}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <LinkButton href="/analisis/subir-video">
            Nuevo análisis
            <ArrowRight aria-hidden />
          </LinkButton>
          <LinkButton href="/seguimiento" variant="outline">
            <History aria-hidden />
            Ver seguimiento
          </LinkButton>
        </div>
      </div>
      <div className="hidden items-center bg-surface-subtle p-6 md:flex">
        <GaitFigure tone="light" guides={false} />
      </div>
    </section>
  );
}
