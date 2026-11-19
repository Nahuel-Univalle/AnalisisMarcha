# Ficha técnica e inventario verificable del dataset V4

Fecha de inspección: 18 de noviembre de 2026 (America/La_Paz).

Repositorio inspeccionado: `C:\Users\fnahu\Desktop\GITMarcha\AnalisisMarcha`.

Modelo: `gait_deep_v4exp_M1_BN_recalibrated_candidate_v1`.

## Resultado y alcance

Se recuperaron los **117 registros únicos y sus 117 archivos de video locales**, sin registros faltantes. Los IDs, etiquetas, IDs de sujeto y grupos coinciden entre el NPZ, el manifiesto filtrado y la tabla de muestras. También coincide el orden de los 117 registros. El manifiesto completo contiene 137 filas: 117 incluidas y 20 excluidas. Estas últimas se detallan por ID y motivo en `excluidos_del_manifiesto.csv`; no son registros perdidos del dataset usado.

| Categoría registrada | Código | Videos | Grupos de sujeto |
|---|---:|---:|---:|
| Normal | 0 | 58 | 30 |
| Parkinson | 1 | 26 | 7 |
| Esclerosis múltiple | 2 | 22 | 21 |
| Riesgo de caída | 3 | 11 | 9 |
| **Total** | | **117** | **67** |

Los nombres originales, incluido el prefijo `Escleorosis`, se conservaron sin corregirlos ni generar nuevos identificadores. La categoría es una etiqueta registrada, no un diagnóstico clínico certificado.

## Identificación del dataset exacto

La configuración del candidato declara `dataset = outputs/dataset_v4_4class/dataset_v4_preview.npz`, `n_samples = 117`, `n_subjects = 67` y el orden de las cuatro clases. La sección `bn_recalibration.data` vuelve a identificar ese NPZ. El SHA-256 de los pesos locales coincide con el declarado en la configuración y con `step19_candidate/CANDIDATE_SHA256.txt`:

`7b4ac547ff80367b74ddf93c95a9deae82c44f36f3c671f63eb5a4a82c53400d`.

El script histórico `step19_candidate/build_candidate.py` toma las entradas de `step18_bn/bn_recal.py`; este último lee la variante `M1_principal` definida en `step12_training/train_protocol_v2.py`, que apunta al mismo NPZ. Esos scripts se leyeron como texto y **no se ejecutaron ni importaron**.

El nombre «preview» y el campo `purpose` del JSON de metadatos describen la creación inicial para auditoría. Los scripts posteriores y la configuración documentan su utilización en el modelo final y la recalibración. No se tomó como dataset del candidato la variante M3 de `step5/`, el dataset V1 de `data/video_training/deep/dataset.npz`, datos de sensores ni videos de usuarios de `uploads/`.

El NPZ inspeccionado contiene `X_seq[117,68,96]`, `X_feat[117,36]`, `y[117]`, `video`, `subject_id`, `split_group`, `class_names`, `window_s`, `start_s` y `end_s`. Se abrió con `numpy.load(..., allow_pickle=False)` únicamente para lectura.

## Significado y procedencia de las siete columnas

| Columna | Fuente y tratamiento |
|---|---|
| ID video | `video` del NPZ, contrastado con `video` del manifiesto y de `samples_v4_preview.csv`, y con el nombre del archivo original. |
| ID sujeto | `subject_id` del NPZ y del manifiesto, contrastado con `split_group` y `subject_mapping_v4.csv`. Es un ID de agrupación del dataset. |
| Categoría | `class_names[y]` del NPZ, contrastado con `class` y `label` del manifiesto, el mapa de etiquetas del modelo y la tabla de muestras. Traducción de presentación al español sin cambiar el código original. |
| Origen | Solo se atribuye una fuente cuando existe evidencia explícita por registro. Las reglas heurísticas de `source_of()` no acreditan una institución, autor o repositorio de origen. |
| Duración | Medición nueva con FFprobe sobre cada archivo original de `video_path`, en segundos, usando `stream.duration` del primer flujo de video. Estaba disponible en 117/117; no fue necesario recurrir a `format.duration` ni a OpenCV. |
| Resolución | `stream.width × stream.height` obtenido con FFprobe en cada original. Dimensiones codificadas, sin aplicar el redimensionamiento del preprocesamiento. La rotación declarada se conserva en la trazabilidad. |
| Etiqueta validada | Se escribe «Etiqueta registrada: [clase] ([código]). Sin validación clínica individual acreditada». La concordancia entre archivos acredita el registro de la etiqueta, no la condición clínica. |

La duración es numérica en el Excel y el CSV. En Excel se muestra con la unidad `s`; el valor almacenado está en segundos. `trazabilidad_por_video.csv` conserva la duración del flujo, la del contenedor y la base elegida. Los seis decimales reproducen la salida de FFprobe y no deben interpretarse como precisión clínica de medición.

