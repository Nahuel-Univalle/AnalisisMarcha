import { redirect } from "next/navigation";

/**
 * `/referencias` no tiene contenido propio: antes renderizaba el mismo
 * componente que `/datasets/parkinson` bajo una URL distinta, sin ningún
 * enlace de navegación que apuntara aquí. Se mantiene como redirect para no
 * romper accesos directos a esta URL; `/datasets/parkinson` es la única
 * fuente de verdad. La ruta ya está protegida (solo admin) por
 * `src/proxy.ts`, por lo que no hace falta repetir esa verificación aquí.
 */
export default function ReferencesPage() {
  redirect("/datasets/parkinson");
}
