import { randomUUID } from "node:crypto";
import bcrypt from "bcryptjs";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const email = "admin@ejemplo.com";
  const passwordHash = await bcrypt.hash("Admin@12345", 10);
  const id = randomUUID();

  const [admin] = await prisma.$queryRawUnsafe<
    Array<{ email: string; name: string; role: string }>
  >(
    `
      INSERT INTO "User" ("id", "email", "name", "passwordHash", "role")
      VALUES ($1, $2, $3, $4, 'ADMIN')
      ON CONFLICT ("email")
      DO UPDATE SET
        "name" = EXCLUDED."name",
        "passwordHash" = EXCLUDED."passwordHash",
        "role" = 'ADMIN',
        "updatedAt" = CURRENT_TIMESTAMP
      RETURNING "email", "name", "role"::text
    `,
    id,
    email,
    "Administrador del Sistema",
    passwordHash
  );

  console.log(`Admin listo: ${admin.email} (${admin.role})`);
}

main()
  .catch((error) => {
    console.error("CREATE_ADMIN_ERROR", error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
