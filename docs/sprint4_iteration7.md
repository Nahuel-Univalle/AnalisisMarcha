# Sprint 4 — Iteración 7: Parámetros básicos de marcha y organización por categorías

## ¿Qué hace la Iteración 7?

A partir de las coordenadas de pose extraídas en el Sprint 3 (MediaPipe Pose → CSV
de landmarks), la Iteración 7:

1. **Calcula parámetros básicos de marcha** por video:
   - **velocidad** (normalizada),
   - **cadencia** (pasos/min),
   - **longitud de paso** (normalizada).
2. **Clasifica los datos** en una de las cuatro categorías del proyecto:
   `control`, `parkinson`, `multiple_sclerosis`, `fall_risk`.
3. **Valida** que las coordenadas del Sprint 3 sirven para calcular esos parámetros.

> ⚠️ **Importante (sin afirmaciones clínicas):** las categorías son **etiquetas de
> organización del dataset**, no diagnósticos. Los videos de ejemplo NO están
> diagnosticados; sus etiquetas son plantillas para estructurar el dataset.

## Archivos y scripts involucrados

| Archivo | Rol |
|---|---|
| `scripts/export_pose_csv.py` | (Sprint 3, mejorado) Exporta landmarks a `outputs/pose_landmarks.csv`. Ahora acepta un 2º argumento opcional con el nº de frames a muestrear (más frames = mejor señal de marcha). |
| `scripts/calculate_basic_params.py` | (Sprint 3, mejorado) Mantiene el cálculo por frame (`outputs/basic_gait_params.csv`) y **añade** los parámetros agregados por video en `outputs/gait_basic_parameters.csv`. |
| `scripts/validate_iteration7.py` | (nuevo) Valida que `outputs/pose_landmarks.csv` es usable. Genera `outputs/iteration7_validation_report.json`. |
| `data/dataset_metadata.csv` | (nuevo) Metadatos: `video_id, file_path, category, notes`. Asocia cada video a una de las 4 categorías. |
| `docs/sprint4_iteration7.md` | (este documento). |

### Entradas y salidas

- **Entrada:** `outputs/pose_landmarks.csv`
  (columnas: `frame_index, landmark_index, x, y, z, visibility, image_width, image_height`).
- **Salidas:**
  - `outputs/basic_gait_params.csv` — por frame (base Sprint 3, intacto).
  - `outputs/gait_basic_parameters.csv` — por video (Iteración 7).
  - `outputs/iteration7_validation_report.json` — reporte de validación.

### Columnas de `outputs/gait_basic_parameters.csv`

`video_id, source_file, category, total_frames, fps, frames_with_pose,
estimated_steps, cadence_steps_per_min, average_step_length_normalized,
estimated_velocity_normalized, notes`

El CSV hace **upsert por `video_id`**: al procesar varios videos se acumulan filas
(una por video) y se forma el dataset de parámetros.

## Fórmulas (todas normalizadas)

Se usan los landmarks de MediaPipe Pose: caderas **23 (izq.)** y **24 (der.)**,
tobillos **27 (izq.)** y **28 (der.)**. Todas las coordenadas están normalizadas
(0–1 respecto al ancho/alto de la imagen).

Series por frame:
- `ankle_distance` = distancia euclidiana entre tobillos `27` y `28`.
- `hip_center_x` = promedio de `x` de las caderas `23` y `24`.

Duración:
```
duracion_s = (frame_max - frame_min) / fps
```

### Cadencia
- **Eventos de paso (`estimated_steps`):** se cuentan los **picos** de la señal
  `ankle_distance` a lo largo de los frames. Cada vez que un pie se adelanta, la
  separación entre tobillos alcanza un máximo local ≈ **un paso**.
  Umbral del pico = `media + 0.25 · desviación_típica`, con una distancia mínima
  entre picos para no contar ruido.
- **Cadencia:**
```
cadence_steps_per_min = estimated_steps / duracion_s * 60
```

