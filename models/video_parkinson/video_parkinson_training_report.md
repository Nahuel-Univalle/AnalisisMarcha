# Entrenamiento de modelo por video

Este modelo no emite diagnóstico médico definitivo. Su resultado debe interpretarse como apoyo tecnológico para identificar patrones de marcha asociados a Parkinson.

## Dataset
- Videos totales usados: 87
- Sujetos totales: 37
- Videos normales: 59
- Videos Parkinson: 28
- Sujetos normales: 30
- Sujetos Parkinson: 7

## Extraccion
- Landmarks extraidos con MediaPipe Pose.
- Distancias y movimientos normalizados por escala corporal estimada.

## Validacion
- Metodo: GroupKFold por subject_id; splits train/val/test por sujeto
- La division se realiza por subject_id para evitar fuga de datos.

## Modelo seleccionado
- LogisticRegression
- Recall Parkinson promedio: 0.8000
- F1 promedio: 0.7660
- Accuracy promedio: 0.9319
- ROC AUC promedio: 0.9892857142857143

## Limitaciones
- El rendimiento depende de calidad, encuadre y diversidad de videos.
- No debe usarse como diagnostico medico definitivo.
- La validacion evita fuga de sujetos entre folds.

## Recomendacion de uso
Usar como apoyo tecnologico y no como diagnostico medico definitivo. Los resultados deben revisarse junto con evaluacion clinica profesional.

## Features usadas
- body_motion_mean
- body_motion_std
- hip_center_motion_mean
- shoulder_center_motion_mean
- vertical_motion_mean
- horizontal_motion_mean
- left_ankle_motion_mean
- right_ankle_motion_mean
- left_knee_motion_mean
- right_knee_motion_mean
- leg_motion_asymmetry
- ankle_vertical_range_left
- ankle_vertical_range_right
- ankle_vertical_asymmetry
- knee_vertical_range_left
- knee_vertical_range_right
- step_regularity_score
- left_wrist_motion_mean
- right_wrist_motion_mean
- arm_swing_mean
- arm_swing_asymmetry
- left_arm_range
- right_arm_range
- shoulder_width_mean
- hip_width_mean
- trunk_inclination_mean
- trunk_inclination_std
- trunk_sway_mean
- trunk_sway_std
- posture_stability_score
- estimated_step_count
- estimated_cadence_steps_per_min
- step_frequency_hz
- gait_variability
- motion_smoothness
- rhythm_variability
