"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { StoredPattern } from "@/lib/analysis/conditionLabels";

export type RecentReport = {
  id: string;
  userEmail: string;
  userName: string;
  title: string;
  date: string;
  pattern: StoredPattern | null;
  modelConfidence: number | null;
  summary: string;
};

export type AdminSummary = {
  totalUsers: number;
  totalAnalyses: number;
  totalReports: number;
  totalVideos: number;
  patternCounts: Partial<Record<StoredPattern | "sin_clasificar", number>>;
  modelStatus: {
    available: boolean;
    accuracy: number | null;
    macroF1: number | null;
    modelVersion: string | null;
    trainingVideos: number | null;
    trainingSubjects: number | null;
    message: string;
  };
  recentReports: RecentReport[];
};

const EMPTY_SUMMARY: AdminSummary = {
  totalUsers: 0,
  totalAnalyses: 0,
  totalReports: 0,
  totalVideos: 0,
  patternCounts: {},
  modelStatus: {
    available: false,
    accuracy: null,
    macroF1: null,
    modelVersion: null,
    trainingVideos: null,
    trainingSubjects: null,
    message: "Sin datos",
  },
  recentReports: [],
};

type SummaryState = {
  summary: AdminSummary;
  loading: boolean;
  failed: boolean;
  /** Falló la lectura y no hay un resumen anterior: los ceros de EMPTY_SUMMARY no son datos reales. */
  unavailable: boolean;
  retry: () => void;
};

const AdminSummaryContext = createContext<SummaryState | null>(null);

// Cada pantalla monta su propio AppShell: conservar el último resumen evita que
// el estado del sistema parpadee al navegar, mientras se actualiza en segundo plano.
let lastSummary: AdminSummary | null = null;

export function clearAdminSummaryCache() {
  lastSummary = null;
}

/** Una sola lectura de GET /api/admin/summary para la barra superior y el panel. */
export function AdminSummaryProvider({ children }: { children: React.ReactNode }) {
  const [summary, setSummary] = useState<AdminSummary>(lastSummary ?? EMPTY_SUMMARY);
  const [loading, setLoading] = useState(lastSummary === null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await fetch("/api/admin/summary");
        if (!response.ok) throw new Error(String(response.status));
        const payload = (await response.json()) as AdminSummary;
        lastSummary = payload;
        if (active) {
          setSummary(payload);
          setFailed(false);
        }
      } catch {
        if (active) setFailed(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setLoading(true);
    setFailed(false);
    setAttempt((value) => value + 1);
  }, []);

  const unavailable = failed && summary === EMPTY_SUMMARY;
  const value = useMemo(
    () => ({ summary, loading, failed, unavailable, retry }),
    [summary, loading, failed, unavailable, retry]
  );

  return <AdminSummaryContext.Provider value={value}>{children}</AdminSummaryContext.Provider>;
}

export function useAdminSummary() {
  const context = useContext(AdminSummaryContext);

  if (!context) {
    throw new Error("useAdminSummary debe usarse dentro de AdminSummaryProvider");
  }

  return context;
}

/** Lee una lista de una API administrativa existente, con carga, error y reintento. */
export function useAdminList<T>(url: string, key: string) {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(String(response.status));
        const payload = (await response.json()) as Record<string, T[]>;
        if (active) {
          setRows(payload[key] ?? []);
          setFailed(false);
        }
      } catch {
        if (active) setFailed(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [url, key, attempt]);

  const retry = useCallback(() => {
    setLoading(true);
    setFailed(false);
    setAttempt((value) => value + 1);
  }, []);

  return { rows, loading, failed, retry };
}

export const formatDecimal = (value: number | null) =>
  value === null ? "Sin dato" : value.toLocaleString("es", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
