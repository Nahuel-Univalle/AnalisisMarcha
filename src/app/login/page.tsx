"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Mail } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { validateEmailFormat } from "@/lib/validations/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, ready, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

  return (
    <AuthLayout
      panelTitle="Orientación visual para el seguimiento de tu marcha"
      panelText="Analiza videos, conserva informes y revisa señales funcionales con una experiencia segura y centrada en salud."
      panelNote="Resultado orientativo, no diagnóstico. Toda interpretación debe revisarse con un profesional de salud."
    >
      <p className="reveal text-xs font-bold uppercase tracking-[0.09em] text-ink-subtle">Acceso seguro</p>
      <h1 className="reveal mt-2 text-[30px] font-bold leading-[38px] tracking-[-0.02em] text-ink">
        Bienvenido nuevamente
      </h1>
      <p className="reveal mt-2 text-[15px] leading-6 text-ink-muted">
        Ingresa para consultar tus análisis, informes y seguimiento personal.
      </p>

      <form onSubmit={handleSubmit} className="reveal mt-8 space-y-5" noValidate>
        <FormField
          label="Correo electrónico"
          icon={Mail}
          type="email"
          autoComplete="email"
          value={email}
          onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
          onChange={(event) => {
            setEmail(event.target.value);
            setError("");
          }}
          placeholder="usuario@email.com"
          error={touched.email ? validation.email : undefined}
        />

        <FormField
          label="Contraseña"
          icon={Lock}
          type="password"
          autoComplete="current-password"
          value={password}
          onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
          onChange={(event) => {
            setPassword(event.target.value);
            setError("");
          }}
          error={touched.password ? validation.password : undefined}
        />

        {error && <InlineAlert tone="error">{error}</InlineAlert>}

        <Button className="w-full" size="lg" type="submit" loading={loading}>
          {loading ? "Iniciando sesión..." : "Iniciar sesión"}
        </Button>
      </form>

      <p className="mt-6 border-t border-line pt-6 text-sm text-ink-muted">
        ¿No tienes cuenta?{" "}
        <Link href="/registro" className="font-semibold text-primary hover:text-primary-dark hover:underline">
          Crear cuenta
        </Link>
      </p>
    </AuthLayout>
  );
}
