"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Circle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { InlineAlert } from "@/components/ui/InlineAlert";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { cn } from "@/lib/utils";
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

  return (
    <AuthLayout
      panelTitle="Crea un perfil seguro para tus informes"
      panelText="Tus videos, análisis e informes quedan asociados solo a tu cuenta para mantener un seguimiento privado."
      panelNote="El sistema entrega orientación inicial y no reemplaza una valoración médica profesional."
    >
      <p className="reveal text-xs font-bold uppercase tracking-[0.09em] text-ink-subtle">Registro de usuario</p>
      <h1 className="reveal mt-2 text-[30px] font-bold leading-[38px] tracking-[-0.02em] text-ink">
        Crea tu cuenta
      </h1>
      <p className="reveal mt-2 text-[15px] leading-6 text-ink-muted">
        Guarda tus informes y revisa tu evolución de manera privada.
      </p>

      <form onSubmit={handleSubmit} className="reveal mt-8 grid gap-5 sm:grid-cols-2" noValidate>
        <div className="sm:col-span-2">
          <FormField
            label="Nombre completo"
            autoComplete="name"
            value={form.name}
            onBlur={() => validateField("name")}
            onChange={(event) => updateField("name", event.target.value)}
            error={errors.name}
          />
        </div>

        <FormField
          label="Edad"
          type="number"
          inputMode="numeric"
          value={form.age}
          onChange={(event) => updateField("age", event.target.value)}
          error={errors.age}
        />

        <FormField
          label="Correo electrónico"
          type="email"
          autoComplete="email"
          value={form.email}
          onBlur={() => validateField("email")}
          onChange={(event) => updateField("email", event.target.value)}
          error={errors.email}
        />

        <FormField
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onBlur={() => validateField("password")}
          onChange={(event) => updateField("password", event.target.value)}
          error={errors.password}
        />

        <FormField
          label="Confirmar contraseña"
          type="password"
          autoComplete="new-password"
          value={form.confirmPassword}
          onBlur={() => validateField("confirmPassword")}
          onChange={(event) =>
            updateField("confirmPassword", event.target.value)
          }
          error={errors.confirmPassword}
        />

        <div className="sm:col-span-2">
          <p className="text-[13px] font-semibold text-ink">La contraseña debe cumplir:</p>
          <ul className="mt-2 grid gap-x-4 gap-y-1.5 sm:grid-cols-2">
            {passwordRules.map((rule) => (
              <li
                key={rule.label}
                className={cn(
                  "flex items-center gap-2 text-[13px]",
                  rule.valid ? "font-medium text-success" : "text-ink-subtle"
                )}
              >
                {rule.valid ? (
                  <Check className="h-3.5 w-3.5" strokeWidth={3} aria-hidden />
                ) : (
                  <Circle className="h-3.5 w-3.5" aria-hidden />
                )}
                {rule.label}
                <span className="sr-only">{rule.valid ? "(cumplido)" : "(pendiente)"}</span>
              </li>
            ))}
          </ul>
        </div>

        <label
          className={cn(
            "flex cursor-pointer gap-3 rounded-lg border p-3.5 text-sm leading-5 sm:col-span-2",
            errors.accepted
              ? "border-danger bg-danger-bg text-danger"
              : "border-line bg-surface-subtle text-ink"
          )}
        >
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4 shrink-0 accent-primary"
            checked={form.accepted}
            aria-invalid={Boolean(errors.accepted)}
            onChange={(event) => updateField("accepted", event.target.checked)}
          />
          Entiendo que el sistema no reemplaza una valoración médica
          profesional.
        </label>

        {errors.accepted && (
          <p className="-mt-3 text-[13px] font-medium text-danger sm:col-span-2">
            {errors.accepted}
          </p>
        )}

        {generalError && (
          <div className="sm:col-span-2">
            <InlineAlert tone="error">{generalError}</InlineAlert>
          </div>
        )}

        <Button
          className="sm:col-span-2"
          size="lg"
          type="submit"
          loading={loading}
        >
          {loading ? "Creando cuenta..." : "Crear cuenta"}
        </Button>
      </form>

      <p className="mt-6 border-t border-line pt-6 text-sm text-ink-muted">
        ¿Ya tienes cuenta?{" "}
        <Link href="/login" className="font-semibold text-primary hover:text-primary-dark hover:underline">
          Iniciar sesión
        </Link>
      </p>
    </AuthLayout>
  );
}
