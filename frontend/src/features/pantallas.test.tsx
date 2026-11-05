/** Pruebas de pantallas con la API simulada (fetch falso). */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { rutas } from "../rutas";

const USUARIO_ADMIN = {
  id: "u1",
  correo: "dueno@gmail.com",
  nombre: "Dueño Prueba",
  foto: null,
  rol: "admin",
  activo: true,
  ultimo_acceso: "2026-11-03T15:00:00Z",
  creado_en: "2026-11-01T15:00:00Z",
};

type Respuesta = { status?: number; body: unknown };
let respuestas: Record<string, Respuesta>;
let llamadas: { url: string; metodo: string; cuerpo: unknown }[];

beforeEach(() => {
  llamadas = [];
  respuestas = {
    "GET /api/v1/salud": { body: { estado: "ok", base_datos: "conectada" } },
    "GET /api/v1/auth/yo": { body: USUARIO_ADMIN },
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, opciones?: RequestInit) => {
      const metodo = opciones?.method ?? "GET";
      const ruta = url.split("?")[0];
      llamadas.push({
        url,
        metodo,
        cuerpo: opciones?.body ? JSON.parse(String(opciones.body)) : null,
      });
      const r = respuestas[`${metodo} ${ruta}`] ?? {
        status: 404,
        body: { detalle: "No encontrado", codigo: "NO_ENCONTRADO", campos: {} },
      };
      return new Response(JSON.stringify(r.body), {
        status: r.status ?? 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );
});

afterEach(() => vi.unstubAllGlobals());

function montar(ruta: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(rutas, { initialEntries: [ruta] });
  render(
    <QueryClientProvider client={qc}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

describe("Listado de promesas", () => {
  it("muestra estado vacío y el enlace para crear", async () => {
    respuestas["GET /api/v1/contratos"] = { body: { items: [], total: 0, pagina: 1, tamano: 20 } };
    montar("/");
    expect(await screen.findByText("Aún no hay promesas registradas.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Registrar la primera promesa" })).toHaveAttribute(
      "href",
      "/promesas/nueva",
    );
  });

  it("muestra el error si el servidor no responde", async () => {
    respuestas["GET /api/v1/contratos"] = { status: 503, body: {} };
    montar("/");
    expect(await screen.findByText("No se pudo cargar la información")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });
});

describe("Cobros y morosidad", () => {
  const resumen = {
    clientes: 3,
    morosos: 1,
    en_gracia: 0,
    por_vencer: 1,
    al_dia: 1,
    riesgo_rescision: 1,
    monto_vencido: "20438.00",
    mora_estimada: "1532.85",
  };
  const moroso = {
    contrato_id: "c1",
    numero_formateado: "00012",
    cliente_nombre: "Juan Carlos Pérez Muñoz",
    telefono: "5555-0000",
    lotificacion: "monaco",
    lote_codigo: "36-B34",
    dia_pago_mensual: 30,
    cuota_nivelada: "10219.00",
    numero_cuotas: 11,
    cuotas_pagadas: 8,
    proxima_cuota_numero: 9,
    proxima_vencimiento: "2025-10-30",
    proxima_monto: "10219.00",
    cuotas_vencidas: 2,
    dias_atraso: 45,
    monto_vencido: "20438.00",
    mora_estimada: "1532.85",
    enganche_pendiente: "0.00",
    saldo_capital: "30648.00",
    ultimo_pago: "2025-09-30",
    situacion: "moroso",
    riesgo_rescision: true,
  };

  it("muestra los morosos por defecto con su atraso y el resumen", async () => {
    respuestas["GET /api/v1/cartera"] = {
      body: {
        fecha: "2025-12-14",
        dias_gracia: 5,
        resumen,
        items: [moroso],
        total: 1,
        pagina: 1,
        tamano: 20,
      },
    };
    montar("/cobros");
    expect(await screen.findByText("Juan Carlos Pérez Muñoz")).toBeInTheDocument();
    expect(screen.getByText("2 cuotas vencidas")).toBeInTheDocument();
    expect(screen.getByText("45 días de atraso")).toBeInTheDocument();
    expect(screen.getByText("Riesgo de rescisión", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByText("Cada mes, día 30")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Registrar pago/ })).toHaveAttribute(
      "href",
      "/promesas/c1/pago",
    );
    expect(screen.getByRole("button", { name: /Morosos/ })).toHaveAttribute("aria-pressed", "true");
    const consulta = llamadas.find((l) => l.url.includes("/cartera"));
    expect(consulta?.url).toContain("situacion=moroso");
    expect(screen.getByRole("button", { name: "Descargar reporte PDF" })).toBeInTheDocument();
  });

  it("filtra por situación y avisa cuando no hay clientes", async () => {
    const usuario = userEvent.setup();
    respuestas["GET /api/v1/cartera"] = {
      body: {
        fecha: "2025-12-14",
        dias_gracia: 5,
        resumen,
        items: [],
        total: 0,
        pagina: 1,
        tamano: 20,
      },
    };
    montar("/cobros");
    expect(await screen.findByText("No hay clientes morosos.")).toBeInTheDocument();
    await usuario.click(screen.getByRole("button", { name: /Pagan esta semana/ }));
    await waitFor(() =>
      expect(llamadas.some((l) => l.url.includes("situacion=por_vencer"))).toBe(true),
    );
    expect(await screen.findByText("No hay clientes en esta situación.")).toBeInTheDocument();
  });
});

describe("Nueva promesa", () => {
  it("no envía el formulario con errores y los marca en los campos", async () => {
    const usuario = userEvent.setup();
    montar("/promesas/nueva");
    await usuario.click(await screen.findByRole("button", { name: "Guardar promesa" }));
    expect(
      await screen.findByText("Hay campos con errores. Revíselos (están marcados en rojo)."),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/DPI inválido/).length).toBeGreaterThan(0);
    expect(screen.getByText("Seleccione la lotificación")).toBeInTheDocument();
    expect(llamadas.some((l) => l.metodo === "POST" && l.url.endsWith("/contratos"))).toBe(false);
  });

  it("muestra en el campo el error que devuelve el servidor", async () => {
    const usuario = userEvent.setup();
    respuestas["POST /api/v1/contratos"] = {
      status: 409,
      body: {
        detalle: "El lote 36-B34 ya está asignado a otra promesa",
        codigo: "LOTE_NO_DISPONIBLE",
        campos: { "lote.codigo": "no_disponible" },
      },
    };
    respuestas["POST /api/v1/contratos/calcular"] = { status: 422, body: { detail: [] } };
    montar("/promesas/nueva");
    await usuario.selectOptions(await screen.findByLabelText(/^Lotificación/), "Monaco");
    await usuario.type(screen.getByLabelText(/^DPI/), "1234567892101");
    await usuario.type(
      screen.getAllByLabelText(/Nombres y apellidos/)[0]!,
      "Juan Carlos Pérez Muñoz",
    );
    await usuario.type(screen.getByLabelText(/Lote No\./), "36-B34");
    await usuario.type(screen.getByLabelText(/Área total/), "144");
    await usuario.type(screen.getByLabelText(/Precio del terreno/), "20000");
    await usuario.type(screen.getByLabelText(/Fecha de la primera cuota/), "2099-02-28");
    await usuario.click(screen.getByRole("button", { name: "Guardar promesa" }));

    await waitFor(() =>
      expect(llamadas.some((l) => l.metodo === "POST" && l.url.endsWith("/contratos"))).toBe(true),
    );
    const envio = llamadas.find((l) => l.metodo === "POST" && l.url.endsWith("/contratos"));
    expect(envio?.cuerpo).toMatchObject({
      lotificacion: "monaco",
      comprador: { dpi: "1234567892101" },
      lote: { codigo: "36-B34" },
      saldo_inicial: null,
    });
    expect(
      (await screen.findAllByText("El lote 36-B34 ya está asignado a otra promesa")).length,
    ).toBeGreaterThan(0);
    expect(screen.getByLabelText(/Lote No\./)).toHaveAttribute("aria-invalid", "true");
  });
});

describe("Inicio de sesión con Google", () => {
  it("sin sesión muestra solo la pantalla de acceso", async () => {
    respuestas["GET /api/v1/auth/yo"] = {
      status: 401,
      body: { detalle: "Inicia sesión", codigo: "NO_AUTENTICADO", campos: {} },
    };
    respuestas["GET /api/v1/auth/config"] = { body: { google_client_id: "" } };
    montar("/cobros");
    expect(await screen.findByText(/Inicia sesión con tu cuenta de Google/)).toBeInTheDocument();
    expect(await screen.findByText("Inicio de sesión no configurado")).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Principal" })).not.toBeInTheDocument();
    expect(llamadas.some((l) => l.url.includes("/cartera"))).toBe(false);
  });

  it("con sesión muestra el usuario y cierra sesión", async () => {
    respuestas["POST /api/v1/auth/salir"] = { body: {} };
    respuestas["GET /api/v1/contratos"] = { body: { items: [], total: 0, pagina: 1, tamano: 20 } };
    montar("/");
    expect(await screen.findByText("Dueño Prueba")).toBeInTheDocument();
    respuestas["GET /api/v1/auth/yo"] = { status: 401, body: { detalle: "x", codigo: "X" } };
    respuestas["GET /api/v1/auth/config"] = { body: { google_client_id: "" } };
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByText(/Inicia sesión con tu cuenta de Google/)).toBeInTheDocument();
    expect(llamadas.some((l) => l.metodo === "POST" && l.url.endsWith("/auth/salir"))).toBe(true);
  });

  it("el menú de Usuarios solo aparece para administradores", async () => {
    respuestas["GET /api/v1/auth/yo"] = { body: { ...USUARIO_ADMIN, rol: "operador" } };
    respuestas["GET /api/v1/contratos"] = { body: { items: [], total: 0, pagina: 1, tamano: 20 } };
    montar("/");
    expect(await screen.findByText("Operador")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usuarios" })).not.toBeInTheDocument();
  });
});

describe("Gestión de usuarios", () => {
  it("valida el correo y autoriza una cuenta", async () => {
    respuestas["GET /api/v1/usuarios"] = { body: [USUARIO_ADMIN] };
    respuestas["POST /api/v1/usuarios"] = {
      status: 201,
      body: { ...USUARIO_ADMIN, id: "u2", correo: "cajera@gmail.com", nombre: "", rol: "operador" },
    };
    montar("/usuarios");
    expect(await screen.findByText("dueno@gmail.com")).toBeInTheDocument();

    const correo = screen.getByLabelText(/Correo de la cuenta de Google/);
    await userEvent.type(correo, "no-es-correo");
    await userEvent.click(screen.getByRole("button", { name: "Autorizar" }));
    expect(await screen.findByText("Correo no válido")).toBeInTheDocument();
    expect(llamadas.some((l) => l.metodo === "POST")).toBe(false);

    await userEvent.clear(correo);
    await userEvent.type(correo, "Cajera@Gmail.com");
    await userEvent.selectOptions(screen.getByLabelText("Rol"), "operador");
    await userEvent.click(screen.getByRole("button", { name: "Autorizar" }));
    await waitFor(() =>
      expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({
        correo: "cajera@gmail.com",
        rol: "operador",
      }),
    );
    expect(await screen.findByText(/Cuenta autorizada/)).toBeInTheDocument();
  });
});
