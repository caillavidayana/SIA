<template>
  <section>
    <h3>Comparación de cotizaciones</h3>
    <button class="sia-secondary" :disabled="ocupado" @click="cargar">Consultar cotizaciones</button>
    <p v-if="error" role="alert">{{ error }}</p>
    <div v-if="cotizaciones.length" class="sia-tabla"><table><thead><tr><th>Proveedor</th><th>Producto</th><th>Cantidad</th><th>Precio unitario (Bs)</th><th>Total (Bs)</th><th>Documento</th><th>Selección</th></tr></thead><tbody><tr v-for="c in cotizaciones" :key="c.id"><td>{{ c.proveedor }}</td><td>{{ c.descripcion }}</td><td>{{ c.cantidad }}</td><td>{{ c.precio_unitario }}</td><td>{{ c.total }}</td><td><button class="sia-secondary" @click="verDocumento(c)">Ver evidencia</button></td><td>{{ c.seleccionada ? 'Seleccionada' : '' }}<button v-if="editable && !c.seleccionada" class="sia-secondary" :disabled="ocupado" @click="seleccionar(c)">Seleccionar</button></td></tr></tbody></table></div>
    <p v-if="consultado && !cotizaciones.length">Todavía no se registraron cotizaciones comparables. La proforma del expediente conserva su función actual.</p>
    <details v-if="editable"><summary>Registrar otra cotización</summary>
      <label class="sia-field">Proveedor<input v-model="form.proveedor" maxlength="180"></label>
      <label class="sia-field">Descripción<textarea v-model="form.descripcion" /></label>
      <label class="sia-field">Cantidad<input v-model="form.cantidad" type="number" min="1" step="1"></label>
      <label class="sia-field">Precio unitario (Bs)<input v-model="form.precio_unitario" type="number" min="0.01" step="0.01"></label>
      <label class="sia-field">Documento<ArchivoInput type="file" accept="application/pdf,image/png,image/jpeg,image/webp" @change="archivo=$event.target.files?.[0] || null" /></label>
      <button class="sia-primary" :disabled="ocupado || !archivo || !form.proveedor.trim() || !form.descripcion.trim() || !form.precio_unitario" @click="guardar">Guardar cotización</button>
    </details>
  </section>
</template>
<script setup>
import { reactive, ref, watch } from 'vue'
const props=defineProps({id:[Number,String],editable:Boolean})
const cotizaciones=ref([]), ocupado=ref(false), error=ref(''), consultado=ref(false), archivo=ref(null)
const form=reactive({proveedor:'',descripcion:'',cantidad:1,precio_unitario:''})
watch(()=>props.id,()=>{cotizaciones.value=[];consultado.value=false;error.value='';archivo.value=null;Object.assign(form,{proveedor:'',descripcion:'',cantidad:1,precio_unitario:''})})
async function api(endpoint,body){const r=await fetch(`/api/compras/solicitudes/${props.id}/${endpoint}/`,{method:body?'POST':'GET',headers:{Authorization:`Token ${localStorage.getItem('sigta_token')}`,...(body && !(body instanceof FormData)?{'Content-Type':'application/json'}:{})},body:body instanceof FormData?body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw new Error(d.detalle || Object.values(d)[0] || 'No fue posible completar la acción.');return d}
async function verDocumento(c){try{const r=await fetch(c.documento_url,{headers:{Authorization:`Token ${localStorage.getItem('sigta_token')}`}});if(!r.ok)throw new Error('No se pudo abrir el documento.');const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=`cotizacion-${c.id}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),60000)}catch(e){error.value=e.message}}
async function cargar(){ocupado.value=true;error.value='';try{cotizaciones.value=await api('cotizaciones');consultado.value=true}catch(e){error.value=e.message}finally{ocupado.value=false}}
async function guardar(){ocupado.value=true;error.value='';try{const fd=new FormData();for(const [k,v] of Object.entries(form))fd.append(k,v);fd.append('documento',archivo.value);await api('cotizaciones',fd);await cargar()}catch(e){error.value=e.message}finally{ocupado.value=false}}
async function seleccionar(c){const motivo=await window.sigtaPrompt(`Motivo de selección de la cotización de ${c.proveedor}`);if(!motivo?.trim())return;ocupado.value=true;error.value='';try{await api('seleccionar-cotizacion',{cotizacion_id:c.id,motivo:motivo.trim()});await cargar()}catch(e){error.value=e.message}finally{ocupado.value=false}}
</script>
<style scoped>.sia-tabla {overflow:auto;margin:14px 0;}table {width:100%;border-collapse:collapse;}th,td {padding:10px;text-align:left;border-bottom:1px solid var(--sigta-borde);}th {background:var(--sigta-azul-tenue);}</style>
