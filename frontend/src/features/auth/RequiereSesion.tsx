import type { ReactNode } from "react";

import { Cargando, ErrorVista } from "../../components/ui/Basicos";
import { ContextoUsuario } from "./contexto";
import { useEscucharSesionExpirada, useSesion } from "./hooks";
import { Login } from "./Login";

/** Protege toda la app: sin sesión de Google válida solo se ve la pantalla de acceso. */
export function RequiereSesion({ children }: { children: ReactNode }) {
  useEscucharSesionExpirada();
  const sesion = useSesion();

  if (sesion.isPending) {
    return (
      <div className="mx-auto max-w-sm px-4 py-24">
        <Cargando filas={3} />
      </div>
    );
  }
  if (sesion.isError) {
    return (
      <div className="mx-auto max-w-md px-4 py-24">
        <ErrorVista error={sesion.error} reintentar={() => void sesion.refetch()} />
      </div>
    );
  }
  if (!sesion.data) return <Login />;
  return <ContextoUsuario value={sesion.data}>{children}</ContextoUsuario>;
}
