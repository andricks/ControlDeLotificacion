/** Clases compartidas (Tailwind) para mantener un solo estilo en toda la app. */

export function claseInput(conError: boolean): string {
  return [
    "block w-full rounded-md border bg-white px-3 py-2 text-sm shadow-sm",
    "placeholder:text-slate-400 focus:outline-none focus:ring-2",
    "disabled:cursor-not-allowed disabled:bg-slate-100",
    conError
      ? "border-peligro focus:ring-peligro/30"
      : "border-slate-300 focus:border-primario focus:ring-primario/20",
  ].join(" ");
}

export const claseTabla = "min-w-full divide-y divide-slate-200 text-sm";
export const claseTh =
  "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600";
export const claseTd = "px-3 py-2 align-top";
