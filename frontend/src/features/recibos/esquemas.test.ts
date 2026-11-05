import { describe, expect, it } from "vitest";

import {
  aPayloadRecibo,
  esquemaPago,
  resumenPago,
  valoresPago,
  type FormularioPago,
} from "./esquemas";

function pago(
  cambios: Omit<Partial<FormularioPago>, "desglose"> & {
    desglose?: Partial<FormularioPago["desglose"]>;
  },
): FormularioPago {
  const base = valoresPago("2025-11-04");
  return { ...base, ...cambios, desglose: { ...base.desglose, ...cambios.desglose } };
}

describe("formulario de pago", () => {
  it("recibo real: cuota 9 de 10,219 deja saldo 20,429", () => {
    const v = pago({ cuota_numero: "9", desglose: { capital: "10219" } });
    expect(esquemaPago.safeParse(v).success).toBe(true);
    expect(resumenPago(v, "30648.00")).toEqual({
      total: "10219.00",
      aCapital: "10219.00",
      saldoResultante: "20429.00",
      excedeSaldo: false,
    });
  });

  it("mora e intereses no reducen el saldo", () => {
    const v = pago({
      cuota_numero: "9",
      desglose: { capital: "10219", recargo_mora: "510.95", intereses: "100" },
    });
    const r = resumenPago(v, "30648.00");
    expect(r.total).toBe("10829.95");
    expect(r.saldoResultante).toBe("20429.00");
  });

  it("solo envía los campos del concepto elegido", () => {
    const v = pago({
      concepto: "abono_capital",
      desglose: { abono_capital: "5000", capital: "999" },
    });
    const p = aPayloadRecibo(v, "abc");
    expect(p.desglose.capital).toBe("0");
    expect(p.desglose.abono_capital).toBe("5000");
    expect(p.cuota_numero).toBeNull();
  });

  it("detecta pago mayor al saldo", () => {
    expect(
      resumenPago(
        pago({ concepto: "abono_capital", desglose: { abono_capital: "40000" } }),
        "30648",
      ).excedeSaldo,
    ).toBe(true);
  });

  it.each([
    ["cuota sin número", pago({ desglose: { capital: "100" } }), "cuota_numero"],
    ["total cero", pago({ concepto: "otros" }), "desglose"],
    [
      "enganche sin monto",
      pago({ concepto: "enganche", desglose: { otros: "5" } }),
      "desglose.enganche",
    ],
    [
      "boleta sin número",
      pago({
        cuota_numero: "1",
        desglose: { capital: "1" },
        boletas: [{ numero: "", cuenta: "" }],
      }),
      "boletas.0.numero",
    ],
  ])("rechaza: %s", (_n, v, ruta) => {
    const r = esquemaPago.safeParse(v);
    expect(r.success).toBe(false);
    expect(r.error?.issues.some((i) => i.path.join(".") === ruta)).toBe(true);
  });
});
