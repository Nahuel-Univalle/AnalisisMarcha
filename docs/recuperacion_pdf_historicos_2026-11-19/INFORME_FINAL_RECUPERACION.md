# Informe final – gestión de informes PDF históricos (19 de noviembre de 2026)

Alcance: investigación y corrección segura continuadas desde el trabajo de Codex. No se entrenó, no se tocó la tesis, no se hicieron commits ni push, no se reconstruyó ni guardó ningún PDF histórico.

## 1. Estado que dejó Codex
- Auditoría, inventario y clasificación **completos** (JSON/CSV en esta carpeta) y correcciones de aplicación **completas y funcionales**, pero **sin informe final** y con dos defectos menores:
  - `tsc --noEmit` fallaba por un error de tipos en `scripts/test-historical-pdf-download.ts` (script de prueba; no afectaba a la aplicación).
  - Un import sin uso en `scripts/audit-historical-report-records.mjs` (aviso de ESLint).
- Se conservó íntegro todo lo demás. No se ejecutó `git reset`, `git clean` ni restauraciones.

## 2. Archivos
**Modificados por Codex (12, ya registrados en git como modificados):** `package.json`, `src/app/analisis/informe/page.tsx`, `src/app/api/admin/reports/route.ts`, `src/app/api/admin/summary/route.ts`, `src/app/api/analysis/video/route.ts`, `src/app/api/me/reports/[id]/pdf/route.ts`, `src/app/api/me/reports/route.ts`, `src/components/analysis/SavedReportsList.tsx`, `src/lib/analysis/canonicalPdf.ts`, `src/lib/analysis/resultPresentation.ts`, `src/lib/ml/modelMetrics.ts`, `src/types/index.ts`. Los cuatro primeros de esta lista relacionados con PDF/historial tienen respaldo en `respaldo_previo/`.
**Nuevos de Codex relacionados con PDF:** `src/lib/analysis/{pdfDownload,pdfPresentation,reportPdfStatus,reportPdfStorage}.ts` y los scripts `audit-historical-report-records.mjs`, `check-all-historical-pdf-endpoints.ts`, `inspect-historical-report-evidence.py`, `inventory-historical-report-files.py`, `match-historical-report-candidates.mjs`, `scan-historical-json-evidence.py`, `run-historical-pdf-check.mjs`, `test-historical-pdf-download.ts`, `test-historical-pdf-recovery.mjs`, `verify-historical-scientific-evidence.mjs`, entre otros. `src/components/report/MedicalReport.tsx` **no fue modificado** (git no muestra cambios).
**Modificados por mí (2, mínimos):**
1. `scripts/test-historical-pdf-download.ts`: la llamada a `assert.rejects` pasaba `undefined` como segundo argumento (error de tipos); ahora llama a dos formas válidas. El comportamiento de la prueba no cambia.
2. `scripts/audit-historical-report-records.mjs`: eliminado el import `readFile` sin uso.

## 3–5. Auditoría de los 79 informes (verificada con los archivos actuales)
| Concepto | Resultado |
|---|---|
| Registros `MedicalReport` | 79 |
| PDF originales realmente recuperados | **0** (ningún PDF con id de informe en `tmp`, `private-videos`, `outputs`, `data`; los dos PDF de Descargas son rasterizados sin id y no coinciden por propietario/clase/confianza) |
| Datos históricos originales verificados (cuatro probabilidades, clase, confianza, versión) | **64** — procedentes de 4 archivos de pruebas E2E antiguas (4 + 20 + 20 + 20 análisis); `verify-historical-scientific-evidence.mjs` reejecutado: 64 verificados, **0 conflictos** |
| Solo datos parciales en la base | **15** |
| Informes reconstruibles de forma fiel | **0 confirmados**: faltan bytes del PDF, fecha de emisión, características completas y estado de interfaz |

Encontrar las probabilidades **no** es haber recuperado el PDF.

## 6. Causa comprobada
Los informes anteriores se descargaban directamente al navegador (generador antiguo, cliente) y «Guardar en seguimiento» creaba solo el registro en base de datos; el almacenamiento canónico de PDF es posterior. No existe archivo en servidor que servir.

