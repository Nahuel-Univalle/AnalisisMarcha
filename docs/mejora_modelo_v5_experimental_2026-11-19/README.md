# Mejora experimental V5 — índice

Estado: **experimental, no integrado**. V4 intacto; modelo activo de la app sin cambios.

| Documento | Contenido |
|---|---|
| `INFORME_TECNICO_V5.md` | Informe completo (fases 1–8) |
| `RECOMENDACION_FINAL.md` | Decisión y criterio para reemplazar V4 |
| `TEXTO_TESIS_3_3_6_y_4_4.md` | Textos para el Capítulo III 3.3.6 y Capítulo IV 4.4 + cambios en Resumen/Conclusiones |
| `FORMULAS_CARACTERISTICAS_V5.md` | Fórmula y significado físico de cada característica |
| `codigo/` | Pipeline V5, pruebas, entrenamiento, evaluación (solo lectura sobre V4) |
| `resultados/` | JSON/CSV de métricas, pruebas, robustez, externos; `dataset_v5_bank.npz`, `oof_V5*.npz`, `modelos_cv_V5*` (checkpoints de fold), logs |
| `figuras/` | fig1–fig7 (PNG 300 dpi) |
| `checkpoints/` | Modelos finales V5-P y V5-S (entrenados con los 117 videos; no estiman exactitud) |

**No añadir a Git sin autorización**: `resultados/dataset_v5_bank.npz`, `resultados/modelos_cv_*`, `resultados/oof_*.npz` y `checkpoints/` (el repositorio ya contiene modelos y no se han hecho commits). No hay videos en esta carpeta.
