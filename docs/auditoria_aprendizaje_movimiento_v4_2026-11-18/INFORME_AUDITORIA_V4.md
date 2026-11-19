# Auditoría técnica del modelo V4: ¿aprende movimiento humano?

Fecha: 18 de noviembre de 2026. Repositorio: `C:\Users\fnahu\Desktop\GITMarcha\AnalisisMarcha`.
Modelo: `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`.
Tipo de trabajo: diagnóstico por inspección de código y lectura de artefactos existentes. No se entrenó, no se ejecutó ninguna inferencia, no se modificó ningún archivo existente.

## 0. Alcance y método

Qué se hizo:

- Se leyeron los archivos de código citados con sus números de línea (ver `TRAZABILIDAD_CODIGO.csv`).
- Se leyeron los inventarios y la auditoría experimental previa (`docs/inventario_dataset_v4_2026-11-18`, `docs/evidencia_experimental_v4_2026-11-18`).
- Se calcularon estadísticos **descriptivos** a partir de artefactos ya guardados: tablas cruzadas de `samples_v4_preview.csv`, la matriz de confusión del OOF del candidato (`step18_bn/oof_per_video.csv`) y medianas y correlaciones de Spearman de `X_feat` en `dataset_v4_preview.npz` (abierto solo para lectura, sin `allow_pickle`). Los scripts auxiliares viven en una carpeta temporal fuera del repositorio.
- Una única comprobación de cadena (`'LEFT_HIP_vx'.endswith('_x')`) verifica el hallazgo A1.

Qué no se hizo: ejecutar el modelo, MediaPipe u OpenCV; reentrenar; recalcular las sondas; abrir navegadores, Unity o el documento Word; operaciones Git.

Todo número marcado como «recalculado» es aritmética sobre archivos ya existentes. No sustituye una prueba experimental.

Una advertencia sobre rutas: el directorio de trabajo de la sesión (`EMERGENTESFINAL\analisis-marcha-ia`) es otro proyecto. Todos los archivos citados están en `GITMarcha\AnalisisMarcha`, que es donde se escriben estos entregables.

## 1. Flujo real del modelo V4

```
Video
 → extract_normalized (24_normalized_reextract.py:55-124): rejilla 15 fps, ≤720 px, MediaPipe Pose (model_complexity=1)
 → 17 landmarks (x, y normalizados por W y H; z y visibility se guardan pero no entran a la red)
 → ventana 5.03 s desde el primer cuadro con pose (14_predict…:153-158 / build_dataset_v4_preview.py:74-81)
 ├─ frames_to_sequence (deep_common.py:204-276) → X_seq [68, 96]
 └─ build_feature_row (video_training_common.py:640-806) con duración = W_eff → 36 características → FeatureScaler
 → GaitTemporalModel.forward(seq, feat) (deep_common.py:477-484)
 → logits / T (T = 0.9022) → softmax → 4 clases
```

### 1.1 Qué recibe realmente el modelo

- `seq` [68, 96] y `feat` [36]. Nada más: ni nombre de archivo, ni metadatos, ni píxeles (`deep_common.py:477-484`; producción en `14_predict_deep_video_v4exp.py:170-172`).
- La rama de secuencia pasa por tres `Conv1d` con BatchNorm y GELU, y concatena pooling medio y máximo (`deep_common.py:448-456, 481`).
- La rama de características pasa por `Linear 36→24→16` con BatchNorm (`461-466`).
- Ambas se fusionan en una cabeza de 32 neuronas y 4 salidas (`471-475`). El modelo tiene 18.088 parámetros (Paso 17).

### 1.2 Cómo se construyen los 68 × 96

1. Posición: por cuadro, (x, y) de 17 puntos menos el centro de cadera de ese cuadro (`deep_common.py:242-243`). Esto elimina la traslación global.
2. Escala: por cuadro, `max(tronco, ancho hombros, ancho caderas)` (`233`); por clip, la mediana de esas escalas (`257-258`).
3. NaN: interpolación lineal en el tiempo (`187-201`). Se exigen los 4 puntos de tronco para aceptar el cuadro (`224`).
4. Tiempo: se normaliza a [0,1] sobre el tramo entre el primer y el último cuadro válido (`260-263`) y se remuestrea a 96 puntos (`264-268`).
5. Velocidad: diferencia entre pasos consecutivos de los 96 puntos (`270-272`).

