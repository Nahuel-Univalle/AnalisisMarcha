# Informes guardados: botones «Ver informe» y «Descargar PDF» (19-nov-2026)

## Cambio
- `src/components/analysis/SavedReportsList.tsx`: cada registro con PDF disponible (o generable) muestra **Ver informe** y **Descargar PDF**
  junto a «Videos». «Ver informe» abre el PDF en pestaña nueva; «Descargar PDF» lo guarda. Se eliminó el bloque aparte «Descargar PDF guardado».
  Registro sin archivo: sin botones, texto «PDF no disponible» y el motivo en la fila «PDF» (el registro se conserva). Vista de administración sin cambios.
- `src/components/analysis/HistoryTimeline.tsx`: ranura `actions` por registro (nada más cambia; filtro por categorías y «Videos» intactos).
- `src/lib/analysis/pdfDownload.ts`: `fetchReportPdfBlob` — GET a `/api/me/reports/[id]/pdf`; si el servidor responde `PDF_NOT_GENERATED`
  pide la generación canónica (POST, el mismo generador, una sola vez y solo a petición del clic) y vuelve a leer; `HISTORICAL_PDF_UNAVAILABLE` nunca se reconstruye.
  Rutas, autenticación y propiedad: sin cambios. Respaldo previo en `respaldo_previo/`.
- Un informe guardado cuyo PDF aún no se generó dice «Disponible; se genera al abrirlo o descargarlo» y pasa a «PDF disponible» tras abrirlo.

## Pruebas (Chrome por CDP, servidor de producción aislado, BD técnica 55432)
17/17: flujo real (video → V5-CR → resultado → informe → guardar en seguimiento); 2 registros (uno con PDF, uno histórico sin archivo);
el registro con PDF muestra los 3 botones; el histórico, «PDF no disponible» y ningún botón de PDF; filtro por patrón presente;
**clic real** en «Ver informe» abre una pestaña nueva navegada al blob del PDF; «Descargar PDF» descarga `informe_analisis_marcha.pdf`
(A4, 2 páginas, diseño unificado, sin identificadores internos); tras abrir, el registro pasa a «PDF disponible»;
otra cuenta → 404, sin sesión → 401; histórico sin archivo → 404 JSON `HISTORICAL_PDF_UNAVAILABLE`, nada generado.
Además: tsc 0 errores · ESLint 0 errores · build OK · HTTP completo 21/21 · historial/caché 22/22 · descarga cliente 6/6.

## Límites
Chrome sin ventana no tiene visor de PDF: allí la pestaña recibe el archivo; se comprobó que se abre y navega al PDF, no su pintado en el visor.
Verifíquelo a mano (Chrome/Edge normal). No se probó en Firefox/Safari. No se modificó V5-CR, la base, resultados ni la tesis; sin commits.
