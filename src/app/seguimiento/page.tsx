"use client";

import { CSSProperties, useEffect, useMemo, useState } from "react";
import { FileCheck2, Plus } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { LinkButton } from "@/components/ui/LinkButton";
import { PageHeader } from "@/components/ui/PageHeader";
import { HistoryTimeline, HistoryItem } from "@/components/analysis/HistoryTimeline";
import { SavedReportsList } from "@/components/analysis/SavedReportsList";
import { useAuth } from "@/context/AuthContext";
import { StoredPattern, storedPatternStatus, storedPatternTitle } from "@/lib/analysis/conditionLabels";
import { formatPercent } from "@/lib/formatPercent";

// Forma de GET /api/me/analyses (endpoint existente, sin cambios).
type ApiAnalysis = {
  id: string;
  date: string;
  pattern: StoredPattern | null;
  modelConfidence: number | null;
  summary: string;
  reportId: string | null;
  video: {
    originalVideoUrl: string | null;
    processedVideoUrl: string | null;
  };
  conditions: Array<{ condition: string; status: string }>;
};

export default function TrackingPage() {
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";

  return (
    <AppShell>
      <div className="grid gap-8">
        <PageHeader
          eyebrow={admin ? "Administración" : "Historial"}
          title={admin ? "Informes guardados del sistema" : "Seguimiento de análisis"}
          description={
            admin
              ? "Vista global de informes generados por todos los usuarios."
              : "Tus análisis anteriores en orden cronológico. Esta sección no reemplaza controles médicos."
          }
          actions={
            !admin ? (
              <LinkButton href="/analisis/subir-video">
                <Plus aria-hidden />
                Nuevo análisis
              </LinkButton>
            ) : undefined
          }
        />

        <section className="reveal" style={{ "--i": 1 } as CSSProperties}>
          {admin ? <SavedReportsList admin /> : <AnalysisHistory />}
        </section>
      </div>
    </AppShell>
  );
}

function AnalysisHistory() {
  const [analyses, setAnalyses] = useState<ApiAnalysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAnalyses() {
      try {
        const response = await fetch("/api/me/analyses");
        if (!response.ok) return;
        const payload = (await response.json()) as { analyses: ApiAnalysis[] };
        if (active) setAnalyses(payload.analyses);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAnalyses();

    return () => {
      active = false;
    };
  }, []);

  const items = useMemo<HistoryItem[]>(
    () =>
      analyses.map((analysis) => {
        return {
          id: analysis.id,
          date: analysis.date,
          title: storedPatternTitle(analysis.pattern),
          pattern: analysis.pattern,
          meta: [
            ["Tipo", "Análisis de marcha"],
            ["Estado", storedPatternStatus(analysis.pattern)],
            ...(analysis.modelConfidence !== null && analysis.modelConfidence !== undefined
              ? ([["Confianza del modelo", formatPercent(analysis.modelConfidence)]] as Array<[string, string]>)
              : []),
            ["Fecha", analysis.date],
          ],
          summary: analysis.summary,
          originalSrc: analysis.video?.originalVideoUrl,
          processedSrc: analysis.video?.processedVideoUrl,
          tag: analysis.reportId ? (
            <span className="inline-flex h-6 items-center gap-1 rounded-md border border-line bg-surface-subtle px-1.5 text-[11px] font-semibold text-ink-muted">
              <FileCheck2 className="h-3 w-3 text-primary" aria-hidden />
              Informe guardado
            </span>
          ) : undefined,
        };
      }),
    [analyses]
  );

  return (
    <HistoryTimeline
      items={items}
      loading={loading}
      emptyTitle="Todavía no tienes análisis"
      emptyDescription="Cuando realices tu primer análisis, aparecerá aquí en orden cronológico."
      emptyAction={<LinkButton href="/analisis/subir-video">Nuevo análisis</LinkButton>}
    />
  );
}
