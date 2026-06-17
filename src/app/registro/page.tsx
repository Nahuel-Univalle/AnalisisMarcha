"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  CheckCircle,
  Eye,
  EyeOff,
  Loader2,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  validateEmailFormat,
  validateFullName,
  validatePassword,
  validateRegisterInput,
} from "@/lib/validations/auth";

type RegisterErrors = Record<string, string>;

export default function RegisterPage() {
  const router = useRouter();
  const { register, ready, user } = useAuth();

  const [form, setForm] = useState({
    name: "",
    age: "",
    email: "",
    password: "",
    confirmPassword: "",
    accepted: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<RegisterErrors>({});
  const [generalError, setGeneralError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (ready && user) {
      router.replace("/dashboard");
    }
  }, [ready, user, router]);

  const passwordRules = useMemo(() => {
    return [
      { label: "Mínimo 8 caracteres", valid: form.password.length >= 8 },
      { label: "Una letra mayúscula", valid: /[A-ZÁÉÍÓÚÑ]/.test(form.password) },
      { label: "Una letra minúscula", valid: /[a-záéíóúñ]/.test(form.password) },
      { label: "Un número", valid: /[0-9]/.test(form.password) },
      {
        label: "Un carácter especial",
        valid: /[!@#$%^&*()_\-+=.[\]{};:'",.<>/?\\|`~]/.test(form.password),
      },
      {
        label: "Sin espacios",
        valid: form.password.length > 0 && !/\s/.test(form.password),
      },
    ];
  }, [form.password]);

  const updateField = (field: keyof typeof form, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
    setGeneralError("");
  };

  const validateField = (field: keyof typeof form) => {
    if (field === "name") {
      setErrors((prev) => ({ ...prev, name: validateFullName(form.name) }));
    }
    if (field === "email") {
      setErrors((prev) => ({ ...prev, email: validateEmailFormat(form.email) }));
    }
    if (field === "password") {
      setErrors((prev) => ({
        ...prev,
        password: validatePassword(form.password, form.name, form.email),
      }));
    }
    if (field === "confirmPassword") {
      setErrors((prev) => ({
        ...prev,
        confirmPassword:
          form.password !== form.confirmPassword
            ? "Las contraseñas no coinciden."
            : "",
      }));
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setGeneralError("");

    const validation = validateRegisterInput(form);

    if (!validation.valid) {
      setErrors(validation.errors);
      setGeneralError("Corrige los campos marcados antes de continuar.");
      return;
    }

    setLoading(true);

    try {
      await register({
        name: form.name,
        age: form.age,
        email: form.email,
        password: form.password,
        confirmPassword: form.confirmPassword,
        accepted: form.accepted,
      });
      router.push("/dashboard");
    } catch (error) {
      setGeneralError(
        error instanceof Error ? error.message : "Error al crear la cuenta."
      );
    } finally {
      setLoading(false);
    }
  };

  const inputClass = (field: string) =>
    `w-full rounded-2xl border px-4 py-3 outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 ${
      errors[field] ? "border-red-300 bg-red-50" : "border-slate-300 bg-white"
    }`;

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-4 animate-fadeIn">
      <Card className="grid w-full max-w-6xl overflow-hidden border-slate-200 p-0 shadow-xl shadow-slate-300/70 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="relative hidden overflow-hidden bg-linear-to-br from-primary via-secondary to-accent p-12 text-white lg:block">
          <div className="absolute left-8 top-8 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
          <div className="relative z-10 flex h-full flex-col justify-between">
            <div>
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-white/15 shadow-lg backdrop-blur">
                <ShieldCheck className="h-9 w-9" />
              </div>
              <h2 className="mt-8 text-4xl font-black">
                Crea un perfil seguro para tus informes
              </h2>
              <p className="mt-4 max-w-md leading-7 text-blue-50">
                Tus videos, análisis e informes quedan asociados solo a tu
                cuenta para mantener un seguimiento privado.
              </p>
            </div>

            <div className="rounded-2xl border border-white/20 bg-white/10 p-5 shadow-xl backdrop-blur">
              <p className="text-sm font-semibold text-blue-50">
                El sistema entrega orientación inicial y no reemplaza una
                valoración médica profesional.
              </p>
            </div>
          </div>
        </section>

        <section className="p-6 sm:p-8 lg:p-12">
          <Link
            href="/"
            className="mb-8 flex items-center gap-2 font-black text-slate-900"
          >
            <Activity className="h-7 w-7 text-accent" />
            Análisis de Marcha IA
          </Link>

          <p className="text-sm font-bold uppercase tracking-wide text-secondary">
            Registro de usuario
          </p>
          <h1 className="mt-2 text-4xl font-black text-slate-900">
            Crea tu cuenta
          </h1>
          <p className="mt-3 text-slate-500">
            Guarda tus informes y revisa tu evolución de manera privada.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 grid gap-5 md:grid-cols-2">
            <div className="md:col-span-2">
              <input
                className={inputClass("name")}
                placeholder="Nombre completo"
                value={form.name}
                onBlur={() => validateField("name")}
                onChange={(event) => updateField("name", event.target.value)}
              />
              {errors.name && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {errors.name}
                </p>
              )}
            </div>

            <div>
              <input
                className={inputClass("age")}
                placeholder="Edad"
                type="number"
                value={form.age}
                onChange={(event) => updateField("age", event.target.value)}
              />
              {errors.age && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {errors.age}
                </p>
              )}
            </div>

            <div>
              <input
                className={inputClass("email")}
                placeholder="Correo electrónico"
                type="email"
                value={form.email}
                onBlur={() => validateField("email")}
                onChange={(event) => updateField("email", event.target.value)}
              />
              {errors.email && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {errors.email}
                </p>
              )}
            </div>

            <div>
              <div className="relative">
                <input
                  className={`${inputClass("password")} appearance-none pr-12`}
                  placeholder="Contraseña"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onBlur={() => validateField("password")}
                  onChange={(event) => updateField("password", event.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-3 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-primary"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {errors.password}
                </p>
              )}
            </div>

            <div>
              <div className="relative">
                <input
                  className={`${inputClass("confirmPassword")} appearance-none pr-12`}
                  placeholder="Confirmar contraseña"
                  type={showConfirmPassword ? "text" : "password"}
                  value={form.confirmPassword}
                  onBlur={() => validateField("confirmPassword")}
                  onChange={(event) =>
                    updateField("confirmPassword", event.target.value)
                  }
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((value) => !value)}
                  className="absolute right-3 top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-primary"
                  aria-label={
                    showConfirmPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                  }
                >
                  {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-2 text-sm font-semibold text-red-600">
                  {errors.confirmPassword}
                </p>
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-inner md:col-span-2">
              <p className="mb-3 text-sm font-bold text-slate-700">
                La contraseña debe cumplir:
              </p>
              <div className="grid gap-2 md:grid-cols-2">
                {passwordRules.map((rule) => (
                  <div
                    key={rule.label}
                    className={`flex items-center gap-2 text-sm ${
                      rule.valid ? "text-emerald-700" : "text-slate-500"
                    }`}
                  >
                    {rule.valid ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    {rule.label}
                  </div>
                ))}
              </div>
            </div>

            <label
              className={`flex gap-3 rounded-2xl border p-4 text-sm shadow-sm md:col-span-2 ${
                errors.accepted
                  ? "border-red-200 bg-red-50 text-red-800"
                  : "border-amber-200 bg-amber-50 text-amber-900"
              }`}
            >
              <input
                type="checkbox"
                checked={form.accepted}
                onChange={(event) => updateField("accepted", event.target.checked)}
              />
              Entiendo que el sistema no reemplaza una valoración médica
              profesional.
            </label>

            {errors.accepted && (
              <p className="-mt-3 text-sm font-semibold text-red-600 md:col-span-2">
                {errors.accepted}
              </p>
            )}

            {generalError && (
              <div className="animate-slideIn rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700 shadow-md md:col-span-2">
                {generalError}
              </div>
            )}

            <Button className="md:col-span-2" size="lg" type="submit" disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Creando cuenta..." : "Crear cuenta"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-slate-500">
            ¿Ya tienes cuenta?{" "}
            <Link
              href="/login"
              className="font-bold text-accent transition hover:text-primary"
            >
              Iniciar sesión
            </Link>
          </p>
        </section>
      </Card>
    </main>
  );
}
