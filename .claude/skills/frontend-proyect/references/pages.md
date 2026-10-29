# Project Page Reference

This document contains information about important frontend pages and their established patterns.

Claude should consult this document before modifying an existing page or creating a similar one.

---

> **Actualización (implementación en curso, Fases A-J):** el usuario aprobó
> la auditoría y se ejecutó la implementación real por fases. Las notas de
> cada página de abajo describen el estado **pre-implementación** (auditoría
> original); los bloques "✅ Actualizado" al final de cada una reflejan lo
> que realmente cambió. Ver `mistakes.md` para el detalle de cada corrección.

# Existing Pages (verificado en el código, 2026-09)

## Landing pública

Route: `/` — Source: `src/app/page.tsx`
Purpose: presentación pública del producto para usuarios no autenticados.
Layout: `PublicHeader` + hero de 2 columnas (texto/CTA a la izquierda, tarjeta ilustrativa a la derecha) + sección "¿Cómo funciona?" de 4 tarjetas.
Componentes: `PublicHeader`, `Card`, `MedicalDisclaimer`.
Nota: la "ilustración" de la tarjeta derecha son `div`s posicionados a mano simulando una figura humana — no es un asset real. Los dos CTA principales son `<Link>` con clases copiadas de `Button`, no el componente `Button`.

✅ Actualizado (Fase D): la ilustración ahora es el ícono `Footprints` sobre `.brand-gradient` (sin divs de figura humana, decisión de producto ya aprobada). Ambos CTAs son `LinkButton`. La tarjeta hero usa `.brand-gradient` en vez de `from-blue-700 to-emerald-600`.

## Login

Route: `/login` — Source: `src/app/login/page.tsx`
Purpose: autenticación de usuario existente.
Layout: `Card` de 2 columnas en `lg` (formulario + panel de marca con gradiente); una sola columna en mobile/tablet.
Componentes: `Button`, `Card`, validación inline (`validateEmailFormat`).
Patrón a reutilizar: validación `touched` + mensaje de error por campo, mostrar/ocultar contraseña, botón con spinner (`Loader2`) durante el submit. Es de los flujos mejor resueltos del proyecto.

✅ Actualizado (Fase D): campos ahora usan `FormField` (reemplaza `inputClass`/`inputState` a mano), el error de submit usa `InlineAlert`, el botón usa la prop `loading` de `Button` (reemplaza el `Loader2` manual), y el panel de marca usa `.brand-gradient`.

## Registro

Route: `/registro` — Source: `src/app/registro/page.tsx`
Purpose: alta de nuevo usuario.
Layout: igual estructura que `login` (panel de marca + formulario), pero el panel de marca queda a la izquierda en vez de la derecha.
Componentes: `Button`, `Card`. Checklist de reglas de contraseña en vivo (`passwordRules`).
Nota: duplica casi al 100% la lógica de estilos de input de `login` (`inputClass` vs. `inputState`) sin un componente compartido.

✅ Actualizado (Fase D): mismos cambios que `login` — `FormField`, `InlineAlert`, `Button` con `loading`, `.brand-gradient`. La duplicación con `login` queda resuelta porque ambos ahora comparten `FormField` en vez de reimplementar la lógica cada uno.

## Dashboard (usuario)

Route: `/dashboard` — Source: `src/app/dashboard/page.tsx`
Purpose: pantalla de inicio tras autenticarse. Si `user.role === "ADMIN"` renderiza en su lugar `AdminDashboard` (mismo route, contenido completamente distinto).
Layout: saludo + título, tarjeta CTA con gradiente ("Nuevo análisis"), grid de 4 estadísticas, estado vacío condicional, grid de 8 "qué observa el sistema".
Datos: `GET /api/me/summary`.
Estados: loading (placeholder `"..."` en las cifras), empty (`totalAnalyses === 0`).

✅ Actualizado (Fase E): la tarjeta CTA usa `.brand-gradient`. Las 4 tarjetas de estadísticas ("4 stats = 4 colores") se redujeron a 3 métricas reales con un único estilo de ícono (`bg-accent/10 text-primary`, mismo patrón que la landing); "Privacidad protegida" (que era una tarjeta estática, no una métrica) se separó a un `InlineAlert` propio. Se quitó el hover-lift del grid "qué observa el sistema".

