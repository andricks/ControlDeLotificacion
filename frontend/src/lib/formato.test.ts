import { describe, expect, it } from "vitest";

import { fecha, moneda } from "./formato";

describe("formato", () => {
  it("moneda en quetzales con 2 decimales", () => {
    expect(moneda("112400")).toMatch(/^Q 112.400,00$|^Q 112,400\.00$/);
    expect(moneda(null)).toBe("—");
    expect(moneda("")).toBe("—");
  });
  it("fecha dd/mm/aaaa sin corrimiento de zona horaria", () => {
    expect(fecha("2025-02-28")).toBe("28/02/2025");
    expect(fecha("2025-01-01T00:00:00Z")).toBe("01/01/2025");
    expect(fecha(null)).toBe("—");
  });
});
