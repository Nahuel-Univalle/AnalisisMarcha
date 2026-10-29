import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  /**
   * Solo para superficies realmente clickeables/navegables. El Card base no
   * reacciona al hover: la mayoría de sus usos son contenido estático.
   */
  interactive?: boolean;
};

/**
 * Superficie blanca con borde fino, sin sombra. Representa UNA zona de
 * contenido; dentro se separa con divisores, nunca con otro Card.
 */
export function Card({ className, interactive = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-line bg-surface p-6",
        interactive &&
          "cursor-pointer transition-[border-color,box-shadow] duration-150 hover:border-line-strong hover:shadow-raised",
        className
      )}
      {...props}
    />
  );
}
