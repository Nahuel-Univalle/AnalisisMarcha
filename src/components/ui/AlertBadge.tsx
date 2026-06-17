import { SignalSeverity } from "@/types";

type Props = {
  level: SignalSeverity;
};

export function AlertBadge({ level }: Props) {
  const styles = {
    Bajo: "bg-emerald-100 text-emerald-700 border-emerald-200 shadow-emerald-100",
    Medio: "bg-amber-100 text-amber-700 border-amber-200 shadow-amber-100",
    Alto: "bg-red-100 text-red-700 border-red-200 shadow-red-100",
    Info: "bg-slate-100 text-slate-700 border-slate-200 shadow-slate-100",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-4 py-1 text-sm font-bold shadow-md ${styles[level]}`}
    >
      {level}
    </span>
  );
}

