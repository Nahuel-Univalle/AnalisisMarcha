# Plan de pruebas experimentales para el candidato V4

Fecha: 18 de noviembre de 2026. **Ninguna de estas pruebas se ha ejecutado.** Este plan es un diseño para revisión; no se iniciará nada sin autorización explícita del alcance.

## Principios comunes

1. **Congelar antes de mirar.** Escribir el procedimiento, las métricas y los criterios de decisión antes de ejecutar, y guardarlos con su SHA-256.
2. **Entradas coherentes entre ramas.** Toda perturbación se aplica sobre los *cuadros de landmarks* o sobre el *video* y las dos ramas se recalculan con las funciones de producción (`frames_to_sequence` y `build_feature_row`). No se modifican `X_seq` y `X_feat` por separado, porque eso genera pares que no corresponden a ningún video real.
3. **Modelo adecuado a la pregunta.**
   - *Candidato final congelado* (`gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`): sirve para medir **estabilidad** de la predicción. Como entrenó con los 117 videos, **no mide generalización**. Su exactitud sobre esos videos es resustitución.
   - *Checkpoints OOF* (`outputs/dataset_v4_4class/step12_training/models_cv/M1_principal/p{42..46}_f{1..5}.pt`, 25 modelos con su fold de test): sirven para medir **rendimiento sobre videos no vistos**. Para reproducir el procedimiento del candidato hay que recalibrar BN con el TRAIN de cada fold (solo estadísticas, sin etiquetas ni gradientes), como en `step18_bn/bn_recal.py`. La existencia de estos archivos en disco debe verificarse primero.
4. **Unidad de análisis: sujeto o grupo, no video.** Reportar métricas por videos, pero los intervalos y las pruebas se calculan remuestreando grupos (bootstrap por grupo). Las 585 predicciones OOF no son independientes.
5. **Sin entrenar los modelos principales.** Las pruebas A–D usan solo inferencia. La Prueba E entrena clasificadores auxiliares y requiere autorización específica.
6. **Línea base reproducible.** Antes de cualquier perturbación, reproducir la predicción original de cada video con el mismo código y comparar con las predicciones guardadas. Si no coinciden, detener y registrar.

## Orden recomendado

| Orden | Prueba | Inferencia/entrenamiento | Modelo | Por qué en este lugar |
|---|---|---|---|---|
| 0 | Verificaciones previas | Ninguna | — | Existen `pose_cache/` y los 25 checkpoints; las predicciones base se reproducen |
| 1 | **D** Coherencia del movimiento | Solo cálculo sobre pose guardada | — | No usa el modelo; define qué diferencias de movimiento existen y cuánto pesan duración, escala y aspecto |
| 2 | **A** Dependencia temporal | Solo inferencia | Checkpoints OOF + candidato | Barata, muy informativa sobre uso de dinámica |
| 3 | **C** Importancia de características | Solo inferencia | Checkpoints OOF | Requiere los resultados de A y D para interpretar bloques de variables |
| 4 | **B** Robustez visual | Reextracción de pose + inferencia | Candidato + checkpoints OOF | La más costosa; reutiliza lo aprendido en A, C y D |
| 5 | **E** Sondas dentro de fold (opcional) | Entrena clasificadores auxiliares | — | Cierra B7; no es necesaria para decidir sobre el modelo |

---

## Verificaciones previas (Orden 0)

- Comprobar que `pose_cache/*.pkl`, `models_cv/M1_principal/*.pt` y `partitions_outer_test_subjects.csv` existen, y registrar sus SHA-256.
- Reconstruir `dataset_v4_preview.npz` a partir de `pose_cache` con el procedimiento del Paso 5 («control_w503», que ya demostró reproducir el Paso 4) y verificar diferencia máxima 0 respecto a `X_seq` y `X_feat`.
- Reproducir las predicciones OOF guardadas de dos folds.

Criterio de parada: cualquier diferencia no explicada.

---

## Prueba D — Coherencia del movimiento sin confundirla con duración ni fuente

Orden recomendado: **primera**, porque no usa el modelo y orienta las demás.

