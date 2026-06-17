import Link from "next/link";
import { Activity } from "lucide-react";

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/85 shadow-md shadow-slate-200/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-8">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-slate-950"
        >
          <Activity className="h-6 w-6 text-cyan-600" />
          Análisis de Marcha IA
        </Link>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden text-sm font-semibold text-slate-700 transition hover:text-primary md:block"
          >
            Iniciar sesión
          </Link>

          <Link
            href="/registro"
            className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white shadow-md transition duration-200 hover:scale-[1.02] hover:bg-blue-600 hover:shadow-lg"
          >
            Crear cuenta
          </Link>
        </div>
      </div>
    </header>
  );
}