Las dimensiones originales y los tiempos completos no se sustituyen por `max_dim = 720`, `target_fps = 15`, la ventana nominal de 5,03 s, los límites de segmento o el tamaño de secuencia [68,96]. El inventario describe los archivos locales originales del pipeline; no certifica que sean archivos nativos de cámara sin ediciones anteriores.

## Cobertura verificada y faltante

Cada celda siguiente expresa **verificados / faltantes por video**. «Faltante» significa que no se acreditó ese dato; escribir un marcador de ausencia en una celda no cuenta como verificación del campo.

| Categoría | ID video | ID sujeto como grupo | Categoría | Origen: atribución documentada | Duración | Resolución | Etiqueta registrada | Validación clínica individual |
|---|---|---|---|---|---|---|---|---|
| Normal (58) | 58 / 0 | 58 / 0 | 58 / 0 | 0 / 58 | 58 / 0 | 58 / 0 | 58 / 0 | 0 / 58 |
| Parkinson (26) | 26 / 0 | 26 / 0 | 26 / 0 | 0 / 26 | 26 / 0 | 26 / 0 | 26 / 0 | 0 / 26 |
| Esclerosis múltiple (22) | 22 / 0 | 22 / 0 | 22 / 0 | 0 / 22 | 22 / 0 | 22 / 0 | 22 / 0 | 0 / 22 |
| Riesgo de caída (11) | 11 / 0 | 11 / 0 | 11 / 0 | 5 / 6 | 11 / 0 | 11 / 0 | 11 / 0 | 0 / 11 |
| **Total (117)** | **117 / 0** | **117 / 0** | **117 / 0** | **5 / 112** | **117 / 0** | **117 / 0** | **117 / 0** | **0 / 117** |

`resumen_por_categoria.csv` y la hoja `Resumen` desglosan estos conteos, la ausencia de URL original y la documentación parcial de plataforma.

### Origen: niveles de evidencia

- **5 atribuciones documentadas:** `RiesgoCaida1`, `RiesgoCaida2`, `RiesgoCaida5`, `RiesgoCaida6` y `RiesgoCaida7`. `source_evidence` en `outputs/dataset_v4_riesgo22/step3/subject_mapping_riesgo22.csv` registra «Mission Gait (marca de agua)». La misma atribución está en `video_status_riesgo22.csv::fuente_visible`. Se conserva como atribución documental por marca de agua, sin afirmar una cadena de adquisición certificada, licencia o diagnóstico.
- **4 registros con plataforma documentada, sin atribución original acreditada:** `RiesgoCaida10`, `RiesgoCaida11`, `RiesgoCaida19` y `RiesgoCaida22`. La documentación menciona TikTok. Las cuentas se omiten de los entregables. El campo mantiene «Origen no acreditado» y añade la plataforma como evidencia parcial.
- **108 registros sin atribución acreditada ni esa referencia de plataforma.** Incluyen los 84 normales/Parkinson, los 22 de EM y `RiesgoCaida4` y `RiesgoCaida9`. Por tanto, **112/117 carecen de atribución original acreditada**, incluidos los cuatro con plataforma TikTok.
- No se encontró URL individual de adquisición o publicación original para los 117 en los manifiestos y documentación revisados. **0/117 tienen procedencia original completamente trazable por URL/documento primario.**

`build_manifest_v4.py::source_of()` asigna `lab_A`, `clinic_848x478_60fps`, `social_vertical` u `other_horizontal` a partir de clase, dimensiones y orientación. No se convirtieron esas descripciones en nombres de laboratorios ni fuentes confirmadas. La referencia a una «sala Mission Gait» para `Escleorosis12` y `Escleorosis13` respalda la comparación visual de sujetos del informe previo; sin una atribución primaria por archivo no se elevó a origen acreditado.

### Sujetos y validación clínica

Los 117 registros conservan sus IDs documentados, equivalentes a 67 grupos de partición. El manifiesto identifica 90 videos en 40 grupos con estado `confirmed` y 27 videos en 27 grupos `provisional`. Los 40 grupos no son 40 identidades certificadas por registros clínicos: 37 proceden de IDs de nombre de archivo en normal/Parkinson y 3 de agrupaciones visuales en EM/riesgo. Los 27 grupos provisionales corresponden a 20 de EM y 7 de riesgo. No se crean nuevas identidades ni se interpreta el total de 67 como 67 participantes clínicamente acreditados.

