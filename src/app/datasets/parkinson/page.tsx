"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, RefreshCw } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAuth } from "@/context/AuthContext";

type DatasetRecord = {
  id: string;
  subjectId: string;
  condition: string;
  walkNumber: string | null;
  age: number | null;
  recordedSpeed: number | null;
  meanForceAsymmetryAbs: number | null;
  meanForceAsymmetryIndex: number | null;
  estimatedCadence: number | null;
  doubleSupportRatio: number | null;
};

type DatasetResponse = {
  summary: {
    totalRecords: number;
    controlCount: number;
    parkinsonCount: number;
  };
  warnings: string[];
  records: DatasetRecord[];
  pagination: {
    page: number;
    limit: number;
    totalRecords: number;
    totalPages: number;
  };
};

type RawStatus = {
  totalRawSamples: number;
  controlSamples: number;
  parkinsonSamples: number;
  readyForTraining: boolean;
  message: string;
};

type ModelStatus = {
  modelAvailable: boolean;
  trainingReady: boolean;
  metricsAvailable: boolean;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1Score: number | null;
  samples?: number | null;
  controlSamples?: number | null;
  parkinsonSamples?: number | null;
  validationMethod?: string | null;
  trainSize?: number | null;
  testSize?: number | null;
  warning?: string | null;
  controlRecords: number;
  parkinsonRecords: number;
  rawSamples: number;
  status?: string;
  message: string;
};

const EMPTY_RESPONSE: DatasetResponse = {
  summary: {
    totalRecords: 0,
    controlCount: 0,
    parkinsonCount: 0,
  },
  warnings: [],
  records: [],
  pagination: {
    page: 1,
    limit: 20,
    totalRecords: 0,
    totalPages: 1,
  },
};

const EMPTY_RAW_STATUS: RawStatus = {
  totalRawSamples: 0,
  controlSamples: 0,
  parkinsonSamples: 0,
  readyForTraining: false,
  message: "Aún no se cargaron muestras crudas.",
};

const EMPTY_MODEL_STATUS: ModelStatus = {
  modelAvailable: false,
  trainingReady: false,
  metricsAvailable: false,
  accuracy: null,
  precision: null,
  recall: null,
  f1Score: null,
  samples: null,
  controlSamples: null,
  parkinsonSamples: null,
  validationMethod: null,
  trainSize: null,
  testSize: null,
  warning: null,
  controlRecords: 0,
  parkinsonRecords: 0,
  rawSamples: 0,
  status: "pendiente de entrenamiento",
  message: "Aún no existe modelo entrenado disponible.",
};

function formatNumber(value: number | null, suffix = "") {
  if (value === null || value === undefined) return "Sin dato";
  return `${value}${suffix}`;
}