Consecuencia que conviene tener presente: la rama de secuencia **no recibe la velocidad de traslación** (la cadera es el origen) **ni el tiempo absoluto** (el eje temporal está normalizado). La velocidad de marcha y la cadencia llegan al modelo solo por la rama de 36 características. Las velocidades de la secuencia son «por 1/95 del tramo analizado», de modo que dependen de la duración de ese tramo (ver B3).

### 1.3 Diferencias entre entrenamiento V4 y producción

Se comparó línea a línea `build_dataset_v4_preview.py:64-146` con `14_predict_deep_video_v4exp.py:130-176`. Usan las mismas funciones, la misma rejilla, el mismo ancla, la misma ventana y la misma duración efectiva W_eff. El Paso 14 documentó verificación bit a bit. **No se encontró diferencia de preprocesamiento entre entrenamiento y producción**, salvo un punto no medido (hipótesis C6): el entrenamiento usa límites de segmento manuales (`start_s`, `end_s`) en 10 videos (6 EM, 4 Riesgo) y la producción no puede tenerlos.

## 2. Las 36 características

El inventario completo, con fórmula, líneas, sensibilidad y clasificación, está en `CARACTERISTICAS_36.csv`. Resumen por categoría (cada característica figura en una sola categoría; las categorías 3 y 4 se solapan parcialmente con la 2):

| Categoría | Características |
|---|---|
| **1. Principalmente cinemáticas** (razones o medidas relativas; riesgo moderado, sobre todo por vista) | `leg_motion_asymmetry`, `ankle_vertical_asymmetry`, `trunk_sway_mean`, `trunk_sway_std`, `posture_stability_score` |
| **2. Cinemáticas sensibles al protocolo** (magnitud proporcional a la escala y al aspecto) | `body_motion_mean/std`, `hip_center_motion_mean`, `shoulder_center_motion_mean`, `vertical_motion_mean`, `horizontal_motion_mean`, `left/right_ankle_motion_mean`, `left/right_knee_motion_mean`, `left/right_wrist_motion_mean`, `gait_variability`, `trunk_inclination_mean/std` |
| **3. Potencialmente dominadas por adquisición** | `shoulder_width_mean`, `hip_width_mean` (proxy de vista), `estimated_step_count` (conteo absoluto en la ventana), `motion_smoothness` (saturada por escala) |
| **4. Significado o implementación a revisar** | `arm_swing_mean`, `arm_swing_asymmetry`, `left_arm_range`, `right_arm_range`, `ankle_vertical_range_left/right`, `knee_vertical_range_left/right` (coordenadas absolutas), `step_regularity_score` (dos definiciones), `estimated_cadence_steps_per_min`, `step_frequency_hz` (duplicado y valores implausibles), `rhythm_variability` |

Distinción entre riesgo teórico y defecto comprobado:

- **Defectos comprobados** (código + datos): las nueve derivadas de coordenadas absolutas (ocho rangos y una razón entre ellos) miden recorrido global; `shoulder_width_mean` es circular (la escala es casi el ancho de hombros, valores 0.998–1.134 en las cuatro clases); `cadence` y `step_frequency_hz` son el mismo número multiplicado por 60; `step_regularity_score` mezcla dos fórmulas.
- **Riesgos teóricos**: la dependencia de duración, encuadre, perspectiva y pose de las características de la categoría 2. Se apoyan en asociaciones descriptivas (por ejemplo, 19 de 36 características tienen |rho| entre 0.65 y 0.75 con la relación de aspecto en las 117 muestras), pero esa asociación está confundida con la clase (todo normal/Parkinson es 16:9). Dentro del grupo no laboratorio (n=33) esas mismas 19 caen a un rango de −0.18 a 0.43.
- **No se afirma** que una característica esté mal solo porque dependa de la grabación.

Un dato que merece verificación por separado: la mediana de `estimated_cadence_steps_per_min` en normales es 187 pasos/min. Es mucho más que el rango fisiológico habitual (100–120). Puede indicar picos de ruido (umbral media+0.2·std y separación mínima de 0.2 s a 15 fps, `video_training_common.py:593-612`). Es una hipótesis (C3), no un defecto demostrado.

