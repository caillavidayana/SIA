<template>
  <div :class="['notification-layout', {embedded}]">
    <SolicitanteMenu v-if="!embedded && !esTecnico" />
    <LogoutModal :visible="mostrarLogout" @cancelar="mostrarLogout=false" @confirmar="confirmarSalida" />
    <main class="page">
    <header v-if="!embedded">
      <div><h1>Notificaciones</h1><p>Decisiones y novedades relacionadas con sus tickets.</p></div>
      <div class="header-actions">
        <button v-if="pendientes" class="read-all" @click="marcarTodas">Marcar todas como leídas</button>
      </div>
        <UsuarioHeader @actualizar="cargar" />
      </header>
    <div v-if="embedded && pendientes" class="header-actions"><button class="read-all" @click="marcarTodas">Marcar todas como le&#237;das</button></div>
    <section class="stats">
      <article><i class="blue"><IconoSigta nombre="notificaciones" :tamano="19" /></i><div><small>Sin leer</small><b>{{pendientes}}</b></div></article>
      <article><i class="green"><IconoSigta nombre="validar" :tamano="19" /></i><div><small>Aprobadas</small><b>{{aprobadas}}</b></div></article>
      <article><i class="red"><IconoSigta nombre="error" :tamano="19" /></i><div><small>Rechazadas</small><b>{{rechazadas}}</b></div></article>
      <article><i class="gold"><IconoSigta nombre="reporte" :tamano="19" /></i><div><small>Total</small><b>{{notificaciones.length}}</b></div></article>
    </section>
    <section class="list">
      <article v-for="n in notificaciones" :key="n.id" :class="[n.tipo.toLowerCase(),{unread:!n.leida}]">
        <i>{{n.tipo==='EXITO'?'✓':n.tipo==='RECHAZO'?'!':'i'}}</i>
        <div><div class="title"><strong>{{n.titulo}}</strong><em v-if="!n.leida">Nueva</em></div><p>{{n.mensaje}}</p><small>{{fecha(n.creada_en)}} · {{n.ticket_titulo}}</small></div>
        <div class="actions"><button @click="verDetalle(n)">Ver detalles</button><button v-if="!n.leida" class="secondary" @click="marcarLeida(n)">Marcar leída</button></div>
      </article>
      <div v-if="!cargando&&!notificaciones.length" class="empty"><span>✓</span><h3>Está al día</h3><p>No tiene notificaciones registradas.</p></div>
      <div v-if="cargando" class="empty">Consultando notificaciones…</div>
    </section>
    </main>
  </div>
</template>

<script setup>
import UsuarioHeader from '../components/UsuarioHeader.vue'
import {computed,onMounted,ref} from 'vue'
import {useRoute,useRouter} from 'vue-router'
import LogoutModal from '../components/LogoutModal.vue'
import IconoSigta from '../components/IconoSigta.vue'
import SolicitanteMenu from '../components/SolicitanteMenu.vue'
const props = defineProps({ embedded: Boolean })
const emit = defineEmits(["actualizadas"])
const router=useRouter(),route=useRoute(),notificaciones=ref([]),cargando=ref(true)
const usuario=JSON.parse(localStorage.getItem('sigta_usuario')||'{}'),roles=(usuario.roles||[]).map(r=>String(r?.codigo||r).toUpperCase())
const esTecnico=route.path.startsWith('/especialista/')||roles.includes('ESPECIALISTA')||roles.includes('AGENTE')
const pendientes=computed(()=>notificaciones.value.filter(n=>!n.leida).length)
const aprobadas=computed(()=>notificaciones.value.filter(n=>n.tipo==='EXITO').length)
const rechazadas=computed(()=>notificaciones.value.filter(n=>n.tipo==='RECHAZO').length)
const headers=()=>({Authorization:`Token ${localStorage.getItem('sigta_token')}`,Accept:'application/json'})

