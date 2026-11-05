import type { CuotaPlan } from "../../api/tipos";
import { Insignia } from "../../components/ui/Basicos";
import { claseTabla, claseTd, claseTh } from "../../lib/estilos";
import { fecha, moneda } from "../../lib/formato";

const TONO = { pagada: "exito", parcial: "alerta", pendiente: "neutro" } as const;
const TEXTO = { pagada: "Pagada", parcial: "Parcial", pendiente: "Pendiente" } as const;

export function TablaPlan({
  cuotas,
  conEstado = false,
}: {
  cuotas: CuotaPlan[];
  conEstado?: boolean;
}) {
  return (
    <div className="max-h-96 overflow-auto rounded-md border border-slate-200">
      <table className={claseTabla}>
        <thead className="sticky top-0 bg-slate-50">
          <tr>
            <th className={claseTh}>No.</th>
            <th className={claseTh}>Vencimiento</th>
            <th className={`${claseTh} text-right`}>Capital</th>
            <th className={`${claseTh} text-right`}>Interés</th>
            <th className={`${claseTh} text-right`}>Cuota</th>
            <th className={`${claseTh} text-right`}>Saldo</th>
            {conEstado && <th className={claseTh}>Estado</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {cuotas.map((q) => (
            <tr key={q.numero}>
              <td className={claseTd}>{q.numero}</td>
              <td className={claseTd}>{fecha(q.vencimiento)}</td>
              <td className={`${claseTd} numero text-right`}>{moneda(q.capital)}</td>
              <td className={`${claseTd} numero text-right`}>{moneda(q.interes)}</td>
              <td className={`${claseTd} numero text-right font-medium`}>{moneda(q.cuota)}</td>
              <td className={`${claseTd} numero text-right`}>{moneda(q.saldo_despues)}</td>
              {conEstado && (
                <td className={claseTd}>
                  <Insignia tono={TONO[q.estado]}>{TEXTO[q.estado]}</Insignia>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
