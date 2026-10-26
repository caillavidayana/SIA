<template>
  <div class="page-layout">
    <SolicitanteMenu />
    <main class="page-content">
      <header class="page-header">
        <span>SIA / Portal Solicitante / Compras</span>
        <h1>Registrar solicitud de compra</h1>
        <p>Registre el requerimiento de adquisición y adjunte el expediente para su evaluación.</p>
      
        <UsuarioHeader @actualizar="cargarAreas" />
      </header>

      <form class="form-card" @submit.prevent="guardar">
        <section class="form-section">
          <div class="section-title"><b>1</b><div><h2>Información de la solicitud</h2><p>Describa claramente el bien, servicio o componente requerido.</p></div></div>
          <div class="fields one">
            <label>Título <em>*</em><input v-model="form.titulo" required placeholder="Ej.: Adquisición de monitor institucional"></label>
            <label>Descripción <em>*</em><textarea v-model="form.descripcion" required maxlength="1000" placeholder="Explique qué necesita adquirir y para qué será utilizado..."></textarea><small>{{ form.descripcion.length }} / 1000 caracteres</small></label>
          </div>
        </section>

        <section class="form-section">
          <div class="section-title"><b>2</b><div><h2>Clasificación y área solicitante</h2><p>Seleccione el tipo de adquisición y el área que realiza el pedido.</p></div></div>
          <div class="fields two">
            <label>Tipo de adquisición <em>*</em><select v-model="form.tipo" required><option value="" disabled>Seleccione un tipo</option><option value="BIEN">Bien</option><option value="SERVICIO">Servicio</option><option value="ACTIVO_FIJO">Activo fijo</option><option value="COMPONENTE">Componente</option></select></label>
            <label>Área solicitante <em>*</em><select v-model="form.area" required><option value="" disabled>Seleccione un área</option><option v-for="area in areas" :key="area.id" :value="area.id">{{ area.nombre }}</option></select></label>
          </div>
        </section>

        <section class="form-section">
          <div class="section-title"><b>3</b><div><h2>Cantidad y presupuesto estimado</h2><p>Indique las cantidades requeridas y el costo aproximado de la adquisición.</p></div></div>
          <div class="fields two">
            <label>Cantidad <em>*</em><input v-model.number="form.cantidad" type="number" min="1" required></label>
            <label>Monto estimado (Bs)<input v-monto inputmode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" v-model="form.monto_estimado" type="text" min="0" step="0.01" placeholder="Ej.: 850.00"></label>
            <label>Centro de costo<input v-model="form.centro_costo" placeholder="Opcional"></label>
            <label>Ticket de soporte vinculado<input v-model="form.ticket_soporte_vinculado" placeholder="Ej.: SOP-2026-0002"></label>
          </div>
        </section>

        <section class="form-section">
          <div class="section-title"><b>4</b><div><h2>Detalle técnico y justificación</h2><p>Registre las características necesarias y la razón institucional de la compra.</p></div></div>
          <div class="fields one">
            <label>Especificaciones técnicas <em>*</em><textarea v-model="form.especificaciones" required placeholder="Detalle características, dimensiones, compatibilidad, marca referencial..."></textarea></label>
            <label>Justificación <em>*</em><textarea v-model="form.justificacion" required placeholder="Explique por qué es necesaria esta adquisición..."></textarea></label>
          </div>
        </section>

        <section class="form-section">
          <div class="section-title"><b>5</b><div><h2>Expediente documental</h2><p>Adjunte los cuatro documentos obligatorios para enviar el trámite a la DAF.</p></div></div>
          <div class="documents">
            <label v-for="doc in documentos" :key="doc.campo"><span>{{ doc.nombre }} <em>*</em></span><small>{{ archivos[doc.campo]?.name || 'PDF o documento digital' }}</small><ArchivoInput type="file" required @change="seleccionar(doc.campo,$event)" /></label>
          </div>
        </section>

        <p v-if="mensaje" class="message">{{ mensaje }}</p>
        <footer class="form-actions"><button type="button" @click="router.push('/usuario/dashboard')">Cancelar</button><button class="primary" type="submit" :disabled="guardando">{{ guardando ? 'Enviando expediente...' : 'Enviar expediente de compra' }}</button></footer>
      </form>
    </main>
  </div>
</template>

