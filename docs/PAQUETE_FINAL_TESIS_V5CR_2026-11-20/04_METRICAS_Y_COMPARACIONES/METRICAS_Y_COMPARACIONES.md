# Métricas verificadas y comparaciones V4 – V5-P – V5-C – V5-CR

**Verificación:** las métricas se recalcularon desde las predicciones fuera de partición (OOF) originales con `scripts/calcular_metricas_y_matrices.py`. **63 de 63** valores recalculados coinciden (tolerancia 0,0001) con `comparacion_final.json` (`VERIFICACION_CONTRA_ORIGINALES.csv`). Los cinco valores citados en la solicitud (V5-CR: exactitud 0,8598; F1 macro 0,7852; F1 Parkinson 0,9207; F1 esclerosis múltiple 0,6839; F1 riesgo de caída 0,5806) **coinciden con los originales**.

## 0. Protocolo (leer antes de citar cualquier cifra)
- Evaluación **interna** por validación cruzada agrupada por grupo técnico de sujeto (`StratifiedGroupKFold`, 5 particiones externas) repetida con **5 semillas de partición (42–46)**; cada semilla produce una predicción fuera de partición por video (117). Cada métrica es el **promedio de las 5 métricas por semilla**; las semillas **no son muestras independientes**.
- Todas las versiones usan los mismos 117 videos, grupos y semillas, así que sus comparaciones son pareadas.
- Los intervalos de confianza (IC95 %) son por remuestreo (bootstrap) de **grupos de sujeto** (2000 remuestreos).
- La evaluación **no es clínica ni externa**: 117 videos / 67 grupos técnicos (27 provisionales), con asociación entre la fuente de grabación y la clase (ver `03_DATASET_Y_METODOLOGIA/`). Los mismos 117 videos sirvieron para diseñar y comparar varias versiones (riesgo de sobreajuste a la evaluación).
- «V4 base» = modelo V4 sin recalibrar BatchNorm; «**V4 activo**» = V4 con BatchNorm recalibrada (el que usaba la aplicación antes de V5-CR). **No se mezclan** con V5-P ni V5-CR. V5-P = 36 características; V5-C = 33 características sin traslación global; **V5-CR = V5-C + interpolación relativa a la cadera (modelo final)**.

## 1. Tabla principal (promedio de 5 semillas)
| Modelo | Exactitud | F1 macro | F1 normal | F1 Parkinson | F1 esclerosis múltiple | F1 riesgo de caída |
|---|---|---|---|---|---|---|
| V4 base | 0,8342 | 0,7252 | 0,9532 | 0,8458 | 0,7387 | 0,3630 |
| V4 activo (BN recalibrada) | 0,8513 | 0,7442 | 0,9626 | 0,8806 | 0,7555 | 0,3781 |
| V5-P | 0,8803 | 0,7999 | 0,9770 | 0,9311 | 0,7301 | 0,5615 |
| V5-C | 0,8410 | 0,7716 | 0,9389 | 0,8808 | 0,6870 | 0,5797 |
| **V5-CR** | **0,8598** | **0,7852** | **0,9557** | **0,9207** | **0,6839** | **0,5806** |

Precisión, sensibilidad, ECE y Brier de cada modelo: `METRICAS_VERIFICADAS_POR_MODELO.csv`. Para V5-CR: precisión 0,9789 / 0,8786 / 0,7812 / 0,5066 y sensibilidad 0,9345 / 0,9692 / 0,6182 / 0,6909 (normal / Parkinson / esclerosis múltiple / riesgo de caída).

## 2. Intervalos de confianza (IC95 % bootstrap por grupo; `INTERVALOS_CONFIANZA_BOOTSTRAP_POR_GRUPO.csv`)
Estos intervalos se recalcularon en este paquete (semilla de remuestreo 20261120); los de las diferencias provienen de `comparacion_final.json` (semilla original 20261119), por lo que pueden diferir en el cuarto decimal.
| Modelo | Exactitud [IC95] | F1 macro [IC95] |
|---|---|---|
| V4 base | 0,834 [0,755; 0,901] | 0,725 [0,630; 0,795] |
| V4 activo | 0,851 [0,775; 0,916] | 0,744 [0,655; 0,814] |
| V5-P | 0,880 [0,821; 0,928] | 0,800 [0,721; 0,854] |
| V5-C | 0,841 [0,770; 0,898] | 0,772 [0,670; 0,842] |
| V5-CR | 0,860 [0,798; 0,909] | 0,785 [0,697; 0,847] |

