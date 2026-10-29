import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { BrandMark } from "@/components/brand/BrandMark";
import { GaitFigure } from "@/components/brand/GaitFigure";

type AuthLayoutProps = {
  panelTitle: string;
  panelText: string;
  panelNote: string;
  children: React.ReactNode;
};

/** Composición compartida de acceso: formulario blanco y orientación visual. */
export function AuthLayout({ panelTitle, panelText, panelNote, children }: AuthLayoutProps) {
  return (
    <main className="auth-screen grid min-h-screen lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
      <section className="auth-form-panel flex flex-col px-5 py-8 sm:px-10 lg:px-14">
        <Link href="/" className="self-start rounded-md">
          <BrandMark />
        </Link>
        <div className="mx-auto flex w-full max-w-[440px] flex-1 flex-col justify-center py-10">
          {children}
        </div>
      </section>

      <section className="auth-visual-panel hidden flex-col justify-center gap-8 overflow-hidden p-12 lg:flex xl:p-16">
        <div className="max-w-md">
          <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink-muted">Análisis de marcha</p>
          <h2 className="mt-3 text-[28px] font-semibold leading-[36px] tracking-[-0.03em] text-ink">{panelTitle}</h2>
          <p className="mt-4 text-sm leading-7 text-ink-muted">{panelText}</p>
        </div>

        <div className="auth-visual-figure mx-auto w-full px-8 py-4">
          <GaitFigure tone="light" guides grid />
        </div>

        <p className="flex max-w-md items-start gap-2.5 border-t border-line pt-5 text-xs leading-5 text-ink-muted">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary-dark" aria-hidden />
          {panelNote}
        </p>
      </section>
    </main>
  );
}
