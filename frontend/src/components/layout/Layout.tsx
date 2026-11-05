import { CalendarClock, FilePlus2, FileText, LogOut, Receipt, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { useSalud } from "../../api/consultas";
import { useUsuarioActual } from "../../features/auth/contexto";
import { useCerrarSesion } from "../../features/auth/hooks";
import { NOMBRE_ROL } from "../../features/usuarios/esquemas";

const MENU = [
  { a: "/", texto: "Promesas", icono: FileText, fin: true },
  { a: "/promesas/nueva", texto: "Nueva promesa", icono: FilePlus2, fin: false },
  { a: "/recibos", texto: "Recibos", icono: Receipt, fin: false },
  { a: "/cobros", texto: "Cobros y morosidad", icono: CalendarClock, fin: false },
];
const MENU_ADMIN = { a: "/usuarios", texto: "Usuarios", icono: Users, fin: false };

function EstadoServidor() {
  const { data, isError } = useSalud();
  const conectado = data?.base_datos === "conectada";
  const texto = isError
    ? "Servidor apagado"
    : !data
      ? "Verificando…"
      : conectado
        ? "Conectado"
        : "Base de datos sin conexión";
  const color =
    isError || (data && !conectado) ? "bg-peligro" : conectado ? "bg-acento" : "bg-slate-400";
  return (
    <p className="flex items-center gap-2 text-xs text-slate-300" role="status">
      <span className={`size-2 rounded-full ${color}`} aria-hidden /> {texto}
    </p>
  );
}

function UsuarioSesion() {
  const yo = useUsuarioActual();
  const salir = useCerrarSesion();
  return (
    <div className="flex items-center gap-2 border-t border-white/10 px-4 py-3">
      {yo.foto ? (
        <img src={yo.foto} alt="" referrerPolicy="no-referrer" className="size-8 rounded-full" />
      ) : (
        <span className="size-8 rounded-full bg-white/20" aria-hidden />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium" title={yo.correo}>
          {yo.nombre || yo.correo}
        </p>
        <p className="text-xs text-slate-300">{NOMBRE_ROL[yo.rol]}</p>
      </div>
      <button
        type="button"
        onClick={() => salir.mutate()}
        disabled={salir.isPending}
        title="Cerrar sesión"
        aria-label="Cerrar sesión"
        className="rounded-md p-2 text-slate-200 hover:bg-white/10 disabled:opacity-60"
      >
        <LogOut className="size-4" aria-hidden />
      </button>
    </div>
  );
}

export function Layout() {
  const yo = useUsuarioActual();
  const menu = yo.rol === "admin" ? [...MENU, MENU_ADMIN] : MENU;
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="bg-primario text-white md:w-60 md:shrink-0">
        <div className="flex items-center justify-between gap-4 px-4 py-4 md:block">
          <div>
            <p className="text-sm font-semibold leading-tight">Inmobiliaria Estrada</p>
            <p className="text-xs text-slate-300">Sistema documental</p>
          </div>
          <div className="md:mt-3">
            <EstadoServidor />
          </div>
        </div>
        <nav
          aria-label="Principal"
          className="flex gap-1 overflow-x-auto px-2 pb-2 md:flex-col md:pb-4"
        >
          {menu.map(({ a, texto, icono: Icono, fin }) => (
            <NavLink
              key={a}
              to={a}
              end={fin}
              className={({ isActive }) =>
                `flex items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-white/15 text-white" : "text-slate-200 hover:bg-white/10"
                }`
              }
            >
              <Icono className="size-4" aria-hidden /> {texto}
            </NavLink>
          ))}
        </nav>
        <UsuarioSesion />
      </aside>
      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        <div className="mx-auto max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
