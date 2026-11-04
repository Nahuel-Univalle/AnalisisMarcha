"use client";

import { CSSProperties } from "react";
import Link from "next/link";
import { BrainCircuit, FileText, ScanLine, Users, Video, type LucideIcon } from "lucide-react";
import { ActivityTable, LoadError } from "@/components/admin/ActivityTable";
import { formatDecimal, useAdminSummary } from "@/components/admin/adminData";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/EmptyState";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { PageHeader, SectionHeader } from "@/components/ui/PageHeader";
import { PatternBadge } from "@/components/ui/PatternBadge";
import { GAIT_CLASS_ORDER, STORED_PATTERN_LABEL } from "@/lib/analysis/conditionLabels";
import { cn } from "@/lib/utils";

const delay = (i: number) => ({ "--i": i }) as CSSProperties;

function KpiCard({
  icon: Icon,
  label,
  children,
  className,
}: {
  icon: LucideIcon;
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("p-5 shadow-raised", className)}>
      <div className="flex items-start justify-between gap-3">
        <p className="min-h-10 text-[13px] font-semibold leading-5 text-ink-muted">{label}</p>
        <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary-dark">
          <Icon className="h-[18px] w-[18px]" aria-hidden />
        </span>
      </div>
      <div className="mt-2">{children}</div>
    </Card>
  );
}

function KpiNumber({ value }: { value: number }) {
  const { loading, unavailable } = useAdminSummary();

  return loading ? (
    <Skeleton className="h-9 w-16" />
  ) : unavailable ? (
    <p className="flex min-h-9 items-center text-[17px] font-bold text-ink-muted">Sin dato</p>
  ) : (
    <p className="tabular text-[32px] font-extrabold leading-9 tracking-[-0.02em] text-ink">{value}</p>
  );
}

