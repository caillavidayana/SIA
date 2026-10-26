<template>
  <section ref="seccion" class="cotizaciones-sia" aria-label="Cotizaciones y proveedores" tabindex="-1">
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <div v-for="(fila, i) in guardadasEditables" :key="`guardada-${fila.id || i}`" class="cotizacion">
      <div class="archivo"><b>✓ Guardada</b><span>{{ fila.nombre_original }}</span><a :href="fila.archivo_url" target="_blank" rel="noopener">Ver documento</a></div>
      <label>Proveedor<input v-model="fila.proveedor" :disabled="!fila.id" maxlength="180" placeholder="Nombre o razón social"></label>
      <label>Nombre de la empresa (opcional)<input v-model="fila.empresa" maxlength="180" placeholder="Empresa"></label>
      <small v-if="!fila.id">Documento histórico conservado. Adjunte nuevas cotizaciones identificadas si necesita completar el requisito.</small>
    </div>
    <div v-for="(fila, i) in nuevas" :key="fila.clave" class="cotizacion">
      <div class="archivo"><b>Por guardar</b><span>{{ fila.archivo.name }}</span><button type="button" @click="nuevas.splice(i,1)" :aria-label="`Quitar ${fila.archivo.name}`">Quitar</button></div>
      <label>Proveedor<input v-model="fila.proveedor" maxlength="180" placeholder="Nombre o razón social"></label>
      <label>Nombre de la empresa (opcional)<input v-model="fila.empresa" maxlength="180" placeholder="Empresa"></label>
    </div>
    <label class="adjuntar">Cotización / proforma<ArchivoInput ref="entrada" :multiple="ampliado" accept=".pdf,.jpg,.jpeg,.png,.webp" @change="agregar" /></label>
    <small>PDF, JPG, PNG o WEBP · hasta 10 MB por archivo. Puede guardar un borrador incompleto y continuar después.</small>
    <p v-if="ampliado && progreso?.faltantes" class="pendientes">Faltan {{ progreso.faltantes }} {{ progreso.faltantes===1?'cotización válida':'cotizaciones válidas' }}. Los archivos del mismo proveedor cuentan una sola vez.</p>
  </section>
</template>
<script setup>
// 1. CAJA CHICA (R01): modal de rechazo; valor real desde la API de Django.
// 2. COTIZACIONES (R02): pide faltantes y conserva formulario/archivos.
// CAMBIAR NUMEROS EN .env DEL BACKEND, no en los textos ni comparaciones de Vue.
// Limite=1500: SIA_LIMITE_CAJA_CHICA. Umbral=800: SIA_UMBRAL_COTIZACIONES.
// Cambiar SIA_COTIZACIONES_MINIMAS actualiza tambien el numero de faltantes.

