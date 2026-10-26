<template>
  <div class="layout sigta-role-layout almacen-vista">
    <aside :class="{ abierto: menuAbierto }">
      <div class="brand-row">
        <div class="brand"><b><img src="/img/emi.jpg" alt="EMI"></b><div><strong>SIA</strong><small>Almacén y Compras</small></div></div>
        <button type="button" class="menu-toggle" :aria-expanded="menuAbierto" aria-label="Mostrar opciones del menú" @click="menuAbierto = !menuAbierto"><span></span><span></span><span></span></button>
      </div>
      <p>CAJA CHICA</p>
      <button v-for="m in menu" :key="m.id" class="alm-menu-item" :class="{active:vista===m.id}" @click="irA(m.id)"><span class="icon-badge" :style="{'--alm-icon':m.color,'--alm-icon-bg':m.color+'26'}"><IconoSigta :nombre="m.icono" :tamano="16" /></span><span class="alm-menu-label">{{ m.nombre }}</span><em v-if="m.total!==undefined">{{ m.total }}</em></button>
      <div class="bottom"><button class="logout" @click="mostrarLogout = true"><IconoSigta nombre="salir" :tamano="17" />Cerrar sesión</button></div>
    </aside>

    <LogoutModal :visible="mostrarLogout" @cancelar="mostrarLogout = false" @confirmar="confirmarSalida" />
    <TarjetaGuardado :visible="mostrarGuardado" :texto="textoGuardado" :tipo="tipoGuardado" @cerrar="ocultarGuardado" />

    <main>
      <header>
        <div><h1>{{ titulo }}</h1><p>{{ subtitulo }}</p></div>

      
        <UsuarioHeader @actualizar="cargar" />
      </header>
      <CajaChicaPanel resumen />

<p v-if="errorCarga" class="alm-error" role="alert">{{ errorCarga }}</p>
<section v-if="vista==='resumen'">        <div class="stats">
          <article @click="irA('comprar')"><i class="gold"><IconoSigta nombre="compras" :tamano="19" /></i><div><small>Por comprar</small><b>{{ porComprar.length }}</b><p>fondos desembolsados</p></div></article>
          <article @click="irA('entrada')"><i class="blue"><IconoSigta nombre="almacen" :tamano="19" /></i><div><small>Por registrar entrada</small><b>{{ porIngresar.length }}</b><p>producto adquirido</p></div></article>
          <article @click="irA('salida')"><i class="blue"><IconoSigta nombre="salir" :tamano="19" /></i><div><small>Por registrar salida</small><b>{{ porDespachar.length }}</b><p>en almacén</p></div></article>
          <article @click="irA('entrega')"><i class="green"><IconoSigta nombre="conformidad" :tamano="19" /></i><div><small>Por entregar</small><b>{{ porEntregar.length }}</b><p>con acta de conformidad</p></div></article>
        </div>

</section>
<AlmacenTabla v-if="vista==='resumen'" :mostrar-buscador="false" etapa="comprar" titulo="Compras pendientes de realizar" :registros="porComprar" :cargando="cargando" @registrar="abrirCompraDashboard" />
<AlmacenTabla v-else-if="esGestionAlmacen" :key="vista" :etapa="vista" :titulo="configuracionGestion.bandeja" :registros="bandejaActual" :cargando="cargando" @registrar="abrir" @detalle="verDetalle" />
<AlmacenTabla v-else-if="vista==='historial'" etapa="historial" titulo="Historial de movimientos" :registros="historial" :cargando="cargando" @detalle="verDetalle" />
</main>
<ModalSia v-if="activo" :titulo="`${configuracionGestion.etiqueta} · ${activo.codigo}`" amplio :ocupado="procesando" @cerrar="cerrar">            <div class="ticket-header-card"><div class="t-head"><h2>{{ activo.codigo }}</h2><span class="codigo-badge">{{ configuracionGestion.etiqueta }}</span></div><p>{{ activo.titulo }}</p><div class="t-meta"><span><b>Solicitante:</b> {{ activo.solicitante_nombre || 's/d' }}</span><span><b>Cantidad:</b> {{ activo.cantidad }} unid.</span></div></div>

            <div class="workflow-card"><div class="wf-header">{{ configuracionGestion.etiqueta }}</div><div class="wf-body">
              <div v-if="pasoActual===1" class="wf-step active"><div class="step-num">1</div><div class="step-content"><h4>{{ configuracionGestion.paso1 }}</h4><p>{{ configuracionGestion.ayuda1 }}</p><div v-if="pasoActual===1" class="step-form"><p class="copy">{{ contextoPaso1 }}</p><div class="step-actions"><button class="reject" @click="cerrar">Cancelar</button><button class="flex-btn primary" :disabled="procesando" @click="completarPasoUno">{{ textoPasoUno }}</button></div></div></div></div>
              <div v-if="pasoActual===2" class="wf-step active"><div class="step-num">2</div><div class="step-content"><h4>{{ configuracionGestion.paso2 }}</h4><p>{{ configuracionGestion.ayuda2 }}</p><div v-if="pasoActual===2" class="step-form">
                <template v-if="vista==='comprar'"><label class="campo">Monto real cobrado (Bs)<input v-model="formCompra.monto_real" type="number" min="0" step="0.01" placeholder="0.00"></label><label class="campo">Proveedor<input v-model="formCompra.proveedor" placeholder="Nombre o razón social"></label><div class="campo">Factura o recibo<EvidenciaFactura v-model="comprobante" /></div><label class="campo">Verificación del producto<input v-model="formCompra.observacion_verificacion" placeholder="El producto corresponde a lo solicitado..."></label></template>
                <template v-else-if="vista==='entrada'"><label class="campo">Cantidad recibida<input v-model="formIngreso.cantidad_recibida" type="number" min="1" :max="activo.cantidad" :placeholder="`Máximo ${activo.cantidad}`"></label><label class="campo">Recibido por<input v-model="formIngreso.responsable_recepcion" placeholder="Nombre de quien recibe en almacén"></label><label class="campo">Observación del ingreso<input v-model="formIngreso.observacion_ingreso" placeholder="Estado del producto, embalaje..."></label></template>
                <template v-else-if="vista==='salida'"><label class="campo">Cantidad que sale<input v-model="formSalida.cantidad_entregada" type="number" min="1" :max="activo.cantidad_recibida" :placeholder="`Máximo ${activo.cantidad_recibida}`"></label><label class="campo">Entregado a<input v-model="formSalida.entregado_a" :readonly="!!activo.receptor_acta?.tecnico" placeholder="Nombre de quien retira el producto"></label><label class="campo">Observación de la salida<input v-model="formSalida.observacion_salida" placeholder="Detalle adicional..."></label></template>
                <ActaEntregaAlmacen v-else :solicitud="activo" :ocupado="procesando" v-model="acta" v-model:acta-id="actaId" v-model:listo="actaLista" @ver="verArchivo" />
                <div class="step-actions"><button class="reject" @click="pasoActual=1">Retroceder</button><button class="flex-btn primary" :disabled="!pasoDosValido" @click="pasoActual=3">Continuar</button></div>
              </div></div></div>
              <div v-if="pasoActual===3" class="wf-step active"><div class="step-num">3</div><div class="step-content"><h4>Confirmar registro</h4><p class="alm-confirmacion">{{ resumenRegistro }}</p><p>Revise la información. Al confirmar, el expediente avanzará al siguiente proceso.</p><div v-if="pasoActual===3" class="step-form"><div class="step-actions"><button class="reject" @click="pasoActual=2">Retroceder</button><button class="flex-btn primary" :disabled="procesando" @click="registrarGestion">{{ configuracionGestion.accion }}</button></div></div></div></div>
            </div></div>
