import { readFile } from "node:fs/promises";
import path from "node:path";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

function splitSqlStatements(sql: string) {
  const statements: string[] = [];
  let current = "";
  let inDollarBlock = false;

  for (const line of sql.split(/\r?\n/)) {
    const trimmed = line.trim();

    if (trimmed.startsWith("--")) continue;

    if (trimmed.includes("$$")) {
      inDollarBlock = !inDollarBlock;
    }

    current += `${line}\n`;

    if (!inDollarBlock && trimmed.endsWith(";")) {
      statements.push(current.trim().replace(/;$/, ""));
      current = "";
    }
  }

  if (current.trim()) {
    statements.push(current.trim().replace(/;$/, ""));
  }

  return statements.filter(Boolean);
}

async function main() {
  const patchPath = path.join(
    process.cwd(),
    "prisma",
    "manual_patches",
    "20260603_fix_auth_columns_safe.sql"
  );
  const sql = await readFile(patchPath, "utf8");

  for (const statement of splitSqlStatements(sql)) {
    await prisma.$executeRawUnsafe(statement);
  }

  console.log("Patch aplicado: prisma/manual_patches/20260603_fix_auth_columns_safe.sql");
}

main()
  .catch((error) => {
    console.error("APPLY_SAFE_AUTH_PATCH_ERROR", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