## 3. La secuencia temporal

| Factor | Estado | Evidencia |
|---|---|---|
| Normalización respecto a cadera | Mitigado (D3) | `deep_common.py:236-243` |
| Escala corporal robusta | Mitigado en la secuencia (máximo por cuadro, mediana por clip); **inconsistente con la rama de características**, que usa otra escala (A2) | `233, 257-258` vs `video_training_common.py:509-524` |
| Aspecto (x/W, y/H) | **Presente** en M1/candidato (A4) | `build_dataset_v4_preview.py:139`; c3 solo en M3 |
| Velocidades | Calculadas sobre la secuencia remuestreada; dependen de la duración del tramo analizado (B3) | `263-272` |
| FPS de origen | Mitigado por la rejilla de 15 fps (D5); pérdidas de pose causan pasos irregulares (A8) | `24_normalized_reextract.py:48, 82-96` |
| Resolución de origen | Mitigado (≤720 px); la precisión de articulaciones en baja resolución no está medida (C4) | `49, 75, 100-101` |
| Orientación vertical/horizontal | No hay tratamiento específico; solo la distorsión por aspecto (A4) y una advertencia en producción | `14_predict…:105-110` |
| Perspectiva/vista | **Presente**: afecta escala (A2) y la interpretación de varias características | A2 |
| Interpolación | Correcta, pero rellena huecos (normales: tasa de pose mediana 0.94, mínimo 0.68) | `187-201` |
| Ventanas | **Duración desigual por clase** (B3): 55/58 normales no llenan 5.03 s | `samples_v4_preview.csv` |
| Movimiento de cámara | No eliminado en las características (coordenadas absolutas); la secuencia lo elimina al restar la cadera | A3, D3 |
| ¿Hay información temporal suficiente para distinguir patrones? | Conserva forma del movimiento relativo, amplitudes, simetría y ciclos por ventana; **no** velocidad absoluta, que viene de las características | §1.2 |

Se requieren pruebas experimentales para: efecto de la duración (A, D), movimiento de cámara (B), ruido de pose (B).

## 4. El dataset V4 y sus sesgos

Todos los números de esta sección se recalcularon desde `samples_v4_preview.csv` (117 filas) salvo indicación.

### 4.1 Colinealidad entre clase y condiciones de grabación

| Clase | Resolución | Vista | Cámara | FPS | Orientación |
|---|---|---|---|---|---|
| Normal (58) | 1920×1080: 58 | lateral: 58 | trípode: 58 | 30: 50, 50: 8 | horizontal: 58 |
| Parkinson (26) | 1920×1080: 26 | lateral: 26 | trípode: 26 | 30: 14, 50: 12 | horizontal: 26 |
| EM (22) | 478×850: 17; otros 5 | frontal 10, posterior 5, lateral 6, mixta 1 | no anotada | ~30 (13+), 60: 2, 25: 1 | vertical: 20, horizontal: 2 |
| Riesgo (11) | 848×478: 6; 478×850: 3; otros 2 | lateral 4, frontal 3, posterior 3, mixta 1 | en mano/acompaña: 10, fija: 1 | 60: 6; 16.7–30: 5 | horizontal: 6, vertical: 5 |

Es una separación casi perfecta entre el supergrupo {Normal, Parkinson} y {EM, Riesgo}: la resolución 1920×1080 aparece en 84 de 84 videos de normales y Parkinson y en 0 de 33 videos de EM y Riesgo. Con este dataset **no es posible separar** el efecto de la fuente, la resolución, la vista, el uso de trípode y la clase para ese par de supergrupos.

Lo que sí puede estudiarse con cierta limpieza:

- **Normal vs Parkinson** (ambos laboratorio): comparten resolución, vista, cámara y entorno. Persisten diferencias de FPS (50 fps: 8 normales vs 12 Parkinson) y de duración del clip.
- **EM vs Riesgo** (ambos no laboratorio): comparten ser videos de redes sociales o clínicos, pero difieren en vista y estilo de cámara (Riesgo: 10 de 11 con cámara en mano o acompañando; EM: no anotada).

