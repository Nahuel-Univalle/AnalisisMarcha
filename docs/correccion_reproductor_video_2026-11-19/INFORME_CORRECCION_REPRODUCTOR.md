# Corrección de la reproducción del video durante el análisis (19-nov-2026)

## Causa (reproducida en Chrome real, antes de corregir)
Prueba con un `.MOV` real (H.264 + AAC, 11,87 s) subido por la interfaz, en un servidor de producción aislado: la primera reproducción llegó al final y el elemento `<video>` disparó `error` con `MEDIA_ERR_DECODE` (código 3): *«Failed to send audio packet for decoding … timestamp=11882667»*, es decir, el **último paquete de audio** del archivo (el audio dura 11,894 s, el video 11,867 s). Evidencia: `navegador/result_replay_mov.json` (resultado previo a la corrección: el panel pasó a «no pudo reproducirse» mientras el análisis seguía en curso).
Defecto de la aplicación: `VideoStage` convertía cualquier evento `error` en un estado `failed[src]=true` **permanente**, desmontaba el `<video>` y mostraba el mensaje sin reintento, aunque el video hubiera cargado y reproducido bien. El estado solo se reiniciaba cuando, al terminar el análisis, `key` cambiaba y el componente se remontaba (por eso «desaparecía»).
Descartado con evidencia: la URL temporal no se revoca durante el análisis (`revokeObjectURL` solo ocurre en `setVideo/clearVideo`); la fuente no cambia hasta el final; el análisis no toca el archivo ni el reproductor (el blob es local al navegador); con mp4 H.264 de 7 s y de 10 s el fallo no ocurre.

## Archivos modificados (respaldo en `respaldo_previo/`)
- `src/components/analysis/VideoStage.tsx`: nuevo `StageVideo` que **no se desmonta** por un error. Si el video ya había cargado, recarga el mismo recurso (`load()`), conserva posición (o vuelve al inicio si el error ocurre en el último 1,5 s), deja el aviso visible («El navegador reportó un aviso al leer el final del archivo…») y registra el detalle con `console.warn`. Máximo 3 recuperaciones; si nunca cargó o la recuperación falla, muestra el mensaje de error con botón **Reintentar** (que remonta con la misma URL). El aviso se muestra bajo el video, fuera del efecto de escaneo (una captura reveló que se solapaba con las esquinas del visor; corregido).
- `src/context/AnalysisContext.tsx`: la única URL temporal viva se libera también al desmontar el proveedor (sin fugas); no se revoca mientras el video está activo.

Sin cambios: V5-CR, pesos, escalador, etiquetas, videos, rutas API, base de datos, tesis.

## Pruebas reales (Chrome headless (modo nuevo) por CDP, servidor aislado, BD técnica 55432)
Script: `navegador/prueba_navegador_cdp.mjs`; resultados `navegador/result_*.json`.
| Escenario | Resultado |
|---|---|
| Antes de corregir, MOV: terminar y repetir durante el análisis | **FALLA** (reproducido) |
| Después, MOV 1080p horizontal: reproducir durante el análisis, terminar, repetir mientras V5-CR sigue, pausar/reanudar ×4, buscar adelante/atrás, fallo de carga forzado + Reintentar, fin del análisis, reproducir, ir a resultado | 22/22 |
| mp4 vertical 478×850 | 22/22 |
| mp4 horizontal 1280×720 | 22/22 |
| Escritorio y móvil (390 px), aviso visible y sin solapamientos | capturas `shot_notice_desk.png`, `shot_notice_mobmov.png` |
| Mismo `<video>` (sin remontar) durante todo el análisis; el análisis seguía en curso en cada paso | verificado en cada escenario |
| HTTP completo (login, carga, V5-CR, BD, historial, informe, PDF, administración, controles de acceso, entradas negativas) | 21/21 |
| `tsc` 0 errores · ESLint 0 errores (2 avisos previos) · `next build` OK · presentación PDF y descarga de cliente | pasan |

## Estado
El reproductor es independiente del análisis. V5-CR y el resto de funciones sin cambios (la prueba HTTP completa pasa). **Limitaciones:** pruebas en Chrome (no en Edge/Firefox/Safari); la descarga de PDF por botón se comprobó por HTTP, no con clic en el navegador; el servidor habitual (`npm run dev`) no estaba en ejecución al terminar, por lo que debe iniciarlo para su verificación manual.

## Verificación manual
1. `npm run dev`; entre, suba el video que falló y pulse «Iniciar análisis».
2. Reprodúzcalo, deje que termine y pulse Play otra vez antes de que acabe el análisis: debe reproducirse de nuevo (si el navegador avisa del final del archivo verá una línea de aviso bajo el video, no un error).
3. Si ve «Este video no pudo reproducirse», pulse «Reintentar» y entregue la consola del navegador (línea `VideoStage: error de reproducción`).
