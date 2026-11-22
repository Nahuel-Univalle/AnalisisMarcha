"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { FileDown, FileText, Search } from "lucide-react";
import { LinkButton } from "@/components/ui/LinkButton";
import { HistoryTimeline, HistoryItem } from "@/components/analysis/HistoryTimeline";
import { SavedReport } from "@/types";
import { storedPatternStatus, storedPatternTitle } from "@/lib/analysis/conditionLabels";
import { formatPercent } from "@/lib/formatPercent";
import { Button } from "@/components/ui/Button";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { fetchReportPdfBlob } from "@/lib/analysis/pdfDownload";

function pdfStatusText(availability: SavedReport["pdfAvailability"], admin: boolean) {
  if (!availability) return "Disponibilidad del archivo sin verificar";
  if (!admin && availability.status === "not_generated") return "Disponible; se genera al abrirlo o descargarlo";
  return availability.message;
}

/**
 * Informes guardados: misma carga que tenía /seguimiento
 * (GET /api/me/reports, o /api/admin/reports para el rol admin).
 * `refreshKey` permite recargar la lista tras guardar un informe nuevo.
 */
export function SavedReportsList({ admin, refreshKey = 0 }: { admin: boolean; refreshKey?: number }) {
  const searchId = useId();
  const [reports, setReports] = useState<Array<SavedReport & { pdfUrl?: string | null }>>([]);
  const [loading, setLoading] = useState(true);
  const [userFilter, setUserFilter] = useState("");
  const [busy, setBusy] = useState<{ id: string; action: "view" | "download" } | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // Abre (pestaña nueva) o descarga el PDF de un informe por las rutas canónicas. Si todavía no se
  // generó, el servidor lo genera una sola vez a petición del usuario; un informe histórico sin
  // archivo nunca se reconstruye (se muestra el motivo).
  async function openOrDownload(id: string, action: "view" | "download") {
    setDownloadError(null);
    setBusy({ id, action });
    // La pestaña se abre dentro del clic (si no, el navegador bloquea la ventana emergente).
    const viewer = action === "view" ? window.open("", "_blank") : null;
    if (action === "view" && !viewer) {
      setDownloadError("El navegador bloqueó la nueva pestaña. Permita las ventanas emergentes para este sitio o use «Descargar PDF».");
      setBusy(null);
      return;
    }
    try {
      const { blob, generated } = await fetchReportPdfBlob(id);
      const url = URL.createObjectURL(blob);
      if (viewer) {
        viewer.location.href = url;
      } else {
        const link = document.createElement("a");
        link.href = url;
        link.download = "informe_analisis_marcha.pdf";
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
      setTimeout(() => URL.revokeObjectURL(url), 5 * 60_000);
      if (generated) setReloadKey((n) => n + 1); // el registro pasa a «PDF disponible»
    } catch (error) {
      viewer?.close();
      setDownloadError(error instanceof Error ? error.message : "El PDF de este informe no está disponible.");
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadReports() {
      setLoading(true);
      try {
        const response = await fetch(admin ? "/api/admin/reports" : "/api/me/reports");
        if (!response.ok) return;
        const payload = (await response.json()) as { reports: Array<SavedReport & { pdfUrl?: string | null }> };
        if (active) setReports(payload.reports);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadReports();

    return () => {
      active = false;
    };
  }, [admin, refreshKey, reloadKey]);

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
        title: report.patternKey !== undefined ? storedPatternTitle(report.patternKey) : report.pattern || report.title,
        pattern: report.patternKey ?? null,
        subtitle: admin && report.userEmail ? `${report.userName} · ${report.userEmail}` : undefined,
        meta: [
          ["Tipo", report.analysisType || "Análisis de marcha"],
          ["Estado", storedPatternStatus(report.patternKey)],
          ...(report.modelConfidence !== null && report.modelConfidence !== undefined
            ? ([["Confianza del modelo", formatPercent(report.modelConfidence)]] as Array<[string, string]>)
            : []),
          ["Fecha", report.date],
          ["PDF", pdfStatusText(report.pdfAvailability, admin)],
        ] as Array<[string, string]>,
        summary: report.summary,
        originalSrc: report.originalVideoUrl || report.localOriginalVideoUrl,
        processedSrc: report.processedVideoUrl || report.localProcessedVideoUrl,
        actions: admin ? undefined : pdfActions(report),
      }));
  }, [admin, reports, userFilter, busy]); // eslint-disable-line react-hooks/exhaustive-deps

  function pdfActions(report: SavedReport) {
    const status = report.pdfAvailability?.status;
    if (status !== "available" && status !== "not_generated") {
      return <p className="self-center text-xs font-semibold text-ink-subtle">PDF no disponible</p>;
    }
    const label = `${report.title}, ${report.date}`;
    const working = busy?.id === report.id ? busy.action : null;
    return (
      <>
        <Button
          variant="outline"
          size="sm"
          aria-label={`Ver informe — ${label}`}
          loading={working === "view"}
          disabled={busy !== null}
          onClick={() => openOrDownload(report.id, "view")}
        >
          {working !== "view" && <FileText aria-hidden />}
          Ver informe
        </Button>
        <Button
          variant="outline"
          size="sm"
          aria-label={`Descargar PDF — ${label}`}
          loading={working === "download"}
          disabled={busy !== null}
          onClick={() => openOrDownload(report.id, "download")}
        >
          {working !== "download" && <FileDown aria-hidden />}
          Descargar PDF
        </Button>
      </>
    );
  }

  return (
    <>
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
    {downloadError && <InlineAlert tone="warning" role="alert">{downloadError}</InlineAlert>}
    </>
  );
}
