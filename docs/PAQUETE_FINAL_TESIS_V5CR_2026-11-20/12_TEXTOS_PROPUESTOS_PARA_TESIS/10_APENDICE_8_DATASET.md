# Apéndice 8 — Ficha técnica e inventario del dataset (actualización propuesta)

## A. Texto nuevo propuesto
**Ficha técnica.** El conjunto contiene 117 videos únicos (58 normales, 26 de Parkinson, 22 de esclerosis múltiple y 11 de riesgo de caída), agrupados en 67 grupos técnicos de sujeto (30, 7, 21 y 9). El inventario por video (identificador, grupo técnico, estado del grupo —con identidad registrada o provisional—, clase registrada, fuente de grabación, orientación, vista, estilo de cámara, duración, fotogramas por segundo y resolución) se proporciona en `MANIFIESTO_TRAZABILIDAD_117_VIDEOS.csv`; no incluye rutas ni datos personales. Las etiquetas son registradas y **ninguna cuenta con validación clínica individual**; 112 de 117 videos carecen de atribución de origen acreditada y ninguno tiene procedencia trazable por un documento primario. Se excluyeron 20 videos (18 por pose insuficiente o ausencia de tramo continuo de marcha y 2 por revisión manual pendiente), detallados con su motivo en `VIDEOS_EXCLUIDOS_20_CON_MOTIVO.csv`. El modelo V5-CR transforma cada video en hasta siete ventanas de 2,6 s (633 en total; media 5,4 por video).

**Tabla resumen.**
| Clase | Videos | Grupos | Grupos provisionales | Fuente de grabación |
|---|---:|---:|---:|---|
| Normal | 58 | 30 | 0 | laboratorio (58) |
| Parkinson | 26 | 7 | 0 | laboratorio (26) |
| Esclerosis múltiple | 22 | 21 | 20 | redes sociales vertical (20), repositorio clínico (2) |
| Riesgo de caída | 11 | 9 | 7 | repositorio clínico (6), redes sociales vertical (5) |
| **Total** | **117** | **67** | **27** | |

**Corrección terminológica.** Donde el apéndice diga «ID de sujeto» o «67 sujetos», debe decir «ID de grupo técnico» y «67 grupos técnicos de sujeto». La columna «Etiqueta validada» debe renombrarse «Etiqueta registrada (sin validación clínica individual)».

## B. Se conserva
Las 117 filas del inventario V4 (el conjunto de videos no cambió) con ID, categoría, duración y resolución verificados con FFprobe (`docs/inventario_dataset_v4_2026-11-18/inventario_v4.csv`).

## C. Se reemplaza
La columna «Origen» si afirma procedencias no acreditadas, y los textos que describen la secuencia como 68 × 96 o la ventana de 5,03 s.

## D. Figuras/tablas
`fig_distribucion_dataset`; `RESUMEN_DATASET_POR_CLASE.csv`.

## E. Fuentes
`03_DATASET_Y_METODOLOGIA/`; `docs/inventario_dataset_v4_2026-11-18/ficha_tecnica_y_fuentes.md`, `trazabilidad_por_video.csv`, `excluidos_del_manifiesto.csv`.
