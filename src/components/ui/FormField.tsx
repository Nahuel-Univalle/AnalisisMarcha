"use client";

import { forwardRef, InputHTMLAttributes, useId, useState } from "react";
import { CircleAlert, Eye, EyeOff, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type FormFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id"> & {
  label: string;
  error?: string;
  icon?: LucideIcon;
  id?: string;
};

/**
 * Campo de formulario compartido: label asociado por htmlFor/id, ícono
 * opcional, estado de error y —para type="password"— botón de mostrar/ocultar.
 */
export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  function FormField({ label, error, icon: Icon, type = "text", className, id, ...props }, ref) {
    const generatedId = useId();
    const fieldId = id ?? generatedId;
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === "password";
    const resolvedType = isPassword ? (showPassword ? "text" : "password") : type;

    return (
      <div>
        <label htmlFor={fieldId} className="text-[13px] font-semibold text-ink">
          {label}
        </label>
        <div className="relative mt-1.5">
          {Icon && (
            <Icon
              aria-hidden
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle"
            />
          )}
          <input
            ref={ref}
            id={fieldId}
            type={resolvedType}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${fieldId}-error` : undefined}
            className={cn(
              "h-11 w-full appearance-none rounded-lg border bg-surface text-[15px] text-ink outline-none transition-[border-color,box-shadow] duration-150 placeholder:text-ink-subtle/70",
              "focus:shadow-[0_0_0_3px_rgba(11,149,134,0.12)]",
              Icon ? "pl-10" : "pl-3.5",
              isPassword ? "pr-12" : "pr-3.5",
              error
                ? "border-danger focus:border-danger"
                : "border-line-strong hover:border-ink-subtle focus:border-accent-blue",
              className
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              className="absolute right-1.5 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-ink-subtle transition-colors hover:bg-surface-subtle hover:text-ink"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
        </div>
        {error && (
          <p id={`${fieldId}-error`} className="mt-1.5 flex items-start gap-1.5 text-[13px] font-medium text-danger">
            <CircleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            {error}
          </p>
        )}
      </div>
    );
  }
);
