import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Save, Trash2, UserCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { useFieldArray, useForm, useWatch, type Path } from "react-hook-form";
import { useNavigate } from "react-router";

import { ErrorApi } from "../../api/cliente";
import { buscarClientePorDpi, useCrearContrato } from "../../api/consultas";
import type { ClienteLeer } from "../../api/tipos";
import { Alerta, Seccion } from "../../components/ui/Basicos";
import { Boton } from "../../components/ui/Boton";
import { AreaTexto, Casilla, Entrada, EntradaMonto, Seleccion } from "../../components/ui/Campos";
import { hoyIso, NOMBRE_LOTIFICACION } from "../../lib/formato";
import { useDiferido } from "../../lib/hooks";
import { dpiValido, normalizarDpi } from "../../lib/validaciones";
import {
  aCondiciones,
  aPayload,
  esquemaCondicionesPrevia,
  esquemaPromesa,
  valoresIniciales,
  type FormularioPromesa,
} from "./esquemas";
import { VistaPrevia } from "./VistaPrevia";

const ESTADOS_CIVILES = [
  "",
  "Soltero(a)",
  "Casado(a)",
  "Unido(a)",
  "Divorciado(a)",
  "Viudo(a)",
].map((v) => ({
  valor: v,
  texto: v || "— Seleccione —",
}));
const LOTIFICACIONES = [
  { valor: "", texto: "— Seleccione —" },
  ...Object.entries(NOMBRE_LOTIFICACION).map(([valor, texto]) => ({ valor, texto })),
];
const PLAZOS = ["1", "2", "3", "4"].map((v) => ({
  valor: v,
  texto: `${v} año${v === "1" ? "" : "s"}`,
}));

const s = (v: string | number | null | undefined) =>
  v === null || v === undefined ? "" : String(v);