import { computed, onMounted, ref, watch } from 'vue'
import { SigtaModal } from '../utils/swal'
import { reglas, cargarReglas } from '../utils/reglas'
import { progresoCotizaciones, mensajeCotizaciones } from '../utils/reglasCore'
const props = defineProps({ guardadas: { type: Array, default: () => [] }, monto: [String,Number], via: { type: String, default: 'CAJA_CHICA' }, expediente: [String,Number] })
defineEmits(['update:via'])
const ampliado=ref(false)
const nuevas=ref([]), guardadasEditables=ref([]), error=ref(''), seccion=ref(null), entrada=ref(null)
let secuencia=0
watch(()=>props.guardadas, filas=>{ guardadasEditables.value=filas.map(f=>({...f}));if(filas.length>1)ampliado.value=true }, { immediate:true })
watch(()=>props.expediente, ()=>{ nuevas.value=[];error.value='';ampliado.value=props.guardadas.length>1 })
const progreso=computed(()=>reglas.value ? progresoCotizaciones(props.monto,[...guardadasEditables.value,...nuevas.value],reglas.value) : null)
const dinero=v=>Number(v).toLocaleString('es-BO',{minimumFractionDigits:2,maximumFractionDigits:2})
onMounted(async()=>{try{await cargarReglas()}catch(e){error.value=e.message}})
function agregar(evento){
  error.value=''
  for(const archivo of evento.target.files||[]){
    if(!/\.(pdf|jpe?g|png|webp)$/i.test(archivo.name)||!archivo.size||archivo.size>10*1024*1024){error.value=`Revise ${archivo.name}: use un formato permitido de hasta 10 MB.`;continue}
    if(!nuevas.value.some(f=>f.archivo.name===archivo.name&&f.archivo.size===archivo.size&&f.archivo.lastModified===archivo.lastModified))nuevas.value.push({archivo,proveedor:'',empresa:'',proveedor_identificador:'',clave:++secuencia})
  }
  evento.target.value=''
}
// R01 y R02: se consulta de nuevo al enviar; no se confía en una caché vieja.
async function validar(){
  try{
    await cargarReglas()
    const monto=Number(props.monto)
    if(props.monto===''||!Number.isFinite(monto)||monto<0)throw new Error('Ingrese un costo estimado válido antes de enviar.')
    // REQUERIMIENTO 1 (R01): rechazo prioritario, no se elude con cotizaciones.
    if(monto>Number(reglas.value.limite_caja_chica)){
      await SigtaModal.fire({title:'Requerimiento rechazado por exceder el límite',text:`El monto de Bs ${dinero(monto)} supera el límite permitido de Bs ${dinero(reglas.value.limite_caja_chica)}. El requerimiento no puede enviarse. Corrija el monto para continuar; sus datos y documentos se conservan.`,icon:'warning',confirmButtonText:'Aceptar'})
      return false
    }
    // REQUERIMIENTO 2 (R02): al superar 500, completar tres proveedores.
    if(progreso.value.faltantes){
      await SigtaModal.fire({title:'Cotizaciones adicionales requeridas',text:mensajeCotizaciones(monto,progreso.value,reglas.value),icon:'info',confirmButtonText:'Aceptar'})
      if(monto>Number(reglas.value.umbral_cotizaciones))ampliado.value=true
      seccion.value?.scrollIntoView({behavior:'smooth',block:'center'});seccion.value?.focus();entrada.value?.focus()
      return false
    }
    return true
  }catch(e){error.value=e.message;await SigtaModal.fire({title:'Revise el requerimiento',text:e.message,icon:'warning',confirmButtonText:'Entendido'});return false}
}
function adjuntar(datos){
  for(const fila of nuevas.value)datos.append('cotizaciones',fila.archivo)
  datos.append('cotizaciones_metadata',JSON.stringify(nuevas.value.map(({proveedor,empresa,proveedor_identificador})=>({proveedor,empresa,proveedor_identificador}))))
  datos.append('proveedores_guardados',JSON.stringify(guardadasEditables.value.filter(f=>f.id).map(({id,proveedor,empresa,proveedor_identificador})=>({id,proveedor,empresa,proveedor_identificador}))))
}
function limpiar(){nuevas.value=[]}
defineExpose({validar,adjuntar,limpiar})
</script>
<style scoped>
.cotizaciones-sia{grid-column:1/-1;color:var(--sigta-texto)}header{display:flex;justify-content:space-between;align-items:center;gap:12px}header small{font-size:10px;letter-spacing:1px;color:var(--sigta-texto-suave);font-weight:800}h3{margin:5px 0 10px;color:var(--sigta-azul);font-size:17px}header>span{background:var(--sigta-azul);color:white;padding:7px 12px;border-radius:20px;font-size:12px;white-space:nowrap}p,small{font-size:12px;line-height:1.6}label{display:grid;gap:6px;font-size:12px;font-weight:700}input,select{box-sizing:border-box;width:100%;min-width:0;padding:10px;border:1px solid var(--sigta-borde);border-radius:7px;background:white;color:var(--sigta-texto)}input:focus-visible,select:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid var(--sigta-mostaza);outline-offset:2px}.cotizacion{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0;padding:14px;background:white;border:1px solid var(--sigta-borde);border-radius:9px}.archivo{grid-column:1/-1;display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:12px;overflow-wrap:anywhere}.archivo b{color:var(--sigta-azul);font-size:11px}.archivo span{flex:1}.archivo a,.archivo button{color:var(--sigta-azul);background:white;border:1px solid var(--sigta-borde);border-radius:6px;padding:6px 9px;font-size:12px;cursor:pointer}.adjuntar{margin:15px 0 8px;color:var(--sigta-azul)}.pendientes{color:var(--sigta-alerta);background:var(--sigta-mostaza-suave);padding:10px;border-radius:8px}.error{color:var(--sigta-error)}.via{max-width:300px;margin:12px 0}@media(max-width:600px){.cotizacion{grid-template-columns:1fr}header{align-items:flex-start}.cotizaciones-sia{padding:14px}}
</style>
