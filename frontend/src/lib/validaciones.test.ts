import { describe, expect, it } from "vitest";

import { aCentavos, deCentavos, dpiValido, nitValido } from "./validaciones";

// Números ficticios con verificador válido (los mismos que usa el backend en sus tests).
describe("nitValido", () => {
  it.each(["576937-K", "576937k", "1234567-9", "CF", "cf", "12345679"])("acepta %s", (nit) => {
    expect(nitValido(nit)).toBe(true);
  });
  it.each(["1234567-8", "", "K", "12A45-6"])("rechaza %s", (nit) => {
    expect(nitValido(nit)).toBe(false);
  });
});

describe("dpiValido", () => {
  it.each(["1234567892101", "8765432122101", "1234 56789 2101"])("acepta %s", (dpi) => {
    expect(dpiValido(dpi)).toBe(true);
  });
  it.each(["1234567882101", "1234567892301", "1234567892100", "123456789210", ""])(
    "rechaza %s",
    (dpi) => {
      expect(dpiValido(dpi)).toBe(false);
    },
  );
});

describe("centavos (sin errores de punto flotante)", () => {
  it("convierte montos", () => {
    expect(aCentavos("10219")).toBe(1_021_900);
    expect(aCentavos("0.1")).toBe(10);
    expect(aCentavos("1,234.56")).toBe(123_456);
    expect(aCentavos("abc")).toBe(0);
    expect(aCentavos("")).toBe(0);
  });
  it("0.10 + 0.20 = 0.30 exacto", () => {
    expect(deCentavos(aCentavos("0.10") + aCentavos("0.20"))).toBe("0.30");
  });
  it("formatea negativos", () => {
    expect(deCentavos(-505)).toBe("-5.05");
  });
});
