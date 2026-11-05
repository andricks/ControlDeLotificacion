import { Phone, Search, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { useCartera } from "../../api/consultas";
import type { ClienteCartera, ResumenCartera, SituacionPago } from "../../api/tipos";
import { Cargando, ErrorVista, Insignia, Seccion, Vacio } from "../../components/ui/Basicos";
import { BotonPdf } from "../../components/ui/BotonPdf";
import { Seleccion } from "../../components/ui/Campos";
import { Paginacion } from "../../components/ui/Paginacion";
import { claseInput, claseTabla, claseTd, claseTh } from "../../lib/estilos";
import { fecha, moneda, NOMBRE_LOTIFICACION } from "../../lib/formato";
import { useDiferido } from "../../lib/hooks";

const SITUACION: Record<
  SituacionPago,
  { texto: string; tono: "peligro" | "alerta" | "info" | "exito" }
> = {
  moroso: { texto: "Moroso", tono: "peligro" },
  en_gracia: { texto: "En gracia", tono: "alerta" },
  por_vencer: { texto: "Por vencer", tono: "info" },
  al_dia: { texto: "Al día", tono: "exito" },
};

const FILTROS: { valor: SituacionPago | ""; texto: string; clave: keyof ResumenCartera }[] = [
  { valor: "moroso", texto: "Morosos", clave: "morosos" },
  { valor: "en_gracia", texto: "En gracia", clave: "en_gracia" },
  { valor: "por_vencer", texto: "Pagan esta semana", clave: "por_vencer" },
  { valor: "al_dia", texto: "Al día", clave: "al_dia" },
  { valor: "", texto: "Todos", clave: "clientes" },
];

const LOTIFICACIONES = [
  { valor: "", texto: "Todas" },
  ...Object.entries(NOMBRE_LOTIFICACION).map(([valor, texto]) => ({ valor, texto })),
];

function plural(n: number, uno: string, varios: string) {
  return `${n} ${n === 1 ? uno : varios}`;
}

function Atraso({ c }: { c: ClienteCartera }) {
  if (c.situacion === "moroso")
    return (
      <>
        <div className="font-medium text-peligro">
          {plural(c.cuotas_vencidas, "cuota vencida", "cuotas vencidas")}
        </div>
        <div className="text-xs text-slate-500">
          {plural(c.dias_atraso, "día", "días")} de atraso
        </div>
        {c.riesgo_rescision && (
          <div className="mt-1">
            <Insignia tono="peligro">Riesgo de rescisión</Insignia>
          </div>
        )}
      </>
    );
  if (c.situacion === "en_gracia")
    return <span className="text-alerta">{plural(c.dias_atraso, "día", "días")} (en gracia)</span>;
  return <span className="text-slate-400">—</span>;
}

export function Cartera() {
  const [params, setParams] = useSearchParams();
  const [texto, setTexto] = useState(params.get("buscar") ?? "");
  const buscar = useDiferido(texto, 350);
  const situacion = params.get("situacion") ?? "moroso";
  const lotificacion = params.get("lotificacion") ?? "";
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
      p.set(clave, valor);
      if (clave !== "situacion" && !valor) p.delete(clave);
      if (clave !== "pagina") p.delete("pagina");
      return p;
    });

  const { data, isLoading, error, refetch } = useCartera({
    situacion: situacion || undefined,
    buscar,
    lotificacion,
    pagina,
  });
  const resumen = data?.resumen;
  const filtrosPdf = new URLSearchParams(
    Object.entries({ situacion, buscar, lotificacion }).filter(([, v]) => v),
  ).toString();

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Cobros y morosidad</h1>
          <p className="text-sm text-slate-500">
            {data
              ? `Situación al ${fecha(data.fecha)} · ${plural(data.dias_gracia, "día", "días")} de gracia después de cada vencimiento.`
              : "Quién debe, a quién le toca pagar y cuándo."}
          </p>
        </div>
        <BotonPdf
          variante="primario"
          texto="Descargar reporte PDF"
          ruta={`/cartera/pdf${filtrosPdf ? `?${filtrosPdf}` : ""}`}
          nombre={`cobros_${situacion || "todos"}.pdf`}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-peligro/30 bg-peligro-suave p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-peligro">
            Clientes morosos
          </p>
          <p className="numero mt-1 text-2xl font-semibold text-slate-900">
            {resumen ? resumen.morosos : "—"}
            {resumen && (
              <span className="text-sm font-normal text-slate-500"> de {resumen.clientes}</span>
            )}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Monto vencido
          </p>
          <p className="numero mt-1 text-2xl font-semibold text-slate-900">
            {moneda(resumen?.monto_vencido)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Mora estimada
          </p>
          <p className="numero mt-1 text-2xl font-semibold text-slate-900">
            {moneda(resumen?.mora_estimada)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Riesgo de rescisión
          </p>
          <p className="numero mt-1 text-2xl font-semibold text-slate-900">
            {resumen ? resumen.riesgo_rescision : "—"}
          </p>
          <p className="text-xs text-slate-500">2 o más cuotas en mora</p>
        </div>
      </div>

      <Seccion titulo="Clientes">
        <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label="Filtrar por situación">
          {FILTROS.map((f) => {
            const activo = situacion === f.valor;
            return (
              <button
                key={f.clave}
                type="button"
                aria-pressed={activo}
                onClick={() => cambiar("situacion", f.valor)}
                className={`rounded-full border px-3 py-1 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-primario/40 ${
                  activo
                    ? "border-primario bg-primario text-white"
                    : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                {f.texto}
                {resumen && <span className="numero ml-1.5 opacity-80">{resumen[f.clave]}</span>}
              </button>
            );
          })}
        </div>
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
              placeholder="Buscar por nombre o lote…"
              className={`${claseInput(false)} pl-9`}
            />
          </label>
          <Seleccion
            etiqueta="Lotificación"
            opciones={LOTIFICACIONES}
            value={lotificacion}
            onChange={(e) => cambiar("lotificacion", e.target.value)}
          />
        </div>

        {isLoading && <Cargando />}
        {error && <ErrorVista error={error} reintentar={() => void refetch()} />}
        {data && data.items.length === 0 && (
          <Vacio
            mensaje={
              situacion === "moroso" && !buscar && !lotificacion
                ? "No hay clientes morosos."
                : "No hay clientes en esta situación."
            }
          />
        )}
        {data && data.items.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <table className={claseTabla}>
                <thead className="bg-slate-50">
                  <tr>
                    <th className={claseTh}>Cliente</th>
                    <th className={claseTh}>Lote</th>
                    <th className={claseTh}>Paga</th>
                    <th className={claseTh}>Próxima cuota</th>
                    <th className={claseTh}>Atraso</th>
                    <th className={`${claseTh} text-right`}>Vencido</th>
                    <th className={`${claseTh} text-right`}>Mora est.</th>
                    <th className={claseTh}>Último pago</th>
                    <th className={claseTh}>
                      <span className="sr-only">Acciones</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.items.map((c) => (
                    <tr key={c.contrato_id} className="hover:bg-slate-50">
                      <td className={claseTd}>
                        <Link
                          to={`/promesas/${c.contrato_id}`}
                          className="font-medium text-primario hover:underline"
                        >
                          {c.cliente_nombre}
                        </Link>
                        <div className="text-xs text-slate-500">Promesa {c.numero_formateado}</div>
                        {c.telefono && (
                          <a
                            href={`tel:${c.telefono.replace(/[^\d+]/g, "")}`}
                            className="inline-flex items-center gap-1 text-xs text-slate-600 hover:underline"
                          >
                            <Phone className="size-3" aria-hidden /> {c.telefono}
                          </a>
                        )}
                      </td>
                      <td className={claseTd}>
                        <div>{c.lote_codigo}</div>
                        {c.lotificacion && (
                          <div className="text-xs text-slate-500">
                            {NOMBRE_LOTIFICACION[c.lotificacion]}
                          </div>
                        )}
                      </td>
                      <td className={claseTd}>
                        <div className="whitespace-nowrap">Cada mes, día {c.dia_pago_mensual}</div>
                        <div className="numero text-xs text-slate-500">
                          {moneda(c.cuota_nivelada)}
                        </div>
                      </td>
                      <td className={claseTd}>
                        {c.proxima_cuota_numero ? (
                          <>
                            <div className="whitespace-nowrap">
                              {fecha(c.proxima_vencimiento)}{" "}
                              <Insignia tono={SITUACION[c.situacion].tono}>
                                {SITUACION[c.situacion].texto}
                              </Insignia>
                            </div>
                            <div className="text-xs text-slate-500">
                              Cuota {c.proxima_cuota_numero} de {c.numero_cuotas} ·{" "}
                              <span className="numero">{moneda(c.proxima_monto)}</span>
                            </div>
                          </>
                        ) : (
                          <span className="text-slate-400">Sin cuotas pendientes</span>
                        )}
                        {Number(c.enganche_pendiente) > 0 && (
                          <div className="text-xs text-alerta">
                            Enganche pendiente {moneda(c.enganche_pendiente)}
                          </div>
                        )}
                      </td>
                      <td className={claseTd}>
                        <Atraso c={c} />
                      </td>
                      <td className={`${claseTd} numero text-right font-medium`}>
                        {Number(c.monto_vencido) > 0 ? moneda(c.monto_vencido) : "—"}
                      </td>
                      <td className={`${claseTd} numero text-right`}>
                        {Number(c.mora_estimada) > 0 ? moneda(c.mora_estimada) : "—"}
                      </td>
                      <td className={`${claseTd} whitespace-nowrap`}>
                        {c.ultimo_pago ? (
                          fecha(c.ultimo_pago)
                        ) : (
                          <span className="text-slate-400">Ninguno</span>
                        )}
                      </td>
                      <td className={`${claseTd} whitespace-nowrap`}>
                        <Link
                          to={`/promesas/${c.contrato_id}/pago`}
                          className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-primario hover:bg-primario-suave"
                        >
                          <Wallet className="size-4" aria-hidden /> Registrar pago
                        </Link>
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
