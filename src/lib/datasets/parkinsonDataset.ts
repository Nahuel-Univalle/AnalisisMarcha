import { prisma } from "@/lib/prisma";

export const PARKINSON_IMPORT_WARNING =
  "El análisis se basa en patrones de referencia disponibles. Para una valoración más precisa, el resultado debe ser revisado por un profesional de salud.";

export type ParkinsonRecordQuery = {
  page?: number;
  limit?: number;
  condition?: string;
};

export type ParkinsonEvaluationStats = {
  totalRecords: number;
  controlCount: number;
  parkinsonCount: number;
  control: DatasetAverages | null;
  parkinson: DatasetAverages | null;
  overall: DatasetAverages | null;
  warnings: string[];
};

export type DatasetAverages = {
  averageAge: number | null;
  averageSpeed: number | null;
  averageAsymmetry: number | null;
  averageCadence: number | null;
  averageDoubleSupport: number | null;
};

const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 20;

function normalizePage(value?: number) {
  if (!value || Number.isNaN(value) || value < 1) return 1;
  return Math.floor(value);
}

function normalizeLimit(value?: number) {
  if (!value || Number.isNaN(value) || value < 1) return DEFAULT_LIMIT;
  return Math.min(Math.floor(value), MAX_LIMIT);
}

function round(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined) return null;
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function mapAverages(aggregate: {
  _avg: {
    age: number | null;
    recordedSpeed: number | null;
    meanForceAsymmetryAbs: number | null;
    meanForceAsymmetryIndex: number | null;
    estimatedCadence: number | null;
    doubleSupportRatio: number | null;
  };
}): DatasetAverages {
  return {
    averageAge: round(aggregate._avg.age, 1),
    averageSpeed: round(aggregate._avg.recordedSpeed, 3),
    averageAsymmetry: round(
      aggregate._avg.meanForceAsymmetryIndex ??
        aggregate._avg.meanForceAsymmetryAbs,
      3
    ),
    averageCadence: round(aggregate._avg.estimatedCadence, 1),
    averageDoubleSupport: round(aggregate._avg.doubleSupportRatio, 3),
  };
}

function buildWarnings(total: number, controlCount: number, parkinsonCount: number) {
  const warnings: string[] = [];

  if (total === 0) {
    warnings.push(PARKINSON_IMPORT_WARNING);
    return warnings;
  }

  if (controlCount > 0 && parkinsonCount === 0) {
    warnings.push(
      "El análisis se basa en patrones de referencia disponibles. Para una valoración más precisa, el resultado debe ser revisado por un profesional de salud."
    );
  }

  if (controlCount === 0 && parkinsonCount > 0) {
    warnings.push(
      "El análisis se basa en patrones de referencia disponibles. Para una valoración más precisa, el resultado debe ser revisado por un profesional de salud."
    );
  }

  return Array.from(new Set(warnings));
}

export async function getParkinsonDatasetSummary() {
  const [totalRecords, controlCount, parkinsonCount, aggregate] =
    await Promise.all([
      prisma.parkinsonDatasetRecord.count(),
      prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 0 } }),
      prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 1 } }),
      prisma.parkinsonDatasetRecord.aggregate({
        _avg: {
          age: true,
          recordedSpeed: true,
          meanForceAsymmetryAbs: true,
          meanForceAsymmetryIndex: true,
          estimatedCadence: true,
          doubleSupportRatio: true,
        },
      }),
    ]);

  return {
    summary: {
      totalRecords,
      controlCount,
      parkinsonCount,
      ...mapAverages(aggregate),
    },
    warnings: buildWarnings(totalRecords, controlCount, parkinsonCount),
  };
}

export async function getParkinsonDatasetRecords(query: ParkinsonRecordQuery = {}) {
  const page = normalizePage(query.page);
  const limit = normalizeLimit(query.limit);
  const where = query.condition
    ? { condition: { equals: query.condition, mode: "insensitive" as const } }
    : {};

  const [totalRecords, records] = await Promise.all([
    prisma.parkinsonDatasetRecord.count({ where }),
    prisma.parkinsonDatasetRecord.findMany({
      where,
      orderBy: [{ subjectId: "asc" }, { walkNumber: "asc" }],
      skip: (page - 1) * limit,
      take: limit,
      select: {
        id: true,
        subjectId: true,
        condition: true,
        parkinsonBinary: true,
        walkNumber: true,
        walkType: true,
        age: true,
        recordedSpeed: true,
        meanForceAsymmetryAbs: true,
        meanForceAsymmetryIndex: true,
        estimatedCadence: true,
        doubleSupportRatio: true,
        createdAt: true,
      },
    }),
  ]);

  return {
    records,
    pagination: {
      page,
      limit,
      totalRecords,
      totalPages: Math.max(1, Math.ceil(totalRecords / limit)),
    },
  };
}

async function aggregateFor(parkinsonBinary?: number) {
  const where = parkinsonBinary === undefined ? undefined : { parkinsonBinary };

  const [count, aggregate] = await Promise.all([
    prisma.parkinsonDatasetRecord.count({ where }),
    prisma.parkinsonDatasetRecord.aggregate({
      where,
      _avg: {
        age: true,
        recordedSpeed: true,
        meanForceAsymmetryAbs: true,
        meanForceAsymmetryIndex: true,
        estimatedCadence: true,
        doubleSupportRatio: true,
      },
    }),
  ]);

  return count > 0 ? mapAverages(aggregate) : null;
}

export async function getParkinsonDatasetStatsForEvaluation(): Promise<ParkinsonEvaluationStats> {
  const [totalRecords, controlCount, parkinsonCount, control, parkinson, overall] =
    await Promise.all([
      prisma.parkinsonDatasetRecord.count(),
      prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 0 } }),
      prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 1 } }),
      aggregateFor(0),
      aggregateFor(1),
      aggregateFor(),
    ]);

  return {
    totalRecords,
    controlCount,
    parkinsonCount,
    control,
    parkinson,
    overall,
    warnings: buildWarnings(totalRecords, controlCount, parkinsonCount),
  };
}
