# Optimización final realista del modelo de marcha — informe verificable

Fecha: 2026-11-19. Proyecto: `C:\Users\fnahu\Desktop\GITMarcha\AnalisisMarcha`. No se modificó V4, V5-P (código, checkpoints y resultados siguen con el mismo hash), la aplicación, la tesis ni el Word; no hay commits. Todo lo nuevo está en esta carpeta (`codigo/`, `resultados/`, `figuras/`, `checkpoints/`).

> **Con los videos y etiquetas disponibles, no encontré una mejora adicional suficientemente respaldada más allá de V5-CR. Recomiendo conservar V5-CR como mejor candidato técnico actual del prototipo y detener el entrenamiento.** V5-CR **no** supera de forma demostrable en poder predictivo al V4 activo ni a V5-P; su ventaja es de integridad del preprocesamiento y robustez a la cámara. Todo es validación interna sobre los mismos 117 videos.

## 1. Qué problemas investigué y qué mostró la evidencia

Primero medí cada problema con modelos congelados (sin entrenar); solo se corrige lo demostrado.

| Problema | Evidencia | ¿Justifica un cambio? |
|---|---|---|
| A. Ruido en coordenadas | jitter σ=0,005/0,01: V5-P −0,030/−0,039 ΔF1 macro, IC95 por sujeto [−0,065; 0,010] y [−0,081; 0,006]; V4 −0,008/−0,025 | **No** (IC incluyen 0); V5-P ya entrena con ruido σ=0,01 |
| B. Pérdida de cuadros | 20 % de cuadros perdidos: V5-P −0,011 [−0,024; −0,0002] | **No** (efecto mínimo) |
| C. Confusión EM↔riesgo | V5-P: EM→riesgo 32/110, riesgo→EM 18/55; V4 BN 27/110 y 25/55 | **No**: es un límite de los datos (hallazgo B5 de la auditoría); ningún cambio de código se justifica sin datos |
| D. Calibración | V5-P es *subconfiado* (confianza 0,760 < exactitud 0,880); la temperatura por fold ya lo corrige (confianza 0,840; ECE calibrado 0,082 vs 0,076 de V4 base) | **No**: el mecanismo ya existe |
| E. Dependencia de la cámara / desplazamiento global | Con una cámara que sigue a la persona: V4 base −0,325 y V5-P **−0,313** ΔF1 macro (IC [−0,362; −0,258]); −0,12 con 50 %. `horizontal_motion_mean` mediana: 0,60 normal (trípode), 0,31 Parkinson (trípode), 0,037 EM, 0,011–0,095 riesgo (cámara en mano/acompaña) | **Sí** → experimento V5-C |
| F. Consistencia de ventanas | Exactitud por video: 5 ventanas 0,880, todas 0,877, voto 0,884 (sin diferencias); pero 370/633 ventanas cambian su secuencia ante una cámara que sigue, **todas** con landmarks enmascarados o cuadros interpolados; las 137 sin ellos, 0 | **Sí** → corrección V5-CR |

## 2. Experimentos realizados (pre-registrados en `PREREGISTRO_V5C.md`)

Solo se ejecutaron **dos** variantes nuevas, cada una con hipótesis y criterios fijados antes de ver sus resultados; mismo protocolo, arquitectura, semillas y particiones por sujeto que V5-P.

**V5-C (hipótesis E).** Se eliminan de V5-P las magnitudes que dependen de la traslación de la persona en la imagen (`hip_center_motion_mean`, `shoulder_center_motion_mean`, `horizontal_motion_mean`) y se redefinen sin ella `body_motion_mean/std`, `motion_smoothness` y un término de `gait_variability` → 33 características; secuencia idéntica. Coste declarado: se pierde la velocidad de avance en la imagen (solo interpretable con cámara fija).
**V5-CR (defecto F, adenda 1).** V5-C + interpolación de los landmarks enmascarados en coordenadas relativas a la cadera. El defecto estaba en mi propio V5: `resample_grid` interpolaba coordenadas absolutas y mantenía el valor en los extremos, filtrando la traslación a las coordenadas relativas (mediana 1,10 longitudes de torso en las ventanas afectadas; fracción afectada: normal 0,85, Parkinson 0,57, EM 0,29, riesgo 0,43). V4 interpolaba coordenadas ya relativas.

