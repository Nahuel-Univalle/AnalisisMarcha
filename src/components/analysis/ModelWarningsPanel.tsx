import { InlineAlert } from "@/components/ui/InlineAlert";
import type { PresentedModelWarning } from "@/lib/analysis/resultPresentation";

type ModelWarningsPanelProps = {
  alerts: PresentedModelWarning[];
  notes: PresentedModelWarning[];
};

/**
 * Advertencias sobre las condiciones del video que pueden afectar la
 * clasificación experimental. Las de calidad van en tono de advertencia; las
 * informativas (p. ej. vista no verificada) en tono neutro.
 */
export function ModelWarningsPanel({ alerts, notes }: ModelWarningsPanelProps) {
  if (alerts.length === 0 && notes.length === 0) return null;

  return (
    <div className="grid gap-3">
      {alerts.length > 0 && (
        <InlineAlert tone="warning">
          <p className="font-semibold">Condiciones del video que aumentan la incertidumbre</p>
          <ul className="mt-2 space-y-1.5 font-normal">
            {alerts.map((warning) => (
              <li key={warning.code}>
                <span className="font-semibold">{warning.title}.</span> {warning.message}
              </li>
            ))}
          </ul>
        </InlineAlert>
      )}
      {notes.map((note) => (
        <InlineAlert key={note.code} tone="info">
          <span className="font-semibold">{note.title}.</span> <span className="font-normal">{note.message}</span>
        </InlineAlert>
      ))}
    </div>
  );
}
