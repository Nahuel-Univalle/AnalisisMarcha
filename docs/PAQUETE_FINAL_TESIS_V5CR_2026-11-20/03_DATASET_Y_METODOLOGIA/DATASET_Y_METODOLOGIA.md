# Dataset y metodología de V5-CR

> Verificado el 2026-11-20 contra `outputs/dataset_v4_4class/manifest_v4_preview.csv`, `dataset_v4_preview.npz`, `dataset_v5cr_bank.npz` y la ficha previa `docs/inventario_dataset_v4_2026-11-18/`. Los 117 videos **no se copian** al paquete (privacidad). Trazabilidad por video, sin rutas ni datos personales: `MANIFIESTO_TRAZABILIDAD_117_VIDEOS.csv`; resumen: `RESUMEN_DATASET_POR_CLASE.csv`; excluidos: `VIDEOS_EXCLUIDOS_20_CON_MOTIVO.csv`. Reproducible con `scripts/generar_manifiesto_dataset.py`.

## 1. Cantidades verificadas (todas coinciden con lo reportado)
| Clase (etiqueta registrada) | Videos | Grupos técnicos de sujeto | Grupos provisionales |
|---|---:|---:|---:|
| Normal | 58 | 30 | 0 |
| Parkinson | 26 | 7 | 0 |
| Esclerosis múltiple | 22 | 21 | 20 |
| Riesgo de caída | 11 | 9 | 7 |
| **Total** | **117** | **67** | **27** |

Etiquetas, grupos y orden de los 117 videos son idénticos en el conjunto V4 y en el banco de ventanas de V5-CR (comprobado por script). Además, el manifiesto completo tiene 137 filas: 117 incluidas y **20 excluidas** (18 `EXCLUDE` por pose insuficiente/sin tramo de marcha continuo y 2 `MANUAL_REVIEW`), que **no** se usaron en el entrenamiento ni en la evaluación y se mantienen fuera.

## 2. Procedencia de los videos (sin inventar)
- **Laboratorio (84 videos: 58 normales + 26 Parkinson):** grabaciones en laboratorio, trípode, 1920×1080, vista lateral, horizontal; los nombres de archivo llevan un identificador de sujeto del dataset (`NNN_NM` / `NNN_PD`).
- **Redes sociales / material público vertical (25 videos: 20 esclerosis múltiple + 5 riesgo de caída):** orientación vertical (478×850), cámara con anotación incompleta.
- **Repositorio/clínica de 848×478 a 60 fps (8 videos: 2 esclerosis múltiple + 6 riesgo de caída):** para 5 videos de riesgo de caída la marca de agua documentada indica «Mission Gait»; 4 videos de riesgo de caída mencionan una plataforma de redes en la documentación (las cuentas se omiten).
- **Atribución original acreditada: 5 de 117; 112 de 117 carecen de ella. Procedencia original trazable por URL o documento primario: 0 de 117.** (`docs/inventario_dataset_v4_2026-11-18/ficha_tecnica_y_fuentes.md`). No se afirma una institución, autor o repositorio para el resto.

## 3. Etiquetas y sus limitaciones
- La etiqueta de clase es la **registrada** (carpeta/nombre/documentación); **ninguno de los 117 videos tiene validación clínica individual acreditada**. No es un diagnóstico certificado.
- «Riesgo de caída» y «esclerosis múltiple» proceden de fuentes heterogéneas (menor resolución, vertical, cámara en mano o que acompaña); el rótulo no equivale a una evaluación funcional estandarizada.

## 4. Grupos registrados frente a sujetos verificados
- Un **grupo técnico** (`split_group`) agrupa los videos que se asume pertenecen a la misma persona. Para normal y Parkinson (37 grupos) el identificador de sujeto procede del dataset original (en el nombre de archivo). Para **27 grupos** (20 de esclerosis múltiple y 7 de riesgo de caída) el estado es **provisional**: la fuente no identifica a la persona, no hay evidencia de repetición entre videos y se asigna **1 video = 1 grupo**; si dos videos proceden realmente de la misma persona, la separación por sujeto no la detecta (posible fuga de identidad entre entrenamiento y prueba).
- Por tanto, **«67 sujetos» debe leerse «67 grupos técnicos de sujeto»**, no 67 personas verificadas. 90 videos tienen grupo con identidad registrada y 27 provisional.

