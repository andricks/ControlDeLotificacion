import { useState, type ReactNode } from "react";

import { Alerta } from "../../components/ui/Basicos";
import { Boton } from "../../components/ui/Boton";
import { AreaTexto } from "../../components/ui/Campos";
import { Dialogo } from "../../components/ui/Dialogo";
import { esquemaEliminar } from "./esquemas";

/** Confirmación de borrado con motivo obligatorio (validado con Zod). */
export function DialogoEliminar({
  abierto,
  titulo,
  children,
  cargando,
  error,
  alCerrar,
  alConfirmar,
}: {
  abierto: boolean;
  titulo: string;
  children: ReactNode;
  cargando: boolean;
  error: Error | null;
  alCerrar: () => void;
  alConfirmar: (motivo: string) => Promise<void>;
}) {
  const [motivo, setMotivo] = useState("");
  const [tocado, setTocado] = useState(false);
  const validacion = esquemaEliminar.safeParse({ motivo });
  const mensaje = validacion.success ? undefined : validacion.error.issues[0]?.message;

  function cerrar() {
    setMotivo("");
    setTocado(false);
    alCerrar();
  }

  async function confirmar() {
    setTocado(true);
    if (!validacion.success) return;
    try {
      await alConfirmar(validacion.data.motivo);
      setMotivo("");
      setTocado(false);
    } catch {
      // el error se muestra en el diálogo
    }
  }

  return (
    <Dialogo abierto={abierto} titulo={titulo} alCerrar={cerrar}>
      <div className="space-y-3">
        <div className="text-sm text-slate-600">{children}</div>
        <AreaTexto
          etiqueta="Motivo del borrado"
          obligatorio
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          onBlur={() => setTocado(true)}
          error={tocado || motivo.length > 0 ? mensaje : undefined}
        />
        {error && <Alerta tono="peligro">{error.message}</Alerta>}
        <div className="flex justify-end gap-2">
          <Boton variante="secundario" onClick={cerrar}>
            Cancelar
          </Boton>
          <Boton variante="peligro" cargando={cargando} onClick={() => void confirmar()}>
            Borrar
          </Boton>
        </div>
      </div>
    </Dialogo>
  );
}