**Pruebas ejecutadas**
- Numéricas de V5-C (`fase8_pruebas_c.py`): 12 PASS, 0 FAIL (invariancia a cámara que sigue, zoom y aspecto; espejo; persona rígida; 633 ventanas reales sin NaN/inf; características no redefinidas idénticas a V5-P). Incidencia: el umbral de la prueba que demuestra que V5-P *no* es invariante (0,05) era arbitrario y se cambió a 1e-3 antes de entrenar.
- Corrección V5-CR (`fase8_prueba_cr.py`): **0 de 633 ventanas** cambian ante la cámara que sigue (máx. 7·10⁻¹²) y las 137 ventanas sin huecos son idénticas a V5-C (una difiere en 3,7·10⁻⁹, redondeo float32; mi tolerancia inicial 1e-9 era inferior a la precisión de float32 y se corrigió a 1e-6).
- Validación cruzada agrupada por sujeto (5 semillas × 5 folds) de V5-C y V5-CR, modelos finales y batería de robustez/dependencia con modelos congelados (reproducción de las predicciones OOF guardadas: 100 %).

## 3. Resultados (mismos 117 videos, grupos y particiones; IC95 por grupo de sujeto, 2 000 remuestreos)

| | V4 BN (activo) | V5-P | V5-C | **V5-CR** |
|---|---:|---:|---:|---:|
| Exactitud | 0,851 | 0,880 | 0,841 | 0,860 |
| F1 macro | 0,744 | **0,800** | 0,772 | 0,785 |
| F1 normal / parkinson / EM / riesgo | 0,963 / 0,881 / 0,756 / 0,378 | 0,977 / 0,931 / 0,730 / 0,562 | 0,939 / 0,881 / 0,687 / 0,580 | 0,956 / 0,921 / 0,684 / 0,581 |
| Sensibilidad normal / parkinson / EM / riesgo | 0,935 / 0,962 / 0,745 / 0,364 | 0,955 / 0,985 / 0,682 / 0,636 | 0,903 / 0,954 / 0,609 / 0,709 | 0,935 / 0,969 / 0,618 / 0,691 |
| ECE crudo / calibrado por fold | 0,067 / – | 0,147 / 0,082 | 0,129 / 0,074 | 0,131 / **0,064** |
| Brier | 0,245 | 0,231 | 0,269 | 0,231 |
| Exactitud normal+Parkinson / EM+riesgo | 0,943 / 0,618 | 0,964 / 0,667 | 0,919 / 0,642 | 0,945 / 0,642 |

Matrices de confusión (suma de 5 semillas; filas reales N/P/EM/R): V4 BN `[271,19,0,0],[1,125,0,4],[0,1,82,27],[1,9,25,20]` · V5-P `[277,12,1,0],[0,128,1,1],[0,3,75,32],[0,2,18,35]` · **V5-CR** `[271,13,3,3],[0,126,1,3],[6,4,68,32],[0,1,16,38]`. CSV completo: `resultados/METRICAS_FINALES.csv`; JSON: `comparacion_final.json`.

**Diferencias pareadas (IC95 por sujeto)**
| Comparación | F1 macro | Exactitud | Clases con IC que excluye 0 |
|---|---|---|---|
| V5-C − V5-P | −0,028 [−0,079; 0,015] | −0,039 [−0,074; −0,006] | normal −0,038 [−0,071; −0,014]; parkinson −0,050 [−0,112; −0,011] (empeoran) |
| V5-CR − V5-C | +0,014 [−0,032; 0,062] | +0,019 [−0,019; 0,056] | ninguna |
| **V5-CR − V5-P** | −0,015 [−0,052; 0,020] | −0,021 [−0,045; 0,003] | normal −0,021 [−0,042; −0,004] (empeora) |
| **V5-CR − V4 BN (activo)** | **+0,041 [−0,029; 0,102]** | +0,009 [−0,039; 0,053] | riesgo +0,203 [0,023; 0,356] (mejora); sensibilidad de riesgo +0,327 |
| V5-CR − V4 base | +0,060 [−0,007; 0,124] | +0,026 [−0,023; 0,074] | parkinson +0,075 [0,009; 0,193]; riesgo +0,218 [0,059; 0,360] |
| V5-P − V4 BN (referencia previa) | +0,056 [−0,006; 0,114] | +0,029 [−0,015; 0,075] | riesgo +0,183 [0,027; 0,317] |