El propio informe de V4 señala que no se sabe si los IDs `NNN_NM` y `NNN_PD` de igual número pertenecen a la misma persona; se preserva su tratamiento como grupos distintos. No se encontraron documentos de diagnóstico individual, controles clínicos o adjudicación profesional vinculados a cada ID que permitan certificar sus etiquetas. La tarjeta del modelo declara su carácter experimental y ausencia de validación clínica. Tampoco una validación técnica de pose, una decisión `KEEP_AS_IS` o una evaluación del modelo equivale a validación clínica de la etiqueta.

## Mediciones originales

| Categoría | Duración mínima–máxima del flujo original (s) | Resoluciones y número de archivos |
|---|---|---|
| Normal | 3,400000–12,866667 | 1920 × 1080: 58 |
| Parkinson | 6,733300–19,980000 | 1920 × 1080: 26 |
| Esclerosis múltiple | 7,233333–43,833333 | 478 × 850: 17; 848 × 478: 2; 320 × 568: 1; 424 × 848: 1; 720 × 1280: 1 |
| Riesgo de caída | 5,694244–26,016667 | 848 × 478: 6; 720 × 1280: 1; 478 × 850: 3; 576 × 1280: 1 |

Invocación aplicada a cada ruta original, sin recortar, decodificar ni generar videos:

```text
ffprobe -v error -select_streams v:0 -show_entries stream=index,codec_name,width,height,duration,nb_frames,avg_frame_rate:stream_side_data=rotation:format=duration,size -of json <ruta_original>
```

La versión exacta de FFprobe y las respuestas técnicas seleccionadas están en `auditoria_verificable.json`. No se exportaron etiquetas de metadatos que pudieran contener nombres personales.

## Duplicados, coherencia y límites

- 117 IDs únicos en el NPZ y 137 IDs únicos en el manifiesto completo. Ninguna ruta incluida está duplicada.
- 0 discordancias de ID, etiqueta, grupo o pertenencia entre NPZ, manifiesto, muestras y mapeo de sujetos. Ningún grupo de partición cruza clases.
- Las dimensiones nuevas coinciden con las del manifiesto en los 117. No hay discrepancias de duración superiores a 0,05 s respecto a los tiempos históricos redondeados del manifiesto.
- Se calcularon SHA-256 de los **138 archivos de `videos/`**, incluidos los excluidos: no hay archivos byte a byte idénticos. Tampoco hay tensores `X_seq` o `X_feat` exactamente repetidos entre los 117 del NPZ.
- Los hashes de los 11 archivos incluidos de riesgo coinciden con el sondeo histórico de V4. Para los otros 106, este inventario establece una huella actual y concilia ruta, dimensiones y duración. No se certifica retrospectivamente una identidad binaria histórica donde no se haya usado un hash por archivo de esa etapa.
- La auditoría previa `near_duplicates_riesgo22.json` señala similitud perceptual `RiesgoCaida1`–`RiesgoCaida7` y una coincidencia de fotogramas `RiesgoCaida2`–`Escleorosis12`. `technical_probe_riesgo22.csv` también conserva esos indicadores. Son alertas de una revisión anterior, **no prueba de duplicación ni de identidad compartida**; los SHA-256 actuales son distintos y el informe de V4 trata a las personas de EM y riesgo como distintas. Se conserva la incertidumbre, sin fusionar grupos ni cambiar etiquetas.
- `step3/subject_mapping_riesgo22.csv` registra además `RiesgoCaida3`–`RiesgoCaida4` como posible duplicado no confirmado. El primero está excluido. No se realizó una nueva inspección visual exhaustiva de todos los cuadros; los hashes descartan duplicación exacta de archivos, no recortes, reediciones o semejanzas de contenido.
- Los videos antiguos de riesgo reutilizaban los mismos nombres; el informe del Paso 1 advierte que `data/video_training/manifest.csv` y sus landmarks corresponden a la colección antigua. Igualmente, los archivos `VideoEscleorosis*` de la auditoría V2 no se confundieron con los `Escleorosis*` actuales de V4. Los hallazgos de procedencia de aquella colección no se transfieren por parecido del nombre.

## Archivos originales que sustentan cada dato

Todas las rutas de esta sección son relativas a la raíz del repositorio. `auditoria_verificable.json::checks.source_sha256` contiene sus huellas SHA-256 para identificar la versión leída.

