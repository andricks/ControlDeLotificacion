import { Ban, Trash2 } from "lucide-react";
import { useState } from "react";

import { useAnularRecibo, useEliminarRecibo } from "../../api/consultas";
import type { ReciboLeer } from "../../api/tipos";
import { Alerta, Insignia } from "../../components/ui/Basicos";
import { Boton } from "../../components/ui/Boton";
import { BotonPdf } from "../../components/ui/BotonPdf";
import { AreaTexto } from "../../components/ui/Campos";
import { Dialogo } from "../../components/ui/Dialogo";
import { claseTabla, claseTd, claseTh } from "../../lib/estilos";
import { ETIQUETA_CONCEPTO, fecha, moneda } from "../../lib/formato";
import { DialogoEliminar } from "../contratos/DialogoEliminar";

/** Tabla de recibos. Con `permitirAnular`, el último recibo vigente muestra "Anular" y
 * "Borrar"; los anulados muestran "Borrar". */
export function TablaRecibos({
  recibos,
  permitirAnular = false,
  mostrarCliente = false,
}: {
  recibos: ReciboLeer[];
  permitirAnular?: boolean;
  mostrarCliente?: boolean;
}) {
  const [porAnular, setPorAnular] = useState<ReciboLeer | null>(null);
  const [motivo, setMotivo] = useState("");
  const anular = useAnularRecibo();
  const [porBorrar, setPorBorrar] = useState<ReciboLeer | null>(null);
  const eliminar = useEliminarRecibo();
  const ultimoVigente = recibos.filter((r) => !r.anulado).sort((a, b) => b.numero - a.numero)[0];

  async function confirmar() {
    if (!porAnular) return;
    try {
      await anular.mutateAsync({ id: porAnular.id, motivo });
      setPorAnular(null);
      setMotivo("");
    } catch {
      // el error se muestra en el diálogo
    }
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className={claseTabla}>
          <thead className="bg-slate-50">
            <tr>
              <th className={claseTh}>No.</th>
              <th className={claseTh}>Fecha</th>
              {mostrarCliente && <th className={claseTh}>Cliente / Lote</th>}
              <th className={claseTh}>Concepto</th>
              <th className={`${claseTh} text-right`}>Total</th>
              <th className={`${claseTh} text-right`}>Saldo después</th>
              <th className={claseTh}>
                <span className="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {recibos.map((r) => (
              <tr key={r.id} className={r.anulado ? "bg-slate-50 text-slate-400" : ""}>
                <td className={claseTd}>
                  <span className={r.anulado ? "line-through" : "font-medium"}>
                    {r.numero_formateado}
                  </span>
                  {r.numero_fel && <div className="text-xs text-slate-500">FEL {r.numero_fel}</div>}
                </td>
                <td className={claseTd}>{fecha(r.fecha)}</td>
                {mostrarCliente && (
                  <td className={claseTd}>
                    <div>{r.cliente_nombre}</div>
                    <div className="text-xs text-slate-500">
                      Lote {r.lotes_texto} · Promesa {String(r.contrato_numero).padStart(5, "0")}
                    </div>
                  </td>
                )}
                <td className={claseTd}>
                  {ETIQUETA_CONCEPTO[r.concepto]}
                  {r.cuota_numero && (
                    <span className="text-slate-500">
                      {" "}
                      No. {r.cuota_numero} ({r.cuota_mes})
                    </span>
                  )}
                  {r.anulado && (
                    <div>
                      <Insignia tono="peligro">Anulado</Insignia>{" "}
                      <span className="text-xs">{r.motivo_anulacion}</span>
                    </div>
                  )}
                </td>
                <td className={`${claseTd} numero text-right`}>{moneda(r.total)}</td>
                <td className={`${claseTd} numero text-right`}>{moneda(r.saldo_actual)}</td>
                <td className={`${claseTd} whitespace-nowrap`}>
                  <div className="flex justify-end gap-1">
                    <BotonPdf
                      pequeno
                      variante="fantasma"
                      texto="PDF"
                      ruta={`/recibos/${r.id}/pdf`}
                      nombre={`recibo_${r.numero_formateado}.pdf`}
                    />
                    {permitirAnular && ultimoVigente?.id === r.id && (
                      <Boton
                        pequeno
                        variante="fantasma"
                        icono={<Ban className="size-4" aria-hidden />}
                        onClick={() => {
                          anular.reset();
                          setPorAnular(r);
                        }}
                      >
                        Anular
                      </Boton>
                    )}
                    {permitirAnular && (r.anulado || ultimoVigente?.id === r.id) && (
                      <Boton
                        pequeno
                        variante="fantasma"
                        className="text-peligro"
                        icono={<Trash2 className="size-4" aria-hidden />}
                        onClick={() => {
                          eliminar.reset();
                          setPorBorrar(r);
                        }}
                      >
                        Borrar
                      </Boton>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialogo
        abierto={porAnular !== null}
        titulo={`Anular recibo No. ${porAnular?.numero_formateado ?? ""}`}
        alCerrar={() => setPorAnular(null)}
      >
        <div className="space-y-3">
          <p className="text-sm text-slate-600">
            Se revertirá el saldo y el plan de cuotas al estado anterior a este recibo. El recibo no
            se borra: queda marcado como anulado.
          </p>
          <AreaTexto
            etiqueta="Motivo de la anulación"
            obligatorio
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            error={
              motivo.length > 0 && motivo.trim().length < 5
                ? "Escriba al menos 5 caracteres"
                : undefined
            }
          />
          {anular.error && <Alerta tono="peligro">{anular.error.message}</Alerta>}
          <div className="flex justify-end gap-2">
            <Boton variante="secundario" onClick={() => setPorAnular(null)}>
              Cancelar
            </Boton>
            <Boton
              variante="peligro"
              cargando={anular.isPending}
              disabled={motivo.trim().length < 5}
              onClick={() => void confirmar()}
            >
              Anular recibo
            </Boton>
          </div>
        </div>
      </Dialogo>

      <DialogoEliminar
        abierto={porBorrar !== null}
        titulo={`Borrar recibo No. ${porBorrar?.numero_formateado ?? ""}`}
        cargando={eliminar.isPending}
        error={eliminar.error}
        alCerrar={() => setPorBorrar(null)}
        alConfirmar={async (motivo) => {
          if (!porBorrar) return;
          await eliminar.mutateAsync({ id: porBorrar.id, motivo });
          setPorBorrar(null);
        }}
      >
        {porBorrar?.anulado ? (
          <p>El recibo ya está anulado: se quitará del sistema sin cambiar saldos.</p>
        ) : (
          <p>
            Se revertirá el saldo y el plan de cuotas al estado anterior a este recibo y el recibo
            dejará de aparecer en el sistema.
          </p>
        )}
        <p className="mt-2">Queda registro del borrado en la auditoría.</p>
      </DialogoEliminar>
    </>
  );
}
