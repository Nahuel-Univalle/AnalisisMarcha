import Link, { LinkProps } from "next/link";
import { AnchorHTMLAttributes } from "react";
import { buttonClasses, ButtonSize, ButtonVariant } from "./Button";

type LinkButtonProps = LinkProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
  };

/**
 * Una acción que navega (no ejecuta un handler) pero debe verse exactamente
 * como <Button>. Antes, cada pantalla que necesitaba esto copiaba a mano las
 * clases de Button sobre un <Link> (PublicHeader, AdminDashboard, landing),
 * y ya habían divergido entre sí. Este componente reutiliza las mismas
 * clases (buttonClasses) para que ambos queden siempre sincronizados.
 */
export function LinkButton({
  className,
  variant = "primary",
  size = "md",
  ...props
}: LinkButtonProps) {
  return <Link className={buttonClasses({ variant, size, className })} {...props} />;
}
