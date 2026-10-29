"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
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
import { PageHeader, SectionHeader } from "@/components/ui/PageHeader";
import { InlineAlert } from "@/components/ui/InlineAlert";
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
      <div className="grid gap-8">
        <PageHeader
          eyebrow="Administración"
          title="Patrones de referencia"
          description="Sección para revisar los datos de referencia usados por la aplicación. Los resultados para pacientes siguen siendo orientativos y requieren valoración profesional."
          actions={
            <Button variant="outline" onClick={() => setPage(1)}>
              <RefreshCw aria-hidden />
              Actualizar
            </Button>
          }
        />

        <InlineAlert tone="info">
          <span className="font-semibold text-ink">Datos de referencia.</span>{" "}
          Esta información resume el conjunto control/Parkinson cargado en
          PostgreSQL. No representa una valoración clínica individual.
        </InlineAlert>

        {error && <InlineAlert tone="error">{error}</InlineAlert>}

        <section
          aria-label="Indicadores del dataset"
          className="reveal grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-4 xl:grid-cols-7"
        >
          {kpis.map(([label, value]) => (
            <div key={label} className="bg-surface px-5 py-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.09em] text-ink-subtle">{label}</p>
              <p className="tabular mt-2 text-2xl font-extrabold tracking-[-0.02em] text-ink">{value}</p>
            </div>
          ))}
        </section>

        <div className="grid gap-6 xl:grid-cols-12">
          <section className="reveal rounded-xl border border-line bg-surface p-6 xl:col-span-8">
            <SectionHeader title="Distribución del dataset" />
            <div className="mt-5 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summaryChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(18, 79, 72, 0.13)" vertical={false} />
                  <XAxis dataKey="label" stroke="#124F48" tickLine={false} axisLine={{ stroke: "rgba(18, 79, 72, 0.13)" }} fontSize={12} />
                  <YAxis stroke="#124F48" tickLine={false} axisLine={false} fontSize={12} />
                  <Tooltip
                    cursor={{ fill: "rgba(204, 252, 240, 0.4)" }}
                    contentStyle={{
                      borderRadius: "8px",
                      borderColor: "rgba(18, 79, 72, 0.13)",
                      boxShadow: "0 4px 16px rgba(18, 79, 72, 0.08)",
                      fontSize: 13,
                    }}
                  />
                  <Bar dataKey="total" fill="#0B9586" radius={[4, 4, 0, 0]} maxBarSize={56} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="reveal divide-y divide-line rounded-xl border border-line bg-surface xl:col-span-4">
            <div className="p-6">
              <h2 className="text-base font-bold text-ink">Estado de muestras crudas</h2>
              <p className="mt-2 text-sm leading-6 text-ink-muted">{rawStatus.message}</p>
            </div>
            <div className="p-6">
              <h2 className="text-base font-bold text-ink">Preparación de datos</h2>
              <p className="mt-2 text-sm leading-6 text-ink-muted">
                Los datos de referencia contienen registros control y Parkinson
                suficientes para apoyar una comparación orientativa.
              </p>
              <dl className="mt-4 space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-subtle">Registros resumidos</dt>
                  <dd className="text-right font-mono text-[13px] text-ink">
                    {modelStatus.controlRecords} control / {modelStatus.parkinsonRecords} Parkinson
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-subtle">Estado</dt>
                  <dd className="font-semibold text-ink">
                    {modelStatus.trainingReady ? "Datos preparados" : "Datos incompletos"}
                  </dd>
                </div>
              </dl>
            </div>
          </section>
        </div>

        {data.warnings.length > 0 && (
          <div className="grid gap-3">
            {data.warnings.map((warning) => (
              <InlineAlert key={warning} tone="warning">
                {warning}
              </InlineAlert>
            ))}
          </div>
        )}

        <section className="reveal overflow-hidden rounded-xl border border-line bg-surface">
          <div className="flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between">
            <SectionHeader title="Registros resumidos" />
            <div className="w-full md:max-w-xs">
              <label htmlFor="condition-filter" className="sr-only">
                Filtrar condición
              </label>
              <input
                id="condition-filter"
                value={condition}
                onChange={(event) => {
                  setCondition(event.target.value);
                  setPage(1);
                }}
                placeholder="Filtrar condición"
                className="h-10 w-full rounded-lg border border-line-strong bg-surface px-3 text-sm text-ink outline-none transition-colors placeholder:text-ink-subtle focus:border-accent-blue"
              />
            </div>
          </div>

          <div className="max-h-[560px] overflow-auto border-t border-line">
            <table className="w-full min-w-190 text-left text-sm">
              <thead className="sticky top-0 z-10 bg-surface-subtle text-[11px] uppercase tracking-[0.08em] text-ink-subtle">
                <tr className="border-b border-line">
                  <th scope="col" className="px-5 py-2.5 font-bold">Sujeto</th>
                  <th scope="col" className="py-2.5 pr-4 font-bold">Condición</th>
                  <th scope="col" className="py-2.5 pr-4 text-right font-bold">Caminata</th>
                  <th scope="col" className="py-2.5 pr-4 text-right font-bold">Edad</th>
                  <th scope="col" className="py-2.5 pr-4 text-right font-bold">Velocidad</th>
                  <th scope="col" className="py-2.5 pr-4 text-right font-bold">Asimetría</th>
                  <th scope="col" className="py-2.5 pr-4 text-right font-bold">Ritmo</th>
                  <th scope="col" className="py-2.5 pr-5 text-right font-bold">Apoyo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {loading ? (
                  <tr>
                    <td className="px-5 py-6 text-ink-muted" colSpan={8}>
                      Cargando información de referencia...
                    </td>
                  </tr>
                ) : data.records.length === 0 ? (
                  <tr>
                    <td className="px-5 py-6 text-ink-muted" colSpan={8}>
                      No hay registros resumidos para mostrar.
                    </td>
                  </tr>
                ) : (
                  data.records.map((record) => (
                    <tr key={record.id} className="transition-colors duration-150 hover:bg-surface-subtle">
                      <td className="px-5 py-2.5 font-semibold text-ink">{record.subjectId}</td>
                      <td className="py-2.5 pr-4 text-ink-muted">{record.condition}</td>
                      <td className="py-2.5 pr-4 text-right font-mono text-[13px] text-ink">{record.walkNumber ?? "-"}</td>
                      <td className="py-2.5 pr-4 text-right font-mono text-[13px] text-ink">{formatNumber(record.age)}</td>
                      <td className="py-2.5 pr-4 text-right font-mono text-[13px] text-ink">{formatNumber(record.recordedSpeed)}</td>
                      <td className="py-2.5 pr-4 text-right font-mono text-[13px] text-ink">
                        {formatNumber(record.meanForceAsymmetryIndex ?? record.meanForceAsymmetryAbs)}
                      </td>
                      <td className="py-2.5 pr-4 text-right font-mono text-[13px] text-ink">{formatNumber(record.estimatedCadence)}</td>
                      <td className="py-2.5 pr-5 text-right font-mono text-[13px] text-ink">{formatNumber(record.doubleSupportRatio)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-3 border-t border-line px-5 py-4 md:flex-row md:items-center md:justify-between">
            <p className="font-mono text-[13px] text-ink-muted">
              Página {data.pagination.page} de {data.pagination.totalPages}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= data.pagination.totalPages}
                onClick={() => setPage((current) => current + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
