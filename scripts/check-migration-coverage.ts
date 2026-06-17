import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const checks: Record<string, { table?: string; columns?: string[]; indexes?: string[] }> = {
  "20260601000000_dataset_parkinson_postgres": {
    table: "ParkinsonDatasetRecord",
    columns: [
      "id",
      "sourceFile",
      "subjectId",
      "condition",
      "parkinsonBinary",
      "walkNumber",
      "recordedSpeed",
      "meanForceAsymmetryAbs",
      "meanForceAsymmetryIndex",
      "createdAt",
    ],
    indexes: [
      "ParkinsonDatasetRecord_sourceFile_subjectId_walkNumber_key",
      "ParkinsonDatasetRecord_condition_idx",
      "ParkinsonDatasetRecord_parkinsonBinary_idx",
      "ParkinsonDatasetRecord_subjectId_idx",
    ],
  },
  "20260601000000_dataset_import_log": {
    table: "DatasetImportLog",
    columns: ["id", "datasetName", "filePath", "rowsImported", "rowsSkipped", "status", "createdAt"],
  },
  "20260601010000_sync_existing_dataset_tables": {
    table: "ParkinsonDatasetRecord",
    columns: ["stdLeftTotal", "stdRightTotal", "leftStepEvents", "rightStepEvents"],
  },
  "20260601190000_add_parkinson_raw_samples": {
    table: "ParkinsonRawSample",
    columns: ["id", "sourceFile", "subjectId", "sampleIndex", "leftTotal", "rightTotal", "createdAt"],
    indexes: [
      "ParkinsonRawSample_sourceFile_subjectId_walkNumber_sampleIndex_key",
      "ParkinsonRawSample_sourceFile_idx",
      "ParkinsonRawSample_subjectId_idx",
      "ParkinsonRawSample_condition_idx",
      "ParkinsonRawSample_parkinsonBinary_idx",
    ],
  },
  "20260601220000_add_cloudinary_video_storage": {
    table: "VideoMarcha",
    columns: [
      "originalVideoUrl",
      "originalVideoPublicId",
      "processedVideoUrl",
      "processedVideoPublicId",
      "videoProvider",
      "originalFileName",
      "processedFileName",
      "cloudinaryOriginalBytes",
      "cloudinaryProcessedBytes",
      "cloudinaryOriginalFormat",
      "cloudinaryProcessedFormat",
    ],
  },
  "20260602030000_add_local_video_fallback_urls": {
    table: "VideoMarcha",
    columns: ["localOriginalVideoUrl", "localProcessedVideoUrl"],
  },
};

async function tableExists(tableName: string) {
  const [row] = await prisma.$queryRawUnsafe<Array<{ exists: boolean }>>(
    `
      SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = $1
      ) AS exists
    `,
    tableName
  );
  return row?.exists ?? false;
}

async function missingColumns(tableName: string, columns: string[]) {
  const rows = await prisma.$queryRawUnsafe<Array<{ column_name: string }>>(
    `
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = $1
        AND column_name = ANY($2::text[])
    `,
    tableName,
    columns
  );
  const found = new Set(rows.map((row) => row.column_name));
  return columns.filter((column) => !found.has(column));
}

async function missingIndexes(indexes: string[]) {
  const rows = await prisma.$queryRawUnsafe<Array<{ indexname: string }>>(
    `
      SELECT indexname
      FROM pg_indexes
      WHERE schemaname = 'public'
        AND indexname = ANY($1::text[])
    `,
    indexes
  );
  const found = new Set(rows.map((row) => row.indexname));
  return indexes.filter((index) => !found.has(index));
}

async function main() {
  console.log("=== MIGRATION COVERAGE CHECK ===");

  for (const [migration, check] of Object.entries(checks)) {
    const missing: string[] = [];

    if (check.table && !(await tableExists(check.table))) {
      missing.push(`table:${check.table}`);
    }

    if (check.table && check.columns) {
      missing.push(...(await missingColumns(check.table, check.columns)).map((column) => `column:${check.table}.${column}`));
    }

    if (check.indexes) {
      missing.push(...(await missingIndexes(check.indexes)).map((index) => `index:${index}`));
    }

    console.log(`${missing.length === 0 ? "OK" : "MISSING"} ${migration}`);
    for (const item of missing) {
      console.log(`  ${item}`);
    }
  }
}

main()
  .catch((error) => {
    console.error("CHECK_MIGRATION_COVERAGE_ERROR", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
