"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { AnalysisResult, SavedReport, VideoMeta } from "@/types";
import { mockAnalysisResult } from "@/data/mockAnalysis";
import { useAuth } from "@/context/AuthContext";

type AnalysisContextValue = {
  videoFile: File | null;
  videoUrl: string | null;
  videoMeta: VideoMeta | null;
  result: AnalysisResult;
  reports: SavedReport[];
  category: string;
  setCategory: (category: string) => void;
  setResult: (result: AnalysisResult) => void;
  setVideo: (file: File) => void;
  clearVideo: () => void;
  addReport: () => void;
};

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

function formatSize(bytes: number) {
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(2)} MB`;
}

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoMeta, setVideoMeta] = useState<VideoMeta | null>(null);
  const [result, setResult] = useState<AnalysisResult>(mockAnalysisResult);
  const [reports, setReports] = useState<SavedReport[]>([]);
  // Sprint 4 Iteración 8: categoría del dataset (etiqueta organizativa, no diagnóstico).
  const [category, setCategory] = useState<string>("control");

  useEffect(() => {
    queueMicrotask(() => {
      if (!user?.email) {
        setReports([]);
        return;
      }

      const savedReports = localStorage.getItem(`gait-reports:${user.email}`);
      if (savedReports) {
        setReports(JSON.parse(savedReports));
      } else {
        setReports([]);
      }
    });
  }, [user?.email]);

  const setVideo = (file: File) => {
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }

    const url = URL.createObjectURL(file);

    setVideoFile(file);
    setVideoUrl(url);
    setVideoMeta({
      name: file.name,
      size: formatSize(file.size),
      type: file.type || "video",
      duration: "Duración estimada válida",
    });
  };

  const clearVideo = () => {
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }

    setVideoFile(null);
    setVideoUrl(null);
    setVideoMeta(null);
    setResult(mockAnalysisResult);
  };

  const addReport = () => {
    const newReport: SavedReport = {
      id: crypto.randomUUID(),
      date: new Date().toISOString().split("T")[0],
      alertLevel: result.alertLevel,
      title: result.title || "Informe de análisis de marcha",
      originalVideoUrl: result.originalVideoUrl,
      processedVideoUrl:
        result.processedVideoUrl ||
        result.annotatedVideoUrl ||
        result.localProcessedVideoUrl ||
        undefined,
      localOriginalVideoUrl: result.localOriginalVideoUrl ?? null,
      localProcessedVideoUrl: result.localProcessedVideoUrl ?? null,
      videoProvider: result.videoProvider,
      videoRecordId: result.videoRecordId ?? null,
      analysisId: result.id ?? null,
    };

    const updated = [newReport, ...reports];
    setReports(updated);
    if (user?.email) {
      localStorage.setItem(`gait-reports:${user.email}`, JSON.stringify(updated));
    }
  };

  return (
    <AnalysisContext.Provider
      value={{
        videoFile,
        videoUrl,
        videoMeta,
        result,
        reports,
        category,
        setCategory,
        setResult,
        setVideo,
        clearVideo,
        addReport,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);

  if (!context) {
    throw new Error("useAnalysis debe usarse dentro de AnalysisProvider");
  }

  return context;
}