### Longitud de paso
```
average_step_length_normalized = media de ankle_distance en los frames-pico
```
Representa la separación típica entre los pies en el momento del paso (normalizada).
Si no hay picos claros, se usa la separación media de tobillos como aproximación.

### Velocidad
```
estimated_velocity_normalized = |hip_center_x[fin] - hip_center_x[inicio]| / duracion_s
```
Es el desplazamiento horizontal del centro de la cadera dividido por el tiempo
(en *anchos de imagen por segundo*).

## Manejo de categorías

`scripts/calculate_basic_params.py` resuelve la categoría así:
1. Si se pasa `--category`, se usa esa (validada contra las 4 oficiales).
2. Si no, se busca en `data/dataset_metadata.csv` por `video_id` o por nombre de archivo.
3. Si no se encuentra, queda `unknown` y se anota en `notes`.

Para añadir un video al dataset basta con agregar una fila a `data/dataset_metadata.csv`:
```
video_id,file_path,category,notes
mi_video_01,videos/mi_video_01.mp4,control,Descripcion opcional
```

## Validación de coordenadas

`scripts/validate_iteration7.py` comprueba, sobre `outputs/pose_landmarks.csv`:
- el archivo existe;
- existen las columnas requeridas (`frame_index, landmark_index, x, y, visibility`);
- hay landmarks de **caderas (23, 24)** y **tobillos (27, 28)**;
- hay suficientes frames (≥ 5);
- la visibilidad media de los landmarks clave es aceptable (≥ 0.30, informativa);
- hay suficientes frames con pose válida (≥ 5 con los 4 landmarks);
- los parámetros básicos se pueden calcular sin que el proceso falle (cálculo de prueba).

Genera `outputs/iteration7_validation_report.json` con `overall_status`:
`USABLE` o `NO_USABLE`, además del detalle de cada check. El script sale con
código `0` si las coordenadas son usables y `1` si no.

## Limitaciones (video RGB monocular)

- **Sin escala real:** una sola cámara RGB no da metros. Por eso longitud y
  velocidad son **normalizadas** (fracción de la imagen), no metros ni m/s.
- **FPS no viaja en el CSV de landmarks:** la cadencia y la velocidad dependen del
  FPS; si no se conoce, se asume `--fps 30` (configurable). Pásalo si conoces el real.
- **Muestreo:** con pocas muestras (export por defecto = 20 frames) la cadencia es
  poco fiable (submuestreo). Para una señal densa, exporta más frames
  (`export_pose_csv.py <video> 300`).
- **Dirección de la marcha:** la velocidad usa el desplazamiento **horizontal** de
  la cadera; si la persona camina hacia la cámara o en el sitio, queda subestimada.
- Estos valores son **orientativos y académicos**; no constituyen diagnóstico.

## Comandos (PowerShell)

```powershell
# 1) Activar el entorno Python 3.11
.\.venv311\Scripts\Activate.ps1

# 2) Generar los landmarks de pose si no existen (Sprint 3).
#    2º argumento opcional = nº de frames a muestrear (más = mejor señal de marcha).
.\.venv311\Scripts\python.exe scripts\export_pose_csv.py "public\uploads-temp\analysis_5088f48e-b58d-4973-931f-72781f851487.mp4" 300

# 3) Calcular los parámetros básicos de marcha (velocidad, cadencia, longitud de paso)
#    y asociar la categoría (desde data\dataset_metadata.csv o con --category).
.\.venv311\Scripts\python.exe scripts\calculate_basic_params.py --video-id demo_walk_01 --fps 30

# 4) Validar que las coordenadas del Sprint 3 son usables.
.\.venv311\Scripts\python.exe scripts\validate_iteration7.py
```

Sin argumentos, `calculate_basic_params.py` mantiene el comportamiento del Sprint 3
(lee `outputs/pose_landmarks.csv`, escribe `outputs/basic_gait_params.csv`) y, además,
genera `outputs/gait_basic_parameters.csv`.
