import { ShieldAlert } from "lucide-react";
import { Card } from "./Card";

export function MedicalDisclaimer() {
  return (
    <Card className="animate-slideIn border-amber-200 bg-amber-50 shadow-lg shadow-amber-100/70">
      <div className="flex gap-3">
        <ShieldAlert className="mt-1 h-5 w-5 text-amber-700" />
        <div>
          <h3 className="font-bold text-amber-900">Advertencia médica</h3>
          <p className="mt-1 text-sm text-amber-800">
            Este sistema no reemplaza una valoración médica profesional. El
            resultado es una orientación inicial generada a partir del análisis
            visual de la marcha.
          </p>
        </div>
      </div>
    </Card>
  );
}
