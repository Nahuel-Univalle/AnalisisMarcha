import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const TABLES_TO_CHECK = [
  "User",
  "GaitAnalysis",
  "MedicalReport",
  "VideoMarcha",
  "Video",
  "VideoMatcha",
];

const USER_COLUMNS = [
  "id",
  "email",
  "name",
  "age",
  "passwordHash",
  "role",
  "createdAt",
  "updatedAt",
];

const VIDEO_COLUMNS = [
  "originalVideoUrl",
  "originalVideoPublicId",
  "processedVideoUrl",
  "processedVideoPublicId",
  "videoProvider",
  "localOriginalVideoUrl",
  "localProcessedVideoUrl",
];

type TableRow = {
  table_name: string;
  exists: boolean;
};

type ColumnRow = {
  table_name: string;
  column_name: string;
  data_type: string;
  udt_name: string;
  is_nullable: string;
  column_default: string | null;
};

type EnumRow = {
  typname: string;
  enum_values: string[];
};

type MigrationRow = {
  migration_name: string;
  started_at: Date;
  finished_at: Date | null;
  rolled_back_at: Date | null;
  logs: string | null;
};

type ConstraintRow = {
  table_name: string;
  constraint_name: string;
  constraint_type: string;
  columns: string[];
};

async function tableExists(tableName: string) {
  const [row] = await prisma.$queryRawUnsafe<TableRow[]>(
    `
      SELECT $1::text AS table_name, EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = $1
      ) AS exists
    `,
    tableName
  );

  return row;
}

async function columnsFor(tableName: string, columns: string[]) {
  return prisma.$queryRawUnsafe<ColumnRow[]>(
    `
      SELECT
        table_name,
        column_name,
        data_type,
        udt_name,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = $1
        AND column_name = ANY($2::text[])
      ORDER BY ordinal_position
    `,
    tableName,
    columns
  );
}

async function enumTypes() {
  return prisma.$queryRawUnsafe<EnumRow[]>(
    `
      SELECT
        t.typname,
        array_agg(e.enumlabel ORDER BY e.enumsortorder) AS enum_values
      FROM pg_type t
      JOIN pg_enum e ON e.enumtypid = t.oid
      JOIN pg_namespace n ON n.oid = t.typnamespace
      WHERE n.nspname = 'public'
        AND t.typname IN ('UserRole')
      GROUP BY t.typname
      ORDER BY t.typname
    `
  );
}

async function migrationRows() {
  return prisma.$queryRawUnsafe<MigrationRow[]>(
    `
      SELECT migration_name, started_at, finished_at, rolled_back_at, logs
      FROM "_prisma_migrations"
      ORDER BY started_at
    `
  );
}

async function constraintsFor(tableName: string) {
  return prisma.$queryRawUnsafe<ConstraintRow[]>(
    `
      SELECT
        tc.table_name,
        tc.constraint_name,
        tc.constraint_type,
        array_agg(kcu.column_name::text ORDER BY kcu.ordinal_position)::text[] AS columns
      FROM information_schema.table_constraints tc
      LEFT JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
       AND tc.table_schema = kcu.table_schema
      WHERE tc.table_schema = 'public'
        AND tc.table_name = $1
        AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE', 'FOREIGN KEY')
      GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
      ORDER BY tc.constraint_type, tc.constraint_name
    `,
    tableName
  );
}

function printColumns(title: string, columns: ColumnRow[], expected: string[]) {
  const found = new Set(columns.map((column) => column.column_name));
  console.log(`\n${title}`);

  for (const column of columns) {
    console.log(
      `  OK ${column.column_name} | ${column.data_type}/${column.udt_name} | nullable=${column.is_nullable} | default=${column.column_default ?? "-"}`
    );
  }

  for (const column of expected) {
    if (!found.has(column)) {
      console.log(`  MISSING ${column}`);
    }
  }
}

async function main() {
  console.log("=== DB SCHEMA AUDIT ===");

  console.log("\nTables");
  const tableRows = await Promise.all(TABLES_TO_CHECK.map(tableExists));
  for (const table of tableRows) {
    console.log(`  ${table.exists ? "OK" : "MISSING"} ${table.table_name}`);
  }

  const userColumns = await columnsFor("User", USER_COLUMNS);
  printColumns("User columns", userColumns, USER_COLUMNS);

  const userConstraints = await constraintsFor("User");
  console.log("\nUser constraints");
  for (const constraint of userConstraints) {
    console.log(
      `  ${constraint.constraint_type} ${constraint.constraint_name} (${constraint.columns.join(", ")})`
    );
  }

  const enums = await enumTypes();
  console.log("\nEnums");
  if (enums.length === 0) {
    console.log("  MISSING UserRole");
  } else {
    for (const enumType of enums) {
      console.log(`  OK ${enumType.typname}: ${enumType.enum_values.join(", ")}`);
    }
  }

  const videoColumns = await columnsFor("VideoMarcha", VIDEO_COLUMNS);
  printColumns("VideoMarcha storage columns", videoColumns, VIDEO_COLUMNS);

  console.log("\n_prisma_migrations");
  const migrations = await migrationRows();
  for (const migration of migrations) {
    const status = migration.rolled_back_at
      ? "ROLLED_BACK"
      : migration.finished_at
        ? "APPLIED"
        : "FAILED/PENDING";

    console.log(
      `  ${status} ${migration.migration_name} | finished=${migration.finished_at?.toISOString() ?? "-"} | rolledBack=${migration.rolled_back_at?.toISOString() ?? "-"}`
    );

    if (migration.logs) {
      console.log(`    logs: ${migration.logs.replace(/\s+/g, " ").trim()}`);
    }
  }
}

main()
  .catch((error) => {
    console.error("AUDIT_DB_SCHEMA_ERROR", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
