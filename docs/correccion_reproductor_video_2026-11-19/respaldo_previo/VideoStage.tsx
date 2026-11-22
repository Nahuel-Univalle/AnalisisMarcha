"use client";

import { useState } from "react";
import { TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

export type VideoSource = {
  label: "Original" | "Puntos clave";
  src: string;
};

type VideoStageProps = {
  sources: VideoSource[];
  /** Pestaña inicial (por etiqueta). */
  initial?: VideoSource["label"];
  /** Altura máxima del video: sm 240 · md 400 · lg min(60vh, 520). */
  size?: "sm" | "md" | "lg";
  /** Efecto de escaneo (solo mientras el análisis real está en curso). */
  scanning?: boolean;
  scanningLabel?: string;
  /** Miniatura muda sin controles (p. ej. dashboard). */
  thumbnail?: boolean;
  className?: string;
};

const MAX_HEIGHT = {
  sm: "max-h-[240px]",
  md: "max-h-[400px]",
  lg: "max-h-[min(60vh,520px)]",
};

const MIN_HEIGHT = {
  sm: "min-h-[180px]",
  md: "min-h-[240px]",
  lg: "min-h-[300px]",
};

/**
 * Marco único para TODO video del producto. Fondo navy: un video vertical
 * queda centrado con bandas navy a los lados; nunca se estira ni se recorta
 * (object-contain) y su altura está limitada.
 */
export function VideoStage({
  sources,
  initial,
  size = "md",
  scanning = false,
  scanningLabel = "Detectando puntos corporales",
  thumbnail = false,
  className,
}: VideoStageProps) {
  const available = sources.filter((source) => Boolean(source.src));
  const [selected, setSelected] = useState<VideoSource["label"] | null>(null);
  const [failed, setFailed] = useState<Record<string, boolean>>({});

  if (available.length === 0) return null;

  const activeLabel =
    selected && available.some((s) => s.label === selected)
      ? selected
      : initial && available.some((s) => s.label === initial)
        ? initial
        : available[0].label;
  const active = available.find((source) => source.label === activeLabel) ?? available[0];
  const isKeypoints = active.label === "Puntos clave";

  return (
    <figure className={cn("min-w-0 overflow-hidden rounded-xl border border-navy-800 bg-navy-950 shadow-raised", thumbnail && "flex flex-col", className)}>
      {!thumbnail && (
        <div className="flex min-h-11 flex-wrap items-center justify-between gap-2 border-b border-navy-800 px-3 py-2">
          {available.length > 1 ? (
            <div role="tablist" aria-label="Versión del video" className="flex gap-1">
              {available.map((source) => {
                const selectedTab = source.label === active.label;
                return (
                  <button
                    key={source.label}
                    type="button"
                    role="tab"
                    aria-selected={selectedTab}
                    onClick={() => setSelected(source.label)}
                    className={cn(
                      "inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-xs font-semibold transition-colors duration-150",
                      selectedTab ? "bg-navy-800 text-white" : "text-on-navy hover:text-white"
                    )}
                  >
                    <SourceDot keypoints={source.label === "Puntos clave"} />
                    {source.label}
                  </button>
                );
              })}
            </div>
          ) : (
            <figcaption className="inline-flex items-center gap-1.5 px-1 text-xs font-semibold text-white">
              <SourceDot keypoints={isKeypoints} />
              {active.label}
            </figcaption>
          )}
          {scanning && (
            <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-accent-cyan">
              <span className="ring-pulse h-1.5 w-1.5 rounded-full bg-accent-cyan" aria-hidden />
              {scanningLabel}
            </span>
          )}
        </div>
      )}

      <div className={cn("relative flex items-center justify-center p-2", MIN_HEIGHT[size], thumbnail && "flex-1")}>
        {failed[active.src] ? (
          <p className="flex max-w-xs items-start gap-2 p-6 text-sm text-on-navy">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-accent-cyan" aria-hidden />
            {isKeypoints
              ? "El video con puntos clave se generó, pero no pudo reproducirse."
              : "Este video no pudo reproducirse en el navegador."}
          </p>
        ) : (
          <div className="relative min-w-0 max-w-full">
            <video
              key={active.src}
              src={thumbnail ? `${active.src}#t=0.5` : active.src}
              controls={!thumbnail}
              muted={thumbnail}
              playsInline
              preload="metadata"
              onError={() => setFailed((prev) => ({ ...prev, [active.src]: true }))}
              className={cn("block h-auto w-auto max-w-full rounded-md object-contain", MAX_HEIGHT[size])}
            >
              Tu navegador no puede reproducir este video.
            </video>
            {scanning && (
              <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-md" aria-hidden>
                <div className="scan-line" />
                <ViewfinderCorners />
              </div>
            )}
          </div>
        )}
      </div>
    </figure>
  );
}

function SourceDot({ keypoints }: { keypoints: boolean }) {
  return (
    <span
      className={cn("h-1.5 w-1.5 rounded-full", keypoints ? "bg-accent-cyan" : "bg-on-navy")}
      aria-hidden
    />
  );
}

function ViewfinderCorners() {
  const corner = "absolute h-4 w-4 border-accent-cyan";
  return (
    <>
      <span className={cn(corner, "left-2 top-2 border-l-2 border-t-2")} />
      <span className={cn(corner, "right-2 top-2 border-r-2 border-t-2")} />
      <span className={cn(corner, "bottom-2 left-2 border-b-2 border-l-2")} />
      <span className={cn(corner, "bottom-2 right-2 border-b-2 border-r-2")} />
    </>
  );
}
