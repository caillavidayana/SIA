<template>
  <div class="layout sigta-role-layout tesoreria-vista">
    <aside :class="{ abierto: menuAbierto }">
      <div class="brand-row">
        <div class="brand"><b><img src="/img/emi.jpg" alt="EMI"></b><div><strong>SIA</strong><small>Tesorería</small></div></div>
        <button type="button" class="menu-toggle" :aria-expanded="menuAbierto" aria-label="Mostrar opciones del menú" @click="menuAbierto = !menuAbierto"><span></span><span></span><span></span></button>
      </div>
      <p>CAJA CHICA</p>
      <button v-for="m in menu" :key="m.id" type="button" class="tes-menu-item" :class="{ active: vista === m.id }" @click="irA(m.id)"><span class="icon-badge" :style="{ '--tes-icon': m.color, '--tes-icon-bg': m.color + '26' }"><IconoSigta :nombre="m.icono" :tamano="16" /></span><span class="tes-menu-label">{{ m.nombre }}</span><em v-if="m.total !== undefined">{{ m.total }}</em></button>
      <div class="bottom"><button class="logout" @click="mostrarLogout = true"><IconoSigta nombre="salir" :tamano="18" /><span>Cerrar sesión</span></button></div>
    </aside>
    <LogoutModal :visible="mostrarLogout" @cancelar="mostrarLogout = false" @confirmar="confirmarSalida" />
    <TarjetaGuardado :visible="mostrarGuardado" :texto="textoGuardado" :tipo="tipoGuardado" @cerrar="ocultarGuardado" />

    <main>
      <header class="tes-page-header"><div><h1>{{ titulo }}</h1><p>{{ subtitulo }}</p></div><UsuarioHeader @actualizar="cargar" /></header>
      <p v-if="errorCarga" class="tes-error" role="alert">{{ errorCarga }}</p>
      <CajaChicaPanel v-if="vista==='resumen'||vista==='caja'" />
      <section v-if="vista === 'resumen'" class="stats">
        <button @click="irA('desembolso')"><i><IconoSigta nombre="compras" :tamano="20" /></i><div><small>Por desembolsar</small><b>{{ porDesembolsar.length }}</b><p>certificados por DAF</p></div></button>
        <button @click="irA('historial')"><i><IconoSigta nombre="historial" :tamano="20" /></i><div><small>Desembolsados</small><b>{{ desembolsados.length }}</b><p>entregas registradas</p></div></button>
        <article><i><IconoSigta nombre="etiqueta" :tamano="20" /></i><div><small>Monto desembolsado</small><b>{{ montoTotal }}</b><p>bolivianos en total</p></div></article>
        <article><i><IconoSigta nombre="solicitudes" :tamano="20" /></i><div><small>Expedientes</small><b>{{ expedientes.length }}</b><p>en el sistema</p></div></article>
      </section>
      <TesoreriaTabla v-if="vista === 'desembolso'" :registros="porDesembolsar" :cargando="cargando" @ver="abrir" />
      <section v-else-if="vista === 'historial'">
        <div class="tes-hist-filtros"><label>Desde<input v-model="desdeHist" type="date"></label><label>Hasta<input v-model="hastaHist" type="date"></label><button v-if="desdeHist || hastaHist" class="sia-secondary" @click="desdeHist = ''; hastaHist = ''">Limpiar fechas</button><span>Fecha de registro del desembolso</span></div>
        <TesoreriaTabla :registros="historialFiltrado" :cargando="cargando" historial @ver="verDetalle" />
      </section>
    </main>

    <ModalSia v-if="expedienteActivo" :titulo="`Revisión y desembolso · ${expedienteActivo.codigo}`" amplio :ocupado="procesando" @cerrar="cerrarEntrega">
      <ResumenExpediente :registro="expedienteActivo" requerimiento />
      <section class="tes-workflow">
        <h3 class="tes-section-head">{{ pasoActual === 1 ? 'Revisión y desembolso' : 'Registro de entrega de fondos' }}</h3>
        <div class="tes-section-body">
          <template v-if="pasoActual === 1">
            <h4>Revisión de documentos autorizados</h4><p class="tes-help">Revise los documentos remitidos por la DAF antes de continuar.</p>
            <div v-for="doc in documentos(expedienteActivo)" :key="doc.campo" class="tes-documento"><strong>{{ doc.nombre }}</strong><button v-if="doc.url" class="sia-primary" :disabled="cargandoDocumento" @click="verArchivo(doc.url, doc.nombre)">Ver documento</button><span v-else>No adjunto</span></div>
            <p v-if="recuperandoRecibo" class="tes-help" role="status">Consultando si existe un recibo pendiente de firma…</p>
            <p v-else-if="recibo" class="tes-help">Este expediente ya tiene un recibo generado. Puede continuar para adjuntar su copia firmada.</p>
            <div class="tes-actions"><button class="tes-cancelar" @click="cerrarEntrega">Cancelar</button><button class="sia-primary tes-flex" :disabled="recuperandoRecibo" @click="pasoActual = 2">Aprobar y continuar</button></div>
          </template>
          <template v-else>
            <p class="tes-help">Complete los datos, genere el recibo y adjunte el PDF firmado por ambas partes antes de registrar la entrega.</p>
            <div class="tes-form-grid">
              <label class="sia-field">Método de desembolso<select v-model="form.tipo_desembolso" :disabled="procesando"><option value="">Seleccione un método</option><option>Efectivo</option><option>Transferencia</option><option>QR</option></select></label>
              <label class="sia-field">Monto entregado (Bs.)<input v-model="form.monto_desembolsado" :disabled="procesando" type="number" min="0.01" step="0.01" placeholder="0.00"></label>
              <label class="sia-field tes-full">Nombre completo de quien recibe<input v-model="form.responsable_adquisicion" :disabled="procesando" type="text" maxlength="150" autocomplete="name" placeholder="Nombres y apellidos"></label>
              <div class="tes-entrega tes-full"><small>Entrega los fondos</small><strong>{{ nombre }}</strong><span>Tesorería · usuario autenticado</span></div>
            </div>
            <section class="tes-recibo">
              <h4>1. Generar e imprimir el recibo</h4>
              <p class="tes-help">El PDF incluye el requerimiento, el importe, el método de pago y los nombres de quien entrega y quien recibe, con espacios para ambas firmas.</p>
              <button class="sia-primary" :disabled="procesando || !datosValidos" @click="generarRecibo">{{ procesando ? 'Procesando…' : recibo ? 'Generar un nuevo recibo' : 'Generar recibo PDF' }}</button>
              <div v-if="recibo" class="tes-recibo-listo"><strong>Recibo {{ recibo.referencia }}</strong><button class="sia-secondary" :disabled="cargandoDocumento" @click="verArchivo(recibo.original_url, 'Recibo de entrega de fondos')">Ver e imprimir PDF</button><button class="sia-secondary" @click="descargarOriginal">Descargar PDF</button></div>
            </section>
            <section v-if="recibo" class="tes-recibo">
              <h4>2. Adjuntar el recibo firmado</h4><p class="tes-help">Imprima el recibo, obtenga las firmas de quien entrega y quien recibe, y suba el mismo documento escaneado en PDF.</p>
              <label class="sia-field">PDF con ambas firmas<ArchivoInput type="file" :disabled="procesando" accept="application/pdf,.pdf" @change="seleccionarArchivo($event, 'firmado')" /></label>
              <p v-if="firmadoFile" class="tes-help">Seleccionado: {{ firmadoFile.name }}</p>
              <label v-if="form.tipo_desembolso !== 'Efectivo'" class="sia-field">Comprobante de {{ form.tipo_desembolso }} (obligatorio)<ArchivoInput :key="form.tipo_desembolso" type="file" :disabled="procesando" accept="application/pdf,image/png,image/jpeg,image/webp,.pdf,.png,.jpg,.jpeg,.webp" @change="seleccionarArchivo($event, 'comprobante')" /></label>
              <p v-if="comprobanteFile" class="tes-help">Comprobante: {{ comprobanteFile.name }}</p>
              <label class="tes-check"><input v-model="firmasConfirmadas" :disabled="procesando" type="checkbox">Confirmo que el PDF adjunto corresponde a este recibo y contiene las firmas de quien recibe y quien entrega los fondos.</label>
            </section>
            <div class="tes-actions"><button class="sia-secondary" :disabled="procesando" @click="pasoActual = 1">Volver a documentos</button><button class="sia-primary tes-flex" :disabled="!puedeRegistrar || procesando" @click="desembolsar">{{ procesando ? 'Registrando…' : 'Registrar desembolso con respaldo firmado' }}</button></div>
          </template>
          <p v-if="errorAccion" class="tes-error" role="alert">{{ errorAccion }}</p>
        </div>
      </section>
    </ModalSia>

    <ModalSia v-if="detalle" :titulo="`Historial de desembolso · ${detalle.codigo}`" amplio @cerrar="detalle = null">
      <ResumenExpediente :registro="detalle" requerimiento />
      <section class="tes-workflow"><h3 class="tes-section-head">Datos de la entrega y respaldo para auditoría</h3><div class="tes-section-body">
        <dl class="tes-auditoria"><div><dt>Monto desembolsado</dt><dd>Bs. {{ detalle.monto_desembolsado }}</dd></div><div><dt>Método de pago</dt><dd>{{ detalle.tipo_desembolso || 'Sin registro' }}</dd></div><div><dt>Nombre completo de quien recibe</dt><dd>{{ reciboConfirmado?.datos.recibe || detalle.responsable_adquisicion || 'Sin registro' }}</dd></div><div><dt>Nombre completo de quien entrega</dt><dd>{{ reciboConfirmado?.datos.entrega || entregaAnterior?.nombre_firmante || 'Sin registro' }}</dd></div><div><dt>Fecha de registro del desembolso</dt><dd>{{ fechaHora(reciboConfirmado?.confirmado_en || entregaAnterior?.creado_en) }}</dd></div><div><dt>Estado actual</dt><dd>{{ detalle.estado_nombre || detalle.estado }}</dd></div><div><dt>Recepción confirmada por Compras</dt><dd>{{ detalle.fondos_recibidos_por || 'Pendiente' }}</dd></div><div><dt>Fecha de recepción</dt><dd>{{ fechaHora(detalle.fondos_recibidos_en) }}</dd></div></dl>
        <p v-if="cargandoHistorial" role="status">Consultando documentos de auditoría…</p>
        <p v-if="errorHistorial" class="tes-error" role="alert">{{ errorHistorial }}</p>
        <template v-if="reciboConfirmado">
          <p class="tes-help">Referencia del recibo: {{ reciboConfirmado.referencia }}</p>
          <div class="tes-documento"><strong>Recibo original generado por el sistema</strong><button class="sia-primary" @click="verArchivo(reciboConfirmado.original_url, 'Recibo original')">Ver PDF</button></div>
          <div class="tes-documento"><strong>Recibo con las firmas de quien recibe y quien entrega</strong><button class="sia-primary" @click="verArchivo(reciboConfirmado.firmado_url, 'Recibo firmado')">Ver PDF firmado</button></div>
          <div v-if="reciboConfirmado.comprobante_url" class="tes-documento"><strong>Comprobante de {{ reciboConfirmado.datos.metodo }}</strong><button class="sia-primary" @click="verArchivo(reciboConfirmado.comprobante_url, 'Comprobante de desembolso')">Ver comprobante</button></div>
          <div v-if="reciboConfirmado.saldo_confirmado_url" class="tes-documento"><strong>Saldo real después del desembolso</strong><button class="sia-primary" @click="verArchivo(reciboConfirmado.saldo_confirmado_url, 'Constancia de saldo confirmado')">Ver saldo en PDF</button></div>
          <details class="tes-snapshot"><summary>Datos conservados en el recibo original</summary><dl class="tes-auditoria"><div v-for="campo in snapshotCampos" :key="campo[0]"><dt>{{ campo[0] }}</dt><dd>{{ reciboConfirmado.datos[campo[1]] }}</dd></div></dl></details>
        </template>
        <template v-else-if="!cargandoHistorial && !errorHistorial"><p class="tes-help">Este desembolso se registró antes del nuevo recibo firmado. Se muestran los respaldos existentes.</p><div v-if="detalle.comprobante_desembolso" class="tes-documento"><strong>Comprobante de desembolso archivado</strong><button class="sia-primary" @click="verArchivo(detalle.comprobante_desembolso, 'Comprobante archivado')">Ver comprobante</button></div><div v-if="entregaAnterior" class="tes-documento"><strong>Constancia del registro de desembolso</strong><button class="sia-primary" @click="verArchivo(`/api/compras/solicitudes/${detalle.id}/documentos/${entregaAnterior.id}/pdf/`, 'Constancia de desembolso')">Ver PDF</button></div></template>
        <h4 class="tes-doc-titulo">Documentos del expediente</h4><div v-for="doc in documentos(detalle, true).filter(d => d.url)" :key="doc.campo" class="tes-documento"><strong>{{ doc.nombre }}</strong><button class="sia-primary" @click="verArchivo(doc.url, doc.nombre)">Ver documento</button></div>
        <p v-if="detalle.motivo_rechazo">Motivo de rechazo: {{ detalle.motivo_rechazo }}</p>
      </div></section>
    </ModalSia>

    <ModalSia v-if="visor" :titulo="visor.nombre" amplio @cerrar="cerrarVisor">
      <p v-if="visor.cargando" role="status">Abriendo documento…</p><p v-if="visor.error" class="tes-error" role="alert">{{ visor.error }}</p>
      <template v-if="visor.url"><iframe v-if="visor.tipo === 'application/pdf'" :src="visor.url" :title="visor.nombre" class="tes-pdf"></iframe><img v-else-if="visor.tipo.startsWith('image/')" :src="visor.url" :alt="visor.nombre" class="tes-imagen"><p v-else>Este formato se puede descargar para abrirlo con su aplicación correspondiente.</p><a :href="visor.url" :download="visor.archivo" class="sia-secondary">Descargar documento</a></template>
    </ModalSia>
  </div>
