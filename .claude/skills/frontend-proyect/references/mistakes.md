# Frontend Mistakes and Lessons

This document records frontend mistakes that have previously been identified in this project.

Claude must consult these lessons to avoid repeating known problems.

---

# Known Lessons (auditoría de código, 2026-09 — verificadas contra el código real, ninguna inventada)

## Lesson: Hover-lift aplicado a contenido no interactivo

Problem: `Card.tsx` aplica `hover:-translate-y-1 hover:shadow-xl` a **todas** sus instancias, sin excepción. El mismo efecto se copió a mano en decenas de `div`s (grid de estadísticas en `dashboard`, grid "qué observa el sistema", las 3 listas de `AdminDashboard`, filas de "últimos análisis/informes/usuarios", zona de carga de `subir-video`), incluso cuando ese contenido no es un link ni dispara ninguna acción.

Why it was wrong: el hover-lift comunica "esto es interactivo, puedes hacer click". Aplicarlo a texto estático engaña al usuario y es, además, el tipo de detalle que hace que una interfaz se sienta "genérica de plantilla" en vez de diseñada a propósito (ver anti-patrones de `SKILL.md`: "Floating cards without hierarchy").

Rule: el hover-lift/shadow-grow se reserva para elementos genuinamente interactivos (botones, links, filas clickeables de una tabla). El `Card` base no debería moverse solo porque el mouse pasa por encima; si una instancia específica de `Card` SÍ es clickeable, ese comportamiento debe ser explícito (prop o clase agregada en el call-site), no el default global.

✅ Resuelto (Fase A-F): `Card` ahora tiene `interactive?: boolean` (default `false`, sin hover-lift). Se quitó `hover:-translate-y-1` de los `div`s copiados a mano en `dashboard`, `AdminDashboard` y `movimiento`. Pendiente revisar `resultado`/`evaluacion`/`informe`/`seguimiento` en sus fases correspondientes (G/H).

## Lesson: "Botón" duplicado fuera del componente Button

Problem: al menos 4 lugares reimplementan a mano las clases visuales de `Button` sobre un `<Link>` de `next/link`, cada uno con pequeñas variaciones: `PublicHeader` ("Crear cuenta": `hover:bg-blue-600`), `AdminDashboard` ("Accesos rápidos"), y la landing (`page.tsx`, dos CTAs: "Comenzar análisis" y "Ver cómo funciona").

Why it was wrong: exactamente el anti-patrón que señala `CLAUDE.md` ("Never create multiple slightly different versions of the same component") — son 4 variantes ligeramente distintas del mismo concepto visual, y ya divergieron entre sí (colores de hover distintos).

Rule: cuando una acción debe navegar (no ejecutar un handler), reutilizar las clases de `Button` de forma centralizada en lugar de copiarlas — evaluar en Fase 3/4 si conviene un wrapper polimórfico (`Button` capaz de renderizar `Link`) en vez de duplicar.

✅ Resuelto (Fase B/D/E): se creó `LinkButton` (envuelve `next/link` reutilizando `buttonClasses()` de `Button`). Aplicado en `PublicHeader`, landing y `AdminDashboard`.

## Lesson: Mismo elemento de marca con dos colores distintos

Problem: el ícono del logo (`Activity` de lucide-react, junto al texto "Análisis de Marcha IA") usa `text-accent` en `AppHeader.tsx` y `text-cyan-600` en `PublicHeader.tsx`.

Why it was wrong: es el mismo elemento de identidad de marca en dos cabeceras del mismo producto — debería ser visualmente idéntico. El color usado en uno de los dos ni siquiera es un token declarado del proyecto.

Rule: los elementos de marca (logo, ícono de marca) deben usar siempre el mismo color, tomado de la paleta declarada (`primary`/`secondary`/`accent`).

✅ Resuelto (Fase A): ambos logos usan `text-accent`.

## Lesson: Colores fuera de la paleta declarada

Problem: `tailwind.config.ts`/`globals.css` solo declaran `primary`, `secondary`, `accent`, `surface`, `danger`. Sin embargo, el código usa extensamente `cyan-*` (logo de `PublicHeader`, `ProgressSteps`, y — según trabajo previo de la misma sesión — `ModelPerformanceCard`, `ConditionEvaluation`, barras de probabilidad) e `indigo-*` (una de las 4 tarjetas de estadísticas del dashboard), sin que ninguno de los dos esté documentado ni justificado semánticamente.

