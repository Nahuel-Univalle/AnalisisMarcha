import { CSSProperties } from "react";
import { cn } from "@/lib/utils";

/**
 * Esqueleto de marcha en mitad de zancada (vista lateral), con la misma
 * topología de articulaciones que detecta el sistema: cabeza, hombros, codos,
 * muñecas, caderas, rodillas, tobillos, talones y puntas de pie.
 *
 * Firma visual del producto sobre una superficie oscura o mint.
 * No muestra valores: las etiquetas nombran lo que el sistema observa, nunca
 * cifras inventadas.
 */

type Point = [number, number];

const J = {
  head: [212, 62],
  neck: [205, 104],
  shoulderN: [196, 122],
  shoulderF: [220, 118],
  elbowN: [178, 192],
  wristN: [158, 252],
  elbowF: [240, 186],
  wristF: [266, 244],
  hipN: [196, 262],
  hipF: [214, 258],
  kneeN: [236, 352],
  ankleN: [250, 444],
  heelN: [242, 460],
  toeN: [284, 452],
  kneeF: [186, 356],
  ankleF: [146, 430],
  heelF: [134, 438],
  toeF: [170, 461],
} satisfies Record<string, Point>;

type JointKey = keyof typeof J;

// Orden = orden de dibujo. Primero el lado lejano (tenue), luego tronco y lado cercano.
const FAR_BONES: Array<[JointKey, JointKey]> = [
  ["shoulderF", "elbowF"],
  ["elbowF", "wristF"],
  ["hipF", "kneeF"],
  ["kneeF", "ankleF"],
  ["ankleF", "heelF"],
  ["heelF", "toeF"],
  ["ankleF", "toeF"],
];

const TRUNK_BONES: Array<[JointKey, JointKey]> = [
  ["neck", "shoulderN"],
  ["neck", "shoulderF"],
  ["shoulderN", "shoulderF"],
  ["shoulderN", "hipN"],
  ["shoulderF", "hipF"],
  ["hipN", "hipF"],
];

const NEAR_BONES: Array<[JointKey, JointKey]> = [
  ["shoulderN", "elbowN"],
  ["elbowN", "wristN"],
  ["hipN", "kneeN"],
  ["kneeN", "ankleN"],
  ["ankleN", "heelN"],
  ["heelN", "toeN"],
  ["ankleN", "toeN"],
];

const FAR_POINTS: JointKey[] = ["shoulderF", "elbowF", "wristF", "hipF", "kneeF", "ankleF", "heelF", "toeF"];
const NEAR_POINTS: JointKey[] = [
  "head",
  "neck",
  "shoulderN",
  "elbowN",
  "wristN",
  "hipN",
  "kneeN",
  "ankleN",
  "heelN",
  "toeN",
];

// Puntos con halo (pulso lento en landing / pulso durante el procesamiento).
const HALO_POINTS: JointKey[] = ["ankleN", "hipN", "wristF", "ankleF", "kneeN"];

// Trayectoria del tobillo en la fase de balanceo (curva de Bézier) y
// muestras sobre ella, como "historial" de posiciones del punto.
const ANKLE_TRACE = "M 70 440 C 120 405, 200 405, 250 444";
const TRACE_SAMPLES: Point[] = [
  [103, 423],
  [141, 415],
  [179, 416],
  [217, 425],
];

const GROUND_Y = 462;

const iv = (i: number) => ({ "--i": i }) as CSSProperties;

type GaitFigureProps = {
  tone?: "dark" | "light";
  /** Dibujo de entrada: huesos, luego puntos, luego trayectoria. */
  animated?: boolean;
  /** Pulso lento en 3–5 articulaciones (landing). */
  ambient?: boolean;
  /** Pulso más activo (durante el análisis real). */
  active?: boolean;
  /** Guías de medida: plomada, altura de cadera, longitud de paso, ángulo de rodilla. */
  guides?: boolean;
  /** Etiquetas de lo que observa el sistema (sin valores). */
  annotations?: boolean;
  /** Retícula de medición de fondo. */
  grid?: boolean;
  className?: string;
  title?: string;
};

