/** Validación del formulario "Nueva Promesa de Compra Venta" (espejo de las reglas del backend). */

import { z } from "zod";

import type { CondicionesEntrada, ContratoCrear, Lotificacion, Persona } from "../../api/tipos";
import { NOMBRE_LOTIFICACION } from "../../lib/formato";
import {
  aCentavos,
  dpiValido,
  nitValido,
  normalizarDpi,
  PATRON_MONTO,
} from "../../lib/validaciones";

const PATRON_FECHA = /^\d{4}-\d{2}-\d{2}$/;
const PATRON_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

const texto = (max: number) => z.string().trim().max(max, `Máximo ${max} caracteres`);
const monto = z.string().trim().regex(PATRON_MONTO, "Monto inválido (ej. 1234.56, sin comas)");
const montoOpcional = z
  .string()
  .trim()
  .refine((v) => v === "" || PATRON_MONTO.test(v), "Monto inválido");
const fecha = z.string().regex(PATRON_FECHA, "Fecha requerida");
const fechaOpcional = z.string().refine((v) => v === "" || PATRON_FECHA.test(v), "Fecha inválida");
const dpiOpcional = z
  .string()
  .trim()
  .refine((v) => v === "" || dpiValido(v), "DPI inválido (13 dígitos con verificador correcto)");
const enteroOpcional = (min: number, max: number) =>
  z
    .string()
    .trim()
    .refine(
      (v) => v === "" || (/^\d+$/.test(v) && Number(v) >= min && Number(v) <= max),
      `Entre ${min} y ${max}`,
    );

const persona = {
  nombres_apellidos: texto(150),
  dpi: dpiOpcional,
  direccion: texto(250),
  telefono: texto(60),
  email: z
    .string()
    .trim()
    .refine((v) => v === "" || PATRON_EMAIL.test(v), "Correo inválido"),
  fecha_nacimiento: fechaOpcional,
  nacionalidad: texto(60),
  profesion_actividad: texto(250),
};