Why it was wrong: `DESIGN_SYSTEM.md` es explícito — "Never introduce a new accent color without justification" y "Color should communicate meaning". `cyan`/`indigo` aparecen mezclados con `primary`/`accent` (ambos azules) sin ninguna razón semántica visible; en el dashboard, 4 tarjetas de estadísticas usan 4 colores distintos (azul, verde, índigo, gris) para 4 números que no tienen una jerarquía de importancia distinta entre sí.

Rule: antes de usar un color, verificar que sea uno de los 5 tokens declarados o que su introducción esté justificada por un significado semántico real (no decorativo). Decidir en Fase 3/4 si `cyan` se adopta formalmente como token o se reemplaza por `accent`/`primary` en todos sus usos.

✅ Resuelto en componentes base y páginas ya trabajadas (Fase A/E): `cyan-*` reemplazado por `accent`/`primary` en `ProgressSteps`, `PublicHeader`, `dashboard` (hero + stats). `indigo-*` eliminado del dashboard (las 4 tarjetas de estadísticas ahora comparten un único estilo). Pendiente verificar `evaluacion`/`seguimiento` en Fase G/H (auditoría original los señaló, todavía no se tocaron).

## Lesson: Botones 100% pill-shaped, contradice la jerarquía de radios documentada

Problem: `Button.tsx` usa `rounded-full` sin excepción para las 4 variantes.

Why it was wrong: `DESIGN_SYSTEM.md` §5 pide explícitamente "Avoid excessive pill-shaped elements" y sugiere 8–10px para inputs/botones, no un radio total. Es, además, el componente compartido de más alto impacto del proyecto (aparece en toda página con una acción).

Rule: alinear el radio de `Button` con la escala documentada (8–10px) salvo que exista una razón de identidad visual explícita para mantener la pastilla — decisión a validar en Fase 3, no a cambiar unilateralmente sin avisar (afecta visualmente TODA la aplicación).

✅ Resuelto (Fase A, aprobado explícitamente por el usuario): `Button` usa `rounded-lg` (8px), mismas 4 variantes, sin agregar ninguna nueva. `AlertBadge` mantiene `rounded-full` deliberadamente (es una pastilla de estado, no un control interactivo — categoría distinta).

## Lesson: Valores internos sin traducir expuestos al usuario

Problem: el `<select>` de "Categoría del dataset" en `subir-video/page.tsx` muestra literalmente `control`, `parkinson`, `multiple_sclerosis`, `fall_risk` como opciones visibles.

Why it was wrong: el resto del proyecto (páginas `resultado`/`evaluacion`, `src/lib/analysis/resultPresentation.ts`) fue rediseñado específicamente para nunca mostrar nombres internos/técnicos al usuario. Este selector quedó fuera de ese trabajo y reintroduce el mismo problema en el punto de entrada del flujo.

Rule: cualquier valor que el usuario vea en la UI debe pasar por una capa de traducción a lenguaje humano, igual que ya se hace en el resto del flujo de análisis. Además, decisión de producto pendiente: confirmar si un usuario regular debe ver/elegir esta categoría en absoluto, o si es un campo de uso interno/investigación que no debería estar en el flujo de un usuario final (no se puede inferir esto solo del código — requiere decisión del dueño del producto).

✅ Resuelto (Fase F, decisión de producto ya dada por el usuario): el selector solo se renderiza cuando `isAdmin()` es verdadero (`src/app/analisis/subir-video/page.tsx`). Un usuario final nunca ve ni elige `control`/`parkinson`/`multiple_sclerosis`/`fall_risk`; el valor por defecto (`"control"`, ya definido en `AnalysisContext`) se sigue enviando sin cambios al backend, preservando compatibilidad total con `/api/analysis/video`. No se tocó ningún contrato de API ni lógica de IA — solo visibilidad condicional en la UI.

## Lesson: Estado "de validación" que no depende del video real

Problem: `ValidationChecklist.tsx` siempre muestra los mismos 7 ítems y siempre marca el ítem #4 ("Buena iluminación") en advertencia, sin importar qué video se subió.

