# 4.3 Pruebas del sistema y 4.6 Conclusión de pruebas (propuesta)

## A. Texto nuevo propuesto
**4.3 Pruebas del sistema.** Las pruebas se ejecutaron en dos niveles. (1) *Pruebas del modelo y del preprocesamiento*: 28 comprobaciones numéricas del preprocesamiento (21 de V5 más 7 demostraciones de defectos de V4), 12 de V5-C y un criterio específico de V5-CR sobre 633 ventanas reales (0 ventanas con diferencia ante una cámara que sigue a la persona); y 24 comprobaciones del predictor desplegado (artefactos, hashes, orden de características, imputación, dimensiones, equivalencia con el evaluador en 117 de 117 videos, videos reales de las cuatro clases y casos negativos). (2) *Pruebas de integración y de interfaz*, ejecutadas en un entorno aislado con una base PostgreSQL técnica y cuentas de prueba: 21 comprobaciones HTTP de extremo a extremo (inicio de sesión, carga, pose, inferencia V5-CR, persistencia, historial, informe, PDF, administración, permisos y entradas negativas), 22 de gestión de PDF e historial (404 explícito de informes históricos, propiedad, caché antigua, PDF nuevo), 6 de descarga en el cliente, 12 de presentación y 37 de integridad de artefactos. Las pruebas en navegador (Chrome controlado por protocolo de depuración) comprobaron el reproductor durante el análisis (22 a 23 comprobaciones por video con un video horizontal en formato MOV, uno vertical y uno horizontal en MP4), la descarga del PDF con el botón real (8) y el historial con los botones «Ver informe» y «Descargar PDF» (17). Compilación y análisis estático: TypeScript sin errores, ESLint sin errores y compilación de producción correcta.

**Resultados y errores corregidos.** Todas las baterías finales terminaron sin comprobaciones fallidas. Durante las pruebas se detectaron y corrigieron, entre otros: un fallo de inferencia en la aplicación habitual causado por un límite de tiempo que se presentaba como «modelo no disponible» (ahora se distingue la causa y se amplía el límite); un error de reproducción al repetir el video antes de terminar el análisis (el reproductor se desmontaba ante un error de decodificación del final del archivo); y un PDF de texto plano con identificadores internos y contenido distinto del informe en pantalla (ahora ambos comparten el modelo de datos).

**Alcance y limitaciones de las pruebas.** Las pruebas automatizadas no se ejecutaron contra el servidor habitual con datos reales ni con almacenamiento en la nube; las pruebas sobre la base habitual fueron de solo lectura y manuales del propietario. La batería HTTP se ejecutó varias veces con el mismo resultado y se cuenta una vez. No se probaron otros navegadores ni dispositivos móviles reales, y la apertura del PDF con un visor se comprobó a nivel del documento, no de su pintado.

**4.6 Conclusión de pruebas.** Las pruebas realizadas respaldan que el flujo completo —carga, estimación de pose, inferencia con V5-CR, resultado, registro, historial, informe PDF y administración— funciona de manera consistente con el modelo configurado y con los controles de acceso, que el predictor desplegado reproduce exactamente al evaluador, y que los casos sin información corporal suficiente producen un resultado no concluyente. No acreditan el desempeño clínico del modelo, que solo ha sido evaluado internamente.

## B. Se conserva
La metodología de pruebas (niveles, casos de prueba por requerimiento) y las pruebas históricas de V4, rotuladas como tales.

## C. Se reemplaza
Los conteos de pruebas y resultados de V4 en las tablas 4.3 y 4.4 (si corresponden a pruebas del sistema), y cualquier afirmación de pruebas con el servidor habitual no respaldada por un registro.

## D. Figuras/tablas
`08_PRUEBAS_DEL_SISTEMA/PRUEBAS_EJECUTADAS_RESUMEN.csv` (una fila por batería, con fecha, entorno, totales y limitaciones); capturas 07–14.

## E. Fuentes
`08_PRUEBAS_DEL_SISTEMA/evidencias/` y los archivos indicados en la columna «evidencia» del CSV (`fase3_pruebas.json`, `fase8_pruebas_c.json`, `fase8_prueba_cr.json`, `test_deep.log`, `PRUEBAS_E2E.json`, `PRUEBAS_HTTP_AISLADAS.json`, `navegador_*.json`).