<p v-if="errorAccion" class="alm-error" role="alert">{{ errorAccion }}</p></ModalSia>
<ModalSia v-if="detalle" :titulo="`Detalle del expediente · ${detalle.codigo}`" amplio @cerrar="detalle=null">
  <DetalleAlmacen :registro="detalle" :estado="etiquetaEstado(detalle.estado)" :actas="actasDetalle" :error="errorDetalle" @ver="verArchivo" />
</ModalSia>
<ModalSia v-if="visor" :titulo="visor.nombre" amplio @cerrar="cerrarVisor"><p v-if="visor.cargando" role="status">Abriendo documento…</p><p v-if="visor.error" class="alm-error" role="alert">{{ visor.error }}</p><template v-if="visor.url"><iframe v-if="visor.tipo==='application/pdf'" :src="visor.url" :title="visor.nombre" class="alm-pdf"></iframe><img v-else-if="visor.tipo.startsWith('image/')" :src="visor.url" :alt="visor.nombre" class="alm-imagen"><p v-else>Descargue el archivo para abrirlo con su aplicación correspondiente.</p><a :href="visor.url" :download="visor.archivo" class="sia-secondary">Descargar documento</a></template></ModalSia>
</div></template>
<script setup>
import CajaChicaPanel from '../components/CajaChicaPanel.vue'
import { mostrarErrorRegla } from '../utils/errorRegla'
import AlmacenTabla from '../components/AlmacenTabla.vue'
import ActaEntregaAlmacen from '../components/ActaEntregaAlmacen.vue'
import ModalSia from '../components/ModalSia.vue'
import DetalleAlmacen from '../components/DetalleAlmacen.vue'
import EvidenciaFactura from '../components/EvidenciaFactura.vue'
import { solicitarFirma } from '../utils/firma'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import LogoutModal from '../components/LogoutModal.vue'
import IconoSigta from '../components/IconoSigta.vue'
import TarjetaGuardado from '../components/TarjetaGuardado.vue'
import { usarGuardado } from '../utils/guardado.js'

const router = useRouter()
const { mostrar: mostrarGuardado, texto: textoGuardado, tipo: tipoGuardado, animar: animarGuardado, animarError, ocultar: ocultarGuardado } = usarGuardado()
const usuario = ref(JSON.parse(localStorage.getItem('sigta_usuario') || '{}'))
const vista = ref('resumen')
const menuAbierto = ref(false)
const expedientes = ref([])
const cargando = ref(false)
const procesando = ref(false)
const activo = ref(null)
const detalle = ref(null)
const comprobante = ref(null)
const acta = ref(null)
const actaId = ref(null), actaLista = ref(false)
const errorCarga = ref(''), errorAccion = ref(''), errorDetalle = ref(''), actasDetalle = ref([]), visor = ref(null)
const pasoActual = ref(1)

const nombre = computed(() => usuario.value.nombre || usuario.value.nombre_completo || 'Compras y Almacén')
const primerNombre = computed(() => nombre.value.split(' ')[0])
const iniciales = computed(() => nombre.value.split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase())
const saludo = computed(() => new Date().getHours() < 12 ? 'Buenos días' : new Date().getHours() < 19 ? 'Buenas tardes' : 'Buenas noches')