### 4.2 Ventana analizada y calidad de pose

| Clase | Ventana media (s) | Llenan 5.03 s | Tasa de pose mediana |
|---|---|---|---|
| Normal | 3.94 (mín. 2.77) | 3 de 58 | 0.938 (mín. 0.68) |
| Parkinson | 5.03 | 26 de 26 | 1.000 |
| EM | 4.98 | 19 de 22 | 1.000 |
| Riesgo | 5.03 | 11 de 11 | 1.000 |

Los videos de normales duran 3.4–12.9 s (mediana 4.6 s) y los de Parkinson 6.7–20.0 s (mediana 12.5 s), de modo que la ventana efectiva está truncada por el video en los normales. Esto introduce una señal de duración correlacionada con la clase en la entrada de la red (B3).

### 4.3 Sujetos y fuga

- 67 grupos: Normal 30, Parkinson 7, EM 21, Riesgo 9. 27 son provisionales (20 EM, 7 Riesgo), 0/117 con validación clínica individual (inventario).
- El código no permite intersección de grupos entre TRAIN y TEST (aserciones en `train_protocol_v2.py:139, 145`). Fuga por sujetos desconocidos: posible solo si un grupo provisional reúne mal a una persona (C5).
- Alertas heredadas de duplicados cercanos (RiesgoCaida1–7, RiesgoCaida2–Escleorosis12): son alertas, no pruebas; los SHA-256 son distintos.
- Parkinson tiene solo 7 sujetos: cada fold externo prueba 1–2.
- Los identificadores técnicos no se convirtieron en identidades clínicas: la etiqueta es la registrada, sin validación clínica individual.

## 5. Pruebas experimentales existentes

### 5.1 Por qué V4 (F1 ≈ 0.744) queda por debajo de ciertas sondas de metadatos

Comparación metodológicamente comparable: P12, 117 videos, 5 particiones por 5 semillas, mismas particiones externas (informe de evidencia §3).

| Procedimiento | Macro-F1 OOF |
|---|---|
| Candidato BN-B | 0.7442 ± 0.0104 |
| 7 metadatos técnicos, LR / RF | 0.7773 / 0.7864 |
| 7 técnicos + orientación + fuente + vista + fondo, LR / RF | 0.8585 / 0.8250 |
| 36 características, LR / RF | 0.6222 / 0.6359 |

Lectura correcta:

- Las condiciones de grabación **permiten predecir** la etiqueta con las mismas particiones. Es consecuencia directa de la colinealidad de §4.1.
- Los clasificadores de las sondas eligen explícitamente esas variables; la red no las recibe. Que la sonda alcance un valor superior **no demuestra que la red las use**.
- Las sondas no usan los mismos hiperparámetros ni el mismo procedimiento de selección (el DL ajusta épocas y temperatura internamente), de modo que la diferencia de 0.04–0.11 no es un efecto puro de la información disponible.
- Que el candidato quede por debajo de las sondas es compatible con dos explicaciones: (a) la red no aprovecha del todo los atajos, o (b) la red aprende algo distinto, con 18.088 parámetros y 117 videos. No se puede distinguir con los datos actuales.

### 5.2 Limitaciones de las sondas

- Imputación por mediana y codificación categórica ajustadas con los 117 videos antes de dividir (`audit_shortcuts_v4.py:146-158`, `train_protocol_v2.py:270-271`). Puede inflar ligeramente las sondas; el efecto no está medido (B7).
- `source` se obtiene por reglas heurísticas (`build_manifest_v4.py::source_of()`): la sonda mixta mide separabilidad de esos estratos, no de fuentes verificadas.
- `22_source_bias.py` (0.8971) usa 136 videos y una colección anterior (EM/Riesgo reemplazados): **no es comparable** con V4. Su valor histórico no sirve para medir el candidato.
- Las 585 predicciones no son 585 observaciones independientes: las cinco repeticiones reutilizan los mismos 117 videos. La DE de repeticiones no es un intervalo de confianza.

### 5.3 Lo que sí muestra el OOF del candidato (recalculado)

Matriz sumada de las cinco repeticiones (filas = clase real; columnas Normal, Parkinson, EM, Riesgo):

