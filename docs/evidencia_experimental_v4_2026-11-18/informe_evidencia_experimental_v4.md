# Evidencia experimental del aprendizaje de marcha y del sesgo de grabación en V4

Fecha: 18 de noviembre de 2026. Repositorio: `C:\Users\fnahu\Desktop\GITMarcha\AnalisisMarcha`.

Modelo de interés: `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`.

## 1. Respuesta a la pregunta de investigación

**Los resultados existentes apoyan la presencia de señal cinemática, especialmente velocidad en normal/Parkinson bajo el protocolo de laboratorio, pero no demuestran que el candidato V4 sea independiente de fuente, resolución, iluminación o vista. Hay evidencia cuantitativa importante de confusión entre clase y condiciones de grabación.**

La red recibe secuencias de pose y 36 características, no fotogramas RGB ni la columna de origen como entrada explícita. Esto reduce la exposición directa al fondo, pero no evita que la perspectiva, el seguimiento de pose, el tiempo observado o el movimiento de cámara afecten esas entradas. Un buen rendimiento agrupado por sujeto tampoco elimina la confusión entre fuente y clase cuando las fuentes se repiten entre entrenamiento y prueba.

El 89,71 % de `22_source_bias.py` es una **sonda histórica** sobre 136 videos; no es una evaluación del candidato V4 ni una medición de cuánto del rendimiento de la red proviene de metadatos. La evidencia más pertinente está en las sondas de P12 sobre los mismos 117 videos y particiones del V4.

## 2. Origen verificable del resultado cercano al 90 %

Archivo de resultado: `models/gait_deep/audit/source_bias_report.json`, localizador `sondas_solo_metadatos.4_clases.rf.accuracy = 0.8971`.

Datos: `data/video_training/deep/dataset.npz`, cargado mediante `deep_common.load_dataset()` sin ruta alternativa. El CSV de evidencia `models/gait_deep/audit/video_technical_metadata.csv` contiene los mismos 136 nombres e IDs de grupo que ese NPZ. Se verificó esa correspondencia sin regenerar características.

