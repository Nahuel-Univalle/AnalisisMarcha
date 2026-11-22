# Informe técnico — Mejora experimental del modelo de marcha (V5)

Fecha: 2026-11-19. Proyecto: `C:\Users\fnahu\Desktop\GITMarcha\AnalisisMarcha`. **V4 no se modificó** (hashes de los artefactos originales en `resultados/fase1_hashes_originales.json`; la app sigue usando `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`). No hay commits. Todo el código nuevo está en `codigo/` y se ejecuta sobre `pose_cache` (sin reextraer pose, sin tocar videos).

## 1. Resumen

Se implementó un pipeline V5 aislado que corrige los defectos de preprocesamiento de la auditoría y se entrenó con la **misma arquitectura** y el **mismo protocolo** que V4 (mismas particiones por sujeto, semillas 42–46, 5 folds, época por validación interna, escalador y temperatura ajustados solo con entrenamiento).

| | V4 base (M1) | V4 BN (activo) | **V5-P** |
|---|---:|---:|---:|
| Exactitud OOF | 0,834 | 0,851 | **0,880** |
| F1 macro OOF | 0,725 | 0,744 | **0,800** |
| F1 normal / parkinson / EM / riesgo | 0,953 / 0,846 / 0,739 / 0,363 | 0,963 / 0,881 / 0,756 / 0,378 | 0,977 / 0,931 / 0,730 / **0,562** |
| Sensibilidad riesgo | 0,345 | 0,364 | 0,636 |

- **V5-P supera a V4 base** con incertidumbre por sujeto (F1 macro +0,075; IC95 [0,016; 0,136]).
- **Frente al V4 BN activo la diferencia de F1 macro no es concluyente** (+0,056; IC95 [−0,006; 0,114]).
- Esclerosis múltiple no mejora; la calibración cruda empeora; la validación externa es de 20 videos de calidad dudosa (empate con V4 BN).
- **Recomendación: conservar V4 BN como modelo activo; V5-P queda como candidato prometedor pendiente de validación externa.** Ver `RECOMENDACION_FINAL.md`.

## 2. Fase 1 — Línea base y reproducción (V4, sin cambios)

`codigo/fase1_linea_base.py` → `resultados/fase1_linea_base_v4.json`, `fase1_hashes_originales.json`.
- Checkpoint activo SHA-256 `7b4ac547…53400d` (candidato BN) y base `d7323250…213048`; ambos recalculados.
- Dataset: 117 videos, 67 grupos de sujeto; por clase 58/26/22/11 videos y 30/7/21/9 grupos; **27 grupos provisionales** (20 EM, 7 riesgo), 40 confirmados; 36 características; 53 NaN en `X_feat`.
- Métricas reproducidas desde `oof_probabilities.npz`: M1 base F1 macro 0,7252, exactitud 0,8342; candidato BN 0,7442 / 0,8513, **idénticas a los informes**; además el `oof_predictions.csv` del Paso 12 coincide con el npz en las 5 semillas.
- Protocolo: `step12_training/train_protocol_v2.py` (StratifiedGroupKFold por sujeto; escalador y BN solo con entrenamiento del fold: `train_fixed`, líneas 82–119).

**Defectos que requerían modificación vs. solo evaluación**

| Hallazgo | ¿Modificación? | Acción en V5 |
|---|---|---|
| A1 espejo | sí | `mirror_seq` niega x en posiciones y velocidades |
| A2 escala dependiente de la vista | sí | escala = longitud del torso |
| A3 nueve características absolutas | sí | referenciadas a cadera/hombro; ángulo del brazo |
| A4 relación de aspecto | sí | coordenadas isotrópicas con el aspecto del video |
| A5 aumentación incoherente | sí | ruido en posiciones y velocidades recalculadas; sin escala/recorte |
| A6 regularidad con dos definiciones | sí | una sola definición (NaN si no hay picos) |
| A8 fps visual por cuadros con pose | sí | rejilla uniforme de 15 fps |
| B3 duración de ventana por clase | sí | ventana fija de 2,6 s |
| B1, B4–B6, C4, C5 (fuente↔clase, pocos sujetos) | no (requieren más datos) | no corregibles con código |
| B2, B8–B10, C1, C7 (sondas, atajos) | evaluación | Fases 4 y 7 |

## 3. Fase 2 — Correcciones y decisiones documentadas

Fórmulas y significado físico de las 36 características: `FORMULAS_CARACTERISTICAS_V5.md`.