Why it was wrong: la pantalla se llama "Validando tu video" y dice "Revisamos si el video cumple las condiciones mínimas" — el usuario razonablemente asume que el contenido refleja SU video. El backend del proyecto ya calcula datos reales de calidad (`poseDetectionRate`, `analysisReliable`, etc., usados más adelante en `resultado`) que no se conectan aquí.

Rule: un componente de "revisión"/"validación" no debe presentar contenido estático como si fuera específico del archivo del usuario. Conectar esta pantalla a datos reales es una decisión de alcance mayor a un ajuste visual — señalar antes de implementar.

✅ Resuelto parcialmente (Fase F, por instrucción explícita del usuario: solo presentación, sin conectar datos reales todavía). `ValidationChecklist` ya no muestra íconos de aprobado/advertencia por ítem ni un veredicto fijo de "Buena iluminación" — se reformuló como una lista de recomendaciones para que el usuario revise su propio video ("Antes de continuar, verifica que tu video cumple con"), y el único estado real que se muestra (`valid`) sigue viniendo de `Boolean(videoFile)`. La conexión a detección real de iluminación/pose/calidad queda explícitamente diferida a una fase futura, cuando el pipeline lo soporte.

## Lesson: Ilustración "programmer art" en la landing

Problem: la tarjeta destacada de la landing (`page.tsx`) simula una figura humana con `div`s posicionados a mano (círculo + líneas), en vez de un ícono o ilustración real.

Why it was wrong: coincide con el anti-patrón "Placeholder-looking UI" que el propio `CLAUDE.md` pide evitar explícitamente.

Rule: no inventar un asset de ilustración de reemplazo sin dirección del dueño del producto (podría ser un ícono más simple, una captura real del video anotado con landmarks, o una ilustración encargada) — señalar como decisión pendiente, no resolver unilateralmente.

✅ Resuelto (Fase D, decisión de producto ya dada: simplificar, no inventar otra figura humana con divs). La tarjeta ahora usa el ícono `Footprints` de lucide-react sobre `.brand-gradient`, sin ningún div posicionado a mano. Una captura real del sistema puede reemplazar esta zona más adelante.

## Lesson: Múltiples gradientes de marca sin un patrón único

Problem: existen al menos 3 combinaciones de gradiente distintas para "tarjetas destacadas": `from-primary via-secondary to-accent` (login, registro, dashboard), `from-blue-700 to-emerald-600` (landing), y variaciones por nivel de riesgo en `resultado` (de un trabajo anterior de esta misma sesión).

Why it was wrong: cada pantalla "inventa" su propio gradiente de héroe en lugar de reutilizar un tratamiento único — inconsistencia visual entre páginas que deberían sentirse parte del mismo producto.

Rule: definir un único gradiente de marca (o decidir deliberadamente no usar gradientes fuera de la pantalla de autenticación) y reutilizarlo, en vez de que cada página cree el suyo.

✅ Resuelto (Fase A/D/E): se agregó la clase `.brand-gradient` en `globals.css` (`primary → secondary → accent`, 135deg) como único tratamiento de gradiente de marca. Reemplaza los gradientes ad-hoc de `login`, `registro`, `dashboard` y la landing. Pendiente revisar las variaciones por nivel de riesgo de `resultado` en Fase G (esas sí comunican significado semántico por severidad, no son decorativas — evaluar si encajan en esta regla o son un caso aparte).

## Lesson: Ruta duplicada sin diferenciación (`/referencias`)

Problem: `src/app/referencias/page.tsx` importa y renderiza directamente `ParkinsonDatasetPage` (el mismo componente de `/datasets/parkinson`), sin ninguna diferencia de contenido. No es una redirección — es el mismo componente montado bajo una URL distinta. Tampoco está enlazada desde ninguna navegación (`AppHeader` solo enlaza `/datasets/parkinson` y `/seguimiento`), aunque sigue protegida como ruta admin en `src/proxy.ts`.

Why it matters: es una duplicación real de página completa, no solo de un componente visual — dos URLs, contenido idéntico, y una de ellas inalcanzable desde la UI normal.

Rule / decisión pendiente (Fase I, señalada al usuario, no resuelta unilateralmente): decidir si `/referencias` debe fusionarse con `/datasets/parkinson`, redirigir a ella, o tener en el futuro un propósito propio distinto. Es una decisión de arquitectura de información/routing, no una decisión puramente visual — no se resuelve solo con el código.

