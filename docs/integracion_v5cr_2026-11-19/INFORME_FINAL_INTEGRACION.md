# Integración final de V5-CR — 19 de noviembre de 2026

## Resultado y alcance comprobado

V5-CR está configurado como modelo principal por defecto en `src/lib/ml/activeModel.ts`. El predictor activo es `15_predict_deep_video_v5cr.py`; el checkpoint es `gait_deep_v5exp_V5CR_7e9ed60965fe.pt`. El backend y la administración consultan la misma selección. No hay cambio automático a V4 si V5-CR falla. V4 se conserva y puede seleccionarse explícitamente con `GAIT_MODEL_VERSION=v4`.

Se ejecutó el flujo completo mediante HTTP en Next.js y PostgreSQL aislado: autenticación, carga de un video real existente de investigación, estimación de pose, inferencia V5-CR, persistencia, historial, informe, generación y descarga de PDF y resumen administrativo. También se ejecutó el predictor desde video real para cada una de las cuatro clases. Esto acredita integración técnica del prototipo; no acredita validación clínica ni nueva exactitud experimental.

La inspección visual de las pantallas de escritorio/móvil **no se pudo ejecutar**: el host del navegador indicó `The browser access host is unavailable`; el controlador de escritorio indicó `Computer Use native pipe is unavailable`, incluso después de los reintentos y reinicio del runtime. Se inspeccionaron visualmente las páginas del PDF renderizado. Las pruebas HTTP no se presentan como pruebas de interacción de navegador.

## 1. Estado que había dejado Claude

- `git status --short` inicial: únicamente tres carpetas no seguidas, las de mejora experimental, optimización e integración. Ningún archivo seguido estaba modificado.
- Las rutas de video y administración seguían usando V4 BN recalibrado; no había predictor V5-CR de producción.
- Claude había creado el manifiesto previo y cuatro respaldos: ruta de video, métricas, ruta de administración y predictor V4.
- Se comprobaron **26/26 hashes previos**, sin discrepancias, antes de editar. Los cuatro respaldos coincidían con sus originales. El manifiesto previo no se sobrescribió.

## 2. Archivos modificados y añadidos

Archivos preexistentes modificados:

| Archivo | Cambio |
|---|---|
| `src/app/api/analysis/video/route.ts` | Selección central del predictor y artefactos; disponibilidad del modelo seleccionado. Anula también las probabilidades y confianza legadas cuando la calidad es insuficiente. Conserva la persistencia de la versión obtenida del predictor. |
| `src/app/api/admin/summary/route.ts` | Versión, hash y métricas internas del modelo seleccionado; alcance de validación explícito. |
| `src/lib/ml/modelMetrics.ts` | Expone la selección activa; conserva la referencia histórica de V4 como respaldo. |
| `src/lib/analysis/resultPresentation.ts` | Correspondencia de nombres relativos de V5-CR, unidades angulares y descripción de ventana; conserva el comportamiento de registros V4. El ritmo por picos se identifica como estimación interna, sin validación de conteo clínico. |
| `package.json` | Predictor y pruebas principales apuntan a V5-CR; conserva la prueba antigua como `test:deep:legacy`. |

Archivos de funcionamiento añadidos:

- `src/lib/ml/activeModel.ts`: modelo por defecto y selección explícita de respaldo, compartida por inferencia y administración.
- `scripts/video_training/deep/15_predict_deep_video_v5cr.py`: carga validada, ventanas, inferencia, probabilidades, advertencias y errores controlados.
- `scripts/video_training/deep/v5cr/{__init__,v5_preproc,v5c_preproc,v5cr_preproc}.py`: preprocesamiento de despliegue. Solo se adaptó el arranque de importaciones; todas las funciones conservan su AST original.
- `models/gait_deep_v5cr/`: pesos copiados, configuración y escalador corregidos, etiquetas originales, manifiesto de despliegue y README.

Herramientas/evidencias añadidas:

