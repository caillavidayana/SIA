<template>
  <section class="caja-control">
    <header><div><small>CONTROL FINANCIERO</small><h2>Control de Caja Chica</h2><p>Compromisos y desembolsos registrados, sin duplicar importes.</p></div><label>Mes del fondo<input v-model="mes" type="month" @change="cargar"></label><button type="button" class="sia-secondary" :disabled="cargando" @click="cargar">Actualizar saldo</button></header>
    <p v-if="error" class="caja-error" role="alert">{{ error }}</p>
    <p v-if="cargando" role="status">Consultando el fondo mensual…</p>
    <template v-if="datos">
      <div class="caja-indicadores"><article><small>Fondo mensual</small><strong>Bs {{ moneda(datos.fondo_mensual) }}</strong></article><article><small>Desembolsado</small><strong>Bs {{ moneda(datos.utilizado) }}</strong></article><article><small>Comprometido por aprobarse el pago</small><strong>Bs {{ moneda(datos.comprometido) }}</strong></article><article :class="{deficit:Number(datos.saldo_disponible)<0}"><small>Saldo disponible</small><strong>Bs {{ moneda(datos.saldo_disponible) }}</strong></article></div>
      <div class="caja-progreso"><span>{{ datos.porcentaje_utilizado }} % utilizado o comprometido</span><progress :value="Math.min(100,Number(datos.porcentaje_utilizado))" max="100" :aria-label="`Fondo utilizado: ${datos.porcentaje_utilizado} por ciento`"></progress></div>
      <p v-if="Number(datos.saldo_disponible)<0" class="caja-error">Los movimientos históricos superan el fondo configurado. Se conservan para auditoría y no se permiten nuevos compromisos sin saldo.</p>
      <div v-if="!resumen" class="caja-tabla"><table><thead><tr><th>Compra</th><th>Requerimiento</th><th>Situación financiera</th><th>Importe</th><th>Desembolsado</th></tr></thead><tbody><tr v-for="m in datos.movimientos" :key="m.compra_id"><td>{{ m.codigo }}</td><td>{{ m.titulo }}</td><td>{{ estado(m.estado) }}</td><td>Bs {{ moneda(m.monto) }}</td><td>Bs {{ moneda(m.desembolsado) }}</td></tr><tr v-if="!datos.movimientos.length"><td colspan="5">No hay movimientos de Caja Chica para este mes.</td></tr></tbody></table></div>
    </template>
  </section>
</template>
<script setup>
import {onMounted,ref} from 'vue'
defineProps({resumen:Boolean})
const mes=ref(new Intl.DateTimeFormat('sv-SE',{timeZone:'America/La_Paz',year:'numeric',month:'2-digit'}).format(new Date()))
const datos=ref(null),error=ref(''),cargando=ref(false)
const moneda=v=>Number(v||0).toLocaleString('es-BO',{minimumFractionDigits:2,maximumFractionDigits:2})
const estado=v=>({COMPROMETIDO:'Comprometido',DESEMBOLSADO:'Desembolsado',LIBERADO:'Liberado'}[v]||v)
async function cargar(){
  cargando.value=true;error.value=''
  try{const r=await fetch(`/api/caja-chica/saldo/?mes=${encodeURIComponent(mes.value)}`,{headers:{Authorization:`Token ${localStorage.getItem('sigta_token')}`}});const d=await r.json();if(!r.ok)throw new Error(d.detalle||d.detail||'No se pudo consultar el saldo.');datos.value=d}catch(e){error.value=e.message}finally{cargando.value=false}
}
onMounted(cargar)
defineExpose({cargar})
</script>
<style scoped>
.caja-control{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-top:4px solid var(--sigta-mostaza);border-radius:12px;margin:18px 0;padding:22px;color:var(--sigta-texto)}header{display:flex;align-items:center;gap:18px;flex-wrap:wrap}header>div{flex:1;min-width:220px}header small{font-size:10px;letter-spacing:1px;color:var(--sigta-texto-suave);font-weight:800}h2{margin:5px 0;color:var(--sigta-azul);font-size:21px}p{font-size:12px;line-height:1.6}label{font-size:12px;display:grid;gap:6px;font-weight:700}input{padding:9px;border:1px solid var(--sigta-borde);border-radius:7px}.caja-indicadores{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:20px 0}.caja-indicadores article{background:var(--sigta-azul-tenue);border:1px solid var(--sigta-borde);border-radius:9px;padding:17px}.caja-indicadores small,.caja-indicadores strong{display:block}.caja-indicadores small{font-size:11px;line-height:1.5;color:var(--sigta-texto-suave)}.caja-indicadores strong{font-size:21px;margin-top:8px;color:var(--sigta-azul)}.caja-indicadores article.deficit{background:var(--sigta-error-fondo)}.deficit strong,.caja-error{color:var(--sigta-error)}.caja-progreso{font-size:12px;color:var(--sigta-texto-suave)}progress{width:100%;height:12px;display:block;margin-top:9px;accent-color:var(--sigta-mostaza)}.caja-tabla{overflow:auto;margin-top:20px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;padding:12px;border-bottom:1px solid var(--sigta-borde)}th{background:var(--sigta-azul-tenue);color:var(--sigta-azul)}@media(max-width:1000px){.caja-indicadores{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:550px){.caja-control{padding:15px}.caja-indicadores{grid-template-columns:1fr}.caja-indicadores strong{font-size:20px}}
</style>
