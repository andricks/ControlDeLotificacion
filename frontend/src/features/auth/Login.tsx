import { ShieldCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Alerta, Cargando } from "../../components/ui/Basicos";
import { cargarGoogle } from "./google";
import { useConfigAuth, useLoginGoogle } from "./hooks";

/** Pantalla de acceso: el ÚNICO método es la cuenta de Google autorizada. */
export function Login() {
  const config = useConfigAuth();
  const { mutate: entrar, isPending, error } = useLoginGoogle();
  const contenedor = useRef<HTMLDivElement>(null);
  const [errorGoogle, setErrorGoogle] = useState<string | null>(null);
  const clientId = config.data?.google_client_id ?? "";

  useEffect(() => {
    if (!clientId) return;
    let cancelado = false;
    cargarGoogle()
      .then((google) => {
        if (cancelado || !contenedor.current) return;
        google.initialize({
          client_id: clientId,
          callback: (r) => entrar(r.credential),
          auto_select: false,
          cancel_on_tap_outside: true,
          context: "signin",
          ux_mode: "popup",
        });
        google.renderButton(contenedor.current, {
          theme: "filled_blue",
          size: "large",
          text: "signin_with",
          shape: "rectangular",
          locale: "es",
          width: 280,
        });
      })
      .catch((e: unknown) => {
        if (!cancelado) setErrorGoogle(e instanceof Error ? e.message : "Error con Google");
      });
    return () => {
      cancelado = true;
    };
  }, [clientId, entrar]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex size-12 items-center justify-center rounded-full bg-primario-suave">
            <ShieldCheck className="size-6 text-primario" aria-hidden />
          </div>
          <h1 className="text-lg font-semibold text-slate-900">Inmobiliaria Estrada</h1>
          <p className="text-sm text-slate-500">Sistema documental</p>
        </div>

        <p className="mb-4 text-center text-sm text-slate-600">
          Inicia sesión con tu cuenta de Google autorizada.
        </p>

        {config.isPending ? (
          <Cargando filas={1} />
        ) : config.isError ? (
          <Alerta tono="peligro" titulo="No se pudo contactar al servidor">
            {config.error.message}
          </Alerta>
        ) : !clientId ? (
          <Alerta tono="alerta" titulo="Inicio de sesión no configurado">
            Falta GOOGLE_CLIENT_ID en el archivo .env del servidor.
          </Alerta>
        ) : (
          <div className="flex min-h-11 justify-center" aria-busy={isPending}>
            <div ref={contenedor} />
          </div>
        )}

        <div className="mt-4 space-y-2">
          {isPending && (
            <p className="text-center text-sm text-slate-500" role="status">
              Verificando tu cuenta…
            </p>
          )}
          {error && (
            <Alerta tono="peligro" titulo="Acceso denegado">
              {error.message}
            </Alerta>
          )}
          {errorGoogle && <Alerta tono="peligro">{errorGoogle}</Alerta>}
        </div>
      </div>
    </main>
  );
}
