import { CSSProperties } from "react";
import Image from "next/image";
import { ArrowRight, FileText, ListChecks, ShieldCheck, Video } from "lucide-react";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { BrandMark } from "@/components/brand/BrandMark";
import { LinkButton } from "@/components/ui/LinkButton";
import { OBSERVED_GROUPS } from "@/components/analysis/guidance";
import styles from "./home.module.css";

const STEPS = [
  {
    title: "Sube un video",
    text: "Un video caminando, con el cuerpo completo visible.",
  },
  {
    title: "Revisión",
    text: "Confirmas que el video cumple las recomendaciones de grabación.",
  },
  {
    title: "Análisis de movimiento",
    text: "El sistema detecta los puntos del cuerpo y evalúa la marcha.",
  },
  {
    title: "Resultado e informe",
    text: "Recibes una orientación explicada y un informe para tu consulta.",
  },
];

const PROOF = [
  { icon: Video, title: "Análisis a partir de un video", text: "Sin sensores ni equipos especiales." },
  { icon: ListChecks, title: "Explicación de cada hallazgo", text: "Qué se observó y por qué es relevante." },
  { icon: FileText, title: "Informe para tu consulta", text: "Un documento para compartir con un profesional." },
];

const delay = (i: number) => ({ "--i": i }) as CSSProperties;

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <PublicHeader />

      <main>
        {/* ================= Hero ================= */}
        <section className={styles.hero} aria-labelledby="home-heading">
          <div className={styles.imageWrap} aria-hidden="true">
            <Image
              src="/images/gait-biomechanics-hero.png"
              alt=""
              fill
              preload
              sizes="100vw"
              className={styles.image}
            />
          </div>
          <div className={styles.veil} aria-hidden="true" />
          <div className={styles.heroInner}>
            <div className={styles.copy}>
              <p
                className={`reveal ${styles.eyebrow}`}
                style={delay(0)}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
                Tecnología para una evaluación objetiva
              </p>

              <h1
                id="home-heading"
                className={`reveal ${styles.title}`}
                style={delay(1)}
              >
                Analiza tu marcha con inteligencia artificial
              </h1>

              <p className={`reveal ${styles.description}`} style={delay(2)}>
                Obtén un análisis orientativo de tu forma de caminar a partir de un
                video, detecta patrones de movimiento y recibe información clara
                para compartir con un profesional de salud.
              </p>

              <div className={`reveal ${styles.actions}`} style={delay(3)}>
                <LinkButton href="/login" size="lg">
                  Comenzar análisis
                  <ArrowRight aria-hidden />
                </LinkButton>
                <LinkButton href="#funciona" variant="outline" size="lg">
                  Ver cómo funciona
                </LinkButton>
              </div>

              <p className={`reveal ${styles.note}`} style={delay(4)}>
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" aria-hidden />
                Resultado orientativo, no diagnóstico. Toda interpretación debe
                revisarse con un profesional de salud.
              </p>
            </div>
          </div>
        </section>

        {/* ================= Prueba ================= */}
        <section className="border-y border-line bg-surface-subtle">
          <div className="mx-auto grid max-w-[1240px] px-4 md:grid-cols-3 md:px-8">
            {PROOF.map(({ icon: Icon, title, text }, index) => (
              <div
                key={title}
                className={`flex gap-3 py-6 md:px-6 ${index > 0 ? "border-t border-line md:border-l md:border-t-0" : "md:pl-0"}`}
              >
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden />
                <div>
                  <p className="text-sm font-semibold text-ink">{title}</p>
                  <p className="mt-0.5 text-sm text-ink-muted">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ================= Cómo funciona ================= */}
        <section id="funciona" className="mx-auto max-w-[1240px] scroll-mt-20 px-4 py-20 md:px-8 lg:py-24">
          <div className="max-w-xl">
            <p className="text-xs font-bold uppercase tracking-[0.09em] text-accent-cyan-ink">Cómo funciona</p>
            <h2 className="mt-2 text-[28px] font-bold leading-9 tracking-[-0.02em] text-ink md:text-[32px] md:leading-10">
              Cuatro pasos, de tu video a un informe
            </h2>
          </div>

          <ol className="relative mt-12 grid gap-8 md:grid-cols-4 md:gap-6">
            <span className="absolute left-0 right-0 top-[18px] hidden h-px bg-line-strong md:block" aria-hidden />
            {STEPS.map((step, index) => (
              <li key={step.title} className="relative flex gap-4 md:block">
                <span className="relative z-10 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line-strong bg-background font-mono text-xs font-medium text-ink">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="md:mt-5 md:pr-4">
                  <h3 className="text-base font-semibold text-ink">{step.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-ink-muted">{step.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        {/* ================= Qué analiza ================= */}
        <section id="analiza" className="scroll-mt-16 border-t border-line bg-surface">
          <div className="mx-auto grid max-w-[1240px] gap-12 px-4 py-20 md:px-8 lg:grid-cols-12 lg:py-24">
            <div className="lg:col-span-4">
              <p className="text-xs font-bold uppercase tracking-[0.09em] text-accent-cyan-ink">Qué analiza</p>
              <h2 className="mt-2 text-[28px] font-bold leading-9 tracking-[-0.02em] text-ink md:text-[32px] md:leading-10">
                Lo que el sistema observa en tu caminata
              </h2>
              <p className="mt-4 text-[15px] leading-7 text-ink-muted">
                A partir de los puntos del cuerpo detectados en el video, el
                sistema describe características de la marcha y las explica en
                lenguaje sencillo.
              </p>
            </div>

            <div className="grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 lg:col-span-8">
              {OBSERVED_GROUPS.map((group) => (
                <div key={group.title} className="bg-surface p-6">
                  <h3 className="text-[11px] font-bold uppercase tracking-[0.09em] text-ink-subtle">{group.title}</h3>
                  <ul className="mt-4 space-y-3">
                    {group.items.map(({ label, icon: Icon }) => (
                      <li key={label} className="flex items-center gap-3 text-[15px] font-medium text-ink">
                        <Icon className="h-4 w-4 shrink-0 text-navy-700" aria-hidden />
                        {label}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ================= Uso responsable ================= */}
        <section id="responsable" className="scroll-mt-16 bg-navy-900">
          <div className="mx-auto grid max-w-[1240px] gap-10 px-4 py-20 md:px-8 lg:grid-cols-12 lg:py-24">
            <div className="lg:col-span-5">
              <p className="text-xs font-bold uppercase tracking-[0.09em] text-accent-cyan">Uso responsable</p>
              <h2 className="mt-2 text-[28px] font-bold leading-9 tracking-[-0.02em] text-white md:text-[32px] md:leading-10">
                Una orientación para tu consulta, no un diagnóstico
              </h2>
              <p className="mt-4 text-[15px] leading-7 text-on-navy">
                Este sistema no reemplaza una valoración médica profesional. El
                resultado es una orientación inicial generada a partir del
                análisis visual de la marcha.
              </p>
              <LinkButton href="/registro" size="lg" className="mt-8">
                Crear cuenta
                <ArrowRight aria-hidden />
              </LinkButton>
            </div>

            <dl className="grid gap-px self-start overflow-hidden rounded-xl border border-navy-700 bg-navy-700 lg:col-span-6 lg:col-start-7">
              {[
                ["Patrón compatible", "Indica similitud con patrones de marcha aprendidos; no confirma una enfermedad."],
                ["Características observadas", "Describe lo que se vio en el video, en lenguaje sencillo."],
                ["Requiere valoración profesional", "La interpretación clínica corresponde a un profesional de salud."],
              ].map(([term, detail]) => (
                <div key={term} className="bg-navy-900 p-6">
                  <dt className="text-[15px] font-semibold text-white">{term}</dt>
                  <dd className="mt-1 text-sm leading-6 text-on-navy">{detail}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>
      </main>

      <footer className="border-t border-navy-800 bg-navy-950">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-3 px-4 py-8 md:flex-row md:items-center md:justify-between md:px-8">
          <BrandMark tone="light" />
          <p className="text-[13px] text-on-navy">
            Resultado orientativo. No constituye un diagnóstico médico.
          </p>
        </div>
      </footer>
    </div>
  );
}
