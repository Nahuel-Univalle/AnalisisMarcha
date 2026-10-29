import { cookies } from "next/headers";
import { SESSION_COOKIE, verifySession } from "@/lib/auth/sessionToken";

export type SessionUser = {
  email: string;
  name: string;
  role: "USER" | "ADMIN";
};

export async function getSessionUser(): Promise<SessionUser | null> {
  const cookieStore = await cookies();
  const payload = await verifySession(cookieStore.get(SESSION_COOKIE)?.value);

  if (!payload) return null;

  return { email: payload.email, name: payload.name, role: payload.role };
}
