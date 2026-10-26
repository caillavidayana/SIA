import { SigtaModal } from './swal'
export async function mostrarErrorRegla(datos) {
  if (!['R01','R02','R09'].includes(datos?.regla)) return false
  await SigtaModal.fire({title:datos.titulo||'Revise la operación',text:datos.detalle,icon:datos.regla==='R02'?'info':'warning',confirmButtonText:datos.regla==='R02'?'Agregar cotizaciones':'Entendido'})
  return true
}
