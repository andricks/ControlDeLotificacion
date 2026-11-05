/** Cliente HTTP de la API con errores en español y descarga de PDFs. */

const BASE = "/api/v1";

export class ErrorApi extends Error {
  readonly status: number;
  readonly codigo: string;
  /** Errores por campo: "comprador.dpi" → mensaje. */
  readonly campos: Record<string, string>;

  constructor(
    status: number,
    mensaje: string,
    codigo = "ERROR",
    campos: Record<string, string> = {},
  ) {
    super(mensaje);
    this.status = status;
    this.codigo = codigo;
    this.campos = campos;
  }
}

interface ErrorValidacionFastApi {
  loc: (string | number)[];
  msg: string;
}

function limpiarMensaje(msg: string): string {
  return msg.replace(/^Value error, /, "");
}

async function leerError(respuesta: Response): Promise<ErrorApi> {
  let cuerpo: unknown = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    // respuesta sin JSON
  }
  if (cuerpo && typeof cuerpo === "object") {
    const c = cuerpo as Record<string, unknown>;
    // Errores de dominio del backend: {detalle, codigo, campos}
    if (typeof c.detalle === "string") {
      const campos: Record<string, string> = {};
      for (const clave of Object.keys((c.campos as Record<string, string>) ?? {})) {
        campos[clave] = c.detalle;
      }
      return new ErrorApi(respuesta.status, c.detalle, String(c.codigo ?? "ERROR"), campos);
    }
    // Validación de FastAPI/Pydantic: {detail: [{loc, msg}]}
    if (Array.isArray(c.detail)) {
      const campos: Record<string, string> = {};
      const errores = c.detail as ErrorValidacionFastApi[];
      for (const e of errores) {
        const ruta = e.loc.filter((p) => p !== "body" && p !== "query").join(".");
        campos[ruta || "_"] = limpiarMensaje(e.msg);
      }
      const primero = errores[0] ? limpiarMensaje(errores[0].msg) : "Datos inválidos";
      return new ErrorApi(respuesta.status, `Revise los datos: ${primero}`, "VALIDACION", campos);
    }
  }
  const mensajes: Record<number, string> = {
    404: "No encontrado",
    500: "Error interno del servidor",
    502: "El servidor no está disponible",
    503: "Servicio no disponible (¿base de datos conectada?)",
  };
  return new ErrorApi(respuesta.status, mensajes[respuesta.status] ?? `Error ${respuesta.status}`);
}

async function solicitar<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, {
      ...opciones,
      headers: { "Content-Type": "application/json", ...opciones.headers },
    });
  } catch {
    throw new ErrorApi(0, "No se pudo conectar con el servidor. ¿Está encendido el backend?");
  }
  if (!respuesta.ok) {
    if (respuesta.status === 401 && !ruta.startsWith("/auth/")) avisarSesionExpirada();
    throw await leerError(respuesta);
  }
  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

/** Evento global: la cookie de sesión expiró o fue revocada → volver a la pantalla de acceso. */
export const EVENTO_SESION_EXPIRADA = "sesion-expirada";

function avisarSesionExpirada(): void {
  window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA));
}

export const api = {
  get: <T>(ruta: string, params?: Record<string, string | number | undefined | null>) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params ?? {})) {
      if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
    }
    const sufijo = qs.toString() ? `?${qs}` : "";
    return solicitar<T>(`${ruta}${sufijo}`);
  },
  post: <T>(ruta: string, cuerpo: unknown) =>
    solicitar<T>(ruta, { method: "POST", body: JSON.stringify(cuerpo) }),
  patch: <T>(ruta: string, cuerpo: unknown) =>
    solicitar<T>(ruta, { method: "PATCH", body: JSON.stringify(cuerpo) }),
};

function nombreDesdeCabecera(cabecera: string | null, respaldo: string): string {
  const coincide = cabecera?.match(/filename="?([^";]+)"?/i);
  return coincide?.[1] ?? respaldo;
}

/** Descarga un PDF de la API y lo guarda con el nombre que indica el servidor. */
export async function descargarPdf(ruta: string, nombreRespaldo: string): Promise<void> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`${BASE}${ruta}`);
  } catch {
    throw new ErrorApi(0, "No se pudo conectar con el servidor");
  }
  if (!respuesta.ok) {
    if (respuesta.status === 401) avisarSesionExpirada();
    throw await leerError(respuesta);
  }
  const blob = await respuesta.blob();
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreDesdeCabecera(
    respuesta.headers.get("Content-Disposition"),
    nombreRespaldo,
  );
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}
