# Corrección del error de inferencia V5-CR en la aplicación habitual (19-nov-2026)

## 1. Qué muestra la evidencia real
Registro del servidor habitual (`LOG_DEV_HABITUAL_FALLO_ORIGINAL.log`, copia de `.next/dev/logs/next-development.log`), tiempos desde el arranque del servidor:

| t | Evento |
|---|---|
| 00:02:15 | `SPRINT4_DATASET_EVIDENCE` → el análisis de pose (`analyze_video.py`) **terminó bien** |
| 00:05:10.8 | `EXPERIMENTAL_GAIT_MODEL_FAILED "sin respuesta del script de inferencia"` |
| 00:05:36.9 | `DEEP_GAIT_MODEL_ERROR`, stderr con solo avisos de arranque de TensorFlow; **sin traceback de Python** |

El orden (fallo primero, cierre del proceso 26 s después) es el de un **límite de tiempo**: la ruta daba 150 s (`SPRINT4_TIMEOUT_MS`, constante compartida con el pipeline Sprint 4), mataba el lanzador `python.exe` del venv, resolvía `null` y, cuando el intérprete real por fin cerró sus tuberías, registraba el error de lectura. Los errores de carga de modelo, ruta, SHA, escalador, etiquetas o dependencias **no** son la causa: el proceso llegó a ejecutar MediaPipe (aparecen sus avisos) y los mismos artefactos cargan y predicen correctamente fuera del servidor.

**Causa próxima demostrada:** el predictor V5-CR no devolvió resultado en 150 s y la ruta lo presentó como «modelo no disponible». Es además un defecto de presentación (punto 5 del encargo): un tiempo agotado o una caída del proceso se mostraba como indisponibilidad del modelo.

**Lo que no pude demostrar:** por qué ese video concreto tardó más de 150 s. No lo reproduje: en este equipo el predictor V5-CR tarda 16–20 s en videos de 2–12 MB (igual que V4, 17 s), y 33 s en un video de 2 min a 1080p, tanto solo como a través de la ruta (43 s y 95 s totales). El video del intento fallido no se conservó (la ruta borra los temporales al fallar). No afirmo una causa de fondo para esa lentitud.

## 2. Qué comprobé (todo ejecutado)
Python/entorno: la ruta usa `.venv311` (no hay `PYTHON_*` en `.env`); torch 2.14, mediapipe 0.10.14, cv2 4.13. Checkpoint, escalador (33), configuración y etiquetas: las validaciones SHA-256 y de orden de columnas del propio predictor pasan en cada ejecución. Predictor de pruebas y predictor de la API son el mismo script (`15_predict_deep_video_v5cr.py`). Ventana 68×40, K=5 y temperatura: ejecutados sin error (`inference_done windows=5`).

## 3. Archivos modificados
- `src/app/api/analysis/video/route.ts`: tiempo límite propio del modelo (300 s, ajustable con `GAIT_MODEL_TIMEOUT_MS`), cierre del **árbol** de procesos en Windows (`taskkill /T /F`), registro de código de salida/señal/stderr, y causas distintas: `MODEL_TIMEOUT` (504), `MODEL_INFERENCE_ERROR` (500) y `EXPERIMENTAL_MODEL_UNAVAILABLE` (503, solo cuando de verdad falta script, Python o artefactos).
- `scripts/video_training/deep/15_predict_deep_video_v5cr.py`: tiempos por etapa en stderr (`V5CR_STAGE`), `faulthandler` para caídas nativas y la medición de movimiento de cámara acotada al tramo extraído (≤ 400 fotogramas); no afecta a la predicción, solo al aviso de cámara, y reduce de 25,8 s a 7,8 s en un video de 2 min.
- `scripts/test-v5cr-e2e.mjs`: modo de servidor configurable (`V5CR_E2E_MODE=start`), porque `next dev` no admite un segundo servidor mientras el habitual está activo.
- Respaldo previo con SHA-256 en `respaldo_previo/`. Pesos, escalador, etiquetas, preprocesamiento (`v5cr/`) y V4: sin tocar (26 artefactos coinciden con el manifiesto).

## 4. Pruebas
| Prueba | Resultado |
|---|---|
| `tsc --noEmit` | exit 0 |
| ESLint | 0 errores (1 aviso previo en un script de prueba) |
| `next build` | exit 0 |
| `test_v5cr_deployment.py --real-videos` | 24 PASS, 0 FAIL: 4 videos reales (normal, parkinson, esclerosis múltiple vertical, riesgo de caída), fixtures negativos |
| HTTP completo en servidor de producción aislado (BD técnica 55432, Cloudinary vacío) | 21/21: video → pose → inferencia V5-CR → PostgreSQL → historial → guardar informe → PDF → administración; versión guardada `gait_deep_v5exp_V5CR_7e9ed60965fe`; video sin persona sin clasificación inventada; video corrupto rechazado |
| Tiempo agotado provocado (`GAIT_MODEL_TIMEOUT_MS=3000`) | HTTP 504 `MODEL_TIMEOUT` con mensaje propio; 0 procesos huérfanos tras el cierre |
| Presentación del PDF | pasa |

## 5. Estado de V5-CR y de la base
Modelo realmente usado en las pruebas: `gait_deep_v5exp_V5CR_7e9ed60965fe`, SHA-256 `7e9ed609…c9dade`, probabilidades reales de 4 clases (no simuladas). No se activó V4 en ningún momento.
Base habitual: tablas sin cambios salvo **un registro `SystemLog` `LOGIN_USER` del 19-nov 19:12 (su propio inicio de sesión)**; por eso `verify-defense-preservation` marca «cambiada». El intento fallido no escribió análisis, video ni informe (el fallo ocurre antes del guardado).

## 6. Limitación y qué hacer
No pude probar el flujo **en la base habitual** ni con el video del fallo. Reintente el mismo video en la aplicación habitual (no hace falta reiniciar: la ruta y el script se recargan). Si vuelve a fallar, el mensaje ya dirá la causa (tiempo, error interno o indisponibilidad) y el servidor registrará, entre `DEEP_GAIT_MODEL_*`, el código de salida y los tiempos por etapa. Entregue las líneas `DEEP_GAIT_MODEL_*`/`EXPERIMENTAL_GAIT_MODEL_FAILED` de `.next/dev/logs/next-development.log` y el nombre, tamaño y duración del video.
