# Sprint 4 — Iteración 8: Parámetros adicionales y dataset para el modelo

## ¿Qué hace la Iteración 8?

Sobre los parámetros de marcha de la Iteración 7, la Iteración 8:

1. **Calcula parámetros adicionales** por video: **simetría**, **estabilidad** y
   **variabilidad** (todos normalizados, a partir de las coordenadas de pose).
2. **Limpia y organiza el dataset** en un único archivo de features con etiquetas.
3. **Particiona** el dataset en **train / validation / test** (70/15/15).
4. Deja los datos **listos para el modelo de Sprint 5** (sin entrenar ni evaluar).

> ⚠️ **Sin afirmaciones clínicas:** las categorías son etiquetas de organización del
> dataset, no diagnósticos. Todos los valores son **orientativos y normalizados**.

## Archivos y scripts involucrados

| Archivo | Rol |
|---|---|
| `scripts/calculate_basic_params.py` | (Iteración 7, **ampliado**) Ahora también calcula y guarda `symmetry`, `stability`, `gait_variability` en `outputs/gait_basic_parameters.csv`. Lo demás queda intacto. |
| `scripts/prepare_iteration8_dataset.py` | (nuevo) Combina parámetros + categorías → `outputs/gait_features_dataset.csv` y genera `data/train.csv`, `data/validation.csv`, `data/test.csv`. |
| `scripts/validate_iteration8.py` | (nuevo) Valida el dataset → `outputs/iteration8_validation_report.json`. |
| `data/dataset_metadata.csv` | (existente) Categorías por video. |
| `docs/sprint4_iteration8.md` | (este documento). |

## Parámetros adicionales (cómo se calculan)

Se usan landmarks de MediaPipe Pose: caderas **23/24**, tobillos **27/28**,
hombros **11/12**. Todas las coordenadas son normalizadas (0–1).

### Simetría — `symmetry` (0–1; 1 = más simétrico)
Compara la **amplitud de movimiento vertical** de cada tobillo (cuánto se eleva cada
pie a lo largo del video):
```
amp_izq = max(y_tobillo_izq) - min(y_tobillo_izq)
amp_der = max(y_tobillo_der) - min(y_tobillo_der)
symmetry = 1 - |amp_izq - amp_der| / max(amp_izq, amp_der)
```
1 = ambos pies se mueven por igual; valores menores = más asimetría.

### Estabilidad — `stability` (0–1; 1 = más estable)
Menos variación de la **inclinación del tronco** = más estable. El ángulo del tronco
por frame se mide entre el centro de hombros y el centro de caderas respecto a la
vertical:
```
stability = clamp01( 1 - desviacion_tipica(angulo_tronco) / 25 )
```
Si los hombros no son visibles, se usa como reserva el **bamboleo vertical del
centro de cadera**: `clamp01(1 - 8 * std(hip_center_y))`.

### Variabilidad — `gaitVariability` (>= 0; mayor = más irregular)
**Coeficiente de variación** de la separación entre tobillos (irregularidad de la
zancada de un paso a otro):
```
gaitVariability = desviacion_tipica(separacion_tobillos) / media(separacion_tobillos)
```

## Dataset final de features

`scripts/prepare_iteration8_dataset.py` genera `outputs/gait_features_dataset.csv`
con columnas:

`video_id, source_file, category, label, walkingSpeed, cadence, stepLength,
symmetry, stability, gaitVariability, frames_with_pose, notes`

Origen de cada feature (desde `outputs/gait_basic_parameters.csv`):
- `walkingSpeed` ← `estimated_velocity_normalized`
- `cadence` ← `cadence_steps_per_min`
- `stepLength` ← `average_step_length_normalized`
- `symmetry`, `stability` ← iguales
- `gaitVariability` ← `gait_variability`

## Categorías y etiquetas

La categoría se toma de `data/dataset_metadata.csv` (autoritativa por `video_id`) y
se mapea a una etiqueta numérica:

| category | label |
|---|---|
| control | 0 |
| parkinson | 1 |
| multiple_sclerosis | 2 |
| fall_risk | 3 |

Las filas con categoría no válida se **omiten** del dataset (se informan en el log).

## Partición train / validation / test

Particiones reproducibles (semilla fija) **70 / 15 / 15**, con reservas seguras para
conjuntos pequeños (nunca falla; todas las particiones llevan cabecera):

- **1 fila** → todo a `train`; `validation` y `test` solo con cabeceras.
- **2 filas** → 1 `train`, 1 `test` (validation con cabeceras).
- **3 filas** → 1 `train`, 1 `validation`, 1 `test`.
- **≥ 4 filas** → ~70/15/15 garantizando al menos 1 en cada partición.

> Con un solo video de ejemplo, el dataset se genera correctamente con **1 fila** en
> `train.csv`. El objetivo es dejar la **estructura** lista para Sprint 5, no un
> dataset grande.

## Validación de la Iteración 8

`scripts/validate_iteration8.py` comprueba que el dataset existe, tiene las columnas
requeridas, las features numéricas son numéricas, las categorías y labels son
válidos y coherentes, y que existen `train.csv`, `validation.csv` y `test.csv`.
Genera `outputs/iteration8_validation_report.json` con
`overall_status: READY_FOR_MODEL_PREPARATION` cuando todo lo crítico pasa.

## Limitaciones (video RGB monocular)

- **Sin escala real:** todos los valores son **normalizados** (fracción de imagen),
  no metros, m/s ni unidades clínicas.
- **Simetría/estabilidad/variabilidad** son proxies computacionales orientativos,
  sensibles al ángulo de cámara, iluminación y visibilidad de los landmarks.
- **Dataset pequeño:** con un único video de ejemplo, las particiones son mínimas;
  sirven como estructura para Sprint 5, no para entrenar un modelo robusto todavía.
- **No hay diagnóstico:** no se entrena ni evalúa ningún modelo en esta iteración.

## Comandos (PowerShell)

```powershell
# 1) Activar el entorno
.\.venv311\Scripts\Activate.ps1

# 2) (Si hace falta) generar parámetros por video — Iteración 7/8
.\.venv311\Scripts\python.exe scripts\export_pose_csv.py "public\uploads-temp\analysis_5088f48e-b58d-4973-931f-72781f851487.mp4" 300
.\.venv311\Scripts\python.exe scripts\calculate_basic_params.py --video-id demo_walk_01 --fps 30

# 3) Preparar el dataset de features + particiones (Iteración 8)
.\.venv311\Scripts\python.exe scripts\prepare_iteration8_dataset.py

# 4) Validar el dataset (Iteración 8)
.\.venv311\Scripts\python.exe scripts\validate_iteration8.py
```

### Verificar que Iteración 7 sigue funcionando
```powershell
.\.venv311\Scripts\python.exe scripts\calculate_basic_params.py --video-id demo_walk_01 --fps 30
.\.venv311\Scripts\python.exe scripts\validate_iteration7.py
```