export const esquemaPromesa = z
  .object({
    fecha_firma: fecha,
    lotificacion: z
      .string()
      .refine((v) => Object.hasOwn(NOMBRE_LOTIFICACION, v), "Seleccione la lotificación"),
    comprador: z.object({
      ...persona,
      nombres_apellidos: texto(150).min(3, "Escriba el nombre completo"),
      dpi: z
        .string()
        .trim()
        .refine(dpiValido, "DPI inválido (13 dígitos con verificador correcto)"),
      nit: z
        .string()
        .trim()
        .refine((v) => v === "" || nitValido(v), "NIT inválido; use CF si no tiene"),
      estado_civil: texto(60),
      num_dependientes: enteroOpcional(0, 20),
      trabajo: z.object({
        empresa: texto(250),
        direccion: texto(250),
        telefono: texto(60),
        puesto: texto(250),
        tiempo_trabajo: texto(60),
        ingreso_mensual: montoOpcional,
        otros_ingresos: montoOpcional,
      }),
    }),
    tiene_conyuge: z.boolean(),
    conyuge_gestor: z.object(persona),
    dependientes: z
      .array(
        z.object({
          nombre: texto(150).min(3, "Escriba el nombre"),
          edad: enteroOpcional(0, 120),
          dpi: dpiOpcional,
        }),
      )
      .max(5, "Máximo 5 dependientes"),
    lote: z.object({
      codigo: texto(30).min(1, "Indique el número de lote"),
      area_m2: monto.refine((v) => aCentavos(v) > 0, "El área debe ser mayor que cero"),
      finca: texto(60),
      folio: texto(60),
      libro: texto(60),
      libro_de: texto(60),
    }),
    condiciones: z.object({
      precio_terreno: monto,
      mejoras: monto,
      enganche: monto,
      otros_descuentos: monto,
      enganche_fraccionado: z
        .array(z.object({ fecha, monto }))
        .max(4, "Máximo 4 pagos de enganche"),
      plazo_anios: z.enum(["1", "2", "3", "4"]),
      numero_cuotas: enteroOpcional(1, 48),
      tasa_interes_anual_pct: monto.refine((v) => aCentavos(v) <= 10_000, "Máximo 100 %"),
      cuota_nivelada: montoOpcional,
      fecha_primera_cuota: fecha,
      dia_pago_mensual: enteroOpcional(1, 31),
      otras_condiciones: texto(1000),
    }),
    viene_de_papel: z.boolean(),
    saldo_inicial: z.object({
      saldo_capital: montoOpcional,
      cuotas_pagadas: enteroOpcional(0, 48),
      fecha_corte: fechaOpcional,
      nota: texto(250),
    }),
  })
  .superRefine((v, ctx) => {
    const c = v.condiciones;
    if (v.tiene_conyuge && v.conyuge_gestor.nombres_apellidos.length < 3) {
      ctx.addIssue({
        code: "custom",
        path: ["conyuge_gestor", "nombres_apellidos"],
        message: "Escriba el nombre completo",
      });
    }
    const total = aCentavos(c.precio_terreno) + aCentavos(c.mejoras);
    if (aCentavos(c.enganche) + aCentavos(c.otros_descuentos) > total) {
      ctx.addIssue({
        code: "custom",
        path: ["condiciones", "enganche"],
        message: "El enganche y descuentos superan el total",
      });
    }
    if (c.enganche_fraccionado.length > 0) {
      const suma = c.enganche_fraccionado.reduce((s, f) => s + aCentavos(f.monto), 0);
      if (suma !== aCentavos(c.enganche)) {
        ctx.addIssue({
          code: "custom",
          path: ["condiciones", "enganche_fraccionado"],
          message: "La suma de los pagos de enganche debe ser igual al enganche",
        });
      }
    }
    const maximo = Number(c.plazo_anios) * 12;
    if (c.numero_cuotas && Number(c.numero_cuotas) > maximo) {
      ctx.addIssue({
        code: "custom",
        path: ["condiciones", "numero_cuotas"],
        message: `Máximo ${maximo} cuotas para el plazo elegido`,
      });
    }
    if (v.fecha_firma && c.fecha_primera_cuota && c.fecha_primera_cuota <= v.fecha_firma) {
      ctx.addIssue({
        code: "custom",
        path: ["condiciones", "fecha_primera_cuota"],
        message: "Debe ser posterior a la fecha de firma",
      });
    }
    if (v.viene_de_papel) {
      const s = v.saldo_inicial;
      if (!s.saldo_capital)
        ctx.addIssue({
          code: "custom",
          path: ["saldo_inicial", "saldo_capital"],
          message: "Indique el saldo actual",
        });
      if (!s.cuotas_pagadas)
        ctx.addIssue({
          code: "custom",
          path: ["saldo_inicial", "cuotas_pagadas"],
          message: "Indique las cuotas ya pagadas",
        });
      if (!s.fecha_corte)
        ctx.addIssue({
          code: "custom",
          path: ["saldo_inicial", "fecha_corte"],
          message: "Indique la fecha del saldo",
        });
    }
  });

export type FormularioPromesa = z.infer<typeof esquemaPromesa>;

const vacioPersona = {
  nombres_apellidos: "",
  dpi: "",
  direccion: "",
  telefono: "",
  email: "",
  fecha_nacimiento: "",
  nacionalidad: "Guatemalteca",
  profesion_actividad: "",
};

export function valoresIniciales(hoy: string): FormularioPromesa {
  return {
    fecha_firma: hoy,
    lotificacion: "", // se elige siempre a mano para no imprimir otra lotificación por error
    comprador: {
      ...vacioPersona,
      nit: "",
      estado_civil: "",
      num_dependientes: "",
      trabajo: {
        empresa: "",
        direccion: "",
        telefono: "",
        puesto: "",
        tiempo_trabajo: "",
        ingreso_mensual: "",
        otros_ingresos: "",
      },
    },
    tiene_conyuge: false,
    conyuge_gestor: { ...vacioPersona },
    dependientes: [],
    lote: { codigo: "", area_m2: "", finca: "", folio: "", libro: "", libro_de: "Jalapa" },
    condiciones: {
      precio_terreno: "",
      mejoras: "0",
      enganche: "0",
      otros_descuentos: "0",
      enganche_fraccionado: [],
      plazo_anios: "1",
      numero_cuotas: "",
      tasa_interes_anual_pct: "0",
      cuota_nivelada: "",
      fecha_primera_cuota: "",
      dia_pago_mensual: "",
      otras_condiciones: "",
    },
    viene_de_papel: false,
    saldo_inicial: { saldo_capital: "", cuotas_pagadas: "", fecha_corte: "", nota: "" },
  };
}

