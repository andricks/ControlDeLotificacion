import { createContext, useContext } from "react";

import type { UsuarioLeer } from "../../api/tipos";

export const ContextoUsuario = createContext<UsuarioLeer | null>(null);

/** Usuario actual dentro de las pantallas protegidas por `RequiereSesion`. */
export function useUsuarioActual(): UsuarioLeer {
  const usuario = useContext(ContextoUsuario);
  if (!usuario) throw new Error("useUsuarioActual se usó fuera de RequiereSesion");
  return usuario;
}
