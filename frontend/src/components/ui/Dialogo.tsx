import { useEffect, useRef, type ReactNode } from "react";

/** Diálogo modal accesible basado en <dialog> (Esc cierra, foco atrapado por el navegador). */
export function Dialogo({
  abierto,
  titulo,
  alCerrar,
  children,
}: {
  abierto: boolean;
  titulo: string;
  alCerrar: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo) return;
    if (abierto && !dialogo.open) dialogo.showModal?.();
    if (!abierto && dialogo.open) dialogo.close?.();
  }, [abierto]);

  return (
    <dialog
      ref={ref}
      onClose={alCerrar}
      aria-labelledby="titulo-dialogo"
      className="m-auto w-full max-w-md rounded-lg p-0 shadow-xl backdrop:bg-slate-900/40"
    >
      {abierto && (
        <div className="p-5">
          <h2 id="titulo-dialogo" className="mb-3 text-lg font-semibold text-slate-900">
            {titulo}
          </h2>
          {children}
        </div>
      )}
    </dialog>
  );
}
