# Revisión de la aplicación para la defensa - 19 de noviembre de 2026

## Dictamen

**No doy todavía el software por completamente verificado para una demostración de defensa.** El flujo nuevo funciona en las pruebas técnicas aisladas y V5-CR está seleccionado también en el entorno habitual, pero faltan las pruebas visuales/interactivas de escritorio y móvil. Además, la descarga de un PDF histórico del entorno habitual devuelve 404 y no hay archivos canónicos de sus 79 informes en la ruta configurada.

Puede prepararse un ensayo del flujo nuevo con un caso técnico y PDF nuevo. No debe presentarse como aprobada la navegación visual ni la descarga de los informes históricos.

## Entorno habitual: lectura segura

- Configuración real: PostgreSQL `127.0.0.1:5433`, base `analisis_marcha_db`, contenedor existente `analisis_marcha_postgres`. Se inició el contenedor; no se cambiaron `.env`, volúmenes, usuarios ni esquema.
- No hay variable de entorno que fuerce V4. La configuración y la respuesta de `/api/admin/summary` seleccionan `gait_deep_v5exp_V5CR_7e9ed60965fe`.
- SHA-256: `7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade`.
- Métricas consultadas: exactitud interna 0,8598; F1 macro 0,7852. No se modificaron las métricas ni se entrenó el modelo.
- Base existente: 18 usuarios, 169 análisis, 173 videos y 79 informes. Se compararon recuentos y huellas del contenido completo de nueve tablas antes/después. **La base habitual permaneció sin cambios.** Evidencias: `BD_ANTES.json`, `BD_DESPUES.json` y `CONSERVACION_FINAL.json`.
- Los análisis históricos conservaron sus versiones; la consulta de parámetros encontró 74 referencias a V4 BN y 9 al V4 anterior. No se atribuyó V5-CR a resultados antiguos ni a registros que carecen de versión.

La inspección autenticada utilizó sesiones técnicas firmadas temporalmente en memoria para solicitudes **GET**, sin cambiar contraseñas, roles ni cuentas. Esto comprueba los endpoints y permisos indicados; no equivale a probar el formulario de inicio de sesión en un navegador.

## Qué se comprobó y qué no

| Elemento | Evidencia ejecutada | Estado |
|---|---|---|
| Modelo en entorno habitual | Configuración efectiva, disponibilidad, hash y API administrativa | Verificado |
| Inicio y carga | GET de `/`, `/login`, `/dashboard`, `/analisis/subir-video` | Respuesta HTTP verificada; interfaz no revisada visualmente |
| Resultados, evaluación e informe | GET de sus rutas protegidas | Rutas disponibles; contenido e interacciones del navegador pendientes |
| Historial habitual | GET autenticado de resumen, análisis, informes y `/seguimiento` | Consulta verificada; registros conservados |
| Administración habitual | GET autenticado de panel, análisis, informes y resumen; solicitud sin sesión rechazada | API/rutas verificadas; presentación y filtros pendientes |
| Carga e inferencia desde video | Flujo completo con video real de investigación en la base técnica del puerto 55432 | Verificado por HTTP en entorno aislado |
| Carga en base habitual | No se enviaron videos ni se añadieron registros | Pendiente; se evita afectar a datos de usuarios |
| PDF nuevo | Generación, descarga y revisión visual de dos páginas; pruebas de presentación | Verificado en entorno técnico |
| PDF antiguo compatible | Descarga de un PDF técnico de la caché anterior y comparación de bytes | Verificado para el archivo compatible consultado |
| PDF histórico habitual | 79 registros sin archivo canónico en la ruta configurada; GET consultado devuelve 404 | No disponible/no aprobado |
| Escritorio y móvil | Inventario de herramientas sin aplicaciones/navegadores y errores de conexión | No ejecutado/no aprobado |

Las rutas de carga/resultados responden, pero son páginas con estado de cliente: un GET 200 no acredita su representación ni los pasos del formulario. La ruta correcta de carga es `/analisis/subir-video`; un primer sondeo a `/analisis` devolvió 404 por usar una dirección que no es la del flujo. No se creó un acceso nuevo innecesario para ocultar ese resultado.

## Cambios exclusivamente de presentación del PDF

1. Se retiraron las fracciones crudas de confianza y probabilidades que duplicaban el porcentaje mostrado.
2. Se reducen decimales de presentación y se eliminan ceros sobrantes. El ritmo legado usa como máximo una cifra decimal; otras magnitudes usan hasta tres, conservando cifras significativas si un valor pequeño quedaría falsamente en cero.
3. Se eliminó la repetición de identificadores internos como «Marcha normal. normal». El identificador sigue en los datos almacenados.
4. Se explicó que el ritmo por picos V5-CR procede de la primera ventana seleccionada de 2,6 s y no es un conteo clínico validado. Las mediciones auxiliares legadas usan otro cálculo/tramo de video y no son directamente comparables ni entradas del clasificador V5-CR.
5. La nueva generación usa la caché `canonical-v5-presentation`. Se mantiene la lectura de la caché anterior `canonical-v4` cuando su validación de origen es compatible. Los archivos anteriores no se sobrescriben ni eliminan.

