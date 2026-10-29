import Link from "next/link";
import { BrandMark } from "@/components/brand/BrandMark";
import { LinkButton } from "@/components/ui/LinkButton";

const ANCHORS = [
  ["Cómo funciona", "#funciona"],
  ["Qué analiza", "#analiza"],
  ["Uso responsable", "#responsable"],
];

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-surface/95 backdrop-blur-sm">
      <div className="mx-auto flex min-h-[72px] max-w-[1440px] items-center justify-between gap-4 px-4 md:px-10">
        <Link href="/" className="rounded-md">
          <BrandMark />
        </Link>

        <nav aria-label="Secciones" className="hidden items-center gap-7 md:flex">
          {ANCHORS.map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="text-sm font-medium text-ink-muted transition-colors duration-150 hover:text-ink"
            >
              {label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <LinkButton href="/login" variant="outline" size="sm" className="hidden sm:inline-flex">
            Iniciar sesión
          </LinkButton>
          <LinkButton href="/registro" size="sm">
            Crear cuenta
          </LinkButton>
        </div>
      </div>
    </header>
  );
}
