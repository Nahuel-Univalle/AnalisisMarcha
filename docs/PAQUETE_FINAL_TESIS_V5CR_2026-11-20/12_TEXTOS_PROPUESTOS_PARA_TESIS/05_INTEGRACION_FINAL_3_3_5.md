# 3.3.5 Construcción e implementación — integración final (propuesta)

## A. Texto nuevo propuesto
**Integración del modelo.** El modelo V5-CR (`gait_deep_v5exp_V5CR_7e9ed60965fe`) se integró como modelo principal mediante un predictor específico (`15_predict_deep_video_v5cr.py`) que reproduce el procedimiento de evaluación: antes de cada inferencia verifica el SHA-256 de los pesos, la configuración, el escalador y el mapa de etiquetas, y la coherencia de dimensiones (secuencia 68 × 40, 33 características, cuatro clases). Una prueba de equivalencia sobre los 117 videos del banco mostró que el predictor desplegado produce las mismas secuencias, características, logits y probabilidades que el evaluador (diferencia máxima 0). El modelo V4 se conserva como respaldo, pero no se utiliza automáticamente: si V5-CR falla, el sistema informa el error en lugar de clasificar con otro modelo.

**Análisis y resultados no concluyentes.** La interfaz de programación de aplicaciones ejecuta el análisis de pose y el predictor y aplica un control de calidad: si el seguimiento corporal es insuficiente (tasa de detección menor de 0,45, menos de 15 cuadros con pose, o ninguna ventana utilizable), el análisis se registra como **no concluyente** y no se presentan clase, probabilidades ni confianza. Los fallos del modelo se distinguen por su causa (tiempo máximo excedido, error interno de inferencia o modelo no disponible), con un límite de 300 s y cierre del proceso, y se muestran con mensajes específicos.

**Reproductor de video.** El reproductor del video original es independiente del procesamiento: el usuario puede reproducir, pausar, desplazar y repetir el video durante todo el análisis. El elemento de video no se desmonta ante un error; si el navegador informa un error de decodificación después de haber cargado el video (observado al final de archivos con un último paquete de audio no decodificable), el reproductor se recupera de forma automática y registra el detalle en la consola; si el video no carga, se muestra el error con la opción «Reintentar». La dirección temporal del video local se libera al reemplazarlo o al cerrar la aplicación.

**Informe PDF.** El informe en pantalla y el PDF descargable se construyen desde un único modelo de datos (`reportModel.ts`). El PDF, en formato A4 con texto seleccionable y las mismas fuentes y colores de la interfaz, presenta el resultado, las cuatro probabilidades, las advertencias, las observaciones, los parámetros de marcha, la interpretación, las recomendaciones y la advertencia final, sin identificadores internos. Se genera en el servidor, se valida contra el registro canónico y se almacena con un manifiesto (hash del origen y del documento).

**Historial y administración.** El historial de análisis y la lista de informes guardados leen la base de datos; cada informe con archivo disponible ofrece «Ver informe» y «Descargar PDF», y los informes sin archivo conservan su registro y muestran que no pueden descargarse. El panel de administración muestra el estado y la versión del modelo (con sus métricas internas) y los análisis e informes del sistema.

**Informes históricos.** Se auditaron 79 informes registrados antes del almacenamiento canónico: ninguno tiene PDF original (el generador anterior descargaba el documento directamente en el navegador). El sistema conserva sus registros, indica que el archivo no está disponible y no reconstruye documentos; para 64 de ellos existen probabilidades originales en resultados de pruebas antiguas, pero no se generaron informes reconstruidos. Una caché antigua se acepta solo si su manifiesto y sus hashes coinciden con el registro del propietario.

**Control de acceso.** Las rutas de análisis, historial e informes exigen sesión; el PDF de un informe solo se entrega a su propietario (otra cuenta recibe 404 y sin sesión 401). El administrador accede a los datos agregados del sistema, no a la descarga de informes de pacientes.

## B. Se conserva
La descripción de la arquitectura web, la autenticación por sesión, la base de datos PostgreSQL, el almacenamiento de videos y la secuencia de pantallas (carga, revisión, análisis, resultado, informe).

## C. Se reemplaza
Las descripciones del flujo con V4, del PDF generado por captura de pantalla o con texto plano y las capturas de interfaz que muestren la versión anterior.

## D. Figuras/tablas
`fig_flujo_completo_sistema_V5CR`; capturas 07–14 y 17–20 de `09_CAPTURAS_Y_EVIDENCIAS`; páginas del PDF (`reutilizadas/`).

## E. Fuentes
`src/app/api/analysis/video/route.ts`; `15_predict_deep_video_v5cr.py`; `src/components/analysis/VideoStage.tsx`; `src/lib/analysis/{reportModel,reportPdf,reportPdfStorage}.ts`; `src/components/analysis/SavedReportsList.tsx`; `docs/integracion_v5cr_2026-11-19/INFORME_FINAL_INTEGRACION.md` (equivalencia 117/117); `docs/correccion_inferencia_v5cr_2026-11-19/`; `docs/correccion_reproductor_video_2026-11-19/`; `docs/pdf_informe_unificado_2026-11-19/`; `docs/recuperacion_pdf_historicos_2026-11-19/`; `10_INFORMES_PDF_E_HISTORIAL/`.