- 136 videos: 59 normales, 28 Parkinson, 29 EM y 20 riesgo de caída; 86 grupos por `subject_id`.
- Etiquetas: `y` del NPZ; nombres y orden `normal`, `parkinson`, `esclerosis_multiple`, `riesgo_caida`.
- Las fuentes A/B son agrupaciones definidas a partir de esas clases: A = normal/Parkinson y B = EM/riesgo. No son IDs de procedencia primaria independientemente acreditados.
- Partición: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`; cada video recibe una predicción fuera de fold. Las métricas se calculan sobre el conjunto de predicciones OOF, no promediando los cinco porcentajes de fold.
- RF: 400 árboles, profundidad máxima 6, `class_weight=balanced_subsample`, `random_state=42`.
- Regresión logística: `max_iter=3000`, `class_weight=balanced`, `C=0.5`.
- En cada fold se ajustan una imputación por mediana y un escalado estándar, dentro de un `Pipeline`, usando únicamente su TRAIN.
- El script no guarda una configuración separada: parámetros y partición están en `grouped_probe()`. El JSON y el CSV son sus salidas principales. El JSON no incluye un vector de predicciones OOF individuales ni una desviación entre repeticiones; no se inventan esos valores.

### Las 15 variables exactas

`width`, `height`, `aspect_ratio`, `fps`, `frame_count`, `duration_s`, `brightness_mean`, `brightness_std`, `sharpness_lap_var`, `saturation_mean`, `edge_density`, `person_bbox_height_frac`, `person_bbox_width_frac`, `valid_seq_frames`, `pose_rate`.

Las primeras seis son propiedades técnicas; cinco son resúmenes fotométricos de hasta 12 cuadros distribuidos por el archivo; dos describen el encuadre obtenido de landmarks y dos describen extracción/calidad de pose. Por ello, es una sonda de **metadatos y proxies de adquisición/pose**, no una sonda exclusivamente de resolución o iluminación. No recibe las 36 características cinemáticas ni secuencias temporales completas. Duración, encuadre y calidad pueden, aun así, relacionarse con el movimiento del sujeto.

### Métricas históricas realmente archivadas

| Tarea histórica | Clasificador | Exactitud | Exactitud balanceada | Macro-F1 |
|---|---|---|---|---|
| 4_clases | logreg | 0.8676 | 0.8250 | 0.8273 |
| 4_clases | rf | 0.8971 | 0.8598 | 0.8629 |
| fuente_A_vs_B | logreg | 1.0000 | 1.0000 | 1.0000 |
| fuente_A_vs_B | rf | 1.0000 | 1.0000 | 1.0000 |
| normal_vs_parkinson_solo_fuenteA | logreg | 0.9540 | 0.9380 | 0.9463 |
| normal_vs_parkinson_solo_fuenteA | rf | 0.9655 | 0.9558 | 0.9601 |
| EM_vs_riesgo_solo_fuenteB | logreg | 0.7755 | 0.7638 | 0.7658 |
| EM_vs_riesgo_solo_fuenteB | rf | 0.8163 | 0.8060 | 0.8083 |


RF produce exactitud 0,8971, exactitud balanceada 0,8598 y macro-F1 0,8629 para cuatro clases. No deben intercambiarse estas tres métricas. El `chance_level=0.25` del script es una referencia uniforme de cuatro clases; la proporción de la clase mayoritaria es 59/136 = 0,4338. No se debe presentar 25 % como exactitud de la regla mayoritaria.

**Alcance de la verificación:** se localizaron el generador, sus parámetros, sus entradas y el valor archivado. No hay predicciones OOF individuales de esta sonda entre los resultados localizados; por tanto, no se recalculó independientemente su 0,8971. Se conserva como resultado experimental archivado, no como una nueva ejecución. Los videos antiguos de EM/riesgo fueron reemplazados posteriormente, a veces reutilizando nombres: ejecutar hoy el script podría leer archivos distintos de los de aquella auditoría.

El texto interpretativo del script que dice que las sondas dentro de fuente «deberían» acercarse al azar es una expectativa, no el resultado: RF alcanzó 0,9655 de exactitud dentro de A y 0,8163 dentro de B. No es correcto citar esa expectativa como si hubiera sido observada.

## 3. Comparabilidad metodológica con V4

| Aspecto | Sonda histórica P22 | V4, protocolo V2 y BN-B |
|---|---|---|
| Colección | 136 videos, 86 grupos; EM/riesgo antiguos | 117 videos, 67 grupos; selección y colección V4 |
| Distribución | 59 / 28 / 29 / 20 | 58 / 26 / 22 / 11 |
| Agrupación | `subject_id` histórico | `split_group` del V4; parte de los grupos es provisional |
| CV externa | 5 folds, una semilla 42 | 5 folds, cinco semillas 42–46 |
| Selección del DL | No aplica a la sonda | Tres folds internos para época y temperatura; ajuste externo con E* fijo |
| Entradas | 15 metadatos/proxies | Pose [68,96] y 36 características; sondas de 7 metadatos y 11 campos mixtos |
| Agregación | Un resultado OOF global | Un resultado OOF global por semilla; media y DE muestral de cinco repeticiones |
| Separación por fuente | No; agrupar por sujeto mantiene dominios compartidos | Tampoco; los test externos son por sujeto, no por fuente de adquisición |

**Conclusión:** no se resta ni se compara directamente «89,71 % frente al porcentaje del V4» para medir mejora, deterioro o aprendizaje de marcha. Cambian datos, agrupaciones y protocolo. La comparación pertinente usa las sondas del propio P12, que comparten el orden de los 117 videos, etiquetas, grupos, semillas y test externos con M1/M3. Se reconstruyeron sus 25 listas de sujetos de prueba y coinciden con `partitions_outer_test_subjects.csv`.

### Comparación interna disponible para V4

Media ± DE muestral entre cinco repeticiones. Cada repetición reúne 117 predicciones OOF de cinco folds.

| Entrada / procedimiento | Exactitud OOF | Macro-F1 OOF |
|---|---|---|
| M1 base: secuencia + características | 0.8342 ± 0.0097 | 0.7252 ± 0.0143 |
| M1 + BatchNorm B: procedimiento del candidato | 0.8513 ± 0.0097 | 0.7442 ± 0.0104 |
| M3: preprocesamiento experimental c3 + bs5 | 0.8444 ± 0.0237 | 0.7505 ± 0.0265 |
| Sonda: 7 metadatos técnicos (LR) | 0.8632 ± 0.0181 | 0.7773 ± 0.0288 |
| Sonda: 7 metadatos técnicos (RF) | 0.8769 ± 0.0143 | 0.7864 ± 0.0234 |
| Sonda: metadatos + estrato/vista/fondo (LR) | 0.9060 ± 0.0060 | 0.8585 ± 0.0120 |
| Sonda: metadatos + estrato/vista/fondo (RF) | 0.8889 ± 0.0105 | 0.8250 ± 0.0203 |
| Referencia: 36 características (LR) | 0.7521 ± 0.0160 | 0.6222 ± 0.0282 |
| Referencia: 36 características (RF) | 0.7590 ± 0.0273 | 0.6359 ± 0.0372 |


La sonda técnica usa exactamente siete campos: `video_duration_s`, `src_frame_count`, `src_fps`, `width`, `height`, `aspect_ratio`, `file_size_mb`. La sonda mixta agrega `orientation`, `source`, `view`, `background_motion_15fps` (11 campos antes de codificar categorías). Por ello, el 90,60 % de exactitud de la sonda mixta LR **tampoco debe llamarse «solo resolución» ni confundirse con el 89,71 % histórico**.

RF técnico registra macro-F1 0,7864, frente a 0,7442 del procedimiento BN-B. La sonda mixta LR registra 0,8585. Son resultados medidos bajo los mismos test externos y evidencian que condiciones de adquisición permiten predecir las etiquetas. **No estiman una fracción causal de sesgo ni prueban que el modelo use exactamente esas variables.** No se declara significación estadística de diferencias entre clasificadores.

Limitaciones de comparabilidad que permanecen:

1. Son algoritmos e hiperparámetros distintos. P12 usa RF de 300 árboles, `min_samples_leaf=2`, y LR con C por defecto (1), distintos de los parámetros del P22 histórico. Los hiperparámetros de las sondas son fijos; el DL tiene selección interna de época/temperatura.
2. `audit_shortcuts_v4.py::design()` imputa medianas y ajusta el codificador categórico sobre todo el conjunto antes de dividirlo; las referencias de 36 características también imputan globalmente. Esto puede introducir información distributiva del test. No se ha modificado ni corregido. La comparación es una auditoría interna con esta limitación, no una prueba completamente aislada de principio a fin. Las siete variables técnicas de los 117 registros están presentes en la tabla de muestras; la advertencia de imputación global afecta especialmente a entradas con valores no finitos.
3. `source` se construye mediante reglas heurísticas de clase/formato/orientación en `build_manifest_v4.py::source_of()`. No es una etiqueta independiente y certificada de origen. Las sondas mixtas miden separabilidad de esos estratos y deben leerse con esa dependencia.
4. BN-B se evaluó históricamente en los mismos folds recalibrando **solo con TRAIN**. Se verificaron los 25 controles guardados sin intersección con test. Su OOF evalúa el procedimiento de construcción del candidato, no aplica los pesos finales congelados a nuevos pacientes externos.
5. Las cinco repeticiones reutilizan videos y sujetos: 585 predicciones no son 585 videos ni observaciones independientes. Las DE de las figuras no son intervalos de confianza clínicos.

## 4. Experimentos de mitigación, ablación y robustez localizados

### 4.1 Normalización real de FPS y resolución: antecedente V3

`24_normalized_reextract.py::extract_normalized()` selecciona cuadros secuencialmente a 15 fps y reduce la dimensión máxima a 720 px. No hace un recorte común ni iguala el punto de vista o la iluminación. Conserva la relación de aspecto, que puede seguir codificando diferencias entre dominios.

La comparación controlada de `shortcut_learning_normalized_report.json` corresponde a **86 videos normal/Parkinson, 37 grupos**, no al candidato de 117. Se verificó la igualdad de video→grupo/etiqueta tras alinear por nombre: los NPZ tienen distinto orden inicial, pero el script los realinea antes de comparar. El CSV normalizado registra 15 fps y 720×405 en los 86.

| Brazo V3 | Macro-F1 antes | Macro-F1 después |
|---|---:|---:|
| Metadatos, mismas 9 columnas, LR | 0,9644 ± 0,0064 | 0,9599 ± 0,0000 |
| Metadatos, mismas 9 columnas, RF | 0,9649 ± 0,0061 | 0,9606 ± 0,0000 |
| 36 características, LR | 0,9471 ± 0,0104 | 0,9556 ± 0,0061 |
| 36 características, RF | 0,9044 ± 0,0120 | 0,9500 ± 0,0129 |
| DL completo | 0,9609 ± 0,0103 | 0,9485 ± 0,0205 |

Los valores son media ± DE poblacional de tres semillas, tal como los genera `23_experiments.py`. No se mezclan con la DE muestral de P12. Se usaron las mismas nueve columnas antes/después, evitando atribuir a la normalización un cambio causado por retirar variables fotométricas.

La normalización no eliminó la capacidad predictiva de esos metadatos en ese experimento. Esto no demuestra que normalizar sea inútil ni que el descenso del DL sea significativo; solo delimita el resultado observado en esa colección binaria.

### 4.2 Ablaciones anteriores

- En los mismos 86 videos, `shortcut_learning_metadata_ablation_report.json` guarda RF con macro-F1 0,9649 usando nueve variables, 0,9563 retirando encuadre/pose y 0,9515 usando únicamente duración y número de cuadros. Es evidencia de separabilidad del par normal/Parkinson por longitud del clip, no prueba de un mecanismo exclusivamente artificial.
- `experiments_report_final.json` conserva ablaciones del modelo histórico de 136 videos: solo rama de características 0,7976 ± 0,0252, solo secuencia 0,8823 ± 0,0059 y ambas ramas 0,8445 ± 0,0479 de macro-F1. Hay además `experiments_report_norm_final.json`. No son ablaciones del candidato V4. El resultado de ambas ramas no supera a secuencia sola; no sustenta afirmar que la combinación siempre aporta una mejora.
- Existe `experiments_report_SUPERSEDED_nondeterministic.json`, marcado explícitamente como sustituido/no determinista. No se utiliza como evidencia principal.
- La referencia de 36 características de P12 es LR/RF; no equivale a una ablación controlada de la rama temporal de la misma red del candidato. No se localizó esa ablación específica del candidato bajo el protocolo V2.

### 4.3 Resolución, relación de aspecto y ventana en precursores/V4

- El precursor `dataset_v4_ms28_window_p75.npz` contiene 114 videos, 65 grupos y tres clases. La sonda de ancho+alto+AR produce macro-F1 0,5553 (LR) y 0,5675 (RF), frente a 0,2249 del baseline mayoritario. Son **medias de métricas de cinco folds**, no una media de cinco repeticiones OOF. No son comparables directamente con P12.
- P5 probó control, corrección de coordenadas c3, escala corporal bs5 y su combinación, más ventanas de 3,4 y 4,0 s. En la combinación c3+bs5, la correlación AR–movimiento horizontal centrada por clase pasó de 0,104 a 0,025, pero la global pasó de 0,747 a 0,762. Esto apoya la reducción de un componente geométrico en ese diagnóstico; no elimina la confusión de composición entre clase y estrato.
- La referencia del Paso 4 de 36 características pasó de macro-F1 RF 0,6349 a 0,8004 en la variante A. Otras columnas de `comparison_control_vs_variants_step5.csv` proceden de otra batería con distinta agregación; no se mezclan sus 0,8001 y 0,8004 como si fueran la misma corrida.
- M3 de P12 usa esa variante y alcanza 0,7505 ± 0,0265; se mantuvo como experimento secundario y no se adoptó para el candidato M1. No se puede atribuir al candidato una transformación que no recibió.
- Las ventanas menores reducen parte de la señal de duración efectiva, pero no hacen iguales las duraciones reales ni garantizan el mismo número de ciclos observados. No se localizó una prueba factorial del candidato congelado frente a varias resoluciones, FPS, iluminaciones o ángulos manteniendo cada contenido constante.

### 4.4 Dentro de estrato no equivale a validación dejando una fuente fuera

El análisis P5 incluye laboratorio completo (84 videos/37 grupos), laboratorio a 30 fps (64/31), laboratorio a 50 fps (20/9, **cuatro folds** por disponibilidad de grupos) y redes verticales (25/25). Son sondas LR/RF repetidas con semillas **0,1,2**. El subgrupo clínico EM/riesgo (8 videos/5 grupos) tiene un solo grupo EM: el código lo marca inconcluso, sin ejecutar una CV válida (`n_splits=1`).

En redes verticales, la sonda de 36 características del control dio LR macro-F1 0,460; su prueba de permutación por grupo archivada dio p=0,6517 (200 permutaciones), frente a media nula 0,502 y percentil 95 de 0,721. No se rechaza esa referencia nula. No debe compararse macro-F1 automáticamente con 0,5 de exactitud aleatoria en datos desbalanceados.

`social_vertical` agrupa teléfonos, lugares, cuentas y formatos diferentes: es un estrato técnico, no una única fuente de adquisición controlada. No se localizó un leave-one-source-out completo del candidato con presencia de las cuatro clases en cada fuente. La matriz de cobertura muestra 84 videos normal/PD en laboratorio, 25 EM/riesgo en redes verticales y 8 EM/riesgo en el estrato clínico. Ese diseño impide separar plenamente fuente y clase.

### 4.5 Duración frente a velocidad: evidencia a favor de señal de marcha

El P6 midió 84 videos normal/Parkinson, desde pose ya almacenada, en el protocolo de cruce lateral del laboratorio. Sus CSV guardan medianas de velocidad de 2,232 y 0,7995 longitudes de tronco/s y recorridos de 7,4345 y 7,5305 longitudes de tronco, respectivamente. Se recalculó la correlación de Spearman desde esas filas: ρ = -0.8309, consistente con el valor histórico redondeado.

También existe una sonda de velocidad sola en `d3_summary.json` que alcanzó macro-F1 1,000 con LR y RF. Es una sonda cinemática auxiliar de ese subconjunto, **no un resultado del candidato**. Las velocidades estimadas no se solapan entre clases y proceden de 37 grupos; no demuestran qué patrón utiliza la red ni un biomarcador clínico generalizable. La estimación depende del punto de vista y de una normalización corporal, y no está calibrada en m/s.

Por tanto, la alta separabilidad por duración puede contener señal de lentitud de marcha bajo un recorrido fijo. No es defendible afirmar, solo a partir del baseline de duración, que toda esa señal es un error de protocolo. Tampoco se demuestra que sea puramente clínica: existen tiempos de entrada/salida, falta una comparación a velocidades solapadas y las etiquetas no tienen validación clínica individual acreditada.

El JSON `d1_speed_explains_duration.json` registra R²=0,880 y R²=0,885 al agregar clase. Se encontró el archivo y su mención en D1, **pero no el script que genera esos ajustes** en los archivos consultados. Se documenta como resultado archivado de trazabilidad incompleta y no se usa como prueba causal ni en las figuras principales. No se ajustó una nueva regresión.

### 4.6 Cámara, fondo, iluminación y vista

La medición original `camera_motion_norm` usa correlación de fase de todo el cuadro entre imágenes nativas, sin excluir al sujeto. P6 mostró que en el laboratorio se relaciona con movimiento de la persona y FPS; llamarla «movimiento puro de cámara» sería incorrecto.

P6/P7 midieron fondo mediante Lucas-Kanade, excluyendo una caja de la persona y usando 15 fps. En el laboratorio, fondo mediana+p90 dio macro-F1 0,566 (LR) y 0,590 (RF), mucho menor que la sonda de velocidad. Esto apoya que aquel indicador original no era evidencia suficiente de cámara móvil en el laboratorio.

Sin embargo, P7 sobre los 117 registra macro-F1 RF **0,6527 con fondo** y **0,6691 con fondo+vista**; la sonda de imagen (brillo/saturación/nitidez/bordes) y la de vista también conservan capacidad predictiva. Estos resultados corresponden a sondas de tres semillas 0,1,2, no al procedimiento de cinco repeticiones del candidato. Evidencian asociación entre clase y grabación, no sensibilidad causal del candidato a cambiar una variable manteniendo lo demás fijo. Los CSV y JSON conservan los resultados completos en `tabla_resultados_verificados.csv`.

La configuración incluye augmentation de secuencias (recorte/interpolación temporal, desplazamiento, escala, ruido y espejo). Es una medida de entrenamiento, **no una evaluación medida de robustez del candidato** frente a iluminación, perspectiva o diferentes cámaras. No se localizó una curva de degradación controlada de esas variables sobre el modelo congelado.

### 4.7 Resultados del modelo por estrato y externos

La auditoría P13 de M1 base registra exactitud descriptiva 0,931 en laboratorio, 0,656 en redes verticales y 0,375 en el estrato clínico. Se reprodujeron esos conteos a partir de predicciones guardadas; además se reagruparon, sin inferencias nuevas, las predicciones BN-B:

| Estrato | Videos / grupos | M1 base: aciertos/OOF | BN-B: aciertos/OOF |
|---|---|---|---|
| Laboratorio | 84 / 37 | 391/420 (0.9310) | 396/420 (0.9429) |
| Redes verticales | 25 / 25 | 82/125 (0.6560) | 85/125 (0.6800) |
| Clínico 848×478 | 8 / 5 | 15/40 (0.3750) | 17/40 (0.4250) |


Es una estratificación descriptiva del test interno: composición de clases, tamaño y dificultad difieren entre estratos. No aísla un efecto causal de fuente ni constituye una fuente externa retenida.

P19 conserva dos videos externos con etiqueta conocida por nombre, no clínicamente acreditada. El candidato acertó `EXT_PD_001` horizontal y predijo riesgo para `EXT_PD_002` vertical: **1/2 descriptivo**. El modelo base había fallado ambos. Dos videos de una clase no validan generalización, ni permiten atribuir el error del segundo exclusivamente a orientación. El 0,983 de exactitud sobre los 117 del candidato es **resustitución**, y queda excluido de las figuras de generalización.

## 5. Qué puede y qué no puede afirmarse

| Afirmación | Juicio sustentado por los archivos |
|---|---|
| Existe información cinemática discriminativa | Sí, descriptivamente en el laboratorio: velocidad y características de pose discriminan normal/PD. |
| La duración es solo un artefacto sin relación con marcha | No demostrado; D1 encuentra asociación con velocidad en un recorrido aproximadamente común. |
| La red V4 aprende exclusivamente patología de marcha | No demostrado; falta aislar factores y las etiquetas clínicas no están acreditadas individualmente. |
| Las características de grabación predicen etiquetas V4 | Sí; sondas técnicas/mixtas y de fondo/vista lo cuantifican. |
| La red utiliza los metadatos que utiliza el RF | No demostrado por esa comparación; una sonda fuerte mide disponibilidad de un atajo, no su uso causal por la red. |
| 15 fps y ≤720 px eliminan el sesgo de fuente | No demostrado; la normalización V3 no eliminó la separabilidad por metadatos y en V4 persisten asociaciones. |
| Validación por sujeto equivale a validación por fuente | No; el mismo dominio puede estar en TRAIN y TEST de sujetos distintos. |
| BatchNorm recalibrado elimina el sesgo de fuente | No; mejora el OOF, pero no introduce datos cruzados entre fuentes ni una prueba causal de invariancia. |
| El candidato es robusto a otra iluminación, cámara o ángulo | No demostrado con las pruebas controladas localizadas. |
| Los dos externos validan clínicamente el modelo | No; muestra insuficiente y etiquetas no acreditadas. |

## 6. Pruebas nuevas propuestas, no ejecutadas

1. **Evaluación externa cruzada por fuente y clase.** Requiere videos con etiquetas clínicas documentadas, IDs de sujeto y adquisición, varias fuentes independientes y presencia de cada clase en varias fuentes. Congelar candidato y protocolo antes de observar resultados. Evaluar por sujeto y fuente totalmente nuevos, reportando macro-F1, recall por clase, calibración y variación entre fuentes. Demostraría transferencia a las fuentes retenidas; un resultado negativo mediría un fallo de transferencia. El V4 actual no permite una versión completa por falta de cobertura clase×fuente. Si se quisiera entrenar modelos por exclusión de fuente, requeriría autorización adicional de entrenamiento.
2. **Perturbaciones pareadas del candidato congelado.** Requiere originales o copias de evaluación y una rejilla predefinida de resolución, FPS, compresión e iluminación, manteniendo el contenido y sujeto. Reextraer pose y ejecutar el candidato sin actualizar pesos. Medir cambios de clase, caída de macro-F1/recall y alteración de pose por video. Mostraría sensibilidad a esas perturbaciones; no demostraría invariancia a fuentes reales no representadas. Para ángulo/perspectiva, preferir grabaciones sincronizadas multivista: girar una imagen no reproduce una nueva cámara. Esta prueba implica nuevas inferencias y no se ejecutó.
3. **Prueba temporal controlada.** Requiere las secuencias de evaluación y controles coherentes (por ejemplo, orden temporal alterado o ventanas con duración/ciclos equiparados), diseño fijado y evaluación por sujeto. El candidato congelado puede medir dependencia de dinámica temporal mediante nuevas inferencias. Una ablación de ramas comparable requeriría modelos reentrenados con el mismo protocolo V2; tampoco está autorizada ni se ejecutó. Una caída ante desorden temporal mostraría uso de dinámica, sin certificar especificidad clínica.
4. **Sondas con preprocesamiento estrictamente dentro de fold.** Requiere las tablas ya existentes y particiones guardadas. Ajustar imputadores/codificadores solo en TRAIN, guardar predicciones OOF y comparar el mismo conjunto de videos/semillas. Aislaría el posible efecto de preprocesamiento transductivo en las sondas. Es un entrenamiento nuevo de clasificadores auxiliares y no se realizó.

No se iniciará ninguna de estas pruebas sin una solicitud posterior que autorice su alcance.

## 7. Localización exacta del código original

Las líneas corresponden a los archivos locales inspeccionados; sus SHA-256 están en `sha256_fuentes.csv`. El mapa completo contiene 119 funciones/declaraciones/escrituras, con inicio y final. Los CSV de resultados conservan localizadores de campos JSON o filas/columnas de CSV.

| Resultado o etapa | Archivo, función y líneas exactas |
|---|---|
| 15 variables y extracción del sondeo original | `scripts/video_training/deep/22_source_bias.py` — `video_metadata()`, líneas 59–95; `scripts/video_training/deep/22_source_bias.py` — `person_bbox_frac()`, líneas 98–116 |
| Particiones, ajuste y métricas del 89,71 % | `scripts/video_training/deep/22_source_bias.py` — `grouped_probe()`, líneas 119–149 |
| Lectura del dataset y escritura del informe original | `scripts/video_training/deep/22_source_bias.py` — `main()`, líneas 161–251; `scripts/video_training/deep/deep_common.py` — `load_dataset()`, líneas 612–620 |
| Normalización física para extraer pose | `scripts/video_training/deep/24_normalized_reextract.py` — `extract_normalized()`, líneas 55–124 |
| Comparación antes/después en 86 videos | `outputs/dataset_v3/_shortcut_learning_audit_normalized.py` — `main()`, líneas 125–214 |
| Ablaciones de metadatos en V3 | `outputs/dataset_v3/_shortcut_learning_metadata_ablation.py` — `main()`, líneas 125–171 |
| Ablaciones de ramas del modelo histórico | `scripts/video_training/deep/23_experiments.py` — `main()`, líneas 285–370; `scripts/video_training/deep/23_experiments.py` — `_cv_once()`, líneas 205–218 |
| Resolución/AR en el precursor de 114 videos | `outputs/dataset_v4_ms28/_resolution_shortcut_audit.py` — `main()`, líneas 87–255; `outputs/dataset_v4_ms28/_shortcut_learning_audit_preview.py` — `classical_cv_eval()`, líneas 152–217 |
| Reglas heurísticas de estrato/fuente | `outputs/dataset_v4_4class/build_manifest_v4.py` — `source_of()`, líneas 120–126 |
| Imputación y codificación de sondas V4 | `outputs/dataset_v4_4class/audit_shortcuts_v4.py` — `design()`, líneas 146–158 |
| Variantes de coordenadas, escala y ventana | `outputs/dataset_v4_4class/step5/build_variants_step5.py` — `build()`, líneas 79–134 |
| Evaluación dentro de estrato y permutación | `outputs/dataset_v4_4class/step5/within_source_step5.py` — `probe_detail()`, líneas 57–77; `outputs/dataset_v4_4class/step5/within_source_step5.py` — `permutation_test()`, líneas 80–102 |
| Duración, velocidad y correlaciones por video | `outputs/dataset_v4_4class/step6/d1_duration_vs_gait.py` — `per_video()`, líneas 54–122; `outputs/dataset_v4_4class/step6/d1_duration_vs_gait.py` — `main()`, líneas 157–228 |
| Movimiento de fondo con sujeto enmascarado | `outputs/dataset_v4_4class/step6/d2_camera_measurement.py` — `measure()`, líneas 55–150 |
| Sondas duración/velocidad/fondo en laboratorio | `outputs/dataset_v4_4class/step6/d3_combined_shortcut_test.py` — `main()`, líneas 55–140 |
| Sondas de fondo, vista y metadatos en 117 videos | `outputs/dataset_v4_4class/step7/analyze_four_class.py` — `main()`, líneas 72–244 |
| Particiones y ajuste interno del V4 | `outputs/dataset_v4_4class/step12_training/train_protocol_v2.py` — `sgkf()`, líneas 78–79; `outputs/dataset_v4_4class/step12_training/train_protocol_v2.py` — `run_variant()`, líneas 131–185 |
| Sondas comparables de metadatos V4 | `outputs/dataset_v4_4class/step12_training/train_protocol_v2.py` — `probe_oof()`, líneas 188–198; `outputs/dataset_v4_4class/step12_training/train_protocol_v2.py` — `main()`, líneas 229–298 |
| Agregación de métricas V4 | `outputs/dataset_v4_4class/step12_training/train_protocol_v2.py` — `summarize()`, líneas 201–218 |
| Auditoría descriptiva OOF por estrato | `outputs/dataset_v4_4class/step13_audit/audit_oof_m1.py` — `main()`, líneas 52–240 |
| Recalibración BN y OOF solo con TRAIN | `outputs/dataset_v4_4class/step18_bn/bn_recal.py` — `recalibrate()`, líneas 54–77; `outputs/dataset_v4_4class/step18_bn/bn_recal.py` — `oof()`, líneas 158–210 |
| Congelación y evaluación del candidato | `outputs/dataset_v4_4class/step19_candidate/build_candidate.py` — `build()`, líneas 67–122; `outputs/dataset_v4_4class/step19_candidate/build_candidate.py` — `evaluate()`, líneas 144–212 |
| R² duración/velocidad = 0,88 | Solo `step6/d1_speed_explains_duration.json` y referencia en `D1_duration_vs_gait.md`: generador no localizado. No se atribuye una función o línea inexistente. |


Además de los rangos anteriores, `train_protocol_v2.py:267–275` enumera los campos y ejecuta las sondas; `:286–293` guarda los resultados; `bn_recal.py:176–177` aplica BN solo sobre TRAIN y predice TEST; `:195–203` escribe predicciones y controles. `22_source_bias.py:51–56` declara las 15 variables y `:138–144` calcula las métricas. Estas referencias no implican ejecución en esta revisión.

## 8. Títulos y pies para la tesis

**Tabla 4.4.1. Rendimiento fuera de fold de los procedimientos de marcha y las sondas de metadatos sobre el dataset V4 con particiones comunes por sujeto.** Nota: 117 videos, 67 grupos, cinco repeticiones de cinco folds. Se presentan media y DE muestral; las sondas técnicas y mixtas tienen entradas distintas, y la comparación no demuestra dependencia causal de la red. Fuente: resultados P12 y P18 del repositorio.

**Figura 4.4.1. Macro-F1 del V4 y de las sondas de adquisición evaluadas con las mismas particiones externas por sujeto.** Nota: rombos = medias; puntos = cinco repeticiones; barras = ±1 DE muestral, no intervalos de confianza. M3 es experimental. BN-B corresponde al procedimiento del candidato. Fuente: `metrics_protocol_v2.json` y `oof_comparison.json`.

**Figura 4.4.2. Efecto de normalizar FPS y resolución en el experimento binario V3 de normal frente a Parkinson.** Nota: 86 videos/37 grupos, tres semillas, mismos nueve metadatos antes/después; media ± DE poblacional del informe original. No corresponde a V4 ni se compara directamente con la figura anterior. Fuente: `shortcut_learning_normalized_report.json`.

**Figura 4.4.3. Relación observada entre duración del clip y velocidad horizontal estimada de cadera en los videos de laboratorio del V4.** Nota: 84 videos/37 grupos; cada punto es una medición guardada; no se ajustó una regresión nueva. Velocidad en longitudes de tronco/s y etiquetas del dataset. No prueba un mecanismo causal ni un biomarcador clínico. Fuente: `D1_duration_vs_gait.csv`.

## 9. Verificación, límites y entregables

Se leyeron archivos ignorados por Git presentes localmente. Se reconstruyeron las 25 particiones V4, sin ajustar clasificadores. Se recalcularon 50 métricas desde predicciones guardadas de M1/M3/BN y todas coinciden con lo archivado dentro de su redondeo. Las métricas de las sondas históricas y de P12 se extrajeron de sus resúmenes: **no se encontraron sus predicciones OOF individuales entre las salidas revisadas**. Por ello su verificación es documental y de consistencia de agregados, no una reproducción independiente de sus clasificadores.

No se importaron módulos del proyecto, entrenaron clasificadores, ejecutaron inferencias, reextrajeron poses ni procesaron cuadros de video. La agregación de predicciones ya guardadas, las correlaciones descriptivas de mediciones existentes y la reconstrucción de particiones no son experimentos predictivos nuevos. Se verificaron los hashes de los archivos fuente antes y después. El código, los pesos, los datos originales y Word permanecen intactos.

Entregables en esta carpeta: este informe; `texto_tesis_4_4.md`; `tabla_resultados_verificados.csv` (158 valores con protocolo, fuente y localizador); `tabla_4_4_1_comparacion_v4.csv`; tres PNG a 600 dpi; `trazabilidad_codigo_resultados.csv`; `verificacion_metricas_desde_predicciones.csv`; `rendimiento_descriptivo_por_estrato.csv`; `evidencia_extraida.json`; `sha256_fuentes.csv`; `verificacion_final.json`; `SHA256_ENTREGABLES.txt`.