- `prepare_v5cr_deployment.py`, `test_v5cr_deployment.py`, `scripts/test-v5cr-presentation.ts`, `scripts/test-v5cr-e2e.mjs`, `scripts/run-v5cr-check.mjs`, `scripts/audit-v5cr-integration.py`.
- Informes JSON, logs, PDF, páginas renderizadas y respaldos adicionales de `package.json` y `resultPresentation.ts` dentro de esta carpeta.
- Archivos temporales en `tmp/v5cr-e2e/` y copias de video de prueba con UUID en `private-videos/`. El archivo temporal habitual `tmp/debug_last_analysis.json` recibió trazas de las pruebas. Ninguno es una modificación del dataset original.

## 3. Errores encontrados y solución

### Escalador: 36 nombres para 33 estadísticas

El entrenamiento final carga `dataset_v5cr_bank.npz`, toma sus `feature_names` y construye el modelo con 33 entradas. El banco procede de `v5cr_preproc.window_inputs_C`, que utiliza `v5c_preproc.features_C` y su `KEEP_IDX`.

Las columnas eliminadas son **`hip_center_motion_mean`, `shoulder_center_motion_mean` y `horizontal_motion_mean`**, en sus posiciones originales. No se toman las primeras 33 columnas.

El defecto de metadatos nace en `deep_common.FeatureScaler.fit`: devuelve el escalador sin especificar `columns`, por lo que el constructor conserva los 36 nombres predeterminados heredados de V4. `to_json()` serializa esa lista, aunque el banco y las estadísticas tienen 33 valores. El cálculo de entrenamiento transforma las matrices por posición, por lo que ese campo descriptivo incorrecto no cambia los pesos ni las estadísticas aprendidas.

En la copia de despliegue solo se sustituyó `columns` por el orden de 33 nombres que coinciden entre banco, configuración y preprocesador. Los vectores `medians`, `means` y `stds` se conservaron exactamente. Además se reprodujeron las estadísticas a partir de las ventanas de evaluación del banco completo, sin entrenar el modelo, y coincidieron.

### Configuración identificada como V5-C

Solo se cambió `config.status` en la copia de despliegue para identificar V5-CR. La configuración original sigue intacta. La auditoría comprueba que `status` y `columns` son, respectivamente, los únicos campos cambiados de ambos JSON.

### Presentación heredada de V4

Los nombres de simetría y movimiento relativo cambiaron en V5-CR. Sin adaptación, la presentación omitía algunas mediciones y mantenía explicaciones de V4. Se adaptaron los descriptores de visualización por versión, conservando los números reales y los registros históricos. No se usan características eliminadas como entradas de V5-CR. Las métricas auxiliares del procesador visual existente siguen siendo observaciones complementarias y no entran en el clasificador.

### Confianza residual con pose insuficiente

El gate existente anulaba la clase principal, pero dejaba algunos campos legados de predicción. Se anulan también `predictionLabel`, `predictionConfidence` y `classProbabilities` cuando el análisis no es confiable. Un video negro de prueba produce un resultado no concluyente sin clasificación ni confianza.

### Incidencias de pruebas conservadas

- El primer arnés de prueba mezclaba una relación Prisma anidada con un identificador escalar incompatible. Se corrigió el arnés; log `PRUEBAS_E2E_INTENTO1.log`.
- El segundo intento intentó analizar como administrador. El sistema lo rechazó correctamente. Se separaron las cuentas técnicas USER y ADMIN; log `PRUEBAS_E2E_INTENTO2.log`.
- Una repetición concurrente de desarrollo y compilación dejó incompleto `.next/dev/types/validator.ts`; el build falló por `sExpected`. Se conservó el archivo generado como evidencia y se eliminó únicamente ese archivo de caché para regenerarlo. La compilación aislada posterior pasó. No se cambió TypeScript de la aplicación para ocultar el fallo.
- Bajo esa carga concurrente, una petición agotó el límite de inferencia y devolvió 503 sin usar otro modelo. Se limitaron a dos los hilos internos de CPU de PyTorch y se repitieron las pruebas secuencialmente. No se cambiaron pesos, entradas ni protocolo. Logs `BUILD_FALLO_CONCURRENCIA.log` y `PRUEBAS_E2E_TIMEOUT_CONCURRENCIA.log`.
- PowerShell mezclaba advertencias nativas y codificación UTF-16 en los logs. El ejecutor `run-v5cr-check.mjs` captura UTF-8 y el código de salida nativo en `EXIT_*.json`.

## 4. Protocolo de inferencia reproducido

