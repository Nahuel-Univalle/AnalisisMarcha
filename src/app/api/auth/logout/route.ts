import { NextResponse } from "next/server";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/auth/sessionToken";

export async function POST() {
  const response = NextResponse.json({ message: "Sesión cerrada." });

  response.cookies.set(SESSION_COOKIE, "", {
    ...sessionCookieOptions(),
    maxAge: 0,
  });

  return response;
}
