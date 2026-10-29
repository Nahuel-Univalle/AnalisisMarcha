import {
  ArrowLeftRight,
  Footprints,
  Gauge,
  Hand,
  LucideIcon,
  Repeat,
  Scale,
  Timer,
} from "lucide-react";
import type { UserCharacteristicCard } from "@/lib/analysis/resultPresentation";

/**
 * Perfil de movimiento: las mismas "características observadas" que produce
 * userCharacteristicCards(), agrupadas en Ritmo / Simetría / Movimiento /
 * Estabilidad y con íconos lucide (en lugar de emoji). Agrupar es solo
 * presentación: los textos no se alteran.
 */

const GROUP_ORDER = ["Ritmo", "Simetría", "Movimiento", "Estabilidad"] as const;
type GroupTitle = (typeof GROUP_ORDER)[number];

const CHARACTERISTIC_MAP: Record<string, { group: GroupTitle; icon: LucideIcon }> = {
  "Ritmo de la caminata": { group: "Ritmo", icon: Timer },
  "Regularidad de la marcha": { group: "Ritmo", icon: Repeat },
  "Simetría del movimiento": { group: "Simetría", icon: ArrowLeftRight },
  "Velocidad al caminar": { group: "Movimiento", icon: Gauge },
  "Movimiento de los brazos": { group: "Movimiento", icon: Hand },
  "Movimiento de las piernas": { group: "Movimiento", icon: Footprints },
  "Estabilidad corporal": { group: "Estabilidad", icon: Scale },
};

export function MovementProfile({ cards }: { cards: UserCharacteristicCard[] }) {
  const groups = GROUP_ORDER.map((title) => ({
    title,
    items: cards
      .filter((card) => (CHARACTERISTIC_MAP[card.title]?.group ?? "Movimiento") === title)
      .map((card) => ({ ...card, Icon: CHARACTERISTIC_MAP[card.title]?.icon ?? Footprints })),
  })).filter((group) => group.items.length > 0);

  return (
    <div className="grid overflow-hidden rounded-xl border border-line bg-surface md:grid-cols-2">
      {groups.map((group, index) => (
        <section
          key={group.title}
          className={[
            "p-5",
            index > 0 ? "border-t border-line" : "",
            index === 1 ? "md:border-t-0 md:border-l" : "",
            index === 3 ? "md:border-l" : "",
          ].join(" ")}
        >
          <h3 className="text-[11px] font-bold uppercase tracking-[0.09em] text-accent-cyan-ink">
            {group.title}
          </h3>
          <ul className="mt-3 space-y-3.5">
            {group.items.map(({ title, description, Icon }) => (
              <li key={title} className="flex gap-3">
                <Icon className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" aria-hidden />
                <div className="min-w-0">
                  <p className="text-sm font-semibold leading-5 text-ink">{title}</p>
                  <p className="mt-0.5 text-[13px] leading-5 text-ink-muted">{description}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