**A. Espejo.** V4 solo negaba posiciones x (`deep_common.py:422`; los canales `*_vx` terminan en `_vx`, no en `_x`). Prueba: reflejar los landmarks y reprocesar da una secuencia idéntica a `mirror_seq` (error 1,8·10⁻¹⁵); en V4 el error en canales vx es **0,24**.

**B. Escala.** Alternativas comparadas con las 117 ventanas (`fase2_escala.json`): estabilidad intra-ventana (CV) y dispersión entre vistas de «escala / altura corporal».

| Escala | CV intra-ventana | Dispersión entre vistas (máx/mín) |
|---|---:|---:|
| Mediana de (ancho hombros, ancho caderas, torso) — **la de las características V4** | 0,411 | **3,52** (lateral 0,076; frontal 0,236) |
| Media de torso, hombros y caderas | 0,104 | 1,62 |
| Máx. (torso, anchos) — la de la secuencia V4 | 0,045 | 1,26 (en estos videos coincide siempre con el torso) |
| **Torso (elegida, pre-registrada)** | 0,045 | 1,26 |
| Torso + muslo | 0,036 | 1,15 |

Se eligió el torso (simple, independiente de las piernas que se quieren medir). Torso + muslo es un poco más estable, pero acopla la escala a la amplitud de zancada (la señal clínica). La escala de las características V4 era claramente dependiente de la vista (hallazgo A2 confirmado). **No se convierte a metros.**

**C. Características.** Las nueve señaladas (rangos verticales de tobillo/rodilla, balanceo y rangos de brazo, asimetrías) usaban coordenadas absolutas. Demostración con esqueleto sintético: con **brazos inmóviles** `left_arm_range` de V4 pasa de 15,9 a 66,1 solo por aumentar la velocidad de traslación; en V5 el balanceo angular es 0,000 en ambos casos y 0,68 rad con ±20° reales (esperado 0,60–0,70).

**D. Aspecto.** La misma escena en 16:9, 4:3, 1:1 y 9:16 produce entradas V5 idénticas (≤ 4·10⁻¹⁶); en V4 las características cambian hasta 15× en términos relativos y la secuencia hasta 0,75.

**E. Consistencia temporal.** La duración de la ventana V4 por sí sola predice la clase con F1 macro 0,43 (regresión logística) / 0,39 (bosque) frente a 0,25 del azar (`fase2_ventana.json`): hay una señal de duración (normales: mediana 4,0 s, mínimo 2,77 s; Parkinson/riesgo: 5,03 s). Además V4 reescala el tiempo a 96 puntos, de modo que las velocidades dependen de la duración (en la prueba sintética, secuencia de 2,7 s vs 20 s con el mismo movimiento: diferencia 0,42). Alternativa V5: ventana **fija de 2,6 s** (40 muestras a 15 fps; todo video del dataset tiene ≥ 2,77 s), velocidades por paso de 1/15 s, ventanas deslizantes (paso 0,4 s) **dentro del mismo tramo analizado por V4**, evaluación por video con 5 ventanas equiespaciadas. Costo: menos ciclos de marcha por ventana (≈2,5).

## 4. Fase 3 — Pruebas del preprocesamiento (antes de entrenar)

`codigo/fase3_pruebas_unitarias.py` → `resultados/fase3_pruebas.json`: **21 PASS, 0 FAIL, 7 demostraciones de defectos V4** (+ la prueba de correspondencia entrenamiento↔inferencia con el dataset construido: bit a bit, error 0).
Incluye: espejo doble = original; espejo = landmarks reflejados (secuencia y 36 características); velocidad = diferencia de posiciones (también tras aumentación); 633 ventanas reales sin valores inválidos; invariancia a traslación, zoom y aspecto; ventanas cortas rechazadas; independencia de la duración del clip; respuesta sintética a cadencia, balanceo y zancada; invariancia al paneo de cámara de las variables relativas.
Incidencia: un umbral de la prueba de zancada (0,1) estaba mal calculado (el esperado analítico es ≈0,09–0,10, medido 0,093); se corrigió a 0,05 con la derivación explícita **antes** de entrenar y consta en el código. Un error en la permutación L/R de las características de V5-S se detectó al lanzarlo (excepción), se corrigió y se relanzó antes de obtener resultados.
Limitación de las pruebas: son sintéticas y sobre 117 videos; no demuestran invariancia a rotación 3D ni a oclusiones.

## 5. Fase 4 — Dependencia del movimiento (modelos congelados)

