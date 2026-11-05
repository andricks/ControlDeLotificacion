import { Link } from "react-router";

export function NoEncontrado() {
  return (
    <div className="py-20 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Página no encontrada</h1>
      <p className="mt-2 text-slate-500">La dirección no existe.</p>
      <Link to="/" className="mt-4 inline-block text-primario underline">
        Ir al listado de promesas
      </Link>
    </div>
  );
}