/** "" → null para que el backend reciba campos opcionales vacíos como ausentes. */
const n = (v: string): string | null => (v.trim() === "" ? null : v.trim());
const entero = (v: string): number | null => (v.trim() === "" ? null : Number(v));

function aPersona(p: FormularioPromesa["conyuge_gestor"]): Persona {
  return {
    nombres_apellidos: p.nombres_apellidos.trim(),
    dpi: n(p.dpi) && normalizarDpi(p.dpi),
    direccion: n(p.direccion),
    telefono: n(p.telefono),
    email: n(p.email),
    fecha_nacimiento: n(p.fecha_nacimiento),
    nacionalidad: p.nacionalidad.trim() || "Guatemalteca",
    profesion_actividad: n(p.profesion_actividad),
  };
}

export function aCondiciones(c: FormularioPromesa["condiciones"]): CondicionesEntrada {
  return {
    precio_terreno: c.precio_terreno.trim(),
    mejoras: c.mejoras.trim() || "0",
    enganche: c.enganche.trim() || "0",
    otros_descuentos: c.otros_descuentos.trim() || "0",
    enganche_fraccionado: c.enganche_fraccionado.map((f) => ({
      fecha: f.fecha,
      monto: f.monto.trim(),
    })),
    plazo_anios: Number(c.plazo_anios),
    numero_cuotas: entero(c.numero_cuotas),
    tasa_interes_anual_pct: c.tasa_interes_anual_pct.trim() || "0",
    cuota_nivelada: n(c.cuota_nivelada),
    fecha_primera_cuota: c.fecha_primera_cuota,
    dia_pago_mensual: entero(c.dia_pago_mensual),
    otras_condiciones: n(c.otras_condiciones),
  };
}

export function aPayload(v: FormularioPromesa): ContratoCrear {
  const comp = v.comprador;
  const t = comp.trabajo;
  return {
    fecha_firma: v.fecha_firma,
    lotificacion: v.lotificacion as Lotificacion, // ya validada por esquemaPromesa
    comprador: {
      ...aPersona(comp),
      dpi: normalizarDpi(comp.dpi),
      nit: n(comp.nit),
      estado_civil: n(comp.estado_civil),
      num_dependientes: entero(comp.num_dependientes) ?? 0,
      trabajo: {
        empresa: n(t.empresa),
        direccion: n(t.direccion),
        telefono: n(t.telefono),
        puesto: n(t.puesto),
        tiempo_trabajo: n(t.tiempo_trabajo),
        ingreso_mensual: n(t.ingreso_mensual),
        otros_ingresos: n(t.otros_ingresos),
      },
    },
    conyuge_gestor: v.tiene_conyuge ? aPersona(v.conyuge_gestor) : null,
    dependientes: v.dependientes.map((d) => ({
      nombre: d.nombre.trim(),
      edad: entero(d.edad),
      dpi: n(d.dpi),
    })),
    lote: {
      codigo: v.lote.codigo.trim().toUpperCase(),
      area_m2: v.lote.area_m2.trim(),
      finca: n(v.lote.finca),
      folio: n(v.lote.folio),
      libro: n(v.lote.libro),
      libro_de: n(v.lote.libro_de),
    },
    condiciones: aCondiciones(v.condiciones),
    notario: null,
    saldo_inicial: v.viene_de_papel
      ? {
          saldo_capital: v.saldo_inicial.saldo_capital.trim(),
          cuotas_pagadas: Number(v.saldo_inicial.cuotas_pagadas),
          fecha_corte: v.saldo_inicial.fecha_corte,
          nota: n(v.saldo_inicial.nota),
        }
      : null,
  };
}

/** Solo las condiciones, para pedir la vista previa del plan mientras se escribe. */
export const esquemaCondicionesPrevia = z.object({
  precio_terreno: monto,
  mejoras: monto,
  enganche: monto,
  otros_descuentos: monto,
  plazo_anios: z.enum(["1", "2", "3", "4"]),
  numero_cuotas: enteroOpcional(1, 48),
  tasa_interes_anual_pct: monto,
  cuota_nivelada: montoOpcional,
  fecha_primera_cuota: fecha,
  dia_pago_mensual: enteroOpcional(1, 31),
});

/** Motivo para borrar una promesa o un recibo (mismo límite que el backend). */
export const esquemaEliminar = z.object({
  motivo: z
    .string()
    .trim()
    .min(5, "Escriba al menos 5 caracteres")
    .max(250, "Máximo 250 caracteres"),
});
