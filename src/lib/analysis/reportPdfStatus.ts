export type ReportPdfAvailability = {
  status: "available" | "not_generated" | "unavailable";
  message: string;
};

export const HISTORICAL_PDF_UNAVAILABLE_MESSAGE =
  "El archivo histórico de este informe no está disponible. El registro se conserva; no se han reconstruido ni sustituido sus resultados.";

export const PDF_NOT_GENERATED_MESSAGE =
  "El análisis original está disponible, pero todavía no hay un PDF validado para descargar.";
