// 10. CONTRASENAS (R10): el minimo de caracteres llega del backend.
// Cambiar OPTIONS.min_length en backend/config/settings.py y reiniciar Django.
// No introducir otro minimo fijo en este archivo o en las pantallas.
import { ref, onMounted } from 'vue'
export function usarPoliticaPassword() {
  const minimo=ref(null), errorPolitica=ref('')
  onMounted(async()=>{
    try{
      const r=await fetch('/api/configuracion-publica/')
      const d=await r.json()
      if(!r.ok||!Number.isInteger(d.password_min_length))throw new Error('No se pudo consultar la política vigente de contraseñas.')
      minimo.value=d.password_min_length
    }catch(e){errorPolitica.value=e.message}
  })
  return {minimo,errorPolitica}
}
