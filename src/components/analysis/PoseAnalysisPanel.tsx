"use client";

import { useAnalysis } from "@/context/AnalysisContext";

export function PoseAnalysisPanel() {
  const { videoUrl } = useAnalysis();

  return (
    <div className="relative aspect-video overflow-hidden rounded-3xl bg-slate-950 shadow-lg">
      {videoUrl ? (
        <video
          src={videoUrl}
          className="h-full w-full object-cover opacity-70"
          controls
        />
      ) : (
        <div className="flex h-full items-center justify-center text-white">
          Video simulado
        </div>
      )}

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-0 top-0 h-1 w-full animate-pulse bg-cyan-300 shadow-[0_0_20px_#67e8f9]" />

        <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
          <line x1="50" y1="18" x2="50" y2="40" stroke="#67e8f9" strokeWidth="1.5" />
          <line x1="42" y1="34" x2="58" y2="34" stroke="#67e8f9" strokeWidth="1.5" />
          <line x1="50" y1="40" x2="43" y2="62" stroke="#67e8f9" strokeWidth="1.5" />
          <line x1="50" y1="40" x2="58" y2="60" stroke="#67e8f9" strokeWidth="1.5" />
          <line x1="43" y1="62" x2="40" y2="82" stroke="#67e8f9" strokeWidth="1.5" />
          <line x1="58" y1="60" x2="63" y2="82" stroke="#67e8f9" strokeWidth="1.5" />

          <circle cx="50" cy="18" r="2" fill="#a78bfa" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="42" cy="34" r="2" fill="#a78bfa" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="58" cy="34" r="2" fill="#a78bfa" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="50" cy="40" r="2" fill="#a78bfa" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="43" cy="62" r="2" fill="#a78bfa" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="58" cy="60" r="2" fill="#a78bfa" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="40" cy="82" r="2" fill="#67e8f9" stroke="#ffffff" strokeWidth="0.5" />
          <circle cx="63" cy="82" r="2" fill="#67e8f9" stroke="#ffffff" strokeWidth="0.5" />
        </svg>

        <div className="absolute bottom-5 left-5 rounded-2xl bg-white/90 p-3 text-sm font-semibold text-slate-900 backdrop-blur">
          Analizando postura y trayectoria
        </div>
      </div>
    </div>
  );
}