## Panel administrativo

Route: `/dashboard` (rama admin) — Source: `src/components/admin/AdminDashboard.tsx`
Purpose: resumen operativo para el rol ADMIN.
Layout: grid de 6 métricas, accesos rápidos, 3 columnas de "últimos X" (análisis/informes/usuarios).
Datos: `GET /api/admin/summary`.
Estados: loading, empty por cada una de las 3 listas.

✅ Actualizado (Fase E): "Accesos rápidos" usa `LinkButton` en vez de `<Link>` con clases copiadas. Se quitó el hover-lift de las 3 listas de "últimos X" (no son filas clickeables).

## Subir video

Route: `/analisis/subir-video` — Source: `src/app/analisis/subir-video/page.tsx`
Purpose: primer paso del flujo de análisis — cargar el video y elegir la categoría del dataset.
Layout: 2/3 + 1/3 en desktop (dropzone + consejos), apilado en mobile.
Componentes: `AppShell`, `Card`, `Button`.
Nota importante: el `<select>` "Categoría del dataset" expone directamente los valores internos (`control`, `parkinson`, `multiple_sclerosis`, `fall_risk`) como texto visible al usuario, sin traducir — inconsistente con el resto de la app, donde ya se tradujeron todos los nombres internos a lenguaje humano (ver `resultado`/`evaluacion`).

✅ Actualizado (Fase F, decisión de producto ya dada): el selector solo se renderiza si `isAdmin()`. Un usuario final ya no lo ve; el valor por defecto `"control"` se sigue enviando al backend sin cambios de contrato. Además se reforzó el foco visible del `<select>` (antes solo cambiaba el color del borde) con un anillo de foco (`focus:ring-2`), igual que el resto de los inputs del proyecto.

## Validación

Route: `/analisis/validacion` — Source: `src/app/analisis/validacion/page.tsx`
Purpose: pantalla intermedia que "revisa" el video antes de analizarlo.
Componentes: `ValidationChecklist` (ver nota de contenido estático en `componets.md`), `MedicalDisclaimer`, `Button`.

✅ Actualizado (Fase F): `ValidationChecklist` se reformuló como recomendaciones para autorrevisión del usuario, sin veredictos falsos por ítem (ver `mistakes.md`). El título/copy de la página se ajustó de "Validando tu video" (implica que el sistema ejecutó una validación) a "Revisión antes de continuar" (honesto sobre que es el usuario quien revisa).

## Analizando movimiento

Route: `/analisis/movimiento` — Source: `src/app/analisis/movimiento/page.tsx`
Purpose: dispara la llamada a `/api/analysis/video`, muestra progreso (`ProgressSteps`) y los dos videos (original/anotado) en cuanto están listos.
Estados: loading (`processing` + `Loader2`), error (`apiError`), completado (habilita "Ver resultado").

✅ Actualizado (Fase F): el error de la llamada a la API usa `InlineAlert` en vez de un `<div>` a mano; se quitó el hover-lift de los 4 tiles de estado ("Cuerpo detectado", "Calidad", etc. — no son clickeables).

## Resultado

Route: `/analisis/resultado` — Source: `src/app/analisis/resultado/page.tsx`
Purpose: **Nivel 1** — resumen orientativo para el usuario general (rediseñado en una fase anterior de este proyecto para lenguaje no técnico). Usa `src/lib/analysis/resultPresentation.ts` para traducir los datos crudos del modelo.
Layout (pre-implementación): secuencia vertical de `Card`s — patrón identificado, coincidencia, calidad del análisis, hallazgos principales, características observadas, calidad del video, observaciones, recomendaciones, aviso.
Nota (pre-implementación): era la página con más `Card`s apiladas en secuencia de todo el proyecto — candidata a revisión de jerarquía/agrupación en una fase de mejora.

