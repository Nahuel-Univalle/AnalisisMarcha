"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import { TopBar } from "./TopBar";

export function AppShell({ children, className }: { children: React.ReactNode; className?: string }) {
  const router = useRouter();
  const { user, ready } = useAuth();

  useEffect(() => {
    if (ready && !user) {
      router.push("/login");
    }
  }, [ready, user, router]);

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

  return (
    <div className={cn("app-shell min-h-screen", className)}>
      <a href="#app-content" className="app-skip-link">Ir al contenido</a>
      <TopBar />
      <main id="app-content" className="app-container app-content" tabIndex={-1}>{children}</main>
    </div>
  );
}
