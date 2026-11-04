"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import Cookies from "js-cookie";
import { User } from "@/types";

type RegisterData = {
  name: string;
  age?: string;
  email: string;
  password: string;
  confirmPassword: string;
  accepted: boolean;
};

type AuthContextValue = {
  user: User | null;
  ready: boolean;
  /** No se pudo verificar la sesión (servidor o red), lo que no equivale a "sin sesión". */
  sessionError: boolean;
  retrySession: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  isAdmin: () => boolean;
};

type SessionState = { user: User | null; ready: boolean; sessionError: boolean };

type SessionCheck =
  | { outcome: "authenticated"; user: User }
  | { outcome: "unauthenticated" }
  | { outcome: "unavailable" };

const SESSION_TIMEOUT_MS = 8_000;
const SESSION_RETRY_DELAYS_MS = [1_000, 3_000];
const REVALIDATE_ON_VISIBLE_AFTER_MS = 60_000;

const AuthContext = createContext<AuthContextValue | null>(null);

// Solo 401 significa "sin sesión". Cualquier otro fallo (5xx, red, timeout o
// petición abortada) es temporal y no debe interpretarse como cierre de sesión.
async function checkSession(): Promise<SessionCheck> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), SESSION_TIMEOUT_MS);

  try {
    const response = await fetch("/api/auth/me", { cache: "no-store", signal: controller.signal });

    if (response.status === 401) return { outcome: "unauthenticated" };
    if (!response.ok) return { outcome: "unavailable" };

    const data = await response.json();
    return { outcome: "authenticated", user: data.user as User };
  } catch {
    return { outcome: "unavailable" };
  } finally {
    clearTimeout(timeout);
  }
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<SessionState>({ user: null, ready: false, sessionError: false });
  // Cada verificación, login o logout invalida las verificaciones en curso.
  const syncId = useRef(0);
  const lastSyncAt = useRef(0);

  const syncSession = useCallback(async () => {
    const id = ++syncId.current;

    for (let attempt = 0; ; attempt += 1) {
      const result = await checkSession();
      if (id !== syncId.current) return;

      if (result.outcome === "authenticated") {
        lastSyncAt.current = Date.now();
        localStorage.setItem("gait-user", JSON.stringify(result.user));
        setSession({ user: result.user, ready: true, sessionError: false });
        return;
      }

      if (result.outcome === "unauthenticated") {
        lastSyncAt.current = Date.now();
        localStorage.removeItem("gait-user");
        setSession({ user: null, ready: true, sessionError: false });
        return;
      }

      if (attempt >= SESSION_RETRY_DELAYS_MS.length) break;
      await wait(SESSION_RETRY_DELAYS_MS[attempt]);
      if (id !== syncId.current) return;
    }

    // Si ya había un usuario se conserva: el fallo puede ser momentáneo.
    setSession((current) => ({ ...current, ready: true, sessionError: !current.user }));
  }, []);

  useEffect(() => {
    // La identidad real vive en la cookie de sesion firmada (HttpOnly). El
    // usuario local solo sirve para pintar la interfaz y se valida con el servidor.
    Cookies.remove("gait-user", { path: "/" });

    const initialSync = setTimeout(() => void syncSession(), 0);

    // bfcache restaura la página con su estado congelado: hay que revalidarla.
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted) void syncSession();
    };
    const onVisibilityChange = () => {
      if (
        document.visibilityState === "visible" &&
        Date.now() - lastSyncAt.current > REVALIDATE_ON_VISIBLE_AFTER_MS
      ) {
        void syncSession();
      }
    };

    window.addEventListener("pageshow", onPageShow);
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      clearTimeout(initialSync);
      syncId.current += 1;
      window.removeEventListener("pageshow", onPageShow);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [syncSession]);

  const retrySession = useCallback(() => {
    setSession((current) => ({ ...current, ready: false, sessionError: false }));
    void syncSession();
  }, [syncSession]);

  const persistUser = (nextUser: User) => {
    syncId.current += 1;
    lastSyncAt.current = Date.now();
    localStorage.setItem("gait-user", JSON.stringify(nextUser));
    setSession({ user: nextUser, ready: true, sessionError: false });
  };

  const login = async (email: string, password: string) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "No se pudo iniciar sesión.");
    }

    persistUser(data.user);
  };

  const register = async (data: RegisterData) => {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const responseData = await response.json();

    if (!response.ok) {
      const error = new Error(responseData.message || "No se pudo crear la cuenta.");
      throw error;
    }

    persistUser(responseData.user);
  };

  const logout = () => {
    syncId.current += 1;
    localStorage.removeItem("gait-user");
    Cookies.remove("gait-user", { path: "/" });
    setSession({ user: null, ready: true, sessionError: false });
    void fetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
  };

  const isAdmin = () => session.user?.role === "ADMIN";

  return (
    <AuthContext.Provider
      value={{
        user: session.user,
        ready: session.ready,
        sessionError: session.sessionError,
        retrySession,
        login,
        register,
        logout,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }

  return context;
}
