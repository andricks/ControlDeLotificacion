import type { EstadoContrato, Lotificacion } from "../api/tipos";

const formatoMoneda = new Intl.NumberFormat("es-GT", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** Los montos llegan del backend como string (Decimal): solo se formatean, no se opera. */
export function moneda(valor: string | number | null | undefined): string {
  if (valor === null || valor === undefined || valor === "") return "—";
  const n = Number(valor);
  return Number.isFinite(n) ? `Q ${formatoMoneda.format(n)}` : "—";
}

/** "2025-02-28" → "28/02/2025" sin conversiones de zona horaria. */
export function fecha(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-");
  return a && m && d ? `${d}/${m}/${a}` : "—";
}

const formatoFechaHora = new Intl.DateTimeFormat("es-GT", {
  timeZone: "America/Guatemala",
  dateStyle: "short",
  timeStyle: "short",
});

/** Instante UTC del backend → fecha y hora en Guatemala. */
export function fechaHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : formatoFechaHora.format(d);
}

export function hoyIso(): string {
  const ahora = new Date();
  const local = new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

/** Mismo catálogo que `LOTIFICACIONES` del backend (lotes/schemas.py). */
export const NOMBRE_LOTIFICACION: Record<Lotificacion, string> = {
  monaco: "Monaco",
  finca_el_ensueno: "Finca El Ensueño",
  tablon_campestre2: "Tablon Campestre2",
};

export const ETIQUETA_ESTADO_CONTRATO: Record<string, string> = {
  vigente: "Vigente",
  cancelado_total: "Pagado",
  desistido: "Desistido",
  anulado: "Anulado",
};

export const TONO_ESTADO: Record<EstadoContrato, "exito" | "info" | "alerta" | "peligro"> = {
  vigente: "info",
  cancelado_total: "exito",
  desistido: "alerta",
  anulado: "peligro",
};

export const ETIQUETA_CONCEPTO: Record<string, string> = {
  enganche: "Enganche",
  cuota: "Cuota nivelada",
  abono_capital: "Abono a capital",
  otros: "Otros",
};