| Real | N | PD | EM | RC |
|---|---|---|---|---|
| Normal | 271 | 19 | 0 | 0 |
| Parkinson | 1 | 125 | 0 | 4 |
| EM | 0 | 1 | 82 | 27 |
| Riesgo | 1 | 9 | 25 | 20 |

- **El supergrupo se conserva en 570 de 585 predicciones (97.4 %)**: 4 de laboratorio pasan a no laboratorio y 11 al revés. Esto es compatible tanto con «lee el formato» como con «distingue marcha de laboratorio frente a marcha de video doméstico». No los distingue.
- **Normal vs Parkinson** (dentro de laboratorio): 396 de 420 aciertos (94.3 %), sobre la misma fuente. Es la evidencia más limpia de señal cinemática. Aun así, normales y Parkinson difieren en duración de clip y en la ventana efectiva (B3), y en velocidad (P6: ρ = −0.83 entre duración y velocidad estimada).
- **EM vs Riesgo**: 102 de 154 aciertos entre las predicciones EM/Riesgo (66.2 %), frente a 70.8 % de EM; recall de Riesgo 20/55 (36.4 %); 6 de 11 videos de Riesgo acertados ≤1 de 5 repeticiones. No se demuestra discriminación entre esas clases por encima de la proporción de clase. Esto es consistente con el F1 0.378 de Riesgo y con las advertencias ya presentes en producción.

### 5.4 Ablaciones y robustez existentes

- Ablación por ramas (136 videos históricos): solo características 0.7976, solo secuencia 0.8823, ambas 0.8445. Es del modelo antiguo, no del candidato V4; en ese experimento ambas ramas no superaron a la secuencia sola.
- Normalización FPS/resolución (86 videos normal/Parkinson, V3): los metadatos conservaron F1 0.96 y el DL pasó de 0.961 a 0.949. No es V4.
- M3 (corrección de aspecto + escala alternativa) rindió F1 0.7505 ± 0.0265 frente a 0.7252 ± 0.0143 de M1 base (sin BN). Un desempeño similar tras corregir aspecto y escala **es compatible con que la red no dependa solo de esa distorsión**, sin excluir otros atajos.
- No existe ninguna prueba de robustez del candidato congelado frente a iluminación, compresión, FPS o resolución, ni una ablación temporal.

## 6. Hallazgos

Detalle completo, con líneas, evidencia, consecuencia, gravedad y solución, en `HALLAZGOS.csv` (32 filas). Resumen:

### A. Errores de implementación confirmados

| ID | Hallazgo | Archivo:línea | Gravedad |
|---|---|---|---|
| A1 | El espejo no invierte el signo de las velocidades en x: `_POS_X_IDX` busca nombres que terminan en `_x` y los de velocidad terminan en `_vx` | `deep_common.py:352, 420-423` | Media |
| A2 | La escala de las 36 características es la mediana de {ancho hombros, ancho caderas, tronco} y coincide con el ancho de hombros aparente; la secuencia usa otra escala | `video_training_common.py:509-524`; `deep_common.py:233` | Alta |
| A3 | Nueve características de «balanceo de brazos» y rangos verticales usan coordenadas absolutas y miden recorrido global (ρ = 0.88 con el recorrido horizontal en laboratorio) | `video_training_common.py:681-690, 761-787` | Alta |
| A4 | Sin corrección de aspecto: x/W, y/H (M1 y candidato) | `deep_common.py:229-243`; `build_dataset_v4_preview.py:139` | Alta |
| A5 | La aumentación temporal deja velocidades y características incoherentes con las posiciones | `deep_common.py:397-417` | Media |
| A6 | `step_regularity_score` mezcla dos definiciones | `video_training_common.py:733-738` | Baja |
| A7 | Redundancias: cadencia = 60·frecuencia, `shoulder_width_mean` ≈ 1 por construcción | `697-698, 788` | Baja |
| A8 | Movimiento por paso de muestreo sin dt; fps visual con cuadros válidos | `557-561, 659` | Baja (mitigado por rejilla de 15 fps) |

Ninguno de estos hallazgos invalida las métricas OOF como mediciones de lo que se hizo: el protocolo no tiene fuga conocida (D4). Lo que afectan es **qué significan las entradas** y **qué puede estar aprendiendo la red**.