/* Las cuatro tareas del BPMN, cada una con su bandeja. */
const porComprar = computed(() => expedientes.value.filter(e => e.estado === 'FONDOS_DESEMBOLSADOS'))
const porIngresar = computed(() => expedientes.value.filter(e => e.estado === 'COMPRA_REGISTRADA' && !e.fecha_ingreso_almacen))
const porDespachar = computed(() => expedientes.value.filter(e => e.estado === 'COMPRA_REGISTRADA' && e.fecha_ingreso_almacen && !e.fecha_despacho_almacen))
const porEntregar = computed(() => expedientes.value.filter(e => e.estado === 'COMPRA_REGISTRADA' && e.fecha_despacho_almacen))
const historial = computed(() => expedientes.value.filter(e => e.fecha_ingreso_almacen || e.monto_real))
const esGestionAlmacen = computed(() => ['comprar', 'entrada', 'salida', 'entrega'].includes(vista.value))
const busquedaBandeja = ref('')
const bandejaFiltrada = computed(() => bandejaActual.value.filter(e => [e.codigo,e.titulo,e.solicitante_nombre].some(v => String(v||'').toLowerCase().includes(busquedaBandeja.value.trim().toLowerCase()))))
const bandejaActual = computed(() => ({ comprar: porComprar.value, entrada: porIngresar.value, salida: porDespachar.value, entrega: porEntregar.value }[vista.value] || []))
const configuracionGestion = computed(() => ({
  comprar: { bandeja: 'Compras pendientes', etiqueta: 'Realizar compra', estado: 'fondos entregados', paso1: 'Revisar expediente y fondos', ayuda1: 'Confirme que el requerimiento y los fondos recibidos son correctos.', paso2: 'Registrar compra y respaldo', ayuda2: 'Registre el proveedor, monto real y factura o recibo.', accion: 'Registrar compra' },
  entrada: { bandeja: 'Entradas pendientes', etiqueta: 'Entrada de almacén', estado: 'compra registrada', paso1: 'Verificar producto adquirido', ayuda1: 'Revise el producto y sus datos de compra antes de ingresarlo.', paso2: 'Registrar ingreso a almacén', ayuda2: 'Indique la cantidad recibida y el responsable de recepción.', accion: 'Registrar entrada' },
  salida: { bandeja: 'Salidas pendientes', etiqueta: 'Salida de almacén', estado: 'en almacén', paso1: 'Verificar disponibilidad', ayuda1: 'Confirme las unidades disponibles y el destino solicitado.', paso2: 'Registrar salida de almacén', ayuda2: 'Indique las unidades que salen y quién las recibe.', accion: 'Registrar salida' },
  entrega: { bandeja: 'Entregas pendientes', etiqueta: 'Entregar con acta', estado: 'salida registrada', paso1: 'Revisar salida y destinatario', ayuda1: 'Confirme el destino y las unidades despachadas.', paso2: 'Adjuntar acta de conformidad', ayuda2: 'Genere el acta, imprímala y adjunte el PDF firmado por quien recibe y por el encargado.', accion: 'Entregar con acta' },
}[vista.value] || {}))
const contextoPaso1 = computed(() => {
  if (vista.value === 'comprar') return `Solicitado: ${activo.value?.cantidad || 0} unidad(es). Monto desembolsado: Bs ${activo.value?.monto_desembolsado || 's/d'}.`
  if (vista.value === 'entrada') return `Proveedor: ${activo.value?.proveedor || 's/d'}. Cantidad solicitada: ${activo.value?.cantidad || 0}.`
  if (vista.value === 'salida') return `Disponible en almacén: ${activo.value?.cantidad_recibida || 0} unidad(es), recibidas por ${activo.value?.responsable_recepcion || 's/d'}.`
  return `Salida registrada: ${activo.value?.cantidad_entregada || 0} unidad(es) con destino a ${activo.value?.entregado_a || 's/d'}.`
})
const textoPasoUno = computed(() => vista.value === 'comprar' && !activo.value?.fondos_recibidos_en ? 'Confirmar recepción de fondos' : 'Aprobar y continuar')
const pasoDosValido = computed(() => {
  if (vista.value === 'comprar') return !!(formCompra.monto_real && formCompra.proveedor.trim() && comprobante.value)
  if (vista.value === 'entrada') return Number.isInteger(Number(formIngreso.cantidad_recibida)) && Number(formIngreso.cantidad_recibida)>0 && Number(formIngreso.cantidad_recibida)<=Number(activo.value?.cantidad) && !!formIngreso.responsable_recepcion.trim()
  if (vista.value === 'salida') return Number.isInteger(Number(formSalida.cantidad_entregada)) && Number(formSalida.cantidad_entregada)>0 && Number(formSalida.cantidad_entregada)<=Number(activo.value?.cantidad_recibida) && !!formSalida.entregado_a.trim()
  return !!(acta.value && actaId.value && actaLista.value)
})

const menu = computed(() => [
  { id: 'resumen', icono: 'inicio', nombre: 'Dashboard', color: '#F2C400' },
  { id: 'comprar', icono: 'compras', nombre: 'Realizar compra', total: porComprar.value.length, color: '#C79A1E' },
  { id: 'entrada', icono: 'almacen', nombre: 'Entrada de almacén', total: porIngresar.value.length, color: '#3E7BD6' },
  { id: 'salida', icono: 'solicitudes', nombre: 'Salida de almacén', total: porDespachar.value.length, color: '#7B6FD9' },
  { id: 'entrega', icono: 'conformidad', nombre: 'Entregar con acta', total: porEntregar.value.length, color: '#2E9E6B' },
  { id: 'historial', icono: 'historial', nombre: 'Historial', color: '#D9538A' },
])

const titulo = computed(() => ({
  resumen: 'Dashboard de Compras y Almacén',
  comprar: 'Realizar compra',
  entrada: 'Registrar entrada de almacén',
  salida: 'Registrar salida de almacén',
  entrega: 'Entregar con acta de conformidad',
  historial: 'Historial de movimientos',
}[vista.value]))