✅ Rediseñado (Fase G, prioridad explícita del usuario — jerarquía real, no solo recoloreo). Estructura actual, 7 secciones:
1. **Resultado principal**: `Card` hero con color según severidad (semántico, no decorativo) + `AlertBadge` + resumen.
2. **Nivel de confianza y calidad**: se fusionaron 3 `Card`s sueltas ("Patrón identificado", "Calidad del análisis", "Calidad del video") en **una sola** `Card` con sub-secciones internas (grid de 2 columnas + un divisor `border-t` para los datos técnicos de seguimiento corporal + el video anotado). El aviso de "no confiable" pasó de `Card` amarilla a `InlineAlert`.
3. **Hallazgos principales**: grid de `Card`s, una por hallazgo (unidad conceptual real, se mantiene).
4. **Características observadas**: grid de `div`s simples (no `Card`, ya estaba bien).
5. **Observaciones**: `<details>` colapsable (se mantiene, no se convirtió en `Card`).
6. **Recomendaciones**: `Card` con lista.
7. **Aviso médico**: `Card` (sección con nombre propio, uso legítimo de `Card`).
Se quitó el hover-lift de los tiles de seguimiento corporal (ahora integrados en la sección 2).

## Análisis detallado (evaluación)

Route: `/analisis/evaluacion` — Source: `src/app/analisis/evaluacion/page.tsx`
Purpose: **Nivel 2** — vista para profesional, con distribución de probabilidades por clase y parámetros cuantitativos agrupados.
Componentes propios: tabla de hallazgos, bloque técnico colapsable (`<details>`).

✅ Actualizado (Fase G): esta página ya estaba bien estructurada para su audiencia (secciones A/B/C con letras, tabla real para hallazgos, densidad técnica apropiada para profesionales — se mantuvo esa estructura tal cual, según instrucción explícita de no rediseñar lo que ya funciona). Solo se corrigieron colores fuera de paleta: `bg-cyan-500` → `bg-accent` (barra de distribución del modelo), `text-cyan-700` → `text-primary` (título de grupo de parámetros). El aviso de "no concluyente" pasó a `InlineAlert`.

## Informe

Route: `/analisis/informe` — Source: `src/app/analisis/informe/page.tsx`
Purpose: genera/descarga el PDF (`MedicalReport`) y permite guardarlo en seguimiento.

✅ Actualizado (Fase H): los 3 mensajes de estado (guardado/error de guardado/error de descarga) usan `InlineAlert` (success/error/warning) en vez de `<div>`s a mano. `MedicalReport.tsx` (el contenido imprimible) ya estaba bien resuelto — usa una tabla real para parámetros cuantitativos y no envuelve todo en `Card`; no requirió cambios.

## Seguimiento

Route: `/seguimiento` — Source: `src/app/seguimiento/page.tsx`
Purpose: historial de informes guardados (propio o global si es admin). Filtro por nivel de alerta + búsqueda por usuario (solo admin).
Datos: `GET /api/me/reports` o `GET /api/admin/reports`.

✅ Actualizado (Fase H): el color `focus:border-cyan-500` del input de filtro se reemplazó por `focus:border-accent` + anillo de foco. El chip de filtro activo pasó de `bg-slate-950` (negro puro, sin relación con la paleta) a `bg-primary`. Se quitó el hover-lift de cada fila de informe (no es toda la fila la que es clickeable, solo el botón "Ver informe" interno). Se evaluó convertir la lista a una `<table>` real (instrucción de Fase H), pero cada fila incluye videos embebidos y texto largo — contenido no puramente tabular — por lo que se mantuvo como lista de bloques, decisión ya justificada en el propio layout.

## Datasets (Parkinson) / Referencias

Route: `/datasets/parkinson` (source: `src/app/datasets/parkinson/page.tsx`) — exclusivo admin, **única fuente de verdad**. KPIs reales (conteos de registros/muestras desde la API), gráfico de barras real con `recharts` (datos reales, no decorativos), tabla paginada de registros de referencia.

✅ Resuelto (limpieza post-implementación): `/referencias` (`src/app/referencias/page.tsx`) ya no renderiza una copia de `ParkinsonDatasetPage`. Se confirmó mediante búsqueda exhaustiva (imports, enlaces de navegación, redirects, docs, config, historial de git) que no tenía ningún propósito funcional distinto ni ninguna dependencia real apuntando a ella — no estaba enlazada desde ninguna navegación (`AppHeader` solo enlaza "Datasets" → `/datasets/parkinson` e "Informes globales" → `/seguimiento`). Ahora es un redirect server-side (`redirect("/datasets/parkinson")`) para no romper accesos directos existentes a esa URL, sin duplicar contenido. La protección de rol admin la resuelve `src/proxy.ts` antes de llegar a la página.

