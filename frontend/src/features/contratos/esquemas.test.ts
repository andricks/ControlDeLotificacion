import { describe, expect, it } from "vitest";

import { formularioEjemplo } from "../../test/datos";
import { aPayload, esquemaEliminar, esquemaPromesa } from "./esquemas";

describe("esquemaEliminar", () => {
  it("exige un motivo de al menos 5 caracteres (sin contar espacios)", () => {
    expect(esquemaEliminar.safeParse({ motivo: "   abc   " }).success).toBe(false);
    expect(esquemaEliminar.safeParse({ motivo: "x".repeat(251) }).success).toBe(false);
    const r = esquemaEliminar.safeParse({ motivo: "  Promesa de prueba " });
    expect(r.success && r.data.motivo).toBe("Promesa de prueba");
  });
});

function errores(cambiar: (v: ReturnType<typeof formularioEjemplo>) => void): string[] {
  const v = formularioEjemplo();
  cambiar(v);
  const r = esquemaPromesa.safeParse(v);
  return r.success ? [] : r.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`);
}

describe("esquemaPromesa", () => {
  it("acepta el ejemplo", () => {
    expect(errores(() => {})).toEqual([]);
  });

  it.each([
    [
      "sin lotificación",
      (v: ReturnType<typeof formularioEjemplo>) => (v.lotificacion = ""),
      "lotificacion",
    ],
    [
      "lotificación fuera de la lista",
      (v: ReturnType<typeof formularioEjemplo>) => (v.lotificacion = "otra"),
      "lotificacion",
    ],
    [
      "DPI inválido",
      (v: ReturnType<typeof formularioEjemplo>) => (v.comprador.dpi = "123"),
      "comprador.dpi",
    ],
    [
      "NIT inválido",
      (v: ReturnType<typeof formularioEjemplo>) => (v.comprador.nit = "1234567-8"),
      "comprador.nit",
    ],
    [
      "monto con 3 decimales",
      (v: ReturnType<typeof formularioEjemplo>) => (v.condiciones.precio_terreno = "1.555"),
      "condiciones.precio_terreno",
    ],
    [
      "cuotas > plazo×12",
      (v: ReturnType<typeof formularioEjemplo>) => (v.condiciones.numero_cuotas = "13"),
      "condiciones.numero_cuotas",
    ],
    [
      "enganche fraccionado no suma",
      (v: ReturnType<typeof formularioEjemplo>) =>
        (v.condiciones.enganche_fraccionado = [{ fecha: "2025-01-22", monto: "5000" }]),
      "condiciones.enganche_fraccionado",
    ],
    [
      "primera cuota antes de la firma",
      (v: ReturnType<typeof formularioEjemplo>) =>
        (v.condiciones.fecha_primera_cuota = "2025-01-01"),
      "condiciones.fecha_primera_cuota",
    ],
    [
      "cónyuge sin nombre",
      (v: ReturnType<typeof formularioEjemplo>) => (v.tiene_conyuge = true),
      "conyuge_gestor.nombres_apellidos",
    ],
    [
      "papel sin saldo",
      (v: ReturnType<typeof formularioEjemplo>) => (v.viene_de_papel = true),
      "saldo_inicial.saldo_capital",
    ],
    [
      "enganche mayor al total",
      (v: ReturnType<typeof formularioEjemplo>) => {
        v.condiciones.enganche = "999999";
        v.condiciones.enganche_fraccionado = [];
      },
      "condiciones.enganche",
    ],
  ])("rechaza: %s", (_nombre, cambiar, ruta) => {
    expect(errores(cambiar).some((e) => e.startsWith(ruta))).toBe(true);
  });
});

describe("aPayload", () => {
  it("convierte vacíos a null, normaliza y omite cónyuge/saldo no marcados", () => {
    const p = aPayload(formularioEjemplo());
    expect(p.lote.codigo).toBe("36-B34");
    expect(p.lotificacion).toBe("tablon_campestre2");
    expect(p.comprador.email).toBeNull();
    expect(p.conyuge_gestor).toBeNull();
    expect(p.saldo_inicial).toBeNull();
    expect(p.condiciones.numero_cuotas).toBe(11);
    expect(p.condiciones.cuota_nivelada).toBeNull();
    expect(p.condiciones.plazo_anios).toBe(1);
  });

  it("incluye saldo inicial cuando el cliente viene del papel", () => {
    const v = formularioEjemplo();
    v.viene_de_papel = true;
    v.saldo_inicial = {
      saldo_capital: "30648",
      cuotas_pagadas: "8",
      fecha_corte: "2025-10-01",
      nota: "",
    };
    expect(aPayload(v).saldo_inicial).toEqual({
      saldo_capital: "30648",
      cuotas_pagadas: 8,
      fecha_corte: "2025-10-01",
      nota: null,
    });
  });
});
