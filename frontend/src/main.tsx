import "./index.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";

import { rutas } from "./rutas";

const clienteConsultas = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: 1 } },
});

const raiz = document.getElementById("root");
if (!raiz) throw new Error("No se encontró el elemento #root");

createRoot(raiz).render(
  <StrictMode>
    <QueryClientProvider client={clienteConsultas}>
      <RouterProvider router={createBrowserRouter(rutas)} />
    </QueryClientProvider>
  </StrictMode>,
);
