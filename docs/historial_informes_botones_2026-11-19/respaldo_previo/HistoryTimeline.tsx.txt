"use client";

import { ReactNode, useMemo, useState } from "react";
import { ChevronDown, Video } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { PatternBadge } from "@/components/ui/PatternBadge";
import { FilterTabs } from "@/components/ui/FilterTabs";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import { VideoStage } from "@/components/analysis/VideoStage";
import { GaitFigure } from "@/components/brand/GaitFigure";
import { formatDayMonth, monthGroup } from "@/lib/formatDate";
import { STORED_PATTERN_LABEL, StoredPattern } from "@/lib/analysis/conditionLabels";
import { cn } from "@/lib/utils";

export type HistoryItem = {
  id: string;
  date: string;
  title: string;
  /** Patrón asignado por el modelo (4 clases) o "no concluyente". */
  pattern: StoredPattern | null;
  /** Línea secundaria (p. ej. usuario en la vista admin). */
  subtitle?: string;
  meta: Array<[string, string]>;
  summary?: string;
  originalSrc?: string | null;
  processedSrc?: string | null;
  /** Indicador adicional junto al título (p. ej. "Informe guardado"). */
  tag?: ReactNode;
};

const ALL = "todos";
const UNCLASSIFIED = "sin_clasificar";
const PATTERN_FILTERS: StoredPattern[] = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida", "no_concluyente"];

const patternValue = (item: HistoryItem) => item.pattern ?? UNCLASSIFIED;

type HistoryTimelineProps = {
  items: HistoryItem[];
  loading: boolean;
  emptyTitle: string;
  emptyDescription?: string;
  emptyAction?: ReactNode;
  /** Controles extra en la barra de filtros (p. ej. búsqueda admin). */
  toolbar?: ReactNode;
};

/**
 * Lista cronológica agrupada por mes, con filtro por patrón de marcha y videos
 * en un área desplegable. Se usa para el historial de análisis (Seguimiento)
 * y para los informes guardados (Informes / Informes globales).
 */
export function HistoryTimeline({
  items,
  loading,
  emptyTitle,
  emptyDescription,
  emptyAction,
  toolbar,
}: HistoryTimelineProps) {
  const [patternFilter, setPatternFilter] = useState(ALL);
  const [openVideos, setOpenVideos] = useState<string | null>(null);

  const filtered = useMemo(
    () => items.filter((item) => patternFilter === ALL || patternValue(item) === patternFilter),
    [items, patternFilter]
  );

  // Las 4 clases siempre; "No concluyente" y "Sin clasificar" solo si existen.
  const filterOptions = [
    { value: ALL, label: "Todos", count: items.length },
    ...PATTERN_FILTERS.map((pattern) => ({
      value: pattern as string,
      label: STORED_PATTERN_LABEL[pattern],
      count: items.filter((item) => item.pattern === pattern).length,
    })).filter((option) => option.value !== "no_concluyente" || option.count > 0),
    { value: UNCLASSIFIED, label: "Sin clasificar", count: items.filter((item) => !item.pattern).length },
  ].filter((option) => option.value !== UNCLASSIFIED || option.count > 0);

  const groups = useMemo(() => {
    const map = new Map<string, { label: string; items: HistoryItem[] }>();
    for (const item of filtered) {
      const { key, label } = monthGroup(item.date);
      if (!map.has(key)) map.set(key, { label, items: [] });
      map.get(key)!.items.push(item);
    }
    return Array.from(map.entries());
  }, [filtered]);

  return (
    <div className="grid gap-6">
      <div className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span className="pl-1 text-xs font-semibold text-ink-muted">Patrón de marcha</span>
          <FilterTabs label="Filtrar por patrón de marcha" options={filterOptions} value={patternFilter} onChange={setPatternFilter} />
        </div>
        {toolbar}
      </div>

      {loading ? (
        <div className="divide-y divide-line rounded-xl border border-line bg-surface">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex gap-5 p-5">
              <Skeleton className="h-10 w-12" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
                <Skeleton className="h-3 w-4/5" />
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-line bg-surface px-6 py-10">
          <EmptyState
            visual={
              <div className="w-16 rounded-lg bg-navy-900 p-2">
                <GaitFigure guides={false} />
              </div>
            }
            title={items.length > 0 ? "Ningún elemento coincide con el filtro" : emptyTitle}
            description={items.length > 0 ? "Prueba con otro patrón de marcha." : emptyDescription}
            action={items.length > 0 ? undefined : emptyAction}
          />
        </div>
      ) : (
        <div className="grid gap-8">
          {groups.map(([key, group]) => (
            <div key={key}>
              <h3 className="mb-4 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.09em] text-ink-muted">
                {group.label}
                <span className="h-px flex-1 bg-line" aria-hidden />
              </h3>
              <ol className="overflow-hidden rounded-xl border border-line bg-surface shadow-raised">
                {group.items.map((item, index) => {
                  const { day, month } = formatDayMonth(item.date);
                  const originalSrc = item.originalSrc || "";
                  const processedSrc = item.processedSrc || "";
                  const hasVideos = Boolean(originalSrc || processedSrc);
                  const open = openVideos === item.id;

                  return (
                    <li key={item.id} className={cn("transition-colors hover:bg-surface-subtle", index > 0 && "border-t border-line")}>
                      <div className="grid gap-4 p-5 sm:grid-cols-[64px_minmax(0,1fr)_auto] sm:gap-6 sm:p-6">
                        <div className="flex items-center gap-3 self-start rounded-lg bg-primary-soft px-3 py-2 sm:block sm:px-1 sm:text-center">
                          <p className="tabular text-2xl font-bold leading-7 text-ink">{day}</p>
                          <p className="font-mono text-[11px] uppercase text-ink-subtle">{month}</p>
                        </div>

                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-[16px] font-bold leading-6 tracking-[-0.01em] text-ink">{item.title}</h4>
                            <PatternBadge pattern={item.pattern} />
                            {item.tag}
                          </div>
                          {item.subtitle && <p className="mt-0.5 text-[13px] text-ink-muted">{item.subtitle}</p>}
                          <dl className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                            {item.meta.map(([label, value]) => (
                              <div key={label} className="flex gap-1.5">
                                <dt className="text-ink-subtle">{label}:</dt>
                                <dd className={cn("text-ink-muted", label === "Fecha" && "font-mono")}>{value}</dd>
                              </div>
                            ))}
                          </dl>
                          {item.summary && (
                            <p className="mt-2 line-clamp-2 max-w-3xl text-sm leading-6 text-ink-muted">{item.summary}</p>
                          )}
                        </div>

                        {hasVideos && (
                          <div className="flex items-start">
                            <Button
                              variant="secondary"
                              size="sm"
                              aria-expanded={open}
                              aria-controls={`videos-${item.id}`}
                              onClick={() => setOpenVideos(open ? null : item.id)}
                            >
                              <Video aria-hidden />
                              Videos
                              <ChevronDown className={cn("transition-transform duration-200", open && "rotate-180")} aria-hidden />
                            </Button>
                          </div>
                        )}
                      </div>

                      {open && hasVideos && (
                        <div id={`videos-${item.id}`} className="fade-in border-t border-line bg-surface-subtle p-5 sm:pl-28">
                          <div className="max-w-2xl">
                            <VideoStage
                              sources={[
                                { label: "Puntos clave", src: processedSrc },
                                { label: "Original", src: originalSrc },
                              ]}
                              size="sm"
                            />
                          </div>
                        </div>
                      )}
                    </li>
                  );
                })}
              </ol>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