1. Mismo extractor `24_normalized_reextract.extract_normalized`: lectura secuencial, rejilla a 15 FPS, dimensión máxima de 720 píxeles y límite original de 400 muestras.
2. Coordenadas isotrópicas (`x × ancho/alto`, `y`), visibilidad mínima 0,2 y cuadros con los cuatro puntos de tronco válidos.
3. Ancla en el primer cuadro con pose. Tramo efectivo de hasta 5,03 s. Banco de ventanas de **2,6 s**, paso **0,4 s**, conservando los vecinos para interpolación como en investigación.
4. `resample_grid_rel`: interpola cadera por separado y cada landmark relativo a la cadera; reconstruye coordenadas absolutas. Escala por mediana de longitud del torso. No utiliza la interpolación absoluta antigua.
5. Mismo requisito de al menos 20 cuadros válidos por ventana. Sin ventana aceptada, no hay predicción.
6. Selección sobre ventanas aceptadas: `unique(round(linspace(0, n-1, min(5,n))))`, idéntica a `TC.Bank`.
7. Secuencia **68 × 40** y **33** características en orden verificado. Imputación de valores no finitos con las medianas originales; estandarización con medias/desviaciones originales; salida float32.
8. Modelo en evaluación, sin gradientes. Media de logits float32 entre ventanas; conversión a float64 para dividir por **T = 0,6615**; softmax estable de las cuatro clases en el orden original.
9. Validación de dimensiones, orden, finitud y probabilidades. Artefacto ausente/alterado produce fallo controlado, sin predicción de respaldo.

La equivalencia con entrenamiento se verificó con los segmentos originales del manifiesto de investigación. Los videos subidos por usuarios se analizan desde el inicio disponible y no reciben recortes o etiquetas obtenidos del dataset.

## 5. Versión y hashes

Checkpoint principal:

`models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe.pt`

SHA-256 original y desplegado:

`7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade`

El manifiesto `MANIFIESTO_SHA256_POSTERIOR.json` contiene hashes antes/después de los archivos preexistentes, hashes de archivos nuevos y el hash del manifiesto previo. `AUDITORIA_INTEGRIDAD.json` verifica los artefactos originales, los respaldos, los únicos campos de metadatos cambiados, las copias exactas y las funciones de los preprocesadores.

Los 23 archivos del manifiesto previo ajenos a las tres rutas/métricas editadas conservan sus hashes, incluidos **todos los checkpoints y artefactos originales V4/V5-P/V5-S/V5-C/V5-CR** enumerados allí. Los respaldos de Claude siguen coincidiendo con los hashes previos.

## 6. Pruebas y evidencia

| Batería | Alcance | Evidencia |
|---|---|---|
| Python | 24 comprobaciones unitarias/integradas: artefactos, orden, estadísticas, imputación, dimensiones, rechazo de pesos alterados, ventanas, logits y probabilidades, geometría y videos reales/negativos | `PRUEBAS_PYTHON.json`, `PRUEBAS_PYTHON.log`, `EXIT_PYTHON.json` |
| TypeScript | 12 comprobaciones de selección, presentación de cantidades reales, cuatro probabilidades, pose insuficiente e identidad histórica | `PRUEBAS_TYPESCRIPT.json`, `PRUEBAS_TYPESCRIPT.log` |
| HTTP extremo a extremo | 20 comprobaciones, incluyendo preparativos y regresiones de permisos; video real hasta BD, historial, PDF y administración; entradas negativas | `PRUEBAS_E2E.json`, `PRUEBAS_E2E.log`, `EXIT_E2E.json` |
| Integridad | 37 comprobaciones de conservación y metadatos/funciones | `AUDITORIA_INTEGRIDAD.json`, `MANIFIESTO_SHA256_POSTERIOR.json` |
| Compilación y regresión estática | Next.js build, TypeScript y ESLint | `BUILD.log`, `TYPESCRIPT.log`, `ESLINT.log`, `EXIT_*.json` |

Las etiquetas `unit`, `integrated`, `e2e`, `regression` y `setup` de cada JSON detallan qué se ejecutó. Las pruebas de funciones sobre landmarks no se presentan como prueba de cámara real completa ni como E2E de navegador.