## 5. Separación entrenamiento/evaluación y particiones
- Validación cruzada **agrupada por grupo técnico de sujeto** (`StratifiedGroupKFold`, 5 particiones externas), **semillas de partición 42, 43, 44, 45, 46**; en cada partición, un grupo no aparece a la vez en entrenamiento y prueba (comprobado con `assert` en el código de entrenamiento).
- Dentro de cada partición de entrenamiento: validación anidada de 3 particiones agrupadas (semillas `1000·p+k`) para elegir el número de épocas (E\*) y la temperatura de calibración. El modelo final desplegado (E\* = 73, T = 0,6615) se entrenó con los 117 videos y **no** tiene evaluación independiente propia: su rendimiento se estima con la validación cruzada.
- Cada video produce entre 1 y 7 ventanas de 2,6 s (media 5,41; en total **633 ventanas** para los 117 videos); en evaluación se promedian los logits de K ≤ 5 ventanas equiespaciadas por video. **Las ventanas no son videos ni sujetos independientes.**

## 6. Aumento de datos permitido (solo en entrenamiento)
Espejo horizontal físicamente correcto (prob. 0,5) y ruido gaussiano σ = 0,01 en posiciones (prob. 0,6) con velocidades recalculadas. **No** se generan videos, sujetos ni etiquetas artificiales, ni se usan datos sintéticos como ejemplos de entrenamiento (las señales sintéticas de `fase3_pruebas`/`fase8_pruebas_c` sirven solo para verificar el código).

## 7. Medidas contra fuga de información
- Escalador (mediana, media, desviación), imputación de NaN y temperatura se ajustan **solo con el entrenamiento** de cada partición (`Bank.fit_scaler(tr)`, `choose_epoch`, `fit_temperature` con validación interna).
- Particiones por grupo; semillas fijas; la época óptima se elige con validación interna anidada, no con la partición de prueba.
- El escalador final y T se ajustaron sin usar etiquetas de otros conjuntos. **Limitación:** los mismos 117 videos se utilizaron para diseñar y comparar varias versiones (V4, V5-P, V5-C, V5-CR) y para elegir cambios de preprocesamiento (p. ej. eliminar características de traslación), de modo que la evaluación interna puede estar sobreajustada al conjunto; el diseño de V5-CR se registró con criterios definidos antes de ver resultados (`PREREGISTRO_V5C.md` y su Adenda).

## 8. Asociación entre fuente de grabación y clase (limitación mayor)
| Clase | Laboratorio | Redes sociales (vertical) | Clínica 848×478 |
|---|---:|---:|---:|
| Normal (58) | 58 | 0 | 0 |
| Parkinson (26) | 26 | 0 | 0 |
| Esclerosis múltiple (22) | 0 | 20 | 2 |
| Riesgo de caída (11) | 0 | 5 | 6 |
La fuente casi determina la clase: normal y Parkinson solo existen en el laboratorio y la esclerosis múltiple es sobre todo vertical. El modelo podría aprender propiedades de la grabación en lugar de la marcha. V5-CR reduce algunas pistas (aspecto, traslación de cámara) pero **no puede eliminar** esta asociación con el material disponible; una prueba previa (V4) mostró que la orientación de grabación era predecible a partir de las características.

## 9. Desbalance y tamaño
58 / 26 / 22 / 11 videos (5,3 : 2,4 : 2 : 1). Parkinson tiene 7 grupos y riesgo de caída 9 grupos: los intervalos de confianza por clase son amplios (p. ej., F1 de riesgo de caída 0,58 con IC95 0,31–0,74). Se usan pesos de clase en la función de pérdida y métricas por clase y F1 macro.

## 10. Ausencia de validación clínica externa
No existe un conjunto de prueba externo limpio ni validación clínica. Una prueba exploratoria con 2 videos externos y 20 videos descartados por calidad (V5-P) mostró que las etiquetas de esos videos no están verificadas; no se interpreta como evaluación. Los resultados deben presentarse como validación interna de un prototipo orientativo.

## 11. Duración, resolución y vistas (resumen)
Duración 3,4–43,8 s por video (media 10,1 s): normal media 4,85 s (3,4–12,9), Parkinson 12,99 s (6,7–20,0), esclerosis múltiple 18,61 s (7,2–43,8), riesgo de caída 13,59 s (5,7–26,0). **La duración del clip difiere por clase** (en V4 permitía predecir la clase con F1 macro 0,43, azar ≈ 0,25); V5-CR no la usa como entrada (ventana fija de 2,6 s y tramo de análisis de a lo sumo 5,03 s desde el primer cuadro con pose). 94 videos tienen vista lateral y 23 frontal/posterior/oblicua; 92 son horizontales y 25 verticales; la cámara es fija (trípode) en 85 videos y con paneo, en mano o sin anotar en el resto (detalle en el manifiesto).