function PatternDistribution() {
  const { summary, loading, unavailable } = useAdminSummary();
  const rows = GAIT_CLASS_ORDER.map((key) => ({
    key,
    label: STORED_PATTERN_LABEL[key],
    count: summary.patternCounts[key] ?? 0,
  }));
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  const max = Math.max(1, ...rows.map((row) => row.count));
  const inconclusive = summary.patternCounts.no_concluyente ?? 0;
  const unclassified = summary.patternCounts.sin_clasificar ?? 0;

  return (
    <section className="flex flex-col">
      <SectionHeader title="Distribución de resultados por patrón" as="h2" />
      <Card className="mt-3 flex flex-1 flex-col p-5 shadow-raised sm:p-6">
        {unavailable ? (
          <p className="text-sm text-ink-muted">Sin datos de distribución: no se pudo cargar el resumen.</p>
        ) : (
          <>
            <ul className="grid flex-1 content-between gap-4">
              {rows.map((row) => {
                const share = total > 0 ? Math.round((row.count / total) * 100) : 0;
                return (
                  <li key={row.key} className="group relative rounded-md">
                    <div className="flex items-baseline justify-between gap-3 text-sm">
                      <span className="font-semibold text-ink">{row.label}</span>
                      {loading ? (
                        <Skeleton className="h-4 w-14" />
                      ) : (
                        <span className="tabular shrink-0 text-ink">
                          <span className="font-bold">{row.count}</span>{" "}
                          <span className="ml-1 text-[13px] text-ink-subtle">{share}%</span>
                        </span>
                      )}
                    </div>
                    <div className="mt-1.5 h-3.5" aria-hidden>
                      {!loading && (
                        <div
                          className="h-full rounded-r bg-primary transition-[opacity] duration-150 group-hover:opacity-80"
                          style={{ width: `${row.count === 0 ? 0 : Math.max((row.count / max) * 100, 1)}%` }}
                        />
                      )}
                    </div>
                    {!loading && (
                      <span className="pointer-events-none absolute right-0 top-full z-10 mt-1 hidden rounded-md border border-line bg-surface px-2 py-1 text-xs font-medium text-ink shadow-overlay group-hover:block">
                        {row.label}: {row.count} análisis ({share}% de {total})
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
            <p className="mt-5 border-t border-line pt-4 text-[13px] leading-5 text-ink-subtle">
              Análisis guardados, incluidos los de versiones anteriores del modelo. Son clasificaciones experimentales, no diagnósticos.
              {!loading && inconclusive > 0 && ` No se incluyen ${inconclusive} no concluyentes.`}
              {!loading && unclassified > 0 && ` No se incluyen ${unclassified} sin clasificar.`}
            </p>
          </>
        )}
      </Card>
    </section>
  );
}

function CurrentModelCard() {
  const { summary, loading, unavailable } = useAdminSummary();
  const model = summary.modelStatus;
  const facts: Array<[string, string]> = [
    ["Clases", String(GAIT_CLASS_ORDER.length)],
    ["Videos de entrenamiento", model.trainingVideos === null ? "Sin dato" : String(model.trainingVideos)],
    ["Sujetos", model.trainingSubjects === null ? "Sin dato" : String(model.trainingSubjects)],
    ["Macro-F1", formatDecimal(model.macroF1)],
    ["Accuracy", formatDecimal(model.accuracy)],
    ["Estado", unavailable ? "Sin dato" : model.available ? "Disponible" : "No disponible"],
  ];

  return (
    <section className="flex flex-col">
      <SectionHeader title="Modelo actual" as="h2" />
      <Card className="mt-3 flex-1 p-5 shadow-raised sm:p-6">
        <p className="text-[13px] font-semibold text-ink-muted">Versión</p>
        {loading ? (
          <Skeleton className="mt-1 h-5 w-3/4" />
        ) : (
          <p className="mt-0.5 font-mono text-[13px] font-medium break-all text-ink">{model.modelVersion ?? "Sin dato"}</p>
        )}
        <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-line pt-4 sm:grid-cols-3">
          {facts.map(([label, value]) => (
            <div key={label} className="flex flex-col justify-between">
              <dt className="text-[13px] leading-5 text-ink-subtle">{label}</dt>
              <dd className="tabular mt-0.5 text-[15px] font-bold text-ink">
                {loading ? <Skeleton className="h-5 w-12" /> : value}
              </dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 text-[13px] leading-5 text-ink-subtle">Macro-F1 y Accuracy: evaluación interna por validación cruzada agrupada por sujeto.</p>
        <InlineAlert tone="warning" className="mt-4">
          Clasificación experimental. No constituye diagnóstico clínico.
        </InlineAlert>
      </Card>
    </section>
  );
}

function RecentReports() {
  const { summary, loading, unavailable } = useAdminSummary();

  return (
    <section>
      <SectionHeader
        title="Últimos informes"
        as="h2"
        action={
          <Link href="/seguimiento" className="text-[13px] font-semibold text-primary hover:underline">
            Ver todos
          </Link>
        }
      />
      <Card className="mt-3 overflow-hidden p-0 shadow-raised">
        {loading ? (
          <div className="space-y-4 p-5">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-5 w-full" />)}
          </div>
        ) : unavailable ? (
          <p className="px-5 py-8 text-sm text-ink-muted">No se pudieron cargar los informes.</p>
        ) : summary.recentReports.length === 0 ? (
          <p className="px-5 py-8 text-sm text-ink-muted">Sin informes registrados.</p>
        ) : (
          <ul className="divide-y divide-line">
            {summary.recentReports.map((report) => (
              <li key={report.id} className="px-5 py-3.5">
                <div className="flex items-center justify-between gap-3">
                  <PatternBadge pattern={report.pattern} />
                  <span className="font-mono text-[12px] text-ink-subtle">{report.date}</span>
                </div>
                <div className="mt-2 flex items-center justify-between gap-3">
                  <p className="min-w-0 truncate text-[13px] text-ink-muted" title={report.userEmail}>{report.userName}</p>
                  <Link
                    href="/seguimiento"
                    aria-label={`Ver informe de ${report.userName} del ${report.date} en Informes globales`}
                    className="shrink-0 text-[13px] font-semibold text-primary hover:underline"
                  >
                    Ver informe
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </section>
  );
}

export function AdminDashboard() {
  const { summary, loading, failed, unavailable, retry } = useAdminSummary();
  const model = summary.modelStatus;

  return (
    <div className="grid gap-8">
      <PageHeader
        title="Panel administrativo"
        description="Resumen y gestión del sistema de análisis de marcha mediante videos con un modelo de Deep Learning de 4 clases."
      />

      <div className="reveal" style={delay(1)}>
        <InlineAlert tone="info" className="border-line-strong text-ink">
          <span>
            <span className="font-bold">Sistema basado en videos:</span> clasificación experimental de 4 clases (Normal, Parkinson, Esclerosis múltiple y Riesgo de caída).
          </span>
        </InlineAlert>
      </div>

      {failed && (
        <LoadError message="No se pudo cargar el resumen del sistema." onRetry={retry} />
      )}

      <section aria-label="Métricas del sistema" className="reveal grid grid-cols-2 gap-4 md:grid-cols-6 xl:grid-cols-5" style={delay(2)}>
        <KpiCard icon={Users} label="Usuarios registrados" className="md:col-span-2 xl:col-span-1">
          <KpiNumber value={summary.totalUsers} />
        </KpiCard>
        <KpiCard icon={ScanLine} label="Análisis totales" className="md:col-span-2 xl:col-span-1">
          <KpiNumber value={summary.totalAnalyses} />
        </KpiCard>
        <KpiCard icon={FileText} label="Informes generados" className="md:col-span-2 xl:col-span-1">
          <KpiNumber value={summary.totalReports} />
        </KpiCard>
        <KpiCard icon={Video} label="Videos procesados" className="md:col-span-3 xl:col-span-1">
          <KpiNumber value={summary.totalVideos} />
        </KpiCard>
        <KpiCard icon={BrainCircuit} label="Estado del modelo" className="col-span-2 md:col-span-3 xl:col-span-1">
          {loading ? (
            <Skeleton className="h-9 w-28" />
          ) : unavailable ? (
            <p className="flex min-h-9 items-center text-[17px] font-bold text-ink-muted">Sin dato</p>
          ) : (
            <p className="flex min-h-9 items-center gap-2 text-[17px] font-bold text-ink">
              <span className={cn("h-2.5 w-2.5 shrink-0 rounded-full", model.available ? "bg-success" : "bg-danger")} aria-hidden />
              {model.available ? "Disponible" : "No disponible"}
            </p>
          )}
        </KpiCard>
      </section>

      <div className="reveal grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]" style={delay(3)}>
        <PatternDistribution />
        <CurrentModelCard />
      </div>

      <div className="reveal grid items-start gap-6 xl:grid-cols-[minmax(0,2.2fr)_minmax(0,1fr)]" style={delay(4)}>
        <ActivityTable title="Actividad reciente" />
        <RecentReports />
      </div>
    </div>
  );
}
