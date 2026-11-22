# Estado final del software (verificado el 2026-11-20)

## 1. Identificación
| Concepto | Valor (fuente) |
|---|---|
| Aplicación | «Análisis de Marcha IA» (`package.json` nombre `analisis-marcha-ia`, versión `0.1.0`; el proyecto no usa versionado semántico propio) |
| Modelo principal configurado | **`gait_deep_v5exp_V5CR_7e9ed60965fe`** (`src/lib/ml/activeModel.ts`, `DEFAULT_GAIT_MODEL = "v5cr"`; no hay variable de entorno que lo cambie en `.env`) |
| SHA-256 del checkpoint | `7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade` (verificado; el predictor lo comprueba en cada inferencia) |
| Respaldo V4 | `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`, SHA-256 `7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d`, intacto; solo se usaría con `GAIT_MODEL_VERSION=v4` (retroceso explícito) |
| Pila | Next.js 16.2.6, React 19.2.4, Prisma 6.18 + PostgreSQL, jsPDF 4.2.1; Python 3.12.3 (entorno `.venv311`), PyTorch 2.14.0 (CPU), MediaPipe 0.10.14, NumPy 2.4.6 |
| Git | Último commit `ef41974` (2026-11-18, «ModeloDeepLearningV4»). **Los cambios de V5-CR y posteriores no están confirmados:** 17 archivos modificados y 43 elementos sin seguimiento (modelo `models/gait_deep_v5cr/`, `scripts/video_training/deep/v5cr/`, `src/lib/analysis/{reportModel,reportPdf,…}.ts`, carpetas `docs/…`) |

## 2. Funcionalidades posteriores a V4: implementadas, comprobadas y pendientes
Criterio: **Implementada** = existe en el código (archivo indicado); **Comprobada** = hay una prueba ejecutada con evidencia real (ver `08_PRUEBAS_DEL_SISTEMA/`); **Pendiente** = falta evidencia o prueba visual.
| # | Funcionalidad | Implementación (archivo) | Comprobación | Pendiente |
|---|---|---|---|---|
| 1 | V5-CR como modelo principal | `activeModel.ts`, `15_predict_deep_video_v5cr.py`, `models/gait_deep_v5cr/` | Python 24/24 (SHA, orden, escalador, 117/117 videos igual al evaluador); E2E HTTP 21/21 con versión V5-CR guardada | — |
| 2 | V4 conservado como respaldo | `models/gait_deep_v4exp_bn_candidate_v1/` | 26 artefactos sin cambios (verify-defense-preservation) | Retroceso `GAIT_MODEL_VERSION=v4` no se ejercitó con un video en esta serie |
| 3 | Cambios en el flujo de inferencia | `route.ts` usa el predictor activo; ventanas de 2,6 s; sin sustitución automática por V4 | E2E y Python | — |
| 4 | Validación de disponibilidad del modelo | `hasActiveGaitModel()`, SHA y coherencia config/escalador/etiquetas en el predictor | Python (rechazo de pesos alterados) | — |
| 5 | Errores del modelo diferenciados | `route.ts`: `MODEL_TIMEOUT` (504), `MODEL_INFERENCE_ERROR` (500), `EXPERIMENTAL_MODEL_UNAVAILABLE` (503); límite 300 s (`GAIT_MODEL_TIMEOUT_MS`); cierre del árbol de procesos | Tiempo agotado provocado con límite de 3 s: 504 correcto, sin procesos huérfanos | Caída nativa/salida inválida no se provocaron |
| 6 | Resultados no concluyentes | gate de pose en `route.ts` (`pose_detection_rate < 0,45`, etc.) | E2E: video sin persona → sin clase ni probabilidades | — |
| 7 | Reproductor independiente del análisis; recuperación ante `MEDIA_ERR_DECODE`; botón Reintentar | `VideoStage.tsx` (`StageVideo`), `AnalysisContext.tsx` | Navegador Chrome (CDP): 22/22 con 3 videos, 23/23 final; defecto reproducido antes (7/8) | Pruebas en otros navegadores |
| 8 | Informe PDF A4 con texto seleccionable y diseño unificado con la pantalla | `reportModel.ts` (fuente común), `MedicalReport.tsx`, `reportPdf.ts`, `assets/pdf-fonts/` | Descarga con botón real (Chrome) y contraste de texto/probabilidades por script; 5 variantes de clase | Revisión visual del PDF en visores externos y con Cloudinary |
| 9 | Fuente común de datos pantalla–PDF y caché de versión | `reportModel.ts`; renderer `canonical-v6-report` (`pdfPresentation.ts`) | E2E / HTTP aislado | — |
| 10 | Historial de análisis (Seguimiento) y de informes guardados con «Ver informe» / «Descargar PDF» | `SavedReportsList.tsx`, `HistoryTimeline.tsx`, `pdfDownload.ts` | Navegador 17/17 (clic real, registro sin PDF, filtro, propiedad) | «Ver informe» con visor de PDF real (Chrome sin ventana no lo tiene) |
| 11 | Gestión de los 79 informes históricos sin PDF original | `reportPdfStorage.ts`, `pdf/route.ts`, `reportPdfStatus.ts` | 79/79 devuelven 404 explícito (solo lectura); HTTP aislado 22/22 | — |
| 12 | Caché antigua compatible | `readCached` (`canonical-v4`) | HTTP aislado: descarga byte a byte | Solo se verificó con PDF técnicos de pruebas |
| 13 | Autenticación y propiedad | `requireUser`, `pdf/route.ts` | otra cuenta → 404, anónimo → 401 (informes); usuario común no accede al resumen administrativo (403) | Que el administrador no pueda crear análisis de paciente está en el código (`route.ts`) pero no tiene prueba específica |
| 14 | Panel de administración con estado del modelo | `api/admin/summary/route.ts`, `AdminDashboard.tsx` | HTTP (versión, exactitud 0,8598, F1 0,7852) y captura 20 | Probado con base técnica; no con datos reales |
| 15 | Aplicación sobre la base habitual | — | Solo lecturas; pruebas manuales del propietario (análisis V5-CR completo en el registro del servidor) | Sin pruebas automatizadas sobre la base habitual |
| 16 | Otros cambios hallados en el repositorio | `package.json` (scripts `test:deep`, `test:v5cr:*`, `deep:predict` apuntan a V5-CR; `test:deep:legacy` conserva el de V4), `resultPresentation.ts` (presentación de parámetros V5-CR: ritmo en picos/min, simetría relativa), `modelMetrics.ts`, `types/index.ts`, `informe/page.tsx` | tsc/ESLint/build | — |

