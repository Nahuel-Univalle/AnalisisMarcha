"use client";

import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";
import { ValidationChecklist } from "@/components/analysis/ValidationChecklist";
import { useAnalysis } from "@/context/AnalysisContext";

export default function ValidationPage() {
  const router = useRouter();
  const { videoFile } = useAnalysis();

  const valid = Boolean(videoFile);

  return (
    <AppShell>
      <section className="mx-auto max-w-4xl">
        <h1 className="text-center text-4xl font-black text-slate-950">
          Validando tu video
        </h1>

        <p className="mx-auto mt-3 max-w-2xl text-center text-slate-600">
          Revisamos si el video cumple las condiciones mínimas para un análisis
          confiable.
        </p>

        <div className="mt-8">
          <ValidationChecklist valid={valid} />
        </div>

        <div className="mt-6">
          <MedicalDisclaimer />
        </div>

        <div className="mt-8 flex justify-center gap-3">
          {!valid && (
            <Button
              variant="outline"
              onClick={() => router.push("/analisis/subir-video")}
            >
              Subir otro video
            </Button>
          )}

          <Button
            disabled={!valid}
            onClick={() => router.push("/analisis/movimiento")}
          >
            Iniciar análisis
          </Button>
        </div>
      </section>
    </AppShell>
  );
}