V5-CR por clase (F1 [IC95]): normal 0,956 [0,922; 0,980]; Parkinson 0,921 [0,804; 0,966]; esclerosis múltiple 0,684 [0,539; 0,796]; riesgo de caída 0,581 [0,314; 0,744]. Los intervalos de todas las versiones se solapan ampliamente.

## 3. Diferencias de V5-CR frente a las demás (`DIFERENCIAS_V5CR_VS_OTROS.csv`)
| Comparación | Métrica | Diferencia [IC95] | ¿Excluye 0? |
|---|---|---|---|
| V5-CR − V4 activo | F1 macro | +0,041 [−0,029; 0,102] | **No (no concluyente)** |
| V5-CR − V4 activo | exactitud | +0,009 [−0,039; 0,053] | No |
| V5-CR − V4 activo | F1 riesgo de caída | +0,203 [0,023; 0,356] | **Sí** |
| V5-CR − V4 activo | sensibilidad riesgo de caída | +0,327 [0,125; 0,525] | **Sí** |
| V5-CR − V4 activo | F1 esclerosis múltiple | −0,072 [−0,182; 0,027] | No |
| V5-CR − V4 activo | ECE sin calibrar | +0,064 [0,022; 0,085] | **Sí: V5-CR sin calibrar está peor calibrado** |
| V5-CR − V4 activo | McNemar (voto mayoritario) | 9 videos solo V5-CR, 3 solo V4; p exacto 0,146 | No |
| V5-CR − V4 base | F1 macro | +0,060 [−0,007; 0,124] | No |
| V5-CR − V5-P | F1 macro | −0,015 [−0,052; 0,020] | No |
| V5-CR − V5-P | F1 normal | −0,021 [−0,042; −0,004] | **Sí (V5-CR peor en normal)** |
| V5-CR − V5-C | F1 macro | +0,014 [−0,032; 0,062] | No |

**Conclusión metodológica obligatoria:** la mejora global de V5-CR frente al V4 activo **no quedó estadísticamente demostrada**. La única mejora respaldada por intervalos es la de la clase riesgo de caída (con 11 videos y 9 grupos). V5-CR **empeora** en esclerosis múltiple (no significativo) y en normal frente a V5-P (significativo), y su calibración sin ajustar es peor.

## 4. Calibración (ECE: promedio por semilla, 10 intervalos de confianza)
| Modelo | ECE sin calibrar | ECE calibrado (temperatura por partición) | Brier sin calibrar | Brier calibrado |
|---|---|---|---|---|
| V4 base | 0,0949 | 0,0762 (`calibracion_v4_v5.json`) | 0,2732 | 0,2691 |
| V4 activo | 0,0666 | no disponible | 0,2451 | no disponible |
| V5-P | 0,1467 | 0,0821 | 0,2308 | 0,2077 |
| V5-C | 0,1291 | 0,0740 | 0,2687 | 0,2516 |
| V5-CR | 0,1307 | 0,0638 | 0,2311 | 0,2134 |

**Comparación válida solo bajo el mismo protocolo:** las columnas «sin calibrar» son comparables entre todos los modelos. La calibración por temperatura ajustada por partición existe para V5-P, V5-C, V5-CR y **solo para V4 base** (fuente: `docs/mejora_modelo_v5_experimental_2026-11-19/resultados/calibracion_v4_v5.json`); **no existe para V4 activo**. Bajo ese mismo protocolo, V5-CR calibrado (ECE 0,064; Brier 0,213) frente a V4 base calibrado (0,076; 0,269) es algo mejor, sin intervalo de confianza calculado para esa diferencia; frente a V4 activo (0,067 sin calibrar) solo es válida la comparación sin calibrar, en la que V5-CR es peor (+0,064; IC95 0,022 a 0,085). V4 activo usa una temperatura global T = 0,9022 y V5-CR T = 0,6615. La calibración por partición de V5-CR se evaluó sobre el mismo OOF con el que se estima T, por lo que es una evaluación interna. Figura: `fig_calibracion_V5CR_diagrama_fiabilidad`.

