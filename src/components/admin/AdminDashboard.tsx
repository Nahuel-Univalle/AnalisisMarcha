"use client";

import { CSSProperties, useEffect, useState } from "react";
import { Database, Files } from "lucide-react";
import { LinkButton } from "@/components/ui/LinkButton";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { PageHeader, SectionHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";

type AdminSummary = {
  totalUsers: number;
  totalAnalyses: number;
  totalReports: number;
  totalVideos: number;
  datasetSummary: {
    datasetRecords: number;
    rawSamples: number;
  };
  modelStatus: {
    available: boolean;
    metricsAvailable: boolean;
    accuracy: number | null;
    message: string;
  };
  recentAnalyses: Array<{
    id: string;
    userEmail: string;
    userName: string;
    date: string;
    alertLevel: string;
    summary: string;
  }>;
  recentReports: Array<{
    id: string;
    userEmail: string;
    userName: string;
    title: string;
    date: string;
    alertLevel: string;
    summary: string;
  }>;
  recentUsers: Array<{
    email: string;
    name: string;
    role: string;
    date: string;
  }>;
};

const EMPTY_SUMMARY: AdminSummary = {
  totalUsers: 0,
  totalAnalyses: 0,
  totalReports: 0,
  totalVideos: 0,
  datasetSummary: {
    datasetRecords: 0,
    rawSamples: 0,
  },
  modelStatus: {
    available: false,
    metricsAvailable: false,
    accuracy: null,
    message: "Sin datos",
  },
  recentAnalyses: [],
  recentReports: [],
  recentUsers: [],
};

const delay = (i: number) => ({ "--i": i }) as CSSProperties;

export function AdminDashboard() {
  const [summary, setSummary] = useState<AdminSummary>(EMPTY_SUMMARY);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      try {
        const response = await fetch("/api/admin/summary");
        if (!response.ok) return;
        const payload = (await response.json()) as AdminSummary;
        if (active) setSummary(payload);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadSummary();

    return () => {
      active = false;
    };
  }, []);

  const metrics: Array<[string, number | string]> = [
    ["Usuarios registrados", summary.totalUsers],
    ["Análisis totales", summary.totalAnalyses],
    ["Informes generados", summary.totalReports],
    ["Videos procesados", summary.totalVideos],
    ["Registros de referencia", summary.datasetSummary.datasetRecords],
  ];

  return (
    <div className="grid gap-10">
      <PageHeader
        eyebrow="Administración"
        title="Panel administrativo"
        description="Resumen general del sistema de análisis de marcha."
        actions={
          <>
            <LinkButton href="/datasets/parkinson" variant="outline">
              <Database aria-hidden />
              Datasets
            </LinkButton>
            <LinkButton href="/seguimiento" variant="outline">
              <Files aria-hidden />
              Informes globales
            </LinkButton>
          </>
        }
      />

      <section
        aria-label="Métricas del sistema"
        className="reveal grid overflow-hidden rounded-xl border border-line bg-surface sm:grid-cols-3 xl:grid-cols-6"
        style={delay(1)}
      >
        {metrics.map(([label, value], index) => (
          <div
            key={label}
            className={cn(
              "border-line px-5 py-5",
              index > 0 && "border-t sm:border-t-0",
              index % 3 !== 0 && "sm:border-l",
              index >= 3 && "sm:border-t xl:border-t-0",
              index === 3 && "xl:border-l"
            )}
          >
            <p className="min-h-8 text-[11px] font-bold uppercase leading-4 tracking-[0.09em] text-ink-subtle">{label}</p>
            <p className="tabular mt-2 text-[28px] font-extrabold leading-8 tracking-[-0.02em] text-ink">
              {loading ? <Skeleton className="h-8 w-12" /> : value}
            </p>
          </div>
        ))}
        <div className="border-t border-line px-5 py-5 sm:border-l xl:border-t-0">
          <p className="min-h-8 text-[11px] font-bold uppercase leading-4 tracking-[0.09em] text-ink-subtle">Estado del modelo</p>
          <p className="mt-3 flex items-center gap-2 text-[15px] font-semibold text-ink">
            {loading ? (
              <Skeleton className="h-6 w-24" />
            ) : (
              <>
                <span
                  className={cn("h-2 w-2 rounded-full", summary.modelStatus.available ? "bg-success" : "bg-danger")}
                  aria-hidden
                />
                {summary.modelStatus.available ? "Disponible" : "No disponible"}
              </>
            )}
          </p>
        </div>
      </section>

      <div className="reveal grid gap-6 xl:grid-cols-3" style={delay(2)}>
        <ActivityList
          title="Últimos análisis"
          empty="Sin análisis registrados."
          loading={loading}
          rows={summary.recentAnalyses.map((analysis) => ({
            key: analysis.id,
            primary: analysis.userName,
            secondary: analysis.userEmail,
            date: analysis.date,
            badge: <AlertBadge level={analysis.alertLevel} size="sm" />,
          }))}
        />
        <ActivityList
          title="Últimos informes"
          empty="Sin informes registrados."
          loading={loading}
          rows={summary.recentReports.map((report) => ({
            key: report.id,
            primary: report.title,
            secondary: report.userEmail,
            date: report.date,
            badge: <AlertBadge level={report.alertLevel} size="sm" />,
          }))}
        />
        <ActivityList
          title="Usuarios recientes"
          empty="Sin usuarios registrados."
          loading={loading}
          rows={summary.recentUsers.map((user) => ({
            key: user.email,
            primary: user.name,
            secondary: user.email,
            date: user.date,
            badge: (
              <span className="inline-flex h-6 items-center rounded-md border border-line bg-surface-subtle px-1.5 font-mono text-[11px] text-ink-muted">
                {user.role}
              </span>
            ),
          }))}
        />
      </div>
    </div>
  );
}

type ActivityRow = {
  key: string;
  primary: string;
  secondary: string;
  date: string;
  badge: React.ReactNode;
};

function ActivityList({
  title,
  empty,
  loading,
  rows,
}: {
  title: string;
  empty: string;
  loading: boolean;
  rows: ActivityRow[];
}) {
  return (
    <section>
      <SectionHeader title={title} as="h2" />
      <div className="mt-3 rounded-xl border border-line bg-surface">
        {loading ? (
          <div className="space-y-3 p-5">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-3/5" />
          </div>
        ) : rows.length === 0 ? (
          <p className="px-5 py-6 text-sm text-ink-muted">{empty}</p>
        ) : (
          <ul className="divide-y divide-line">
            {rows.map((row) => (
              <li key={row.key} className="flex items-start justify-between gap-3 px-5 py-3.5">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-ink">{row.primary}</p>
                  <p className="truncate text-[13px] text-ink-muted">{row.secondary}</p>
                  <p className="mt-0.5 font-mono text-[11px] text-ink-subtle">{row.date}</p>
                </div>
                {row.badge}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
