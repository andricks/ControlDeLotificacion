import {
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type Ref,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

import { claseInput } from "../../lib/estilos";

interface Envoltura {
  etiqueta: string;
  error?: string;
  ayuda?: string;
  obligatorio?: boolean;
  className?: string;
}

function Marco({
  etiqueta,
  error,
  ayuda,
  obligatorio,
  className = "",
  id,
  children,
}: Envoltura & { id: string; children: ReactNode }) {
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {etiqueta}
        {obligatorio && (
          <span className="text-peligro" aria-hidden>
            {" "}
            *
          </span>
        )}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} role="alert" className="mt-1 text-xs text-peligro">
          {error}
        </p>
      ) : ayuda ? (
        <p id={`${id}-ayuda`} className="mt-1 text-xs text-slate-500">
          {ayuda}
        </p>
      ) : null}
    </div>
  );
}

type PropsEntrada = Envoltura &
  Omit<InputHTMLAttributes<HTMLInputElement>, "className"> & { ref?: Ref<HTMLInputElement> };

export function Entrada({
  etiqueta,
  error,
  ayuda,
  obligatorio,
  className,
  ref,
  ...input
}: PropsEntrada) {
  const id = useId();
  return (
    <Marco
      id={id}
      etiqueta={etiqueta}
      error={error}
      ayuda={ayuda}
      obligatorio={obligatorio}
      className={className}
    >
      <input
        id={id}
        ref={ref}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : ayuda ? `${id}-ayuda` : undefined}
        className={claseInput(Boolean(error))}
        {...input}
      />
    </Marco>
  );
}

/** Entrada para montos en quetzales (texto con teclado numérico, alineado a la derecha). */
export function EntradaMonto(props: PropsEntrada) {
  return <Entrada inputMode="decimal" placeholder="0.00" autoComplete="off" {...props} />;
}

type PropsSeleccion = Envoltura &
  Omit<SelectHTMLAttributes<HTMLSelectElement>, "className"> & {
    ref?: Ref<HTMLSelectElement>;
    opciones: { valor: string; texto: string }[];
  };

export function Seleccion({
  etiqueta,
  error,
  ayuda,
  obligatorio,
  className,
  ref,
  opciones,
  ...select
}: PropsSeleccion) {
  const id = useId();
  return (
    <Marco
      id={id}
      etiqueta={etiqueta}
      error={error}
      ayuda={ayuda}
      obligatorio={obligatorio}
      className={className}
    >
      <select
        id={id}
        ref={ref}
        aria-invalid={Boolean(error)}
        className={claseInput(Boolean(error))}
        {...select}
      >
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.texto}
          </option>
        ))}
      </select>
    </Marco>
  );
}

type PropsArea = Envoltura &
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> & {
    ref?: Ref<HTMLTextAreaElement>;
  };

export function AreaTexto({
  etiqueta,
  error,
  ayuda,
  obligatorio,
  className,
  ref,
  ...area
}: PropsArea) {
  const id = useId();
  return (
    <Marco
      id={id}
      etiqueta={etiqueta}
      error={error}
      ayuda={ayuda}
      obligatorio={obligatorio}
      className={className}
    >
      <textarea
        id={id}
        ref={ref}
        rows={2}
        aria-invalid={Boolean(error)}
        className={claseInput(Boolean(error))}
        {...area}
      />
    </Marco>
  );
}

export function Casilla({
  etiqueta,
  ref,
  ...input
}: { etiqueta: string; ref?: Ref<HTMLInputElement> } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-700">
      <input
        type="checkbox"
        ref={ref}
        className="size-4 rounded border-slate-300 accent-primario"
        {...input}
      />
      {etiqueta}
    </label>
  );
}
