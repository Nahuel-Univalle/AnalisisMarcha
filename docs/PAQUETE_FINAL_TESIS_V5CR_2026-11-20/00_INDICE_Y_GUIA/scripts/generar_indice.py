"""INDICE_DE_ARCHIVOS.md: lista todos los archivos del paquete por carpeta (tamaño en KB)."""
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
DESC = {
    "00_INDICE_Y_GUIA": "Guía de uso e índice", "01_ESTADO_FINAL_DEL_SOFTWARE": "Estado verificado del software y de las funcionalidades", "02_MODELO_V5CR_Y_ARQUITECTURA": "Ficha técnica del modelo V5-CR, capas y parámetros",
    "03_DATASET_Y_METODOLOGIA": "Dataset de 117 videos: manifiesto anonimizado, resumen, excluidos, metodología", "04_METRICAS_Y_COMPARACIONES": "Métricas recalculadas y verificadas, IC95, diferencias, robustez",
    "05_MATRICES_DE_CONFUSION": "Matrices de confusión V5-CR y V4 activo (PNG 300 dpi, SVG, CSV, script)", "06_FIGURAS_Y_GRAFICAS": "Figuras académicas con datos, scripts y pies para Word",
    "07_PREPROCESAMIENTO_Y_FORMULAS": "Preprocesamiento V5-CR y tabla de 33 características", "08_PRUEBAS_DEL_SISTEMA": "Baterías de pruebas realmente ejecutadas y evidencias",
    "09_CAPTURAS_Y_EVIDENCIAS": "Capturas reales de la aplicación (videos ocultos) y pendientes", "10_INFORMES_PDF_E_HISTORIAL": "Gestión de informes PDF e historial; ejemplos de PDF",
    "11_CAMBIOS_POR_CAPITULO": "Inventario de cambios necesarios en la tesis", "12_TEXTOS_PROPUESTOS_PARA_TESIS": "Textos en español para incorporar al Word (A nuevo, B conservar, C reemplazar, D figuras, E fuentes)",
    "13_FUENTES_Y_TRAZABILIDAD": "Matriz de trazabilidad, hashes, fuentes y discrepancias", "14_AUDITORIA_FINAL": "Informe de auditoría y pendientes",
}
lines = ["# Índice de archivos del paquete\n", "Tamaños en KB. Los videos, checkpoints y datasets pesados NO se copian: sus rutas y hashes están en `13_FUENTES_Y_TRAZABILIDAD/MANIFIESTO_ARCHIVOS_SHA256.txt`.\n"]
total = 0
for d in sorted(p for p in PKG.iterdir() if p.is_dir()):
    fs = sorted(f for f in d.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
    lines.append(f"\n## {d.name} — {DESC.get(d.name, '')} ({len(fs)} archivos)\n")
    for f in fs:
        total += 1
        lines.append(f"- `{f.relative_to(PKG).as_posix()}` ({f.stat().st_size / 1024:.1f} KB)")
lines.append(f"\n**Total:** {total} archivos (sin contar este índice).")
(PKG / "00_INDICE_Y_GUIA" / "INDICE_DE_ARCHIVOS.md").write_text("\n".join(lines), encoding="utf-8")
print(total, "archivos indexados")
