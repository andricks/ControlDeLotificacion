import { FilePlus2, Search, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { useContratos } from "../../api/consultas";
import { Cargando, ErrorVista, Insignia, Seccion, Vacio } from "../../components/ui/Basicos";
import { BotonPdf } from "../../components/ui/BotonPdf";
import { Seleccion } from "../../components/ui/Campos";
import { Paginacion } from "../../components/ui/Paginacion";
import { claseInput, claseTabla, claseTd, claseTh } from "../../lib/estilos";
import {
  ETIQUETA_ESTADO_CONTRATO,
  fecha,
  moneda,
  NOMBRE_LOTIFICACION,
  TONO_ESTADO,
} from "../../lib/formato";
import { useDiferido } from "../../lib/hooks";

const ESTADOS = [
  { valor: "", texto: "Todos" },
  ...Object.entries(ETIQUETA_ESTADO_CONTRATO).map(([valor, texto]) => ({ valor, texto })),
];

export function ListaPromesas() {
  const [params, setParams] = useSearchParams();
  const [texto, setTexto] = useState(params.get("buscar") ?? "");
  const buscar = useDiferido(texto, 350);
  const estado = params.get("estado") ?? "";
  const pagina = Number(params.get("pagina") ?? "1") || 1;

  useEffect(() => {
    setParams(
      (p) => {
        if (buscar) p.set("buscar", buscar);
        else p.delete("buscar");
        if ((p.get("buscar") ?? "") !== (params.get("buscar") ?? "")) p.delete("pagina");
        return p;
      },
      { replace: true },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buscar]);

  const cambiar = (clave: string, valor: string) =>
    setParams((p) => {
      if (valor) p.set(clave, valor);
      else p.delete(clave);
      if (clave !== "pagina") p.delete("pagina");
      return p;
    });

  const { data, isLoading, error, refetch } = useContratos({ buscar, estado, pagina });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Promesas de Compra Venta</h1>
          <p className="text-sm text-slate-500">Busque por número, nombre, DPI o lote.</p>
        </div>
        <Link
          to="/promesas/nueva"
          className="inline-flex items-center gap-2 rounded-md bg-primario px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primario-hover"
        >
          <FilePlus2 className="size-4" aria-hidden /> Nueva promesa
        </Link>
      </div>

      <Seccion titulo="Listado">
        <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_12rem]">
          <label className="relative block">
            <span className="sr-only">Buscar</span>
            <Search
              className="pointer-events-none absolute left-3 top-2.5 size-4 text-slate-400"
              aria-hidden
            />
            <input
              type="search"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Buscar por No., nombre, DPI o lote…"
              className={`${claseInput(false)} pl-9`}
            />
          </label>
          <Seleccion
            etiqueta="Estado"
            opciones={ESTADOS}
            value={estado}
            onChange={(e) => cambiar("estado", e.target.value)}
          />
        </div>

        {isLoading && <Cargando />}
        {error && <ErrorVista error={error} reintentar={() => void refetch()} />}
        {data && data.items.length === 0 && (
          <Vacio
            mensaje={
              buscar || estado
                ? "No hay promesas que coincidan con la búsqueda."
                : "Aún no hay promesas registradas."
            }
            accion={
              !buscar && !estado ? (
                <Link to="/promesas/nueva" className="text-primario underline">
                  Registrar la primera promesa
                </Link>
              ) : undefined
            }
          />
        )}
        {data && data.items.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <table className={claseTabla}>
                <thead className="bg-slate-50">
                  <tr>
                    <th className={claseTh}>No.</th>
                    <th className={claseTh}>Firma</th>
                    <th className={claseTh}>Comprador</th>
                    <th className={claseTh}>Lote</th>
                    <th className={`${claseTh} text-right`}>Total</th>
                    <th className={`${claseTh} text-right`}>Saldo</th>
                    <th className={claseTh}>Estado</th>
                    <th className={claseTh}>
                      <span className="sr-only">Acciones</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.items.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50">
                      <td className={claseTd}>
                        <Link
                          to={`/promesas/${c.id}`}
                          className="font-medium text-primario hover:underline"
                        >
                          {c.numero_formateado}
                        </Link>
                      </td>
                      <td className={claseTd}>{fecha(c.fecha_firma)}</td>
                      <td className={claseTd}>
                        <div>{c.comprador_nombre}</div>
                        <div className="text-xs text-slate-500">DPI {c.comprador_dpi}</div>
                      </td>
                      <td className={claseTd}>
                        <div>{c.lote_codigo}</div>
                        {c.lotificacion && (
                          <div className="text-xs text-slate-500">
                            {NOMBRE_LOTIFICACION[c.lotificacion]}
                          </div>
                        )}
                      </td>
                      <td className={`${claseTd} numero text-right`}>{moneda(c.total)}</td>
                      <td className={`${claseTd} numero text-right font-medium`}>
                        {moneda(c.saldo_capital)}
                      </td>
                      <td className={claseTd}>
                        <Insignia tono={TONO_ESTADO[c.estado]}>
                          {ETIQUETA_ESTADO_CONTRATO[c.estado]}
                        </Insignia>
                      </td>
                      <td className={`${claseTd} whitespace-nowrap`}>
                        <div className="flex flex-wrap justify-end gap-1">
                          {c.estado === "vigente" && (
                            <Link
                              to={`/promesas/${c.id}/pago`}
                              className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-primario hover:bg-primario-suave"
                            >
                              <Wallet className="size-4" aria-hidden /> Pago
                            </Link>
                          )}
                          <BotonPdf
                            pequeno
                            variante="fantasma"
                            texto="Promesa"
                            ruta={`/contratos/${c.id}/pdf`}
                            nombre={`promesa_${c.numero_formateado}.pdf`}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion
              pagina={data.pagina}
              tamano={data.tamano}
              total={data.total}
              cambiar={(p) => cambiar("pagina", String(p))}
            />
          </>
        )}
      </Seccion>
    </div>
  );
}
