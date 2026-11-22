# 4.4 Evaluación del modelo V5-CR y resultados comparativos (propuesta)

## A. Texto nuevo propuesto
**4.4.1 Protocolo.** La evaluación es interna: validación cruzada de cinco particiones agrupada por grupo técnico de sujeto, repetida con cinco semillas, sobre los 117 videos. Cada semilla produce una predicción fuera de partición por video; las métricas son el promedio de las cinco semillas y los intervalos de confianza del 95 % se obtuvieron por remuestreo de grupos de sujeto. Las repeticiones no son muestras independientes. Todas las versiones se evaluaron con los mismos videos, grupos y particiones, de modo que las comparaciones son pareadas. «V4 base» designa el modelo sin recalibración de BatchNorm y «V4 activo» el modelo con BatchNorm recalibrada, que operaba en la aplicación antes de V5-CR.

**4.4.2 Resultados de V5-CR.** El modelo final obtuvo una exactitud de 0,860 (IC95 0,798–0,909) y un F1 macro de 0,785 (0,697–0,847). Por clase, el F1 fue 0,956 (normal), 0,921 (Parkinson), 0,684 (esclerosis múltiple) y 0,581 (riesgo de caída), con sensibilidades de 0,935, 0,969, 0,618 y 0,691 y precisiones de 0,979, 0,879, 0,781 y 0,507. La matriz de confusión (suma de las cinco repeticiones, 585 predicciones) muestra que la confusión predominante es entre esclerosis múltiple y riesgo de caída: 32 de 110 predicciones de esclerosis múltiple se clasificaron como riesgo de caída y 16 de 55 de riesgo de caída como esclerosis múltiple. La ECE sin calibrar fue 0,131 y con temperatura por partición 0,064.

**4.4.3 Comparación entre versiones.**
| Modelo | Exactitud | F1 macro | F1 normal | F1 Parkinson | F1 esclerosis múltiple | F1 riesgo de caída |
|---|---|---|---|---|---|---|
| V4 base | 0,834 | 0,725 | 0,953 | 0,846 | 0,739 | 0,363 |
| V4 activo | 0,851 | 0,744 | 0,963 | 0,881 | 0,756 | 0,378 |
| V5-P | 0,880 | 0,800 | 0,977 | 0,931 | 0,730 | 0,562 |
| V5-C | 0,841 | 0,772 | 0,939 | 0,881 | 0,687 | 0,580 |
| **V5-CR** | **0,860** | **0,785** | 0,956 | 0,921 | 0,684 | 0,581 |

Frente al V4 activo, la diferencia de F1 macro (+0,041; IC95 −0,029 a 0,102) y la de exactitud (+0,009; −0,039 a 0,053) **no fueron estadísticamente concluyentes**; tampoco lo fue la prueba de McNemar sobre el voto mayoritario (9 videos acertados solo por V5-CR frente a 3 solo por V4; p = 0,146). La **única mejora respaldada por los intervalos fue la de la clase riesgo de caída**: F1 +0,203 (0,023 a 0,356) y sensibilidad +0,327 (0,125 a 0,525), con 11 videos y 9 grupos. En esclerosis múltiple el F1 fue menor (−0,072; −0,182 a 0,027) y en normal frente a V5-P fue menor (−0,021; −0,042 a −0,004). V5-CR no es distinguible de V5-P (F1 macro −0,015; −0,052 a 0,020) y presenta una diferencia no concluyente de +0,014 frente a V5-C.

**4.4.4 Calibración.** Sin calibrar, la ECE de V5-CR (0,131) fue significativamente peor que la del V4 activo (0,067; diferencia +0,064, IC95 0,022 a 0,085). Con temperatura ajustada por partición, la ECE de V5-CR bajó a 0,064 (Brier 0,213). Bajo ese mismo protocolo solo existe una referencia de V4 base (ECE 0,076; Brier 0,269), con la que la diferencia es pequeña y sin intervalo de confianza calculado; no existen probabilidades del V4 activo calibradas por partición, por lo que no puede afirmarse que V5-CR esté mejor calibrado que el V4 activo.

**4.4.5 Robustez.** Con los modelos congelados, una cámara que sigue a la persona redujo el F1 macro en 0,325 en V4 base y en 0,313 en V5-P, y no lo alteró en V5-CR (variación 0,000, invariante por construcción y verificada en 633 ventanas reales); lo mismo ocurrió con el paneo, la relación de aspecto y el zoom. V5-CR no mejoró la robustez frente al ruido en los puntos corporales (σ = 0,01: −0,038 frente a −0,025 de V4 base) ni frente a la pérdida de fotogramas (−0,005). Un filtro pasa-bajos sobre la secuencia redujo el F1 macro en 0,336 y aleatorizar las fases en 0,609, lo que indica que el modelo se apoya en la dinámica fina del movimiento, mientras que desordenar bloques temporales apenas lo cambió (−0,009).

**4.4.6 Sesgo de adquisición.** Clasificadores que solo utilizan siete metadatos técnicos del video (resolución, fotogramas por segundo, duración, etc.) alcanzaron, con los mismos videos y particiones, un F1 macro de 0,777 a 0,786 (V4), del mismo orden que el de V5-CR. Por tanto el rendimiento interno no puede atribuirse con certeza a la marcha: la fuente de grabación está fuertemente asociada a la clase. V5-CR elimina algunas pistas de grabación (aspecto, traslación de cámara), pero esa asociación persiste y no se repitió la sonda con las características de V5-CR.

**4.4.7 Conclusión del apartado.** El modelo V5-CR corrige defectos verificables del preprocesamiento y es invariante al desplazamiento global de la cámara; muestra una mejora respaldada para la clase riesgo de caída, sin mejora global estadísticamente demostrada frente al V4 activo, con peor desempeño en esclerosis múltiple y una calibración sin ajustar menos fiable. Los resultados son una validación interna de un prototipo: no constituyen rendimiento clínico ni evidencia de generalización a otras fuentes de grabación.

## B. Se conserva
Los resultados de V4 (0,834/0,725 base; 0,851/0,744 activo; F1 por clase del activo 0,963/0,881/0,756/0,378), la auditoría de sesgo de V4 y las sondas de metadatos, rotulados como versión previa.

## C. Se reemplaza
La presentación de V4 como evaluación del modelo final; las matrices de confusión, comparaciones y calibración de V4 si figuran como resultados del sistema (Figuras 4.9–4.11, Tablas 4.3–4.4: verificar en el Word).

## D. Figuras/tablas
`fig_comparacion_exactitud_f1macro_por_version`, `fig_V5CR_precision_sensibilidad_f1_por_clase`, `matriz_confusion_V5CR_A/B`, `matriz_confusion_D_comparacion_V4activo_vs_V5CR`, `fig_calibracion_V5CR_diagrama_fiabilidad`, `fig_robustez_camara_ruido_perdida_fotogramas`, `fig_f1_macro_por_semilla`; tablas de `METRICAS_VERIFICADAS_POR_MODELO.csv`, `DIFERENCIAS_V5CR_VS_OTROS.csv` y `ROBUSTEZ_COMPARADA_DELTA_F1_MACRO.csv`.

## E. Fuentes
`04_METRICAS_Y_COMPARACIONES/` (verificado 63/63 contra `comparacion_final.json`); `05_MATRICES_DE_CONFUSION/`; `docs/optimizacion_final_v5_2026-11-19/INFORME_FINAL_OPTIMIZACION.md`; `docs/evidencia_experimental_v4_2026-11-18/tabla_4_4_1_comparacion_v4.csv` (sondas de metadatos).