const subtitulo = computed(() => ({
  resumen: 'Adquisición, control en almacén y entrega de los bienes de Caja Chica.',
  comprar: 'Expedientes con fondos ya desembolsados por Tesorería.',
  entrada: 'Productos comprados que deben ingresar formalmente a almacén.',
  salida: 'Productos en almacén listos para salir hacia el área solicitante.',
  entrega: 'Productos que salieron de almacén y deben entregarse con acta.',
  historial: 'Todos los movimientos que usted registró.',
}[vista.value]))

const ETIQUETAS = {
  CREADO_PENDIENTE_DAF: 'Esperando revisión de la DAF',
  EVALUADO_PENDIENTE_CERTIFICACION: 'Esperando certificación de la DAF',
  VERIFICADO_PENDIENTE_AUTORIZACION: 'Esperando autorización del Director',
  APROBADO_PARA_DESEMBOLSO: 'Esperando desembolso de Tesorería',
  FONDOS_DESEMBOLSADOS: 'Fondos entregados — por comprar',
  COMPRA_REGISTRADA: 'Compra realizada',
  COMPRADO_Y_ENTREGADO: 'Entregado al solicitante',
  DESCARGO_PENDIENTE_LIQUIDACION: 'Acta firmada',
  CERRADO_ARCHIVADO: 'Cerrado y archivado',
  RECHAZADO: 'Rechazado',
  ANULADO: 'Anulado',
}

function etiquetaEstado(estado) { return ETIQUETAS[estado] || estado }

function fecha(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' }) : 's/d'
}

const token = () => localStorage.getItem('sigta_token')

async function cargar() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const r = await fetch('/api/compras/solicitudes/', { headers: { Authorization: `Token ${token()}` } })
    const d = await r.json()
    if (!r.ok) await mostrarErrorRegla(d)
    if (!r.ok) throw new Error(d.detalle || 'No se pudieron cargar los expedientes.')
    expedientes.value = Array.isArray(d) ? d : (d.results || [])
    if (activo.value) activo.value = expedientes.value.find(e => e.id === activo.value.id) || null
  } catch (e) { errorCarga.value = e.message } finally {
    cargando.value = false
  }
}

function irA(id) {
  vista.value = id
  menuAbierto.value = false
  cerrar()
}

function abrir(e) {
  activo.value = e
  errorAccion.value = ''
  actaId.value = null
  actaLista.value = false
  pasoActual.value = 1
  modoGestion.value = false
  comprobante.value = null
  acta.value = null
  formCompra.monto_real = e.monto_desembolsado || ''
  formCompra.proveedor = ''
  formCompra.observacion_verificacion = ''
  formIngreso.cantidad_recibida = e.cantidad || 1
  formIngreso.responsable_recepcion = ''
  formIngreso.observacion_ingreso = ''
  formSalida.cantidad_entregada = e.cantidad_recibida || 1
  formSalida.entregado_a = e.receptor_acta?.nombre || ''
  formSalida.observacion_salida = ''
}

function cerrar() {
  if (procesando.value) return
  activo.value = null
  pasoActual.value = 1
  modoGestion.value = false
}

