# Project Component Reference

This document records reusable frontend components available in the project.

Claude should consult this document and the codebase before creating new components.

> Nota: este archivo se llama `componets.md` (typo heredado) pero es el que
> referencian `SKILL.md` y `CLAUDE.md` como `components.md`. No se ha
> renombrado durante la auditoría para no romper esa referencia sin
> aprobación explícita — ver `mistakes.md`.

> **Actualización (implementación en curso, Fase A-D completadas):** el
> usuario aprobó la auditoría y se está ejecutando la implementación real
> por fases (A → J). Las secciones de abajo marcadas "(actualizado)" ya
> reflejan el estado post-implementación de esas fases; el resto del
> documento sigue describiendo el estado pre-implementación tal como se
> auditó, hasta que su fase correspondiente se ejecute.

---

# Rule

Do not create a new component if an equivalent reusable component already exists.

When a reusable component is created or discovered, document it here.

---

# Existing Components (verificado en el código, 2026-09)

## Button (actualizado — Fase A/B)

Location: `src/components/ui/Button.tsx`

Purpose: único botón compartido del proyecto. Envuelve un `<button>` nativo.

Variants: `primary` (por defecto), `secondary`, `outline`, `danger` — se mantuvieron exactamente estas 4, sin agregar ninguna nueva.
Sizes: `sm`, `md` (por defecto), `lg`.

Radio: `rounded-lg` (antes `rounded-full`, aprobado explícitamente por el usuario para alinear con el Design System). Ya no tiene `hover:scale-[1.02]` (simplificación menor, justificada por la regla de "no animación innecesaria").

Props: extiende `ButtonHTMLAttributes<HTMLButtonElement>` + `variant` + `size` + **`loading?: boolean`** (nuevo). `loading` muestra un `Loader2` girando, agrega `aria-busy` y deshabilita el botón automáticamente — reemplaza el patrón manual `{loading && <Loader2 />}` + `disabled={loading}` que antes se repetía en `login`/`registro`.

El módulo también exporta `buttonClasses()`, `BUTTON_VARIANT_CLASSES` y `BUTTON_SIZE_CLASSES` para que otros elementos con apariencia de botón (como `LinkButton`) reutilicen exactamente las mismas clases en vez de copiarlas a mano.

Use when: cualquier acción disparada por el usuario dentro de la app autenticada o en formularios.

Do not use when: se necesita que la acción navegue como un link real — usar `LinkButton` (ver más abajo), no reimplementar las clases de `Button` sobre un `<Link>`.

Ejemplo:
```tsx
<Button variant="outline" size="sm" onClick={handleLogout}>
  <LogOut className="h-4 w-4" />
  Cerrar sesión
</Button>

<Button size="lg" type="submit" loading={loading}>
  {loading ? "Iniciando sesión..." : "Iniciar sesión"}
</Button>
```

## LinkButton (nuevo — Fase B)

Location: `src/components/ui/LinkButton.tsx`

