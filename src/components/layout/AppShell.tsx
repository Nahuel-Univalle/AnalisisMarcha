"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { AppHeader } from "./AppHeader";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, ready } = useAuth();

  useEffect(() => {
    if (ready && !user) {
      router.push("/login");
    }
  }, [ready, user, router]);

  if (!ready || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-slate-600">Cargando...</p>
      </main>
    );
  }

  return (
    <>
      <AppHeader />
      <main className="page-container">{children}</main>
    </>
  );
}

