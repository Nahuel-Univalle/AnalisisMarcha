"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { LinkButton } from "@/components/ui/LinkButton";
import { HistoryTimeline, HistoryItem } from "@/components/analysis/HistoryTimeline";
import { SavedReport } from "@/types";

/**
 * Informes guardados: misma carga que tenía /seguimiento
 * (GET /api/me/reports, o /api/admin/reports para el rol admin).
 * `refreshKey` permite recargar la lista tras guardar un informe nuevo.
 */
export function SavedReportsList({ admin, refreshKey = 0 }: { admin: boolean; refreshKey?: number }) {
  const searchId = useId();
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [userFilter, setUserFilter] = useState("");

  useEffect(() => {
    let active = true;

    async function loadReports() {
      setLoading(true);
      try {
        const response = await fetch(admin ? "/api/admin/reports" : "/api/me/reports");
        if (!response.ok) return;
        const payload = (await response.json()) as { reports: SavedReport[] };
        if (active) setReports(payload.reports);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadReports();

    return () => {
      active = false;
    };
  }, [admin, refreshKey]);

  const items = useMemo<HistoryItem[]>(() => {
    return reports
      .filter(
        (report) =>
          !admin ||
          !userFilter.trim() ||
          report.userEmail?.toLowerCase().includes(userFilter.toLowerCase()) ||
          report.userName?.toLowerCase().includes(userFilter.toLowerCase())
      )
      .map((report) => ({
        id: report.id,
        date: report.date,
        title: report.pattern || report.title,
        alertLevel: report.alertLevel,
        subtitle: admin && report.userEmail ? `${report.userName} · ${report.userEmail}` : undefined,
        meta: [
          ["Tipo", report.analysisType || "Análisis de marcha"],
          ["Estado", report.patternStatus || "Completado"],
          ["Fecha", report.date],
        ],
        summary: report.summary,
        originalSrc: report.originalVideoUrl || report.localOriginalVideoUrl,
        processedSrc: report.processedVideoUrl || report.localProcessedVideoUrl,
      }));
  }, [admin, reports, userFilter]);

  return (
    <HistoryTimeline
      items={items}
      loading={loading}
      emptyTitle={admin ? "No existen informes registrados en el sistema." : "No tienes informes guardados"}
      emptyDescription={
        admin ? undefined : "Genera el informe de un análisis y guárdalo para que aparezca aquí."
      }
      emptyAction={admin ? undefined : <LinkButton href="/analisis/subir-video">Nuevo análisis</LinkButton>}
      toolbar={
        admin ? (
          <div className="w-full md:max-w-xs">
            <label htmlFor={searchId} className="sr-only">
              Filtrar por usuario o email
            </label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle" aria-hidden />
              <input
                id={searchId}
                type="search"
                value={userFilter}
                onChange={(event) => setUserFilter(event.target.value)}
                placeholder="Filtrar por usuario o email"
                className="h-10 w-full rounded-lg border border-line-strong bg-surface pl-9 pr-3 text-sm text-ink outline-none transition-colors placeholder:text-ink-subtle focus:border-accent-blue"
              />
            </div>
          </div>
        ) : undefined
      }
    />
  );
}