Purpose: versión de `Button` que navega (envuelve `next/link`'s `Link`), usando `buttonClasses()` para verse idéntico a `Button`. Mismas props `variant`/`size` que `Button`, más `href`.

Use when: una acción es una navegación real (debe ser un `<a>` por accesibilidad/SEO), pero visualmente debe verse como un botón — p. ej. CTAs de la landing, "Crear cuenta" en `PublicHeader`.

Do not use when: la acción no navega (usar `Button`) o el enlace debe verse como texto simple (usar un `<Link>` normal, como "Iniciar sesión"/"Crear cuenta" en los footers de `login`/`registro`).

Ya en uso en: `PublicHeader` ("Crear cuenta"), landing `page.tsx` ("Comenzar análisis", "Ver cómo funciona"). Pendiente de aplicar en `AdminDashboard` (Fase I).

## FormField (nuevo — Fase D)

Location: `src/components/ui/FormField.tsx`

Purpose: campo de formulario con label asociado (`htmlFor`/`id` vía `useId()`), ícono opcional, estado de error (`aria-invalid` + `aria-describedby`) y, para `type="password"`, botón de mostrar/ocultar. Reemplaza la lógica `inputClass`/`inputState` que `login` y `registro` reimplementaban cada uno por su cuenta.

Use when: cualquier campo de texto/email/password/number en un formulario.

Ya en uso en: `login`, `registro`.

## InlineAlert (nuevo — Fase D)

Location: `src/components/ui/InlineAlert.tsx`

Purpose: banner de mensaje en línea con 4 tonos (`error`, `warning`, `success`, `info`), cada uno con su ícono. Reemplaza los `<div className="rounded-2xl border border-red-200 bg-red-50 ...">` escritos a mano en cada página.

Use when: mostrar un error/advertencia/confirmación puntual asociado a una acción (envío de formulario, guardado). No usar para el aviso médico fijo (eso sigue siendo `MedicalDisclaimer`).

Ya en uso en: `login`, `registro`. Pendiente de aplicar en `movimiento.tsx` (Fase F).

## Card (actualizado — Fase A)

Location: `src/components/ui/Card.tsx`

Purpose: contenedor genérico con borde, fondo blanco, radio y sombra. Es, con diferencia, el componente más reutilizado del proyecto (decenas de usos en todas las páginas de `analisis/*`, `dashboard`, `seguimiento`, `login`, `registro`, `AdminDashboard`).

Ya no aplica `hover:-translate-y-1 hover:shadow-xl` a todas las instancias por defecto. Ahora tiene una prop **`interactive?: boolean`** (default `false`): solo cuando `interactive` es `true` aparece un hover sutil (`hover:border-slate-300 hover:shadow-md`, sin desplazamiento). Usar `interactive` únicamente quando la tarjeta completa es clickeable/navegable; el resto de usos (bloques de texto, estadísticas) debe dejar el default `false`.

Use when: agrupar contenido relacionado que forma una unidad reconocible (una sección de resultado, un formulario, una fila de estadísticas).

Do not use when: el contenido es una lista de ítems pequeños repetidos (hoy se anidan `<div className="rounded-2xl bg-slate-50 p-4">` dentro de un `Card` para simular sub-tarjetas — evaluar si esos ítems realmente necesitan chrome de tarjeta o alcanza con una lista/grid simple).

## AlertBadge

Location: `src/components/ui/AlertBadge.tsx`

Purpose: pastilla de estado semántico por nivel de alerta.

Variants (prop `level`, tipo `SignalSeverity`): `Bajo` (verde/emerald), `Medio` (ámbar), `Alto` (rojo), `Info` (gris).

Use when: mostrar el nivel de alerta de un análisis o de una señal individual. Es el único lugar del proyecto donde el color comunica un significado clínico consistente — patrón a imitar en otros indicadores de estado.

## MedicalDisclaimer

Location: `src/components/ui/MedicalDisclaimer.tsx`

Purpose: aviso fijo ("Este sistema no reemplaza una valoración médica profesional...") sobre fondo ámbar. Envuelve internamente un `Card`.

Use when: en cualquier pantalla donde el usuario vea un resultado, antes de generar un informe, o en la landing pública. Ya se usa de forma consistente en `resultado`, `evaluacion`, `page.tsx` (landing) y `validacion`.

## ProgressSteps (actualizado — Fase A)

Location: `src/components/ui/ProgressSteps.tsx`

Purpose: indicador de pasos horizontal (grid de 6 columnas en desktop) para el flujo de análisis de video.

Props: `steps: string[]`, `current: number`.

El paso activo ahora usa `border-accent/30 bg-accent/10 text-primary` (antes `cyan-300`/`cyan-50`/`cyan-800`, fuera de la paleta declarada) y radio `rounded-lg` (antes `rounded-2xl`).

## AppShell

Location: `src/components/layout/AppShell.tsx`

Purpose: layout wrapper para toda página autenticada. Redirige a `/login` si no hay sesión (protección client-side; el proyecto además protege por servidor vía `src/proxy.ts`, el equivalente a middleware en Next 16). Renderiza `AppHeader` + `<main className="page-container">`.

Use when: envolver el contenido de cualquier página bajo `/dashboard`, `/analisis/*`, `/seguimiento`, `/datasets/*`, `/referencias`.

## AppHeader / PublicHeader (actualizado — Fase A/C)

Location: `src/components/layout/AppHeader.tsx`, `src/components/layout/PublicHeader.tsx`

Purpose: cabecera sticky con logo, navegación y menú móvil (`AppHeader`, para usuarios autenticados) o logo + CTA de login/registro (`PublicHeader`, para la landing).

Siguen siendo dos componentes independientes que no comparten código (no se fusionaron — tienen suficientes diferencias de navegación como para justificarlo), pero ya no divergen visualmente: el ícono del logo (`Activity`) usa `text-accent` en ambos, la sombra del header es `shadow-sm` en ambos (antes `PublicHeader` tenía `shadow-md shadow-slate-200/70`), y los estados activos de navegación usan `bg-accent/10`/`rounded-lg` en vez de `bg-blue-50`/`rounded-full`. El botón de menú móvil de `AppHeader` ya no tiene `hover:scale-[1.02]`. "Crear cuenta" en `PublicHeader` ahora es un `LinkButton` en vez de un `<Link>` con clases copiadas a mano.

## ValidationChecklist (actualizado — Fase F)

Location: `src/components/analysis/ValidationChecklist.tsx`

Purpose: lista de 7 recomendaciones para que el usuario revise su propio video, dentro de un `Card`.

El contenido sigue sin conectarse a una detección real (por instrucción explícita: solo se autorizó mejorar la presentación en esta fase, no inventar datos). Antes cada ítem tenía un ícono de aprobado/advertencia y un veredicto fijo por ítem (el #4 "Buena iluminación" siempre en advertencia), lo que simulaba una verificación que nunca ocurrió. Ahora todos los ítems usan el mismo ícono neutro (`Info`) y ningún veredicto individual — el único estado real mostrado es el banner final (`valid`), que viene de `Boolean(videoFile)` en `validacion/page.tsx`. Conectar esto a una detección real de iluminación/pose/calidad queda para una fase futura, cuando el pipeline lo soporte.

## Otros componentes de dominio (no genéricos, específicos de análisis)

- ~~`src/components/analysis/ConditionEvaluation.tsx`, `ModelPerformanceCard.tsx`, `SignalCard.tsx`, `PoseAnalysisPanel.tsx`~~ — **eliminados** (limpieza post-implementación, a pedido explícito del usuario). Eran código huérfano confirmado: cero imports en el resto de la app (verificado con grep antes y después, incluyendo imports dinámicos — no existen en este proyecto — y referencias por nombre en docs/config). Antes de eliminarlos se verificó que todo lo que importaban (`Card`, `AlertBadge`, `formatPercent`, `useAnalysis`, y los tipos `Signal`/`ConditionEvaluation`/`AnalysisResult`) sigue definido y usado por código real independiente de estos 4 archivos — no quedó ningún import huérfano. **Nota importante**: el tipo `ConditionEvaluation` en `src/types/index.ts` (usado por `AnalysisResult.conditions`, campo real y activo en `movimiento/page.tsx` y las rutas de API) es distinto del componente eliminado del mismo nombre — el tipo NO se tocó.
- `src/components/report/MedicalReport.tsx` — contenido del informe PDF/impresión. Revisado en Fase H: ya usa una tabla real para parámetros cuantitativos y no envuelve todo en `Card`; no requirió cambios.
- `src/components/admin/AdminDashboard.tsx` — panel exclusivo del rol admin. Actualizado en Fase E: "Accesos rápidos" ahora usa `LinkButton` en vez de `<Link>` con clases copiadas a mano, y se quitó el hover-lift de las 3 listas de actividad reciente (no son filas clickeables).

---

# Componentes que faltan (huecos restantes tras Fase A-D)

- **Input/FormField compartido**: resuelto — ver `FormField` arriba. Ya aplicado en `login`/`registro`. `AdminDashboard` y cualquier futuro formulario deberían usarlo también.
- **LinkButton / Button polimórfico**: resuelto — ver `LinkButton` arriba. Aplicado en `PublicHeader` y landing. Pendiente aplicar en `AdminDashboard` ("Accesos rápidos", Fase I).
- **Loading spinner/estado de carga reutilizable**: parcialmente resuelto — `Button`/`LinkButton` ahora soportan `loading` para botones. Sigue sin existir un patrón común para estados de carga de página completa o de sección (p. ej. mientras carga el dashboard o un informe); evaluar si aparece la necesidad en Fase E-H.

---

# Rediseño v2 (2026-10) — inventario vigente (reemplaza lo anterior donde difiera)

Tokens y reglas: `docs/DESIGN_SYSTEM.md`, sección "Rediseño v2".

- `ui/`: `Button` (mismas 4 variantes, alturas 32/40/48), `LinkButton`, `Card` (sin sombra), `FormField`, `InlineAlert`, `AlertBadge` + `LevelMeter` + `LEVEL_STYLES` (único mapa nivel→color), `MedicalDisclaimer` (`inline`/`block`, neutro), `PageHeader` / `SectionHeader` / `Eyebrow`, `MetricBlock`, `EmptyState` / `Skeleton`, `FilterTabs`, `StepIndicator` (reemplaza a `ProgressSteps`, eliminado).
- `layout/`: `AppShell` (Sidebar + TopBar + menú deslizante <1024px), `Sidebar`, `TopBar`, `PublicHeader`, `AuthLayout` (login/registro). `AppHeader` eliminado.
- `brand/`: `BrandMark` (logo), `GaitFigure` (esqueleto de marcha SVG; props `animated`, `ambient`, `active`, `guides`, `annotations`, `grid`; usar solo sobre navy).
- `analysis/`: `VideoStage` (ÚNICO contenedor de video, reemplaza a `AnalysisVideo`, eliminado), `FindingsTrace`, `MovementProfile`, `ProcessingTimeline`, `ValidationChecklist`, `NoAnalysisState` + `isPlaceholderResult`, `guidance.ts` (consejos de grabación y aspectos observados ya existentes, centralizados).
- `lib/formatDate.ts`: formato de fechas `YYYY-MM-DD` de la API (solo presentación).
