# Informe de auditoría del paquete (2026-11-20)

Auditoría automática: `scripts/auditar_paquete.py` → `AUDITORIA_AUTOMATICA.json` (se vuelve a ejecutar al final). Revisión visual manual de las figuras y capturas por quien preparó el paquete.

## Resultados de las 12 comprobaciones solicitadas
| # | Comprobación | Resultado | Evidencia |
|---|---|---|---|
| 1 | Todas las carpetas tienen material | **Cumple**: 15 carpetas (00–14) con archivos; ninguna vacía | `AUDITORIA_AUTOMATICA.json` (`carpetas`, `carpetas_vacias = []`) |
| 2 | Imágenes abiertas y legibles | **Cumple**: todos los PNG se abren (verificación con Pillow); figuras principales, matrices y capturas inspeccionadas visualmente; se corrigieron solapamientos en 3 figuras (comparación V4–V5-CR, distribución del dataset, características) antes de cerrar | `png_con_problemas = []` |
| 3 | Las matrices corresponden a V5-CR (y V4 activo) | **Cumple**: la absoluta coincide con `comparacion_final.json`; V4 activo se rotula aparte; etiquetas y grupos de ambas fuentes idénticos (comprobado por script) | `05_MATRICES…/LEEME_MATRICES.md` |
| 4 | Métricas reales | **Cumple**: 63/63 valores recalculados desde las predicciones OOF coinciden con los originales | `VERIFICACION_CONTRA_ORIGINALES.csv` |
| 5 | Figuras con fuente | **Cumple**: cada figura incluye «Fuente: Elaboración propia (2026)…» y pie sugerido; su CSV/script en `06…/datos` y `scripts` | `INDICE_FIGURAS_Y_PIES_PARA_WORD.md` |
| 6 | Datos tabulados = figuras | **Cumple**: las figuras se generan desde los CSV del paquete y, en calibración, desde las mismas predicciones OOF que las tablas (los valores graficados son los de las tablas) | scripts de `06` |
| 7 | Los textos no atribuyen a V5-CR cifras de otra versión | **Cumple tras revisión**: las cifras 0,880/0,800 solo aparecen en la fila V5-P de la tabla comparativa; se evitó mezclar V4 base/activo y V5-P/V5-CR | búsqueda en `12_TEXTOS…` |
| 8 | Limitaciones explícitas | **Cumple**: `08_LIMITACIONES.md`, secciones de limitación en 4.4, ficha del modelo, dataset y métricas; se añadió el hallazgo de la sonda de metadatos y el peor ECE sin calibrar | — |
| 9 | Capturas = software real | **Cumple con salvedades**: 20 capturas de la aplicación real (build de producción, entorno aislado, cuentas técnicas), videos ocultos y estado «no se pudo guardar el video en la nube» por Cloudinary desactivado, ambos declarados | `INDICE_CAPTURAS.md` |
| 10 | Sin información privada innecesaria | **Cumple**: 0 correos reales, 0 rutas de usuario, 0 secretos reales (las coincidencias del patrón son `randomBytes(...)` en scripts de captura y el propio informe automático; la contraseña del contenedor PostgreSQL técnico se retiró de los scripts y se pide por la variable `V5CR_TEST_DB_PASSWORD`); sin videos ni checkpoints copiados; manifiesto de 117 videos sin rutas ni texto libre. Las variantes de PDF usan nombre «Usuario de prueba» | `privacidad_conteos` |
| 11 | Sin archivos vacíos ni figuras provisionales presentadas como definitivas | **Cumple**: 0 archivos vacíos; la figura de curvas de entrenamiento **no se generó** y se declara pendiente; la captura «10» se obtuvo tras corregir el flujo | `archivos_vacios = []` |
| 12 | Word y código de la aplicación sin cambios | **Cumple**: el Word no se abrió ni se modificó; 151 archivos de `src/`, `models/`, `scripts/video_training/deep/`, `python_analysis/`, `prisma/` y `package.json` tienen el mismo SHA-256 que la instantánea tomada antes de crear el paquete (0 cambios) | `aplicacion_cambios_desde_la_instantanea = []` |

## Hallazgos de la auditoría que cambian lo que se puede afirmar
1. **El F1 macro de V5-CR (0,785) es del mismo orden que el de una sonda que solo usa 7 metadatos técnicos (0,777–0,786).** Es un dato heredado de V4 (mismos videos y particiones); no se recalculó para V5-CR.
2. **La ECE sin calibrar de V5-CR es significativamente peor que la del V4 activo** (+0,064; IC95 0,022 a 0,085).
3. **Los NaN de V5-CR** (437 valores en 139 de 633 ventanas) son casi todos características de brazos con muñecas no visibles, no del ritmo de pasos como se asumía; se corrigió la documentación.
4. **El «checkpoint original» y el desplegado difieren en dos archivos de metadatos** (config y escalador); los pesos son idénticos. Documentado en la ficha.
5. Una fórmula de la documentación previa (separación de picos de 0,25 s) difiere del código (0,2 s); la tabla de características usa el código.
6. La **duración del clip** difiere por clase (normal 4,9 s; esclerosis múltiple 18,6 s); V5-CR no la usa como entrada.

## Alcance y límites de esta auditoría
Verifica coherencia, trazabilidad y privacidad del paquete; no valida clínicamente el modelo. Las capturas y pruebas visuales se hicieron con Chrome. La ubicación de los cambios en el Word no se pudo comprobar.
