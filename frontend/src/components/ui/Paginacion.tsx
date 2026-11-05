import { ChevronLeft, ChevronRight } from "lucide-react";

import { Boton } from "./Boton";

export function Paginacion({
  pagina,
  tamano,
  total,
  cambiar,
}: {
  pagina: number;
  tamano: number;
  total: number;
  cambiar: (pagina: number) => void;
}) {
  const paginas = Math.max(1, Math.ceil(total / tamano));
  if (total <= tamano) return null;
  return (
    <nav
      aria-label="Paginación"
      className="mt-3 flex items-center justify-between text-sm text-slate-600"
    >
      <span>
        Página {pagina} de {paginas} · {total} registros
      </span>
      <div className="flex gap-2">
        <Boton
          variante="secundario"
          pequeno
          disabled={pagina <= 1}
          onClick={() => cambiar(pagina - 1)}
          icono={<ChevronLeft className="size-4" aria-hidden />}
        >
          Anterior
        </Boton>
        <Boton
          variante="secundario"
          pequeno
          disabled={pagina >= paginas}
          onClick={() => cambiar(pagina + 1)}
          icono={<ChevronRight className="size-4" aria-hidden />}
        >
          Siguiente
        </Boton>
      </div>
    </nav>
  );
}