| Archivo o conjunto original | Información extraída |
|---|---|
| `models/gait_deep_v4exp_bn_candidate_v1/*_config.json` y `*_label_map.json` | Versión del candidato, ruta exacta al NPZ, cantidades esperadas, clases y códigos, referencia a recalibración. |
| `models/gait_deep_v4exp_bn_candidate_v1/*.pt` | Solo SHA-256 para contrastar la identidad del artefacto; no se cargaron pesos ni ejecutó el modelo. |
| `models/gait_deep_v4exp_bn_candidate_v1/README.md` | Tarjeta del modelo, dataset utilizado y límites de validación clínica. |
| `outputs/dataset_v4_4class/dataset_v4_preview.npz` | Los 117 IDs realmente presentes, etiquetas numéricas, grupos, secuencias/features y límites de ventana almacenados. |
| `outputs/dataset_v4_4class/manifest_v4_preview.csv` | Rutas originales, nombres, IDs de sujeto, grupos, etiquetas, inclusión/exclusión, segmentos y estado del agrupamiento. |
| `outputs/dataset_v4_4class/samples_v4_preview.csv` | Conciliación de los 117 registros y distinción entre duración original y ventana analizada. |
| `outputs/dataset_v4_4class/subject_mapping_v4.csv` | Agrupaciones existentes, estado confirmed/provisional y pertenencia de videos. |
| `outputs/dataset_v4_4class/dataset_v4_preview_meta.json`, `build_dataset_v4_preview.py` | Tamaños del dataset y política de procesamiento; mecanismo de filtrado por `include_in_preview`. |
| `outputs/dataset_v4_4class/build_manifest_v4.py`, `INFORME_PASO4_v4.md` | Criterios de exclusión, construcción heurística de `source`, origen de las agrupaciones y sus limitaciones. |
| `outputs/dataset_v4_4class/step12_training/train_protocol_v2.py`, `step18_bn/bn_recal.py`, `step19_candidate/build_candidate.py` | Cadena documental de utilización de M1 y del mismo NPZ por el candidato. Solo lectura del código. |
| `outputs/dataset_v4_4class/step19_candidate/CANDIDATE_SHA256.txt` | Hash congelado de los pesos del candidato. |
| `outputs/dataset_v4_riesgo22/step3/subject_mapping_riesgo22.csv`, `video_status_riesgo22.csv` | Evidencia explícita de fuente visible para riesgo. No se exportan cuentas ni nombres de personas. |
| `outputs/dataset_v4_riesgo22/technical_probe_riesgo22.csv`, `near_duplicates_riesgo22.json` | Hash histórico de riesgo y alertas previas de similitud. |
| `outputs/dataset_v4_riesgo22/INFORME_PASO1_riesgo22.md`, `step3/INFORME_PASO3_riesgo22.md` | Reemplazo de la colección antigua, criterios de segmento y límites del mapeo de sujetos. |
| `outputs/dataset_v4_ms28/_build_manifest_preview.py` | Procedimiento precursor: normal/PD copiados del manifiesto previo y colección EM nueva por escaneo local. |
| `outputs/dataset_v3/dataset_v3_manifest.csv`, `outputs/dataset_audit_v2/dataset_v2_provenance_report.json` | Antecedentes de documentación clínica ausente para normal/PD y distinción respecto a colecciones antiguas; no se usan para reasignar origen a EM/riesgo de V4. |
| `videos/normal/`, `videos/parkinson/` (incluidas subcarpetas de severidad), `videos/esclerosis_multiple/`, `videos/riesgo_caida/` | Archivos originales medidos con FFprobe y comprobados mediante SHA-256; no se copian a los entregables. |

Se accedió directamente a archivos locales, incluidos los ignorados por Git: tanto el NPZ como los videos están disponibles y `git check-ignore` confirma su exclusión del seguimiento. Había cambios de código previos en el repositorio; no se editaron. Toda escritura de entregables se limita a esta carpeta nueva de documentación. Los scripts auxiliares y las previsualizaciones de verificación se mantienen fuera del repositorio, en una carpeta temporal.

## Entregables y trazabilidad

- `inventario_v4.xlsx`: hojas `Resumen` e `Inventario`; esta última contiene exactamente las siete columnas y 117 registros, con filtro y cabecera inmovilizada.
- `inventario_v4.csv`: los mismos 117 registros y siete columnas, en UTF-8 con BOM.
- `resumen_por_categoria.csv`: conteos verificados/faltantes por campo y categoría.
- `trazabilidad_por_video.csv`: ruta local, fila de manifiesto, índice NPZ, estado de sujeto, segmento, mediciones técnicas, hash y referencia de origen para cada ID. Permite localizar individualmente los campos no acreditados.
- `excluidos_del_manifiesto.csv`: 20 IDs excluidos, con decisión y motivo original.
- `auditoria_verificable.json`: conciliaciones, resultados técnicos, hashes de fuentes, casos faltantes y discrepancias. Los arrays de registros y archivos faltantes están vacíos.
- `texto_tesis_3_3_6_1.md`: texto académico breve para incorporación manual; no se editó el documento Word.

No se entrenó, recalibró ni ejecutó inferencia. No se modificaron código, modelos, manifiestos, videos, bases de datos, credenciales o documentos originales. No se publicaron archivos ni se incluyeron fotogramas, rostros, nombres de participantes o cuentas personales en los entregables.
