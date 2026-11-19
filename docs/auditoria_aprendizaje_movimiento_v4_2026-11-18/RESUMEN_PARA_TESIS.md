# Resumen académico de la auditoría del modelo V4

Fecha: 18 de noviembre de 2026. Texto para incorporación manual en la tesis; no se editó el documento Word.

Esta síntesis solo incluye afirmaciones verificables con el código y los artefactos del repositorio. Los números marcados como recalculados provienen de aritmética sobre archivos existentes, no de nuevos experimentos.

## Alcance de la auditoría

Se realizó una revisión técnica del flujo completo del candidato `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`, desde la extracción de pose hasta la clasificación, mediante lectura de código y de resultados archivados. No se entrenaron modelos ni se ejecutaron nuevas inferencias. El objetivo fue determinar qué información recibe el modelo y qué factores pueden influir en sus resultados además del movimiento corporal.

## Descripción del procesamiento

El sistema extrae 17 puntos corporales con MediaPipe Pose a una rejilla temporal de 15 cuadros por segundo y una dimensión máxima de 720 píxeles. Sobre una ventana de 5,03 s construye dos entradas: una secuencia de 68 canales por 96 pasos (posición y velocidad de los 17 puntos, relativas al centro de cadera y a una escala corporal) y un vector de 36 características de marcha. La red de dos ramas recibe únicamente esas dos entradas; no recibe píxeles, nombres de archivo ni metadatos. El procesamiento usado en el entrenamiento V4 y en la inferencia de la aplicación coincide en las funciones y parámetros revisados.

## Hallazgos verificables

1. **Composición del dataset.** Los 84 videos de marcha normal y de Parkinson fueron grabados todos en 1920×1080, vista lateral y cámara fija. Ninguno de los 33 videos de esclerosis múltiple y riesgo de caída tiene esa resolución, y 25 son verticales con vistas y cámaras variadas. La resolución, la vista y el tipo de cámara están por tanto totalmente asociados al grupo de clases, y este dataset no permite separar su efecto del de la clase.
2. **Sondas de metadatos.** Con las mismas particiones agrupadas por sujeto, clasificadores simples que solo reciben metadatos técnicos de los archivos alcanzan F1 macro de 0,78 a 0,86, frente a 0,744 del candidato. Esto demuestra que las etiquetas pueden predecirse a partir de condiciones de grabación; no demuestra que la red utilice esa información.
3. **Estructura de las predicciones.** En las predicciones fuera de partición del candidato, el 97,4 % (570 de 585, recalculado) conserva el grupo de condiciones de grabación correcto. Este resultado es compatible tanto con el aprendizaje de patrones de movimiento como con la lectura de condiciones de grabación.
4. **Mejor evidencia de señal cinemática.** La distinción entre marcha normal y Parkinson, ambas grabadas en el mismo laboratorio, alcanza una exactitud descriptiva de 94,3 % (396 de 420 predicciones). Este es el contraste menos afectado por diferencias de grabación, aunque los clips normales son más cortos y su ventana efectiva promedia 3,9 s frente a 5,03 s de los demás grupos.
5. **Clases menos respaldadas.** La discriminación entre esclerosis múltiple y riesgo de caída es débil: 66,2 % de aciertos entre las predicciones de ambas clases frente a 70,8 % de proporción de esclerosis múltiple, y sensibilidad de 36,4 % para riesgo de caída.
6. **Características de la red.** Algunas de las 36 características no miden lo que su nombre indica: nueve se calculan con coordenadas absolutas de imagen y reflejan desplazamiento global; la escala corporal de las características es casi el ancho de hombros aparente y por tanto depende del ángulo de vista; no se corrige la relación de aspecto de la imagen. Estos hallazgos describen la definición de las entradas; no se midió su efecto sobre la clasificación.
7. **Aumentación de datos.** El espejo horizontal no invierte el signo de las velocidades horizontales, y las transformaciones temporales no mantienen la coherencia entre ramas. Solo afectan al entrenamiento.
8. **Protocolo de validación.** No se encontró fuga de sujetos en el protocolo de validación cruzada agrupada, y la recalibración de BatchNorm usa únicamente el conjunto de entrenamiento de cada partición. La validación es por sujeto, no por fuente: los sujetos de prueba proceden de las mismas fuentes que los de entrenamiento.

## Lo que no se puede afirmar

- Que el modelo aprenda exclusivamente patrones clínicos de marcha: no está demostrado.
- Que el modelo dependa principalmente de factores de grabación: tampoco está demostrado. Las sondas miden la disponibilidad de atajos, no su uso.
- Que el modelo generalice a nuevas cámaras, vistas o fuentes: no se ha medido; la validación externa disponible consta de dos videos.
- La validez clínica de las etiquetas: ningún registro tiene validación clínica individual acreditada, y 27 de los 67 grupos de sujeto son provisionales.

## Limitaciones

Siete sujetos con Parkinson y nueve con riesgo de caída; las cinco repeticiones de validación reutilizan los mismos 117 videos, por lo que sus desviaciones no son intervalos de confianza; no existe una prueba controlada de robustez del candidato frente a cambios de iluminación, compresión, resolución o cuadros por segundo, ni una ablación temporal.

## Conclusión

El candidato V4 es defendible como **prototipo técnico** de un sistema de análisis de pose y clasificación experimental de patrones de marcha, con validación agrupada por sujeto y advertencias de limitación explícitas. No es defendible como clasificador clínico ni como evidencia de generalización a fuentes de grabación distintas. Antes de modificar el modelo se propone ejecutar pruebas de inferencia sobre el modelo congelado (dependencia temporal, importancia de características, robustez visual y coherencia del movimiento con ventana igualada), cuyo diseño figura en `PLAN_PRUEBAS_V4.md`, y ampliar el conjunto de videos con cada clase en múltiples fuentes de grabación.
