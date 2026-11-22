# Conclusiones y recomendaciones (propuesta)

## A. Conclusiones — texto nuevo propuesto
1. Se desarrolló y puso en funcionamiento un sistema web que, a partir de un video, estima puntos corporales con una red preentrenada y clasifica el patrón de marcha en cuatro categorías experimentales mediante un clasificador propio (red convolucional 1D de dos ramas, 17 788 parámetros), entregando probabilidades por clase, advertencias, informe PDF e historial.
2. Una auditoría técnica del preprocesamiento de la versión V4 identificó defectos verificables (espejo de velocidades, escala dependiente de la vista, características de desplazamiento global, falta de corrección de aspecto y duración de ventana asociada a la clase). Su corrección dio lugar a V5-CR, con ventana fija de 2,6 s, 33 características relativas a la cadera e interpolación relativa a la cadera, que es invariante al desplazamiento global de la cámara.
3. En la evaluación interna, V5-CR alcanzó una exactitud de 0,860 y un F1 macro de 0,785 (V4 activo: 0,851 y 0,744). La mejora global no fue estadísticamente concluyente; solo la clase riesgo de caída mostró una mejora respaldada (F1 de 0,378 a 0,581), mientras que la esclerosis múltiple empeoró de forma no concluyente y la calibración sin ajustar fue peor.
4. Las limitaciones del conjunto de datos —117 videos, 67 grupos técnicos (27 provisionales), etiquetas sin validación clínica individual y fuerte asociación entre la fuente de grabación y la clase— impiden atribuir con certeza el rendimiento a la marcha y impiden afirmar generalización o validez clínica.
5. El sistema informa un resultado no concluyente cuando no hay información corporal suficiente y nunca sustituye al modelo por otro de forma automática; sus resultados son una orientación y no un diagnóstico médico.
6. La aplicación quedó verificada en un entorno aislado con pruebas automatizadas y de navegador (flujo completo, reproductor, informe PDF A4 unificado con la pantalla, historial y administración, control de acceso por propietario); la gestión de los informes históricos conserva sus registros y declara la indisponibilidad de los PDF que nunca se almacenaron.

## A. Recomendaciones — texto nuevo propuesto
1. Ampliar el conjunto de datos con más sujetos por clase (especialmente Parkinson y riesgo de caída), con **fuentes de grabación mezcladas dentro de cada clase**, identidad verificada y etiquetas respaldadas por valoración clínica.
2. Realizar una **validación externa y clínica** con videos y sujetos no usados en el diseño, y repetir la sonda de metadatos con las características de V5-CR.
3. Evaluar estrategias para reducir la dependencia de la fuente de grabación (estandarización del protocolo de captura, vista lateral con cámara fija) y considerar calibración de cámara para medidas en unidades físicas.
4. Guardar las curvas de entrenamiento y los registros completos de cada experimento en futuras versiones.
5. Incorporar una cola de trabajos para la inferencia y pruebas en navegadores y dispositivos adicionales; ejecutar las pruebas automatizadas también contra un entorno de preproducción.
6. Mantener el carácter orientativo del sistema y revisar con profesionales de salud la redacción de los resultados y las advertencias antes de cualquier uso con usuarios reales.
7. Confirmar los cambios en el control de versiones (commit) y documentar el procedimiento de actualización de modelos (hashes y respaldo).

## B. Se conserva
Conclusiones sobre el desarrollo web, usabilidad y arquitectura que no cambiaron; el carácter de prototipo.

## C. Se reemplaza
Conclusiones que atribuyan los resultados a V4, que afirmen identificación temprana demostrada o que no mencionen las limitaciones de la validación interna.

## D. Figuras/tablas
Ninguna (referir a las tablas del 4.4).

## E. Fuentes
`04_METRICAS_Y_COMPARACIONES/METRICAS_Y_COMPARACIONES.md`, `03_DATASET_…`, `08_PRUEBAS_…`, `10_INFORMES_…`, `14_AUDITORIA_FINAL/PENDIENTES_Y_EVIDENCIAS_FALTANTES.md`.
