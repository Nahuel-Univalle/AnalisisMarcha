import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Análisis de Marcha IA",
  description: "Sistema web de orientación inicial para análisis de marcha humana.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="bg-slate-50 text-slate-800 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
