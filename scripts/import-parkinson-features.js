/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("node:fs");
const path = require("node:path");
const readline = require("node:readline");
const { PrismaClient } = require("@prisma/client");

const PROJECT_ROOT = path.resolve(__dirname, "..");
const DATASET_PATH = path.join(
  PROJECT_ROOT,
  "dataset",
  "parkinson",
  "processed",
  "gait_parkinson_dataset_features_summary.csv"
);
const SOURCE_FILE =
  "dataset/parkinson/processed/gait_parkinson_dataset_features_summary.csv";
const DATASET_NAME = "parkinson_features_summary";

loadEnv(".env");
loadEnv(".env.local");

const prisma = new PrismaClient();

const COLUMN_MAP = {
  sourceFile: "source_file",
  subjectId: "subject_id",
  study: "study",
  subjectType: "subject_type",
  condition: "condition",
  parkinsonBinary: "parkinson_binary",
  walkNumber: "walk_number",
  walkType: "walk_type",
  genderCode: "gender_code",
  age: "age",
  heightM: "height_m",
  weightKg: "weight_kg",
  hoehnYahr: "hoehn_yahr",
  updrs: "updrs",
  updrsm: "updrsm",
  tuag: "tuag",
  recordedSpeed: "recorded_speed_m_per_s",
  meanLeftTotal: "mean_left_total",
  stdLeftTotal: "std_left_total",
  meanRightTotal: "mean_right_total",
  stdRightTotal: "std_right_total",
  meanTotalForce: "mean_total_force",
  meanForceAsymmetryAbs: "mean_force_asymmetry_abs",
  meanForceAsymmetryIndex: "mean_force_asymmetry_index",
  leftContactRatio: "left_contact_ratio",
  rightContactRatio: "right_contact_ratio",
  doubleSupportRatio: "double_support_ratio",
  leftStepEvents: "left_step_events",
  rightStepEvents: "right_step_events",
  estimatedCadence: "estimated_cadence_steps_per_min",
  meanLeftStanceTimeSec: "mean_left_stance_time_sec",
  meanRightStanceTimeSec: "mean_right_stance_time_sec",
  meanLeftSwingTimeSec: "mean_left_swing_time_sec",
  meanRightSwingTimeSec: "mean_right_swing_time_sec",
  stdLeftCopX: "std_left_cop_x",
  stdLeftCopY: "std_left_cop_y",
  stdRightCopX: "std_right_cop_x",
  stdRightCopY: "std_right_cop_y",
};

const INTEGER_FIELDS = new Set([
  "parkinsonBinary",
  "genderCode",
  "leftStepEvents",
  "rightStepEvents",
]);

const FLOAT_FIELDS = new Set([
  "age",
  "heightM",
  "weightKg",
  "hoehnYahr",
  "updrs",
  "updrsm",
  "tuag",
  "recordedSpeed",
  "meanLeftTotal",
  "stdLeftTotal",
  "meanRightTotal",
  "stdRightTotal",
  "meanTotalForce",
  "meanForceAsymmetryAbs",
  "meanForceAsymmetryIndex",
  "leftContactRatio",
  "rightContactRatio",
  "doubleSupportRatio",
  "estimatedCadence",
  "meanLeftStanceTimeSec",
  "meanRightStanceTimeSec",
  "meanLeftSwingTimeSec",
  "meanRightSwingTimeSec",
  "stdLeftCopX",
  "stdLeftCopY",
  "stdRightCopX",
  "stdRightCopY",
]);

function loadEnv(fileName) {
  const envPath = path.join(PROJECT_ROOT, fileName);
  if (!fs.existsSync(envPath)) return;

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const index = trimmed.indexOf("=");
    const key = trimmed.slice(0, index).trim();
    const value = trimmed
      .slice(index + 1)
      .trim()
      .replace(/^['"]|['"]$/g, "");

    if (!process.env[key]) process.env[key] = value;
  }
}

function normalizeHeader(value) {
  return String(value || "").trim().replace(/^\uFEFF/, "");
}

function parseCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];

    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
      continue;
    }

    if (char === '"') {
      quoted = !quoted;
      continue;
    }

    if (char === "," && !quoted) {
      values.push(current);
      current = "";
      continue;
    }

    current += char;
  }

  values.push(current);
  return values.map((value) => value.trim());
}

function hasBalancedQuotes(value) {
  let count = 0;
  for (let index = 0; index < value.length; index += 1) {
    if (value[index] !== '"') continue;
    if (value[index + 1] === '"') {
      index += 1;
      continue;
    }
    count += 1;
  }
  return count % 2 === 0;
}