### B. Riesgos metodológicos demostrados

| ID | Hallazgo | Gravedad |
|---|---|---|
| B1 | Colinealidad total entre resolución/vista/cámara y el supergrupo de clases | Crítica |
| B2 | Sondas de metadatos superan al candidato con las mismas particiones | Alta |
| B3 | La ventana analizada difiere por clase (normales 3.9 s frente a 5.03 s) y entra en la secuencia y en el conteo de pasos | Alta |
| B4 | La validación es por sujeto, no por fuente; 97.4 % de las predicciones conserva el supergrupo | Alta |
| B5 | EM vs Riesgo débil: 66.2 % frente a 70.8 % de proporción de clase | Alta |
| B6 | Pocos sujetos (7 en Parkinson) y 27 grupos provisionales | Alta |
| B7 | Sondas con imputación y codificación globales | Media |
| B8 | Las 36 características solas rinden por debajo de metadatos y candidato; no hay ablación comparable por rama en V4 | Media |
| B9 | El candidato depende de recalibración BN con estadísticas del dataset y 1/2 videos externos | Media |
| B10 | 19 de 36 características muy asociadas a la relación de aspecto (confundida con la clase) | Media |

### C. Hipótesis que requieren pruebas

C1 (duración como atajo), C2 (escala dependiente de vista), C3 (picos de ruido en pasos y cadencia), C4 (degradación de pose en baja resolución), C5 (duplicados entre clases y grupos provisionales), C6 (diferencia de segmentación entre entrenamiento y producción), C7 (temperatura calibrada antes de recalibrar BN).

### D. Componentes correctamente implementados

D1 (entradas), D2 (equivalencia entrenamiento-producción), D3 (normalización de la secuencia), D4 (CV sin fuga y BN con solo TRAIN), D5 (rejilla de 15 fps), D6 (corrección de fuga de duración en cadencia), D7 (escalador por fold).

## 7. Respuestas a las ocho preguntas

**1. ¿El modelo V4 recibe realmente información del movimiento corporal?**
Sí. Todas sus entradas derivan de landmarks de pose; no recibe píxeles, nombres ni metadatos. Pero esas entradas **también contienen** información de adquisición: relación de aspecto (A4), ángulo de vista vía escala (A2), duración efectiva del tramo (B3), recorrido global y posiblemente movimiento de cámara (A3) y huecos de pose interpolados. Recibir información del cuerpo no implica que la use de forma exclusiva.

**2. ¿Hay errores comprobados en la implementación?**
Sí: A1–A8, de gravedad entre baja y alta. La más seria es que varias características no significan lo que dicen (A2, A3) y que no hay corrección de aspecto (A4). No se encontró fuga de sujetos ni diferencia entre el preprocesamiento de entrenamiento y el de producción.

**3. ¿Qué características pueden introducir información de la grabación?**
Con evidencia de código y datos: `arm_swing_mean`, `left/right_arm_range`, `arm_swing_asymmetry`, rangos verticales de tobillo y rodilla (coordenadas absolutas), `shoulder_width_mean` y `hip_width_mean` (vista) y `estimated_step_count` (ventana). Con riesgo teórico sensible a escala, aspecto y vista: las 14 características de velocidad y movimiento por articulación, `gait_variability`, `motion_smoothness` y los ángulos de tronco. Las menos expuestas son las asimetrías y `trunk_sway_*`.

**4. ¿Existe evidencia de que el modelo dependa principalmente de esas características, o solo indicios de sesgo del dataset?**
Solo indicios de sesgo del dataset y de disponibilidad de atajos. Lo demostrado es que (a) el dataset confunde clase con grabación, (b) clasificadores simples sobre metadatos obtienen F1 0.78–0.86 y (c) el candidato conserva el supergrupo en 97.4 % de las predicciones. No hay ninguna prueba que mida si cambiar un factor de grabación manteniendo el movimiento cambia la predicción. El resultado de M3 (aspecto y escala corregidos, F1 similar) apunta a que no depende solo de esa distorsión, pero no es concluyente. **No hay evidencia ni a favor ni en contra de que la dependencia sea principal.**

