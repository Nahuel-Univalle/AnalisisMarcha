"use client";

import { useId, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { LoadError, Pagination } from "@/components/admin/ActivityTable";
import { useAdminList } from "@/components/admin/adminData";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/EmptyState";
import { PageHeader, SectionHeader } from "@/components/ui/PageHeader";

// Forma de GET /api/admin/users (endpoint existente, sin cambios).
type AdminUser = {
  id: string;
  email: string;
  name: string;
  role: string;
  date: string;
  totalAnalyses: number;
  totalReports: number;
  totalVideos: number;
};

const PAGE_SIZE = 10;

const roleLabel = (role: string) => (role === "ADMIN" ? "Admin" : "Usuario");
const countLabel = (count: number, singular: string, plural: string) => `${count} ${count === 1 ? singular : plural}`;

export default function AdministrationPage() {
  const searchId = useId();
  const { rows, loading, failed, retry } = useAdminList<AdminUser>("/api/admin/users", "users");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return rows.filter((row) => !term || row.name.toLowerCase().includes(term) || row.email.toLowerCase().includes(term));
  }, [rows, search]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const start = (currentPage - 1) * PAGE_SIZE;
  const visible = filtered.slice(start, start + PAGE_SIZE);

  return (
    <AppShell>
      <div className="grid gap-8">
        <PageHeader
          eyebrow="Administración"
          title="Usuarios"
          description="Cuentas registradas, de la más reciente a la más antigua, con su actividad en el sistema."
        />

        <section className="reveal" style={{ "--i": 1 } as React.CSSProperties}>
          <SectionHeader title="Usuarios registrados" as="h2" />
          <Card className="mt-3 overflow-hidden p-0 shadow-raised">
            <div className="relative border-b border-line p-4">
              <label htmlFor={searchId} className="sr-only">Buscar por nombre o email</label>
              <Search className="pointer-events-none absolute left-7 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle" aria-hidden />
              <input
                id={searchId}
                type="search"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Buscar por nombre o email"
                className="h-10 w-full rounded-lg border border-line-strong bg-surface pl-9 pr-3 text-sm text-ink outline-none transition-colors placeholder:text-ink-subtle focus:border-accent-blue sm:max-w-sm"
              />
            </div>

            {failed ? (
              <div className="p-4">
                <LoadError message="No se pudo cargar la lista de usuarios." onRetry={retry} />
              </div>
            ) : loading ? (
              <div className="space-y-4 p-5">
                {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-5 w-full" />)}
              </div>
            ) : visible.length === 0 ? (
              <p className="px-5 py-8 text-sm text-ink-muted">
                {rows.length === 0 ? "Sin usuarios registrados." : "Ningún usuario coincide con la búsqueda."}
              </p>
            ) : (
              <>
                <table className="hidden w-full table-fixed text-left text-sm md:table">
                  <thead>
                    <tr className="border-b border-line text-[11px] font-bold uppercase tracking-[0.08em] text-ink-subtle">
                      <th scope="col" className="px-5 py-3 font-bold">Usuario</th>
                      <th scope="col" className="w-[84px] px-3 py-3 font-bold">Rol</th>
                      <th scope="col" className="w-[110px] px-3 py-3 font-bold">Registro</th>
                      <th scope="col" className="w-[92px] px-3 py-3 text-right font-bold">Análisis</th>
                      <th scope="col" className="w-[92px] px-3 py-3 text-right font-bold">Informes</th>
                      <th scope="col" className="w-[92px] px-5 py-3 text-right font-bold">Videos</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {visible.map((row) => (
                      <tr key={row.id} className="transition-colors duration-150 hover:bg-surface-subtle">
                        <td className="px-5 py-3">
                          <p className="truncate font-semibold text-ink">{row.name}</p>
                          <p className="truncate text-[13px] text-ink-muted" title={row.email}>{row.email}</p>
                        </td>
                        <td className="px-3 py-3 text-[13px] text-ink-muted">{roleLabel(row.role)}</td>
                        <td className="px-3 py-3 font-mono text-[12px] whitespace-nowrap text-ink-muted">{row.date}</td>
                        <td className="tabular px-3 py-3 text-right text-ink">{row.totalAnalyses}</td>
                        <td className="tabular px-3 py-3 text-right text-ink">{row.totalReports}</td>
                        <td className="tabular px-5 py-3 text-right text-ink">{row.totalVideos}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <ul className="divide-y divide-line md:hidden">
                  {visible.map((row) => (
                    <li key={row.id} className="px-5 py-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-ink">{row.name}</p>
                          <p className="truncate text-[13px] text-ink-muted" title={row.email}>{row.email}</p>
                        </div>
                        <span className="shrink-0 text-[13px] text-ink-muted">{roleLabel(row.role)}</span>
                      </div>
                      <p className="tabular mt-2 text-[13px] text-ink-muted">
                        {row.totalAnalyses} análisis · {countLabel(row.totalReports, "informe", "informes")} · {countLabel(row.totalVideos, "video", "videos")}
                      </p>
                      <p className="mt-0.5 font-mono text-[12px] text-ink-subtle">{row.date}</p>
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
      </div>
    </AppShell>
  );
}