**Hipótesis.** Existen diferencias medibles de movimiento entre clases que persisten cuando se controlan la duración de la ventana, el FPS, la relación de aspecto y la vista. H0: tras el control, las diferencias desaparecen o no son distinguibles de las debidas a esos factores.

**Datos.** `pose_cache` de los 117 videos (cuadros de landmarks a 15 fps ya extraídos), `samples_v4_preview.csv`, `manifest_v4_preview.csv`.

**Procedimiento.**
1. Definir medidas cinemáticas en unidades físicas aproximadas, **calculadas desde los landmarks**: velocidad de traslación de la cadera (longitudes de tronco por segundo, con escala igual a la mediana de la longitud del tronco, que no depende del ancho de hombros); amplitud de la oscilación del tobillo relativa a la cadera; asimetría izquierda/derecha de esa amplitud; frecuencia dominante de la señal del tobillo por análisis espectral; variabilidad entre ciclos.
2. Recalcularlas con **ventana igualada**: la misma duración para todos los videos (por ejemplo, el primer tramo común de 2.7–3.0 s, que cabe en el normal más corto) y con **coordenadas isotrópicas** (x·W/H, como la variante c3).
3. Descomponer: (a) las 14 características de movimiento de la red frente a las medidas del paso 1, calculando su correlación por pares; (b) cuánto de la brecha lab/no-lab (5–15×) cambia al sustituir la escala por la longitud del tronco.
4. Contrastes por estrato:
   - Normal vs Parkinson (84 videos, 37 grupos): comparar a nivel de sujeto (mediana por sujeto, no por video), controlando duración del clip y FPS (30 vs 50) con regresión o estratificación.
   - EM vs Riesgo (33 videos, 30 grupos): estratificar por vista (lateral, frontal, posterior) y orientación.
5. Pruebas: permutación por grupo (≥ 1000 permutaciones), tamaños de efecto con intervalos por bootstrap de grupos, y comprobación de sensibilidad dejando fuera cada grupo.

**Métricas.** Diferencia estandarizada entre clases, AUC univariado por sujeto, correlación parcial con la duración y el FPS, razón entre el efecto crudo y el efecto controlado.

**Resultado favorable.** Al menos las medidas de velocidad y de amplitud relativa separan Normal de Parkinson tras igualar ventana y escala, con intervalos que excluyen cero y sin depender del FPS.

**Resultado que indicaría un problema.** El efecto desaparece o cambia de signo al igualar la ventana, o el efecto se explica por la duración del clip; o la brecha lab/no-lab se reduce más de un orden de magnitud al corregir la escala (confirmaría que las 36 características reflejan la vista más que el movimiento).

**Limitaciones.**
- El par laboratorio/no laboratorio no puede aislarse con estos datos (B1). Esta prueba solo estima contrastes *dentro* de cada grupo.
- Con 7 sujetos con Parkinson los intervalos serán anchos.
- Las medidas no están calibradas en m/s.

**Ejecutable con los 117 videos.** Sí. **Modelo:** ninguno. **Entrenamiento/inferencia:** ninguno (cálculo sobre pose guardada).

---

## Prueba A — Dependencia temporal

**Hipótesis.** La predicción depende de la dinámica de los puntos y no solo de la postura media. H0: la predicción no cambia al destruir o alterar de forma coherente esa dinámica.

**Datos.** `pose_cache` de los 117 videos y sus folds de test (para checkpoints OOF).

**Procedimiento.** Aplicar sobre la **lista de cuadros** (antes de `frames_to_sequence` y `build_feature_row`), de modo que ambas ramas se recalculan de forma coherente:

