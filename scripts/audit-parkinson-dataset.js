/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("node:fs");
const path = require("node:path");
const { PrismaClient } = require("@prisma/client");

const PROJECT_ROOT = path.resolve(__dirname, "..");

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

function printDistribution(title, rows) {
  console.log(title);
  for (const item of rows) {
    console.log(`- ${item.condition} / ${item.parkinsonBinary}: ${item._count._all}`);
  }
}

async function main() {
  const [
    summaryTotal,
    summaryControl,
    summaryParkinson,
    rawTotal,
    rawControl,
    rawParkinson,
    uniqueSources,
    uniqueSubjects,
    summaryDistribution,
    rawDistribution,
  ] = await Promise.all([
    prisma.parkinsonDatasetRecord.count(),
    prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 0 } }),
    prisma.parkinsonDatasetRecord.count({ where: { parkinsonBinary: 1 } }),
    prisma.parkinsonRawSample.count(),
    prisma.parkinsonRawSample.count({ where: { parkinsonBinary: 0 } }),
    prisma.parkinsonRawSample.count({ where: { parkinsonBinary: 1 } }),
    prisma.parkinsonDatasetRecord.findMany({
      distinct: ["sourceFile"],
      select: { sourceFile: true },
    }),
    prisma.parkinsonDatasetRecord.findMany({
      distinct: ["subjectId"],
      select: { subjectId: true },
    }),
    prisma.parkinsonDatasetRecord.groupBy({
      by: ["condition", "parkinsonBinary"],
      _count: { _all: true },
      orderBy: [{ condition: "asc" }, { parkinsonBinary: "asc" }],
    }),
    prisma.parkinsonRawSample.groupBy({
      by: ["condition", "parkinsonBinary"],
      _count: { _all: true },
      orderBy: [{ condition: "asc" }, { parkinsonBinary: "asc" }],
    }),
  ]);
  const trainingReady = summaryControl > 0 && summaryParkinson > 0;

  console.log(`summary total: ${summaryTotal}`);
  console.log(`summary control: ${summaryControl}`);
  console.log(`summary parkinson: ${summaryParkinson}`);
  console.log(`raw total: ${rawTotal}`);
  console.log(`raw control: ${rawControl}`);
  console.log(`raw parkinson: ${rawParkinson}`);
  console.log(`source files unicos: ${uniqueSources.length}`);
  console.log(`sujetos unicos: ${uniqueSubjects.length}`);
  printDistribution("distribucion summary por condicion:", summaryDistribution);
  printDistribution("distribucion raw por condicion:", rawDistribution);
  console.log(`ambas clases summary: ${trainingReady ? "si" : "no"}`);
  console.log(`trainingReady: ${trainingReady}`);

  if (!trainingReady) {
    process.exitCode = 1;
  }
}

main()
  .catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
