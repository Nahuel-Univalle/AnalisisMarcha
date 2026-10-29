"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Database, FileText, Files, History, House, LogOut, ScanLine, type LucideIcon } from "lucide-react";
import { BrandMark } from "@/components/brand/BrandMark";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

type NavItem = { label: string; href: string; icon: LucideIcon; match: (pathname: string) => boolean };

const USER_NAV: NavItem[] = [
  { label: "Inicio", href: "/dashboard", icon: House, match: (p) => p === "/dashboard" },
  {
    label: "Nuevo análisis", href: "/analisis/subir-video", icon: ScanLine,
    match: (p) => p.startsWith("/analisis/") && !p.startsWith("/analisis/informe"),
  },
  { label: "Seguimiento", href: "/seguimiento", icon: History, match: (p) => p.startsWith("/seguimiento") },
  { label: "Informes", href: "/analisis/informe", icon: FileText, match: (p) => p.startsWith("/analisis/informe") },
];

const ADMIN_NAV: NavItem[] = [
  { label: "Inicio", href: "/dashboard", icon: House, match: (p) => p === "/dashboard" },
  { label: "Datasets", href: "/datasets/parkinson", icon: Database, match: (p) => p.startsWith("/datasets") },
  { label: "Informes globales", href: "/seguimiento", icon: Files, match: (p) => p.startsWith("/seguimiento") },
];

export function TopBar() {
  const router = useRouter();
  const pathname = usePathname();
  const { logout, user, isAdmin } = useAuth();
  const admin = isAdmin();
  const nav = admin ? ADMIN_NAV : USER_NAV;
  const initials = user?.name?.split(" ").filter(Boolean).slice(0, 2)
    .map((part) => part[0]?.toUpperCase()).join("") || "U";

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <header className="app-topbar">
      <div className="app-container app-topbar-inner">
        <Link href="/dashboard" className="app-brand" aria-label="Análisis de Marcha IA — Inicio">
          <BrandMark />
        </Link>
        <nav aria-label="Navegación principal" className="app-navigation">
          <ul>
            {nav.map(({ label, href, icon: Icon, match }) => {
              const active = match(pathname);
              return (
                <li key={href}>
                  <Link href={href} aria-current={active ? "page" : undefined}
                    className={cn("app-nav-link", active && "app-nav-link-active")}>
                    <Icon className="h-4 w-4" aria-hidden />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="app-account">
          <span className="app-avatar" aria-hidden>{initials}</span>
          <div className="app-account-name">
            <p title={user?.name}>{user?.name || "Usuario"}</p>
            <span>{admin ? "Administrador" : "Usuario"}</span>
          </div>
          <button type="button" onClick={handleLogout} className="app-logout" aria-label="Cerrar sesión" title="Cerrar sesión">
            <LogOut className="h-4 w-4" aria-hidden />
            <span>Cerrar sesión</span>
          </button>
        </div>
      </div>
    </header>
  );
}
