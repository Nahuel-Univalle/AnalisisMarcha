# Pendientes y evidencias faltantes

## A. Evidencias que no se pudieron obtener (y por qué)
| # | Faltante | Motivo | Qué se hizo / cómo obtenerla |
|---|---|---|---|
| 1 | **Word de la tesis** (293 págs.) | No está en el proyecto; los .docx del escritorio son borradores de mayo de 2026 y no se abrieron | Se trabajó con la estructura conocida; `11_CAMBIOS…` lista qué verificar. Proporcionar el Word (solo lectura) para ubicar cada cambio |
| 2 | **Curvas de entrenamiento/pérdida/validación de V5-CR** | El código calcula la pérdida por época pero no la guardó; los logs solo tienen resumen por partición | No se generaron ni se reconstruyeron. Requeriría reentrenar guardando las curvas (fuera de alcance) |
| 3 | **Validación clínica y externa** | No existen datos | Limitación declarada en todos los textos |
| 4 | **Sonda de metadatos recalculada para V5-CR** | Solo existe la de V4 (mismos videos y particiones) | Se cita como referencia heredada; recalcularla con las características de V5-CR es un análisis pendiente (lectura de datos existentes; no requiere reentrenar) |
| 5 | **IC95 de la diferencia de calibración V5-CR – V4 base** | No existe un cálculo bootstrap de ECE calibrada | Solo se citan valores puntuales |
| 6 | **Robustez de V4 activo** | Solo se evaluó V4 base | La tabla/figura lo rotulan «V4 base» |
| 7 | **Procedencia primaria de los videos** | 0/117 trazables por URL o documento | Declarado; no se inventó |
| 8 | **Matrices de V4 activo con calibración** | No hay OOF calibrado de V4 activo | Se compara solo sin calibrar |

## B. Capturas pendientes
Ver `09_CAPTURAS_Y_EVIDENCIAS/INDICE_CAPTURAS.md`: video visible en el reproductor (se ocultó por privacidad), «Ver informe» con visor de PDF en un navegador de escritorio, capturas en el entorno habitual con Cloudinary, vista móvil del resultado y del informe, Firefox/Safari/Edge.

## C. Pruebas pendientes
- Ejecución de las baterías automatizadas **contra el servidor habitual con datos reales** (hoy solo entorno aislado y lecturas de la base habitual).
- Prueba del retroceso explícito a V4 (`GAIT_MODEL_VERSION=v4`) con un video, y de los fallos de modelo por caída nativa o salida inválida.
- Pruebas en otros navegadores y dispositivos reales; revisión visual manual del PDF en visores externos.
- La prueba legada `test_deep_pipeline.py` (V4) no se reejecutó.

## D. Pendientes de documentación y de repositorio
- **Confirmar los cambios en Git:** los cambios de V5-CR y posteriores (17 archivos modificados, 43 elementos sin seguimiento) no están confirmados en un commit; este paquete no hizo commits.
- Ajustar numeración de figuras/tablas al Word; confirmar el contenido de las Figuras 4.9–4.11 y Tablas 4.3–4.4.
- Revisión por el tutor/profesionales de salud de los textos de resultados y advertencias.

## E. Operaciones que requieren autorización expresa del propietario
- Reconstrucción documental de los 64 informes históricos con datos originales (no se hizo ni se hará sin autorización).
- Cualquier escritura en la base habitual, regeneración masiva de PDF, commit/push, entrenamiento de un nuevo modelo o modificación del Word.

## F. Estado de los datos del propietario en la base habitual
Tras las auditorías, el propietario creó 2 informes y 4 análisis nuevos en pruebas manuales; los 79 informes y 169 análisis históricos siguen presentes. Este paquete **no escribió** en la base habitual.
