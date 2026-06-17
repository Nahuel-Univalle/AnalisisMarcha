import { resolveMx } from "dns/promises";

// DNS error codes that positively confirm the domain cannot receive email:
// the domain does not exist (ENOTFOUND) or has no mail records (ENODATA).
// Any other error (ECONNREFUSED, ETIMEOUT, ESERVFAIL, EREFUSED...) means the
// DNS resolver could not be reached — a local/network limitation, not proof
// that the address is invalid — so we must not block the user on it.
const DEFINITIVE_FAILURE_CODES = new Set(["ENOTFOUND", "ENODATA"]);
const DNS_LOOKUP_TIMEOUT_MS = 3000;

function withTimeout<T>(promise: Promise<T>) {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) => {
      setTimeout(() => {
        const error = new Error("DNS lookup timed out") as NodeJS.ErrnoException;
        error.code = "ETIMEOUT";
        reject(error);
      }, DNS_LOOKUP_TIMEOUT_MS);
    }),
  ]);
}

export async function validateEmailDomain(email: string) {
  const cleanEmail = email.trim().toLowerCase();
  const domain = cleanEmail.split("@")[1];

  if (!domain) {
    return "El dominio del correo no es válido.";
  }

  try {
    const records = await withTimeout(resolveMx(domain));

    if (!records || records.length === 0) {
      return "El dominio del correo no puede recibir emails.";
    }

    return "";
  } catch (error) {
    const code = (error as NodeJS.ErrnoException)?.code;

    if (code && DEFINITIVE_FAILURE_CODES.has(code)) {
      return "El dominio del correo no existe o no puede recibir emails.";
    }

    // DNS could not be verified (offline, blocked resolver, serverless DNS
    // limits, etc.). The format and blocked-domain checks already validated
    // the address, so we allow it instead of rejecting legitimate users.
    return "";
  }
}
