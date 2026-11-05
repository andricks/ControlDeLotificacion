import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variante = "primario" | "secundario" | "peligro" | "fantasma";

const VARIANTES: Record<Variante, string> = {
  primario: "bg-primario text-white hover:bg-primario-hover shadow-sm",
  secundario: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 shadow-sm",
  peligro: "bg-peligro text-white hover:opacity-90 shadow-sm",
  fantasma: "text-primario hover:bg-primario-suave",
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante;
  cargando?: boolean;
  icono?: ReactNode;
  pequeno?: boolean;
}

export function Boton({
  variante = "primario",
  cargando = false,
  icono,
  pequeno = false,
  className = "",
  children,
  disabled,
  type = "button",
  ...resto
}: Props) {
  return (
    <button
      type={type}
      disabled={disabled || cargando}
      aria-busy={cargando}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
        "disabled:cursor-not-allowed disabled:opacity-60",
        pequeno ? "px-2.5 py-1.5 text-xs" : "px-4 py-2 text-sm",
        VARIANTES[variante],
        className,
      ].join(" ")}
      {...resto}
    >
      {cargando ? <Loader2 className="size-4 animate-spin" aria-hidden /> : icono}
      {children}
    </button>
  );
}
