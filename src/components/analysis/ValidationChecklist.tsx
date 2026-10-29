import { CSSProperties } from "react";
import { CircleCheck, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  "Formato compatible (MP4, MOV o AVI).",
  "Duración suficiente para observar varios pasos.",
  "Persona visible de cuerpo completo.",
  "Buena iluminación.",
  "Cámara estable, sin movimientos bruscos.",
  "Movimiento de caminata reconocible.",
  "Fondo despejado, sin obstrucciones.",
];

/**
 * Recomendaciones para que el usuario revise su propio video. No ejecuta
 * ninguna detección: ningún ítem lleva veredicto de aprobado/rechazado. El
 * único estado real es `valid` (en la página: hay un video cargado).
 */
export function ValidationChecklist({ valid = true }: { valid?: boolean }) {
  return (
    <div>
      <h2 className="text-lg font-bold leading-7 text-ink">
        Antes de continuar, verifica que tu video cumple con:
      </h2>
      <p className="mt-0.5 text-sm leading-6 text-ink-muted">
        Revisa cada punto tú mismo: un video que cumpla estas condiciones da un
        análisis más confiable.
      </p>

      <ol className="mt-5 divide-y divide-line border-y border-line">
        {items.map((item, index) => (
          <li
            key={item}
            className="reveal flex items-center gap-4 py-3"
            style={{ "--i": index } as CSSProperties}
          >
            <span className="w-6 shrink-0 font-mono text-xs text-ink-subtle">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="text-[15px] font-medium text-ink">{item}</span>
          </li>
        ))}
      </ol>

      <div
        role="status"
        className={cn(
          "mt-5 flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm font-medium",
          valid ? "border-success-line bg-success-bg text-success" : "border-warning-line bg-warning-bg text-warning"
        )}
      >
        {valid ? (
          <CircleCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        ) : (
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        )}
        {valid
          ? "Video cargado correctamente. Puedes continuar con el análisis."
          : "Todavía no has subido un video. Vuelve a la pantalla anterior para seleccionarlo."}
      </div>
    </div>
  );
}
