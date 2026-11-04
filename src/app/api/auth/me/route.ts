import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/guards";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/auth/sessionToken";
import { prisma } from "@/lib/prisma";

// 401 borra la cookie: si fuera válida pero el usuario ya no existe, proxy.ts
// devolvería /login a /dashboard y el cliente nunca saldría de ese bucle.
function unauthenticated() {
  const response = NextResponse.json({ message: "No autenticado." }, { status: 401 });

  response.cookies.set(SESSION_COOKIE, "", {
    ...sessionCookieOptions(),
    maxAge: 0,
  });

  return response;
}

export async function GET() {
  try {
    const result = await requireUser();

    if ("error" in result) return unauthenticated();

    const user = await prisma.user.findUnique({
      where: { email: result.user.email },
      select: { name: true, age: true, email: true, role: true },
    });

    if (!user) return unauthenticated();

    return NextResponse.json({ user });
  } catch (error) {
    // Base de datos no disponible: es temporal y no significa "sin sesión".
    console.error("AUTH_ME_UNAVAILABLE", error);

    return NextResponse.json(
      { message: "No se pudo verificar la sesión en este momento." },
      { status: 503 }
    );
  }
}
