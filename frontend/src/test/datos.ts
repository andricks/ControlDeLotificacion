import { valoresIniciales, type FormularioPromesa } from "../features/contratos/esquemas";

/** Formulario completo con datos ficticios y los montos del contrato real. */
export function formularioEjemplo(): FormularioPromesa {
  const v = valoresIniciales("2025-01-22");
  v.lotificacion = "tablon_campestre2";
  v.comprador.nombres_apellidos = "Juan Carlos Pérez Muñoz";
  v.comprador.dpi = "1234567892101";
  v.comprador.nit = "1234567-9";
  v.lote = {
    codigo: "36-b34",
    area_m2: "144",
    finca: "",
    folio: "",
    libro: "",
    libro_de: "Jalapa",
  };
  v.condiciones = {
    ...v.condiciones,
    precio_terreno: "20000",
    mejoras: "102400",
    enganche: "10000",
    enganche_fraccionado: [{ fecha: "2025-01-22", monto: "10000" }],
    plazo_anios: "1",
    numero_cuotas: "11",
    fecha_primera_cuota: "2025-02-28",
    dia_pago_mensual: "30",
  };
  return v;
}
