import { getSessionUser } from "@/lib/auth/session";
import { prisma } from "@/lib/prisma";

export async function requireUser() {
  const sessionUser = await getSessionUser();

  if (!sessionUser) {
    return { error: Response.json({ message: "No autenticado." }, { status: 401 }) };
  }

  const user = await prisma.user.findUnique({
    where: { email: sessionUser.email },
    select: { id: true, email: true, name: true, role: true },
  });

  if (!user) {
    return { error: Response.json({ message: "Usuario no encontrado." }, { status: 404 }) };
  }

  return { user };
}

export async function requireAdmin() {
  const result = await requireUser();

  if ("error" in result) return result;

  if (result.user.role !== "ADMIN") {
    return { error: Response.json({ message: "No autorizado." }, { status: 403 }) };
  }

  return result;
}