## 3. Qué está demostrado, qué es experimental y qué sigue pendiente
- **Demostrado (reproducible):** el predictor desplegado reproduce exactamente al evaluador (117/117 videos, error 0); la integración y los flujos HTTP aislados pasan; las métricas internas de V5-CR (63/63 valores recalculados); las invariancias geométricas del preprocesamiento.
- **Experimental:** todo el rendimiento del modelo (validación interna sobre 117 videos, 67 grupos técnicos de sujeto, 27 provisionales); la clasificación es **orientativa y no diagnóstica**; la mejora global frente al V4 activo no es estadísticamente concluyente.
- **Pendiente:** validación externa/clínica; verificación visual completa (otros navegadores, móvil del resultado/informe, PDF en visores externos, entorno con Cloudinary); curvas de entrenamiento (no se guardaron); sonda de metadatos para V5-CR; commit de los cambios.

## 4. Limitaciones técnicas conocidas (hechos verificados)
- Tiempo de análisis: el predictor tarda unos 12–20 s para videos de pocos MB en el equipo de desarrollo (CPU) y 33 s para 2 min de 1080p; un intento del propietario superó el límite anterior de 150 s por una causa de fondo no determinada (el límite se elevó a 300 s y se separó el error).
- La API ejecuta Python por solicitud (un proceso por análisis); no hay cola de trabajos.
- La reproducción del resultado y el informe en pantalla viven en memoria del navegador: al recargar `/analisis/resultado` se pierde el resultado en curso (se conserva el historial en la base).
- El proyecto declara Python 3.11 en el nombre del entorno (`.venv311`), pero el intérprete es 3.12.3.
