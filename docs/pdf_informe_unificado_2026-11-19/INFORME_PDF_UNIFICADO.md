# PDF del informe unificado con el informe en pantalla (19-nov-2026)

## 1. Causa de la diferencia
Eran dos plantillas independientes. La pantalla (`MedicalReport.tsx`) se construye con `resultPresentation.ts`
sobre el análisis; el botón «Descargar PDF» ya no capturaba esa pantalla: pedía al servidor `renderCanonicalPdf`
(`canonicalPdf.ts`), que dibujaba líneas de texto con otro contenido: `analysisId`, `${code}: ` de cada advertencia
(VISTA_NO_VERIFICADA), «Mediciones auxiliares guardadas» (valores del procesador legado), el texto `summary` del
análisis (de ahí «patrón «Patrón compatible…»») y la confianza repetida.

## 2. Corrección
- `src/lib/analysis/reportModel.ts` (nuevo): ÚNICA fuente de datos; función pura que reutiliza las mismas funciones
  de presentación; no recalcula probabilidades.
- `src/components/report/MedicalReport.tsx`: lee ese modelo; marcado y estilos sin cambios.
- `src/lib/analysis/reportPdf.ts` (nuevo): PDF A4 vectorial (texto seleccionable) con la plantilla del informe:
  membrete, distintivo, 7 secciones numeradas, barras de las 4 clases, advertencias, observaciones, tabla de
  parámetros, interpretación, recomendaciones y advertencia final; tokens HEX de `globals.css` y proporciones
  de pantalla (1 px = 0,75 pt); márgenes 56/48/56 px; secciones cortas no se parten entre páginas; numeración
  «n / m» solo si hay más de una página.
- `assets/pdf-fonts/*.ttf` + `scripts/build-pdf-fonts.py`: Manrope (400/600/700) e IBM Plex Mono (400/500), las MISMAS
  fuentes que carga la interfaz (conversión de formato woff2→ttf, sin cambios de diseño de glifos).
- `canonicalPdf.ts`: `renderCanonicalPdf` usa el modelo + `reportPdf`. `canonicalDocument` (validación e hash) NO cambió.
- `pdfPresentation.ts`: nueva caché `canonical-v6-report`. Los PDF ya generados no se borran ni sobrescriben; la
  lectura de la caché antigua verificada `canonical-v4` se mantiene. `canonical-v5-presentation` (texto plano de hoy)
  ya no se sirve: esos informes se regeneran con el diseño nuevo.
- `docs/FRONTEND_RULES.md`: nota de mantenimiento. Sin cambios: V5-CR, modelo, datos, BD, API, otras pantallas.

## 3. Resultados
Imágenes en `imagenes/`: `comparacion_pantalla_vs_pdf.png`, `pdf_DESPUES_pagina1/2.png`, `pdf_ANTES_paginas.png`,
`variante_{normal,parkinson,esclerosis,riesgo,noconcluyente}.png`. PDF en `pdfs/`.
- PDF descargado con el botón real «Descargar PDF» en Chrome: A4 (595,3 × 841,9 pt), 2 páginas, fuentes Manrope/Plex Mono incrustadas.
- Texto de la pantalla vs PDF: toda línea visible de la pantalla está en el PDF (única diferencia: «(clase indicada por el modelo)», texto oculto para lectores de pantalla).
- Ausentes en el PDF: id del análisis, VISTA_NO_VERIFICADA/CAMARA_MOVIL, nombre del checkpoint, «Mediciones auxiliares», «patrón «», «Fecha del registro». Sin líneas duplicadas.
- Porcentajes 83/1/11/6 y confianza 83 % idénticos a las probabilidades del registro canónico (redondeo solo visual).
- Variantes con datos reales: normal, Parkinson, esclerosis múltiple, riesgo de caída (con aviso de clase y observaciones) y no concluyente (1 página, sin clasificación ni confianza).

## 4. Pruebas
| | Resultado |
|---|---|
| tsc | 0 errores |
| ESLint | 0 errores (3 avisos en scripts de prueba) |
| next build | OK (aviso de trazado de archivos ya existente) |
| Presentación (`test-v5cr-presentation`) | pasa |
| HTTP completo (login, carga, V5-CR, BD, historial, informe, PDF, administración, acceso) | 21/21 |
| Historial/PDF aislado (404 explícito de históricos, propietario, caché antigua byte a byte, PDF nuevo) | 22/22 |
| Descarga cliente | 6/6 |
| Flujo UI en Chrome con botón real | pasa (descarga del PDF nuevo) |
No se probó en Edge/Firefox ni en visor de PDF distinto de PyMuPDF/Chrome. La pantalla del informe no cambió de aspecto (misma plantilla).

## 5. Datos científicos
No se modificó ningún dato: el PDF solo presenta el registro canónico. V5-CR, checkpoint, escalador, características y etiquetas: sin cambios
(26 artefactos coinciden con el manifiesto). Base habitual: los 79 informes y 169 análisis históricos siguen allí; hay 2 informes y 4 análisis
nuevos creados por usted en pruebas manuales de hoy (no por estas pruebas, que usan la base técnica del puerto 55432).
