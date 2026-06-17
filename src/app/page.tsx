import Link from "next/link";
import {
  Activity,
  Brain,
  FileText,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { Card } from "@/components/ui/Card";
import { MedicalDisclaimer } from "@/components/ui/MedicalDisclaimer";

export default function LandingPage() {
  return (
    <div className="min-h-screen gradient-bg animate-fadeIn">
      <PublicHeader />

      <main className="mx-auto w-full max-w-7xl px-4 pb-8 pt-0 md:px-8 md:pt-0">
        <section className="grid min-h-[520px] items-start gap-10 pt-0 md:min-h-[560px] md:grid-cols-2 md:pt-2">
          <div className="pt-6 md:pt-10">
            <div className="mb-5 inline-flex rounded-full bg-blue-100 px-4 py-2 text-sm font-bold text-primary shadow-md">
              Salud digital e inteligencia artificial responsable
            </div>

            <h1 className="text-4xl font-black tracking-tight text-slate-900 md:text-6xl">
              Cuida tu forma de caminar con ayuda de inteligencia artificial
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-500">
              Sube un video caminando y recibe una orientación inicial sobre
              posibles señales relacionadas con la marcha, para apoyar una futura
              consulta médica.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-full bg-primary px-7 py-4 font-semibold text-white shadow-md transition duration-200 hover:scale-[1.02] hover:bg-blue-600 hover:shadow-lg"
              >
                Comenzar análisis
              </Link>

              <Link
                href="#funciona"
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-7 py-4 font-semibold text-slate-900 shadow-md transition duration-200 hover:scale-[1.02] hover:bg-slate-50 hover:shadow-lg"
              >
                Ver cómo funciona
              </Link>
            </div>

            <div className="mt-8">
              <MedicalDisclaimer />
            </div>
          </div>

          <Card className="relative mt-4 overflow-hidden bg-linear-to-br from-blue-700 to-emerald-600 p-8 text-white shadow-xl shadow-blue-200/70 md:mt-8">
            <div className="mb-6 flex items-center gap-3">
              <Activity className="h-8 w-8 text-emerald-200" />
              <h2 className="text-2xl font-bold">Análisis visual de marcha</h2>
            </div>

            <div className="relative aspect-video rounded-3xl bg-white/10">
              <div className="absolute left-1/2 top-10 h-14 w-14 -translate-x-1/2 rounded-full border-4 border-emerald-200" />
              <div className="absolute left-1/2 top-24 h-28 w-1 -translate-x-1/2 bg-emerald-200" />
              <div className="absolute left-[42%] top-32 h-1 w-24 bg-emerald-200" />
              <div className="absolute left-[45%] top-52 h-24 w-1 rotate-12 bg-emerald-200" />
              <div className="absolute left-[55%] top-52 h-24 w-1 -rotate-12 bg-emerald-200" />

              <div className="absolute bottom-6 left-6 rounded-2xl bg-white/15 p-4 backdrop-blur">
                Puntos corporales detectados
              </div>
            </div>
          </Card>
        </section>

        <section id="funciona" className="mt-16 pb-10 md:mt-24">
          <h2 className="text-center text-3xl font-black text-slate-900">
            ¿Cómo funciona?
          </h2>

          <div className="mt-8 grid gap-5 md:grid-cols-4">
            {[
              { title: "Sube un video", icon: UploadCloud },
              { title: "Validación del video", icon: ShieldCheck },
              { title: "Análisis de movimiento", icon: Brain },
              { title: "Informe médico", icon: FileText },
            ].map((item, index) => {
              const Icon = item.icon;

              return (
                <Card key={item.title} className="text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-primary shadow-md">
                    <Icon className="h-7 w-7" />
                  </div>

                  <h3 className="font-bold text-slate-950">
                    {index + 1}. {item.title}
                  </h3>
                </Card>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}
