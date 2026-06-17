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
  "raw",
  "gait_parkinson_dataset_raw_merged.csv"
);
const SOURCE_FILE = "dataset/parkinson/raw/gait_parkinson_dataset_raw_merged.csv";
const DATASET_NAME = "parkinson_raw_merged";
const BATCH_SIZE = 5000;
const PROGRESS_EVERY = 10000;

loadEnv(".env");
loadEnv(".env.local");

const prisma = new PrismaClient();

const COLUMN_MAP = {
  sourceFile: "source_file",
  sourceDataset: "source_dataset",
  subjectId: "subject_id",
  study: "study",
  subjectType: "subject_type",
  subjectNumber: "subject_number",
  condition: "condition",
  parkinsonBinary: "parkinson_binary",
  walkNumber: "walk_number",
  walkType: "walk_type",
  sampleIndex: "sample_index",
  time: "time_seconds",
  left1: "left_1",
  left2: "left_2",
  left3: "left_3",
  left4: "left_4",
  left5: "left_5",
  left6: "left_6",
  left7: "left_7",
  left8: "left_8",
  right1: "right_1",
  right2: "right_2",
  right3: "right_3",
  right4: "right_4",
  right5: "right_5",
  right6: "right_6",
  right7: "right_7",
  right8: "right_8",
  leftTotal: "left_total",
  rightTotal: "right_total",
  totalForce: "total_force",
  forceDifference: "force_difference_left_minus_right",
  forceAsymmetryAbs: "force_asymmetry_abs",
  forceAsymmetryIndex: "force_asymmetry_index",
  leftContact: "left_contact",
  rightContact: "right_contact",
  doubleSupport: "double_support",
  noSupport: "no_support",
  leftCopX: "left_cop_x",
  leftCopY: "left_cop_y",
  rightCopX: "right_cop_x",
  rightCopY: "right_cop_y",
  overallCopX: "overall_cop_x",
  overallCopY: "overall_cop_y",
};

const INTEGER_FIELDS = new Set([
  "subjectNumber",
  "parkinsonBinary",
  "sampleIndex",
]);

const BOOLEAN_FIELDS = new Set([
  "leftContact",
  "rightContact",
  "doubleSupport",
  "noSupport",
]);

const FLOAT_FIELDS = new Set([
  "time",
  "left1",
  "left2",
  "left3",
  "left4",
  "left5",
  "left6",
  "left7",
  "left8",
  "right1",
  "right2",
  "right3",
  "right4",
  "right5",
  "right6",
  "right7",
  "right8",
  "leftTotal",
  "rightTotal",
  "totalForce",
  "forceDifference",
  "forceAsymmetryAbs",
  "forceAsymmetryIndex",
  "leftCopX",
  "leftCopY",
  "rightCopX",
  "rightCopY",
  "overallCopX",
  "overallCopY",
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

function toBoolean(value) {
  if (value === null || value === undefined || value === "") return null;
  const normalized = String(value).trim().toLowerCase();
  if (["1", "true", "t", "yes", "y"].includes(normalized)) return true;
  if (["0", "false", "f", "no", "n"].includes(normalized)) return false;
  return null;
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
  if (BOOLEAN_FIELDS.has(field)) return toBoolean(value);
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

function buildRecord(row, lineNumber) {
  const record = {};

  for (const [field, columnName] of Object.entries(COLUMN_MAP)) {
    record[field] = convertValue(field, getMappedCell(row, field, columnName));
  }

  record.sourceFile = record.sourceFile || SOURCE_FILE;
  record.subjectId = record.subjectId || "unknown_subject";
  record.walkNumber = record.walkNumber || "unknown_walk";
  record.sampleIndex = record.sampleIndex ?? lineNumber;

  const label = inferLabel(row, record);
  record.condition = label.condition;
  record.parkinsonBinary = label.parkinsonBinary;

  return record;
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

async function flushBatch(batch) {
  if (batch.length === 0) return 0;
  const result = await prisma.parkinsonRawSample.createMany({
    data: batch,
    skipDuplicates: true,
  });
  return result.count;
}

async function importRawCsv() {
  if (!fs.existsSync(DATASET_PATH)) {
    throw new Error(`No se encontró el CSV raw en ${SOURCE_FILE}.`);
  }

  const stream = fs.createReadStream(DATASET_PATH, { encoding: "utf8" });
  const reader = readline.createInterface({ input: stream, crlfDelay: Infinity });
  let headers = null;
  let pending = "";
  let rowsSeen = 0;
  let imported = 0;
  let skipped = 0;
  let batch = [];

  for await (const line of reader) {
    pending = pending ? `${pending}\n${line}` : line;
    if (!hasBalancedQuotes(pending)) continue;

    const values = parseCsvLine(pending);
    pending = "";

    if (!headers) {
      headers = values.map(normalizeHeader);
      continue;
    }

    rowsSeen += 1;
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] ?? "";
    });

    const record = buildRecord(row, rowsSeen);
    if (!record.sourceFile || !record.subjectId || record.sampleIndex === null) {
      skipped += 1;
      continue;
    }

    batch.push(record);

    if (batch.length >= BATCH_SIZE) {
      const inserted = await flushBatch(batch);
      imported += inserted;
      skipped += batch.length - inserted;
      batch = [];
    }

    if (rowsSeen % PROGRESS_EVERY === 0) {
      console.log(
        `Procesadas ${rowsSeen} filas. Importadas: ${imported}. Omitidas: ${skipped}.`
      );
    }
  }

  if (pending) throw new Error("El CSV terminó con comillas sin cerrar.");

  if (batch.length > 0) {
    const inserted = await flushBatch(batch);
    imported += inserted;
    skipped += batch.length - inserted;
  }

  return { rowsSeen, imported, skipped };
}

async function main() {
  const result = await importRawCsv();
  const [total, control, parkinson] = await Promise.all([
    prisma.parkinsonRawSample.count(),
    prisma.parkinsonRawSample.count({ where: { parkinsonBinary: 0 } }),
    prisma.parkinsonRawSample.count({ where: { parkinsonBinary: 1 } }),
  ]);

  const message = `Importación raw finalizada. Filas leídas: ${result.rowsSeen}. Filas nuevas importadas: ${result.imported}. Filas omitidas: ${result.skipped}. Total actual: ${total}. Control: ${control}. Parkinson: ${parkinson}.`;
  await createImportLog({
    imported: result.imported,
    skipped: result.skipped,
    status: "success",
    message,
  });

  console.log(message);
  console.log(`Raw total actual en PostgreSQL: ${total}`);
  console.log(`Raw control actual: ${control}`);
  console.log(`Raw Parkinson actual: ${parkinson}`);
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
      // La base puede no estar disponible.
    }
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
