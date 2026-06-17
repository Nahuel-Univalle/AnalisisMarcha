"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  Database,
  FileText,
  Users,
  Video,
} from "lucide-react";
import { Card } from "@/components/ui/Card";

type AdminSummary = {
  totalUsers: number;
  totalAnalyses: number;
  totalReports: number;
  totalVideos: number;
  datasetSummary: {
    datasetRecords: number;
    rawSamples: number;
  };
  modelStatus: {
    available: boolean;
    metricsAvailable: boolean;
    accuracy: number | null;
    message: string;
  };
  recentAnalyses: Array<{
    id: string;
    userEmail: string;
    userName: string;
    date: string;
    alertLevel: string;
    summary: string;
  }>;
  recentReports: Array<{
    id: string;
    userEmail: string;
    userName: string;
    title: string;
    date: string;
    alertLevel: string;
    summary: string;
  }>;
  recentUsers: Array<{
    email: string;
    name: string;
    role: string;
    date: string;
  }>;
};

const EMPTY_SUMMARY: AdminSummary = {
  totalUsers: 0,
  totalAnalyses: 0,
  totalReports: 0,
  totalVideos: 0,
  datasetSummary: {
    datasetRecords: 0,
    rawSamples: 0,
  },
  modelStatus: {
    available: false,
    metricsAvailable: false,
    accuracy: null,
    message: "Sin datos",
  },
  recentAnalyses: [],
  recentReports: [],
  recentUsers: [],
};

export function AdminDashboard() {
  const [summary, setSummary] = useState<AdminSummary>(EMPTY_SUMMARY);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      try {
        const response = await fetch("/api/admin/summary");
        if (!response.ok) return;
        const payload = (await response.json()) as AdminSummary;
        if (active) setSummary(payload);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadSummary();

    return () => {
      active = false;
    };
  }, []);

  const metrics = [
    { label: "Usuarios registrados", value: summary.totalUsers, icon: Users },
    { label: "Análisis totales", value: summary.totalAnalyses, icon: Activity },
    { label: "Informes generados", value: summary.totalReports, icon: FileText },
    { label: "Videos procesados", value: summary.totalVideos, icon: Video },
    {
      label: "Registros de referencia",
      value: summary.datasetSummary.datasetRecords,
      icon: Database,
    },
    {
      label: "Estado del modelo",
      value: summary.modelStatus.available ? "Disponible" : "No disponible",
      icon: BarChart3,
    },
  ];

  return (
    <section className="grid gap-6 animate-fadeIn">
      <div>
        <h1 className="text-4xl font-black text-slate-900">
          Panel administrativo
        </h1>
        <p className="mt-2 text-slate-500">
          Resumen general del sistema de análisis de marcha.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.label}>
              <Icon className="mb-4 h-7 w-7 text-primary" />
              <p className="text-sm text-slate-500">{metric.label}</p>
              <p className="mt-1 text-2xl font-black text-slate-900">
                {loading ? "..." : metric.value}
              </p>
            </Card>
          );
        })}
      </div>

      <Card>
        <h2 className="text-2xl font-black text-slate-950">
          Accesos rápidos
        </h2>
        <div className="mt-5 flex flex-wrap gap-3">
          {[
            ["Datasets", "/datasets/parkinson"],
            ["Informes globales", "/seguimiento"],
          ].map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-900 shadow-md transition duration-200 hover:scale-[1.02] hover:bg-slate-50 hover:shadow-lg"
            >
              {label}
            </Link>
          ))}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="text-xl font-black text-slate-950">
            Últimos análisis
          </h2>
          <div className="mt-4 space-y-3">
            {summary.recentAnalyses.length === 0 ? (
              <p className="text-sm text-slate-500">Sin análisis registrados.</p>
            ) : (
              summary.recentAnalyses.map((analysis) => (
                <div key={analysis.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
                  <p className="font-bold text-slate-950">{analysis.userName}</p>
                  <p className="text-sm text-slate-500">
                    {analysis.userEmail} | {analysis.date} | {analysis.alertLevel}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-black text-slate-950">
            Últimos informes
          </h2>
          <div className="mt-4 space-y-3">
            {summary.recentReports.length === 0 ? (
              <p className="text-sm text-slate-500">Sin informes registrados.</p>
            ) : (
              summary.recentReports.map((report) => (
                <div key={report.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
                  <p className="font-bold text-slate-950">{report.title}</p>
                  <p className="text-sm text-slate-500">
                    {report.userEmail} | {report.date} | {report.alertLevel}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-black text-slate-950">
            Usuarios recientes
          </h2>
          <div className="mt-4 space-y-3">
            {summary.recentUsers.length === 0 ? (
              <p className="text-sm text-slate-500">Sin usuarios registrados.</p>
            ) : (
              summary.recentUsers.map((user) => (
                <div key={user.email} className="rounded-lg border border-slate-100 bg-slate-50 p-3 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
                  <p className="font-bold text-slate-950">{user.name}</p>
                  <p className="text-sm text-slate-500">
                    {user.email} | {user.role} | {user.date}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </section>
  );
}
