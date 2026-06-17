type Props = {
  steps: string[];
  current: number;
};

export function ProgressSteps({ steps, current }: Props) {
  return (
    <div className="grid gap-3 md:grid-cols-6">
      {steps.map((step, index) => {
        const active = index <= current;

        return (
          <div
            key={step}
            className={`rounded-2xl border p-3 text-center text-xs font-semibold ${
              active
                ? "border-cyan-300 bg-cyan-50 text-cyan-800"
                : "border-slate-200 bg-white text-slate-400"
            }`}
          >
            {step}
          </div>
        );
      })}
    </div>
  );
}

