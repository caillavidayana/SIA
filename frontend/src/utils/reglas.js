import { ref } from 'vue'
export const reglas = ref(null)
export async function cargarReglas() {
  const respuesta = await fetch('/api/auditoria/limite-caja-chica/', { headers: { Authorization: `Token ${localStorage.getItem('sigta_token')}` } })
  if (!respuesta.ok) throw new Error(`No se pudo consultar la configuración vigente (HTTP ${respuesta.status}).`)
  const datos = await respuesta.json()
  if (!Number.isFinite(Number(datos.limite_caja_chica)) || !Number.isFinite(Number(datos.umbral_cotizaciones)) || !Number.isInteger(datos.cotizaciones_minimas)) throw new Error('La configuración de compras no es válida.')
  reglas.value = datos
  return datos
}