McNemar por voto mayoritario (no incorpora la agrupación por sujeto; solo orientativo): V5-CR vs V4 BN 9 vs 3 (p = 0,146); V5-CR vs V5-C 2 vs 2.

**Robustez y dependencia (cambio de F1 macro; modelos congelados)**
| Prueba | V4 base | V5-P | V5-C | **V5-CR** |
|---|---:|---:|---:|---:|
| Cámara que sigue 100 % | −0,325 | −0,313 | −0,023 [−0,043; −0,005] | **0,000** |
| Cámara que sigue 50 % | −0,117 | −0,119 | −0,002 | 0,000 |
| Paneo 0,05/s | −0,032 | −0,017 | −0,003 | 0,000 |
| Aspecto ×0,75 | −0,096 | 0 | 0 | 0 |
| Jitter σ=0,005 / 0,01 | −0,008 / −0,025 | −0,030 / −0,039 | −0,002 / −0,026 | −0,012 / −0,038 [−0,081; 0,010] |
| 20 % cuadros perdidos | +0,011 | −0,011 | −0,003 | −0,005 |
| Permutar grupo «desplazamiento global» | −0,065 | **−0,157** | −0,025 | −0,009 |
| Rama de características neutralizada | −0,134 | −0,079 | −0,027 | −0,017 |
| Filtro pasa-bajos / tiempo invertido | −0,056 / −0,009 | −0,305 / −0,043 | −0,339 / −0,107 | −0,336 / −0,058 |
| Fases aleatorias (no física) | −0,346 | −0,651 | −0,578 | −0,609 |

La invariancia al aspecto/zoom/cámara que sigue de V5-C/V5-CR es en parte **por construcción** (se verificó además numéricamente); lo que se midió empíricamente con modelos congelados es que esa invariancia **no cuesta más de 0,03 de F1 macro** frente a V5-P y que el modelo ya no colapsa.

## 4. Criterios de aceptación (pre-registrados)

| Criterio | V5-C | V5-CR |
|---|---|---|
| Robustez a cámara que sigue ≥ −0,05 | −0,023 ✔ | 0,000 ✔ |
| Límite inferior IC de ΔF1 macro (vs V4 BN para V5-C; vs V5-C para V5-CR) > −0,05 | −0,049 ✔ (margen de 0,001) | −0,032 ✔ |
| Ninguna clase pierde > 0,10 de F1 | ✔ (máx. −0,050) | ✔ (máx. −0,003) |
| Pruebas numéricas (633 ventanas, sin fuga) | ✔ | ✔ (0 fugas) |

## 5. Qué mejoró y qué empeoró
- **Mejoró:** independencia respecto a la cámara que sigue (de −0,31 a 0,00), paneo, y dependencia del grupo de desplazamiento global (−0,157 → −0,009); corrección de la fuga por interpolación; F1 y sensibilidad de riesgo de caída frente a V4 (0,378 → 0,581; 0,364 → 0,691; IC de F1 excluye 0); calibración tras temperatura (ECE 0,064, el mejor de todos los calibrados).
- **Empeoró o no mejoró:** F1 de normal frente a V5-P (−0,021, IC excluye 0; −0,038 en V5-C) y exactitud (−0,021 n. s.); **esclerosis múltiple**: F1 0,684 vs 0,756 de V4 BN (−0,072 n. s.) y sensibilidad 0,618 vs 0,745 (−0,127); EM→riesgo sigue en 32/110; ECE crudo 0,131 (peor que 0,067); sensibilidad al jitter σ=0,01 −0,038 (n. s.).
- **Mayor dependencia de la dinámica fina** (filtro pasa-bajos −0,336, tiempo invertido −0,058): es coherente con usar movimiento, pero también podría reflejar ruido/estilo de captura; no es evidencia clínica.
- **Compensación explícita:** V5-P tiene la mejor cifra interna (F1 macro 0,800, exactitud 0,880), pero esa cifra incluye información de desplazamiento de la imagen que cambia con la cámara; V5-CR entrega 0,785 (diferencia con V5-P no concluyente) sin esa dependencia. No declaro a V5-CR superior a V5-P en poder predictivo.

