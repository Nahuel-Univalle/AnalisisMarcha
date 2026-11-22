# Pre-registro del experimento V5-C (escrito ANTES de construir V5-C y de ver ningún resultado suyo)

**Problema verificado (E):** al simular una cámara que sigue a la persona, V4 base y V5-P pierden ΔF1 macro −0,325 y −0,313 (IC95 por sujeto [−0,369; −0,279] y [−0,362; −0,258]); con 50 % de seguimiento −0,117 y −0,119. La mediana de `horizontal_motion_mean` por procedencia es 0,60 (normal, trípode), 0,31 (Parkinson, trípode), 0,037 (EM), 0,011–0,095 (riesgo, cámara que acompaña / en mano): la característica distingue «cámara fija» de «cámara que sigue», factor asociado a la clase. La rama de secuencia es invariante (origen en la cadera), por lo que la sensibilidad viene de las características de desplazamiento global.

**Hipótesis:** si se eliminan de las características las magnitudes que dependen de la traslación de la persona en la imagen (no de la marcha relativa), el modelo seguirá reconociendo patrones con rendimiento no inferior y dejará de depender del seguimiento de la cámara.

**Cambio único respecto a V5-P (mismo código, mismos datos, misma arquitectura, mismo protocolo, mismas semillas):** 33 características.
- Se eliminan: `hip_center_motion_mean`, `shoulder_center_motion_mean`, `horizontal_motion_mean` (traslación global).
- Se redefinen sin traslación global: `body_motion_mean/std` (hombros, rodillas y tobillos RELATIVOS a la cadera), `motion_smoothness` y el término de cadera de `gait_variability` (usan solo el movimiento vertical de la cadera).
- Se conservan `vertical_motion_mean` y todo lo demás (incluidos los anchos de hombros/caderas, para no mezclar con la variante V5-S).
- La secuencia [68×40] no cambia.

**Coste biomecánico declarado:** se pierde la velocidad de avance en la imagen, que solo es interpretable con cámara fija. No se elimina información relativa de la marcha.

**Criterios de aceptación fijados antes de ver resultados:**
1. Robustez: ΔF1 macro con cámara que sigue (100 %) ≥ −0,05.
2. Rendimiento: el límite inferior del IC95 por sujeto de ΔF1 macro (V5-C − V4 BN activo) > −0,05, y ninguna clase pierde > 0,10 de F1 frente a V5-P.
3. Pruebas numéricas: invariancia a la traslación horizontal, coherencia del espejo, sin NaN/inf, secuencia idéntica a V5-P.

Si 1 y 3 se cumplen y 2 también: V5-C es la mejor base *defendible* aunque su F1 sea menor que el de V5-P (se informará la compensación). Si 2 falla: se conserva V5-P con la advertencia de dependencia de la cámara. No se ejecutan más variantes.

**Reconocimiento:** cualquier resultado se calcula sobre los mismos 117 videos usados para auditar V4 y V5; no es una estimación externa independiente.

---
# Adenda 1 (escrita tras ver el resultado de V5-C y ANTES de implementar V5-CR)

**Resultado de V5-C (ya conocido):** criterios 1, 2 y 3 cumplidos (ver `resultados/comparacion_final.json`); robustez a cámara que sigue −0,023 (IC [−0,043; −0,005]) en lugar de −0,31.

**Defecto verificado (F, consistencia):** `fase8_fuga_residual.py` → 370/633 ventanas cambian su secuencia ante una cámara que sigue y **las 370 tienen landmarks enmascarados o cuadros interpolados**; las 137 ventanas sin enmascarados cambian exactamente 0. Causa: `resample_grid` interpola cada coordenada en valores **absolutos** y mantiene el valor en los extremos; al restar después la cadera real, la traslación de la persona se filtra en las coordenadas relativas (mediana 1,10 longitudes de torso, máximo 6,2, en las ventanas afectadas; fracción afectada: normal 0,85, Parkinson 0,57, EM 0,29, riesgo 0,43). V4 interpolaba coordenadas ya relativas a la cadera (`deep_common.py:242-256`). Es un defecto de código introducido en V5, correlacionado con la clase (los normales se desplazan más con trípode).

**Cambio único (V5-CR = V5-C + corrección):** interpolar los landmarks en coordenadas relativas a la cadera (y la cadera por separado), reconstruyendo las coordenadas absolutas con la cadera interpolada. Todo lo demás idéntico a V5-C (33 características, arquitectura, protocolo, semillas).

**Criterios de aceptación (fijados ahora):**
1. Prueba numérica: con cámara que sigue (100 %), diferencia de secuencia y características < 1e-6 en las **633 ventanas reales** (hoy 370 fallan); en las 137 ventanas sin enmascarados las entradas son idénticas a V5-C.
2. Robustez: ΔF1 macro con cámara que sigue (100 %) ≥ −0,05.
3. Rendimiento: límite inferior del IC95 por sujeto de ΔF1 macro (V5-CR − V5-C) > −0,05 y ninguna clase pierde > 0,10 de F1 frente a V5-C.
Como es una corrección de exactitud, se **acepta si 1 cumple y no hay deterioro** (2 y 3), aunque el F1 no suba. No se probará ninguna otra variante después de V5-CR.
