import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Plus, Save, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useFieldArray, useForm, useWatch, type Path } from "react-hook-form";
import { Link, useParams } from "react-router";

import { ErrorApi } from "../../api/cliente";
import { useContrato, useRegistrarRecibo, useSugerencia } from "../../api/consultas";
import type { Desglose, ReciboLeer, SugerenciaPago } from "../../api/tipos";
import { Alerta, Cargando, Dato, ErrorVista, Seccion } from "../../components/ui/Basicos";
import { Boton } from "../../components/ui/Boton";
import { BotonPdf } from "../../components/ui/BotonPdf";
import { AreaTexto, Entrada, EntradaMonto, Seleccion } from "../../components/ui/Campos";
import { ETIQUETA_CONCEPTO, fecha as fmtFecha, hoyIso, moneda } from "../../lib/formato";
import { useDiferido } from "../../lib/hooks";
import {
  aPayloadRecibo,
  CAMPOS_POR_CONCEPTO,
  esquemaPago,
  ETIQUETAS_DESGLOSE,
  resumenPago,
  valoresPago,
  type FormularioPago,
} from "./esquemas";

const CONCEPTOS = Object.entries(ETIQUETA_CONCEPTO).map(([valor, texto]) => ({ valor, texto }));
const sinCeros = (v: string) => (Number(v) === 0 ? "" : v);

