<template><section v-if="filas?.length" class="cotizaciones-expediente"><h3>Cotizaciones del expediente</h3><article v-for="(c,i) in filas" :key="c.id || i"><div><b>{{ c.proveedor || 'Proveedor no registrado (histórico)' }}</b><small v-if="c.empresa">Empresa: {{c.empresa}}</small><small>{{ c.nombre_original || c.descripcion || `Cotización ${i+1}` }}<template v-if="c.proveedor_identificador"> · NIT / ID {{ c.proveedor_identificador }}</template></small></div><button type="button" @click="abrir(c)">Ver cotización {{ i+1 }}</button></article><p v-if="error" role="alert">{{ error }}</p></section></template>
<script setup>
import { ref } from 'vue'
const props=defineProps({filas:Array})
const error=ref('')
async function abrir(c){
  error.value=''
  try{
    const url=new URL(c.archivo_url||c.documento_url,window.location.origin)
    if(url.origin!==window.location.origin||!/^\/(api|media)\//.test(url.pathname))throw new Error('Documento no válido.')
    const r=await fetch(url.pathname+url.search,{headers:{Authorization:`Token ${localStorage.getItem('sigta_token')}`}})
    if(!r.ok)throw new Error(`No se pudo abrir el documento (HTTP ${r.status}).`)
    const blob=await r.blob(), local=URL.createObjectURL(blob)
    const a=document.createElement('a');a.href=local;a.download=c.nombre_original||`cotizacion-${c.id||'historica'}.pdf`;a.click();setTimeout(()=>URL.revokeObjectURL(local),1000)
  }catch(e){error.value=e.message}
}
</script>
<style scoped>
.cotizaciones-expediente{margin:16px 0;padding:16px;background:var(--sigta-fondo);border:1px solid var(--sigta-borde);border-top:3px solid var(--sigta-mostaza);border-radius:10px}.cotizaciones-expediente h3{color:var(--sigta-azul);font-size:16px;margin:0 0 12px}.cotizaciones-expediente article{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid var(--sigta-borde)}b,small{display:block;overflow-wrap:anywhere}b{font-size:13px;color:var(--sigta-azul)}small{font-size:11px;color:var(--sigta-texto-suave);margin-top:5px}button{background:var(--sigta-azul);color:white;border:0;border-radius:7px;padding:10px 12px;cursor:pointer;font-weight:700}button:focus-visible{outline:3px solid var(--sigta-mostaza);outline-offset:2px}p{color:var(--sigta-error)}@media(max-width:600px){article{flex-wrap:wrap}}
</style>
