"use client";

import { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/ui/PageHeader";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";
import { ValidationChecklist } from "@/components/analysis/ValidationChecklist";
import { VideoStage } from "@/components/analysis/VideoStage";
import { useAnalysis } from "@/context/AnalysisContext";

export default function ValidationPage() {
  const router = useRouter();
  const { videoFile, videoUrl, videoMeta } = useAnalysis();

  const valid = Boolean(videoFile);

  return (
    <AppShell>
      <div className="grid gap-8">
        <StepIndicator current={1} />

        <PageHeader
          eyebrow="Revisión"
          title="Revisión antes de continuar"
          description="Confirma que tu video cumple estas recomendaciones antes de iniciar el análisis."
        />

        <div className="grid gap-6 lg:grid-cols-12">
          <section className="reveal lg:col-span-5" style={{ "--i": 1 } as CSSProperties}>
            {videoUrl ? (
              <>
                <VideoStage sources={[{ label: "Original", src: videoUrl }]} size="md" />
                {videoMeta && (
                  <p className="mt-3 truncate font-mono text-xs text-ink-muted">
                    {videoMeta.name} · {videoMeta.size}
                  </p>
                )}
              </>
            ) : (
              <div className="flex min-h-[240px] items-center justify-center rounded-xl bg-navy-950 p-6 text-center text-sm text-on-navy">
                No hay un video cargado.
              </div>
            )}
          </section>

          <section
            className="reveal rounded-xl border border-line bg-surface p-6 lg:col-span-7"
            style={{ "--i": 2 } as CSSProperties}
          >
            <ValidationChecklist valid={valid} />
          </section>
        </div>

        <div className="reveal grid gap-5 border-t border-line pt-6 lg:grid-cols-12" style={{ "--i": 3 } as CSSProperties}>
          <MedicalDisclaimer variant="inline" className="lg:col-span-7" />
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end lg:col-span-5">
            <Button variant="outline" size="lg" onClick={() => router.push("/analisis/subir-video")}>
              <ArrowLeft aria-hidden />
              {valid ? "Cambiar video" : "Subir otro video"}
            </Button>
            <Button size="lg" disabled={!valid} onClick={() => router.push("/analisis/movimiento")}>
              Iniciar análisis
              <ArrowRight aria-hidden />
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
