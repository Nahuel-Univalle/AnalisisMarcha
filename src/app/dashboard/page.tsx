"use client";

import Link from "next/link";
import Image from "next/image";
import { Activity, ArrowRight, FileText, History, Plus, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { LinkButton } from "@/components/ui/LinkButton";
import { AdminDashboard } from "@/components/admin/AdminDashboard";
import { useAuth } from "@/context/AuthContext";
import styles from "./dashboard.module.css";

export default function DashboardPage() {
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";

  if (admin) {
    return (
      <AppShell>
        <AdminDashboard />
      </AppShell>
    );
  }

  const firstName = user?.name?.split(" ").filter(Boolean)[0] || "Usuario";
  return (
    <AppShell className={styles.dashboardShell}>
      <div className={styles.page}>
        <section className={styles.hero} aria-labelledby="welcome-heading">
          <div className={styles.backdrop}>
            <Image
              src="/images/gait-biomechanics-hero.png"
              alt="Mujer caminando con puntos de seguimiento biomecánico en el cuerpo"
              fill
              preload
              sizes="100vw"
              className={styles.photo}
            />
          </div>
          <div className={styles.heroContent}>
            <div className={`reveal ${styles.copy}`}>
              <p className={styles.greeting}>Hola, {firstName}</p>
              <p className={styles.eyebrow}><Activity className="h-4 w-4" aria-hidden /> Análisis de movimiento con IA</p>
              <h1 id="welcome-heading">Panel de análisis<br className="hidden sm:block" /> de marcha</h1>
              <p className={styles.description}>Obtén una orientación sobre tu forma de caminar a partir de un video. Revisa los patrones observados y comparte el informe con un profesional de salud.</p>
              <LinkButton href="/analisis/subir-video" size="lg" className={styles.action}>
                <Plus aria-hidden /> Nuevo análisis <ArrowRight aria-hidden />
              </LinkButton>
              <p className={styles.note}><ShieldCheck className="h-4 w-4 shrink-0" aria-hidden /> El análisis es orientativo y no reemplaza una valoración médica.</p>
            </div>
          </div>
        </section>
        <div className={styles.shortcuts}>
          <Link href="/seguimiento" className="welcome-shortcut">
            <History className="h-5 w-5 text-primary" aria-hidden />
            <div><h2>Seguimiento</h2><p>Consulta tus análisis anteriores.</p></div>
            <ArrowRight className="ml-auto h-4 w-4" aria-hidden />
          </Link>
          <Link href="/analisis/informe" className="welcome-shortcut">
            <FileText className="h-5 w-5 text-primary" aria-hidden />
            <div><h2>Informes</h2><p>Revisa tus informes guardados.</p></div>
            <ArrowRight className="ml-auto h-4 w-4" aria-hidden />
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