## 7. Correcciones vigentes
- La API distingue: `PDF_NOT_GENERATED` (análisis disponible, PDF aún no generado → se genera bajo demanda), `HISTORICAL_PDF_UNAVAILABLE` (histórico sin archivo → 404 explícito con mensaje claro, sin generar nada), PDF disponible (caché nueva `canonical-v5-presentation` o antigua `canonical-v4` solo si manifiesto, hash de origen y de PDF y propietario validan) y error de servidor.
- El cliente (`validatedPdfBlob`) rechaza JSON/HTML/vacíos aunque lleguen con HTTP 200 y nunca guarda un error como PDF.
- Historial y administración muestran disponibilidad real; el botón de descarga aparece solo para PDF validados; el registro histórico se conserva y consultable.
- Propiedad: el PDF solo se sirve al propietario (404 a otras cuentas; 401 sin sesión).

## 8. Pruebas ejecutadas por mí en esta sesión (todas reales)
| Prueba | Resultado |
|---|---|
| `tsc --noEmit` | **exit 0** (tras corregir el error de tipos) |
| ESLint | exit 0; 0 errores, 2 avisos en scripts de prueba (1 corregido) |
| `next build` | **exit 0** |
| Descarga cliente (`test-historical-pdf-download.ts`) | 6/6 |
| HTTP aislado (`test-historical-pdf-recovery.mjs`, esquema nuevo en contenedor 55432) | 22 PASS, 0 FAIL: no autenticado rechazado, otra cuenta rechazada, 404 explícito de histórico, sin reconstrucción silenciosa, fila intacta, distinción no-generado/no-disponible, PDF nuevo generado y descargado (idéntico en repetición), **caché antigua compatible descargada byte a byte**, lista de usuario/administración con disponibilidad real |
| 79 informes habituales, GET de solo lectura (`check-all-historical-pdf-endpoints.ts`) | 79 con 404 explícito `HISTORICAL_PDF_UNAVAILABLE`; 0 descargas falsas |
| Evidencia científica de los 64 | 0 conflictos |
Heredado de la revisión previa (no repetido ahora): flujo completo con V5-CR en base aislada 21/21, presentación del PDF 8/8.

## 9. V5-CR y V4
`DEFAULT_GAIT_MODEL = "v5cr"`, versión `gait_deep_v5exp_V5CR_7e9ed60965fe`. Los 26 artefactos de modelos (V4, V5-P, V5-C, V5-CR) coinciden con el manifiesto SHA-256 previo (`allModelArtifactsUnchanged: true`). V4 permanece como respaldo. No se atribuyó V5-CR a ningún resultado antiguo.

## 10. Integridad de la base habitual
`verify-defense-preservation.mjs`: `habitualDatabaseUnchanged: true`. Nueve tablas con las mismas huellas (18 usuarios, 169 análisis, 79 informes). Las escrituras de prueba solo ocurrieron en esquemas nuevos del contenedor 55432.

## 11. Limitaciones pendientes
- **No se pudo hacer prueba visual de navegador/móvil** (herramientas no disponibles). Pendiente en `docs/revision_defensa_2026-11-19/LISTA_MANUAL_DEFENSA.md`.
- Los 79 PDF históricos no son descargables (nunca se conservaron); la interfaz lo indica.
- `private-videos/` figura sin seguimiento en git (lo crea la ruta de análisis); no se ha de subir a git.
- Aviso de build sobre trazado de archivos del servicio PDF (ya conocido, no bloquea).

## 12. Operaciones que requieren su autorización
- **Reconstrucción documental de los 64 informes** (propuesta, no ejecutada): solo con las cuatro probabilidades, clase, confianza, versión y avisos originales; sin características, fecha ni parámetros. Debería generarse con marca visible «Reconstrucción documental, no es el PDF original», fecha de reconstrucción, fuente y hash del JSON de origen, almacenarse en un espacio distinto (`reconstructed/`) con manifiesto propio, y nunca marcarse como original ni actualizar `pdfUrl` sin su orden. Para los 15 restantes no es viable.
- Cualquier escritura en la base habitual, regeneración de PDF o commit.

## 13. Estado final para la defensa
Backend y gestión de PDF: verificados. Pendiente únicamente su ensayo manual en navegador (escritorio y móvil), incluido un caso nuevo con descarga de PDF V5-CR.
