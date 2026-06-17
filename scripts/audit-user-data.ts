import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function countNull(table: string, column: string) {
  const [row] = await prisma.$queryRawUnsafe<Array<{ count: bigint }>>(
    `SELECT COUNT(*)::bigint AS count FROM "${table}" WHERE "${column}" IS NULL`
  );
  return Number(row?.count ?? 0);
}

async function countByUser(table: string) {
  return prisma.$queryRawUnsafe<
    Array<{ userId: string | null; email: string | null; name: string | null; count: bigint }>
  >(
    `
      SELECT t."userId", u."email", u."name", COUNT(*)::bigint AS count
      FROM "${table}" t
      LEFT JOIN "User" u ON u."id" = t."userId"
      GROUP BY t."userId", u."email", u."name"
      ORDER BY count DESC
    `
  );
}

function printByUser(title: string, rows: Awaited<ReturnType<typeof countByUser>>) {
  console.log(`\n${title}`);
  if (rows.length === 0) {
    console.log("  Sin registros");
    return;
  }

  for (const row of rows) {
    console.log(
      `  userId=${row.userId ?? "NULL"} | email=${row.email ?? "SIN_USUARIO"} | name=${row.name ?? "-"} | total=${Number(row.count)}`
    );
  }
}

async function main() {
  const [totalUsers, totalAnalyses, totalVideos, totalReports] = await Promise.all([
    prisma.user.count(),
    prisma.gaitAnalysis.count(),
    prisma.videoMarcha.count(),
    prisma.medicalReport.count(),
  ]);

  console.log("=== USER DATA AUDIT ===");
  console.log(`Total usuarios: ${totalUsers}`);
  console.log(`Total analisis: ${totalAnalyses}`);
  console.log(`Total videos: ${totalVideos}`);
  console.log(`Total informes: ${totalReports}`);
  console.log(`Analisis con userId null: ${await countNull("GaitAnalysis", "userId")}`);
  console.log(`Videos con userId null: ${await countNull("VideoMarcha", "userId")}`);
  console.log(`Informes con userId null: ${await countNull("MedicalReport", "userId")}`);

  printByUser("Analisis por userId", await countByUser("GaitAnalysis"));
  printByUser("Videos por userId", await countByUser("VideoMarcha"));
  printByUser("Informes por userId", await countByUser("MedicalReport"));
}

main()
  .catch((error) => {
    console.error("AUDIT_USER_DATA_ERROR", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
