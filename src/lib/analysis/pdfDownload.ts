/** Reject error JSON/HTML even when a response incorrectly claims HTTP 200. */
export async function validatedPdfBlob(response: Response): Promise<Blob> {
  if (!response.ok || response.headers.get("content-type")?.split(";")[0].trim() !== "application/pdf") {
    let message = "No se pudo descargar un archivo PDF válido.";
    try {
      const payload = await response.json();
      if (typeof payload.message === "string") message = payload.message;
    } catch { /* Keep the explicit error; never download the error response. */ }
    throw new Error(message);
  }
  const blob = await response.blob();
  if (await blob.slice(0, 5).text() !== "%PDF-") throw new Error("La respuesta no contiene un archivo PDF válido.");
  return blob;
}

/**
 * PDF de un informe guardado, por las rutas canónicas existentes: GET; si el servidor indica que
 * todavía no se generó (PDF_NOT_GENERATED) se pide su generación canónica (POST) y se vuelve a leer.
 * Un informe histórico sin archivo (HISTORICAL_PDF_UNAVAILABLE) nunca se reconstruye: se lanza su mensaje.
 * Devuelve `generated: true` si fue necesario generarlo.
 */
export async function fetchReportPdfBlob(reportId: string): Promise<{ blob: Blob; generated: boolean }> {
  const url = `/api/me/reports/${encodeURIComponent(reportId)}/pdf`;
  let response = await fetch(url, { cache: "no-store" });
  let generated = false;
  if (response.status === 404) {
    const missing = await response.clone().json().catch(() => null);
    if (missing?.code !== "PDF_NOT_GENERATED") {
      throw new Error(missing?.message || "El archivo de este informe no está disponible.");
    }
    const creation = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!creation.ok) {
      const failure = await creation.json().catch(() => null);
      throw new Error(failure?.message || "No se pudo generar el PDF de este informe.");
    }
    generated = true;
    response = await fetch(url, { cache: "no-store" });
  }
  return { blob: await validatedPdfBlob(response), generated };
}
