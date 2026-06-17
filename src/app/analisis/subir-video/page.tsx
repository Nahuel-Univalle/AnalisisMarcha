"use client";

import { ChangeEvent, useRef } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAnalysis } from "@/context/AnalysisContext";

export default function UploadVideoPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { setVideo, videoUrl, videoMeta, category, setCategory } = useAnalysis();

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      setVideo(file);
    }
  };

  return (
    <AppShell>
      <section className="grid gap-6 animate-fadeIn lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h1 className="text-4xl font-black text-slate-900">
            Sube tu video caminando
          </h1>

          <p className="mt-2 text-slate-500">
            Selecciona un video donde se vea claramente a la persona caminando.
          </p>

          <Card className="mt-6">
            <div
              onClick={() => inputRef.current?.click()}
              className="group flex min-h-80 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-primary/50 bg-blue-50 p-8 text-center shadow-inner transition duration-200 hover:-translate-y-1 hover:border-primary hover:bg-blue-100 hover:shadow-lg"
            >
              <UploadCloud className="h-14 w-14 text-primary transition duration-200 group-hover:scale-110" />

              <h2 className="mt-4 text-2xl font-black text-slate-900">
                Arrastra tu video aquí o selecciona un archivo
              </h2>

              <p className="mt-2 text-slate-500">
                Formatos aceptados: MP4, MOV, AVI. Tamaño máximo sugerido: 100 MB.
              </p>

              <Button className="mt-6" type="button">
                Seleccionar video
              </Button>

              <input
                ref={inputRef}
                type="file"
                accept="video/mp4,video/quicktime,video/x-msvideo"
                className="hidden"
                onChange={handleFile}
              />
            </div>

            {videoUrl && videoMeta && (
              <div className="mt-6 animate-slideIn rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-inner">
                <video src={videoUrl} controls className="w-full rounded-2xl shadow-lg" />

                <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-3">
                  <p>
                    <strong>Archivo:</strong> {videoMeta.name}
                  </p>
                  <p>
                    <strong>Tamaño:</strong> {videoMeta.size}
                  </p>
                  <p>
                    <strong>Duración:</strong> {videoMeta.duration}
                  </p>
                </div>
              </div>
            )}

            <div className="mt-6">
              <label
                htmlFor="dataset-category"
                className="block text-sm font-semibold text-slate-700"
              >
                Categoría del dataset
                <span className="ml-1 font-normal text-slate-400">
                  (solo etiqueta para investigación, no es un diagnóstico)
                </span>
              </label>
              <select
                id="dataset-category"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-300 bg-white p-3 text-slate-700 shadow-sm transition focus:border-primary focus:outline-none"
              >
                <option value="control">control</option>
                <option value="parkinson">parkinson</option>
                <option value="multiple_sclerosis">multiple_sclerosis</option>
                <option value="fall_risk">fall_risk</option>
              </select>
            </div>

            <Button
              className="mt-6 w-full"
              size="lg"
              disabled={!videoUrl}
              onClick={() => router.push("/analisis/validacion")}
            >
              Validar video
            </Button>
          </Card>
        </div>

        <Card>
          <h2 className="text-xl font-black text-slate-900">
            Consejos para un buen análisis
          </h2>

          <ul className="mt-5 space-y-3 text-sm text-slate-500">
            <li>• Buena iluminación.</li>
            <li>• Cuerpo completo visible.</li>
            <li>• Cámara estable.</li>
            <li>• Persona caminando en línea recta.</li>
            <li>• Video sin cortes bruscos.</li>
            <li>• Fondo despejado.</li>
            <li>• Duración suficiente para observar varios pasos.</li>
          </ul>
        </Card>
      </section>
    </AppShell>
  );
}
