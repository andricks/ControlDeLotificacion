import {
  type QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useEffect } from "react";

import { api, ErrorApi, EVENTO_SESION_EXPIRADA } from "../../api/cliente";
import type { UsuarioLeer } from "../../api/tipos";
import { olvidarCuentaGoogle } from "./google";

export const CLAVE_SESION = ["sesion"] as const;

/** Usuario con sesión iniciada; `null` si no hay sesión (401). */
export function useSesion() {
  return useQuery({
    queryKey: CLAVE_SESION,
    queryFn: async () => {
      try {
        return await api.get<UsuarioLeer>("/auth/yo");
      } catch (e) {
        if (e instanceof ErrorApi && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 5 * 60_000,
    retry: false,
  });
}

/** Marca "sin sesión" y descarta de memoria los datos del usuario anterior. */
function terminarSesion(qc: QueryClient): void {
  qc.setQueryData(CLAVE_SESION, null);
  qc.removeQueries({ predicate: (q) => q.queryKey[0] !== CLAVE_SESION[0] });
}

export function useConfigAuth() {
  return useQuery({
    queryKey: ["auth", "config"],
    queryFn: () => api.get<{ google_client_id: string }>("/auth/config"),
    staleTime: Infinity,
    retry: false,
  });
}

export function useLoginGoogle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (credencial: string) => api.post<UsuarioLeer>("/auth/google", { credencial }),
    onSuccess: (usuario) => qc.setQueryData(CLAVE_SESION, usuario),
  });
}

export function useCerrarSesion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<void>("/auth/salir", {}),
    onSettled: () => {
      olvidarCuentaGoogle();
      terminarSesion(qc);
    },
  });
}

/** Si cualquier petición responde 401, se vuelve a la pantalla de acceso. */
export function useEscucharSesionExpirada() {
  const qc = useQueryClient();
  useEffect(() => {
    const alExpirar = () => terminarSesion(qc);
    window.addEventListener(EVENTO_SESION_EXPIRADA, alExpirar);
    return () => window.removeEventListener(EVENTO_SESION_EXPIRADA, alExpirar);
  }, [qc]);
}