export default function ParkinsonDatasetPage() {
  const router = useRouter();
  const { ready, isAdmin } = useAuth();
  const [data, setData] = useState<DatasetResponse>(EMPTY_RESPONSE);
  const [rawStatus, setRawStatus] = useState<RawStatus>(EMPTY_RAW_STATUS);
  const [modelStatus, setModelStatus] =
    useState<ModelStatus>(EMPTY_MODEL_STATUS);
  const [page, setPage] = useState(1);
  const [condition, setCondition] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const params = useMemo(() => {
    const query = new URLSearchParams({
      page: String(page),
      limit: "20",
    });

    if (condition) query.set("condition", condition);
    return query.toString();
  }, [page, condition]);

  useEffect(() => {
    if (ready && !isAdmin()) {
      router.replace("/dashboard");
    }
  }, [ready, isAdmin, router]);

  useEffect(() => {
    if (!ready || !isAdmin()) return;

    let active = true;

    async function loadReferences() {
      setLoading(true);
      setError(null);

      try {
        const [summaryResponse, rawResponse, modelResponse] = await Promise.all([
          fetch(`/api/datasets/parkinson/summary?${params}`),
          fetch("/api/datasets/parkinson/raw-status"),
          fetch("/api/ml/model-status"),
        ]);
        const [summaryPayload, rawPayload, modelPayload] = await Promise.all([
          summaryResponse.json(),
          rawResponse.json(),
          modelResponse.json(),
        ]);

        if (!active) return;
        setData(summaryPayload as DatasetResponse);
        setRawStatus(rawPayload as RawStatus);
        setModelStatus(modelPayload as ModelStatus);
        if (!summaryResponse.ok || !rawResponse.ok || !modelResponse.ok) {
          setError("No se pudo consultar toda la información técnica.");
        }
      } catch {
        if (active) {
          setError("No se pudo conectar con el servicio de referencia.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadReferences();

    return () => {
      active = false;
    };
  }, [params, ready, isAdmin]);

  if (!ready || !isAdmin()) return null;

  const kpis = [
    ["Registros", data.summary.totalRecords],
    ["Muestras", rawStatus.totalRawSamples],
    ["Control", data.summary.controlCount],
    ["Parkinson", data.summary.parkinsonCount],
    ["Raw control", rawStatus.controlSamples],
    ["Raw Parkinson", rawStatus.parkinsonSamples],
    ["Datos preparados", modelStatus.trainingReady ? "Sí" : "No"],
  ];
  const summaryChartData = [
    { label: "Control", total: data.summary.controlCount },
    { label: "Parkinson", total: data.summary.parkinsonCount },
    { label: "Raw control", total: rawStatus.controlSamples },
    { label: "Raw Parkinson", total: rawStatus.parkinsonSamples },
  ];

  return (
    <AppShell>
      <section className="grid gap-6 animate-fadeIn">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-4xl font-black text-slate-900">
              Patrones de referencia
            </h1>
            <p className="mt-2 max-w-3xl text-slate-500">
              Sección para revisar los datos de referencia usados por la
              aplicación. Los resultados para pacientes siguen siendo
              orientativos y requieren valoración profesional.
            </p>
          </div>

          <Button variant="outline" onClick={() => setPage(1)}>
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </Button>
        </div>

        <Card className="border-blue-200 bg-blue-50">
          <div className="flex items-start gap-3">
            <BookOpen className="mt-1 h-5 w-5 text-primary" />
            <div>
              <h2 className="font-black text-slate-900">
                Datos de referencia
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Esta información resume el conjunto control/Parkinson cargado
                en PostgreSQL. No representa una valoración clínica individual.
              </p>
            </div>
          </div>
        </Card>

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700 shadow-md">
            {error}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-4">
          {kpis.map(([label, value]) => (
            <Card key={label} className="p-5">
              <p className="text-sm font-semibold text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-black text-slate-900">
                {value}
              </p>
            </Card>
          ))}
        </div>

        <Card>
          <h2 className="text-2xl font-black text-slate-900">
            Distribución del dataset
          </h2>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summaryChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="label" stroke="#6B7280" />
                <YAxis stroke="#6B7280" />
                <Tooltip
                  cursor={{ fill: "rgba(59, 130, 246, 0.08)" }}
                  contentStyle={{
                    borderRadius: "16px",
                    borderColor: "#E5E7EB",
                    boxShadow: "0 12px 28px rgba(30, 64, 175, 0.14)",
                  }}
                />
                <Bar dataKey="total" fill="#3B82F6" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <h2 className="text-xl font-black text-slate-950">
              Estado de muestras crudas
            </h2>
            <p className="mt-3 leading-7 text-slate-600">{rawStatus.message}</p>
          </Card>

          <Card>
            <h2 className="text-xl font-black text-slate-950">
              Preparación de datos
            </h2>
            <p className="mt-3 leading-7 text-slate-600">
              Los datos de referencia contienen registros control y Parkinson
              suficientes para apoyar una comparación orientativa.
            </p>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {[
                [
                  "Registros resumidos",
                  `${modelStatus.controlRecords} control / ${modelStatus.parkinsonRecords} Parkinson`,
                ],
                [
                  "Estado",
                  modelStatus.trainingReady ? "Datos preparados" : "Datos incompletos",
                ],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-500">{label}</p>
                  <p className="mt-1 font-bold text-slate-950">{value}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {data.warnings.length > 0 && (
          <div className="grid gap-3">
            {data.warnings.map((warning) => (
              <div
                key={warning}
                className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-800 shadow-md"
              >
                {warning}
              </div>
            ))}
          </div>
        )}

        <Card>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-2xl font-black text-slate-950">
              Registros resumidos
            </h2>

            <input
              value={condition}
              onChange={(event) => {
                setCondition(event.target.value);
                setPage(1);
              }}
              placeholder="Filtrar condición"
              className="rounded-2xl border border-slate-200 px-4 py-2 text-sm outline-none transition-all duration-200 focus:border-secondary focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
            />
          </div>

          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="py-3 pr-4">Sujeto</th>
                  <th className="py-3 pr-4">Condición</th>
                  <th className="py-3 pr-4">Caminata</th>
                  <th className="py-3 pr-4">Edad</th>
                  <th className="py-3 pr-4">Velocidad</th>
                  <th className="py-3 pr-4">Asimetría</th>
                  <th className="py-3 pr-4">Ritmo</th>
                  <th className="py-3">Apoyo</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td className="py-6 text-slate-500" colSpan={8}>
                      Cargando información de referencia...
                    </td>
                  </tr>
                ) : data.records.length === 0 ? (
                  <tr>
                    <td className="py-6 text-slate-500" colSpan={8}>
                      No hay registros resumidos para mostrar.
                    </td>
                  </tr>
                ) : (
                  data.records.map((record) => (
                    <tr
                      key={record.id}
                      className="border-b border-slate-100 transition hover:bg-blue-50/70"
                    >
                      <td className="py-3 pr-4 font-semibold text-slate-900">
                        {record.subjectId}
                      </td>
                      <td className="py-3 pr-4">{record.condition}</td>
                      <td className="py-3 pr-4">{record.walkNumber ?? "-"}</td>
                      <td className="py-3 pr-4">{formatNumber(record.age)}</td>
                      <td className="py-3 pr-4">
                        {formatNumber(record.recordedSpeed)}
                      </td>
                      <td className="py-3 pr-4">
                        {formatNumber(
                          record.meanForceAsymmetryIndex ??
                            record.meanForceAsymmetryAbs
                        )}
                      </td>
                      <td className="py-3 pr-4">
                        {formatNumber(record.estimatedCadence)}
                      </td>
                      <td className="py-3">
                        {formatNumber(record.doubleSupportRatio)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <p className="text-sm text-slate-500">
              Página {data.pagination.page} de {data.pagination.totalPages}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                disabled={page >= data.pagination.totalPages}
                onClick={() => setPage((current) => current + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </Card>
      </section>
    </AppShell>
  );
}
