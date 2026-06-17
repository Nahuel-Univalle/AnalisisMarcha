"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  Eye,
  EyeOff,
  HeartPulse,
  Loader2,
  Lock,
  Mail,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { validateEmailFormat } from "@/lib/validations/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, ready, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [touched, setTouched] = useState({ email: false, password: false });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (ready && user) {
      router.replace("/dashboard");
    }
  }, [ready, user, router]);

  const validation = useMemo(() => {
    return {
      email: email ? validateEmailFormat(email) : "Ingresa tu correo electrónico.",
      password: password ? "" : "Ingresa tu contraseña.",
    };
  }, [email, password]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setTouched({ email: true, password: true });
    setError("");

    if (validation.email || validation.password) return;

    setLoading(true);

    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      setError("No pudimos iniciar sesión. Revisa tu correo y contraseña.");
    } finally {
      setLoading(false);
    }
  };

  const inputState = (field: "email" | "password") =>
    touched[field] && validation[field]
      ? "border-red-300 bg-red-50 focus:ring-red-300"
      : "border-slate-300 bg-white focus:ring-blue-400";

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-4 animate-fadeIn">
      <Card className="grid w-full max-w-6xl overflow-hidden border-slate-200 p-0 shadow-xl shadow-slate-300/70 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="p-6 sm:p-8 lg:p-12">
          <Link
            href="/"
            className="mb-10 flex items-center gap-2 font-black text-slate-900"
          >
            <Activity className="h-7 w-7 text-accent" />
            Análisis de Marcha IA
          </Link>

          <p className="text-sm font-bold uppercase tracking-wide text-secondary">
            Acceso seguro
          </p>
          <h1 className="mt-2 text-4xl font-black text-slate-900">
            Bienvenido nuevamente
          </h1>
          <p className="mt-3 max-w-lg text-slate-500">
            Ingresa para consultar tus análisis, informes y seguimiento personal.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label className="text-sm font-bold text-slate-700">
                Correo electrónico
              </label>
              <div className="relative mt-2">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input
                  className={`w-full rounded-2xl border py-3 pl-12 pr-4 text-slate-800 outline-none transition focus:border-accent focus:ring-2 focus:ring-offset-2 ${inputState("email")}`}
                  type="email"
                  value={email}
                  onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setError("");
                  }}
                  placeholder="usuario@email.com"
                />
              </div>
              {touched.email && validation.email && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {validation.email}
                </p>
              )}
            </div>

            <div>
              <label className="text-sm font-bold text-slate-700">
                Contraseña
              </label>
              <div className="relative mt-2">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input
                  className={`w-full appearance-none rounded-2xl border py-3 pl-12 pr-12 text-slate-800 outline-none transition focus:border-accent focus:ring-2 focus:ring-offset-2 ${inputState("password")}`}
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onBlur={() =>
                    setTouched((prev) => ({ ...prev, password: true }))
                  }
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setError("");
                  }}
                  placeholder="********"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-3 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-primary"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              {touched.password && validation.password && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {validation.password}
                </p>
              )}
            </div>

            {error && (
              <div className="animate-slideIn rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700 shadow-md">
                {error}
              </div>
            )}

            <Button
              className="w-full"
              size="lg"
              type="submit"
              disabled={loading}
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Iniciando sesión..." : "Iniciar sesión"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-slate-500">
            ¿No tienes cuenta?{" "}
            <Link
              href="/registro"
              className="font-bold text-accent transition hover:text-primary"
            >
              Crear cuenta
            </Link>
          </p>
        </section>

        <section className="relative hidden overflow-hidden bg-linear-to-br from-primary via-secondary to-accent p-12 text-white lg:block">
          <div className="absolute right-8 top-8 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 flex h-full flex-col justify-between">
            <div>
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-white/15 shadow-lg backdrop-blur">
                <HeartPulse className="h-9 w-9" />
              </div>
              <h2 className="mt-8 text-4xl font-black">
                Orientación visual para seguimiento de marcha
              </h2>
              <p className="mt-4 max-w-md leading-7 text-blue-50">
                Analiza videos, conserva informes y revisa señales funcionales
                con una experiencia segura y centrada en salud.
              </p>
            </div>

            <div className="rounded-2xl border border-white/20 bg-white/10 p-5 shadow-xl backdrop-blur">
              <p className="text-sm font-semibold text-blue-50">
                Resultado orientativo, no diagnóstico. Toda interpretación debe
                revisarse con un profesional de salud.
              </p>
            </div>
          </div>
        </section>
      </Card>
    </main>
  );
}
