import { FileDown } from "lucide-react";
import { useState } from "react";

import { descargarPdf } from "../../api/cliente";
import { Boton } from "./Boton";

/** Descarga un PDF de la API mostrando estado de carga y error. */
export function BotonPdf({
  ruta,
  nombre,
  texto,
  pequeno = false,
  variante = "secundario",
}: {
  ruta: string;
  nombre: string;
  texto: string;
  pequeno?: boolean;
  variante?: "primario" | "secundario" | "fantasma";
}) {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function descargar() {
    setCargando(true);
    setError(null);
    try {
      await descargarPdf(ruta, nombre);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo descargar");
    } finally {
      setCargando(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start">
      <Boton
        variante={variante}
        pequeno={pequeno}
        cargando={cargando}
        icono={<FileDown className="size-4" aria-hidden />}
        onClick={descargar}
      >
        {texto}
      </Boton>
      {error && (
        <span role="alert" className="mt-1 text-xs text-peligro">
          {error}
        </span>
      )}
    </span>
  );
}