export function GaitFigure({
  tone = "dark",
  animated = false,
  ambient = false,
  active = false,
  guides = true,
  annotations = false,
  grid = false,
  className,
  title = "Esqueleto de marcha con los puntos corporales que analiza el sistema",
}: GaitFigureProps) {
  const line = (a: JointKey, b: JointKey) => ({ x1: J[a][0], y1: J[a][1], x2: J[b][0], y2: J[b][1] });

  return (
    <svg
      viewBox="-20 0 460 510"
      role="img"
      aria-label={title}
      style={{
        "--figure-line": tone === "light" ? "#0B9586" : "#CCFCF0",
        "--figure-guide": tone === "light" ? "#124F48" : "#CCFCF0",
        "--figure-surface": tone === "light" ? "#FFFFFF" : "#124F48",
      } as CSSProperties}
      className={cn(
        "block h-auto w-full overflow-visible",
        animated && "gf-animated",
        ambient && "gf-ambient",
        active && "gf-active",
        className
      )}
    >
      <defs>
        <pattern id="gf-grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="var(--figure-guide)" strokeOpacity="0.07" strokeWidth="1" />
        </pattern>
      </defs>

      {grid && <rect x="-20" y="0" width="460" height="510" fill="url(#gf-grid)" />}

      {/* Guías de medida */}
      {guides && (
        <g stroke="var(--figure-guide)" strokeOpacity="0.32" strokeWidth="1" fill="none">
          {/* Plomada del tronco */}
          <line x1="205" y1="24" x2="205" y2={GROUND_Y} strokeDasharray="3 5" />
          {/* Altura de cadera */}
          <line x1="20" y1="260" x2="400" y2="260" strokeDasharray="3 5" />
          {/* Suelo */}
          <line x1="0" y1={GROUND_Y} x2="420" y2={GROUND_Y} strokeOpacity="0.5" />
          {/* Marcas de apoyo (pisadas) */}
          {[70, 170, 242, 330].map((x, i) => (
            <line key={x} x1={x} y1={GROUND_Y - 6} x2={x} y2={GROUND_Y + 6} strokeOpacity={i === 3 ? 0.18 : 0.55} />
          ))}
          {/* Longitud de paso */}
          <path d={`M 170 ${GROUND_Y + 14} v 6 H 242 v -6`} strokeOpacity="0.55" />
          {/* Ángulo de rodilla */}
          <path d="M 228 330 A 26 26 0 0 0 245 375" strokeOpacity="0.6" />
        </g>
      )}

      {guides && (
        <g className="font-mono" fill="var(--figure-guide)" fillOpacity="0.55" fontSize="9" letterSpacing="0.06em">
          <text x="24" y="252">CADERA</text>
          <text x="174" y={GROUND_Y + 34}>PASO</text>
        </g>
      )}

      {/* Trayectoria del tobillo */}
      <path
        d={ANKLE_TRACE}
        pathLength={1}
        className="gf-trace"
        fill="none"
        stroke="var(--figure-line)"
        strokeOpacity="0.55"
        strokeWidth="1.5"
      />
      {TRACE_SAMPLES.map(([x, y], i) => (
        <circle
          key={x}
          cx={x}
          cy={y}
          r={2.2}
          fill="var(--figure-line)"
          fillOpacity={0.25 + i * 0.15}
          className="gf-point"
          style={iv(20 + i)}
        />
      ))}

      {/* Cabeza */}
      <circle
        cx={J.head[0]}
        cy={J.head[1]}
        r="19"
        pathLength={1}
        className="gf-bone"
        style={iv(0)}
        fill="none"
        stroke="var(--figure-line)"
        strokeWidth="2.5"
      />
      <line {...line("head", "neck")} y1={J.head[1] + 19} pathLength={1} className="gf-bone" style={iv(1)} stroke="var(--figure-line)" strokeWidth="3" strokeLinecap="round" />

      {/* Huesos */}
      <g stroke="var(--figure-line)" strokeLinecap="round" strokeLinejoin="round">
        {FAR_BONES.map(([a, b], i) => (
          <line key={`f${a}${b}`} {...line(a, b)} pathLength={1} className="gf-bone" style={iv(2 + i)} strokeWidth="2.5" strokeOpacity="0.4" />
        ))}
        {TRUNK_BONES.map(([a, b], i) => (
          <line key={`t${a}${b}`} {...line(a, b)} pathLength={1} className="gf-bone" style={iv(4 + i)} strokeWidth="3" strokeOpacity="0.85" />
        ))}
        {NEAR_BONES.map(([a, b], i) => (
          <line key={`n${a}${b}`} {...line(a, b)} pathLength={1} className="gf-bone" style={iv(6 + i)} strokeWidth="3.25" />
        ))}
      </g>

      {/* Halos */}
      {HALO_POINTS.map((key, i) => (
        <circle key={`h${key}`} cx={J[key][0]} cy={J[key][1]} r="6" fill="var(--figure-line)" className="gf-halo" style={iv(i)} />
      ))}

      {/* Puntos corporales */}
      {FAR_POINTS.map((key, i) => (
        <circle
          key={`pf${key}`}
          cx={J[key][0]}
          cy={J[key][1]}
          r="3.6"
          fill="var(--figure-line)"
          fillOpacity="0.55"
          className="gf-point"
          style={iv(i)}
        />
      ))}
      {NEAR_POINTS.map((key, i) => (
        <circle
          key={`pn${key}`}
          cx={J[key][0]}
          cy={J[key][1]}
          r={key === "head" ? 3.5 : 5}
          fill="var(--figure-line)"
          stroke="var(--figure-surface)"
          strokeWidth="2"
          className="gf-point"
          style={iv(4 + i)}
        />
      ))}

      {/* Anotaciones: qué observa el sistema (sin valores) */}
      {annotations && (
        <g className="font-mono" fontSize="10.5" letterSpacing="0.05em">
          <Annotation from={J.wristF} box={[290, 196]} width={138} label="BALANCEO DE BRAZOS" />
          <Annotation from={J.hipN} box={[-12, 290]} width={142} label="SIMETRÍA IZQ. / DER." />
          <Annotation from={[284, GROUND_Y]} box={[300, 478]} width={116} label="RITMO Y CADENCIA" />
        </g>
      )}
    </svg>
  );
}

function Annotation({ from, box, width, label }: { from: Point; box: Point; width: number; label: string }) {
  const [bx, by] = box;
  const anchorX = bx > from[0] ? bx : bx + width;
  return (
    <g className="gf-point" style={iv(18)}>
      <line x1={from[0]} y1={from[1]} x2={anchorX} y2={by + 11} stroke="var(--figure-guide)" strokeOpacity="0.5" strokeWidth="1" />
      <rect x={bx} y={by} width={width} height={22} rx={4} fill="var(--figure-surface)" stroke="var(--figure-guide)" />
      <circle cx={bx + 10} cy={by + 11} r={2.5} fill="var(--figure-line)" />
      <text x={bx + 18} y={by + 15} fill="var(--figure-guide)">
        {label}
      </text>
    </g>
  );
}
