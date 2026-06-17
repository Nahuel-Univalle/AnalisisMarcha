import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  const variants = {
    primary: "bg-primary text-white hover:bg-secondary",
    secondary: "bg-accent/10 text-primary hover:bg-accent/20",
    outline: "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50",
    danger: "bg-red-100 text-red-700 hover:bg-red-200",
  };

  const sizes = {
    sm: "px-4 py-2 text-sm",
    md: "px-5 py-3 text-sm",
    lg: "px-7 py-4 text-base",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50",
        "shadow-sm duration-200 hover:scale-[1.02] hover:shadow",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