No se cambiaron las cantidades científicas de análisis, probabilidades, características, estadísticas del escalador ni pesos. La función de lectura y validación científica `canonicalDocument` se conservó exactamente; el redondeo se aplica al texto del renderizador. Tampoco se regeneraron PDF ni se actualizaron `pdfUrl` de informes de la base habitual.

Los archivos de funcionamiento modificados en esta revisión son `src/lib/analysis/canonicalPdf.ts`, la ruta `src/app/api/me/reports/[id]/pdf/route.ts` y el nuevo helper `src/lib/analysis/pdfPresentation.ts`. Los dos archivos existentes se respaldaron en `respaldo_previo/` antes de editarlos. Se añadió soporte de directorio de evidencias al arnés E2E y comprobaciones de conservación de caché para no sobrescribir los resultados de integración anteriores.

## Pruebas y limitaciones de las evidencias

- `PRUEBAS_PRESENTACION_PDF.json`: ocho comprobaciones de redondeo, identificadores, conservación de valores pequeños, eliminación de texto redundante, salida PDF y ausencia de mutaciones en los datos de origen.
- `e2e/PRUEBAS_E2E.json`: pruebas del flujo nuevo, permisos, persistencia, historial, PDF y entradas negativas, con un video existente de investigación. El entorno es el contenedor técnico `gait-v5cr-integration-20261119`, base `gait_v5cr_test`, puerto 55432, con Cloudinary desactivado. No se usaron pacientes sintéticos ni datos de usuarios habituales.
- `REVISION_ENTORNO_HABITUAL.json`: respuestas GET, versión efectiva y estado del archivo canónico/PDF habitual.
- `CONSERVACION_FINAL.json`: nueve tablas habituales sin cambios, 26 artefactos de modelos comparados con el manifiesto de la integración anterior y validación científica canónica idéntica al respaldo.
- `EXIT_*.json`: códigos de salida de las comprobaciones de esta revisión. Los logs y resultados de la integración anterior se conservaron en su carpeta original.
- Las dos páginas del PDF de ejemplo se renderizaron e inspeccionaron: sin recortes ni superposiciones observados; se verificaron las aclaraciones y la ausencia de decimales extensos/repeticiones solicitadas.

Resultado final de las comprobaciones ejecutadas: **8/8 de presentación y 21/21 del flujo HTTP aislado**. TypeScript, ESLint y build terminaron con código 0. También se comprobó el texto y se revisaron visualmente las dos páginas del PDF descargado por HTTP, no solo la muestra de formato. Las pruebas de pantallas siguen pendientes. El build conserva la advertencia de trazado de archivos del servicio PDF ya observada en la integración anterior; no impidió compilar.

Se conservó una incidencia intermedia en `E2E_CACHE_ANTIGUA_INCOMPATIBLE.log`: el primer PDF técnico elegido pertenecía a una versión de presentación anterior y ya no coincidía con el hash de origen que exige la validación actual. No se debilitó esa validación ni se borró el archivo. La prueba se ejecutó después sobre el PDF técnico más reciente compatible y comparó sus bytes. **Esto no acredita acceso a todos los PDF antiguos**, y en particular no resuelve los archivos ausentes del entorno habitual.

## Revisión visual no disponible

La herramienta devolvió:

- `The browser access host is unavailable`.
- `Computer Use native pipe is unavailable ... El sistema no puede encontrar el archivo especificado. (os error 2)`.

Por ello no se aprobaron diseño de escritorio/móvil, selección de archivos, estados de carga, reproducción de videos, navegación, filtros ni descarga mediante botones. Las pruebas HTTP se describen por separado.

La lista concreta de ejecución está en **`LISTA_MANUAL_DEFENSA.md`**: incluye tamaños 1366 × 768 y 390 × 844/360 × 800, cuentas USER/ADMIN, rutas reales, video de ensayo, entradas negativas, resultados, historial, PDF y administración. Todos sus casilleros visuales siguen pendientes.

## Qué falta antes de decir «listo para la defensa»

1. Completar el ensayo manual de escritorio y móvil, incluido inicio de sesión, carga, videos, resultados, historial, descarga y administración.
2. Ensayar un caso técnico nuevo en el entorno elegido para la demostración. La carga completa de esta revisión se ejecutó en el entorno aislado; la base habitual se revisó sin escrituras.
3. Localizar los archivos canónicos/PDF históricos originales o declarar expresamente que su descarga no forma parte del caso demostrativo. No se deben reconstruir probabilidades ausentes ni cambiar sus resultados para hacerlos descargables.
4. Preparar el caso y su PDF antes de la defensa; comprobar la descarga nuevamente desde el navegador utilizado. Mantener el carácter orientativo y no diagnóstico.

No se modificó la tesis, no se reentrenó ni alteró el modelo, no se eliminaron checkpoints, métricas, respaldos o resultados históricos y no se hicieron commits ni push.

El contenedor técnico del puerto 55432 quedó detenido, con sus datos conservados. El PostgreSQL habitual del puerto 5433 permanece iniciado. Los servidores temporales de revisión se detuvieron; para la revisión manual se debe iniciar `npm run dev`.
