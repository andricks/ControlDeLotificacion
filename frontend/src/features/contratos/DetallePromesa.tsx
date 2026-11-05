import { ArrowLeft, Trash2, Wallet } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";

import { useContrato, useEliminarContrato, useRecibos } from "../../api/consultas";
import {
  Alerta,
  Cargando,
  Dato,
  ErrorVista,
  Insignia,
  Seccion,
  Vacio,
} from "../../components/ui/Basicos";
import { Boton } from "../../components/ui/Boton";
import { BotonPdf } from "../../components/ui/BotonPdf";
import {
  ETIQUETA_ESTADO_CONTRATO,
  fecha,
  moneda,
  NOMBRE_LOTIFICACION,
  TONO_ESTADO,
} from "../../lib/formato";
import { TablaRecibos } from "../recibos/TablaRecibos";
import { DialogoEliminar } from "./DialogoEliminar";
import { TablaPlan } from "./TablaPlan";

export function DetallePromesa() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const navegar = useNavigate();
  const { data: c, isLoading, error, refetch } = useContrato(id);
  const recibos = useRecibos({ contrato_id: id, pagina: 1, tamano: 100 });
  const eliminar = useEliminarContrato();
  const [borrando, setBorrando] = useState(false);

  if (isLoading) return <Cargando filas={8} />;
  if (error || !c) return <ErrorVista error={error} reintentar={() => void refetch()} />;

  const cond = c.condiciones;
  const pagadas = c.plan_cuotas.filter((q) => q.estado === "pagada").length;

  return (
    <div className="space-y-5">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-primario hover:underline">
        <ArrowLeft className="size-4" aria-hidden /> Volver al listado
      </Link>

      {params.get("creada") && (
        <Alerta tono="exito" titulo={`Promesa No. ${c.numero_formateado} guardada`}>
          Ya puede descargar el PDF para imprimir y firmar.
        </Alerta>
      )}

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Promesa No. {c.numero_formateado}{" "}
            <Insignia tono={TONO_ESTADO[c.estado]}>{ETIQUETA_ESTADO_CONTRATO[c.estado]}</Insignia>
          </h1>
          <p className="text-sm text-slate-500">
            {c.comprador.nombres_apellidos} ·{" "}
            {c.lotificacion && `Lotificación ${NOMBRE_LOTIFICACION[c.lotificacion]} · `}Lote{" "}
            {c.lote.codigo} · Firmada el{" "}
            {fecha(c.fecha_firma)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {c.estado === "vigente" && (
            <Link
              to={`/promesas/${c.id}/pago`}
              className="inline-flex items-center gap-2 rounded-md bg-primario px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primario-hover"
            >
              <Wallet className="size-4" aria-hidden /> Registrar pago
            </Link>
          )}
          <BotonPdf
            texto="Promesa PDF"
            ruta={`/contratos/${c.id}/pdf`}
            nombre={`promesa_${c.numero_formateado}.pdf`}
          />
          <BotonPdf
            texto="Estado de cuenta"
            ruta={`/contratos/${c.id}/estado-cuenta/pdf`}
            nombre={`estado_cuenta_${c.numero_formateado}.pdf`}
          />
          <Boton
            variante="secundario"
            icono={<Trash2 className="size-4 text-peligro" aria-hidden />}
            onClick={() => {
              eliminar.reset();
              setBorrando(true);
            }}
          >
            Borrar promesa
          </Boton>
        </div>
      </div>

      <DialogoEliminar
        abierto={borrando}
        titulo={`Borrar promesa No. ${c.numero_formateado}`}
        cargando={eliminar.isPending}
        error={eliminar.error}
        alCerrar={() => setBorrando(false)}
        alConfirmar={async (motivo) => {
          await eliminar.mutateAsync({ id: c.id, motivo });
          void navegar("/", { replace: true });
        }}
      >
        <p>
          La promesa de <strong>{c.comprador.nombres_apellidos}</strong> (lote {c.lote.codigo})
          dejará de aparecer en el sistema
          {recibos.data && recibos.data.total > 0
            ? `, junto con sus ${recibos.data.total} recibo(s)`
            : ""}
          . El lote {c.lote.codigo} quedará disponible para otra venta.
        </p>
        <p className="mt-2">Queda registro del borrado en la auditoría.</p>
      </DialogoEliminar>

      <Seccion titulo="Resumen">
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Dato etiqueta="Total del inmueble">{moneda(cond.total)}</Dato>
          <Dato etiqueta="Enganche (pagado / pactado)">
            {moneda(c.total_pagado_enganche)} / {moneda(cond.enganche)}
          </Dato>
          <Dato etiqueta="Saldo financiado">{moneda(cond.saldo_a_pagar)}</Dato>
          <Dato etiqueta="Saldo actual">
            <span className="text-lg font-semibold">{moneda(c.saldo_capital)}</span>
          </Dato>
          <Dato etiqueta="Cuota nivelada">{moneda(cond.cuota_nivelada)}</Dato>
          <Dato etiqueta="Cuotas pagadas">
            {pagadas} de {c.plan_cuotas.length}
          </Dato>
          <Dato etiqueta="Tasa anual">{cond.tasa_interes_anual_pct} %</Dato>
          <Dato etiqueta="DPI comprador">{c.comprador.dpi}</Dato>
        </dl>
        {c.saldo_inicial && (
          <p className="mt-3 text-xs text-slate-500">
            Cargado desde papel: saldo {moneda(c.saldo_inicial.saldo_capital)} al{" "}
            {fecha(c.saldo_inicial.fecha_corte)}, {c.saldo_inicial.cuotas_pagadas} cuotas pagadas.
          </p>
        )}
      </Seccion>

      <Seccion titulo="Recibos de caja">
        {recibos.isLoading && <Cargando />}
        {recibos.error && (
          <ErrorVista error={recibos.error} reintentar={() => void recibos.refetch()} />
        )}
        {recibos.data && recibos.data.items.length === 0 && (
          <Vacio mensaje="Aún no hay recibos para esta promesa." />
        )}
        {recibos.data && recibos.data.items.length > 0 && (
          <TablaRecibos recibos={recibos.data.items} permitirAnular />
        )}
      </Seccion>

      <Seccion titulo="Plan de cuotas">
        {c.plan_cuotas.length > 0 ? (
          <TablaPlan cuotas={c.plan_cuotas} conEstado />
        ) : (
          <Vacio mensaje="Sin saldo financiado." />
        )}
      </Seccion>
    </div>
  );
}
