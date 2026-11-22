"use client";

import { useRef, useState } from "react";
import { RotateCcw, TriangleAlert } from "lucide-react";
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
  // Cada reintento manual remonta el <video> (misma URL; no se crea ni revoca ninguna).
  const [attempt, setAttempt] = useState(0);

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
          <div className="flex max-w-xs flex-col items-start gap-3 p-6 text-sm text-on-navy" role="alert">
            <p className="flex items-start gap-2">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-accent-cyan" aria-hidden />
              {isKeypoints
                ? "El video con puntos clave se generó, pero no pudo reproducirse."
                : "Este video no pudo reproducirse en el navegador."}
            </p>
            {!thumbnail && (
              <button
                type="button"
                onClick={() => {
                  setFailed((prev) => ({ ...prev, [active.src]: false }));
                  setAttempt((n) => n + 1);
                }}
                className="inline-flex h-8 items-center gap-1.5 rounded-md border border-navy-800 px-3 text-xs font-semibold text-white transition-colors duration-150 hover:bg-navy-800"
              >
                <RotateCcw className="h-3.5 w-3.5" aria-hidden />
                Reintentar
              </button>
            )}
          </div>
        ) : (
          <div className="relative min-w-0 max-w-full">
            <StageVideo
              key={`${active.src}#${attempt}`}
              src={thumbnail ? `${active.src}#t=0.5` : active.src}
              thumbnail={thumbnail}
              className={cn("block h-auto w-auto max-w-full rounded-md object-contain", MAX_HEIGHT[size])}
              onGiveUp={() => setFailed((prev) => ({ ...prev, [active.src]: true }))}
            >
              {scanning && (
                <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-md" aria-hidden>
                  <div className="scan-line" />
                  <ViewfinderCorners />
                </div>
              )}
            </StageVideo>
          </div>
        )}
      </div>
    </figure>
  );
}

const MAX_RECOVERIES = 3;
const TAIL_SECONDS = 1.5;

/**
 * <video> que NO se desmonta por un error de reproducción. Un error posterior a
 * haber cargado el video (p. ej. un paquete de audio final que el navegador no
 * puede decodificar) no invalida el archivo: se recarga el mismo recurso, se
 * conserva la posición y se informa. Solo si el video nunca llega a cargar (o la
 * recuperación falla) se delega en `onGiveUp`, que muestra el error con reintento.
 * El error nunca se oculta: queda en consola y como aviso visible.
 */
function StageVideo({
  src,
  thumbnail,
  className,
  onGiveUp,
  children,
}: {
  src: string;
  thumbnail: boolean;
  className: string;
  onGiveUp: () => void;
  children?: React.ReactNode;
}) {
  const ref = useRef<HTMLVideoElement | null>(null);
  const loaded = useRef(false);
  const recoveries = useRef(0);
  const resumeAt = useRef(0);
  const [notice, setNotice] = useState<string | null>(null);

  function handleError() {
    const video = ref.current;
    if (!video) return;
    const { duration, currentTime } = video;
    console.warn("VideoStage: error de reproducción", {
      code: video.error?.code,
      message: video.error?.message,
      currentTime,
      duration,
      recovered: recoveries.current,
    });
    if (thumbnail || !loaded.current || recoveries.current >= MAX_RECOVERIES) {
      onGiveUp();
      return;
    }
    recoveries.current += 1;
    const atEnd = Number.isFinite(duration) && duration > 0 && currentTime >= duration - TAIL_SECONDS;
    resumeAt.current = atEnd ? 0 : currentTime;
    // Error al leer el final del archivo: recuperación silenciosa (queda en consola).
    // Una interrupción a mitad de la reproducción sí se comunica.
    setNotice(atEnd ? null : "La reproducción se interrumpió y se restauró. Pulse Play para continuar.");
    loaded.current = false;
    video.load(); // limpia el estado de error del elemento; la URL no se toca
  }

  return (
    <>
      <div className="relative">
      <video
        ref={ref}
        src={src}
        controls={!thumbnail}
        muted={thumbnail}
        playsInline
        preload="metadata"
        onLoadedMetadata={(event) => {
          loaded.current = true;
          if (resumeAt.current > 0) event.currentTarget.currentTime = resumeAt.current;
          resumeAt.current = 0;
        }}
        onPlay={() => setNotice(null)}
        onError={handleError}
        className={className}
      >
        Tu navegador no puede reproducir este video.
      </video>
      {children}
      </div>
      {notice && !thumbnail && (
        <p role="status" className="mt-2 flex items-start gap-2 text-xs leading-5 text-on-navy">
          <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent-cyan" aria-hidden />
          {notice}
        </p>
      )}
    </>
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
