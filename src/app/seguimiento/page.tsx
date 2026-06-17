"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { useAuth } from "@/context/AuthContext";
import { SavedReport } from "@/types";

const ALERT_FILTERS = ["Todos", "Bajo", "Medio", "Alto"];

export default function TrackingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [alertFilter, setAlertFilter] = useState("Todos");
  const [userFilter, setUserFilter] = useState("");

  useEffect(() => {
    let active = true;

    async function loadReports() {
      setLoading(true);
      try {
        const response = await fetch(
          admin ? "/api/admin/reports" : "/api/me/reports"
        );
        if (!response.ok) return;
        const payload = (await response.json()) as { reports: SavedReport[] };
        if (active) setReports(payload.reports);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadReports();

    return () => {
      active = false;
    };
  }, [admin]);

  const filteredReports = useMemo(() => {
    return reports.filter((report) => {
      const matchesAlert =
        alertFilter === "Todos" || report.alertLevel === alertFilter;
      const matchesUser =
        !admin ||
        !userFilter.trim() ||
        report.userEmail?.toLowerCase().includes(userFilter.toLowerCase()) ||
        report.userName?.toLowerCase().includes(userFilter.toLowerCase());

      return matchesAlert && matchesUser;
    });
  }, [admin, alertFilter, reports, userFilter]);

  return (
    <AppShell>
      <section className="grid gap-6 animate-fadeIn">
        <div>
          <h1 className="text-4xl font-black text-slate-900">
            {admin ? "Informes guardados del sistema" : "Seguimiento de análisis"}
          </h1>

          <p className="mt-2 max-w-3xl text-slate-500">
            {admin
              ? "Vista global de informes generados por todos los usuarios."
              : "Revisa tus informes guardados. Esta sección no reemplaza controles médicos."}
          </p>
        </div>

        <Card>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-2xl font-black text-slate-900">
              {admin ? "Informes globales" : "Informes guardados"}
            </h2>

            <div className="flex flex-wrap gap-2">
              {ALERT_FILTERS.map((filter) => (
                <button
                  key={filter}
                  onClick={() => setAlertFilter(filter)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold ${
                    alertFilter === filter
                      ? "bg-slate-950 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {admin && (
            <input
              value={userFilter}
              onChange={(event) => setUserFilter(event.target.value)}
              placeholder="Filtrar por usuario o email"
              className="mt-5 w-full rounded-lg border border-slate-200 px-4 py-3 text-sm outline-none focus:border-cyan-500 md:max-w-sm"
            />
          )}

          <div className="mt-6 space-y-3">
            {loading ? (
              <p className="text-slate-500">Cargando informes guardados...</p>
            ) : filteredReports.length === 0 ? (
              <p className="text-slate-500">
                {admin
                  ? "No existen informes registrados en el sistema."
                  : "No tienes informes guardados"}
              </p>
            ) : (
              filteredReports.map((report) => (
                <div
                  key={report.id}
                  className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-md transition duration-200 hover:-translate-y-1 hover:shadow-xl"
                >
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <h3 className="font-bold text-slate-950">
                        {report.title}
                      </h3>
                      <p className="text-sm text-slate-500">
                        {report.date}
                        {admin && report.userEmail
                          ? ` | ${report.userName} (${report.userEmail})`
                          : ""}
                      </p>
                      {report.summary && (
                        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                          {report.summary}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <AlertBadge level={report.alertLevel} />

                      <Button
                        variant="outline"
                        onClick={() => router.push("/analisis/informe")}
                      >
                        Ver informe
                      </Button>
                    </div>
                  </div>

                  {(report.originalVideoUrl ||
                    report.localOriginalVideoUrl ||
                    report.processedVideoUrl ||
                    report.localProcessedVideoUrl) && (
                    <div className="grid gap-4 lg:grid-cols-2">
                      {(report.originalVideoUrl || report.localOriginalVideoUrl) && (
                        <div>
                          <p className="text-sm font-bold text-slate-600">
                            Video original
                          </p>
                          <video
                            src={
                              report.originalVideoUrl ||
                              report.localOriginalVideoUrl ||
                              undefined
                            }
                            controls
                            className="mt-2 w-full rounded-lg shadow-md"
                          />
                        </div>
                      )}

                      {(report.processedVideoUrl ||
                        report.localProcessedVideoUrl) && (
                        <div>
                          <p className="text-sm font-bold text-slate-600">
                            Video con puntos clave
                          </p>
                          <video
                            src={
                              report.processedVideoUrl ||
                              report.localProcessedVideoUrl ||
                              undefined
                            }
                            controls
                            className="mt-2 w-full rounded-lg shadow-md"
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      </section>
    </AppShell>
  );
}
