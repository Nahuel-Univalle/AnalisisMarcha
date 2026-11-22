# Recomendación técnica final

**Con los videos y etiquetas disponibles, no encontré una mejora adicional suficientemente respaldada más allá de V5-CR. Recomiendo conservar V5-CR como mejor candidato técnico actual y detener el entrenamiento.** No integrar todavía en la aplicación (V4 BN sigue activo); no actualizar la tesis hasta decidirlo.

## Por qué V5-CR
- Corrige todos los defectos verificados, incluido uno propio de V5 (interpolación absoluta que filtraba la traslación): 0 de 633 ventanas reales cambian ante una cámara que sigue a la persona.
- Es el único con ΔF1 macro = 0,000 ante cámara que sigue, paneo, aspecto y zoom (V5-P: −0,31 con cámara que sigue; V4: −0,32).
- F1 macro interno 0,785 (V4 BN 0,744; V5-P 0,800). Frente a V4 BN la diferencia **no es concluyente** (+0,041 [−0,029; 0,102]); la única mejora respaldada es riesgo de caída (F1 0,378 → 0,581; sensibilidad 0,364 → 0,691; IC de F1 [0,023; 0,356]).
- Mejor calibración tras temperatura por fold (ECE 0,064).

## Lo que no se puede decir
- No es demostrablemente mejor que V5-P ni que V4 BN en F1 macro; V5-P tiene 0,015 más de F1 (n. s.) a costa de depender de la cámara.
- Esclerosis múltiple empeora frente a V4 BN (F1 0,684 vs 0,756; sensibilidad 0,618 vs 0,745; n. s.) y la confusión EM↔riesgo persiste.
- Todo es validación interna sobre 117 videos (67 grupos, 27 provisionales) usados para diseñar y evaluar varias versiones: riesgo de sobreajuste a la evaluación. Sin validez externa ni clínica.

## Decisión sobre seguir
No seguir entrenando con estos datos. Lo siguiente requiere datos reales nuevos (≥ 10 sujetos por clase, fuentes mezcladas dentro de cada clase, etiqueta verificada) y evaluar V4 BN y V5-CR congelados. Si decide integrar V5-CR: crear un script de inferencia nuevo con `v5cr_preproc.window_inputs_C`, SHA-256 y avisos de calidad, y repetir las pruebas de flujo completo.

Detalle y evidencia: `INFORME_FINAL_OPTIMIZACION.md`.
