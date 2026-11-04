"use client";

import { useId, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, CircleAlert, CircleCheck, Info, RefreshCw, Search } from "lucide-react";
import { useAdminList } from "@/components/admin/adminData";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/EmptyState";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { SectionHeader } from "@/components/ui/PageHeader";
import { PatternBadge } from "@/components/ui/PatternBadge";
import { STORED_PATTERN_LABEL, StoredPattern } from "@/lib/analysis/conditionLabels";
import { formatPercent } from "@/lib/formatPercent";
import { cn } from "@/lib/utils";

// Forma de GET /api/admin/analyses (endpoint existente, sin cambios).
type AdminAnalysis = {
  id: string;
  userEmail: string;
  userName: string;
  date: string;
  pattern: StoredPattern | null;
  modelConfidence: number | null;
  reportId: string | null;
};

const ALL = "todos";
const UNCLASSIFIED = "sin_clasificar";
const PATTERN_FILTERS: StoredPattern[] = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida", "no_concluyente"];

function StatusBadge({ pattern }: { pattern: StoredPattern | null }) {
  const status =
    pattern === "no_concluyente"
      ? { label: "No concluyente", icon: CircleAlert, className: "border-warning-line bg-warning-bg text-warning" }
      : pattern
        ? { label: "Completado", icon: CircleCheck, className: "border-success-line bg-success-bg text-success" }
        : { label: "Sin clasificar", icon: Info, className: "border-line bg-surface-subtle text-ink-muted" };
  const Icon = status.icon;

  return (
    <span className={cn("inline-flex h-6 items-center gap-1.5 rounded-md border px-1.5 text-[11px] font-bold whitespace-nowrap", status.className)}>
      <Icon className="h-3 w-3" aria-hidden />
      {status.label}
    </span>
  );
}

const confidenceLabel = (value: number | null) => (value === null ? "Sin dato" : formatPercent(value));

/** Error de lectura de una API administrativa, con reintento. */
export function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <InlineAlert tone="error">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span>{message} Puede ser un problema temporal.</span>
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw aria-hidden />
          Reintentar
        </Button>
      </div>
    </InlineAlert>
  );
}

/** Paginación de una lista ya cargada en el cliente. */
export function Pagination({
  page,
  pageCount,
  from,
  to,
  total,
  onChange,
}: {
  page: number;
  pageCount: number;
  from: number;
  to: number;
  total: number;
  onChange: (page: number) => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3">
      <p className="tabular text-[13px] text-ink-subtle">{total === 0 ? "0 resultados" : `${from}–${to} de ${total}`}</p>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft aria-hidden />
          Anterior
        </Button>
        <Button variant="outline" size="sm" disabled={page >= pageCount} onClick={() => onChange(page + 1)}>
          Siguiente
          <ChevronRight aria-hidden />
        </Button>
      </div>
    </div>
  );
}

