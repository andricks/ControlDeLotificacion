import { Calculator } from "lucide-react";

import { useCalculo } from "../../api/consultas";
import type { CondicionesEntrada } from "../../api/tipos";
import { Alerta, Cargando, Dato } from "../../components/ui/Basicos";
import { moneda } from "../../lib/formato";
import { TablaPlan } from "./TablaPlan";

/** Totales y plan de cuotas calculados por el servidor mientras se llena el formulario. */
export function VistaPrevia({ condiciones }: { condiciones: CondicionesEntrada | null }) {
  const { data, error, isFetching } = useCalculo(condiciones);

  return (
    <div className="space-y-3" aria-live="polite">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <Calculator className="size-4" aria-hidden /> Vista previa del financiamiento
      </h3>
      {!condiciones && (
        <p className="text-sm text-slate-500">
          Complete precio, enganche, plazo y fecha de la primera cuota para ver el plan de pagos.
        </p>
      )}
      {condiciones && error && <Alerta tono="alerta">{error.message}</Alerta>}
      {condiciones && !data && !error && <Cargando filas={3} />}
      {data && !error && (
        <div className={isFetching ? "opacity-60 transition-opacity" : ""}>
          <dl className="mb-3 grid grid-cols-2 gap-3 rounded-md bg-primario-suave p-3">
            <Dato etiqueta="Total">{moneda(data.condiciones.total)}</Dato>
            <Dato etiqueta="Saldo a pagar">{moneda(data.condiciones.saldo_a_pagar)}</Dato>
            <Dato etiqueta="Cuota nivelada">
              <span className="font-semibold">{moneda(data.condiciones.cuota_nivelada)}</span>
            </Dato>
            <Dato etiqueta="Número de cuotas">{data.condiciones.numero_cuotas}</Dato>
          </dl>
          {data.plan_cuotas.length > 0 ? (
            <TablaPlan cuotas={data.plan_cuotas} />
          ) : (
            <p className="text-sm text-slate-500">Sin saldo financiado (compra al contado).</p>
          )}
        </div>
      )}
    </div>
  );
}
