/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("node:fs");
const path = require("node:path");
const { PrismaClient } = require("@prisma/client");

const PROJECT_ROOT = path.resolve(__dirname, "..");
const DATASET_LOGS = [
  "parkinson_features_summary",
  "parkinson_raw_merged",
  "parkinson_dataset",
];

loadEnv(".env");
loadEnv(".env.local");

const prisma = new PrismaClient();

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

async function main() {
  const deletedLogs = await prisma.datasetImportLog.deleteMany({
    where: { datasetName: { in: DATASET_LOGS } },
  });
  const deletedRaw = await prisma.parkinsonRawSample.deleteMany();
  const deletedSummary = await prisma.parkinsonDatasetRecord.deleteMany();

  console.log("Reset Parkinson completado.");
  console.log(`Logs eliminados: ${deletedLogs.count}`);
  console.log(`Muestras crudas eliminadas: ${deletedRaw.count}`);
  console.log(`Registros resumidos eliminados: ${deletedSummary.count}`);
  console.log("No se borraron usuarios, videos, análisis, informes ni logs generales.");
}

main()
  .catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