export function NuevaPromesa() {
  const navigate = useNavigate();
  const crear = useCrearContrato();
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [existente, setExistente] = useState<ClienteLeer | null>(null);

  const {
    register,
    control,
    handleSubmit,
    setValue,
    setError,
    formState: { errors, isSubmitting, submitCount },
  } = useForm<FormularioPromesa>({
    resolver: zodResolver(esquemaPromesa),
    defaultValues: valoresIniciales(hoyIso()),
    mode: "onTouched",
  });

  const dependientes = useFieldArray({ control, name: "dependientes" });
  const enganches = useFieldArray({ control, name: "condiciones.enganche_fraccionado" });
  const tieneConyuge = useWatch({ control, name: "tiene_conyuge" });
  const vieneDePapel = useWatch({ control, name: "viene_de_papel" });
  const condiciones = useWatch({ control, name: "condiciones" });

  const clave = useDiferido(JSON.stringify(condiciones), 500);
  const condicionesPrevia = useMemo(() => {
    const c = JSON.parse(clave) as FormularioPromesa["condiciones"];
    return esquemaCondicionesPrevia.safeParse(c).success
      ? aCondiciones({ ...c, enganche_fraccionado: [] })
      : null;
  }, [clave]);

  async function revisarDpi(valor: string) {
    setExistente(null);
    if (!dpiValido(valor)) return;
    try {
      setExistente(await buscarClientePorDpi(normalizarDpi(valor)));
    } catch {
      // 404: cliente nuevo
    }
  }

  function usarDatosExistentes(c: ClienteLeer) {
    const t = c.trabajo ?? {};
    setValue(
      "comprador",
      {
        nombres_apellidos: c.nombres_apellidos,
        dpi: c.dpi,
        nit: s(c.nit),
        direccion: s(c.direccion),
        telefono: s(c.telefono),
        email: s(c.email),
        fecha_nacimiento: s(c.fecha_nacimiento),
        nacionalidad: s(c.nacionalidad) || "Guatemalteca",
        estado_civil: s(c.estado_civil),
        num_dependientes: s(c.num_dependientes),
        profesion_actividad: s(c.profesion_actividad),
        trabajo: {
          empresa: s(t.empresa),
          direccion: s(t.direccion),
          telefono: s(t.telefono),
          puesto: s(t.puesto),
          tiempo_trabajo: s(t.tiempo_trabajo),
          ingreso_mensual: s(t.ingreso_mensual),
          otros_ingresos: s(t.otros_ingresos),
        },
      },
      { shouldValidate: true, shouldDirty: true },
    );
    setExistente(null);
  }

  async function enviar(valores: FormularioPromesa) {
    setErrorGeneral(null);
    try {
      const contrato = await crear.mutateAsync(aPayload(valores));
      navigate(`/promesas/${contrato.id}?creada=1`);
    } catch (e) {
      if (e instanceof ErrorApi) {
        for (const [ruta, mensaje] of Object.entries(e.campos)) {
          setError(ruta as Path<FormularioPromesa>, { message: mensaje });
        }
        setErrorGeneral(e.message);
      } else {
        setErrorGeneral("No se pudo guardar la promesa");
      }
    }
  }

  const ec = errors.comprador;
  const et = errors.comprador?.trabajo;
  const ey = errors.conyuge_gestor;
  const el = errors.lote;
  const ed = errors.condiciones;
  const es = errors.saldo_inicial;

  return (
    <form onSubmit={handleSubmit(enviar)} noValidate className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Nueva Promesa de Compra Venta</h1>
          <p className="text-sm text-slate-500">
            Los campos con <span className="text-peligro">*</span> son obligatorios. Los totales y
            el plan de pagos los calcula el sistema.
          </p>
        </div>
      </div>

      <Seccion
        titulo="Lotificación y firma"
        descripcion="El nombre de la lotificación aparece en la promesa, los recibos y el estado de cuenta."
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Seleccion
            etiqueta="Lotificación"
            obligatorio
            opciones={LOTIFICACIONES}
            error={errors.lotificacion?.message}
            {...register("lotificacion")}
          />
          <Entrada
            etiqueta="Fecha de firma"
            type="date"
            obligatorio
            error={errors.fecha_firma?.message}
            {...register("fecha_firma")}
          />
          <div className="sm:col-span-2">
            <Casilla
              etiqueta="Cliente que ya venía pagando en papel (registrar solo su saldo actual)"
              {...register("viene_de_papel")}
            />
          </div>
        </div>
      </Seccion>

      <Seccion
        titulo="Datos del comprador"
        descripcion="Escriba primero el DPI: si el cliente ya existe podrá cargar sus datos."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Entrada
            etiqueta="DPI"
            obligatorio
            inputMode="numeric"
            placeholder="13 dígitos"
            error={ec?.dpi?.message}
            {...register("comprador.dpi", { onBlur: (e) => void revisarDpi(e.target.value) })}
          />
          <Entrada
            etiqueta="Nombres y apellidos"
            obligatorio
            className="lg:col-span-2"
            error={ec?.nombres_apellidos?.message}
            {...register("comprador.nombres_apellidos")}
          />
          {existente && (
            <div className="sm:col-span-2 lg:col-span-3">
              <Alerta tono="info" titulo="Este cliente ya está registrado">
                <p>{existente.nombres_apellidos}</p>
                <Boton
                  pequeno
                  variante="secundario"
                  className="mt-2"
                  icono={<UserCheck className="size-4" aria-hidden />}
                  onClick={() => usarDatosExistentes(existente)}
                >
                  Usar sus datos guardados
                </Boton>
              </Alerta>
            </div>
          )}
          <Entrada
            etiqueta="NIT"
            placeholder="1234567-9 o CF"
            error={ec?.nit?.message}
            {...register("comprador.nit")}
          />
          <Entrada
            etiqueta="Teléfono"
            type="tel"
            error={ec?.telefono?.message}
            {...register("comprador.telefono")}
          />
          <Entrada
            etiqueta="Correo electrónico"
            type="email"
            error={ec?.email?.message}
            {...register("comprador.email")}
          />
          <Entrada
            etiqueta="Dirección"
            className="sm:col-span-2 lg:col-span-3"
            error={ec?.direccion?.message}
            {...register("comprador.direccion")}
          />
          <Entrada
            etiqueta="Fecha de nacimiento"
            type="date"
            ayuda="La edad se calcula sola"
            error={ec?.fecha_nacimiento?.message}
            {...register("comprador.fecha_nacimiento")}
          />
          <Entrada
            etiqueta="Nacionalidad"
            error={ec?.nacionalidad?.message}
            {...register("comprador.nacionalidad")}
          />
          <Seleccion
            etiqueta="Estado civil"
            opciones={ESTADOS_CIVILES}
            error={ec?.estado_civil?.message}
            {...register("comprador.estado_civil")}
          />
          <Entrada
            etiqueta="Personas que dependen de él/ella"
            inputMode="numeric"
            error={ec?.num_dependientes?.message}
            {...register("comprador.num_dependientes")}
          />
          <Entrada
            etiqueta="Profesión o actividad"
            className="lg:col-span-2"
            error={ec?.profesion_actividad?.message}
            {...register("comprador.profesion_actividad")}
          />
        </div>
        <h3 className="mb-3 mt-6 text-sm font-semibold text-slate-700">Datos laborales</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Entrada
            etiqueta="Empresa donde trabaja"
            error={et?.empresa?.message}
            {...register("comprador.trabajo.empresa")}
          />
          <Entrada
            etiqueta="Puesto"
            error={et?.puesto?.message}
            {...register("comprador.trabajo.puesto")}
          />
          <Entrada
            etiqueta="Tiempo de trabajo"
            placeholder="p. ej. 5 años"
            error={et?.tiempo_trabajo?.message}
            {...register("comprador.trabajo.tiempo_trabajo")}
          />
          <Entrada
            etiqueta="Dirección del trabajo"
            className="sm:col-span-2"
            error={et?.direccion?.message}
            {...register("comprador.trabajo.direccion")}
          />
          <Entrada
            etiqueta="Teléfono del trabajo"
            type="tel"
            error={et?.telefono?.message}
            {...register("comprador.trabajo.telefono")}
          />
          <EntradaMonto
            etiqueta="Ingreso mensual (Q)"
            error={et?.ingreso_mensual?.message}
            {...register("comprador.trabajo.ingreso_mensual")}
          />
          <EntradaMonto
            etiqueta="Otros ingresos (Q)"
            error={et?.otros_ingresos?.message}
            {...register("comprador.trabajo.otros_ingresos")}
          />
        </div>
      </Seccion>

      <Seccion
        titulo="Cónyuge, familiar o gestor"
        acciones={<Casilla etiqueta="Incluir" {...register("tiene_conyuge")} />}
      >
        {tieneConyuge ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Entrada
              etiqueta="Nombres y apellidos"
              obligatorio
              className="lg:col-span-2"
              error={ey?.nombres_apellidos?.message}
              {...register("conyuge_gestor.nombres_apellidos")}
            />
            <Entrada
              etiqueta="DPI"
              inputMode="numeric"
              error={ey?.dpi?.message}
              {...register("conyuge_gestor.dpi")}
            />
            <Entrada
              etiqueta="Dirección"
              className="sm:col-span-2"
              error={ey?.direccion?.message}
              {...register("conyuge_gestor.direccion")}
            />
            <Entrada
              etiqueta="Teléfono"
              type="tel"
              error={ey?.telefono?.message}
              {...register("conyuge_gestor.telefono")}
            />
            <Entrada
              etiqueta="Correo electrónico"
              type="email"
              error={ey?.email?.message}
              {...register("conyuge_gestor.email")}
            />
            <Entrada
              etiqueta="Fecha de nacimiento"
              type="date"
              error={ey?.fecha_nacimiento?.message}
              {...register("conyuge_gestor.fecha_nacimiento")}
            />
            <Entrada
              etiqueta="Nacionalidad"
              error={ey?.nacionalidad?.message}
              {...register("conyuge_gestor.nacionalidad")}
            />
            <Entrada
              etiqueta="Profesión o actividad"
              className="sm:col-span-2 lg:col-span-3"
              error={ey?.profesion_actividad?.message}
              {...register("conyuge_gestor.profesion_actividad")}
            />
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            Marque "Incluir" si el contrato lleva datos del cónyuge, un familiar o gestor.
          </p>
        )}
      </Seccion>

      <Seccion
        titulo="Personas que dependen del comprador"
        descripcion="Opcional, hasta 5."
        acciones={
          <Boton
            pequeno
            variante="secundario"
            icono={<Plus className="size-4" aria-hidden />}
            disabled={dependientes.fields.length >= 5}
            onClick={() => dependientes.append({ nombre: "", edad: "", dpi: "" })}
          >
            Agregar
          </Boton>
        }
      >
        {dependientes.fields.length === 0 && (
          <p className="text-sm text-slate-500">Sin dependientes registrados.</p>
        )}
        <div className="space-y-3">
          {dependientes.fields.map((campo, i) => (
            <div
              key={campo.id}
              className="grid items-start gap-3 sm:grid-cols-[1fr_6rem_12rem_auto]"
            >
              <Entrada
                etiqueta={`Nombre ${i + 1}`}
                error={errors.dependientes?.[i]?.nombre?.message}
                {...register(`dependientes.${i}.nombre`)}
              />
              <Entrada
                etiqueta="Edad"
                inputMode="numeric"
                error={errors.dependientes?.[i]?.edad?.message}
                {...register(`dependientes.${i}.edad`)}
              />
              <Entrada
                etiqueta="DPI"
                inputMode="numeric"
                error={errors.dependientes?.[i]?.dpi?.message}
                {...register(`dependientes.${i}.dpi`)}
              />
              <Boton
                variante="fantasma"
                className="sm:mt-6"
                aria-label={`Quitar dependiente ${i + 1}`}
                onClick={() => dependientes.remove(i)}
                icono={<Trash2 className="size-4" aria-hidden />}
              />
            </div>
          ))}
        </div>
      </Seccion>

      <Seccion titulo="Identificación del inmueble">
        <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <Entrada
            etiqueta="Lote No."
            obligatorio
            placeholder="36-B34"
            error={el?.codigo?.message}
            {...register("lote.codigo")}
          />
          <EntradaMonto
            etiqueta="Área total (m²)"
            obligatorio
            error={el?.area_m2?.message}
            {...register("lote.area_m2")}
          />
          <Entrada etiqueta="Finca No." error={el?.finca?.message} {...register("lote.finca")} />
          <Entrada etiqueta="Folio No." error={el?.folio?.message} {...register("lote.folio")} />
          <Entrada etiqueta="Libro No." error={el?.libro?.message} {...register("lote.libro")} />
          <Entrada
            etiqueta="De (departamento)"
            error={el?.libro_de?.message}
            {...register("lote.libro_de")}
          />
        </div>
      </Seccion>

      <Seccion titulo="Condiciones de la compra-venta">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <EntradaMonto
                etiqueta="Precio del terreno (Q)"
                obligatorio
                error={ed?.precio_terreno?.message}
                {...register("condiciones.precio_terreno")}
              />
              <EntradaMonto
                etiqueta="Mejoras al terreno (Q)"
                error={ed?.mejoras?.message}
                {...register("condiciones.mejoras")}
              />
              <EntradaMonto
                etiqueta="Enganche (Q)"
                error={ed?.enganche?.message}
                {...register("condiciones.enganche")}
              />
              <EntradaMonto
                etiqueta="Otros descuentos (Q)"
                error={ed?.otros_descuentos?.message}
                {...register("condiciones.otros_descuentos")}
              />
              <Seleccion
                etiqueta="Plazo"
                obligatorio
                opciones={PLAZOS}
                error={ed?.plazo_anios?.message}
                {...register("condiciones.plazo_anios")}
              />
              <Entrada
                etiqueta="Número de cuotas"
                inputMode="numeric"
                ayuda="Vacío = plazo × 12"
                error={ed?.numero_cuotas?.message}
                {...register("condiciones.numero_cuotas")}
              />
              <EntradaMonto
                etiqueta="Tasa de interés anual (%)"
                error={ed?.tasa_interes_anual_pct?.message}
                {...register("condiciones.tasa_interes_anual_pct")}
              />
              <EntradaMonto
                etiqueta="Cuota nivelada (Q)"
                ayuda="Vacío = la calcula el sistema"
                error={ed?.cuota_nivelada?.message}
                {...register("condiciones.cuota_nivelada")}
              />
              <Entrada
                etiqueta="Fecha de la primera cuota"
                type="date"
                obligatorio
                error={ed?.fecha_primera_cuota?.message}
                {...register("condiciones.fecha_primera_cuota")}
              />
              <Entrada
                etiqueta="Día de pago de cada mes"
                inputMode="numeric"
                ayuda="Vacío = mismo día de la primera cuota"
                error={ed?.dia_pago_mensual?.message}
                {...register("condiciones.dia_pago_mensual")}
              />
            </div>
            <AreaTexto
              etiqueta="Otras condiciones de la negociación"
              error={ed?.otras_condiciones?.message}
              {...register("condiciones.otras_condiciones")}
            />

            <div className="rounded-md border border-slate-200 p-3">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-700">
                  Enganche fraccionado (opcional, hasta 4 pagos)
                </h3>
                <Boton
                  pequeno
                  variante="secundario"
                  icono={<Plus className="size-4" aria-hidden />}
                  disabled={enganches.fields.length >= 4}
                  onClick={() => enganches.append({ fecha: "", monto: "" })}
                >
                  Agregar
                </Boton>
              </div>
              {ed?.enganche_fraccionado?.message && (
                <p role="alert" className="mb-2 text-xs text-peligro">
                  {ed.enganche_fraccionado.message}
                </p>
              )}
              <div className="space-y-2">
                {enganches.fields.map((campo, i) => (
                  <div
                    key={campo.id}
                    className="grid items-start gap-2 sm:grid-cols-[1fr_1fr_auto]"
                  >
                    <Entrada
                      etiqueta={`Fecha ${i + 1}`}
                      type="date"
                      error={ed?.enganche_fraccionado?.[i]?.fecha?.message}
                      {...register(`condiciones.enganche_fraccionado.${i}.fecha`)}
                    />
                    <EntradaMonto
                      etiqueta="Monto (Q)"
                      error={ed?.enganche_fraccionado?.[i]?.monto?.message}
                      {...register(`condiciones.enganche_fraccionado.${i}.monto`)}
                    />
                    <Boton
                      variante="fantasma"
                      className="sm:mt-6"
                      aria-label={`Quitar pago de enganche ${i + 1}`}
                      onClick={() => enganches.remove(i)}
                      icono={<Trash2 className="size-4" aria-hidden />}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="lg:sticky lg:top-4 lg:self-start">
            <VistaPrevia condiciones={condicionesPrevia} />
          </div>
        </div>
      </Seccion>

      {vieneDePapel && (
        <Seccion
          titulo="Saldo actual (cliente que venía pagando en papel)"
          descripcion="Las cuotas indicadas se marcarán como pagadas y el enganche como cancelado."
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <EntradaMonto
              etiqueta="Saldo de capital actual (Q)"
              obligatorio
              error={es?.saldo_capital?.message}
              {...register("saldo_inicial.saldo_capital")}
            />
            <Entrada
              etiqueta="Cuotas ya pagadas"
              obligatorio
              inputMode="numeric"
              error={es?.cuotas_pagadas?.message}
              {...register("saldo_inicial.cuotas_pagadas")}
            />
            <Entrada
              etiqueta="Saldo a la fecha de"
              type="date"
              obligatorio
              error={es?.fecha_corte?.message}
              {...register("saldo_inicial.fecha_corte")}
            />
            <Entrada
              etiqueta="Nota"
              placeholder="Último recibo en papel No. …"
              error={es?.nota?.message}
              {...register("saldo_inicial.nota")}
            />
          </div>
        </Seccion>
      )}

      <div className="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 bg-white/95 px-4 py-3 backdrop-blur">
        <div className="min-w-0 flex-1">
          {errorGeneral && <Alerta tono="peligro">{errorGeneral}</Alerta>}
          {!errorGeneral && submitCount > 0 && Object.keys(errors).length > 0 && (
            <Alerta tono="alerta">
              Hay campos con errores. Revíselos (están marcados en rojo).
            </Alerta>
          )}
        </div>
        <Boton
          type="submit"
          cargando={isSubmitting}
          icono={<Save className="size-4" aria-hidden />}
        >
          Guardar promesa
        </Boton>
      </div>
    </form>
  );
}
