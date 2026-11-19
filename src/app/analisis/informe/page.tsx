"use client";

import { CSSProperties, useState } from "react";
import { BookmarkCheck, BookmarkPlus, FileDown, FileText, Plus } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { LinkButton } from "@/components/ui/LinkButton";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { PageHeader, SectionHeader } from "@/components/ui/PageHeader";
import { MedicalReport } from "@/components/report/MedicalReport";
import { isPlaceholderResult } from "@/components/analysis/NoAnalysisState";
import { SavedReportsList } from "@/components/analysis/SavedReportsList";
import { useAnalysis } from "@/context/AnalysisContext";


export default function ReportPage() {
  const { addReport, result } = useAnalysis();
  const [saved, setSaved] = useState(false);
  const [savedCount, setSavedCount] = useState(0);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownload = async () => {
    setDownloadError(null);
    setDownloading(true);

    try {
      const recordResponse = await fetch("/api/me/reports", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysisId: result.id, title: result.title || "Informe de análisis de marcha" }),
      });
      const record = await recordResponse.json();
      if (!recordResponse.ok || !record.report?.id) throw new Error("No se pudo registrar el informe.");
      const url = `/api/me/reports/${record.report.id}/pdf`;
      let existing = await fetch(url, { cache: "no-store" });
      let pdfBlob: Blob;
      if (existing.ok) {
        pdfBlob = await existing.blob();
      } else {
        if (existing.status !== 404) throw new Error("No se pudo consultar el PDF.");
        const generation = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
        if (!generation.ok) throw new Error("No se pudo generar el PDF canónico en el servidor.");
        existing = await fetch(url, { cache: "no-store" });
        if (!existing.ok) throw new Error("No se pudo recuperar el PDF canónico.");
        pdfBlob = await existing.blob();
      }
      const objectUrl = URL.createObjectURL(pdfBlob);
      const link = document.createElement("a"); link.href = objectUrl; link.download = "informe_analisis_marcha.pdf";
      document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
      setSaved(true);
      setSavedCount((count) => count + 1);
    } catch {
      setDownloadError(
        "No se pudo completar la generación o el guardado del PDF. Si el archivo ya se descargó, consérvalo; su descarga posterior podría no estar disponible."
      );
    } finally {
      setDownloading(false);
    }
  };

  const handleSave = async () => {
    setSaveError(null);
    setSaving(true);

    try {
      const response = await fetch("/api/me/reports", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          analysisId: result.id,
          title: result.title || "Informe de análisis de marcha",
        }),
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.message || "No se pudo guardar el informe.");
      }

      addReport();
      setSaved(true);
      setSavedCount((count) => count + 1);
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : "No se pudo guardar el informe."
      );
    } finally {
      setSaving(false);
    }
  };

  const savedSection = (
    <section className="reveal grid gap-4" style={{ "--i": 2 } as CSSProperties}>
      <SectionHeader
        title="Informes guardados"
        description="Informes que guardaste a partir de tus análisis."
      />
      <SavedReportsList admin={false} refreshKey={savedCount} />
    </section>
  );

  if (isPlaceholderResult(result)) {
    return (
      <AppShell>
        <div className="grid gap-10">
          <PageHeader
            eyebrow="Informes"
            title="Informes médicos"
            description="Documentos orientativos para presentar a un profesional de salud."
            actions={
              <LinkButton href="/analisis/subir-video">
                <Plus aria-hidden />
                Nuevo análisis
              </LinkButton>
            }
          />
          <div className="reveal flex items-start gap-4 rounded-xl border border-line border-l-[3px] border-l-primary bg-surface px-6 py-5 shadow-raised" style={{ "--i": 1 } as CSSProperties}>
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary"><FileText className="h-5 w-5" aria-hidden /></span>
            <p className="text-sm leading-6 text-ink-muted">
              <span className="font-semibold text-ink">Generar un informe nuevo.</span>{" "}
              El informe se prepara al terminar un análisis; desde el resultado
              podrás revisarlo, descargarlo en PDF y guardarlo.
            </p>
          </div>
          {savedSection}
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="grid gap-6">
        <PageHeader
          eyebrow="Informes"
          title="Informe médico"
          description="Documento orientativo para presentar a un profesional de salud."
          actions={
            <>
              <Button variant="outline" onClick={handleSave} loading={saving} disabled={saved}>
                {saved ? <BookmarkCheck aria-hidden /> : !saving && <BookmarkPlus aria-hidden />}
                {saved ? "Guardado en seguimiento" : "Guardar en seguimiento"}
              </Button>
              <Button onClick={handleDownload} loading={downloading}>
                {!downloading && <FileDown aria-hidden />}
                {downloading ? "Generando PDF…" : "Descargar PDF"}
              </Button>
            </>
          }
        />

        {saved && (
          <InlineAlert tone="success">Informe guardado en seguimiento.</InlineAlert>
        )}

        {saveError && <InlineAlert tone="error">{saveError}</InlineAlert>}

        {downloadError && (
          <InlineAlert tone="warning">{downloadError}</InlineAlert>
        )}

        <div className="reveal report-workspace">
          <div className="report-workspace-bar">
            <span className="inline-flex items-center gap-2 font-semibold"><FileText className="h-4 w-4 text-primary" aria-hidden /> Vista previa del informe</span>
            <span>Documento PDF · A4</span>
          </div>
          <div className="report-sheet"><MedicalReport /></div>
        </div>

        <div className="mt-4">{savedSection}</div>
      </div>
    </AppShell>
  );
}
