/** Tipos de la API (espejo de los schemas Pydantic). Los montos llegan como string. */

export type Dinero = string;

export interface Pagina<T> {
  items: T[];
  total: number;
  pagina: number;
  tamano: number;
}

export interface Trabajo {
  empresa?: string | null;
  direccion?: string | null;
  telefono?: string | null;
  puesto?: string | null;
  tiempo_trabajo?: string | null;
  ingreso_mensual?: Dinero | null;
  otros_ingresos?: Dinero | null;
}

export interface Persona {
  nombres_apellidos: string;
  dpi?: string | null;
  direccion?: string | null;
  telefono?: string | null;
  email?: string | null;
  fecha_nacimiento?: string | null;
  nacionalidad?: string;
  profesion_actividad?: string | null;
}

export interface Cliente extends Persona {
  dpi: string;
  nit?: string | null;
  estado_civil?: string | null;
  num_dependientes?: number;
  trabajo?: Trabajo;
}

export interface ClienteLeer extends Cliente {
  id: string;
}

export type Lotificacion = "monaco" | "finca_el_ensueno" | "tablon_campestre2";

export interface Lote {
  codigo: string;
  area_m2: Dinero;
  finca?: string | null;
  folio?: string | null;
  libro?: string | null;
  libro_de?: string | null;
}

export interface CondicionesEntrada {
  precio_terreno: Dinero;
  mejoras: Dinero;
  enganche: Dinero;
  otros_descuentos: Dinero;
  enganche_fraccionado: { fecha: string; monto: Dinero }[];
  plazo_anios: number;
  numero_cuotas?: number | null;
  tasa_interes_anual_pct: Dinero;
  cuota_nivelada?: Dinero | null;
  fecha_primera_cuota: string;
  dia_pago_mensual?: number | null;
  otras_condiciones?: string | null;
}

export interface CondicionesContrato extends CondicionesEntrada {
  total: Dinero;
  saldo_a_pagar: Dinero;
  numero_cuotas: number;
  cuota_nivelada: Dinero;
  dia_pago_mensual: number;
}

export interface CuotaPlan {
  numero: number;
  vencimiento: string;
  capital: Dinero;
  interes: Dinero;
  cuota: Dinero;
  saldo_despues: Dinero;
  capital_pagado: Dinero;
  interes_pagado: Dinero;
  estado: "pendiente" | "parcial" | "pagada";
}

export interface SaldoInicial {
  saldo_capital: Dinero;
  cuotas_pagadas: number;
  fecha_corte: string;
  nota?: string | null;
}

export interface ContratoCrear {
  fecha_firma: string;
  lotificacion: Lotificacion;
  comprador: Cliente;
  conyuge_gestor: Persona | null;
  dependientes: { nombre: string; edad: number | null; dpi: string | null }[];
  lote: Lote;
  condiciones: CondicionesEntrada;
  notario: null;
  saldo_inicial: SaldoInicial | null;
}

export type EstadoContrato = "vigente" | "cancelado_total" | "desistido" | "anulado";

export interface CalculoLeer {
  condiciones: CondicionesContrato;
  plan_cuotas: CuotaPlan[];
}

export interface ContratoLeer {
  id: string;
  numero: number;
  numero_formateado: string;
  fecha_firma: string;
  /** null en promesas creadas antes de poder elegir lotificación. */
  lotificacion: Lotificacion | null;
  cliente_id: string;
  lote_id: string;
  comprador: Cliente;
  conyuge_gestor: Persona | null;
  lote: Lote;
  condiciones: CondicionesContrato;
  plan_cuotas: CuotaPlan[];
  saldo_inicial: SaldoInicial | null;
  total_pagado_enganche: Dinero;
  total_pagado_capital: Dinero;
  saldo_capital: Dinero;
  estado: EstadoContrato;
  creado_en: string;
}

export interface ContratoResumen {
  id: string;
  numero: number;
  numero_formateado: string;
  fecha_firma: string;
  comprador_nombre: string;
  comprador_dpi: string;
  lotificacion: Lotificacion | null;
  lote_codigo: string;
  total: Dinero;
  saldo_capital: Dinero;
  estado: EstadoContrato;
}

export type Concepto = "enganche" | "cuota" | "abono_capital" | "otros";

export interface Desglose {
  enganche: Dinero;
  capital: Dinero;
  intereses: Dinero;
  recargo_mora: Dinero;
  abono_capital: Dinero;
  otros: Dinero;
}

export interface ReciboCrear {
  contrato_id: string;
  fecha: string;
  concepto: Concepto;
  cuota_numero: number | null;
  desglose: Desglose;
  boletas: { numero: string; cuenta: string | null }[];
  numero_fel: string | null;
  observaciones: string | null;
}

export interface ReciboLeer {
  id: string;
  numero: number;
  numero_formateado: string;
  numero_fel: string | null;
  fecha: string;
  contrato_id: string;
  contrato_numero: number;
  cliente_nombre: string;
  lotes_texto: string;
  concepto: Concepto;
  cuota_numero: number | null;
  cuota_mes: string | null;
  desglose: Desglose;
  total: Dinero;
  total_en_letras: string;
  saldo_anterior: Dinero;
  saldo_actual: Dinero;
  boletas: { numero: string; cuenta: string | null }[];
  observaciones: string | null;
  anulado: boolean;
  motivo_anulacion: string | null;
}

export interface EliminadoLeer {
  id: string;
  numero_formateado: string;
  recibos_eliminados: number;
}

export type SituacionPago = "moroso" | "en_gracia" | "por_vencer" | "al_dia";

export interface ClienteCartera {
  contrato_id: string;
  numero_formateado: string;
  cliente_nombre: string;
  telefono: string | null;
  lotificacion: Lotificacion | null;
  lote_codigo: string;
  dia_pago_mensual: number;
  cuota_nivelada: Dinero;
  numero_cuotas: number;
  cuotas_pagadas: number;
  proxima_cuota_numero: number | null;
  proxima_vencimiento: string | null;
  proxima_monto: Dinero;
  cuotas_vencidas: number;
  dias_atraso: number;
  monto_vencido: Dinero;
  mora_estimada: Dinero;
  enganche_pendiente: Dinero;
  saldo_capital: Dinero;
  ultimo_pago: string | null;
  situacion: SituacionPago;
  riesgo_rescision: boolean;
}

export interface ResumenCartera {
  clientes: number;
  morosos: number;
  en_gracia: number;
  por_vencer: number;
  al_dia: number;
  riesgo_rescision: number;
  monto_vencido: Dinero;
  mora_estimada: Dinero;
}

export interface CarteraLeer extends Pagina<ClienteCartera> {
  fecha: string;
  dias_gracia: number;
  resumen: ResumenCartera;
}

export interface SugerenciaPago {
  contrato_id: string;
  fecha: string;
  saldo_capital: Dinero;
  enganche_pendiente: Dinero;
  cuota_numero: number | null;
  cuota_mes: string | null;
  vencimiento: string | null;
  capital: Dinero;
  intereses: Dinero;
  dias_atraso: number;
  recargo_mora: Dinero;
  total_sugerido: Dinero;
  cuotas_vencidas: number;
}

export type Rol = "admin" | "operador" | "consulta";

export interface UsuarioLeer {
  id: string;
  correo: string;
  nombre: string;
  foto: string | null;
  rol: Rol;
  activo: boolean;
  ultimo_acceso: string | null;
  creado_en: string;
}
