import type { RouteObject } from "react-router";

import { Layout } from "./components/layout/Layout";
import { RequiereSesion } from "./features/auth/RequiereSesion";
import { Cartera } from "./features/cartera/Cartera";
import { DetallePromesa } from "./features/contratos/DetallePromesa";
import { ListaPromesas } from "./features/contratos/ListaPromesas";
import { NuevaPromesa } from "./features/contratos/NuevaPromesa";
import { ListaRecibos } from "./features/recibos/ListaRecibos";
import { RegistrarPago } from "./features/recibos/RegistrarPago";
import { Usuarios } from "./features/usuarios/Usuarios";
import { NoEncontrado } from "./pages/NoEncontrado";

export const rutas: RouteObject[] = [
  {
    path: "/",
    element: (
      <RequiereSesion>
        <Layout />
      </RequiereSesion>
    ),
    children: [
      { index: true, element: <ListaPromesas /> },
      { path: "promesas/nueva", element: <NuevaPromesa /> },
      { path: "promesas/:id", element: <DetallePromesa /> },
      { path: "promesas/:id/pago", element: <RegistrarPago /> },
      { path: "recibos", element: <ListaRecibos /> },
      { path: "cobros", element: <Cartera /> },
      { path: "usuarios", element: <Usuarios /> },
      { path: "*", element: <NoEncontrado /> },
    ],
  },
];
