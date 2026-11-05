/** Validaciones de documentos guatemaltecos (mismas reglas que el backend). */

export function normalizarNit(nit: string): string {
  return nit.replace(/[\s-]/g, "").toUpperCase();
}

export function nitValido(valor: string): boolean {
  const nit = normalizarNit(valor);
  if (nit === "CF") return true;
  if (nit.length < 2 || !/^\d+$/.test(nit.slice(0, -1))) return false;
  const cuerpo = nit.slice(0, -1);
  const verificador = nit.slice(-1);
  let suma = 0;
  for (let i = 0; i < cuerpo.length; i++) {
    suma += Number(cuerpo[i]) * (cuerpo.length + 1 - i);
  }
  const esperado = (11 - (suma % 11)) % 11;
  return verificador === (esperado === 10 ? "K" : String(esperado));
}

export function normalizarDpi(dpi: string): string {
  return dpi.replace(/\s/g, "");
}

/** DPI/CUI: 8 dígitos correlativo + verificador + 2 departamento (01-22) + 2 municipio. */
export function dpiValido(valor: string): boolean {
  const dpi = normalizarDpi(valor);
  if (!/^\d{13}$/.test(dpi)) return false;
  const departamento = Number(dpi.slice(9, 11));
  const municipio = Number(dpi.slice(11, 13));
  if (departamento < 1 || departamento > 22 || municipio < 1) return false;
  let suma = 0;
  for (let i = 0; i < 8; i++) suma += Number(dpi[i]) * (i + 2);
  return suma % 11 === Number(dpi[8]);
}

/** Monto con máximo 2 decimales, sin separadores de miles: "1234.56". */
export const PATRON_MONTO = /^\d{1,12}(\.\d{1,2})?$/;

/** Convierte "1,234.5" o "1234.50" a centavos enteros (evita errores de punto flotante). */
export function aCentavos(valor: string | undefined | null): number {
  const limpio = (valor ?? "").replace(/,/g, "").trim();
  if (!limpio || !PATRON_MONTO.test(limpio)) return 0;
  const [enteros = "0", decimales = ""] = limpio.split(".");
  return Number(enteros) * 100 + Number(decimales.padEnd(2, "0"));
}

export function deCentavos(centavos: number): string {
  const signo = centavos < 0 ? "-" : "";
  const abs = Math.abs(centavos);
  return `${signo}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}
