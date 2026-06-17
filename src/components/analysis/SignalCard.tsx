import { Signal } from "@/types";
import { AlertBadge } from "@/components/ui/AlertBadge";
import { Card } from "@/components/ui/Card";

export function SignalCard({ signal }: { signal: Signal }) {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-bold text-slate-950">{signal.name}</h3>
        <AlertBadge level={signal.relevance} />
      </div>
      <p className="text-sm text-slate-600">{signal.description}</p>
    </Card>
  );
}