async function cargar(){
  cargando.value=true
  try{
    const peticiones=[fetch('/api/soporte/notificaciones/',{headers:headers()})]
    const [r]=await Promise.all(peticiones)
    const d=await r.json()
    if(!r.ok)throw new Error(d.detalle || "No se pudieron cargar las notificaciones.")
    notificaciones.value=Array.isArray(d)?d:d.results||[]
    emit("actualizadas", pendientes.value)
  }finally{cargando.value=false}
}
async function marcarLeida(n){await fetch(`/api/soporte/notificaciones/${n.id}/marcar-leida/`,{method:'POST',headers:headers()});n.leida=true;emit("actualizadas",pendientes.value)}
async function marcarTodas(){await fetch('/api/soporte/notificaciones/marcar-todas-leidas/',{method:'POST',headers:headers()});notificaciones.value.forEach(n=>n.leida=true);emit("actualizadas",pendientes.value)}
async function verDetalle(n){if(n.mantenimiento){if(!n.leida)await marcarLeida(n);router.push({path:'/auxiliar-servicios-generales/dashboard',query:{vista:'historial',requerimiento:n.mantenimiento}});return}if(!n.leida)await marcarLeida(n);router.push(esTecnico?{path:'/especialista/dashboard',query:{ticket:n.ticket}}:{path:'/usuario/mis-solicitudes',query:{proceso:'SOPORTE',id:n.ticket,origen:'notificaciones'}})}
function fecha(v){return new Date(v).toLocaleString('es-BO',{dateStyle:'medium',timeStyle:'short'})}
const mostrarLogout=ref(false)
function salir(){localStorage.removeItem('sigta_token');localStorage.removeItem('sigta_usuario');router.push('/login')}
function confirmarSalida(){mostrarLogout.value=false;salir()}
onMounted(cargar)
</script>

<style scoped>
.embedded .page{padding:0;width:100%}.embedded{min-height:0}
*{box-sizing:border-box}
.notification-layout{display:flex;min-height:100vh;background:var(--sigta-azul-tenue)}
.notification-layout>.page{flex:1;min-width:0}
.page{padding:28px;max-width:1650px;color:var(--sigta-texto);font-family:var(--sigta-fuente)}
header{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:24px}
h1{font-size:29px;margin:0!important}
header p{margin:0;font-size:12px;color:var(--sigta-texto-suave)}
.header-actions{display:flex;gap:9px}
.read-all{border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-azul);border-radius:8px;padding:10px 14px;font-weight:700;cursor:pointer}
.read-all:hover{background:var(--sigta-mostaza);border-color:var(--sigta-mostaza)}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:0 0 18px}
.stats article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-top:4px solid var(--sigta-mostaza);border-radius:10px;min-height:120px;padding:18px;display:flex;gap:13px;align-items:center;box-shadow:0 4px 14px rgba(0,0,0,.05)}
.stats i{font-style:normal;width:37px;height:37px;border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--sigta-blanco);flex-shrink:0}
.stats i.blue{background:var(--sigta-azul)}
.stats i.green{background:var(--sigta-azul-medio)}
.stats i.red{background:var(--sigta-error)}
.stats i.gold{background:var(--sigta-mostaza);color:var(--sigta-texto)}
.stats small,.stats b{display:block}
.stats small{font-size:9px;color:var(--sigta-texto-suave)}
.stats b{font-size:28px;margin-top:3px;color:var(--sigta-azul)}

