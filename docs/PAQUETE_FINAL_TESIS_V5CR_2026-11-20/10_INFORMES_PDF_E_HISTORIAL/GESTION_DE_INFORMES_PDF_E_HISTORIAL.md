# Gestión de informes PDF e historial (resumen técnico y académico)

> Fuentes: `docs/recuperacion_pdf_historicos_2026-11-19/`, `docs/pdf_informe_unificado_2026-11-19/`, `docs/historial_informes_botones_2026-11-19/`, código en `src/lib/analysis/`, `src/app/api/me/reports/`. Ejemplos de PDF en `ejemplos/` (generados con cuentas técnicas; la variante «riesgo» se renderizó a partir de un análisis real de pruebas manuales con el nombre sustituido por «Usuario de prueba»; los PDF no contienen identificadores internos).

## 1. Auditoría de los registros históricos
- Se auditaron **79 registros `MedicalReport`** de la base habitual (creados entre 2026-06-03 y 2026-11-03). Ninguno tiene `pdfUrl`, archivo canónico ni caché asociada (0/79).
- Causa comprobada: el generador anterior producía el PDF en el navegador y lo descargaba directamente (captura de pantalla); «Guardar en seguimiento» solo creaba el registro en la base de datos. El almacenamiento canónico de PDF en el servidor es posterior. **No existe archivo que servir.**
- Se buscó en el repositorio, descargas, documentos y carpetas de pruebas: **0 PDF originales recuperados**. Dos PDF de la carpeta de descargas son capturas rasterizadas sin identificador y no coinciden con ningún informe por propietario, clase y confianza.
- Evidencia de datos: cuatro archivos de resultados de pruebas antiguas contienen las cuatro probabilidades originales de **64 de los 79** análisis (4 + 20 + 20 + 20), verificadas contra identidad, propietario, versión, clase y confianza redondeada, sin conflictos. **Otros 15** informes tienen solo información parcial en la base (la clase aparece en 73 registros y la confianza redondeada en 73).
- Estas probabilidades **no equivalen** a un PDF original ni a todos los parámetros necesarios para reproducirlo (faltan bytes, fecha de emisión, características completas y estado de la interfaz).

| Categoría | Cantidad |
|---|---:|
| Registros históricos auditados | 79 |
| PDF originales recuperados | **0** |
| Registros con las cuatro probabilidades originales verificadas (datos recuperados, no PDF) | 64 |
| Registros con información parcial en la base | 15 |
| Informes reconstruidos o regenerados | **0** (no se reconstruyó ninguno ni se modificó ningún registro) |

## 2. Comportamiento actual de la aplicación
| Situación | Qué hace la aplicación |
|---|---|
| Informe histórico sin archivo (los 79) | El registro se conserva y se consulta en el historial; la fila «PDF» dice que el archivo histórico no está disponible; no hay botones de PDF; la ruta responde `404` con código `HISTORICAL_PDF_UNAVAILABLE`; nunca se genera un PDF falso |
| Informe nuevo con registro canónico y sin PDF generado | Muestra «Disponible; se genera al abrirlo o descargarlo». Al pulsar «Ver informe» o «Descargar PDF» el servidor genera **una vez** el PDF canónico (POST, validación del registro) y queda como «PDF disponible» |
| PDF canónico nuevo | Documento A4 con texto seleccionable, mismo modelo de datos que el informe en pantalla (`reportModel.ts`), almacenado con manifiesto (hash del origen y del PDF) en la caché `canonical-v6-report` |
| Caché antigua compatible | Se lee `canonical-v4` solo si el manifiesto, el hash de origen y el hash del PDF validan; los PDF de otros espacios (`canonical-v5-presentation`) no se sirven ni se borran |
| Error real del servidor al generar/descargar | Mensaje específico distinto de los casos anteriores; el cliente nunca guarda una respuesta de error como PDF (`validatedPdfBlob`) |
| Pruebas del cliente | Se rechaza JSON/HTML/vacío aunque llegue con HTTP 200 |

## 3. Controles de acceso
Solo el propietario descarga su informe (`requireUser` + consulta por `userId`): otra cuenta recibe `404`, sin sesión `401`; la ruta de descarga es de usuario (`/api/me/…`) y la lista de administración solo informa la disponibilidad. La disponibilidad se calcula sin modificar los registros.

## 4. Informe PDF final
Contenido (idéntico a la pantalla): membrete y distintivo «Clasificación experimental»; datos del análisis (usuario, fecha de emisión, confianza); resultado con la clase y las **cuatro probabilidades** en barras; advertencias del video; observaciones del movimiento; parámetros de marcha (ritmo estimado por picos y simetría del movimiento de las piernas) con su explicación; interpretación; recomendaciones; advertencia. No muestra identificadores internos, claves de advertencia ni mediciones auxiliares del procesador anterior. Los porcentajes son las probabilidades guardadas con redondeo solo visual (verificado por script). La caché y el nombre de versión no aparecen en el documento.

## 5. Evidencias
Capturas en `09_CAPTURAS_Y_EVIDENCIAS/` (informe visual 12, informe guardado con botones 13, páginas del PDF en `reutilizadas/`); pruebas en `08_PRUEBAS_DEL_SISTEMA/` (HTTP aislado 22/22, descarga cliente 6/6, navegador historial 17/17, descarga con botón real 8/8).

## 6. Limitaciones pendientes
- Los 79 PDF históricos no se pueden descargar (nunca se conservaron). Para 64 de ellos existen datos originales que **podrían** sustentar una *reconstrucción documental* claramente marcada, pero **no se ha hecho ni se hará sin autorización expresa**; propuesta técnica: `docs/recuperacion_pdf_historicos_2026-11-19/` (sección «Operaciones que requieren autorización»): documento rotulado «reconstrucción documental, no es el PDF original» con fecha de reconstrucción, fuente y hash del JSON de origen, almacenado aparte y sin actualizar `pdfUrl`; no viable para los 15 parciales.
- Desde la auditoría, el propietario ha creado 2 informes y 4 análisis nuevos en la base habitual (pruebas manuales); los 79 informes y 169 análisis históricos siguen presentes.
- «Ver informe» se comprobó en Chrome sin ventana (sin visor de PDF): se verifica la apertura de la pestaña y el contenido del archivo, no su pintado.
