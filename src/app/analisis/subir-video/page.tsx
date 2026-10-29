"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileVideo, RefreshCw, UploadCloud } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { PageHeader, SectionHeader } from "@/components/ui/PageHeader";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { OBSERVED_GROUPS, RECORDING_TIPS } from "@/components/analysis/guidance";
import { useAnalysis } from "@/context/AnalysisContext";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import styles from "./upload.module.css";

// Mismos tipos que el atributo `accept` del input. Se usan también para el
// arrastre, que el navegador no filtra por sí solo.
const ACCEPT = "video/mp4,video/quicktime,video/x-msvideo";
const ACCEPTED_TYPES = ACCEPT.split(",");
const ACCEPTED_EXTENSIONS = [".mp4", ".mov", ".avi"];

function isAcceptedVideo(file: File) {
  const name = file.name.toLowerCase();
  return ACCEPTED_TYPES.includes(file.type) || ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  return `${minutes}:${String(total % 60).padStart(2, "0")} min`;
}

export default function UploadVideoPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { setVideo, videoUrl, videoMeta, category, setCategory } = useAnalysis();
  const { isAdmin } = useAuth();
  const [dragging, setDragging] = useState(false);
  const [dropError, setDropError] = useState<string | null>(null);
  // Duración real leída de los metadatos del video de vista previa.
  const [duration, setDuration] = useState<{ url: string; text: string | null } | null>(null);

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      setDropError(null);
      setVideo(file);
    }
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    if (!isAcceptedVideo(file)) {
      setDropError("Formato no compatible. Selecciona un video MP4, MOV o AVI.");
      return;
    }
    setDropError(null);
    setVideo(file);
  };

  const openPicker = () => inputRef.current?.click();
  const durationText = duration && duration.url === videoUrl ? duration.text : null;

  return (
    <AppShell className={styles.shell}>
      <div className={cn("grid gap-5", styles.page)}>
        <StepIndicator current={0} />

        <PageHeader
          eyebrow="Nuevo análisis"
          title="Sube tu video caminando"
          description="Selecciona un video donde se vea claramente a la persona caminando."
        />

        <div className="grid items-start gap-7 lg:grid-cols-12">
          <section className="reveal upload-panel grid gap-5 lg:col-span-8" style={{ "--i": 1 } as React.CSSProperties}>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPT}
              className="sr-only"
              tabIndex={-1}
              aria-hidden
              onChange={handleFile}
            />

            {!videoUrl || !videoMeta ? (
              <div
                onClick={openPicker}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                className={cn(
                  "upload-dropzone group flex min-h-[330px] cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed px-6 py-10 text-center transition-[border-color,background-color,box-shadow] duration-150",
                  dragging
                    ? "border-solid border-primary bg-primary-soft shadow-[0_0_0_3px_rgba(11,149,134,0.12)]"
                    : "border-line-strong hover:border-primary hover:bg-primary-soft"
                )}
              >
                <span
                  className={cn(
                    "inline-flex h-14 w-14 items-center justify-center rounded-xl border border-line bg-surface text-primary transition-transform duration-200",
                    dragging ? "-translate-y-1" : "group-hover:-translate-y-0.5"
                  )}
                >
                  <UploadCloud className="h-7 w-7" aria-hidden />
                </span>
                <h2 className="mt-5 max-w-sm text-xl font-semibold leading-7 tracking-[-0.02em] text-ink">
                  {dragging ? "Suelta el video para cargarlo" : "Arrastra tu video aquí o selecciona un archivo"}
                </h2>
                <div className="mt-3 flex items-center gap-1.5">
                  {["MP4", "MOV", "AVI"].map((format) => (
                    <span
                      key={format}
                      className="rounded-md border border-line bg-surface-subtle px-1.5 py-0.5 font-mono text-[11px] text-ink-muted"
                    >
                      {format}
                    </span>
                  ))}
                </div>
                <p className="mt-2 text-[13px] text-ink-subtle">Tamaño máximo sugerido: 100 MB</p>
                <Button className="mt-6" onClick={(event) => { event.stopPropagation(); openPicker(); }}>
                  Seleccionar video
                </Button>
              </div>
            ) : (
              <div className="fade-in overflow-hidden rounded-xl border border-line bg-surface">
                <div className="flex flex-wrap items-center gap-4 border-b border-line px-5 py-4">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
                    <FileVideo className="h-5 w-5" aria-hidden />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink">{videoMeta.name}</p>
                    <p className="mt-0.5 font-mono text-xs text-ink-muted">
                      {videoMeta.size}
                      {durationText ? ` · ${durationText}` : ""}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={openPicker}>
                    <RefreshCw aria-hidden />
                    Cambiar video
                  </Button>
                </div>
                <div
                  className="bg-navy-950 p-2"
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={handleDrop}
                >
                  <div className="flex min-h-[240px] items-center justify-center">
                    <video
                      key={videoUrl}
                      src={videoUrl}
                      controls
                      playsInline
                      preload="metadata"
                      onLoadedMetadata={(event) =>
                        setDuration({ url: videoUrl, text: formatDuration(event.currentTarget.duration) })
                      }
                      className="block h-auto max-h-[400px] w-auto max-w-full rounded-md object-contain"
                    />
                  </div>
                </div>
              </div>
            )}

            {dropError && <InlineAlert tone="error">{dropError}</InlineAlert>}

            {isAdmin() && (
              <div className="rounded-xl border border-line bg-surface p-5">
                <label htmlFor="dataset-category" className="block text-[13px] font-semibold text-ink">
                  Categoría del dataset
                </label>
                <p className="mt-0.5 text-[13px] text-ink-subtle">
                  Solo visible para administradores — etiqueta interna para investigación, no es un diagnóstico.
                </p>
                <select
                  id="dataset-category"
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                  className="mt-2 h-11 w-full rounded-lg border border-line-strong bg-surface px-3 text-[15px] text-ink outline-none transition-colors focus:border-accent-blue"
                >
                  <option value="control">control</option>
                  <option value="parkinson">parkinson</option>
                  <option value="multiple_sclerosis">multiple_sclerosis</option>
                  <option value="fall_risk">fall_risk</option>
                </select>
              </div>
            )}

            <div className="flex flex-col-reverse items-stretch justify-between gap-4 border-t border-line pt-5 sm:flex-row sm:items-center">
              <p className="text-[13px] text-ink-subtle">
                {videoUrl ? "Siguiente paso: revisar el video antes del análisis." : "Selecciona un video para continuar."}
              </p>
              <Button size="lg" disabled={!videoUrl} onClick={() => router.push("/analisis/validacion")}>
                Continuar a la revisión
                <ArrowRight aria-hidden />
              </Button>
            </div>
          </section>

          <aside className="reveal lg:col-span-4" style={{ "--i": 2 } as React.CSSProperties}>
            <div className="px-1 py-2 lg:px-3">
              <SectionHeader title="Consejos para una mejor grabación" as="h2" />
              <ul className="mt-3">
                {RECORDING_TIPS.map(({ label, icon: Icon }) => (
                  <li key={label} className="flex items-center gap-3 border-b border-line py-3.5 text-[13px] leading-5 text-ink-muted last:border-b-0">
                    <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary-dark">
                      <Icon className="h-4 w-4" aria-hidden />
                    </span>
                    {label}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-3 rounded-xl border border-line bg-surface p-5">
              <h2 className="text-sm font-bold text-ink">¿Qué observa el sistema?</h2>
              <dl className="mt-3 space-y-2.5">
                {OBSERVED_GROUPS.map((group) => (
                  <div key={group.title} className="grid grid-cols-[92px_1fr] gap-3 text-[13px] leading-5">
                    <dt className="text-[11px] font-bold uppercase tracking-[0.09em] text-accent-cyan-ink">
                      {group.title}
                    </dt>
                    <dd className="text-ink-muted">{group.items.map((item) => item.label).join(" · ")}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
