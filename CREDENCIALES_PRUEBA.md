# Credenciales de prueba de SIGTA

> **Uso exclusivo para desarrollo local.** Este archivo contiene contraseñas en texto visible. No debe incluirse en un repositorio público ni utilizarse en producción.

> **Todas las cuentas usan la misma contraseña: `Hola123*`** — así no hay que volver aquí cada vez que se cambia de rol durante las pruebas. Cumple la política del sistema (mayúscula, minúscula, número, carácter especial y 8 caracteres), por lo que también sirve al fijarla de nuevo en el cambio obligatorio.

### Administración

| Rol | Correo | Contraseña | Ruta principal |
|---|---|---|---|
| Admin (superuser) | `superuser@emi.edu.bo` | `Hola123*` | `/superuser/dashboard` |
| Director | `admin@emi.edu.bo` | `Hola123*` | `/admin/dashboard` |

### Jefes

| Rol | Correo | Contraseña | Ruta principal |
|---|---|---|---|
| Jefe UTIC  | `jefe.utic@emi.edu.bo` | `Hola123*` | `/jefe-utic/dashboard` |
| Jefe Mantenimiento | `servicios.generales@emi.edu.bo` | `Hola123*` | `/servicios-generales/dashboard` |

### Técnicos

| Dependencia | Rol | Correo | Contraseña | Ruta principal |
|---|---|---|---|---|
| — | DAF (Dirección de Asuntos Financieros) | `daf@emi.edu.bo` | `Hola123*` | `/daf/dashboard` |
| — | Técnico de Almacén y Compras | `almacen@emi.edu.bo` | `Hola123*` | `/almacen/dashboard` |
| — | Técnico de Tesorería | `tesoreria@emi.edu.bo` | `Hola123*` | `/tesoreria/dashboard` |
| Jefe UTIC | Técnico de Soporte Técnico | `especialista@emi.edu.bo` | `Hola123*` | `/especialista/dashboard` |
| Jefe UTIC | Técnico de Soporte Técnico | `especialista2p@emi.edu.bo'

| Jefe Mantenimiento | Técnico de Mantenimiento | `auxiliar.sg@emi.edu.bo` | `Hola123*` | `/auxiliar-servicios-generales/dashboard` |

### Usuario

| Rol | Correo | Contraseña | Ruta principal |
|---|---|---|---|
| Usuario | `solicitante@emi.edu.bo` | `Hola123*` | `/usuario/dashboard` |

### Cuenta para probar HU-01 / HU-02 (cambio obligatorio de contraseña)

| Rol | Correo | Contraseña temporal | Comportamiento esperado |
|---|---|---|---|
| Solicitante (recién creado) | `nuevo.ingreso@emi.edu.bo` | `Hola123*` | `must_change_password=true`: al iniciar sesión, el sistema exige cambiar la contraseña antes de permitir cualquier otra acción (bloqueado también en el backend, no solo en el redireccionamiento del frontend). |

## Observaciones

- Las cuentas están activas en la base de datos local `backend/db.sqlite3`. Se generan/actualizan con `python manage.py cargar_usuarios_prueba` (además de `cargar_permisos_sigta` para roles y permisos).
- Las contraseñas fueron configuradas para pruebas y deben cambiarse antes de una implementación real.
- Si la base de datos no se copia a otra instalación, estas cuentas no existirán automáticamente hasta correr los comandos de carga.
- Las contraseñas se almacenan con Argon2id (no en texto plano); este archivo es solo para pruebas locales.