function abrirCompraDashboard(e) { vista.value = 'comprar'; abrir(e) }
async function verDetalle(e) {
  detalle.value = e; actasDetalle.value = []; errorDetalle.value = ''
  try {
    const r = await fetch(`/api/compras/solicitudes/${e.id}/actas-almacen/`, { headers: { Authorization: `Token ${token()}` } })
    const datos = await r.json()
    if (!r.ok) throw new Error(datos.detalle || 'No se pudieron consultar las actas.')
    if (detalle.value?.id === e.id) actasDetalle.value = datos
  } catch (error) { if (detalle.value?.id === e.id) errorDetalle.value = error.message }
}
const resumenRegistro = computed(() => {
  if (vista.value === 'comprar') return `Compra a ${formCompra.proveedor}: Bs. ${formCompra.monto_real}. Verificación: ${formCompra.observacion_verificacion || 'Sin observaciones'}.`
  if (vista.value === 'entrada') return `${formIngreso.cantidad_recibida} unidad(es) recibidas por ${formIngreso.responsable_recepcion}. ${formIngreso.observacion_ingreso || 'Sin observaciones'}.`
  if (vista.value === 'salida') return `${formSalida.cantidad_entregada} unidad(es) entregadas a ${formSalida.entregado_a}. ${formSalida.observacion_salida || 'Sin observaciones'}.`
  return 'Se archivará el acta generada con el PDF firmado por quien recibe y por el encargado de almacén.'
})
let numeroVisor = 0
async function verArchivo(url, nombreDocumento) {
  if (!url) return
  cerrarVisor()
  const numero = numeroVisor
  const operacion = { nombre: nombreDocumento, cargando: true, error: '', url: '', tipo: '', archivo: '' }
  visor.value = operacion
  try {
    const destino = new URL(url, window.location.origin)
    if (destino.origin !== window.location.origin || !/^\/(api|media)\//.test(destino.pathname)) throw new Error('El documento no pertenece al expediente.')
    const r = await fetch(destino.pathname, { headers: { Authorization: `Token ${token()}` } })
    if (!r.ok) throw new Error('No se pudo abrir el documento. Actualice el expediente y vuelva a intentarlo.')
    const blob = await r.blob()
    if (!visor.value || numero !== numeroVisor) return
    if (blob.type.includes('json') || blob.type.includes('text/html')) throw new Error('El servidor no devolvió el documento solicitado.')
    const pdf = (await blob.slice(0, 5).text()) === '%PDF-'
    if (!visor.value || numero !== numeroVisor) return
    const tipo = pdf ? 'application/pdf' : blob.type || 'application/octet-stream'
    Object.assign(visor.value, { url: URL.createObjectURL(new Blob([blob], { type: tipo })), tipo, archivo: nombreDocumento.replace(/[^\p{L}\p{N} -]/gu, '') + (pdf ? '.pdf' : tipo === 'image/jpeg' ? '.jpg' : tipo === 'image/png' ? '.png' : '.bin') })
  } catch (error) { if (visor.value && numero === numeroVisor) visor.value.error = error.message } finally { if (visor.value && numero === numeroVisor) visor.value.cargando = false }
}
function cerrarVisor() { numeroVisor++; if (visor.value?.url) URL.revokeObjectURL(visor.value.url); visor.value = null }

const mostrarLogout = ref(false)

function salir() {
  localStorage.removeItem('sigta_token')
  localStorage.removeItem('sigta_usuario')
  router.push('/login')
}

function confirmarSalida() {
  mostrarLogout.value = false
  salir()
}

async function accion(endpoint, cuerpo, esFormData = false, mensajeExito = 'Registro guardado correctamente.', mantenerAbierto = false) {
  procesando.value = true
  try {
    const headers = { Authorization: `Token ${token()}` }
    if (!esFormData) headers['Content-Type'] = 'application/json'
    const r = await fetch(`/api/compras/solicitudes/${activo.value.id}/${endpoint}/`, {
      method: 'POST',
      headers,
      body: esFormData ? cuerpo : JSON.stringify(cuerpo),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) await mostrarErrorRegla(d)
    if (!r.ok) throw new Error(d.detalle || Object.values(d)[0] || 'No fue posible completar la acción.')
    await cargar()
    if (mantenerAbierto) pasoActual.value = 2
    else { activo.value = null; pasoActual.value = 1 }
    await animarGuardado(mensajeExito)
    return d
  } catch (e) {
    errorAccion.value = e.message
  } finally {
    procesando.value = false
  }
}

/* --------- 0. Coordinación con Tesorería --------- */
const modoGestion = ref(false)
const formGestion = reactive({ gestion_estado: 'BUSCANDO', gestion_nota: '' })

async function confirmarFondos(e) {
  activo.value = e
  const firma = await solicitarFirma('Recepción de fondos de Tesorería', activo.value.codigo)
  if (!firma) return
  await accion('confirmar-recepcion-fondos', {firma}, false, 'Recepción de efectivo confirmada.')
}

async function completarPasoUno() {
  if (vista.value === 'comprar' && !activo.value.fondos_recibidos_en) {
    const firma = await solicitarFirma('Recepción de fondos de Tesorería', activo.value.codigo)
  if (!firma) return
  await accion('confirmar-recepcion-fondos', {firma}, false, 'Recepción de efectivo confirmada.', true)
    return
  }
  pasoActual.value = 2
}

function resumenExpediente(e) {
  if (vista.value === 'comprar') return `Bs ${e.monto_desembolsado || 's/d'} · ${e.cantidad} unid.`
  if (vista.value === 'entrada') return `${e.proveedor || 'Proveedor no indicado'} · ${e.cantidad} unid.`
  if (vista.value === 'salida') return `${e.cantidad_recibida || 0} unid. disponibles`
  return `${e.cantidad_entregada || 0} unid. para ${e.entregado_a || 'entrega'}`
}

function abrirGestion(e) {
  activo.value = e
  modoGestion.value = true
  formGestion.gestion_estado = e.gestion_estado || 'BUSCANDO'
  formGestion.gestion_nota = e.gestion_nota || ''
}

async function informarAvance() {
  await accion('actualizar-gestion', {
    gestion_estado: formGestion.gestion_estado,
    gestion_nota: formGestion.gestion_nota.trim(),
  }, false, 'Avance registrado correctamente.')
}


/* --------- 1. Realizar compra --------- */
const formCompra = reactive({ monto_real: '', proveedor: '', observacion_verificacion: '' })

function onComprobante(evento) { comprobante.value = evento.target.files?.[0] || null }

async function registrarCompra() {
  const datos = new FormData()
  datos.append('monto_real', formCompra.monto_real)
  datos.append('proveedor', formCompra.proveedor.trim())
  datos.append('componente_verificado', 'true')
  datos.append('observacion_verificacion', formCompra.observacion_verificacion.trim())
  datos.append('comprobante_compra', comprobante.value)
  await accion('registrar-compra', datos, true, 'Compra registrada correctamente.')
}

/* --------- 2. Entrada de almacén --------- */
const formIngreso = reactive({ cantidad_recibida: '', responsable_recepcion: '', observacion_ingreso: '' })

async function registrarEntrada() {
  await accion('registrar-ingreso-almacen', {
    cantidad_recibida: Number(formIngreso.cantidad_recibida),
    responsable_recepcion: formIngreso.responsable_recepcion.trim(),
    observacion_ingreso: formIngreso.observacion_ingreso.trim(),
  }, false, 'Entrada de almacén registrada correctamente.')
}

/* --------- 3. Salida de almacén --------- */
const formSalida = reactive({ cantidad_entregada: '', entregado_a: '', observacion_salida: '' })

async function registrarSalida() {
  await accion('registrar-despacho-almacen', {
    cantidad_entregada: Number(formSalida.cantidad_entregada),
    entregado_a: formSalida.entregado_a.trim(),
    observacion_salida: formSalida.observacion_salida.trim(),
  }, false, 'Salida de almacén registrada correctamente.')
}

/* --------- 4. Entrega con acta --------- */
function onActa(evento) { acta.value = evento.target.files?.[0] || null }

async function entregarConActa() {
  const datos = new FormData()
  if (!acta.value || !actaId.value || !actaLista.value) return
  datos.append('acta_conformidad', acta.value)
  datos.append('acta_id', actaId.value)
  await accion('entregar-con-acta', datos, true, 'Entrega registrada correctamente.')
}

async function registrarGestion() {
  if (vista.value === 'comprar') await registrarCompra()
  else if (vista.value === 'entrada') await registrarEntrada()
  else if (vista.value === 'salida') await registrarSalida()
  else await entregarConActa()
}

onMounted(cargar)
onUnmounted(cerrarVisor)
</script>

<style scoped>
/* Mismo distintivo de icono que el resto de los paneles por rol. */
aside button .icon-badge { flex-shrink: 0; width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }

*{box-sizing:border-box}.layout{min-height:100vh;background:var(--sigta-fondo);color:var(--sigta-texto);font-family:var(--sigta-fuente)}aside{position:fixed;inset:0 auto 0 0;width:var(--sigta-sidebar);background:var(--sigta-azul);color:var(--sigta-blanco);padding:22px 16px;display:flex;flex-direction:column}.brand,.profile{display:flex;align-items:center;gap:12px}.brand{padding:0 10px 20px;border-bottom:1px solid rgba(255,255,255,.2)}.brand>b{background:var(--sigta-mostaza);color:var(--sigta-azul);padding:14px 10px;border-radius:9px}.brand strong,.brand small,.profile b,.profile small{display:block}.brand strong{font-size:23px}.brand small,.profile small{color:var(--sigta-azul-texto-claro);margin-top:3px}.profile{padding:22px 10px}.profile>i{width:42px;height:42px;border-radius:50%;background:var(--sigta-mostaza);color:var(--sigta-azul);display:grid;place-items:center;font-style:normal;font-weight:900}aside>p{font-size:10px;color:var(--sigta-azul-texto-claro);font-weight:800;letter-spacing:1.4px;margin:14px 10px 8px}aside button{border:0;background:transparent;color:var(--sigta-blanco);border-radius:8px;padding:12px;display:flex;gap:11px;align-items:center;text-align:left;cursor:pointer;margin:2px 0;width:100%}aside button>span{font-size:10px;font-weight:900;width:28px}aside button :deep(.icono-sigta){flex-shrink:0}aside button em{margin-left:auto;background:rgba(255,255,255,.16);padding:2px 8px;border-radius:10px;font-style:normal}aside button.active,aside button:hover{background:rgba(255,255,255,.13)}.bottom{margin-top:auto;border-top:1px solid rgba(255,255,255,.2);padding-top:10px}.bottom button{width:100%}.bottom .logout{gap:14px!important;border:1px solid var(--sigta-mostaza)!important;border-radius:8px!important;background:transparent!important;color:#fff!important;box-shadow:inset 0 0 0 1px rgba(255,199,44,.35)!important;transition:transform .3s cubic-bezier(.34,1.55,.5,1),background .2s ease,color .2s ease,box-shadow .2s ease!important}.bottom .logout .icono-sigta{color:var(--sigta-mostaza);transition:color .2s ease}.bottom .logout:hover{background:#FFB300!important;color:var(--sigta-azul)!important;transform:scale(1.09)!important;box-shadow:0 14px 32px rgba(255,159,0,.55)!important}.bottom .logout:hover .icono-sigta{color:var(--sigta-azul)}main{margin-left:var(--sigta-sidebar);padding:30px 38px 55px;max-width:1650px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:27px}header small{color:var(--sigta-texto-suave)}h1{font-size:var(--sigta-titulo);margin:6px 0}header p{margin:0;color:var(--sigta-texto-suave)}.refresh{border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-azul);padding:10px 14px;border-radius:8px;cursor:pointer}.hero{background:linear-gradient(120deg,var(--sigta-azul),var(--sigta-azul-medio));color:var(--sigta-blanco);border-radius:13px;padding:28px 30px;display:flex;justify-content:space-between;align-items:center}.hero small,.panel-head small,.hoja-head small{font-size:10px;font-weight:800;letter-spacing:1.4px;color:var(--sigta-mostaza-clara)}.hero h2{font-size:24px;margin:7px 0}.hero p{margin:0;color:var(--sigta-azul-texto-claro)}.hero>span{width:68px;height:68px;border:1px solid var(--sigta-mostaza);border-radius:50%;display:grid;place-items:center;font-weight:900}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:18px 0}.stats article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:19px;display:flex;gap:13px;cursor:pointer}.stats i,.flow i{font-style:normal;width:37px;height:37px;border-radius:8px;display:grid;place-items:center;color:var(--sigta-blanco);font-size:10px;font-weight:900;flex-shrink:0}.blue{background:var(--sigta-azul)}.gold{background:var(--sigta-mostaza);color:var(--sigta-texto)!important}.green{background:var(--sigta-azul-medio)}.stats small,.stats b,.stats p{display:block}.stats b{font-size:25px;margin:3px 0}.stats p{font-size:11px;color:var(--sigta-texto-suave);margin:0}.panels{display:grid;grid-template-columns:2fr 1fr;gap:18px}.panel{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:11px;padding:22px}.panel-head h3{margin:5px 0 14px}.flow{width:100%;border:0;border-top:1px solid var(--sigta-borde-suave);background:var(--sigta-blanco);padding:15px 2px;display:flex;gap:13px;align-items:center;text-align:left;cursor:pointer}.flow div{flex:1}.flow b,.flow small{display:block}.flow small{color:var(--sigta-texto-suave);margin-top:4px}.flow>strong{font-size:20px}.copy{color:var(--sigta-texto-suave);font-size:12px;line-height:1.8}.copy a{color:var(--sigta-azul)}.wide{width:100%;padding:10px;border-radius:7px;border:1px solid var(--sigta-borde);cursor:pointer}.primary{background:var(--sigta-azul)!important;color:var(--sigta-blanco)!important;border-color:var(--sigta-azul)!important}.instruction{background:var(--sigta-mostaza-suave);border-left:4px solid var(--sigta-mostaza);padding:14px 17px;margin-bottom:17px;border-radius:7px}.instruction b,.instruction span{display:block}.instruction span{font-size:12px;color:var(--sigta-alerta);margin-top:4px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.cards article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:19px}.top{display:flex;justify-content:space-between;gap:8px}.top span{font-size:12px;font-weight:800;color:var(--sigta-azul)}.top em{font-size:10px;background:var(--sigta-azul-tenue);padding:4px 8px;border-radius:10px;font-style:normal;white-space:nowrap}.cards h3{font-size:17px;margin:15px 0 7px}.datos{list-style:none;margin:0 0 10px;padding:0;display:grid;gap:4px}.datos li{display:flex;justify-content:space-between;gap:10px;font-size:11px;border-bottom:1px dashed var(--sigta-borde-suave);padding-bottom:3px}.datos b{color:var(--sigta-texto-suave)}.datos span{color:var(--sigta-texto-suave);text-align:right}.actions{display:flex;gap:7px;border-top:1px solid var(--sigta-borde-suave);padding-top:13px;margin-top:10px}.actions button{flex:1;padding:9px 6px;border-radius:7px;border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-texto);font-weight:700;cursor:pointer}.actions button:disabled{opacity:.55;cursor:not-allowed}.empty{text-align:center;background:var(--sigta-blanco);border:1px dashed var(--sigta-borde);padding:65px;border-radius:10px;color:var(--sigta-texto-suave)}.empty>span{font-size:31px;color:var(--sigta-exito)}.empty h3{margin:10px 0 6px}.campo{display:block;margin:14px 0;font-size:12px;font-weight:700;color:var(--sigta-texto)}.campo input{display:block;width:100%;margin-top:6px;padding:9px 11px;border:1px solid var(--sigta-borde);border-radius:7px;font-family:inherit;font-size:13px;font-weight:400;color:var(--sigta-texto)}.situacion{font-size:11px;color:var(--sigta-texto-suave);background:var(--sigta-azul-tenue);border-radius:6px;padding:8px 10px;margin:0 0 10px}.situacion.aviso{background:var(--sigta-mostaza-suave);color:var(--sigta-alerta);font-weight:700}.error-linea{background:var(--sigta-error-fondo);color:var(--sigta-error);padding:10px 13px;border-radius:7px;font-size:12px;font-weight:700}.hoja{max-width:760px}.hoja-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.hoja-head h3{margin:5px 0 0}.documentos{display:flex;gap:12px;flex-wrap:wrap}.documentos a{color:var(--sigta-azul);font-size:12px}.detalle-modal-backdrop{position:fixed;inset:0;background:rgba(18,58,107,.55);display:grid;place-items:center;padding:20px;z-index:20}.detalle-modal{background:var(--sigta-blanco);border-radius:14px;width:min(700px,100%);max-height:88vh;display:flex;flex-direction:column}.detalle-modal-header{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--sigta-borde-suave)}.detalle-modal-header h3{margin:0}.detalle-modal-header small{color:var(--sigta-texto-suave)}.detalle-modal-close{border:0;background:transparent;font-size:20px;cursor:pointer;color:var(--sigta-texto-suave)}.detalle-modal-body{padding:20px 24px;overflow-y:auto;display:grid;gap:14px}.detalle-fila{display:grid;grid-template-columns:1fr 1fr;gap:14px}.detalle-campo b{display:block;font-size:11px;color:var(--sigta-texto-suave);margin-bottom:4px}.detalle-campo span,.detalle-campo p{font-size:13px;color:var(--sigta-texto);margin:0}@media(max-width:1050px){.stats{grid-template-columns:1fr 1fr}.panels{grid-template-columns:1fr}.cards{grid-template-columns:1fr 1fr}}@media(max-width:760px){aside{position:static;width:100%}main{margin:0;padding:20px}.stats,.cards{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column;gap:12px}.detalle-fila{grid-template-columns:1fr}}
/* El tema global de rol oculta el icono de .stats y apila la tarjeta en
   bloque (pensado para Admin); aquí se restaura el icono junto al texto. */
main .stats article{display:flex!important;align-items:center!important}
main .stats article>i.gold,main .stats article>i.blue,main .stats article>i.green{display:flex!important;align-items:center;justify-content:center}

/* Patrón maestro–detalle compartido con la vista de Tesorería. */
.gestion-tickets-layout{display:flex;gap:20px;height:calc(100vh - 160px);overflow:hidden;align-items:stretch;margin-top:15px}.gestion-left{width:35%;display:flex;flex-direction:column;background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:12px;overflow:hidden}.gestion-left-header{padding:15px 20px;border-bottom:1px solid var(--sigta-borde-suave);display:flex;justify-content:space-between;align-items:center;background:#f8fafc}.gestion-left-header h3{margin:0;font-size:14px}.badge{background:#fef9c3;color:#854d0e;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:700}.gestion-lista{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:8px}.empty-list{padding:20px;text-align:center;color:var(--sigta-texto-suave);font-size:13px}.ticket-item{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:8px;padding:12px;cursor:pointer;transition:.2s}.ticket-item:hover{border-color:var(--sigta-azul);background:#f8fafc}.ticket-item.activo{border-color:var(--sigta-azul);background:#f0f4f8;border-left:4px solid var(--sigta-azul)}.t-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px}.ticket-item h4{margin:0;font-size:14px;color:var(--sigta-azul)}.ticket-item p{margin:0;font-size:12px;color:var(--sigta-texto-suave);line-height:1.45}.item-meta{margin-top:6px!important;color:var(--sigta-mostaza-oscuro)!important;font-weight:700}.step-badge{font-size:10px;padding:3px 7px;border-radius:10px;text-transform:uppercase;font-weight:700;background:#dbeafe;color:#1e40af}.gestion-right{flex:1;display:flex;flex-direction:column;overflow:hidden}.ticket-header-card{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:12px;padding:20px;margin-bottom:15px}.ticket-header-card h2,.ticket-header-card h3{margin:0}.ticket-header-card>p{margin:8px 0;font-size:14px}.selector-vacio{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:var(--sigta-texto-suave)}.selector-vacio>span{font-size:30px;color:var(--sigta-exito)}.gestion-detalle-wrapper{flex:1;overflow-y:auto;padding-right:10px;display:flex;flex-direction:column}.codigo-badge{background:var(--sigta-azul);color:var(--sigta-blanco);padding:4px 10px;border-radius:20px;font-size:11px;font-weight:700}.t-meta{margin:0;font-size:12px;color:var(--sigta-texto-suave);display:flex;gap:15px}.workflow-card{flex:1;background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:12px;display:flex;flex-direction:column;overflow:hidden;margin-bottom:20px}.wf-header{padding:15px 20px;border-bottom:1px solid var(--sigta-borde-suave);font-weight:700;background:#f8fafc}.wf-body{flex:1;overflow-y:auto;padding:25px;display:flex;flex-direction:column;position:relative}.wf-body:before{content:'';position:absolute;left:45px;top:35px;bottom:35px;width:2px;background:var(--sigta-borde-suave);z-index:1}.wf-step{display:flex;margin-bottom:30px;position:relative;z-index:2}.wf-step:last-child{margin-bottom:0}.step-num{width:42px;height:42px;border-radius:50%;background:var(--sigta-borde);color:var(--sigta-texto-suave);display:grid;place-items:center;font-weight:700;flex-shrink:0;border:4px solid var(--sigta-blanco)}.step-content{margin-left:20px;flex:1;background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:15px 20px}.step-content h4{margin:0 0 5px;font-size:15px}.step-content>p{margin:0 0 15px;font-size:12px;color:var(--sigta-texto-suave)}.wf-step.active .step-num{background:var(--sigta-azul);color:var(--sigta-blanco);box-shadow:0 0 0 4px rgba(0,42,92,.1)}.wf-step.active .step-content{border-color:var(--sigta-azul);box-shadow:0 4px 12px rgba(0,0,0,.05)}.wf-step.completed .step-num{background:var(--sigta-azul-medio);color:var(--sigta-blanco)}.wf-step.completed .step-content,.wf-step.locked .step-content{background:#f8fafc}.wf-step.locked{opacity:.5;pointer-events:none}.step-form{margin-top:15px}.step-actions{display:flex;gap:10px}.reject{background:var(--sigta-blanco);border:1px solid var(--sigta-error);color:var(--sigta-error);padding:10px 20px;border-radius:6px;font-weight:700;cursor:pointer}.flex-btn{flex:1;text-align:center;justify-content:center;padding:10px;border-radius:6px;font-weight:700;cursor:pointer;border:none}.campo input{background:var(--sigta-blanco)}
@media(max-width:1050px){.gestion-tickets-layout{flex-direction:column;height:auto}.gestion-left{width:100%;height:300px}.gestion-right{min-height:650px}}@media(max-width:760px){.gestion-right{min-height:620px}.wf-body{padding:16px}.step-content{margin-left:10px;padding:14px}.t-meta{flex-direction:column;gap:4px}}
.almacen-vista>aside .alm-menu-item .icon-badge{background:var(--alm-icon-bg)!important;color:var(--alm-icon)!important;width:30px!important;height:30px}.alm-menu-item .icon-badge :deep(svg){color:inherit}.almacen-vista>aside .alm-menu-item .alm-menu-label{width:auto!important;background:transparent!important;color:inherit!important;font-size:13px!important;flex:1;font-weight:inherit}.almacen-vista>aside .alm-menu-item{background:transparent!important;color:#dbe7f6!important;border-left:3px solid transparent!important}.almacen-vista>aside .alm-menu-item.active{background:#ffffff22!important;color:var(--sigta-mostaza)!important;border-left-color:var(--sigta-mostaza)!important}.almacen-vista>aside .alm-menu-item:hover{background:#ffffff12!important}.almacen-vista>aside .brand-row{padding-bottom:18px;border-bottom:1px solid #ffffff25}.almacen-vista>aside .brand-row .brand{border-bottom:0!important;min-height:0!important;padding:0 8px!important}.wf-header{background:var(--sigta-azul);color:white}.wf-step .step-num{display:none}.wf-step .step-content{margin-left:0;min-width:0}.wf-body:before{display:none}.wf-body{overflow:visible}.workflow-card{flex:none}.t-meta{flex-wrap:wrap}.ticket-header-card>p{overflow-wrap:anywhere}.alm-error{padding:12px 16px;background:var(--sigta-error-fondo);color:var(--sigta-error);border-radius:8px;font-size:13px}.alm-confirmacion{padding:12px;background:#f4f7fb;border-radius:7px;color:var(--sigta-azul)!important}.alm-detalle{display:grid;gap:16px}.alm-actas-historial button{margin:8px 8px 0 0}.alm-pdf{width:100%;height:65dvh;border:1px solid var(--sigta-borde);border-radius:8px;margin-bottom:14px}.alm-imagen{display:block;max-width:100%;max-height:65dvh;object-fit:contain;margin:0 auto 16px}@media(max-width:760px){.step-actions{flex-wrap:wrap}.wf-body{padding:16px}.step-content{padding:16px}}
</style>
