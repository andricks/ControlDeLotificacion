# ADR-003 — Inicio de sesión exclusivamente con Google

- Fecha: 2026-11-03
- Estado: aceptada

## Contexto
El sistema maneja datos personales (DPI, teléfonos) y documentos legales. Hasta ahora la API no tenía autenticación. El dueño pidió que **solo** se pueda entrar con cuenta de Google.

## Decisión
1. **Google autentica, el sistema autoriza.** El frontend usa Google Identity Services (script oficial, sin paquetes npm) y obtiene un *ID token*. El backend lo verifica con **PyJWT** contra las llaves públicas de Google (`/oauth2/v3/certs`): firma RS256, `aud` = `GOOGLE_CLIENT_ID`, `iss` de Google, `exp`, y `email_verified = true`.
2. **Lista blanca.** Solo entran correos registrados en la colección `usuarios` (activos) o listados en `ADMIN_CORREOS`. Este último **solo crea el admin inicial** si la cuenta aún no existe; después manda la colección (degradar a ese admin es definitivo). Cualquier otra cuenta de Google recibe 403 y queda en auditoría (esos registros caducan a los 90 días, índice TTL). Riesgo aceptado: quien controle un correo de `ADMIN_CORREOS` obtiene admin.
3. **Sin contraseñas ni otros métodos de acceso.** No existe login con usuario/clave.
4. **Sesión propia** en cookie `sesion`: JWT HS256 firmado con `JWT_SECRETO`, `httpOnly`, `SameSite=Strict`, `path=/api`, `Secure` si `COOKIE_SEGURA=true` (producción con HTTPS). Duración `SESION_HORAS` (8 h). El token nunca es accesible desde JavaScript.
5. En cada petición se relee el usuario y se compara `sesion_version` (incluida en el JWT): cerrar sesión, cambiar el rol o desactivar la cuenta **revoca de inmediato todas** sus sesiones, incluso cookies copiadas.
5b. Defensa CSRF adicional: middleware `OrigenPermitido` rechaza métodos no-GET con `Origin` fuera de `CORS_ORIGENES`.
5c. `ENTORNO=produccion` exige `JWT_SECRETO` fuerte, `COOKIE_SEGURA=true` y CORS solo https (si no, la API no arranca) y oculta `/docs`.
6. `google_sub` se fija en el primer acceso; si luego el mismo correo llega con otra cuenta de Google, se rechaza.
7. Roles: `admin` (todo + usuarios), `operador` (crear/registrar/anular), `consulta` (solo métodos GET). Debe quedar siempre al menos un admin activo; un admin no puede degradarse a sí mismo.
8. Límite de 10 intentos/min por IP en `/auth/google` (en memoria; suficiente para un solo proceso).

## Alternativas descartadas
- **`google-auth` + `requests`**: más dependencias para lo mismo que PyJWT (MIT) ya hace.
- **Token en `localStorage`**: expuesto a XSS. Se prefirió cookie httpOnly.
- **Flujo OAuth con redirect + client secret en backend**: innecesario; solo se necesita identidad, no acceso a APIs de Google.

## Consecuencias
- Requiere crear un *OAuth Client ID (Aplicación web)* en Google Cloud Console con orígenes JS autorizados `http://localhost` y `http://localhost:5173` (y el dominio real al desplegar).
- El limitador en memoria no se comparte entre procesos; al desplegar con varios workers, moverlo a la BD o a un proxy.
- Sin conexión a internet no se puede iniciar sesión (Google es obligatorio).
- Pendiente (revisión de seguridad, riesgo medio/bajo): `nonce` de un solo uso en el ID token; regla "último admin" sin atomicidad (carrera improbable con 1–2 admins); `/salud` público.
