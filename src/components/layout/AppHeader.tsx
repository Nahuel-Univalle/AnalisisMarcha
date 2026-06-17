"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Activity, LogOut, Menu, UserCircle, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";

export function AppHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const { logout, user, isAdmin } = useAuth();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const links = isAdmin()
    ? [
        ["Inicio", "/dashboard"],
        ["Datasets", "/datasets/parkinson"],
        ["Informes globales", "/seguimiento"],
      ]
    : [
        ["Inicio", "/dashboard"],
        ["Nuevo análisis", "/analisis/subir-video"],
        ["Seguimiento", "/seguimiento"],
        ["Informes", "/analisis/informe"],
      ];
  const initials =
    user?.name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "U";

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/85 shadow-md shadow-slate-200/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-8">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 font-black text-slate-900"
        >
          <Activity className="h-6 w-6 text-accent" />
          Análisis de Marcha IA
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-semibold text-slate-600 md:flex">
          {links.map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className={`rounded-full px-3 py-2 transition ${
                pathname === href || pathname.startsWith(`${href}/`)
                  ? "bg-blue-50 text-primary shadow-sm"
                  : "hover:bg-slate-50 hover:text-primary"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-semibold text-slate-600 shadow-sm lg:flex">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-black text-white">
              {initials}
            </span>
            <UserCircle className="h-4 w-4 text-secondary" />
            <span>{isAdmin() ? "Administrador" : user?.name}</span>
          </div>

          <Button variant="outline" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Cerrar sesión</span>
          </Button>

          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:scale-[1.02] hover:shadow md:hidden"
            aria-label="Abrir menú"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="animate-slideIn border-t border-slate-200 bg-white/95 px-4 py-4 shadow-lg backdrop-blur-xl md:hidden">
          <nav className="grid gap-3 text-sm font-semibold text-slate-700">
            {links.map(([label, href]) => (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={`rounded-xl px-3 py-2 transition ${
                  pathname === href || pathname.startsWith(`${href}/`)
                    ? "bg-blue-50 text-primary"
                    : "hover:bg-blue-50 hover:text-primary"
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
