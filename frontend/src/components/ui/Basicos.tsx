import { AlertTriangle, CheckCircle2, Inbox, Info, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

import { Boton } from "./Boton";

export function Seccion({
  titulo,
  descripcion,
  acciones,
  children,
}: {
  titulo: string;
  descripcion?: string;
  acciones?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <header className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 px-4 py-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">{titulo}</h2>
          {descripcion && <p className="text-sm text-slate-500">{descripcion}</p>}
        </div>
        {acciones}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}

type Tono = "neutro" | "exito" | "alerta" | "peligro" | "info";

const TONOS: Record<Tono, string> = {
  neutro: "bg-slate-100 text-slate-700",
  exito: "bg-acento-suave text-acento",
  alerta: "bg-alerta-suave text-alerta",
  peligro: "bg-peligro-suave text-peligro",
  info: "bg-primario-suave text-primario",
};

export function Insignia({ tono = "neutro", children }: { tono?: Tono; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${TONOS[tono]}`}
    >
      {children}
    </span>
  );
}

export function Alerta({
  tono = "info",
  titulo,
  children,
}: {
  tono?: Tono;
  titulo?: string;
  children?: ReactNode;
}) {
  const Icono =
    tono === "peligro" || tono === "alerta"
      ? AlertTriangle
      : tono === "exito"
        ? CheckCircle2
        : Info;
  return (
    <div
      role={tono === "peligro" ? "alert" : "status"}
      className={`flex gap-3 rounded-md p-3 text-sm ${TONOS[tono]}`}
    >
      <Icono className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div>
        {titulo && <p className="font-semibold">{titulo}</p>}
        {children}
      </div>
    </div>
  );
}

export function Cargando({ filas = 4 }: { filas?: number }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label="Cargando">
      {Array.from({ length: filas }, (_, i) => (
        <div key={i} className="h-8 animate-pulse rounded bg-slate-100" />
      ))}
    </div>
  );
}

export function Vacio({ mensaje, accion }: { mensaje: string; accion?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-center text-slate-500">
      <Inbox className="size-10 text-slate-300" aria-hidden />
      <p>{mensaje}</p>
      {accion}
    </div>
  );
}

export function ErrorVista({ error, reintentar }: { error: unknown; reintentar?: () => void }) {
  const mensaje = error instanceof Error ? error.message : "Ocurrió un error inesperado";
  return (
    <div className="space-y-3">
      <Alerta tono="peligro" titulo="No se pudo cargar la información">
        {mensaje}
      </Alerta>
      {reintentar && (
        <Boton
          variante="secundario"
          icono={<RefreshCw className="size-4" aria-hidden />}
          onClick={reintentar}
        >
          Reintentar
        </Boton>
      )}
    </div>
  );
}

export function Dato({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{etiqueta}</dt>
      <dd className="mt-0.5 text-sm text-slate-900">{children}</dd>
    </div>
  );
}
