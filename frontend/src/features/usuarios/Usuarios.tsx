import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";

import { ErrorApi } from "../../api/cliente";
import type { Rol, UsuarioLeer } from "../../api/tipos";
import { Alerta, Cargando, ErrorVista, Insignia, Seccion, Vacio } from "../../components/ui/Basicos";
import { Boton } from "../../components/ui/Boton";
import { Entrada, Seleccion } from "../../components/ui/Campos";
import { claseTabla, claseTd, claseTh } from "../../lib/estilos";
import { fechaHora } from "../../lib/formato";
import { useUsuarioActual } from "../auth/contexto";
import {
  esquemaAutorizar,
  NOMBRE_ROL,
  ROLES,
  type DatosAutorizar,
  type FormularioAutorizar,
} from "./esquemas";
import { useActualizarUsuario, useAutorizarUsuario, useUsuarios } from "./hooks";

function FormularioNuevo() {
  const autorizar = useAutorizarUsuario();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormularioAutorizar, unknown, DatosAutorizar>({
    resolver: zodResolver(esquemaAutorizar),
    defaultValues: { correo: "", rol: "consulta" },
  });

  const enviar = handleSubmit((datos) =>
    autorizar.mutate(datos, { onSuccess: () => reset({ correo: "", rol: datos.rol }) }),
  );

  return (
    <form onSubmit={enviar} noValidate className="space-y-3">
      <div className="grid gap-3 md:grid-cols-[1fr_auto_auto] md:items-start">
        <Entrada
          etiqueta="Correo de la cuenta de Google"
          type="email"
          autoComplete="off"
          placeholder="persona@gmail.com"
          obligatorio
          error={errors.correo?.message}
          {...register("correo")}
        />
        <Seleccion
          etiqueta="Rol"
          opciones={[...ROLES]}
          error={errors.rol?.message}
          {...register("rol")}
        />
        <Boton
          type="submit"
          cargando={autorizar.isPending}
          icono={<UserPlus className="size-4" aria-hidden />}
          className="md:mt-6"
        >
          Autorizar
        </Boton>
      </div>
      {autorizar.error && <Alerta tono="peligro">{autorizar.error.message}</Alerta>}
      {autorizar.isSuccess && (
        <Alerta tono="exito">
          Cuenta autorizada. Ya puede entrar con el botón «Iniciar sesión con Google».
        </Alerta>
      )}
    </form>
  );
}

function FilaUsuario({ usuario, esYo }: { usuario: UsuarioLeer; esYo: boolean }) {
  const actualizar = useActualizarUsuario();
  const error = actualizar.error instanceof ErrorApi ? actualizar.error.message : null;
  return (
    <tr>
      <td className={claseTd}>
        <div className="flex items-center gap-2">
          {usuario.foto ? (
            <img
              src={usuario.foto}
              alt=""
              referrerPolicy="no-referrer"
              className="size-7 rounded-full"
            />
          ) : (
            <span className="size-7 rounded-full bg-slate-200" aria-hidden />
          )}
          <div>
            <p className="font-medium text-slate-900">
              {usuario.nombre || "Sin primer acceso"} {esYo && <Insignia tono="info">Tú</Insignia>}
            </p>
            <p className="text-xs text-slate-500">{usuario.correo}</p>
          </div>
        </div>
        {error && (
          <p role="alert" className="mt-1 text-xs text-peligro">
            {error}
          </p>
        )}
      </td>
      <td className={claseTd}>
        <label className="sr-only" htmlFor={`rol-${usuario.id}`}>
          Rol de {usuario.correo}
        </label>
        <select
          id={`rol-${usuario.id}`}
          value={usuario.rol}
          disabled={esYo || actualizar.isPending}
          onChange={(e) => actualizar.mutate({ id: usuario.id, rol: e.target.value as Rol })}
          className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm disabled:bg-slate-100"
        >
          {ROLES.map((r) => (
            <option key={r.valor} value={r.valor}>
              {NOMBRE_ROL[r.valor]}
            </option>
          ))}
        </select>
      </td>
      <td className={claseTd}>
        <Insignia tono={usuario.activo ? "exito" : "neutro"}>
          {usuario.activo ? "Activo" : "Desactivado"}
        </Insignia>
      </td>
      <td className={`${claseTd} whitespace-nowrap text-slate-600`}>
        {fechaHora(usuario.ultimo_acceso)}
      </td>
      <td className={`${claseTd} text-right`}>
        {!esYo && (
          <Boton
            pequeno
            variante={usuario.activo ? "secundario" : "fantasma"}
            cargando={actualizar.isPending}
            onClick={() => actualizar.mutate({ id: usuario.id, activo: !usuario.activo })}
          >
            {usuario.activo ? "Desactivar" : "Reactivar"}
          </Boton>
        )}
      </td>
    </tr>
  );
}

export function Usuarios() {
  const yo = useUsuarioActual();
  const usuarios = useUsuarios();

  if (yo.rol !== "admin") {
    return (
      <Alerta tono="alerta" titulo="Sin permiso">
        Solo un administrador puede gestionar los usuarios.
      </Alerta>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Usuarios</h1>
        <p className="text-sm text-slate-500">
          Solo las cuentas de Google de esta lista pueden entrar al sistema.
        </p>
      </header>

      <Seccion titulo="Autorizar una cuenta de Google">
        <FormularioNuevo />
      </Seccion>

      <Seccion titulo="Cuentas autorizadas">
        {usuarios.isPending ? (
          <Cargando />
        ) : usuarios.isError ? (
          <ErrorVista error={usuarios.error} reintentar={() => void usuarios.refetch()} />
        ) : usuarios.data.length === 0 ? (
          <Vacio mensaje="No hay cuentas autorizadas." />
        ) : (
          <div className="overflow-x-auto">
            <table className={claseTabla}>
              <thead>
                <tr>
                  <th className={claseTh}>Usuario</th>
                  <th className={claseTh}>Rol</th>
                  <th className={claseTh}>Estado</th>
                  <th className={claseTh}>Último acceso</th>
                  <th className={claseTh}>
                    <span className="sr-only">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usuarios.data.map((u) => (
                  <FilaUsuario key={u.id} usuario={u} esYo={u.id === yo.id} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Seccion>
    </div>
  );
}