.list{display:grid;gap:10px}
.list article{display:grid;grid-template-columns:44px 1fr auto;align-items:center;gap:14px;background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:11px;padding:16px}
.list article.unread{box-shadow:inset 4px 0 var(--sigta-mostaza)}
.list article.rechazo{border-color:#efc7c7}
.list article>i{width:42px;height:42px;border-radius:50%;display:grid;place-items:center;background:var(--sigta-azul-tenue);color:var(--sigta-azul);font-style:normal;font-weight:900}
.list article.rechazo>i{background:var(--sigta-error-fondo);color:var(--sigta-error)}
.title{display:flex;gap:9px;align-items:center}
.title em{font-size:9px;font-style:normal;background:var(--sigta-mostaza-suave);color:var(--sigta-mostaza-oscuro);border-radius:9px;padding:3px 7px}
.list p{margin:5px 0;color:var(--sigta-texto-suave)}
.list small{color:var(--sigta-texto-suave)}
.actions{display:flex;gap:7px;flex-direction:column}
.actions button{border:0;background:var(--sigta-azul);color:var(--sigta-blanco);border-radius:7px;padding:8px 11px;font-weight:800;cursor:pointer}
.actions .secondary{background:var(--sigta-blanco);color:var(--sigta-azul);border:1px solid var(--sigta-borde)}

.empty{text-align:center;background:var(--sigta-blanco);border:1px dashed var(--sigta-borde);padding:65px;border-radius:10px;color:var(--sigta-texto-suave)}
.empty>span{font-size:31px;color:var(--sigta-exito)}

@media(max-width:1050px){.stats{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.page{padding:20px}header{align-items:flex-start;flex-direction:column;gap:12px}.stats{grid-template-columns:1fr}.list article{grid-template-columns:38px 1fr}.actions{grid-column:1/-1;flex-direction:row}.actions button{flex:1}}
</style>
<style scoped>
.embedded .page{padding:0;width:100%}.embedded{min-height:0}
.technician-nav > button :deep(.icono-sigta){flex-shrink:0}
</style>
<style scoped>
.embedded .page{padding:0;width:100%}.embedded{min-height:0}
.technician-nav{position:sticky;top:0;width:var(--sigta-sidebar);min-width:var(--sigta-sidebar);height:100vh;padding:20px 14px;background:var(--sigta-azul);color:#fff;display:flex;flex-direction:column}.technician-nav .brand-row{display:flex;align-items:center}.technician-nav .brand{display:flex;align-items:center;gap:11px;padding:0 10px 20px;border-bottom:1px solid #ffffff20;width:100%}.technician-nav .brand>b{display:block;flex-shrink:0}.technician-nav .brand img{width:48px;height:48px;border-radius:10px;display:block}.technician-nav .brand strong,.technician-nav .brand small{display:block}.technician-nav .brand strong{font-size:22px}.technician-nav .brand small{color:var(--sigta-azul-texto-claro);font-size:11px;margin-top:3px}.technician-nav>p{font-size:10px;color:var(--sigta-texto-suave);font-weight:800;letter-spacing:1.4px;margin:14px 10px 8px}.technician-nav button{display:flex;align-items:center;gap:11px;width:100%;border:0;border-left:3px solid transparent;background:transparent;color:#fff!important;font-size:13px!important;font-weight:600!important;border-radius:8px;padding:0 12px;min-height:42px;cursor:pointer;text-align:left;margin:2px 0}.technician-nav>button :deep(.icono-sigta){flex-shrink:0}.technician-nav>button em{margin-left:auto;background:#ffffff1c;border-radius:10px;padding:2px 8px;font-style:normal}.technician-nav>button.active,.technician-nav>button:hover{background:#ffffff14;box-shadow:inset 3px 0 var(--sigta-mostaza-clara)}.technician-nav>button.active{color:var(--sigta-mostaza)!important}.technician-nav>.bottom{margin-top:auto;border-top:1px solid #ffffff20;padding-top:10px}.technician-nav>.bottom button{width:100%}.technician-nav>.bottom .logout{gap:14px;border:1px solid var(--sigta-mostaza);background:transparent;color:#fff!important;font-size:13px!important;box-shadow:inset 0 0 0 1px rgba(255,199,44,.35);transition:transform .3s cubic-bezier(.34,1.55,.5,1),background .2s ease,color .2s ease,box-shadow .2s ease}.technician-nav>.bottom .logout .icono-sigta{color:var(--sigta-mostaza);transition:color .2s ease}.technician-nav>.bottom .logout:hover{background:#FFB300;color:var(--sigta-azul)!important;transform:scale(1.09);box-shadow:0 14px 32px rgba(255,159,0,.55)}.technician-nav>.bottom .logout:hover .icono-sigta{color:var(--sigta-azul)}@media(max-width:700px){.notification-layout{display:block}.technician-nav{position:static;width:100%;min-width:0;height:auto}.technician-nav>p,.technician-nav>button:not(.active){display:none}.technician-nav>button.active{margin-top:10px}}
</style>
