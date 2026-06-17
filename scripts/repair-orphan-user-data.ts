import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function orphanRows(table: string) {
  return prisma.$queryRawUnsafe<Array<{ id: string; userId: string | null }>>(
    `
      SELECT t."id", t."userId"
      FROM "${table}" t
      LEFT JOIN "User" u ON u."id" = t."userId"
      WHERE t."userId" IS NULL OR u."id" IS NULL
      ORDER BY t."id"
      LIMIT 100
    `
  );
}

async function main() {
  const ownerEmail = process.env.ORPHAN_OWNER_EMAIL?.trim().toLowerCase();
  const tables = ["VideoMarcha", "GaitAnalysis", "MedicalReport"];

  console.log("=== ORPHAN USER DATA AUDIT ===");
  for (const table of tables) {
    const rows = await orphanRows(table);
    console.log(`\n${table}: ${rows.length} huerfanos mostrados`);
    for (const row of rows) {
      console.log(`  id=${row.id} userId=${row.userId ?? "NULL"}`);
    }
  }

  if (!ownerEmail) {
    console.log("\nNo se aplicaron cambios. Define ORPHAN_OWNER_EMAIL=correo@ejemplo.com para asignar manualmente.");
    return;
  }

  const owner = await prisma.user.findUnique({
    where: { email: ownerEmail },
    select: { id: true, email: true },
  });

  if (!owner) {
    throw new Error(`No existe usuario con email ${ownerEmail}`);
  }

  console.log(`\nAsignando huerfanos a ${owner.email} (${owner.id})`);
  for (const table of tables) {
    const result = await prisma.$executeRawUnsafe(
      `
        UPDATE "${table}" t
        SET "userId" = $1
        WHERE t."userId" IS NULL
          OR NOT EXISTS (SELECT 1 FROM "User" u WHERE u."id" = t."userId")
      `,
      owner.id
    );
    console.log(`  ${table}: ${result} filas actualizadas`);
  }
}

main()
  .catch((error) => {
    console.error("REPAIR_ORPHAN_USER_DATA_ERROR", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