export function RegistrarPago() {
  const { id = "" } = useParams();
  const contrato = useContrato(id);
  const registrar = useRegistrarRecibo();
  const [creado, setCreado] = useState<ReciboLeer | null>(null);
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);

  const {
    register,
    control,
    handleSubmit,
    setValue,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormularioPago>({
    resolver: zodResolver(esquemaPago),
    defaultValues: valoresPago(hoyIso()),
    mode: "onTouched",
  });
  const boletas = useFieldArray({ control, name: "boletas" });
  const valores = useWatch({ control }) as FormularioPago;
  const fechaDiferida = useDiferido(valores.fecha ?? "", 400);
  const sugerencia = useSugerencia(id, fechaDiferida);

  function aplicarSugerencia(s: SugerenciaPago, concepto: FormularioPago["concepto"]) {
    const opciones = { shouldValidate: false, shouldDirty: true };
    if (concepto === "cuota" && s.cuota_numero) {
      setValue("cuota_numero", String(s.cuota_numero), opciones);
      setValue("desglose.capital", sinCeros(s.capital), opciones);
      setValue("desglose.intereses", sinCeros(s.intereses), opciones);
      setValue("desglose.recargo_mora", sinCeros(s.recargo_mora), opciones);
    }
    if (concepto === "enganche")
      setValue("desglose.enganche", sinCeros(s.enganche_pendiente), opciones);
  }

  // Al cambiar la fecha o el concepto se vuelve a proponer cuota, capital, intereses y mora.
  useEffect(() => {
    if (sugerencia.data && valores.concepto) aplicarSugerencia(sugerencia.data, valores.concepto);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sugerencia.data, valores.concepto]);

  async function enviar(v: FormularioPago) {
    setErrorGeneral(null);
    try {
      setCreado(await registrar.mutateAsync(aPayloadRecibo(v, id)));
    } catch (e) {
      if (e instanceof ErrorApi) {
        for (const [ruta, mensaje] of Object.entries(e.campos))
          setError(ruta as Path<FormularioPago>, { message: mensaje });
        setErrorGeneral(e.message);
      } else setErrorGeneral("No se pudo registrar el pago");
    }
  }

  if (contrato.isLoading) return <Cargando filas={8} />;
  if (contrato.error || !contrato.data)
    return <ErrorVista error={contrato.error} reintentar={() => void contrato.refetch()} />;
  const c = contrato.data;

  if (creado) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <Alerta tono="exito" titulo={`Recibo No. ${creado.numero_formateado} registrado`}>
          <p>
            {creado.total_en_letras} ({moneda(creado.total)}) · Saldo actual:{" "}
            {moneda(creado.saldo_actual)}
          </p>
        </Alerta>
        <div className="flex flex-wrap gap-2">
          <BotonPdf
            variante="primario"
            texto="Descargar recibo PDF"
            ruta={`/recibos/${creado.id}/pdf`}
            nombre={`recibo_${creado.numero_formateado}.pdf`}
          />
          <Boton
            variante="secundario"
            onClick={() => {
              setCreado(null);
              reset(valoresPago(hoyIso()));
            }}
          >
            Registrar otro pago
          </Boton>
          <Link
            to={`/promesas/${c.id}`}
            className="inline-flex items-center rounded-md px-4 py-2 text-sm font-medium text-primario hover:bg-primario-suave"
          >
            Ver la promesa
          </Link>
        </div>
      </div>
    );
  }

  const concepto = valores.concepto ?? "cuota";
  const resumen = resumenPago(valores, c.saldo_capital);
  const s = sugerencia.data;
  const ed = errors.desglose;

  return (
    <form onSubmit={handleSubmit(enviar)} noValidate className="space-y-5">
      <Link
        to={`/promesas/${c.id}`}
        className="inline-flex items-center gap-1 text-sm text-primario hover:underline"
      >
        <ArrowLeft className="size-4" aria-hidden /> Volver a la promesa
      </Link>
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Registrar pago · Recibo de Caja</h1>
        <p className="text-sm text-slate-500">
          Promesa No. {c.numero_formateado} · {c.comprador.nombres_apellidos} · Lote {c.lote.codigo}
        </p>
      </div>

      {c.estado !== "vigente" && (
        <Alerta tono="alerta">Esta promesa no está vigente; no admite más pagos.</Alerta>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Seccion titulo="Pago">
            <div className="grid gap-4 sm:grid-cols-3">
              <Entrada
                etiqueta="Fecha del pago"
                type="date"
                obligatorio
                error={errors.fecha?.message}
                {...register("fecha")}
              />
              <Seleccion
                etiqueta="En concepto de"
                obligatorio
                opciones={CONCEPTOS}
                error={errors.concepto?.message}
                {...register("concepto")}
              />
              {concepto === "cuota" && (
                <Entrada
                  etiqueta="Cuota nivelada No."
                  inputMode="numeric"
                  obligatorio
                  error={errors.cuota_numero?.message}
                  {...register("cuota_numero")}
                />
              )}
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              {CAMPOS_POR_CONCEPTO[concepto].map((campo: keyof Desglose) => (
                <EntradaMonto
                  key={campo}
                  etiqueta={`${ETIQUETAS_DESGLOSE[campo]} (Q)`}
                  error={ed?.[campo]?.message}
                  {...register(`desglose.${campo}`)}
                />
              ))}
            </div>
            {ed?.root?.message || ed?.message ? (
              <p role="alert" className="mt-2 text-xs text-peligro">
                {ed?.root?.message ?? ed?.message}
              </p>
            ) : null}
            {s && (
              <Boton
                pequeno
                variante="fantasma"
                className="mt-3"
                icono={<Sparkles className="size-4" aria-hidden />}
                onClick={() => aplicarSugerencia(s, concepto)}
              >
                Volver a aplicar la sugerencia
              </Boton>
            )}
          </Seccion>

          <Seccion
            titulo="Boletas de depósito y factura"
            acciones={
              <Boton
                pequeno
                variante="secundario"
                icono={<Plus className="size-4" aria-hidden />}
                disabled={boletas.fields.length >= 5}
                onClick={() => boletas.append({ numero: "", cuenta: "" })}
              >
                Agregar boleta
              </Boton>
            }
          >
            <div className="space-y-3">
              {boletas.fields.length === 0 && (
                <p className="text-sm text-slate-500">Sin boletas (pago en efectivo).</p>
              )}
              {boletas.fields.map((campo, i) => (
                <div key={campo.id} className="grid items-start gap-3 sm:grid-cols-[1fr_1fr_auto]">
                  <Entrada
                    etiqueta={`Boleta ${i + 1} — número`}
                    error={errors.boletas?.[i]?.numero?.message}
                    {...register(`boletas.${i}.numero`)}
                  />
                  <Entrada
                    etiqueta="Cuenta"
                    error={errors.boletas?.[i]?.cuenta?.message}
                    {...register(`boletas.${i}.cuenta`)}
                  />
                  <Boton
                    variante="fantasma"
                    className="sm:mt-6"
                    aria-label={`Quitar boleta ${i + 1}`}
                    onClick={() => boletas.remove(i)}
                    icono={<Trash2 className="size-4" aria-hidden />}
                  />
                </div>
              ))}
              <div className="grid gap-4 sm:grid-cols-3">
                <Entrada
                  etiqueta="No. de factura FEL (opcional)"
                  error={errors.numero_fel?.message}
                  {...register("numero_fel")}
                />
                <AreaTexto
                  etiqueta="Observaciones"
                  className="sm:col-span-2"
                  error={errors.observaciones?.message}
                  {...register("observaciones")}
                />
              </div>
            </div>
          </Seccion>
        </div>

        <div className="space-y-5 lg:sticky lg:top-4 lg:self-start">
          <Seccion titulo="Sugerencia del sistema">
            {sugerencia.isLoading && <Cargando filas={3} />}
            {sugerencia.error && <Alerta tono="alerta">{sugerencia.error.message}</Alerta>}
            {s && (
              <dl className="grid grid-cols-2 gap-3">
                <Dato etiqueta="Siguiente cuota">
                  {s.cuota_numero ? `No. ${s.cuota_numero} (${s.cuota_mes})` : "Ninguna"}
                </Dato>
                <Dato etiqueta="Vencimiento">{fmtFecha(s.vencimiento)}</Dato>
                <Dato etiqueta="Días de atraso">{s.dias_atraso}</Dato>
                <Dato etiqueta="Mora sugerida">{moneda(s.recargo_mora)}</Dato>
                <Dato etiqueta="Cuotas vencidas">{s.cuotas_vencidas}</Dato>
                <Dato etiqueta="Enganche pendiente">{moneda(s.enganche_pendiente)}</Dato>
              </dl>
            )}
          </Seccion>
          <Seccion titulo="Resumen del recibo">
            <dl className="space-y-2">
              <Dato etiqueta="Total del recibo">
                <span className="text-xl font-semibold">{moneda(resumen.total)}</span>
              </Dato>
              <Dato etiqueta="Saldo anterior">{moneda(c.saldo_capital)}</Dato>
              <Dato etiqueta="(-) Este pago a capital">{moneda(resumen.aCapital)}</Dato>
              <Dato etiqueta="Saldo actual">
                <span
                  className={resumen.excedeSaldo ? "font-semibold text-peligro" : "font-semibold"}
                >
                  {moneda(resumen.saldoResultante)}
                </span>
              </Dato>
            </dl>
            {resumen.excedeSaldo && (
              <Alerta tono="peligro">El pago a capital excede el saldo.</Alerta>
            )}
          </Seccion>
          {errorGeneral && <Alerta tono="peligro">{errorGeneral}</Alerta>}
          <Boton
            type="submit"
            className="w-full"
            cargando={isSubmitting}
            disabled={c.estado !== "vigente"}
            icono={<Save className="size-4" aria-hidden />}
          >
            Registrar recibo
          </Boton>
        </div>
      </div>
    </form>
  );
}
