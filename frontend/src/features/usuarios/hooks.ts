import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/cliente";
import type { Rol, UsuarioLeer } from "../../api/tipos";
import type { DatosAutorizar } from "./esquemas";

const CLAVE = ["usuarios"] as const;

export function useUsuarios() {
  return useQuery({ queryKey: CLAVE, queryFn: () => api.get<UsuarioLeer[]>("/usuarios") });
}

export function useAutorizarUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datos: DatosAutorizar) => api.post<UsuarioLeer>("/usuarios", datos),
    onSuccess: () => qc.invalidateQueries({ queryKey: CLAVE }),
  });
}

export function useActualizarUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...cambios }: { id: string; rol?: Rol; activo?: boolean }) =>
      api.patch<UsuarioLeer>(`/usuarios/${id}`, cambios),
    onSuccess: () => qc.invalidateQueries({ queryKey: CLAVE }),
  });
}