---

# Rutas verificadas (build real, `next build`)

`/`, `/login`, `/registro`, `/dashboard`, `/datasets/parkinson`, `/referencias`, `/seguimiento`, `/analisis/subir-video`, `/analisis/validacion`, `/analisis/movimiento`, `/analisis/resultado`, `/analisis/evaluacion`, `/analisis/informe` — 13 páginas de UI, todas dentro de `AppShell` excepto `/`, `/login`, `/registro`.

Protección de rutas: doble capa — `src/proxy.ts` (server-side, equivalente a middleware en Next.js 16) + `AppShell` (client-side, redirige si `!user` tras cargar `AuthContext`). No hay layouts anidados adicionales bajo `src/app/` (un único `src/app/layout.tsx` raíz).

---

# Rediseño v2 (2026-10) — estado actual (verificado visualmente a 1440 / 1366 / 390)

- `/`: hero 5/7 con panel navy + `GaitFigure` animado; franja de 3 puntos; "Cómo funciona" como línea de 4 pasos; "Qué analiza" agrupado; banda navy "Uso responsable".
- `/login`, `/registro`: `AuthLayout` (formulario + panel navy con esqueleto). Lógica intacta.
- `/dashboard` (usuario): último análisis (miniatura real en marco navy) + resumen en filas; análisis recientes (de `recentAnalyses` de `/api/me/summary`); "Antes de grabar"; "¿Qué observa el sistema?" agrupado. Sin análisis: panel navy "Realiza tu primer análisis".
- `/dashboard` (admin): métricas en una superficie dividida + 3 listas de actividad.
- `/analisis/subir-video`: `StepIndicator`, dropzone con arrastrar-y-soltar (mismos tipos que `accept`), vista previa y duración reales, consejos a la derecha, CTA "Continuar a la revisión".
- `/analisis/validacion`: video a la izquierda, checklist de autorrevisión (sin veredictos por ítem).
- `/analisis/movimiento`: panel navy único (video con escaneo + `ProcessingTimeline`). Sin porcentajes ni datos técnicos; la última etapa queda "en curso" hasta la respuesta real del servidor. Si hay error: "Ver resultado" deshabilitado y "Subir otro video".
- `/analisis/resultado`: cabecera con franja de estado + nivel (ícono/palabra/medidor); 8/4: `FindingsTrace`, perfil de movimiento, medidas (solo Cadencia y Simetría de piernas); lateral: recomendaciones, aviso, video.
- `/analisis/evaluacion`: documento técnico (A–D) con tabla de hallazgos.
- `/analisis/informe`: hoja A4 sobre "escritorio"; "Guardar en seguimiento" / "Descargar PDF" con estados de carga; "Fecha de emisión" (el resultado en memoria no trae la fecha del análisis).
- `/seguimiento`: línea de tiempo por mes, `FilterTabs` con conteos, videos en área desplegable.
- `/datasets/parkinson`: KPIs en superficie dividida, gráfico con tokens, tabla con cabecera fija.

Pendiente que requiere backend: "Ver informe" en seguimiento abre el análisis en memoria, no el informe guardado.

## Ajuste posterior (2026-10-21): una responsabilidad por sección

- **Inicio** (`/dashboard`): solo bienvenida + "Nuevo análisis", "Último análisis" (de `GET /api/me/analyses`[0]: miniatura, fecha, patrón, alerta, resumen corto; "Ver resultado" si es el análisis en memoria, si no "Ver en seguimiento") y 2 números pequeños (de `/api/me/summary`). Sin historial, sin consejos, sin "Qué observa".
- **Nuevo análisis**: consejos de grabación + "¿Qué observa el sistema?" (compacto, secundario).
- **Seguimiento** (usuario): historial completo de análisis desde `GET /api/me/analyses` con `HistoryTimeline` (filtros, patrón, resumen, videos, marca "Informe guardado"). Admin: informes globales (`SavedReportsList admin`).
- **Informes** (`/analisis/informe`): vista previa/descarga del informe del análisis en sesión + "Informes guardados" (`SavedReportsList`, antes vivía en Seguimiento). Se quitó el botón "Ver informe" de esas filas: llevaba a esta misma página y mostraba otro análisis.

Regla: no repetir el mismo bloque grande en dos secciones.