## 6. Limitaciones que solo se resuelven con datos reales
1. Fuente de grabación aún asociada a la clase (trípode/laboratorio en normal y Parkinson; cámara en mano y menor resolución en EM y riesgo). Se eliminó la dependencia de la **traslación de la cámara**, pero no la de estilo de captura, resolución, vista y postura.
2. Confusión EM↔riesgo (≈ 30/110 y 16–25/55): no hay datos suficientes para separarlas y el Dataset V4 tiene 9 sujetos de riesgo y 21 de EM, con 27 grupos provisionales.
3. 7 sujetos con Parkinson; 0/117 videos con validación clínica individual.
4. Ausencia de un conjunto externo limpio: las 5 semillas y todas las variantes (V5-P, V5-S, V5-C, V5-CR) se evaluaron sobre los mismos 117 videos y sus particiones; **cuantas más versiones se diseñan sobre ellos, más probable es el sobreajuste a esa evaluación**. Estas cifras no son una estimación externa.
5. No se repitieron las sondas de metadatos (F1 0,78–0,86 con solo metadatos en V4) con V5-CR, ni la evaluación de los 20 videos descartados: no habría añadido validez (etiquetas no verificadas).

## 7. Decisión
- **Calidad técnica del preprocesamiento:** V5-CR > V5-C > V5-P > V4 (corrige los defectos A–F verificados y es exactamente invariante a cámara/aspecto/zoom).
- **Rendimiento predictivo interno:** V5-P ≥ V5-CR ≥ V5-C > V4 BN > V4 base; solo la mejora de riesgo de caída frente a V4 BN es estadísticamente respaldada (IC por sujeto excluye 0); F1 macro no distinguible.
- **Robustez:** V5-CR (mejor) > V5-C > V5-P ≈ V4.
- **Generalización:** sin evidencia externa; nada que afirmar sobre validez clínica.
- **Recomendación única:** **V5-CR como versión final del prototipo (candidato técnico), sin integrarla todavía en la aplicación.** Si el criterio fuera maximizar la cifra interna sin considerar la cámara, V5-P es 0,015 de F1 macro superior (n. s.), pero cae 0,31 con cámaras que siguen a la persona. El V4 BN sigue activo hasta que decida la integración.

## 8. ¿Seguir entrenando?
**No.** Los problemas restantes (confusión EM/riesgo, asociación fuente-clase, pocos sujetos, falta de validación externa) no se resuelven con más ajustes sobre los mismos 117 videos; seguir probando variantes aumentaría el riesgo de sobreajuste a la evaluación. Los pasos útiles requieren **datos reales nuevos** (≥ 10 sujetos por clase, fuentes mezcladas dentro de cada clase, etiqueta verificada) y evaluar V4 BN y V5-CR congelados.

## 9. Reproducción
Desde la raíz del proyecto, con `.venv311` y `PYTHONDONTWRITEBYTECODE=1`: `fase8_evidencia.py --version v4|v5P` → `fase8_pruebas_c.py` → `fase8_entrenar_c.py --build/--cv/--final` → `fase8_robustez_c.py` → `fase8_fuga_residual.py` → `fase8_prueba_cr.py` → `crear_entrenador_cr.py` → `fase8_entrenar_cr.py --build/--cv/--final` → `crear_scripts_finales.py` → `fase8_robustez_cr.py` → `fase8_comparar_final.py`. Checkpoints finales en `checkpoints/` (V5-C y V5-CR, entrenados con los 117 videos; no estiman exactitud). No añadir a Git sin autorización: `resultados/dataset_v5c*_bank.npz`, `resultados/modelos_cv_*`, `resultados/oof_*.npz`, `checkpoints/`.
