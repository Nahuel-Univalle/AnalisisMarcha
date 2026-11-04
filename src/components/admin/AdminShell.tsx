"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  ChevronDown,
  Files,
  House,
  LogOut,
  Menu,
  ShieldCheck,
  X,
  type LucideIcon,
} from "lucide-react";
import { BrandMark } from "@/components/brand/BrandMark";
import { clearAdminSummaryCache, AdminSummaryProvider, useAdminSummary } from "@/components/admin/adminData";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

type NavItem = { label: string; href: string; icon: LucideIcon; match: (pathname: string) => boolean };

const NAV: NavItem[] = [
  { label: "Inicio", href: "/dashboard", icon: House, match: (p) => p === "/dashboard" },
  { label: "Análisis", href: "/admin/analisis", icon: Activity, match: (p) => p.startsWith("/admin/analisis") },
  { label: "Informes globales", href: "/seguimiento", icon: Files, match: (p) => p.startsWith("/seguimiento") },
  { label: "Administración", href: "/admin", icon: ShieldCheck, match: (p) => p === "/admin" },
];

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Navegación de administración">
      <ul className="grid gap-1">
        {NAV.map(({ label, href, icon: Icon, match }) => {
          const active = match(pathname);
          return (
            <li key={href}>
              <Link
                href={href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-semibold transition-colors duration-150",
                  active
                    ? "bg-primary-soft text-primary-dark"
                    : "text-ink-muted hover:bg-surface-subtle hover:text-ink"
                )}
              >
                <Icon className="h-[18px] w-[18px] shrink-0" aria-hidden />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/** Refleja lo que devuelve /api/admin/summary: el estado nunca se muestra verde sin datos reales. */
function SystemStatus() {
  const { summary, loading, failed } = useAdminSummary();

  const status = failed
    ? { label: "Sin conexión con el servidor", className: "border-danger-line bg-danger-bg text-danger", dot: "bg-danger" }
    : loading
      ? { label: "Comprobando…", className: "border-line bg-surface-subtle text-ink-muted", dot: "bg-line-strong" }
      : summary.modelStatus.available
        ? { label: "Sistema operativo", className: "border-success-line bg-success-bg text-success", dot: "bg-success" }
        : { label: "Modelo no disponible", className: "border-warning-line bg-warning-bg text-warning", dot: "bg-warning" };

  return (
    <span
      role="status"
      className={cn(
        "inline-flex h-7 min-w-0 items-center gap-2 rounded-md border px-2.5 text-xs font-semibold whitespace-nowrap",
        status.className
      )}
    >
      <span className={cn("h-2 w-2 shrink-0 rounded-full", status.dot)} aria-hidden />
      {status.label}
    </span>
  );
}

function UserMenu() {
  const router = useRouter();
  const { logout, user } = useAuth();
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const initials = user?.name?.split(" ").filter(Boolean).slice(0, 2)
    .map((part) => part[0]?.toUpperCase()).join("") || "A";

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const handleLogout = () => {
    clearAdminSummaryCache();
    logout();
    router.push("/");
  };

  return (
    <div ref={container} className="relative shrink-0">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={`Menú de usuario: ${user?.name ?? "Administrador"}`}
        className="flex min-h-11 items-center gap-2.5 rounded-lg px-1.5 transition-colors duration-150 hover:bg-surface-subtle"
      >
        <span className="app-avatar" aria-hidden>{initials}</span>
        <span className="hidden min-w-0 max-w-[200px] text-left leading-tight md:block">
          <span className="block truncate text-[13px] font-bold text-ink">{user?.name || "Administrador"}</span>
          <span className="block text-[11px] text-ink-subtle">Administrador</span>
        </span>
        <ChevronDown
          className={cn("hidden h-4 w-4 text-ink-subtle transition-transform duration-150 md:block", open && "rotate-180")}
          aria-hidden
        />
      </button>

      {open && (
        <div className="fade-in absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-line bg-surface p-2 shadow-overlay">
          <div className="border-b border-line px-3 pb-3 pt-2">
            <p className="truncate text-sm font-bold text-ink">{user?.name || "Administrador"}</p>
            <p className="truncate text-[13px] text-ink-subtle">{user?.email}</p>
            <p className="mt-1 text-xs font-semibold text-primary-dark">Administrador</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-1 flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-sm font-semibold text-ink-muted transition-colors duration-150 hover:bg-surface-subtle hover:text-ink"
          >
            <LogOut className="h-4 w-4" aria-hidden />
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  );
}

function MobileDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  return (
    <dialog
      ref={dialog}
      aria-label="Menú de administración"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialog.current) onClose();
      }}
      className="fixed inset-y-0 left-0 m-0 h-dvh max-h-none w-[272px] max-w-[85vw] bg-surface p-0 text-ink shadow-overlay backdrop:bg-primary-dark/40 lg:hidden"
    >
      <div className="grid gap-6 p-4">
        <div className="flex items-center justify-between gap-3">
          <Link href="/dashboard" onClick={onClose} className="app-brand" aria-label="Análisis de Marcha IA — Inicio">
            <BrandMark />
          </Link>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar menú"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-ink-muted transition-colors duration-150 hover:bg-surface-subtle hover:text-ink"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        <SidebarNav onNavigate={onClose} />
      </div>
    </dialog>
  );
}

/** Marco de las pantallas de administrador: barra lateral, barra superior y contenido. */
export function AdminShell({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <AdminSummaryProvider>
      <div className="app-shell min-h-screen lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
        <a href="#app-content" className="app-skip-link">Ir al contenido</a>

        <aside className="hidden border-r border-line bg-surface lg:block">
          <div className="sticky top-0 grid gap-8 px-4 py-5">
            <Link href="/dashboard" className="app-brand px-1" aria-label="Análisis de Marcha IA — Inicio">
              <BrandMark />
            </Link>
            <SidebarNav />
          </div>
        </aside>

        <MobileDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />

        <div className="min-w-0">
          <header className="sticky top-0 z-30 border-b border-line bg-surface">
            <div className="mx-auto flex min-h-16 w-full max-w-[1320px] items-center gap-3 px-4 sm:px-6 lg:px-8">
              <button
                type="button"
                onClick={() => setMenuOpen(true)}
                aria-label="Abrir menú"
                aria-expanded={menuOpen}
                className="-ml-1.5 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-ink transition-colors duration-150 hover:bg-surface-subtle lg:hidden"
              >
                <Menu className="h-5 w-5" aria-hidden />
              </button>
              <p className="hidden truncate text-[15px] font-bold text-ink sm:block">Panel administrativo</p>
              <SystemStatus />
              <div className="ml-auto">
                <UserMenu />
              </div>
            </div>
          </header>

          <main id="app-content" className="app-content mx-auto w-full max-w-[1320px] px-4 sm:px-6 lg:px-8" tabIndex={-1}>
            {children}
          </main>
        </div>
      </div>
    </AdminSummaryProvider>
  );
}
