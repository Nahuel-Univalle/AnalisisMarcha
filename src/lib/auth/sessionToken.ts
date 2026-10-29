export const SESSION_COOKIE = "gait-session";
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

export type SessionPayload = {
  email: string;
  name: string;
  role: "USER" | "ADMIN";
  exp: number;
};

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const MIN_SECRET_LENGTH = 32;

function toBase64Url(bytes: Uint8Array) {
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(value: string) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

async function getKey() {
  const secret = process.env.AUTH_SESSION_SECRET;

  // Falla cerrado: nunca se firma ni se acepta nada sin un secreto fuerte.
  if (!secret || secret.length < MIN_SECRET_LENGTH) return null;

  return crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

export async function signSession(
  user: Pick<SessionPayload, "email" | "name" | "role">
) {
  const key = await getKey();

  if (!key) {
    throw new Error("AUTH_SESSION_SECRET no esta configurado correctamente.");
  }

  const payload: SessionPayload = {
    email: user.email.toLowerCase(),
    name: user.name,
    role: user.role === "ADMIN" ? "ADMIN" : "USER",
    exp: Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SECONDS,
  };
  const body = toBase64Url(encoder.encode(JSON.stringify(payload)));
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(body));

  return `${body}.${toBase64Url(new Uint8Array(signature))}`;
}

export async function verifySession(
  token: string | undefined
): Promise<SessionPayload | null> {
  if (!token) return null;

  const parts = token.split(".");
  if (parts.length !== 2) return null;

  try {
    const key = await getKey();
    if (!key) return null;

    const [body, signature] = parts;
    // crypto.subtle.verify compara en tiempo constante.
    const valid = await crypto.subtle.verify(
      "HMAC",
      key,
      fromBase64Url(signature),
      encoder.encode(body)
    );
    if (!valid) return null;

    const payload = JSON.parse(decoder.decode(fromBase64Url(body))) as Partial<SessionPayload>;

    if (
      typeof payload.email !== "string" ||
      !payload.email ||
      typeof payload.name !== "string" ||
      typeof payload.exp !== "number" ||
      payload.exp <= Math.floor(Date.now() / 1000)
    ) {
      return null;
    }

    return {
      email: payload.email.toLowerCase(),
      name: payload.name,
      role: payload.role === "ADMIN" ? "ADMIN" : "USER",
      exp: payload.exp,
    };
  } catch {
    return null;
  }
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  };
}
