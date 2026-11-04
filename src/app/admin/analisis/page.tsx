"use client";

import { ActivityTable } from "@/components/admin/ActivityTable";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";

export default function AdminAnalysesPage() {
  return (
    <AppShell>
      <div className="grid gap-8">
        <PageHeader
          eyebrow="Administración"
          title="Análisis"
          description="Todos los análisis guardados en el sistema. Son clasificaciones experimentales, no diagnósticos."
        />
        <div className="reveal" style={{ "--i": 1 } as React.CSSProperties}>
          <ActivityTable title="Análisis registrados" pageSize={12} />
        </div>
      </div>
    </AppShell>
  );
}
