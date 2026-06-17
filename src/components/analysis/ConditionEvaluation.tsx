import { ConditionEvaluation as ConditionEvaluationType } from "@/types";
import { Card } from "@/components/ui/Card";

export function ConditionEvaluation({
  condition,
}: {
  condition: ConditionEvaluationType;
}) {
  return (
    <Card className="border-cyan-100 bg-linear-to-br from-white to-cyan-50">
      <h3 className="text-lg font-bold text-slate-950">
        {condition.condition}
      </h3>
      <p className="mt-1 text-sm font-semibold text-cyan-700">
        {condition.status}
      </p>
      <p className="mt-3 text-sm leading-6 text-slate-600">
        {condition.description}
      </p>
    </Card>
  );
}