**5. ¿Qué podemos comprobar con los 117 videos actuales?**
- Sensibilidad del modelo congelado (o de los 25 checkpoints de fold) a cambios coherentes de dinámica temporal, brillo, compresión, resolución y FPS (inferencia).
- Importancia de características por grupos, por permutación dentro de estrato (inferencia con checkpoints OOF).
- Contraste cinemático entre Normal y Parkinson (dentro de laboratorio) y entre EM y Riesgo, controlando duración, vista y relación de aspecto, solo desde `pose_cache`.
- Sondas con preprocesamiento dentro de fold.
No se puede comprobar con ellos: generalización a fuentes nuevas, separación fuente-clase en el par laboratorio/no laboratorio, ni validez clínica de las etiquetas.

**6. ¿Qué pruebas específicas debemos ejecutar primero?**
Orden en `PLAN_PRUEBAS_V4.md`. Resumen: (1) Prueba D, que no requiere inferencia; (2) Prueba A con controles temporales coherentes y ventanas equiparadas; (3) Prueba C con los checkpoints OOF; (4) Prueba B, que requiere reextraer pose de videos degradados.

**7. ¿Es necesario corregir el código o reentrenar, o todavía no existe evidencia suficiente para justificarlo?**
- **Reentrenar el candidato actual para «arreglar» sesgo: todavía no hay evidencia que lo justifique.** No se ha demostrado que la red dependa de los atajos.
- **Corregir el código: sí es necesario antes de cualquier reentrenamiento futuro**, porque A1–A5 son defectos demostrables que cualquier nuevo modelo heredaría (espejo, escala, coordenadas absolutas, aspecto, aumentación). Esas correcciones no cambiarían el modelo desplegado ni sus resultados históricos.
- Conviene correr antes las Pruebas D y A: dirán si vale la pena reconstruir las características con ventana igualada, escala robusta y coordenadas relativas.
- Lo que sí justifica recolectar datos ya es B1: no se puede corregir con código.
- La interfaz podría ajustar de inmediato el texto de los conceptos «movimiento de brazos» y «amplitud» (A3), sin tocar el modelo; no se modificó nada en esta auditoría.

**8. ¿Qué tan defendible es el modelo actual como prototipo técnico y cuáles son sus limitaciones?**
Defendible como **prototipo técnico** de un pipeline completo: extracción de pose normalizada, red de dos ramas, validación agrupada por sujeto con selección anidada, recalibración de BN solo con TRAIN, auditorías de sesgo y advertencias en producción. Es metodológicamente honesto: las propias auditorías previas declaran el carácter experimental.
No es defendible como evidencia de que la red aprende patrones clínicos de marcha ni como clasificador de fuentes nuevas. Limitaciones centrales: colinealidad clase-grabación (B1); Riesgo de caída sin discriminación demostrada frente a EM (B5); 7 sujetos con Parkinson; etiquetas sin validación clínica individual; validación externa de 2 videos; entradas con defectos de definición (A2–A4). La única evidencia limpia de señal cinemática es Normal vs Parkinson dentro del laboratorio, y aun ahí hay diferencias de duración de clip y de ventana (B3).

## 8. Limitaciones de esta auditoría

- No se ejecutaron modelos ni se recalcularon sondas; los valores de P12/P18 se tomaron de los resúmenes archivados.
- Las correlaciones de Spearman por característica son descriptivas y están confundidas con la clase.
- Los números de línea corresponden a los archivos tal como están hoy en el repositorio.
- `22_source_bias.py`, `audit_shortcuts_v4.py`, `bn_recal.py` y `build_candidate.py` se citan por sus resúmenes y líneas documentadas en el informe de evidencia previo; `22_source_bias.py`, `bn_recal.py` y `build_candidate.py` no se releyeron línea a línea en esta sesión.
- No se verificó la existencia de los 25 checkpoints de fold (`models_cv/`) ni de `pose_cache/` en disco; el plan de pruebas lo comprueba como primer paso.

## 9. Archivos de esta carpeta

- `INFORME_AUDITORIA_V4.md` (este archivo)
- `CARACTERISTICAS_36.csv`
- `HALLAZGOS.csv`
- `TRAZABILIDAD_CODIGO.csv`
- `PLAN_PRUEBAS_V4.md`
- `RESUMEN_PARA_TESIS.md`
