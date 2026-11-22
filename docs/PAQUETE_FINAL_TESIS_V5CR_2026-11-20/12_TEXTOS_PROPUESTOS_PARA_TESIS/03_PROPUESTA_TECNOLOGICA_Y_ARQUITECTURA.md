# Propuesta tecnológica desarrollada y arquitectura (propuesta)

## A. Texto nuevo propuesto
### Propuesta tecnológica desarrollada
La solución se compone de una aplicación web (Next.js y React, con PostgreSQL mediante Prisma) y un módulo de análisis en Python. El módulo extrae 17 puntos corporales de cada video con **MediaPipe Pose**, una red de estimación de pose **preentrenada** que no fue entrenada ni ajustada en este proyecto, y los transforma en una secuencia de movimiento y en 33 características de marcha. Sobre esas entradas actúa el **clasificador propio** del proyecto, `GaitTemporalModel`, entrenado con los videos del dataset (PyTorch). El resultado se presenta al usuario como clase indicada por el modelo, probabilidades de las cuatro categorías y advertencias, y se almacena para el historial y los informes.

### Arquitectura del clasificador (V5-CR)
`GaitTemporalModel` es una red convolucional unidimensional de dos ramas con 17 788 parámetros entrenables. La **rama de secuencia** recibe un tensor de 68 canales por 40 muestras (34 posiciones y 34 velocidades de los 17 puntos, relativas a la cadera y escaladas por la longitud del torso) y aplica tres convoluciones 1D (68→24 con núcleo 5; 24→32 con núcleo 3 y dilatación 2; 32→32 con núcleo 3 y dilatación 4), cada una con normalización por lotes y activación GELU, con *dropout* de 0,3 en las dos primeras; la salida se resume con la media y el máximo a lo largo del tiempo (64 valores). La **rama de características** procesa las 33 características normalizadas con dos capas densas (33→24 con normalización por lotes, GELU y *dropout*, y 24→16 con GELU). Ambas salidas se concatenan (80 valores) y pasan por una cabeza de clasificación (*dropout* 0,4; 80→32 con GELU; 32→4). Los logits de hasta cinco ventanas de 2,6 s por video se promedian, se dividen por una temperatura de calibración (T = 0,6615) y se transforman con *softmax* en cuatro probabilidades.

### Flujo del sistema
Carga del video → extracción de pose → control de calidad (pose insuficiente produce un resultado no concluyente) → selección de ventanas de 2,6 s en un tramo de hasta 5,03 s → preprocesamiento V5-CR → escalado → clasificador → agregación de logits y calibración → resultado, registro en la base de datos, informe en pantalla y PDF → historial y administración. El modelo V4 se conserva instalado como respaldo y no se utiliza automáticamente cuando V5-CR falla: el sistema informa el error.

## B. Se conserva
Descripción de la aplicación web, base de datos, roles, seguridad y servicios que no cambiaron; la justificación teórica de la red convolucional temporal y de la estimación de pose del marco teórico.

## C. Se reemplaza
La descripción de V4 como arquitectura vigente (36 características, 68 × 96, ventana de 5,03 s con reescalado temporal) y cualquier esquema de red genérico: el diagrama debe ser el de las capas reales.

## D. Figuras/tablas
`fig_arquitectura_GaitTemporalModel_V5CR`; `fig_flujo_completo_sistema_V5CR`; tabla de capas y parámetros (`02_MODELO_V5CR_Y_ARQUITECTURA/arquitectura_capas_V5CR.csv`).

## E. Fuentes
`scripts/video_training/deep/deep_common.py::build_model`; checkpoint `models/gait_deep_v5cr/` (estructura y 17 788 parámetros calculados del `state_dict`); `src/app/api/analysis/video/route.ts`; `15_predict_deep_video_v5cr.py`.
