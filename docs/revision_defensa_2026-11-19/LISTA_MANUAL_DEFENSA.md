# Comprobación manual antes de la defensa

**Estado: pendiente.** Estas comprobaciones de navegador no se ejecutaron porque el host visual y el controlador de escritorio no están disponibles. Un HTTP 200 no demuestra que una pantalla se vea bien ni que sus botones funcionen.

## Preparación

1. Entorno habitual: contenedor `analisis_marcha_postgres`, PostgreSQL `127.0.0.1:5433`, base `analisis_marcha_db`. Ya se inició para esta revisión y no se modificaron sus registros.
2. Inicia `npm run dev` y abre `http://localhost:3000`. La entrada de carga es **`/analisis/subir-video`**, no `/analisis`.
3. Usa tus cuentas habituales USER y ADMIN. No cambies permisos, registros, etiquetas ni sujetos para las pruebas.
4. Para ensayar carga/guardado sin añadir datos a la base habitual, utiliza la base técnica `gait_v5cr_test` del puerto 55432 y su cuenta técnica. El arnés `scripts/test-v5cr-e2e.mjs` permite `V5CR_E2E_KEEP_SERVER=1`; establece `V5CR_TEST_REPORT_DIR` a una carpeta nueva para conservar las evidencias anteriores. Los datos de acceso técnicos se guardan localmente en `tmp/v5cr-e2e/browser-test.json`.
5. Si decides ensayar también una carga en el entorno habitual, usa un **nuevo caso técnico de demostración**, claramente identificado, y un video real de investigación. Eso añadirá registros; no reutilices ni edites un análisis histórico. La carga habitual permanece sin verificar en esta revisión.

## Escritorio: 1366 × 768 o mayor

- [ ] Iniciar sesión como USER desde el formulario. Comprobar errores de credenciales y acceso correcto, sin depender de una sesión previa.
- [ ] En `/dashboard`, comprobar navegación, títulos, botones, foco de teclado y ausencia de texto cortado.
- [ ] Abrir `/analisis/subir-video`: seleccionar un video, revisar la previsualización, validar y continuar; comprobar que el botón de análisis no envía solicitudes duplicadas mientras procesa.
- [ ] Para el ensayo controlado, usar el video existente `videos/normal/001_NM_01.MOV`. Si necesitas identificarlo como prueba, usa una copia temporal; no renombres el original.
- [ ] Seguir los pasos de validación y movimiento hasta `/analisis/resultado`. Comprobar carga, mensajes de espera, reproducción del video original/procesado y ausencia de errores en consola.
- [ ] En resultado: clase entre las cuatro admitidas, cuatro porcentajes, confianza y advertencia no diagnóstica. Los porcentajes mostrados están redondeados; no son probabilidades clínicas.
- [ ] En `/analisis/evaluacion`: confirmar que aparecen las características relativas, simetría y ritmo por picos. No interpretar los picos/min como pasos clínicamente verificados.
- [ ] Comprobar en la respuesta de `/api/analysis/video` que `analysis.modelVersion` sea `gait_deep_v5exp_V5CR_7e9ed60965fe`, y que `modelUsed` y `savedToDatabase` sean verdaderos para el caso válido.
- [ ] Probar un archivo inválido y un video sin persona en el entorno técnico. Deben rechazarse o resultar no concluyentes; nunca mostrar clase, confianza ni probabilidades inventadas.
- [ ] En `/seguimiento`, comprobar el nuevo caso, su fecha y resumen; recargar la página. Abrir un caso V4 y confirmar que mantiene su versión original. No editarlo ni eliminarlo.

## PDF

- [ ] Con el **nuevo análisis técnico**, abrir `/analisis/informe`, guardar y descargar el PDF; volver a descargarlo después de recargar la página.
- [ ] Abrir todas las páginas: no debe haber recortes, superposiciones ni caracteres extraños.
- [ ] Comprobar que clase, confianza y cuatro porcentajes coincidan con el resultado, considerando el redondeo de presentación.
- [ ] Comprobar que no aparezcan fracciones largas como `0.948019...` junto a los porcentajes ni el texto «Marcha normal. normal».
- [ ] Verificar la explicación: el ritmo por picos V5-CR usa la primera ventana de 2,6 s; el ritmo legado procede de otro cálculo/tramo y no es directamente comparable. Un valor como 270 picos/min y otro como 61 de ritmo legado no representan la misma medición.
- [ ] Confirmar versión V5-CR y advertencia orientativa/no diagnóstica.
- [ ] **Pendiente conocido en el entorno habitual:** los 79 informes históricos no tienen su archivo canónico en la ruta configurada y la descarga consultada devolvió 404. No marcar su descarga como aprobada, no regenerarlos con información inventada y no usarlos como ejemplo de descarga durante la defensa sin resolver antes el origen de esos archivos.

## Administración

- [ ] Iniciar sesión como ADMIN y abrir `/admin` y `/admin/analisis`; comprobar navegación, tablas, filtros y estados vacíos.
- [ ] Confirmar V5-CR como modelo disponible. En `/api/admin/summary`: exactitud interna `0.8598`, F1 macro `0.7852` y hash `7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade`.
- [ ] Confirmar que las métricas se describen como validación interna, sin presentarlas como rendimiento clínico garantizado.
- [ ] Confirmar que USER no accede a administración y que ADMIN no crea análisis de paciente. No cambiar roles para facilitar la prueba.

## Móvil: 390 × 844; adicionalmente 360 × 800

Repetir las comprobaciones funcionales anteriores en el modo de dispositivo del navegador y, si es posible, en un teléfono real.

- [ ] Abrir/cerrar el menú; todos los destinos y controles deben seguir accesibles.
- [ ] Comprobar selección de video desde el dispositivo y tamaños táctiles de los botones.
- [ ] Comprobar que videos, distribución de clases, mensajes y tablas no salgan del ancho visible; desplazamiento horizontal solo donde la tabla lo requiera.
- [ ] Comprobar que no se oculten confianza, advertencias, acciones de guardar/descargar ni errores.
- [ ] Comprobar estados de carga, teclado, cambios de orientación y regreso desde otra pantalla.
- [ ] Descargar y abrir el PDF en el visor del móvil.

## Criterio de cierre

No dar la demostración completa por aprobada hasta completar escritorio/móvil, ensayar la carga real en el entorno elegido y resolver o declarar expresamente la indisponibilidad de los PDF históricos. Para una demostración limitada al flujo nuevo, prepara un caso técnico con PDF generado y verifica previamente toda la navegación. No atribuyas a V5-CR validación clínica.