<script setup>
import UsuarioHeader from '../components/UsuarioHeader.vue'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import SolicitanteMenu from '../components/SolicitanteMenu.vue'
const router=useRouter(),areas=ref([]),guardando=ref(false),mensaje=ref('')
const form=reactive({titulo:'',descripcion:'',area:'',tipo:'',cantidad:1,monto_estimado:'',centro_costo:'',ticket_soporte_vinculado:'',especificaciones:'',justificacion:''})
const archivos=reactive({informe:null,poa:null,pedido:null,proforma:null})
const documentos=[{campo:'informe',nombre:'Informe'},{campo:'poa',nombre:'POA'},{campo:'pedido',nombre:'Pedido'},{campo:'proforma',nombre:'Proforma'}]
const token=()=>localStorage.getItem('sigta_token')
function seleccionar(campo,e){archivos[campo]=e.target.files?.[0]||null}
async function cargarAreas(){try{const r=await fetch('/api/usuarios/areas/',{headers:{Authorization:`Token ${token()}`}});const d=await r.json();areas.value=Array.isArray(d)?d:(d.results||[])}catch{mensaje.value='No fue posible cargar las áreas.'}}
async function guardar(){guardando.value=true;mensaje.value='';try{const d=new FormData();Object.entries(form).forEach(([k,v])=>{if(v!==''&&v!==null)d.append(k,String(v))});Object.entries(archivos).forEach(([k,v])=>{if(v)d.append(k,v)});const r=await fetch('/api/compras/solicitudes/',{method:'POST',headers:{Authorization:`Token ${token()}`},body:d});const data=await r.json();if(!r.ok)throw new Error(data.detalle||data.documentos?.[0]||data.documentos||'Revise la información ingresada.');router.push('/usuario/mis-solicitudes')}catch(e){mensaje.value=e.message}finally{guardando.value=false}}
onMounted(cargarAreas)
</script>

<style scoped>
*{box-sizing:border-box}.page-layout{min-height:100vh;display:flex;background:var(--sigta-azul-tenue);font-family: var(--sigta-fuente)}.page-content{flex:1;min-width:0;padding:28px;overflow-x:hidden}.page-header{max-width:1160px;margin:0 auto 22px}.page-header span{display:block;margin-bottom:8px;color:var(--sigta-texto-suave);font-size:9px}.page-header h1{margin:0;color:var(--sigta-texto);font-size:28px}.page-header p{margin:6px 0 0;color:var(--sigta-texto-suave);font-size:12px}.form-card{max-width:1160px;margin:auto;background:var(--sigta-blanco);border-top:5px solid var(--sigta-mostaza);border-radius:10px;box-shadow:0 4px 14px rgba(0,0,0,.05);overflow:hidden}.form-section{padding:26px 28px 28px;border-bottom:1px solid var(--sigta-azul-texto-claro)}.section-title{display:flex;align-items:flex-start;gap:12px;margin-bottom:22px}.section-title>b{width:31px;height:31px;flex:none;display:grid;place-items:center;border-radius:50%;background:var(--sigta-azul);color:var(--sigta-blanco);font-size:12px}.section-title h2{margin:1px 0 4px;color:var(--sigta-texto);font-size:17px}.section-title p{margin:0;color:var(--sigta-texto-suave);font-size:9px}.fields{display:grid;gap:18px}.fields.two{grid-template-columns:1fr 1fr}.fields.one{grid-template-columns:1fr}.fields label,.documents label{color:var(--sigta-texto);font-size:11px;font-weight:700}.fields em,.documents em{color:var(--sigta-error);font-style:normal}.fields input,.fields select,.fields textarea{display:block;width:100%;margin-top:7px;padding:12px 13px;border:1px solid var(--sigta-azul-texto-claro);border-radius:7px;background:var(--sigta-blanco);font:inherit;font-weight:400;color:var(--sigta-azul)}.fields input,.fields select{height:45px}.fields textarea{min-height:120px;resize:vertical}.fields label:first-child textarea{min-height:155px}.fields input:focus,.fields select:focus,.fields textarea:focus{outline:0;border-color:var(--sigta-texto-suave);box-shadow:0 0 0 3px rgba(10,87,148,.08)}.fields label>small{display:block;text-align:right;margin-top:5px;color:var(--sigta-texto-suave);font-size:8px;font-weight:400}.documents{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.documents label{position:relative;display:block;padding:15px;border:1px dashed var(--sigta-texto-suave);border-radius:8px;background:var(--sigta-azul-tenue);cursor:pointer}.documents label span,.documents label small{display:block}.documents label small{margin-top:5px;color:var(--sigta-texto-suave);font-size:9px;font-weight:400}.documents input{position:absolute;inset:0;width:100%;opacity:0;cursor:pointer}.message{margin:18px 28px 0;padding:11px;border-radius:7px;background:var(--sigta-error-fondo);color:var(--sigta-error);font-size:10px}.form-actions{display:flex;justify-content:flex-end;gap:10px;padding:22px 28px}.form-actions button{min-height:42px;padding:0 18px;border:1px solid var(--sigta-borde);border-radius:7px;background:var(--sigta-blanco);color:var(--sigta-texto-suave);font-weight:700;cursor:pointer}.form-actions .primary{min-width:230px;border-color:var(--sigta-texto-suave);background:var(--sigta-texto-suave);color:var(--sigta-blanco)}.form-actions button:disabled{opacity:.6;cursor:not-allowed}@media(max-width:760px){.page-content{padding:18px}.fields.two,.documents{grid-template-columns:1fr}.form-section{padding:22px 18px}.form-actions{padding:18px;flex-direction:column-reverse}.form-actions button{width:100%}}
</style>
