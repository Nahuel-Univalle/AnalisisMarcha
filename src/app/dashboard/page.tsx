"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, FileText, ShieldCheck, UploadCloud } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";
import { AdminDashboard } from "@/components/admin/AdminDashboard";

type DashboardSummary = {
  totalAnalyses: number;
  totalReports: number;
  lastAlertLevel: string;
  privacyStatus: string;
  recentAnalyses: Array<{
    id: string;
    alertLevel: string;
    summary: string;
    date: string;
    videoName: string;
    originalVideoUrl: string | null;
  }>;
  analysisCount: number;
  reportCount: number;
  latestAlert: string;
  latestAnalysisDate: string | null;
};

const EMPTY_SUMMARY: DashboardSummary = {
  totalAnalyses: 0,
  totalReports: 0,
  lastAlertLevel: "Sin datos",
  privacyStatus: "Activa",
  recentAnalyses: [],
  analysisCount: 0,
  reportCount: 0,
  latestAlert: "Sin datos",
  latestAnalysisDate: null,
};

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";
  const [summary, setSummary] = useState<DashboardSummary>(EMPTY_SUMMARY);
  const [loadingSummary, setLoadingSummary] = useState(true);

  useEffect(() => {
    if (admin) return;

    let active = true;

    async function loadSummary() {
      try {
        const response = await fetch("/api/me/summary");
        if (!response.ok) return;
        const payload = (await response.json()) as DashboardSummary;
        if (active) setSummary(payload);
      } finally {
        if (active) setLoadingSummary(false);
      }
    }

    loadSummary();

    return () => {
      active = false;
    };
  }, [admin]);

  if (admin) {
    return (
      <AppShell>
        <AdminDashboard />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <section className="grid gap-6 animate-fadeIn">
        <div>
          <p className="text-lg text-slate-600">
            Hola, {user?.name || "Usuario"}
          </p>

          <h1 className="text-4xl font-black text-slate-900">
            Panel de análisis de marcha
          </h1>

          <p className="mt-2 text-slate-500">
            Sube un video y revisa tus informes generados.
          </p>
        </div>

        <Card className="bg-linear-to-br from-primary via-secondary to-accent text-white shadow-xl shadow-blue-200/70">
          <h2 className="text-2xl font-black">Nuevo análisis de marcha</h2>

          <p className="mt-3 max-w-2xl text-cyan-50">
            Sube un video caminando para recibir una orientación inicial sobre
            posibles señales funcionales.
          </p>

          <Button
            className="mt-6"
            variant="secondary"
            onClick={() => router.push("/analisis/subir-video")}
          >
            <UploadCloud className="h-5 w-5" />
            Subir video
          </Button>
        </Card>

        <div className="grid gap-4 md:grid-cols-4">
          {[
            {
              label: "Análisis realizados",
              value: loadingSummary ? "..." : String(summary.totalAnalyses),
              icon: Activity,
              tone: "from-blue-50 to-white text-accent",
            },
            {
              label: "Último nivel de alerta",
              value: loadingSummary ? "..." : summary.lastAlertLevel,
              icon: ShieldCheck,
              tone: "from-emerald-50 to-white text-emerald-600",
            },
            {
              label: "Informes generados",
              value: loadingSummary ? "..." : String(summary.totalReports),
              icon: FileText,
              tone: "from-indigo-50 to-white text-secondary",
            },
            {
              label: "Privacidad protegida",
              value: "Activa",
              icon: ShieldCheck,
              tone: "from-slate-50 to-white text-primary",
            },
          ].map((item) => {
            const Icon = item.icon;

            return (
              <Card key={item.label} className={`bg-linear-to-br ${item.tone}`}>
                <Icon className="mb-4 h-10 w-10" />
                <p className="text-sm text-slate-500">{item.label}</p>
                <p className="mt-1 text-2xl font-black text-slate-900">
                  {item.value}
                </p>
              </Card>
            );
          })}
        </div>

        {!loadingSummary && summary.totalAnalyses === 0 && (
          <Card>
            <h2 className="text-2xl font-black text-slate-900">
              No tienes análisis aún
            </h2>
            <p className="mt-2 text-slate-500">
              Cuando subas tu primer video, tus resultados aparecerán aquí.
            </p>
          </Card>
        )}

        <Card>
          <h2 className="text-2xl font-black text-slate-900">
            ¿Qué observa el sistema?
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-4">
            {[
              "Velocidad de marcha",
              "Estabilidad",
              "Simetría corporal",
              "Regularidad de pasos",
              "Movimiento de brazos",
              "Posible rigidez",
              "Posible arrastre de pies",
              "Diferencia lateral",
            ].map((item) => (
              <div key={item} className="rounded-2xl border border-slate-100 bg-slate-50 p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
                <p className="font-bold text-slate-900">{item}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </AppShell>
  );
}
