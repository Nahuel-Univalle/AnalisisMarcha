# Alcance y metodología afectada (propuesta)

## A. Texto nuevo propuesto
### Alcance (apartado de introducción / alcance)
El sistema recibe un video de una persona caminando y entrega una **clasificación experimental de patrones de marcha** en cuatro categorías (normal, Parkinson, esclerosis múltiple y riesgo de caída), con las probabilidades de cada categoría, advertencias sobre la calidad del video, observaciones del movimiento y un informe en PDF. **No constituye un diagnóstico médico** ni sustituye la valoración de un profesional de salud. El análisis se limita a videos de cuerpo completo; cuando el seguimiento corporal es insuficiente, el sistema informa un resultado no concluyente en lugar de clasificar. El alcance del modelo se restringe a los datos disponibles: 117 videos con etiquetas registradas, sin validación clínica individual.

### Población y muestra
El conjunto de referencia contiene **117 videos de marcha**: 58 normales, 26 de Parkinson, 22 de esclerosis múltiple y 11 de riesgo de caída. Los videos se agruparon en **67 grupos técnicos de sujeto** (30, 7, 21 y 9, respectivamente); 27 de esos grupos (20 de esclerosis múltiple y 7 de riesgo de caída) son **provisionales**, porque la fuente no identifica a la persona y se asignó un grupo por video. Por ello los 67 grupos no deben interpretarse como 67 personas verificadas. Se excluyeron 20 videos por pose insuficiente, ausencia de un tramo continuo de marcha o revisión pendiente. Las etiquetas son las registradas por el dataset; ningún video cuenta con validación clínica individual. La fuente de grabación está asociada a la clase (normal y Parkinson, de laboratorio con trípode; esclerosis múltiple, principalmente video vertical de redes sociales; riesgo de caída, de fuentes heterogéneas), lo que constituye una limitación metodológica que el diseño no puede eliminar.

### Técnicas e instrumentos / protocolo de evaluación
La evaluación se realizó mediante validación cruzada de cinco particiones agrupada por grupo técnico de sujeto, repetida con cinco semillas (42 a 46), de modo que ningún grupo aparece a la vez en entrenamiento y prueba. El escalador, la imputación de valores faltantes y la temperatura de calibración se ajustaron únicamente con datos de entrenamiento. Las métricas (exactitud, precisión, sensibilidad, F1 por clase, F1 macro, ECE, Brier) son el promedio de las cinco semillas sobre predicciones fuera de partición; los intervalos de confianza del 95 % se obtuvieron por remuestreo de grupos de sujeto (2000 remuestreos). Las cinco repeticiones reutilizan los mismos 117 videos y no son muestras independientes. El diseño de la versión final se fijó con criterios definidos antes de observar los resultados (pre-registro de V5-C y de V5-CR), reconociendo que los mismos videos sirvieron para diseñar y comparar varias versiones.

## B. Se conserva
La descripción metodológica general (tipo de investigación, enfoque, fases de desarrollo) y las cifras de población que no cambiaron (117 videos, 58/26/22/11, 67 grupos).

## C. Se reemplaza
Cualquier mención a «sujetos» donde corresponda «grupos técnicos de sujeto»; la descripción de las características/ventana de V4; si el texto afirma validación con pacientes reales o identificación temprana demostrada.

## D. Figuras/tablas
`fig_distribucion_dataset`; tabla de `RESUMEN_DATASET_POR_CLASE.csv`.

## E. Fuentes
`03_DATASET_Y_METODOLOGIA/DATASET_Y_METODOLOGIA.md` y `MANIFIESTO_TRAZABILIDAD_117_VIDEOS.csv`; `models/gait_deep_v5cr/…_config.json` (`protocol`); `docs/optimizacion_final_v5_2026-11-19/PREREGISTRO_V5C.md`; `docs/inventario_dataset_v4_2026-11-18/ficha_tecnica_y_fuentes.md`.
