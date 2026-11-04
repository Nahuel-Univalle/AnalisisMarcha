"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, RefreshCw } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { AdminShell } from "@/components/admin/AdminShell";
import { Button } from "@/components/ui/Button";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { cn } from "@/lib/utils";
import { TopBar } from "./TopBar";

export function AppShell({ children, className }: { children: React.ReactNode; className?: string }) {
  const router = useRouter();
  const { user, ready, sessionError, retrySession } = useAuth();

  useEffect(() => {
    if (ready && !user && !sessionError) {
      router.replace("/login");
    }
  }, [ready, user, sessionError, router]);

  if (ready && !user && sessionError) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="grid w-full max-w-md gap-4">
          <InlineAlert tone="error">
            No se pudo verificar tu sesión. Puede ser un problema temporal del servidor o de la conexión.
          </InlineAlert>
          <Button className="justify-self-start" onClick={retrySession}>
            <RefreshCw aria-hidden />
            Reintentar
          </Button>
        </div>
      </main>
    );
  }

  if (!ready || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <p className="flex items-center gap-2 text-sm font-medium text-ink-muted">
          <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden />
          Cargando…
        </p>
      </main>
    );
  }

  if (user.role === "ADMIN") {
    return <AdminShell>{children}</AdminShell>;
  }

  return (
    <div className={cn("app-shell min-h-screen", className)}>
      <a href="#app-content" className="app-skip-link">Ir al contenido</a>
      <TopBar />
      <main id="app-content" className="app-container app-content" tabIndex={-1}>{children}</main>
    </div>
  );
}