## 5. Matrices de confusión
Ver `05_MATRICES_DE_CONFUSION/` (valores absolutos como suma de 5 repeticiones, normalizadas por clase verdadera, voto mayoritario por video, comparación V4 activo–V5-CR). La matriz absoluta de V5-CR coincide con la guardada en `comparacion_final.json`: [[271,13,3,3],[0,126,1,3],[6,4,68,32],[0,1,16,38]] (suma de las 5 semillas; **585 predicciones = 117 × 5, no 585 videos**). Confusión principal: **32 de 110** predicciones de esclerosis múltiple se clasificaron como riesgo de caída (29,1 %) y 16 de 55 de riesgo de caída como esclerosis múltiple.

## 6. Robustez (modelos congelados; ΔF1 macro respecto a la línea base de cada modelo; `ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv`)
| Perturbación | V4 base | V5-P | V5-C | V5-CR |
|---|---|---|---|---|
| Cámara que sigue a la persona (100 %) | −0,325 | −0,313 | −0,023 | **0,000** |
| Cámara que sigue (50 %) | −0,117 | −0,119 | −0,002 | 0,000 |
| Paneo de cámara 0,05 /s | −0,032 | −0,017 | −0,003 | 0,000 |
| Relación de aspecto ×0,75 | −0,096 | 0,000 | 0,000 | 0,000 |
| Zoom ×1,3 | 0,000 | 0,000 | 0,000 | 0,000 |
| Ruido de landmarks σ = 0,005 | −0,008 | −0,030 | −0,002 | −0,012 |
| Ruido de landmarks σ = 0,01 | −0,025 | −0,039 | −0,026 | −0,038 |
| Pérdida aleatoria del 20 % de fotogramas | +0,011 | −0,011 | −0,003 | −0,005 |

- V4 **activo** no se evaluó con estas perturbaciones (la tabla usa V4 base). Cada ΔF1 compara el modelo consigo mismo (las líneas base difieren).
- Las invariancias de V5-CR (cámara que sigue, paneo, aspecto, zoom) son **por construcción** y se verificaron numéricamente (0 de 633 ventanas reales cambian ante una cámara que sigue a la persona).
- **V5-CR no mejora** el ruido de landmarks ni la pérdida de fotogramas respecto a V4; con σ = 0,01 empeora (−0,038 frente a −0,025 de V4 base; ambos con IC que incluyen 0).
- Dependencia temporal de V5-CR (`fase4_robustez_v5CR.json`): un filtro pasa-bajos reduce el F1 macro en 0,336 y aleatorizar las fases por canal en 0,609, mientras barajar bloques apenas lo altera (−0,009): el modelo usa la dinámica fina del movimiento (coherente con usar movimiento, pero podría reflejar también ruido de captura). Neutralizar la rama tabular solo reduce 0,017 (no significativo): la rama de secuencia domina.

## 7. Qué NO se puede decir
No hay validación clínica ni externa; no se demostró que V5-CR sea mejor que V4 activo en F1 macro; no se puede afirmar generalización a otras fuentes de grabación; las cifras no estiman rendimiento en pacientes.

## 8. Referencia de sesgo de adquisición (sondas de metadatos; dato heredado de V4, no recalculado para V5-CR)
Sobre los **mismos 117 videos y las mismas particiones por sujeto** (protocolo V2, 5 semillas; fuente: `docs/evidencia_experimental_v4_2026-11-18/tabla_4_4_1_comparacion_v4.csv`), clasificadores que NO ven el movimiento y usan solo **7 metadatos técnicos** (resolución, fps, duración, etc.) obtuvieron: regresión logística exactitud 0,863 y F1 macro **0,777**; bosque aleatorio exactitud 0,877 y F1 macro **0,786**; con metadatos más estrato/vista/fondo hasta F1 macro 0,825–0,859. Para comparar: V4 activo 0,744 y **V5-CR 0,785**. El rendimiento de V5-CR es del mismo orden que el de una sonda que solo conoce propiedades de la grabación. **Consecuencia:** el F1 macro interno de V5-CR no puede interpretarse como evidencia de que el modelo reconozca la marcha independientemente de la fuente. No se repitió esta sonda específicamente para V5-CR (queda como análisis pendiente). Las características de V5-CR eliminan algunas pistas (aspecto, traslación de cámara) y su proxy de orientación fue menos predictivo en V5-P (AUC 0,719 frente a 0,944 en V4 dentro de esclerosis múltiple/riesgo de caída), pero la asociación fuente–clase del dataset persiste.
