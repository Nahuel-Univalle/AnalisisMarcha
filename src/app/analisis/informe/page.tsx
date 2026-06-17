"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { MedicalReport } from "@/components/report/MedicalReport";
import { useAnalysis } from "@/context/AnalysisContext";
import { downloadElementAsPdf } from "@/utils/generatePdf";

export default function ReportPage() {
  const { addReport, result } = useAnalysis();
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownload = async () => {
    setDownloadError(null);

    try {
      await downloadElementAsPdf(
        "medical-report-content",
        "informe_analisis_marcha.pdf"
      );
    } catch {
      setDownloadError(
        "No se pudo generar el PDF automáticamente. Se abrirá la impresión del navegador para guardar como PDF."
      );
      window.print();
    }
  };

  const handleSave = async () => {
    setSaveError(null);

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
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : "No se pudo guardar el informe."
      );
    }
  };

  return (
    <AppShell>
      <section className="grid gap-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-4xl font-black text-slate-950">
              Informe médico PDF
            </h1>

            <p className="mt-2 text-slate-600">
              Documento orientativo para presentar a un profesional de salud.
            </p>
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={handleSave}>
              Guardar informe
            </Button>

            <Button onClick={handleDownload}>
              Guardar o imprimir informe
            </Button>
          </div>
        </div>

        {saved && (
          <div className="rounded-2xl bg-green-50 p-4 text-sm font-semibold text-green-700">
            Informe guardado en seguimiento.
          </div>
        )}

        {saveError && (
          <div className="rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700">
            {saveError}
          </div>
        )}

        {downloadError && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-800">
            {downloadError}
          </div>
        )}

        <MedicalReport />
      </section>
    </AppShell>
  );
}