✅ Resuelto (a pedido explícito del usuario, tras confirmar mediante búsqueda exhaustiva — imports, enlaces de navegación, redirects, docs, config, git history — que no existe ninguna dependencia real ni propósito funcional distinto): `src/app/referencias/page.tsx` ahora es un redirect server-side (`redirect("/datasets/parkinson")` de `next/navigation`) en vez de renderizar una copia del componente. `/datasets/parkinson` sigue siendo la única fuente de verdad; la URL `/referencias` se conserva para no romper accesos directos existentes. La protección de rol admin la sigue resolviendo `src/proxy.ts` antes de llegar a la página, así que el redirect no necesita repetir esa verificación.

## Nota (Fase J): estados de foco reforzados

Dos inputs (`select` de categoría en `subir-video`, filtro de usuario en `seguimiento`) solo cambiaban el color del borde al enfocar, sin anillo de foco — un indicador de foco débil para navegación por teclado. Se alinearon con el patrón ya usado en `FormField`/`datasets/parkinson` (`focus:ring-2 focus:ring-blue-400 focus:ring-offset-2`). También se agregó `aria-expanded` al botón de menú móvil de `AppHeader`, que antes solo tenía un `aria-label` fijo ("Abrir menú") sin reflejar el estado abierto/cerrado.

## Nota de proceso: nombre de archivo con typo

`components.md` (referenciado por `SKILL.md`/`CLAUDE.md`) en realidad existe como `componets.md` en disco. No se renombró durante esta auditoría para no romper la referencia sin aprobación explícita del usuario.

---

# Lecciones del rediseño v2 (2026-10)

> El rediseño v2 reemplaza decisiones anteriores de este archivo: ya no existe
> `.brand-gradient` (no hay gradientes), `AlertBadge` dejó de ser pastilla
> (etiqueta de 6px con medidor de 3 segmentos) y la navegación autenticada es
> un sidebar navy, no un header horizontal.

## Lesson: La paleta por defecto de Tailwind v4 rompe el PDF

Problem: Tailwind v4 compila `slate-*`, `amber-*`, etc. a `oklch()`. html2canvas 1.4.1 (exportación del informe en `src/utils/generatePdf.ts`) no interpreta `oklch()` y la descarga caía al `window.print()`.

Rule: usar solo los tokens HEX de `globals.css`. En `MedicalReport.tsx` evitar además modificadores de opacidad (`bg-x/10`), que generan `color-mix(oklab)`. Verificado: con tokens HEX el PDF se genera por html2canvas sin fallback.

## Lesson: Scroll horizontal dentro de un grid desborda la página en móvil

Problem: `StepIndicator` (lista con `overflow-x-auto`) dentro de un `grid` hacía que la página midiera 487px en un viewport de 390px: los ítems de grid tienen `min-width: auto`.

Rule: todo contenedor con scroll horizontal dentro de un grid/flex lleva `min-w-0`. Verificar `scrollWidth > innerWidth` a 390px.

## Lesson: El resultado de ejemplo de AnalysisContext no debe presentarse como real

Problem: `AnalysisContext` arranca con `mockAnalysisResult`; al abrir "Informes" o "Resultado" sin un análisis en sesión se mostraba un informe "Bajo" de ejemplo con el nombre del usuario.

Rule: las vistas de resultado/detalle/informe usan `isPlaceholderResult()` (`components/analysis/NoAnalysisState.tsx`) y muestran un estado vacío.

## Lesson: El servidor de desarrollo puede servir CSS obsoleto tras reescribir globals.css

Problem: un `next dev` ya en ejecución siguió sirviendo el `globals.css` anterior (gradiente viejo) aun después de recompilar.

Rule: no dar por verificado un cambio de tokens sin confirmar que el CSS servido contiene los tokens nuevos; si no, reiniciar el dev server o verificar con `next build && next start`.

## Lesson: Datos técnicos que nunca vuelven a la UI de usuario

Problem: `/analisis/movimiento` seguía mostrando "Cuerpo detectado %", "Calidad", "Momentos analizados" y "Momentos con seguimiento correcto".

Rule: nunca mostrar al usuario: pasos estimados, información técnica adicional, versión/accuracy/macro-F1 del modelo, cantidad de videos de entrenamiento, calidad técnica del video, conteos de frames. Siguen existiendo en los datos; solo no se muestran.