**Cierre de la ejecución:** las cuatro baterías indicadas finalizaron sin comprobaciones fallidas (24 + 12 + 20 + 37). Los ejecutores nativos de Python, E2E, presentación, TypeScript, ESLint y build terminaron con código **0**. `RESULTADO_FINAL.json` consolida estos resultados. Los fallos intermedios descritos arriba se conservaron y no se cuentan como aprobados.

### Equivalencia numérica

- **117/117 videos del banco**: misma selección de ventanas, mismas secuencias y mismas características que el banco guardado.
- Error absoluto máximo entre secuencias: **0**; características: **0**; logits contra `TC.Bank.video_logits`: **0**; probabilidades contra temperatura/softmax del evaluador: **0**, en la ejecución registrada.
- **633 ventanas reales**: traslación horizontal de cámara simulada en coordenadas, diferencia máxima aproximadamente **2,31 × 10^-15**; corrección de aspecto, aproximadamente **3,27 × 10^-15**. Son pruebas matemáticas sobre datos existentes, sin crear pacientes ni métricas clínicas.

### Inferencia real completa desde archivo

| Video existente | Clase de origen | Formato/cámara | Patrón obtenido |
|---|---|---|---|
| `001_NM_01` | normal | horizontal, trípode | normal |
| `001_PD_01_ML` | Parkinson | horizontal, trípode | parkinson |
| `Escleorosis10` | esclerosis múltiple | vertical; cámara sin anotación completa | esclerosis_multiple |
| `RiesgoCaida1` | riesgo de caída | horizontal, cámara que acompaña/paneo | riesgo_caida |

Las cuatro salidas completas están en `real_*.json`; las duraciones medidas de la ejecución final están en `PRUEBAS_PYTHON.json`. No son pacientes nuevos, un conjunto independiente ni una estimación adicional de exactitud.

El E2E HTTP utiliza `001_NM_01` mediante una copia subida con nombre técnico. `E2E_ANALYSIS.json` registra la versión V5-CR, cuatro probabilidades, confianza, mediciones y persistencia. `E2E_HISTORY.json` demuestra la consulta posterior; `E2E_ADMIN.json` demuestra versión y métricas administrativas; `E2E_POSE_INSUFICIENTE.json` registra el caso no concluyente.

### Entorno de pruebas y conservación de usuarios

PostgreSQL se ejecutó en el contenedor dedicado **`gait-v5cr-integration-20261119`**, base **`gait_v5cr_test`**, puerto local **55432**. Se creó desde la imagen local `postgres:16-alpine`; no se utilizó ni modificó la base habitual del puerto 5432. Las cuentas `@example.invalid` son técnicas; no son pacientes. La fila histórica V4 es una fixture explícita de compatibilidad, sin paciente ni inferencia simulada.

Se deshabilitó Cloudinary en el entorno de pruebas y se usó el almacenamiento local existente. Los registros canónicos y PDF de prueba están aislados en `tmp/v5cr-e2e/`. No se enviaron videos a servicios externos. El contenedor de pruebas se conserva, sin borrar su base. Los servidores de pruebas no forman parte del servicio habitual de la aplicación.

Al terminar se detuvo únicamente el contenedor de pruebas; sus datos se conservaron para reproducir la verificación. El PDF final descargado tiene dos páginas: se comprobaron visualmente ambas, incluidas la versión V5-CR, las cuatro probabilidades, la simetría relativa y la unidad `picos/min`, sin recortes ni superposiciones observados.

## 7. Estado de las funcionalidades

| Funcionalidad | Resultado comprobado |
|---|---|
| Validación y carga | HTTP: rechaza archivo ausente y video corrupto. |
| Pose y características V5-CR | Inferencia integrada desde cuatro videos reales; equivalencia completa con banco. |
| Predicción/probabilidades | Dimensiones correctas, temperatura original y cuatro probabilidades válidas. |
| Pose insuficiente | Clip negro de prueba: análisis no concluyente, sin predicción inventada. |
| Base de datos | Nuevos análisis guardan la versión real del predictor en sus parámetros. |
| Historial | Consulta HTTP de análisis guardado; fixture V4 conserva su versión. |
| PDF | Creación de informe, generación canónica y descarga HTTP; páginas renderizadas para revisión visual. |
| Administración | API devuelve V5-CR, exactitud 0,8598, F1 macro 0,7852 y alcance interno de validación. |
| Interfaz de escritorio/tablet/móvil | Adaptadores de datos comprobados; revisión visual/interacciones de navegador no ejecutadas por indisponibilidad de herramientas. |
| Cloudinary | Flujo de respaldo local probado; subida externa no ejecutada. |

