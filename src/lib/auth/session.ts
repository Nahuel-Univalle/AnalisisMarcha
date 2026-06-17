import { cookies } from "next/headers";

export type SessionUser = {
  email: string;
  name: string;
  role: "USER" | "ADMIN";
};

export async function getSessionUser() {
  const cookieStore = await cookies();
  const rawUser = cookieStore.get("gait-user")?.value;

  if (!rawUser) return null;

  try {
    const parsed = JSON.parse(rawUser) as Partial<SessionUser>;

    if (!parsed.email || !parsed.name) return null;

    return {
      email: parsed.email.toLowerCase(),
      name: parsed.name,
      role: parsed.role === "ADMIN" ? "ADMIN" : "USER",
    };
  } catch {
    return null;
  }
}
