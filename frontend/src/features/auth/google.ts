/** Carga mínima de Google Identity Services (script oficial, sin dependencias npm). */

export interface RespuestaCredencial {
  credential: string;
}

interface GoogleId {
  initialize(opciones: {
    client_id: string;
    callback: (r: RespuestaCredencial) => void;
    auto_select?: boolean;
    cancel_on_tap_outside?: boolean;
    context?: "signin" | "signup" | "use";
    ux_mode?: "popup" | "redirect";
  }): void;
  renderButton(
    contenedor: HTMLElement,
    opciones: {
      theme?: "outline" | "filled_blue" | "filled_black";
      size?: "large" | "medium" | "small";
      text?: "signin_with" | "continue_with" | "signin";
      shape?: "rectangular" | "pill";
      locale?: string;
      width?: number;
    },
  ): void;
  disableAutoSelect(): void;
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}

const URL_SCRIPT = "https://accounts.google.com/gsi/client";
let carga: Promise<GoogleId> | null = null;

export function cargarGoogle(): Promise<GoogleId> {
  if (window.google?.accounts?.id) return Promise.resolve(window.google.accounts.id);
  carga ??= new Promise<GoogleId>((resolver, rechazar) => {
    const script = document.createElement("script");
    script.src = URL_SCRIPT;
    script.async = true;
    script.onload = () => {
      if (window.google?.accounts?.id) resolver(window.google.accounts.id);
      else rechazar(new Error("Google no se inicializó"));
    };
    script.onerror = () => {
      carga = null;
      rechazar(new Error("No se pudo cargar el inicio de sesión de Google"));
    };
    document.head.appendChild(script);
  });
  return carga;
}

/** Evita que Google vuelva a elegir la cuenta automáticamente tras cerrar sesión. */
export function olvidarCuentaGoogle(): void {
  window.google?.accounts?.id.disableAutoSelect();
}
