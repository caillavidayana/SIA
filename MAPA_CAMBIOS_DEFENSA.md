# Dónde cambiar cada requerimiento

En VS Code pulsa **Ctrl + Shift + F** y busca, por ejemplo, `1. CAJA CHICA` o `3. PRIORIDAD AUTOMATICA`. El índice de los diez requerimientos está al inicio de `backend/config/settings.py`. Los mismos títulos identifican los archivos que aplican cada regla.

| Buscar | Dónde editar | Qué cambiar |
|---|---|---|
| `1. CAJA CHICA` | `.env` | `SIA_LIMITE_CAJA_CHICA=1500` para pasar de 1000 a 1500. |
| `2. COTIZACIONES` | `.env` | `SIA_UMBRAL_COTIZACIONES`, `SIA_COTIZACIONES_MINIMAS` y `SIA_PROVEEDORES_DISTINTOS`. |
| `3. PRIORIDAD AUTOMATICA` | `backend/config/settings.py` | `SIA_CATEGORIAS_PRIORIDAD`, `SIA_PALABRAS_PRIORIDAD` y `SIA_PRIORIDAD_AUTOMATICA`. |
| `4. TIEMPOS DE ATENCION` | `.env` | `SIA_SLA_ALTA_HORAS`, `SIA_SLA_MEDIA_HORAS` y `SIA_SLA_BAJA_HORAS`. |
| `5. FLUJO DE ESTADOS` | `backend/config/flujo_tickets.py` | `ESTADOS_FUNCIONALES` y `TRANSICIONES_PERMITIDAS`. Es un mapa de estados, no un importe numérico. |
| `6. REAPERTURA` | `.env` | `SIA_HORAS_REAPERTURA=10` para pasar de siete a diez horas. |
| `7. CARGA DEL TECNICO` | `.env` | `SIA_MAX_TICKETS_TECNICO=8` para pasar de cinco a ocho trabajos activos. |
| `8. APROBACION DE COMPRA` | `.env` | `SIA_REQUIERE_APROBACION_DIRECTOR=False` conserva el flujo sin Director; True reactiva el paso anterior. |
| `9. FONDO Y SALDO` | `.env` | `SIA_FONDO_MENSUAL=7000` para pasar de 5000 a 7000. |
| `10. CONTRASENAS` | `backend/config/settings.py` | `AUTH_PASSWORD_VALIDATORS` → `MinimumLengthValidator` → `OPTIONS` → `min_length`. |

## Ejemplo: Caja Chica de 1000 a 1500

En `.env` cambiar únicamente:

```dotenv
SIA_LIMITE_CAJA_CHICA=1500
```

Reiniciar Django y actualizar el navegador. Un requerimiento de 1200 deja de rechazarse por R01, pero sigue sujeto a cotizaciones, permisos y saldo. El umbral R02 sigue siendo 500 si no se modifica por separado.

No basta con editar el valor por defecto `'1000'` de `os.environ.get` en Python: el `.env` existente tiene prioridad. Las variables definidas en la terminal tienen prioridad incluso sobre `.env`.

## Ejemplo: Hardware en lugar de Red

En `backend/config/settings.py`, bajo `3. PRIORIDAD AUTOMATICA`, cambiar:

```python
SIA_CATEGORIAS_PRIORIDAD = ('HARDWARE', 'SERVIDOR', 'SERVIDORES')
```

Eso sustituye las categorías RED/REDES por HARDWARE y mantiene Servidores. El código real del catálogo es `HARDWARE`. Si solo debe aplicar a Hardware, usar `('HARDWARE',)`.

Las palabras del título y descripción son una condición **independiente**. Si tampoco debe activarse por escribir «red», cambiar también:

```python
SIA_PALABRAS_PRIORIDAD = ('hardware',)
```

Para activarla únicamente por categoría, sin palabras clave, usar `SIA_PALABRAS_PRIORIDAD = ()`. Reiniciar Django y probar con solicitudes nuevas; este cambio no reclasifica masivamente el historial.

## Ejemplo: mínimo de contraseña de 10 a 12 caracteres

En `backend/config/settings.py`, bajo `10. CONTRASENAS`, buscar el `MinimumLengthValidator` existente y cambiar solo:

```python
'OPTIONS': {
    'min_length': 12,
},
```

Reiniciar Django. Las pantallas consultan el mínimo mediante `/api/configuracion-publica/`; no hace falta introducir otro número en Vue. Los demás validadores se conservan y las contraseñas existentes no se reescriben.

## Aplicar y comprobar

Para estos cambios de valores no se requieren migraciones ni recompilar Vue. Detener el backend con Ctrl+C en su terminal y volver a iniciarlo desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 backend
```

Actualizar el navegador con Ctrl+F5. Si se cerró el frontend, iniciarlo en otra terminal con `iniciar.ps1 frontend`. Revisar `VERIFICACION_REQUISITOS_VIGENTES.md` para probar cada regla y `REQUERIMIENTOS_CONFIGURACION.md` para sus funciones y detalles.

Esta modificación añadió comentarios e instrucciones; conservó la lógica y los valores vigentes. Los comentarios frontend señalan que sus números proceden de Django para evitar configurar dos valores diferentes.