</template>

<script setup>
import CajaChicaPanel from '../components/CajaChicaPanel.vue'
import { mostrarErrorRegla } from '../utils/errorRegla'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import LogoutModal from '../components/LogoutModal.vue'
import IconoSigta from '../components/IconoSigta.vue'
import TarjetaGuardado from '../components/TarjetaGuardado.vue'
import ResumenExpediente from '../components/ResumenExpediente.vue'
import ModalSia from '../components/ModalSia.vue'
import TesoreriaTabla from '../components/TesoreriaTabla.vue'
import { usarGuardado } from '../utils/guardado.js'

const router = useRouter()
const { mostrar: mostrarGuardado, texto: textoGuardado, tipo: tipoGuardado, animar: animarGuardado, ocultar: ocultarGuardado } = usarGuardado()
const usuario = JSON.parse(localStorage.getItem('sigta_usuario') || '{}')
const nombre = computed(() => usuario.nombre_completo || usuario.nombre || 'Tesorería')
const vista = ref('resumen'), menuAbierto = ref(false), expedientes = ref([]), cargando = ref(false), procesando = ref(false)
const expedienteActivo = ref(null), detalle = ref(null), pasoActual = ref(1), errorCarga = ref(''), errorAccion = ref('')
const recibo = ref(null), firmadoFile = ref(null), comprobanteFile = ref(null), firmasConfirmadas = ref(false)
const recuperandoRecibo = ref(false)
let aperturaEntrega = 0
const form = reactive({ monto_desembolsado: '', responsable_adquisicion: '', tipo_desembolso: '' })
const desdeHist = ref(''), hastaHist = ref(''), recibosHistorial = ref([]), documentosHistorial = ref([]), cargandoHistorial = ref(false), errorHistorial = ref('')
const visor = ref(null), cargandoDocumento = ref(false), mostrarLogout = ref(false)
const token = () => localStorage.getItem('sigta_token')
const porDesembolsar = computed(() => expedientes.value.filter(e => e.estado === 'APROBADO_PARA_DESEMBOLSO'))
const desembolsados = computed(() => expedientes.value.filter(e => Number(e.monto_desembolsado) > 0))
const montoTotal = computed(() => desembolsados.value.reduce((total, e) => total + Number(e.monto_desembolsado || 0), 0).toLocaleString('es-BO', { minimumFractionDigits: 2 }))
const menu = computed(() => [{ id: 'resumen', icono: 'inicio', nombre: 'Dashboard', color: '#F2C400' }, { id: 'caja', icono: 'compras', nombre: 'Control de Caja Chica', color: '#123A6B' }, { id: 'desembolso', icono: 'compras', nombre: 'Desembolsar dinero', total: porDesembolsar.value.length, color: '#C79A1E' }, { id: 'historial', icono: 'historial', nombre: 'Historial', total: desembolsados.value.length, color: '#6B7C93' }])
const titulo = computed(() => ({ caja: 'Control de Caja Chica', resumen: 'Dashboard de Tesorería', desembolso: 'Desembolsar dinero', historial: 'Historial de desembolsos' })[vista.value])
const subtitulo = computed(() => ({ caja: 'Fondo mensual, compromisos y saldo disponible.', resumen: 'Entrega de fondos de Caja Chica para las compras autorizadas.', desembolso: 'Expedientes certificados por DAF pendientes de entrega de fondos.', historial: 'Datos de entrega, recibos firmados y comprobantes para auditoría.' })[vista.value])
const datosValidos = computed(() => {
  const partes = form.responsable_adquisicion.trim().split(/\s+/)
  return partes.length >= 2 && partes.every(p => /\p{L}/u.test(p)) && /^\d+(?:\.\d{1,2})?$/.test(String(form.monto_desembolsado)) && Number(form.monto_desembolsado) > 0 && ['Efectivo', 'Transferencia', 'QR'].includes(form.tipo_desembolso)
})
const puedeRegistrar = computed(() => datosValidos.value && recibo.value && firmadoFile.value && firmasConfirmadas.value && (form.tipo_desembolso === 'Efectivo' || comprobanteFile.value))
const reciboConfirmado = computed(() => recibosHistorial.value.find(r => r.confirmado_en))
const entregaAnterior = computed(() => documentosHistorial.value.find(d => d.tipo === 'Constancia de desembolso'))
const historialFiltrado = computed(() => desembolsados.value.filter(e => {
  const registro = e.tesoreria_fecha
  const dia = registro ? new Date(registro).toLocaleDateString('sv-SE', { timeZone: 'America/La_Paz' }) : ''
  return (!desdeHist.value || dia >= desdeHist.value) && (!hastaHist.value || dia <= hastaHist.value)
}))
const snapshotCampos = [['Expediente', 'codigo'], ['Requerimiento', 'titulo'], ['Solicitante', 'solicitante'], ['Área', 'area'], ['Quien recibe', 'recibe'], ['Quien entrega', 'entrega'], ['Método', 'metodo'], ['Monto (Bs.)', 'monto'], ['Fecha de emisión', 'fecha']]
function fechaHora(valor) { return valor ? new Date(valor).toLocaleString('es-BO', { timeZone: 'America/La_Paz' }) : 'Sin registro' }
function documentos(e, todos = false) {
  const campos = [['poa', 'POA'], ['proforma', 'Proforma / cotización'], ['informe', 'Informe técnico'], ['pedido', 'Proveído'], ['certificacion_presupuestaria', 'Certificado presupuestario']]
  if (todos) campos.push(['comprobante_compra', 'Comprobante de compra'], ['factura', 'Factura'], ['acta_conformidad', 'Acta de conformidad'], ['fotograma', 'Evidencia de entrega'])
  return campos.map(([campo, nombre]) => ({ campo, nombre, url: e[campo] }))
}
async function api(url, options = {}) {
  const r = await fetch(url, { ...options, headers: { Authorization: `Token ${token()}`, ...options.headers } })
  const datos = await r.json().catch(() => ({}))
  if (!r.ok) await mostrarErrorRegla(datos)
  if (!r.ok) throw new Error(datos.detalle || Object.values(datos)[0] || 'No fue posible completar la operación.')
  return datos
}
async function cargar() {
  cargando.value = true; errorCarga.value = ''
  try {
    const datos = await api('/api/compras/solicitudes/?tesoreria=1')
    expedientes.value = Array.isArray(datos) ? datos : datos.results || []
  } catch (e) { errorCarga.value = e.message } finally { cargando.value = false }
}
function irA(id) { vista.value = id; menuAbierto.value = false; expedienteActivo.value = null; detalle.value = null }
async function abrir(e) {
  const apertura = ++aperturaEntrega
  recuperandoRecibo.value = true
  expedienteActivo.value = e; pasoActual.value = 1; errorAccion.value = ''; recibo.value = null
  Object.assign(form, { monto_desembolsado: e.monto_estimado || '', responsable_adquisicion: '', tipo_desembolso: '' })
  firmadoFile.value = null; comprobanteFile.value = null; firmasConfirmadas.value = false
  try {
    const existentes = await api(`/api/compras/solicitudes/${e.id}/recibos-tesoreria/`)
    if (apertura !== aperturaEntrega || expedienteActivo.value?.id !== e.id) return
    const anterior = existentes.find(r => r.puede_reanudar)
    if (anterior) {
      Object.assign(form, { monto_desembolsado: anterior.datos.monto, responsable_adquisicion: anterior.datos.recibe, tipo_desembolso: anterior.datos.metodo })
      await nextTick()
      if (apertura === aperturaEntrega && expedienteActivo.value?.id === e.id) recibo.value = anterior
    }
  } catch (error) { if (apertura === aperturaEntrega && expedienteActivo.value?.id === e.id) errorAccion.value = 'No se pudo recuperar el recibo anterior. Puede generar uno nuevo después de revisar los documentos.' }
  finally { if (apertura === aperturaEntrega) recuperandoRecibo.value = false }
}
function cerrarEntrega() { if (!procesando.value) expedienteActivo.value = null }
watch(() => [form.monto_desembolsado, form.responsable_adquisicion, form.tipo_desembolso], () => { recibo.value = null; firmadoFile.value = null; comprobanteFile.value = null; firmasConfirmadas.value = false })
function seleccionarArchivo(event, tipo) {
  const archivo = event.target.files?.[0] || null
  if (tipo === 'firmado') { firmadoFile.value = null; firmasConfirmadas.value = false } else comprobanteFile.value = null
  errorAccion.value = ''
  if (!archivo) return
  if (archivo.size > 10 * 1024 * 1024 || !archivo.size) { errorAccion.value = 'El archivo debe tener contenido y pesar hasta 10 MB.'; event.target.value = ''; return }
  if (tipo === 'firmado' && !/\.pdf$/i.test(archivo.name)) { errorAccion.value = 'El recibo firmado debe ser un PDF.'; event.target.value = ''; return }
  if (tipo === 'firmado') firmadoFile.value = archivo; else comprobanteFile.value = archivo
}
async function generarRecibo() {
  if (!datosValidos.value || procesando.value) return
  procesando.value = true; errorAccion.value = ''
  try {
    recibo.value = await api(`/api/compras/solicitudes/${expedienteActivo.value.id}/recibos-tesoreria/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    firmadoFile.value = null; comprobanteFile.value = null; firmasConfirmadas.value = false
    await verArchivo(recibo.value.original_url, 'Recibo de entrega de fondos')
  } catch (e) { errorAccion.value = e.message } finally { procesando.value = false }
}
async function desembolsar() {
  if (!puedeRegistrar.value || procesando.value) return
  procesando.value = true; errorAccion.value = ''
  try {
    const body = new FormData()
    for (const [clave, valor] of Object.entries(form)) body.append(clave, String(valor).trim())
    body.append('recibo_id', recibo.value.id); body.append('recibo_firmado', firmadoFile.value)
    if (comprobanteFile.value) body.append('comprobante_desembolso', comprobanteFile.value)
    await api(`/api/compras/solicitudes/${expedienteActivo.value.id}/desembolsar/`, { method: 'POST', body })
    expedienteActivo.value = null
    await cargar()
    await animarGuardado('Desembolso registrado. El recibo original, el PDF firmado y sus comprobantes están disponibles en el historial.')
  } catch (e) { errorAccion.value = e.message } finally { procesando.value = false }
}
async function verDetalle(e) {
  detalle.value = e; recibosHistorial.value = []; documentosHistorial.value = []; errorHistorial.value = ''; cargandoHistorial.value = true
  try {
    const resultados = await Promise.allSettled([api(`/api/compras/solicitudes/${e.id}/recibos-tesoreria/`), api(`/api/compras/solicitudes/${e.id}/documentos/`)])
    if (detalle.value?.id !== e.id) return
    if (resultados[0].status === 'fulfilled') recibosHistorial.value = resultados[0].value; else errorHistorial.value = 'No fue posible consultar los recibos de auditoría. Cierre y vuelva a abrir el expediente.'
    if (resultados[1].status === 'fulfilled') documentosHistorial.value = resultados[1].value; else errorHistorial.value ||= 'No fue posible consultar las constancias del expediente.'
  } finally { if (detalle.value?.id === e.id) cargandoHistorial.value = false }
}
async function obtenerArchivo(url) {
  const destino = new URL(url, window.location.origin)
  if (destino.origin !== window.location.origin || !/^\/(api|media)\//.test(destino.pathname)) throw new Error('El enlace no corresponde a un documento del expediente.')
  const r = await fetch(destino.pathname, { headers: { Authorization: `Token ${token()}` } })
  if (!r.ok) throw new Error('No fue posible abrir el archivo subido. Actualice el expediente e intente nuevamente.')
  const blob = await r.blob()
  if (blob.type.includes('json') || blob.type.includes('text/html')) throw new Error('El servidor no devolvió el documento solicitado.')
  return blob
}
async function verArchivo(url, nombreDocumento) {
  if (!url || cargandoDocumento.value) return
  cerrarVisor()
  const sesion = { nombre: nombreDocumento, cargando: true, error: '', url: '', tipo: '', archivo: '' }
  visor.value = sesion; cargandoDocumento.value = true
  try {
    const blob = await obtenerArchivo(url)
    if (visor.value?.nombre !== nombreDocumento) return
    const pdf = (await blob.slice(0, 5).text()) === '%PDF-'
    const tipo = pdf ? 'application/pdf' : blob.type || 'application/octet-stream'
    Object.assign(visor.value, { url: URL.createObjectURL(new Blob([blob], { type: tipo })), tipo, archivo: nombreDocumento.replace(/[^\p{L}\p{N} -]/gu, '') + (pdf ? '.pdf' : tipo === 'image/png' ? '.png' : tipo === 'image/jpeg' ? '.jpg' : tipo === 'image/webp' ? '.webp' : '.bin') })
  } catch (e) { if (visor.value) visor.value.error = e.message } finally { if (visor.value) visor.value.cargando = false; cargandoDocumento.value = false }
}
function cerrarVisor() { if (visor.value?.url) URL.revokeObjectURL(visor.value.url); visor.value = null }
async function descargarOriginal() {
  try {
    const blob = await obtenerArchivo(recibo.value.original_url), url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `recibo-${recibo.value.referencia}.pdf`; a.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) { errorAccion.value = e.message }
}
function confirmarSalida() { mostrarLogout.value = false; localStorage.removeItem('sigta_token'); localStorage.removeItem('sigta_usuario'); router.push('/login') }
onMounted(cargar)
onUnmounted(cerrarVisor)
</script>

<style scoped>
*{box-sizing:border-box}.layout{min-height:100vh;font-family:var(--sigta-fuente);color:var(--sigta-texto)}aside{position:fixed;inset:0 auto 0 0;width:var(--sigta-sidebar);display:flex;flex-direction:column;z-index:20;overflow:auto}.brand{display:flex;align-items:center;gap:12px}.brand>b{width:48px;height:48px;border-radius:10px;overflow:hidden;background:white!important}.brand img{width:100%;height:100%;object-fit:contain}.brand strong,.brand small{display:block}.brand small{margin-top:4px;color:var(--sigta-azul-texto-claro)}aside>p{margin:18px 12px 10px}.tesoreria-vista>aside .brand-row{border-bottom:1px solid #ffffff25;padding-bottom:18px}.tesoreria-vista>aside .brand-row .brand{border-bottom:0!important;min-height:0!important;padding:0 8px!important}.tesoreria-vista>aside .tes-menu-item{display:flex;align-items:center;gap:12px;min-height:44px;width:100%;border:0;border-left:3px solid transparent!important;padding:0 12px;margin:3px 0;border-radius:8px;background:transparent!important;color:#dbe7f6!important;font:inherit;font-size:13px;cursor:pointer;text-align:left}.tesoreria-vista>aside .tes-menu-item.active{background:#ffffff22!important;border-left-color:var(--sigta-mostaza)!important;color:var(--sigta-mostaza)!important;font-weight:700}.tesoreria-vista>aside .tes-menu-item:hover{background:#ffffff12!important}.tesoreria-vista>aside .tes-menu-item .icon-badge{display:grid;place-items:center;width:30px!important;height:30px;border-radius:8px;flex-shrink:0;color:var(--tes-icon)!important;background:var(--tes-icon-bg)!important}.tes-menu-item .icon-badge :deep(svg){color:inherit}.tesoreria-vista>aside .tes-menu-label{width:auto!important;background:transparent!important;color:inherit!important;font-size:13px!important;flex:1}.tes-menu-item em{font-style:normal;font-size:11px;background:#ffffff25;border-radius:12px;padding:3px 8px}.tes-menu-item.active em{background:var(--sigta-mostaza);color:var(--sigta-azul)}.bottom{margin-top:auto;padding-top:20px}.bottom .logout{width:100%;display:flex;align-items:center;justify-content:center;gap:12px;border:1px solid var(--sigta-mostaza)!important;border-radius:8px;background:transparent!important;color:white!important;cursor:pointer;font:inherit;font-weight:700}.bottom .logout span{width:auto!important;color:inherit!important;background:transparent!important}.bottom .logout :deep(svg){color:var(--sigta-mostaza)}main{margin-left:var(--sigta-sidebar);padding:30px;min-width:0}.tes-page-header{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:24px}.tes-page-header h1{margin:0 0 6px;font-size:26px;color:var(--sigta-azul)}.tes-page-header p{margin:0;font-size:13px;color:var(--sigta-texto-suave)}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.stats>button,.stats>article{display:flex;align-items:center;gap:14px;border:1px solid var(--sigta-borde);border-top:4px solid var(--sigta-mostaza);border-radius:12px;background:white;padding:22px 18px;text-align:left;color:var(--sigta-azul);font:inherit;min-width:0}.stats>button{cursor:pointer}.stats i{display:grid;place-items:center;flex-shrink:0;width:38px;height:38px;background:var(--sigta-azul);color:white;border-radius:8px}.stats small{display:block;text-transform:uppercase;font-size:11px;font-weight:800;color:var(--sigta-texto-suave)}.stats b{display:block;font-size:26px;margin-top:6px;overflow-wrap:anywhere}.stats p{margin:8px 0 0;font-size:12px;color:var(--sigta-texto-suave)}.tes-hist-filtros{display:flex;align-items:flex-end;flex-wrap:wrap;gap:14px;padding:18px;background:white;border:1px solid var(--sigta-borde);border-radius:10px}.tes-hist-filtros label{font-size:12px;font-weight:700}.tes-hist-filtros input{display:block;margin-top:6px;padding:9px;border:1px solid var(--sigta-borde);border-radius:7px;font:inherit}.tes-hist-filtros span{margin-left:auto;font-size:12px;color:var(--sigta-texto-suave)}.tes-workflow{border:1px solid var(--sigta-borde);border-radius:10px;overflow:hidden;margin-top:22px}.tes-section-head{background:var(--sigta-azul);color:white;margin:0;padding:16px 20px;font-size:15px}.tes-section-body{padding:24px}.tes-section-body h4{margin:0 0 8px;font-size:15px;color:var(--sigta-azul)}.tes-help{font-size:13px;line-height:1.6;color:var(--sigta-texto-suave);margin:8px 0 16px}.tes-documento{display:flex;justify-content:space-between;align-items:center;gap:14px;border:1px solid #e2ebf5;border-radius:8px;background:#f7f9fc;padding:13px 15px;margin-bottom:10px;font-size:13px}.tes-documento button{font-size:12px;white-space:nowrap}.tes-documento>span{font-size:12px;color:var(--sigta-texto-suave)}.tes-actions{display:flex;gap:12px;margin-top:24px;flex-wrap:wrap}.tes-flex{flex:1}.tes-cancelar{border:1px solid var(--sigta-error);background:white;color:var(--sigta-error);padding:10px 18px;border-radius:8px;cursor:pointer;font:inherit;font-weight:700}.tes-form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.tes-form-grid .sia-field{margin:0}.tes-full{grid-column:1/-1}.tes-entrega{padding:15px;background:#f4f7fb;border-radius:8px}.tes-entrega small,.tes-entrega strong,.tes-entrega span{display:block}.tes-entrega strong{margin:5px 0}.tes-entrega span{font-size:12px;color:var(--sigta-texto-suave)}.tes-recibo{border:1px solid var(--sigta-borde);padding:18px;border-radius:9px;margin-top:22px}.tes-recibo-listo{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:16px}.tes-recibo-listo strong{font-size:12px;overflow-wrap:anywhere;width:100%}.tes-check{display:flex;align-items:flex-start;gap:10px;font-size:13px;line-height:1.6}.tes-check input{margin-top:5px;flex-shrink:0}.tes-error{color:var(--sigta-error);background:var(--sigta-error-fondo);padding:12px 16px;border-radius:8px;font-size:13px}.tes-auditoria{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 0 22px}.tes-auditoria>div{background:#f5f8fc;border-radius:7px;padding:13px}.tes-auditoria dt{font-size:12px;color:var(--sigta-texto-suave)}.tes-auditoria dd{margin:6px 0 0;font-size:13px;overflow-wrap:anywhere}.tes-doc-titulo{margin-top:24px!important}.tes-snapshot{margin:20px 0}.tes-snapshot summary{cursor:pointer;font-weight:700;font-size:13px;padding:12px 0}.tes-pdf{width:100%;height:65dvh;border:1px solid var(--sigta-borde);border-radius:8px;margin-bottom:14px}.tes-imagen{display:block;max-width:100%;max-height:65dvh;object-fit:contain;margin:0 auto 16px}@media(max-width:1100px){.stats{grid-template-columns:1fr 1fr}}@media(max-width:760px){aside{position:relative;width:100%}main{margin:0;padding:20px}.tes-page-header{flex-wrap:wrap}.stats{grid-template-columns:1fr 1fr}.stats>button,.stats>article{padding:16px;gap:10px}.stats b{font-size:22px}.tes-form-grid,.tes-auditoria{grid-template-columns:1fr}.tes-section-body{padding:16px}.tes-documento{flex-wrap:wrap}.tes-actions{flex-direction:column}.tes-hist-filtros span{width:100%;margin:0}}@media(max-width:430px){.stats{grid-template-columns:1fr}}
</style>
