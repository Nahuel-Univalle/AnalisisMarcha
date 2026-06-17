import { CheckCircle, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/Card";

const items = [
  "Formato compatible",
  "Duración suficiente",
  "Persona visible de cuerpo completo",
  "Buena iluminación",
  "Cámara estable",
  "Movimiento de caminata reconocible",
  "Calidad suficiente para detectar puntos corporales",
];

export function ValidationChecklist({ valid = true }: { valid?: boolean }) {
  return (
    <Card>
      <h2 className="mb-4 text-xl font-bold text-slate-950">
        Revisión del video
      </h2>

      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item, index) => {
          const warning = index === 3;

          return (
            <div
              key={item}
              className="flex items-start gap-3 rounded-2xl bg-slate-50 p-4"
            >
              {warning ? (
                <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-500" />
              ) : (
                <CheckCircle className="mt-0.5 h-5 w-5 text-green-600" />
              )}

              <div>
                <p className="font-semibold text-slate-900">{item}</p>
                <p className="text-sm text-slate-500">
                  {warning
                    ? "Aceptable, con ligera recomendación de mejora."
                    : "Condición cumplida correctamente."}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div
        className={`mt-5 rounded-2xl p-4 text-sm font-semibold ${
          valid ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
        }`}
      >
        {valid
          ? "Tu video está listo para el análisis."
          : "El video no cumple las condiciones mínimas. Por favor sube otro video."}
      </div>
    </Card>
  );
}