| Control | Transformación | Qué prueba | Esperado si usa movimiento |
|---|---|---|---|
| A0 | Ninguna | Línea base | Reproduce lo guardado |
| A1 | Inversión temporal del tramo | Direccionalidad del ciclo (se invierte la asimetría de zancada, se conserva el espectro) | Cambio moderado |
| A2 | Postura estática: cada cuadro sustituido por la pose media de la ventana (con ruido de pose equivalente) | Que no basta la postura | Pérdida importante de la clase |
| A3 | Barajado de cuadros dentro de bloques cortos (p. ej. 3–5 cuadros) con **cuadros re-secuenciados y re-timestampeados** | Orden fino | Cambio |
| A4 | Reescalado temporal global coherente (×0.8, ×1.25) con timestamps reescalados | Dependencia de velocidad/cadencia absoluta | La predicción cambia con la velocidad (esperable) |
| A5 | **Ventana igualada** (misma duración para todos) | Efecto de la duración de la ventana | Si cae mucho, B3 es un atajo real |
| A6 | Desplazar el ancla ±0.5 s y ±1.0 s | Estabilidad respecto al tramo | Predicción estable |
| A7 | Para Normal y Parkinson en laboratorio: reemplazar el eje temporal de Parkinson por el de un normal con duración equivalente | Efecto de duración | Informativo |

Se evita expresamente poner a cero una rama (daría pares incoherentes). Si se quisiera hacer una ablación de ramas, requiere reentrenar y queda fuera del alcance de esta prueba.

**Métricas.** Cambio de clase predicha (%), ΔP(clase real), Δ macro-F1 y Δ recall por clase con checkpoints OOF; distancia entre vectores de probabilidades; intervalos por bootstrap de grupos.

**Resultado favorable.** A2 y A3 degradan claramente la predicción; A1 y A4 producen cambios interpretables; A5 y A6 no la colapsan.

**Resultado que indicaría un problema.** A2 (postura estática) apenas cambia la predicción (la red no usa dinámica); o A5 (ventana igualada) hace caer el F1 hacia el nivel de las sondas (la ventana era un atajo).

**Limitaciones.** A2 y A3 generan entradas fuera de distribución; el modelo puede responder arbitrariamente aunque sí use dinámica. A1 no distingue entre uso de la dirección y simple cambio de distribución. No certifica especificidad clínica.

**Ejecutable con los 117 videos.** Sí. **Modelo:** checkpoints OOF (rendimiento sobre videos no vistos) y candidato congelado (estabilidad). **Entrenamiento:** no. **Inferencia:** sí.

---

## Prueba C — Importancia de características

**Hipótesis.** Las predicciones no están dominadas por bloques de variables asociados a la grabación. H0: la caída de rendimiento al permutar bloques «de adquisición» es del mismo orden que la de bloques «cinemáticos».

**Datos.** Los 25 checkpoints OOF y sus folds de test (`X_feat` y `X_seq` de los videos no vistos).

**Procedimiento.**
1. Definir bloques de variables antes de ejecutar, según la clasificación de `CARACTERISTICAS_36.csv`: B-vel (velocidad y movimiento por articulación), B-rango (rangos absolutos, categoría 4), B-vista (anchos, inclinación), B-paso (conteo y cadencia), B-asimetría, B-postura. Los bloques evitan repartir la importancia entre variables colineales (cadencia y frecuencia son duplicados).
2. **Permutación por bloque de la rama de características**, **dentro de estrato** (permutar solo entre videos del mismo estrato de grabación) y, como contraste, sin estratificar. Permutar entre estratos crearía combinaciones de variables que no existen en los datos y exageraría la importancia.
3. 50 repeticiones por modelo y bloque.
4. Para la rama de secuencia: ocultación por grupos de articulaciones (piernas, brazos, tronco, cabeza) **sustituyendo cuadros de landmarks por la pose media relativa y recalculando ambas ramas** (así no se rompe la coherencia).
5. Opcional: valores de Shapley por bloques si hay presupuesto de cómputo.

**Métricas.** Δ macro-F1 y Δ log-loss respecto al modelo intacto, por bloque; ranking estable entre las 25 particiones; intervalos por bootstrap de grupos.

**Resultado favorable.** La importancia no se concentra en B-rango ni B-vista, y los bloques de movimiento relativo (asimetrías, oscilación) aportan por sí mismos.

**Resultado que indicaría un problema.** Los bloques que miden recorrido global o ángulo de vista (B-rango, B-vista) concentran la importancia, y/o permutar dentro de estrato elimina casi toda la caída (lo que sugeriría que la información es de estrato).

**Limitaciones.** Variables correlacionadas, entradas fuera de distribución al permutar, y las dos ramas no son separables en la fusión. La importancia mide dependencia del modelo, no causalidad ni valor clínico.

