import { z } from "zod";

export const ROLES = [
  { valor: "consulta", texto: "Consulta (solo ver y descargar)" },
  { valor: "operador", texto: "Operador (registrar promesas y pagos)" },
  { valor: "admin", texto: "Administrador (todo, incluso usuarios)" },
] as const;

export const NOMBRE_ROL: Record<string, string> = {
  consulta: "Consulta",
  operador: "Operador",
  admin: "Administrador",
};

export const esquemaAutorizar = z.object({
  correo: z
    .string()
    .trim()
    .min(1, "Escribe el correo de la cuenta de Google")
    .max(150, "Correo demasiado largo")
    .email("Correo no válido")
    .transform((v) => v.toLowerCase()),
  rol: z.enum(["admin", "operador", "consulta"], { message: "Elige un rol" }),
});

export type FormularioAutorizar = z.input<typeof esquemaAutorizar>;
export type DatosAutorizar = z.output<typeof esquemaAutorizar>;
