/** Validación del formulario "Registrar pago" (espejo de las reglas del backend). */

import { z } from "zod";

import type { Concepto, Desglose, ReciboCrear } from "../../api/tipos";
import { aCentavos, deCentavos, PATRON_MONTO } from "../../lib/validaciones";

const montoOpcional = z
  .string()
  .trim()
  .refine((v) => v === "" || PATRON_MONTO.test(v), "Monto inválido (ej. 1234.56)");
const texto = (max: number) => z.string().trim().max(max, `Máximo ${max} caracteres`);

/** Campos del desglose que aplican a cada concepto; el resto se envía en cero. */
export const CAMPOS_POR_CONCEPTO: Record<Concepto, (keyof Desglose)[]> = {
  enganche: ["enganche", "otros"],
  cuota: ["capital", "intereses", "recargo_mora", "abono_capital", "otros"],
  abono_capital: ["abono_capital", "otros"],
  otros: ["recargo_mora", "otros"],
};

export const ETIQUETAS_DESGLOSE: Record<keyof Desglose, string> = {
  enganche: "Enganche",
  capital: "Capital",
  intereses: "Intereses",
  recargo_mora: "(+) Recargo por mora",
  abono_capital: "(+) Abono a capital",
  otros: "(+) Otros",
};

export const esquemaPago = z
  .object({
    fecha: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Fecha requerida"),
    concepto: z.enum(["enganche", "cuota", "abono_capital", "otros"]),
    cuota_numero: z.string().trim(),
    desglose: z.object({
      enganche: montoOpcional,
      capital: montoOpcional,
      intereses: montoOpcional,
      recargo_mora: montoOpcional,
      abono_capital: montoOpcional,
      otros: montoOpcional,
    }),
    boletas: z
      .array(z.object({ numero: texto(60).min(1, "Número de boleta"), cuenta: texto(60) }))
      .max(5, "Máximo 5 boletas"),
    numero_fel: texto(60),
    observaciones: texto(250),
  })
  .superRefine((v, ctx) => {
    const d = v.desglose;
    const campos = CAMPOS_POR_CONCEPTO[v.concepto];
    const total = campos.reduce((s, c) => s + aCentavos(d[c]), 0);
    if (total <= 0)
      ctx.addIssue({
        code: "custom",
        path: ["desglose"],
        message: "El total del recibo debe ser mayor que cero",
      });
    if (v.concepto === "cuota") {
      if (!/^\d+$/.test(v.cuota_numero))
        ctx.addIssue({
          code: "custom",
          path: ["cuota_numero"],
          message: "Indique el número de cuota",
        });
      if (aCentavos(d.capital) + aCentavos(d.intereses) <= 0)
        ctx.addIssue({
          code: "custom",
          path: ["desglose", "capital"],
          message: "Incluya capital o intereses de la cuota",
        });
    }
    if (v.concepto === "enganche" && aCentavos(d.enganche) <= 0)
      ctx.addIssue({
        code: "custom",
        path: ["desglose", "enganche"],
        message: "Indique el monto del enganche",
      });
    if (v.concepto === "abono_capital" && aCentavos(d.abono_capital) <= 0)
      ctx.addIssue({
        code: "custom",
        path: ["desglose", "abono_capital"],
        message: "Indique el monto del abono",
      });
  });

export type FormularioPago = z.infer<typeof esquemaPago>;

export function valoresPago(hoy: string): FormularioPago {
  return {
    fecha: hoy,
    concepto: "cuota",
    cuota_numero: "",
    desglose: {
      enganche: "",
      capital: "",
      intereses: "",
      recargo_mora: "",
      abono_capital: "",
      otros: "",
    },
    boletas: [],
    numero_fel: "",
    observaciones: "",
  };
}

/** Totales que se muestran antes de guardar (el servidor vuelve a calcular todo). */
export function resumenPago(v: FormularioPago, saldoActual: string) {
  const campos = CAMPOS_POR_CONCEPTO[v.concepto];
  const valor = (c: keyof Desglose) => (campos.includes(c) ? aCentavos(v.desglose[c]) : 0);
  const total = campos.reduce((s, c) => s + valor(c), 0);
  const aCapital = valor("capital") + valor("abono_capital");
  const saldo = aCentavos(saldoActual) - aCapital;
  return {
    total: deCentavos(total),
    aCapital: deCentavos(aCapital),
    saldoResultante: deCentavos(saldo),
    excedeSaldo: saldo < 0,
  };
}

export function aPayloadRecibo(v: FormularioPago, contratoId: string): ReciboCrear {
  const campos = CAMPOS_POR_CONCEPTO[v.concepto];
  const d = (c: keyof Desglose) =>
    campos.includes(c) && v.desglose[c].trim() ? v.desglose[c].trim() : "0";
  return {
    contrato_id: contratoId,
    fecha: v.fecha,
    concepto: v.concepto,
    cuota_numero: v.concepto === "cuota" ? Number(v.cuota_numero) : null,
    desglose: {
      enganche: d("enganche"),
      capital: d("capital"),
      intereses: d("intereses"),
      recargo_mora: d("recargo_mora"),
      abono_capital: d("abono_capital"),
      otros: d("otros"),
    },
    boletas: v.boletas.map((b) => ({ numero: b.numero.trim(), cuenta: b.cuenta.trim() || null })),
    numero_fel: v.numero_fel.trim() || null,
    observaciones: v.observaciones.trim() || null,
  };
}