`codigo/fase4_dependencia_movimiento.py` → `fase4_robustez_{v4,v5P,v5S}.json`, `robustez_v4_v5_tabla.csv`, figuras 5–7. Se usan los **25 checkpoints de fold** de V4 base (`models_cv/M1_principal`) y los 25 de V5; cada prueba se evalúa sobre los sujetos de prueba de cada fold. La reproducción de las predicciones OOF guardadas fue **100 %** en V4 y en V5. Cambios de F1 macro respecto a la entrada intacta (IC95 por sujeto entre corchetes):

| Prueba | V4 base | V5-P | Tipo |
|---|---:|---:|---|
| Rama de características neutralizada (solo secuencia) | −0,134 | −0,079 | ablación sin reentrenar (fuera de distribución) |
| Rama de secuencia neutralizada (solo características) | −0,528 | −0,635 | ídem |
| Permutar grupo «desplazamiento global» | −0,065 | −0,157 | permutación |
| Permutar grupo «brazos» | −0,083 | −0,035 | permutación |
| Permutar grupo «tronco/postura» | −0,051 | −0,034 | permutación |
| Permutar grupo «piernas relativas» | +0,014 | −0,017 | permutación |
| Permutar «proxies de vista» (anchos) | −0,001 | −0,012 | permutación |
| Filtro pasa-bajos (velocidades recalculadas) | −0,056 | −0,305 | física plausible |
| Tiempo invertido (velocidades recalculadas) | −0,009 | −0,043 | coherente, poco natural |
| Fases aleatorias por canal | −0,346 | −0,651 | **no física** (informativa) |
| Bloques temporales barajados | −0,002 | −0,026 | **no física** (informativa) |
| Espejo físico | −0,007 | +0,010 | — |

Lectura (con cautela):
- **V4 usa muy poca información de orden temporal**: barajar bloques o invertir el tiempo casi no altera sus resultados (−0,002/−0,009), mientras que destruir la coordinación entre canales sí (−0,346). Su secuencia aporta sobre todo amplitudes y posturas globales. El balanceo de brazos (la característica con mayor defecto) tiene mucha importancia en V4 (−0,083) pese a medir desplazamiento global.
- **V5 es más sensible a la dinámica fina** (filtro pasa-bajos −0,305 vs −0,056; fases −0,651; tiempo invertido −0,043): usa velocidades físicas y la información de coordinación entre articulaciones. Esto es coherente con una mayor dependencia del movimiento, **pero no prueba que sea movimiento clínico** (la dinámica también puede venir de jitter o estilo de grabación).
- V5 depende más del grupo de desplazamiento global (−0,157), que contiene características sensibles al movimiento de cámara (ver paneo abajo) — vigilar.
- Todas las pruebas de ablación son fuera de distribución y no demuestran causalidad; las dos pruebas «no físicas» no se consideran evidencia concluyente.

### Variaciones de grabación (landmarks perturbados y reprocesados con el pipeline completo)

| Prueba | V4 base | V5-P | V5-S |
|---|---:|---:|---:|
| Aspecto ×0,75 | **−0,096** [−0,141; −0,058] | 0,000* | 0,000* |
| Aspecto ×1,333 | +0,009 | 0,000* | 0,000* |
| Zoom ×1,3 | 0,000 | 0,000 | 0,000 |
| Paneo de cámara 0,05/s | −0,032 [−0,062; −0,002] | −0,017 [−0,030; −0,007] | −0,011 |
| Jitter σ=0,005 / 0,01 | −0,008 / −0,025 | −0,030 / −0,039 | −0,011 / −0,027 |
| Pérdida del 20 % de cuadros | +0,011 | −0,011 | −0,012 |

\*La invariancia de V5 al aspecto es **por construcción** (se le entrega el aspecto real); no es una medida empírica independiente. El jitter y la pérdida de cuadros no mejoran en V5 (son similares o ligeramente peores; los IC incluyen cero).

**Cuánto codifican las características propiedades de la grabación** (`fase4b_sesgo_caracteristicas.json`, Spearman con rangos promediados): características con |ρ| > 0,65 respecto a la relación de aspecto en los 117 videos: **V4 19** (reproduce el valor de la auditoría) → **V5 8**; dentro del grupo EM+riesgo (n = 33), |ρ| > 0,5: 2 → 0; sonda lineal de orientación vertical vs horizontal en EM+riesgo: AUC **0,944 → 0,719**; sonda de fps (30 vs ≥ 40) en normal+Parkinson: 0,555 → 0,627 (peor, n=84). Con n pequeño solo son indicadores.

## 6. Fase 5 — Dataset V5

