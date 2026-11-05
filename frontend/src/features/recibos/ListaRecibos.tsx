import { Search } from "lucide-react";
import { useState } from "react";

import { useRecibos } from "../../api/consultas";
import { Cargando, ErrorVista, Seccion, Vacio } from "../../components/ui/Basicos";
import { Paginacion } from "../../components/ui/Paginacion";
import { claseInput } from "../../lib/estilos";
import { useDiferido } from "../../lib/hooks";
import { TablaRecibos } from "./TablaRecibos";

export function ListaRecibos() {
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(1);
  const buscar = useDiferido(texto, 350);
  const { data, isLoading, error, refetch } = useRecibos({ buscar, pagina });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Recibos de Caja</h1>
        <p className="text-sm text-slate-500">
          Busque por número de recibo, cliente, lote o número FEL.
        </p>
      </div>
      <Seccion titulo="Listado">
        <label className="relative mb-4 block">
          <span className="sr-only">Buscar</span>
          <Search
            className="pointer-events-none absolute left-3 top-2.5 size-4 text-slate-400"
            aria-hidden
          />
          <input
            type="search"
            value={texto}
            placeholder="Buscar recibo…"
            className={`${claseInput(false)} pl-9`}
            onChange={(e) => {
              setTexto(e.target.value);
              setPagina(1);
            }}
          />
        </label>
        {isLoading && <Cargando />}
        {error && <ErrorVista error={error} reintentar={() => void refetch()} />}
        {data && data.items.length === 0 && (
          <Vacio
            mensaje={buscar ? "Ningún recibo coincide con la búsqueda." : "Aún no hay recibos."}
          />
        )}
        {data && data.items.length > 0 && (
          <>
            <TablaRecibos recibos={data.items} mostrarCliente />
            <Paginacion
              pagina={data.pagina}
              tamano={data.tamano}
              total={data.total}
              cambiar={setPagina}
            />
          </>
        )}
      </Seccion>
    </div>
  );
}
