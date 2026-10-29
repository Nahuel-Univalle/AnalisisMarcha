import {
  ArrowLeftRight,
  Ban,
  Camera,
  Clock,
  Footprints,
  Gauge,
  Hand,
  ImageOff,
  LucideIcon,
  PersonStanding,
  Repeat,
  Scale,
  Scissors,
  Sun,
  Waypoints,
} from "lucide-react";

/**
 * Contenido de orientación que ya existía en la app (consejos de grabación
 * de /analisis/subir-video y "¿Qué observa el sistema?" del dashboard),
 * centralizado para reutilizarlo sin duplicarlo. No agrega requisitos nuevos.
 */

export const RECORDING_TIPS: Array<{ label: string; icon: LucideIcon }> = [
  { label: "Buena iluminación", icon: Sun },
  { label: "Cuerpo completo visible", icon: PersonStanding },
  { label: "Cámara estable", icon: Camera },
  { label: "Persona caminando en línea recta", icon: Waypoints },
  { label: "Video sin cortes bruscos", icon: Scissors },
  { label: "Fondo despejado", icon: ImageOff },
  { label: "Duración suficiente para observar varios pasos", icon: Clock },
];

export type ObservedGroup = {
  title: "Ritmo" | "Simetría" | "Movimiento" | "Estabilidad";
  items: Array<{ label: string; icon: LucideIcon }>;
};

// Los 8 aspectos que el dashboard ya listaba, agrupados.
export const OBSERVED_GROUPS: ObservedGroup[] = [
  {
    title: "Ritmo",
    items: [
      { label: "Velocidad de marcha", icon: Gauge },
      { label: "Regularidad de pasos", icon: Repeat },
    ],
  },
  {
    title: "Simetría",
    items: [
      { label: "Simetría corporal", icon: ArrowLeftRight },
      { label: "Diferencia lateral", icon: ArrowLeftRight },
    ],
  },
  {
    title: "Movimiento",
    items: [
      { label: "Movimiento de brazos", icon: Hand },
      { label: "Posible arrastre de pies", icon: Footprints },
      { label: "Posible rigidez", icon: Ban },
    ],
  },
  {
    title: "Estabilidad",
    items: [{ label: "Estabilidad", icon: Scale }],
  },
];