`codigo/construir_dataset_v5.py` → `fase5_dataset_v5.json`. Mismos 117 videos, mismos grupos y orden que V4 (verificado por aserción); los videos originales no se modificaron; los 20 videos descartados **no** se usaron. 633 ventanas de 2,6 s (1–7 por video; normal 3,9, Parkinson 6,9, EM 6,8, riesgo 7,0 de media); 4 ventanas rechazadas por pose insuficiente; fracción interpolada media 3 %. 139 de 633 ventanas tienen algún NaN (se imputa con la mediana del TRAIN). Etiquetas: las de V4 (27 grupos provisionales); no se inventaron identidades clínicas. Por muestrear una ventana por video y época, las clases con más ventanas disponibles no pesan más.

## 7. Fase 6 — Entrenamiento

Misma arquitectura `GaitTemporalModel` (conv1d 24/32/32 + MLP 24/16 + cabeza 32; 18 088 parámetros salvo el número de características), Adam (1e-3, wd 2e-4), 240 épocas máx., lote 16, suavizado de etiquetas 0,05, pesos de clase, época por validación interna anidada (3 folds), temperatura por fold. Diferencias declaradas: entradas V5, ventana muestreada por época, aumentación coherente (espejo físico, ruido σ=0,01 con velocidades recalculadas), evaluación con 5 ventanas por video. **Sin búsqueda de hiperparámetros.** Se ejecutaron solo dos variantes definidas antes de ver resultados: **V5-P (principal, 36 características)** y **V5-S (sensibilidad, 33: sin anchos de hombros/caderas ni step_frequency_hz)**. 25 folds por variante (≈ 60 min en CPU, 1 hilo por proceso), completados; modelos finales con los 117 videos en `checkpoints/` (no usar para estimar exactitud). Tiempo y recursos: 2 procesos en paralelo, sin GPU.
Qué no se hizo: recalibración BatchNorm de V5 (no pre-registrada), reentrenar V4, validación clínica.

## 8. Fase 7 — Comparación V4 vs V5 (validación interna)

Mismos 117 videos, grupos y particiones externas. Incertidumbre: bootstrap por grupo de sujeto (2 000 remuestreos; estadístico = media de las 5 semillas; **las semillas no se tratan como independientes**). Archivos: `comparacion_v4_v5.json/csv`, `calibracion_v4_v5.json`, figuras 1–4.

**Mejoras confirmadas (IC95 por sujeto excluye 0, validación interna, vs V4 base)**
- F1 macro +0,075 [0,016; 0,136] (p_bootstrap 0,018).
- F1 parkinson +0,085 [0,021; 0,212]; F1 riesgo de caída +0,199 [0,063; 0,330]; sensibilidad de riesgo +0,291 [0,164; 0,429].
- Voto mayoritario por video: 107/117 vs 98/117 (solo V5 acierta 10, solo V4 1; McNemar exacto p = 0,012).

**Resultados no concluyentes**
- Frente al **V4 BN activo**: F1 macro +0,056 [−0,006; 0,114]; exactitud +0,029 [−0,015; 0,075]; F1 riesgo +0,183 [0,027; 0,317] (única clase cuyo IC excluye 0); Parkinson +0,051 [−0,007; 0,150]. McNemar vs V4 BN: 10 vs 1 (p = 0,012, a nivel de voto mayoritario, pero el voto no incorpora la agrupación por sujeto).
- Exactitud vs V4 base +0,046 [0,000; 0,093]; F1 normal +0,024 [−0,002; 0,065].
- V5-S (sensibilidad): F1 macro 0,792, +0,067 [−0,001; 0,134] vs V4 base; no concluyente. Quitar los proxies de vista no mejora ni empeora de forma apreciable.

**Empeoramientos / sin mejora**
- Esclerosis múltiple: F1 0,730 (−0,009 vs base; −0,025 vs BN), sensibilidad 0,682 (−0,027); EM→riesgo 32/110 (V4: 28/110). La confusión EM↔riesgo persiste (riesgo→EM bajó de 23/55 a 18/55).
- **Calibración cruda peor**: ECE 0,147 vs 0,095 (V4 base) y 0,067 (V4 BN) (Δ +0,052 [0,011; 0,076] y +0,080 [0,034; 0,100]). Con temperatura por fold: ECE 0,082 (V5-P) vs 0,076 (V4 base); Brier 0,208 vs 0,269 y NLL 0,462 vs 0,543 (mejor). Brier crudo −0,042 [−0,102; 0,015] (n. s.).
- Jitter de landmarks: V5-P algo más sensible (−0,030/−0,039 vs −0,008/−0,025; n. s.).