function toFloat(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number.parseFloat(String(value).replace(",", ".").trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function toInt(value) {
  const parsed = toFloat(value);
  return parsed === null ? null : Math.trunc(parsed);
}

function getCell(row, columnName) {
  const value = row[columnName];
  return value === undefined || value === "" ? null : value;
}

function toCamelCase(value) {
  return value.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function getMappedCell(row, field, columnName) {
  return getCell(row, columnName) ?? getCell(row, field) ?? getCell(row, toCamelCase(columnName));
}

function convertValue(field, value) {
  if (INTEGER_FIELDS.has(field)) return toInt(value);
  if (FLOAT_FIELDS.has(field)) return toFloat(value);
  return value === null ? null : String(value);
}

function inferLabel(row, record) {
  const condition = String(row.condition || "").toLowerCase();
  const subjectType = String(row.subject_type || record.subjectType || "").toLowerCase();
  const sourceFile = String(row.source_file || record.sourceFile || "").toLowerCase();
  const parkinsonBinary = toInt(row.parkinson_binary);

  if (condition === "control" || subjectType === "co" || sourceFile.includes("co")) {
    return { condition: "control", parkinsonBinary: 0 };
  }

  if (
    condition === "parkinson" ||
    condition === "pd" ||
    subjectType === "pt" ||
    sourceFile.includes("pt") ||
    parkinsonBinary === 1
  ) {
    return { condition: "parkinson", parkinsonBinary: 1 };
  }

  return {
    condition: record.condition || "unknown",
    parkinsonBinary: record.parkinsonBinary ?? 0,
  };
}

function buildRecord(row) {
  const record = {};

  for (const [field, columnName] of Object.entries(COLUMN_MAP)) {
    record[field] = convertValue(field, getMappedCell(row, field, columnName));
  }

  record.sourceFile = record.sourceFile || SOURCE_FILE;
  record.subjectId = record.subjectId || "unknown_subject";
  record.walkNumber = record.walkNumber || "unknown_walk";

  const label = inferLabel(row, record);
  record.condition = label.condition;
  record.parkinsonBinary = label.parkinsonBinary;

  return record;
}

async function readCsvRows(filePath) {
  const stream = fs.createReadStream(filePath, { encoding: "utf8" });
  const reader = readline.createInterface({ input: stream, crlfDelay: Infinity });
  let headers = null;
  let pending = "";
  const rows = [];

  for await (const line of reader) {
    pending = pending ? `${pending}\n${line}` : line;
    if (!hasBalancedQuotes(pending)) continue;

    const values = parseCsvLine(pending);
    pending = "";

    if (!headers) {
      headers = values.map(normalizeHeader);
      continue;
    }

    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] ?? "";
    });
    rows.push(row);
  }

  if (pending) throw new Error("El CSV terminó con comillas sin cerrar.");
  return rows;
}

async function createImportLog({ imported, skipped, status, message }) {
  await prisma.datasetImportLog.create({
    data: {
      datasetName: DATASET_NAME,
      filePath: SOURCE_FILE,
      rowsImported: imported,
      rowsSkipped: skipped,
      status,
      message,
    },
  });
}

async function datasetCounts() {
  const [total, control, parkinson, grouped] = await Promise.all([
    prisma.parkinsonDatasetRecord.count(),
    prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 0 } }),
    prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 1 } }),
    prisma.parkinsonDatasetRecord.groupBy({
      by: ["condition", "parkinsonBinary"],
      _count: { _all: true },
      orderBy: [{ condition: "asc" }, { parkinsonBinary: "asc" }],
    }),
  ]);

  return { total, control, parkinson, grouped };
}

async function main() {
  if (!fs.existsSync(DATASET_PATH)) {
    throw new Error(`No se encontró el CSV procesado en ${SOURCE_FILE}.`);
  }

  const rows = await readCsvRows(DATASET_PATH);
  let imported = 0;
  let skipped = 0;
  const errors = [];

  for (const [index, row] of rows.entries()) {
    const record = buildRecord(row);

    try {
      const result = await prisma.parkinsonDatasetRecord.createMany({
        data: [record],
        skipDuplicates: true,
      });

      if (result.count === 0) {
        skipped += 1;
      } else {
        imported += 1;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      errors.push(`Fila ${index + 2}: ${message}`);
    }
  }

  const status = errors.length > 0 ? "error" : "success";
  const counts = await datasetCounts();
  const message =
    errors.length > 0
      ? `Importación con errores. Primeros errores: ${errors.slice(0, 5).join(" | ")}`
      : `Importación finalizada. ${imported} registros importados y ${skipped} omitidos por duplicado. Total: ${counts.total}. Control: ${counts.control}. Parkinson: ${counts.parkinson}.`;

  await createImportLog({ imported, skipped, status, message });

  console.log(`Archivo leído: ${SOURCE_FILE}`);
  console.log(`Filas encontradas: ${rows.length}`);
  console.log(`Filas importadas: ${imported}`);
  console.log(`Filas omitidas: ${skipped}`);
  console.log(`Errores: ${errors.length}`);
  console.log(`Total actual en ParkinsonDatasetRecord: ${counts.total}`);
  console.log(`Cantidad control: ${counts.control}`);
  console.log(`Cantidad Parkinson: ${counts.parkinson}`);
  console.log("Conteo por condición:");
  for (const item of counts.grouped) {
    console.log(
      `- ${item.condition} / ${item.parkinsonBinary}: ${item._count._all}`
    );
  }

  if (errors.length > 0) {
    process.exitCode = 1;
  }
}

main()
  .catch(async (error) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(message);
    try {
      await createImportLog({
        imported: 0,
        skipped: 0,
        status: "error",
        message,
      });
    } catch {
      // La base puede no estar disponible todavía.
    }
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
