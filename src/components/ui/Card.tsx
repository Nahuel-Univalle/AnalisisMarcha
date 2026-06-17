import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200 bg-white p-6 shadow-md shadow-slate-200/80 transition-all duration-200 hover:-translate-y-1 hover:shadow-xl",
        className
      )}
      {...props}
    />
  );
}