**Por grupo de grabación (exactitud OOF)**: normal+Parkinson 0,931 → 0,964; EM+riesgo 0,588 → 0,667 (V4 BN: 0,943 / 0,618).

### Evaluación externa (22 videos no usados en el entrenamiento)
`fase7b_externos_v5.py` → `externos_v5.csv`. 2 videos externos documentados + 20 descartados del dataset por calidad (escaleras, cinta, cortes, vertical, cámara móvil); etiquetas por nombre de archivo, sin validación clínica. V5 devolvió «sin ventanas válidas» en 2 (RiesgoCaida13, 17: pose insuficiente), donde V4 emitió una clase; en los 20 restantes: V5-P 12/20, V5-S 13/20, V4 BN 12/20, V4 base 8/20 (n = 20; clases 1/4/6/9; no concluyente y no es exactitud). V4 base predijo EM en 15 de 20 y ninguna vez Parkinson.

## 9. Limitaciones propias del dataset (no resueltas por V5)
- Fuente de grabación aún colineal con la clase (1920×1080/lateral/trípode en normal+Parkinson; ≤848 px/vertical/cámara en mano en EM+riesgo): la mejora de V5 puede deberse en parte a atajos aún disponibles (estilo de cámara, postura global). La corrección geométrica reduce la codificación de aspecto/orientación (§5) pero no la elimina.
- 7 sujetos con Parkinson, 9 con riesgo; 27 grupos provisionales; 0/117 con validación clínica individual.
- Las sondas con solo metadatos técnicos obtenían F1 macro 0,78–0,86 (informe de evidencia); **no se repitieron con V5**.
- Un solo conjunto de 117 videos, 5 particiones de los mismos videos; sin conjunto externo limpio.
- Las decisiones de diseño de V5 (ventana de 2,6 s, escala torso, ruido 0,01) se tomaron tras leer las auditorías de V4 y con sondas sobre el mismo dataset, pero **sin usar resultados OOF de V5 para elegir**; no obstante, V5 se evaluó sobre los mismos 117 videos usados para auditar V4, por lo que la estimación puede ser optimista.

## 10. Respuestas a la Fase 8
1. **¿Se corrigieron los defectos técnicos?** Sí los de código (A1–A6, A8, B3) con pruebas numéricas aprobadas; no los de datos (B1, B4–B6).
2. **¿V5 representa mejor el movimiento corporal?** Hay indicios (menor dependencia del aspecto, mayor sensibilidad a la dinámica fina y a la coordinación), pero no evidencia concluyente de que sea movimiento clínico.
3. **¿Menos sensible a la grabación?** Aspecto/orientación: sí (parcialmente por construcción; AUC de orientación 0,944→0,719); paneo: algo menos (−0,017 vs −0,032); jitter y pérdida de cuadros: no mejora.
4. **¿Normal y Parkinson?** Parkinson mejora (F1 +0,085 vs V4 base; +0,051 n. s. vs BN); Normal +0,024 (n. s.); exactitud en normal+Parkinson 0,964.
5. **¿EM y riesgo?** Riesgo mejora claramente (F1 0,56; sensibilidad 0,64) pero sigue siendo la clase más débil y no validada; EM no mejora.
6. **¿Qué permanece por falta de datos?** Colinealidad fuente↔clase, pocos sujetos, etiquetas provisionales, ausencia de validación externa limpia.
7. **¿Reemplaza a V4?** Todavía no: la mejora sobre el V4 BN activo no es concluyente en F1 macro, la calibración cruda empeora y la validación externa empata. Conservar V4 BN como activo.
8. **¿Qué se puede afirmar sobre generalización clínica?** Nada. Todo es validación interna sobre 117 videos de 67 grupos; no hay evidencia clínica ni externa suficiente.

## 11. Reproducción
Desde la raíz del proyecto, con `.venv311` y `PYTHONDONTWRITEBYTECODE=1`: `fase1_linea_base.py`, `fase2_escala_y_ventana.py`, `fase3_pruebas_unitarias.py`, `construir_dataset_v5.py`, `fase6_entrenar_v5.py --variant P|S [--final]`, `fase4_dependencia_movimiento.py --version v4|v5P|v5S`, `fase4b_sesgo_caracteristicas.py`, `fase7_comparar_v4_v5.py`, `fase7c_calibracion.py`, `fase7d_figuras_robustez.py`, `fase7b_externos_v5.py`. Semillas fijas; entrenamiento en CPU con 1 hilo (determinista).
