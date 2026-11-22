# Recomendación final — V4 vs V5

**Conservar V4 BN (`gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`) como modelo activo de la aplicación. No se cambió ninguna configuración.** V5-P queda como candidato experimental prometedor.

## Por qué no se reemplaza todavía
1. Contra el modelo activo (V4 BN), V5-P mejora F1 macro en +0,056, pero el IC95 por sujeto [−0,006; 0,114] incluye 0; solo F1 de riesgo de caída (+0,183 [0,027; 0,317]) excluye 0.
2. La calibración cruda empeora (ECE 0,147 vs 0,067); con escalado de temperatura por fold queda comparable (0,082 vs 0,076 de V4 base).
3. En 20 videos no usados en entrenamiento (de calidad dudosa, etiquetas sin validar) V5-P y V4 BN aciertan 12/20 cada uno: empate sin valor estadístico.
4. La evaluación de V5 es interna, sobre los mismos 117 videos usados para auditar V4; la colinealidad fuente↔clase persiste, por lo que parte de la mejora podría explicarse por atajos de grabación.
5. Esclerosis múltiple no mejora (F1 0,730; EM→riesgo 32/110) y riesgo de caída sigue siendo débil (F1 0,562) y no validado clínicamente.

## Qué sí quedó demostrado
- Los defectos de código (espejo, escala, características absolutas, aspecto, duración de ventana, coherencia de aumentación) están corregidos y verificados con 21 pruebas numéricas (0 fallos); V4 los exhibe en las 7 pruebas de regresión.
- V5-P supera a V4 base con incertidumbre por sujeto (F1 macro +0,075 [0,016; 0,136]; McNemar por voto 10 vs 1, p = 0,012) y mejora Parkinson y riesgo de caída.
- V5 es menos dependiente del aspecto/orientación (|ρ|>0,65: 19→8 características; AUC de orientación 0,944→0,719) y menos afectado por el paneo de cámara (−0,017 vs −0,032).

## Qué no empeora ni mejora (reportado sin ocultar)
EM sin mejora; jitter y pérdida de cuadros sin mejora (V5-P algo peor, n. s.); más dependencia del grupo de desplazamiento global (−0,157 al permutar).

## Siguientes pasos (sin reentrenar V4)
1. Conseguir videos nuevos (≥ 10 sujetos por clase, fuentes mezcladas dentro de cada clase, etiqueta verificada) y evaluar V4 BN y V5-P congelados.
2. Repetir las sondas de metadatos (F1 macro 0,78–0,86 con solo metadatos) con V5 para medir cuánto del rendimiento es atajo.
3. Evaluar la recalibración BatchNorm de V5 (no pre-registrada aquí) y, si se decide adoptarlo, integrar `window_inputs` en un script de inferencia nuevo (no se tocó `14_predict_deep_video_v4exp.py`) con SHA-256 y avisos de calidad, y reprobar el flujo completo.
4. Decidir con el tutor cómo presentar V5 en la tesis (texto en `TEXTO_TESIS_3_3_6_y_4_4.md`).

## Criterio para reemplazar V4
Reemplazar solo si V5 supera a V4 BN en un conjunto externo con diferencia de F1 macro cuyo IC por sujeto excluya 0, sin empeorar ninguna clase en más de 0,10 y con calibración (tras temperatura) no peor.