**Ejecutable con los 117 videos.** Sí. **Modelo:** checkpoints OOF (el candidato final vio todos los videos, la importancia sobre él sería de resustitución). **Entrenamiento:** no. **Inferencia:** sí.

---

## Prueba B — Robustez visual

**Hipótesis.** La predicción es estable cuando cambian factores de grabación que no alteran el movimiento. H0: cambios de brillo, contraste, resolución, compresión o FPS modifican la predicción más que lo esperable por ruido.

**Datos.** Los 117 videos originales (solo lectura); las copias degradadas se generan fuera del repositorio.

**Procedimiento.**
1. Rejilla predefinida, un factor a la vez, manteniendo contenido y tiempo reales:
   - Brillo (±30 %) y contraste (±30 %).
   - Resolución: reducir al 50 % y al 25 %. Para los videos de laboratorio, **reducir hasta 478×850 y 720×1280 con letterbox** para imitar los formatos del grupo no laboratorio y probar la hipótesis C4.
   - Compresión: H.264 con CRF 23, 30 y 36.
   - FPS: 30→24 y 30→15 mediante descarte de cuadros con timestamps reales.
   - Relación de aspecto: relleno (letterbox) a 9:16 y a 1:1 sin recortar el cuerpo, con la pose recalculada. Esto prueba directamente A4.
2. Para cada copia, extraer pose con `extract_normalized`, construir ambas ramas con el código de producción e inferir.
3. Medir también el efecto en la pose misma (error medio entre landmarks originales y degradados, en unidades de tronco).

**Métricas.** Tasa de cambio de clase, ΔP(clase real), Δ macro-F1 (con checkpoints OOF), desplazamiento en z-score de cada una de las 36 características y de la pose, por factor y nivel.

**Resultado favorable.** Cambios de clase bajos y proporcionales al desplazamiento de pose; el letterbox de aspecto cambia poco la predicción.

**Resultado que indicaría un problema.** Cambios de clase altos con degradaciones que apenas mueven la pose (señal de dependencia de factores no cinemáticos); o que el letterbox de aspecto desplace las predicciones hacia otra clase de forma sistemática (A4 con efecto real).

**Limitaciones.** Degradar videos de laboratorio no reproduce otras cámaras ni otros ángulos; para perspectiva se necesitan grabaciones sincronizadas multivista. Una alta estabilidad no demuestra invariancia a fuentes no representadas.

**Ejecutable con los 117 videos.** Sí. **Modelo:** candidato congelado para estabilidad; checkpoints OOF para Δ macro-F1. **Entrenamiento:** no. **Inferencia:** sí, con reextracción de pose (nuevas ejecuciones de MediaPipe).

---

## Prueba E (opcional) — Sondas con preprocesamiento dentro de fold

**Hipótesis.** El resultado de las sondas de metadatos no depende de la imputación y codificación globales (B7).

**Procedimiento.** Rehacer las sondas técnica y mixta y la referencia de 36 características con imputación, codificación y escalado dentro de un `Pipeline` ajustado solo con TRAIN, sobre las mismas 25 particiones. Guardar predicciones OOF individuales. Añadir una prueba de permutación de etiquetas por grupo.

**Métricas.** Macro-F1 OOF y su diferencia con las sondas archivadas.

**Resultado favorable/problema.** Una diferencia pequeña (< 0.02) confirma lo archivado; una diferencia grande invalida la comparación previa.

**Limitaciones.** No dice nada sobre lo que usa la red.

**Ejecutable con los 117 videos.** Sí. **Modelo:** clasificadores auxiliares, no la red. **Entrenamiento:** sí (auxiliar); requiere autorización.

---

## Lo que no puede resolver ningún conjunto de pruebas con los 117 videos

- La separación entre fuente y clase para {Normal, Parkinson} vs {EM, Riesgo} (B1).
- La generalización a fuentes nuevas.
- La validez clínica de las etiquetas.

Para esto se necesita recolectar videos con IDs de sujeto y de adquisición documentados, con cada clase en varias fuentes (incluida marcha normal en formato vertical/social y EM/Riesgo en laboratorio), y fijar de antemano el protocolo de evaluación por fuente retenida.