El identificador `canonical-v4` conservado en el servicio PDF es la versión del formato/renderizador canónico, **no** la versión del clasificador. El informe incluye la versión V5-CR guardada por el análisis.

## 8. Métricas, limitaciones y pendientes

Se mantienen las métricas internas originales: exactitud **0,8598**, F1 macro **0,7852**, F1 Parkinson **0,9207**, F1 EM **0,6839**, F1 riesgo **0,5806**. No se recalcularon para sustituir los resultados experimentales. Las probabilidades expresan salida del modelo y no probabilidad clínica de enfermedad.

Pendientes reales:

1. Revisión manual de pantallas e interacciones en escritorio, tablet y móvil antes de la defensa; las herramientas de navegador/escritorio no estaban disponibles.
2. Validación externa y clínica: no existe y no se infiere de estas pruebas. Continúan la confusión EM/riesgo, pocos sujetos y asociación entre fuente y clase.
3. Cámara: se probaron transformaciones matemáticas y un video real con paneo. No se validaron de forma exhaustiva rotación, perspectiva, desenfoque, oclusión ni todas las condiciones de captura.
4. El ritmo mostrado por V5-CR procede de picos en una ventana corta; puede ser alto y no debe presentarse como conteo clínico validado. Las estadísticas originales usadas por el clasificador permanecen intactas.
5. El build conserva una advertencia de trazado de archivos asociada al servicio PDF preexistente. Se registra; no impide compilar. No se amplió esta integración para rediseñar el empaquetado de Next.js.
6. El entorno habitual con la base de usuarios no se usó para pruebas ni se dejó como despliegue productivo en ejecución. La configuración principal del código es V5-CR; el flujo se verificó en el entorno aislado descrito.

## 9. Reproducción y respaldo

Desde la raíz del proyecto, sin entrenar:

```powershell
node scripts/run-v5cr-check.mjs build
node scripts/run-v5cr-check.mjs python
docker start gait-v5cr-integration-20261119
node scripts/run-v5cr-check.mjs e2e
node scripts/run-v5cr-check.mjs presentation
node scripts/run-v5cr-check.mjs typescript
node scripts/run-v5cr-check.mjs lint
.venv311/Scripts/python.exe scripts/audit-v5cr-integration.py
```

Ejecutar build y E2E **secuencialmente**; no compartir generación de tipos con un servidor de desarrollo concurrente. El arnés E2E requiere el contenedor y puerto aislados descritos; no apunta a la base habitual.

Para usar V4 explícitamente en una sesión de PowerShell antes de iniciar la aplicación:

```powershell
$env:GAIT_MODEL_VERSION = 'v4'
npm run dev
```

Para volver al principal V5-CR, retirar esa variable o establecer `v5cr`. Tanto la ruta de inferencia como la administración obedecen la selección. V4 y sus pesos originales permanecen disponibles.

## 10. Cambios posteriores para la tesis

**No se modificó el documento Word.** Posteriormente deberán actualizarse:

- Identificación final, checkpoint y SHA-256 del prototipo: V5-CR.
- Diagrama de preprocesamiento: aspecto, escala de torso e interpolación relativa a cadera.
- Lista exacta de 33 características y eliminación de las tres magnitudes de traslación global.
- Ventanas de 2,6 s/40 muestras, selección de hasta cinco ventanas, promedio de logits y temperatura 0,6615.
- Corrección de metadatos del escalador, sin cambio de estadísticas ni pesos.
- Integración, trazabilidad por análisis, manejo de pose insuficiente y resultados de pruebas separadas por nivel.
- Métricas como validación interna sobre los mismos 117 videos; sin superioridad clínica demostrada y con las limitaciones reales de EM/riesgo, captura y generalización.

No se entrenó ningún modelo, no se alteraron etiquetas/sujetos/dataset, no se eliminaron checkpoints ni carpetas de investigación y no se hicieron commits ni push.
