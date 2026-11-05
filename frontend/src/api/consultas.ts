/** Hooks de TanStack Query para la API. */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./cliente";
import type {
  CalculoLeer,
  CarteraLeer,
  ClienteLeer,
  CondicionesEntrada,
  ContratoCrear,
  ContratoLeer,
  ContratoResumen,
  EliminadoLeer,
  Pagina,
  ReciboCrear,
  ReciboLeer,
  SugerenciaPago,
} from "./tipos";

export const claves = {
  contratos: ["contratos"] as const,
  contrato: (id: string) => ["contratos", id] as const,
  recibos: ["recibos"] as const,
  cartera: ["cartera"] as const,
  sugerencia: (id: string, fecha: string) => ["sugerencia", id, fecha] as const,
};

export function useSalud() {
  return useQuery({
    queryKey: ["salud"],
    queryFn: () => api.get<{ estado: string; base_datos: string }>("/salud"),
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useContratos(filtros: { buscar?: string; estado?: string; pagina: number }) {
  return useQuery({
    queryKey: [...claves.contratos, "lista", filtros],
    queryFn: () => api.get<Pagina<ContratoResumen>>("/contratos", { ...filtros, tamano: 20 }),
    placeholderData: keepPreviousData,
  });
}

export function useContrato(id: string) {
  return useQuery({
    queryKey: claves.contrato(id),
    queryFn: () => api.get<ContratoLeer>(`/contratos/${id}`),
  });
}

export function useCalculo(condiciones: CondicionesEntrada | null) {
  return useQuery({
    queryKey: ["calculo", condiciones],
    queryFn: () => api.post<CalculoLeer>("/contratos/calcular", { condiciones }),
    enabled: condiciones !== null,
    placeholderData: keepPreviousData,
    retry: false,
  });
}

export function useCrearContrato() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (datos: ContratoCrear) => api.post<ContratoLeer>("/contratos", datos),
    onSuccess: () => qc.invalidateQueries({ queryKey: claves.contratos }),
  });
}

export function buscarClientePorDpi(dpi: string) {
  return api.get<ClienteLeer>(`/clientes/por-dpi/${encodeURIComponent(dpi)}`);
}

export function useRecibos(filtros: {
  buscar?: string;
  contrato_id?: string;
  pagina: number;
  tamano?: number;
}) {
  return useQuery({
    queryKey: [...claves.recibos, filtros],
    queryFn: () => api.get<Pagina<ReciboLeer>>("/recibos", { tamano: 20, ...filtros }),
    placeholderData: keepPreviousData,
  });
}

export function useCartera(filtros: {
  situacion?: string;
  buscar?: string;
  lotificacion?: string;
  pagina: number;
}) {
  return useQuery({
    queryKey: [...claves.cartera, filtros],
    queryFn: () => api.get<CarteraLeer>("/cartera", { ...filtros, tamano: 20 }),
    placeholderData: keepPreviousData,
  });
}

export function useSugerencia(contratoId: string, fecha: string) {
  return useQuery({
    queryKey: claves.sugerencia(contratoId, fecha),
    queryFn: () =>
      api.get<SugerenciaPago>("/recibos/sugerencia", { contrato_id: contratoId, fecha }),
    enabled: /^\d{4}-\d{2}-\d{2}$/.test(fecha),
    retry: false,
  });
}

function useInvalidarPagos() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: claves.contratos });
    void qc.invalidateQueries({ queryKey: claves.recibos });
    void qc.invalidateQueries({ queryKey: claves.cartera });
    void qc.invalidateQueries({ queryKey: ["sugerencia"] });
  };
}

export function useRegistrarRecibo() {
  const invalidar = useInvalidarPagos();
  return useMutation({
    mutationFn: (datos: ReciboCrear) => api.post<ReciboLeer>("/recibos", datos),
    onSuccess: invalidar,
  });
}

export function useEliminarContrato() {
  const invalidar = useInvalidarPagos();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo: string }) =>
      api.post<EliminadoLeer>(`/contratos/${id}/eliminar`, { motivo }),
    onSuccess: invalidar,
  });
}

export function useEliminarRecibo() {
  const invalidar = useInvalidarPagos();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo: string }) =>
      api.post<ReciboLeer>(`/recibos/${id}/eliminar`, { motivo }),
    onSuccess: invalidar,
  });
}

export function useAnularRecibo() {
  const invalidar = useInvalidarPagos();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo: string }) =>
      api.post<ReciboLeer>(`/recibos/${id}/anular`, { motivo }),
    onSuccess: invalidar,
  });
}
