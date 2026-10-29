"use client";

import { createContext, useContext, useEffect, useState } from "react";
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
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  isAdmin: () => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    // La identidad real vive en la cookie de sesion firmada (HttpOnly). El
    // usuario local solo sirve para pintar la interfaz y se valida con el servidor.
    Cookies.remove("gait-user", { path: "/" });

    const syncSession = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });

        if (cancelled) return;

        if (response.ok) {
          const data = await response.json();
          localStorage.setItem("gait-user", JSON.stringify(data.user));
          setUser(data.user as User);
        } else {
          localStorage.removeItem("gait-user");
          setUser(null);
        }
      } catch {
        if (cancelled) return;
        localStorage.removeItem("gait-user");
        setUser(null);
      } finally {
        if (!cancelled) setReady(true);
      }
    };

    void syncSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const persistUser = (nextUser: User) => {
    localStorage.setItem("gait-user", JSON.stringify(nextUser));
    setUser(nextUser);
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
    localStorage.removeItem("gait-user");
    Cookies.remove("gait-user", { path: "/" });
    setUser(null);
    void fetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
  };

  const isAdmin = () => user?.role === "ADMIN";

  return (
    <AuthContext.Provider value={{ user, ready, login, register, logout, isAdmin }}>
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