export function ActivityTable({ title, pageSize = 6 }: { title: string; pageSize?: number }) {
  const searchId = useId();
  const filterId = useId();
  const { rows, loading, failed, retry } = useAdminList<AdminAnalysis>("/api/admin/analyses", "analyses");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState(ALL);
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return rows.filter(
      (row) =>
        (filter === ALL || (row.pattern ?? UNCLASSIFIED) === filter) &&
        (!term || row.userName.toLowerCase().includes(term) || row.userEmail.toLowerCase().includes(term))
    );
  }, [rows, search, filter]);

  const hasUnclassified = rows.some((row) => !row.pattern);
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const start = (currentPage - 1) * pageSize;
  const visible = filtered.slice(start, start + pageSize);

  return (
    <section>
      <SectionHeader title={title} as="h2" />
      <Card className="mt-3 overflow-hidden p-0 shadow-raised">
        <div className="flex flex-col gap-2 border-b border-line p-4 sm:flex-row">
          <div className="relative min-w-0 flex-1">
            <label htmlFor={searchId} className="sr-only">Buscar por usuario o email</label>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle" aria-hidden />
            <input
              id={searchId}
              type="search"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Buscar por usuario o email"
              className="h-10 w-full rounded-lg border border-line-strong bg-surface pl-9 pr-3 text-sm text-ink outline-none transition-colors placeholder:text-ink-subtle focus:border-accent-blue"
            />
          </div>
          <div className="sm:w-52">
            <label htmlFor={filterId} className="sr-only">Filtrar por resultado</label>
            <select
              id={filterId}
              value={filter}
              onChange={(event) => {
                setFilter(event.target.value);
                setPage(1);
              }}
              className="h-10 w-full rounded-lg border border-line-strong bg-surface px-3 text-sm text-ink outline-none transition-colors focus:border-accent-blue"
            >
              <option value={ALL}>Todos los resultados</option>
              {PATTERN_FILTERS.map((pattern) => (
                <option key={pattern} value={pattern}>{STORED_PATTERN_LABEL[pattern]}</option>
              ))}
              {hasUnclassified && <option value={UNCLASSIFIED}>Sin clasificar</option>}
            </select>
          </div>
        </div>

        {failed ? (
          <div className="p-4">
            <LoadError message="No se pudo cargar la actividad." onRetry={retry} />
          </div>
        ) : loading ? (
          <div className="space-y-4 p-5">
            {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-5 w-full" />)}
          </div>
        ) : visible.length === 0 ? (
          <p className="px-5 py-8 text-sm text-ink-muted">
            {rows.length === 0 ? "Sin análisis registrados." : "Ningún análisis coincide con la búsqueda o el filtro."}
          </p>
        ) : (
          <>
            <table className="hidden w-full table-fixed text-left text-sm md:table">
              <thead>
                <tr className="border-b border-line text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">
                  <th scope="col" className="px-5 py-3 font-bold">Usuario</th>
                  <th scope="col" className="w-[104px] px-3 py-3 font-bold">Fecha</th>
                  <th scope="col" className="w-[150px] px-3 py-3 font-bold">Resultado</th>
                  <th scope="col" className="w-[96px] px-3 py-3 text-right font-bold">Confianza</th>
                  <th scope="col" className="w-[160px] px-5 py-3 font-bold">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {visible.map((row) => (
                  <tr key={row.id} className="transition-colors duration-150 hover:bg-surface-subtle">
                    <td className="px-5 py-3">
                      <p className="truncate font-semibold text-ink">{row.userName}</p>
                      <p className="truncate text-[13px] text-ink-muted" title={row.userEmail}>{row.userEmail}</p>
                    </td>
                    <td className="px-3 py-3 font-mono text-[12px] whitespace-nowrap text-ink-muted">{row.date}</td>
                    <td className="px-3 py-3"><PatternBadge pattern={row.pattern} /></td>
                    <td className="tabular px-3 py-3 text-right whitespace-nowrap text-ink">{confidenceLabel(row.modelConfidence)}</td>
                    <td className="px-5 py-3"><StatusBadge pattern={row.pattern} /></td>
                  </tr>
                ))}
              </tbody>
            </table>

            <ul className="divide-y divide-line md:hidden">
              {visible.map((row) => (
                <li key={row.id} className="px-5 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-ink">{row.userName}</p>
                      <p className="truncate text-[13px] text-ink-muted" title={row.userEmail}>{row.userEmail}</p>
                    </div>
                    <p className="shrink-0 font-mono text-[12px] text-ink-subtle">{row.date}</p>
                  </div>
                  <div className="mt-2.5 flex flex-wrap items-center gap-2">
                    <PatternBadge pattern={row.pattern} />
                    <StatusBadge pattern={row.pattern} />
                    <span className="tabular ml-auto text-[13px] text-ink-muted">Confianza: {confidenceLabel(row.modelConfidence)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}

        {!failed && !loading && (
          <Pagination
            page={currentPage}
            pageCount={pageCount}
            from={filtered.length === 0 ? 0 : start + 1}
            to={start + visible.length}
            total={filtered.length}
            onChange={setPage}
          />
        )}
      </Card>
    </section>
  );
}
