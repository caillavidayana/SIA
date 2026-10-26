// 2. COTIZACIONES (R02) y 3. PRIORIDAD AUTOMATICA (R03)
// Esta utilidad usa los valores de Django; no configurar importes/categorias aqui.
// Numeros: .env del proyecto. Categoria HARDWARE: backend/config/settings.py.
// R01–R03: cálculos puros; los valores vigentes llegan desde Django.
export function normalizar(texto) {
  return String(texto || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}
export function identidadProveedor(nombre, identificador = '') {
  const limpiar = v => normalizar(v).replace(/[^a-z0-9]/g, '')
  return limpiar(identificador) ? `id:${limpiar(identificador)}` : limpiar(nombre) ? `nombre:${limpiar(nombre)}` : ''
}
export function progresoCotizaciones(monto, filas, reglas) {
  const requeridas = Number(monto) > Number(reglas.umbral_cotizaciones) ? Number(reglas.cotizaciones_minimas) : 1
  const nombres = new Set(), ids = new Set()
  let actuales = 0
  for (const fila of filas) {
    if (!(fila.archivo || fila.archivo_url || fila.documento_url) || !identidadProveedor(fila.proveedor)) continue
    const nombre = identidadProveedor(fila.proveedor), id = identidadProveedor(fila.proveedor, fila.proveedor_identificador)
    if (reglas.proveedores_distintos && (nombres.has(nombre) || ids.has(id))) continue
    nombres.add(nombre); ids.add(id); actuales++
  }
  return { requeridas, actuales, faltantes: Math.max(0, requeridas - actuales) }
}
export function prioridadAutomatica(titulo, descripcion, categoria, reglas) {
  if (!reglas) return null
  if ((reglas.categorias_prioridad || []).some(c => [categoria?.codigo, categoria?.nombre, typeof categoria === 'string' ? categoria : ''].some(v => normalizar(v) === normalizar(c)))) return reglas.prioridad_automatica
  const escapar = v => v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  for (const texto of [titulo, descripcion]) {
    for (const palabra of reglas.palabras_prioridad || []) {
      const patron = normalizar(palabra).trim().split(/\s+/).map(escapar).join('\\s+')
      if (new RegExp(`(?<![\\p{L}\\p{N}_])${patron}(?![\\p{L}\\p{N}_])`, 'u').test(normalizar(texto))) return reglas.prioridad_automatica
    }
  }
  return null
}
export function mensajeCotizaciones(monto, progreso, reglas) {
  const { actuales, faltantes, requeridas } = progreso
  const contexto = Number(monto) > Number(reglas.umbral_cotizaciones) ? `El presupuesto estimado supera Bs ${Number(reglas.umbral_cotizaciones).toLocaleString('es-BO')}. ` : ''
  const cotizacion = n => n === 1 ? 'cotización' : 'cotizaciones'
  return `${contexto}Para enviar este requerimiento debe adjuntar ${requeridas} ${cotizacion(requeridas)} válida${requeridas === 1 ? '' : 's'}${reglas.proveedores_distintos ? ' de proveedores distintos' : ''}. Actualmente tiene ${actuales} ${cotizacion(actuales)} válida${actuales === 1 ? '' : 's'} y necesita agregar ${faltantes} ${cotizacion(faltantes)} adicional${faltantes === 1 ? '' : 'es'}.`
}
