# Limitaciones (propuesta para el apartado de limitaciones / 4.4)

## A. Texto nuevo propuesto
1. **Validación interna.** Todas las métricas provienen de validación cruzada sobre 117 videos y 67 grupos técnicos de sujeto; no hay validación clínica ni un conjunto externo independiente. Los mismos videos sirvieron para diseñar y comparar varias versiones del modelo, con riesgo de sobreajuste a la evaluación.
2. **Identidad de los sujetos.** 27 de los 67 grupos son provisionales (un video por grupo sin evidencia de que pertenezcan a personas distintas); si dos videos proceden de la misma persona, la separación por sujeto no lo evita.
3. **Etiquetas.** Son las registradas; ninguno de los 117 videos tiene validación clínica individual y 112 de 117 carecen de atribución de origen acreditada.
4. **Asociación entre fuente y clase.** Normal y Parkinson proceden solo del laboratorio; esclerosis múltiple, sobre todo de video vertical; el mismo esquema aplica al riesgo de caída. Sondas que solo usan metadatos técnicos alcanzaron un F1 macro de 0,777 a 0,786, del mismo orden que el de V5-CR (0,785): el rendimiento no puede atribuirse con certeza a la marcha.
5. **Tamaño y desbalance.** Parkinson tiene 7 grupos y riesgo de caída 9 (11 videos); los intervalos por clase son amplios (F1 de riesgo de caída 0,58, IC95 0,31–0,74).
6. **Clases débiles.** La esclerosis múltiple y el riesgo de caída se confunden entre sí (29 % de las predicciones de esclerosis múltiple se clasificaron como riesgo de caída); V5-CR empeora la esclerosis múltiple frente a V4 (no concluyente).
7. **Mejora global no demostrada.** La diferencia de F1 macro frente a V4 activo no es estadísticamente concluyente; solo la clase riesgo de caída mejora de forma respaldada.
8. **Calibración.** La ECE sin calibrar de V5-CR es significativamente peor que la de V4 activo; la calibración por temperatura solo puede compararse con V4 base (no existe para V4 activo) y esa diferencia no tiene intervalo de confianza.
9. **Robustez.** V5-CR no mejora el ruido de los puntos ni la pérdida de fotogramas respecto a V4; depende de la dinámica fina del movimiento; todo es 2D (sin corrección de perspectiva ni rotación) y sin unidades físicas.
10. **Características.** Son aproximaciones adimensionales; el «ritmo por picos» no es cadencia clínica ni conteo de pasos validado; en 22 % de las ventanas faltan características de brazos (muñecas no visibles) y se imputan con medianas.
11. **Software.** La inferencia ejecuta un proceso de Python por análisis, sin cola de trabajos; las pruebas automatizadas se hicieron en un entorno aislado y no sobre el servidor habitual con datos reales; no se probaron otros navegadores ni dispositivos móviles reales; no se guardaron las curvas de entrenamiento.
12. **Informes históricos.** Los 79 informes registrados antes del almacenamiento canónico no tienen PDF original; no se reconstruyeron.
13. **Alcance.** El sistema es un prototipo orientativo; no diagnostica ni sustituye la valoración de un profesional de salud.

## B. Se conserva
Las limitaciones ya declaradas sobre V4 que siguen vigentes (fuente–clase, tamaño de muestra, ausencia de validación clínica).

## C. Se reemplaza
Cualquier frase que sugiera validez clínica, generalización o superioridad demostrada de V5-CR sobre V4.

## D. Figuras/tablas
`fig_distribucion_dataset`, tabla de metadatos–sondas (sección 8 de `METRICAS_Y_COMPARACIONES.md`).

## E. Fuentes
`03_DATASET_Y_METODOLOGIA/`, `04_METRICAS_Y_COMPARACIONES/`, `14_AUDITORIA_FINAL/PENDIENTES_Y_EVIDENCIAS_FALTANTES.md`, `docs/evidencia_experimental_v4_2026-11-18/`.
