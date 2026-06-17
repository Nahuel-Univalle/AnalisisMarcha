"use client";

import { AuthProvider } from "@/context/AuthContext";
import { AnalysisProvider } from "@/context/AnalysisContext";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AnalysisProvider>{children}</AnalysisProvider>
    </AuthProvider>
  );
}

