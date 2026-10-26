<template>
  <div class="sigta-role-layout">
    <DafMenu />

    <main class="main-content">

      <header class="barra-perfil">
        <div>
          <h1>Emitir Certificaci&oacute;n</h1>
          <p>Certificaci&oacute;n presupuestaria de los expedientes de compra evaluados.</p>
        </div>

        <UsuarioHeader @actualizar="cargar" />
      </header>

      <section class="cert-bandeja" aria-labelledby="pendientes-cert">
        <div class="cert-bandeja-head">
          <div><h2 id="pendientes-cert">Pendientes de certificación</h2><p>Seleccione un requerimiento para revisar sus documentos y emitir el certificado.</p></div>
          <span class="cert-count" aria-live="polite">{{ porCertificar.length }} por emitir</span>
        </div>
        <label class="cert-search">Buscar requerimiento
          <input v-model="busquedaCert" type="search" placeholder="Buscar por código, título o solicitante…">
        </label>
        <p v-if="errorCarga" class="cert-error" role="alert">{{ errorCarga }}</p>
        <p v-else-if="cargando" class="cert-empty" role="status">Cargando requerimientos…</p>
        <div v-else class="cert-table-wrap">
          <table class="cert-table">
            <thead><tr><th>Código</th><th>Requerimiento</th><th>Solicitante / área</th><th>Monto estimado</th><th>Estado</th><th>Acción</th></tr></thead>
            <tbody>
              <tr v-for="r in certFiltradas" :key="r.id">
                <td><strong>{{ r.codigo }}</strong></td><td>{{ r.titulo }}</td>
                <td>{{ r.solicitante_nombre || 'Sin registro' }}<small>{{ r.area_nombre || r.area || 'Sin área' }}</small></td>
                <td class="cert-monto">Bs. {{ Number(r.monto_estimado || 0).toLocaleString('es-BO', { minimumFractionDigits: 2 }) }}</td>
                <td><span class="cert-status">Por certificar</span></td>
                <td><button class="sia-primary" @click="abrir(r)">Elaborar certificado</button></td>
              </tr>
              <tr v-if="!certFiltradas.length"><td colspan="6" class="cert-empty">{{ busquedaCert ? 'No se encontraron requerimientos con esa búsqueda.' : 'No hay requerimientos pendientes de certificación.' }}</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <ModalSia v-if="itemActivo" :titulo="`Certificación presupuestaria · ${itemActivo.codigo}`" :ocupado="procesando" amplio @cerrar="itemActivo = null">
            <div v-if="itemActivo" class="ticket-header-card compact-header">
              <div class="t-head">
                <h2>{{ itemActivo.titulo }}</h2>
                <span class="codigo-badge">{{ itemActivo.codigo }}</span>
              </div>
              <div class="compact-meta">
                <span>👤 <b>Solicitante:</b> {{ itemActivo.solicitante_nombre || 's/d' }}</span>
                <span>📌 <b>&Aacute;rea:</b> {{ itemActivo.area_nombre || itemActivo.area || 's/d' }}</span>
                <span>💰 <b>Monto:</b> Bs. {{ itemActivo.monto_estimado || 's/d' }}</span>
              </div>
              <div class="evidence-box">
                <div class="evidence-info">
                  <strong>Documentos adjuntos</strong>
                </div>
                <div class="doc-links">
                  <a v-if="itemActivo.informe" :href="itemActivo.informe" target="_blank" rel="noopener" class="evidence-btn">Informe 👁</a>
                  <a v-if="itemActivo.poa" :href="itemActivo.poa" target="_blank" rel="noopener" class="evidence-btn">POA 👁</a>
                  <a v-if="itemActivo.pedido" :href="itemActivo.pedido" target="_blank" rel="noopener" class="evidence-btn">Proveído 👁</a>
                  <a v-if="itemActivo.proforma" :href="itemActivo.proforma" target="_blank" rel="noopener" class="evidence-btn">Proforma 👁</a>
                </div>
              </div>
            </div>

      <ol class="cert-pasos" aria-label="Pasos para emitir">
        <li><b>1</b><span>Revisar requerimiento y documentos</span></li>
        <li><b>2</b><span>Seleccionar partida y completar datos</span></li>
        <li><b>3</b><span>Verificar monto y emitir certificado</span></li>
      </ol>
                      <div class="workflow-card">
              <div class="wf-header">Emitir Certificaci&oacute;n Presupuestaria</div>
              <div class="cert-scroll-body">

                <div class="cert-form">

                  <!-- PARTIDA PRESUPUESTARIA -->
                  <fieldset>
                    <legend>PARTIDA PRESUPUESTARIA</legend>
                    <div class="campo full-width">
                      <label>Seleccione la partida presupuestaria</label>
                      <input 
                        type="text" 
                        v-model="searchPartida" 
                        placeholder="🔍 Escriba para filtrar o haga clic para ver todas..." 
                        class="text-input search-trigger"
                        @focus="showDropdown = true"
                      />
                      <div class="search-results" v-if="showDropdown">
                        <button type="button"
                          v-for="p in partidasFiltradas" 
                          :key="p.codigo" 
                          class="search-item" 
                          @click="seleccionarPartida(p)"
                        >
                          <b>{{ p.codigo }}</b> &mdash; {{ p.descripcion }}
                        </button>
                        <div v-if="partidasFiltradas.length === 0" class="search-item search-empty">
                          No se encontraron coincidencias
                        </div>
                      </div>
                      <div v-if="formCert.partida" class="partida-selected">
                        &check; <b>{{ formCert.partida.codigo }}</b> &mdash; {{ formCert.partida.descripcion }}
                        <button class="partida-change" @click="formCert.partida = null; formCert.partida_confirmada = false; searchPartida = ''; showDropdown = true">&times; Cambiar</button>
                      </div>
                    </div>
                  </fieldset>

                  <!-- SECCIÓN 1 -->
                  <fieldset>
                    <legend>DATOS DE CABECERA Y SISTEMA</legend>
                    <div class="form-grid">
                      <div class="campo">
                        <label>ID Certificaci&oacute;n</label>
                        <input type="text" v-model="formCert.id_certificacion" disabled class="text-input disabled" />
                      </div>
                      <div class="campo">
                        <label>Fecha de Emisi&oacute;n</label>
                        <input type="date" v-model="formCert.fecha_emision" disabled class="text-input disabled" />
                      </div>
                      <div class="campo">
                        <label>Gesti&oacute;n</label>
                        <input type="text" v-model="formCert.gestion" disabled class="text-input disabled" />
                      </div>
                      <div class="campo">
                        <label>Repartici&oacute;n Emisora</label>
                        <input type="text" v-model="formCert.reparticion_emisora" disabled class="text-input disabled" />
                      </div>
                      <div class="campo">
                        <label>Tipo de Cambio</label>
                        <input type="number" step="0.01" v-model="formCert.tipo_cambio" class="text-input" />
                      </div>
                      <div class="campo">
                        <label>Fuente de Financiamiento</label>
                        <select v-model="formCert.fuente_financiamiento" class="text-input">
                          <option value="1 - TGN">1 - TGN</option>
                          <option value="2 - Recursos Propios">2 - Recursos Propios</option>
                          <option value="3 - Donaciones">3 - Donaciones</option>
                        </select>
                      </div>
                    </div>
                  </fieldset>

                  <!-- SECCIÓN 2 -->
                  <fieldset>
                    <legend>DATOS DEL REQUERIMIENTO</legend>
                    <div class="form-grid">
                      <div class="campo">
                        <label>Unidad Solicitante / Interesado</label>
                        <input type="text" v-model="formCert.unidad_solicitante" disabled class="text-input disabled" />
                      </div>
                      <div class="campo">
                        <label>Doc. Referencia</label>
                        <input type="text" v-model="formCert.doc_referencia" disabled class="text-input disabled" />
                      </div>
                      <div class="campo full-width">
                        <label>Informe T&eacute;cnico / Cite</label>
                        <input type="text" v-model="formCert.informe_tecnico" disabled class="text-input disabled" />
                      </div>
                      <div class="campo full-width">
                        <label>Glosa / Descripci&oacute;n del Gasto</label>
                        <textarea v-model="formCert.glosa" class="text-input" rows="3"></textarea>
                      </div>
                    </div>
                  </fieldset>

                  <!-- SECCIÓN 3 -->
                  <fieldset>
                    <legend>IMPUTACI&Oacute;N Y ASIGNACI&Oacute;N PRESUPUESTARIA</legend>
                    <div class="form-grid">
                      <div class="campo full-width">
                        <label>Partida Presupuestaria</label>
                        <input type="text" :value="formCert.partida ? formCert.partida.codigo + ' - ' + formCert.partida.descripcion : 'Seleccione arriba...'" disabled class="text-input disabled" />
                      </div>
                      <div class="campo">
                        <label>Repartici&oacute;n Program&aacute;tica</label>
                        <input type="text" v-model="formCert.reparticion_programatica" class="text-input" />
                      </div>
                      <div class="campo">
                        <label>CATPROG (Categor&iacute;a Program&aacute;tica)</label>
                        <input type="text" v-model="formCert.catprog" class="text-input" />
                      </div>
                    </div>
                  </fieldset>

                  <!-- SECCIÓN 4 -->
                  <fieldset>
                    <legend>VALORIZACI&Oacute;N Y TOTALES</legend>
                    <div class="form-grid">
                      <div class="campo">
                        <label>Monto Certificado (Bs.)</label>
                        <input type="number" step="0.01" v-model="formCert.monto_certificado" class="text-input" />
                      </div>
                      <div class="campo full-width">
                        <label>Monto en Literal</label>
                        <input type="text" :value="montoALiteral(formCert.monto_certificado)" disabled class="text-input disabled" />
                      </div>
                    </div>
                  </fieldset>

                  <!-- BOTÓN EMITIR -->
                  <button 
                    class="btn-emitir" 
                    :disabled="procesando || !formCert.partida || !formCert.monto_certificado || formCert.monto_certificado <= 0" 
                    @click="emitirCertificacion"
                  >
                    {{ procesando ? 'Procesando...' : 'Generar y Emitir Certificación Presupuestaria' }}
                  </button>

                </div>
              </div>
            </div>
    </ModalSia>

    <!-- SUCCESS MODAL -->
    <div v-if="mostrarModalExito" class="detalle-modal-backdrop" @click.self="cerrarModalExito">
      <div class="success-modal">
        <div class="success-icon">✓</div>
        <h2>¡Generada con Éxito!</h2>
        <p>Su certificación fue generada exitosamente. El expediente continúa al siguiente responsable indicado en el trámite.</p>
        <button class="btn-success-close" @click="cerrarModalExito">Aceptar</button>
      </div>
    </div>

  </div>
</template>

<script setup>
import UsuarioHeader from '../components/UsuarioHeader.vue'
import { mostrarErrorRegla } from '../utils/errorRegla'
import ModalSia from '../components/ModalSia.vue'
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DafMenu from '../components/DafMenu.vue'
import { jsPDF } from 'jspdf'

const router = useRouter()
const usuario = ref(JSON.parse(localStorage.getItem('sigta_usuario') || '{}'))
const token = () => localStorage.getItem('sigta_token')

const avatarInicial = computed(() => {
  const n = usuario.value.first_name || usuario.value.username || 'U'
  return n.charAt(0).toUpperCase()
})

const items = ref([])
const cargando = ref(true)
const procesando = ref(false)
const itemActivo = ref(null)
const mostrarModalExito = ref(false)

function cerrarModalExito() {
  mostrarModalExito.value = false
}


/* Búsqueda local sobre los expedientes listos para certificar. */
const errorCarga = ref('')
const busquedaCert = ref('')

const certFiltradas = computed(() => {
  const texto = busquedaCert.value.trim().toLowerCase()
  if (!texto) return porCertificar.value
  return porCertificar.value.filter(r =>
    [r.codigo, r.titulo, r.solicitante_nombre].some(v => (v || '').toLowerCase().includes(texto))
  )
})

const porCertificar = computed(() => items.value.filter(r => r.estado === 'EVALUADO_PENDIENTE_CERTIFICACION' && !r.certificacion_presupuestaria && r.informe && r.poa && r.proforma && (!['SOPORTE', 'MANTENIMIENTO'].includes(r.origen_modulo) || r.pedido)))

// PARTIDAS
const searchPartida = ref('')
const showDropdown = ref(false)
const listaPartidas = [
  { "codigo": "24110", "descripcion": "Mantenimiento y Reparación de Edificios y Estructuras" },
  { "codigo": "24120", "descripcion": "Mantenimiento y Reparación de Vehículos, Maquinaria y Equipos" },
  { "codigo": "24130", "descripcion": "Mantenimiento y Reparación de Muebles y Enseres" },
  { "codigo": "24200", "descripcion": "Mantenimiento y Reparación de Vías y Obras Públicas" },
  { "codigo": "24300", "descripcion": "Servicios de Instalación, Montaje y Acondicionamiento" },
  { "codigo": "32100", "descripcion": "Papel de Escritorio y Cartulina" },
  { "codigo": "32200", "descripcion": "Productos de Artes Gráficas, Impresos y Cartón" },
  { "codigo": "34110", "descripcion": "Combustibles, Lubricantes y Derivados para Vehículos y Equipos" },
  { "codigo": "34200", "descripcion": "Productos Químicos, Farmacéuticos y Reactivos de Laboratorio" },
  { "codigo": "34300", "descripcion": "Llantas y Neumáticos" },
  { "codigo": "34400", "descripcion": "Productos de Cuero y Caucho" },
  { "codigo": "34500", "descripcion": "Productos de Minerales No Metálicos y Plásticos" },
  { "codigo": "34600", "descripcion": "Productos Metálicos (Perfiles, Soportes, Estructuras)" },
  { "codigo": "34800", "descripcion": "Herramientas Menores y Accesorios Mecánicos" },
  { "codigo": "39100", "descripcion": "Material Eléctrico, Cables, Iluminación y Electrónica" },
  { "codigo": "39200", "descripcion": "Material de Aseo, Limpieza y Utensilios de Higiene" },
  { "codigo": "39400", "descripcion": "Insumos, Repuestos y Accesorios Informáticos (RAM, Discos, Cables Red)" },
  { "codigo": "39500", "descripcion": "Útiles de Escritorio, Oficina y Material Didáctico" },
  { "codigo": "39700", "descripcion": "Utensilios de Cocina, Comedor y Laboratorio" },
  { "codigo": "39800", "descripcion": "Otros Repuestos y Accesorios General" },
  { "codigo": "43110", "descripcion": "Equipo de Oficina y Muebles" },
  { "codigo": "43120", "descripcion": "Equipos Computacionales, Servidores y Periféricos" },
  { "codigo": "43200", "descripcion": "Maquinaria y Equipos para Laboratorios y Talleres" },
  { "codigo": "43700", "descripcion": "Otra Maquinaria, Equipos e Instrumentos Especializados" }
]

const partidasFiltradas = computed(() => {
  const t = searchPartida.value.toLowerCase()
  return listaPartidas.filter(p => p.codigo.includes(t) || p.descripcion.toLowerCase().includes(t))
})

const formCert = reactive({
  partida: null,
  partida_confirmada: false,

  id_certificacion: '',
  fecha_emision: '',
  gestion: '2026',
  reparticion_emisora: 'DIRECCION ADMIN. FINANCIERO',
  tipo_cambio: 6.96,
  fuente_financiamiento: '2 - Recursos Propios',

  unidad_solicitante: '',
  doc_referencia: '',
  informe_tecnico: '',
  glosa: '',

  reparticion_programatica: '30020000',
  catprog: '00000001',

  monto_certificado: 0
})

function seleccionarPartida(p) {
  formCert.partida = p
  formCert.partida_confirmada = true
  searchPartida.value = ''
  showDropdown.value = false
}

function montoALiteral(monto) {
  if (!monto || isNaN(monto)) return 'CERO 00/100 BOLIVIANOS'
  
  const unidades = ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
  const decenas = ['', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
  const especiales = {11: 'ONCE', 12: 'DOCE', 13: 'TRECE', 14: 'CATORCE', 15: 'QUINCE', 16: 'DIECISEIS', 17: 'DIECISIETE', 18: 'DIECIOCHO', 19: 'DIECINUEVE'}
  
  function aTexto(num) {
    if (num === 0) return 'CERO'
    if (num < 10) return unidades[num]
    if (num < 20) return especiales[num] || 'DIEZ Y ' + unidades[num % 10]
    if (num === 10) return 'DIEZ'
    if (num === 20) return 'VEINTE'
    if (num < 30) return 'VEINTI' + unidades[num % 10]
    if (num < 100) return decenas[Math.floor(num/10)] + (num%10 === 0 ? '' : ' Y ' + unidades[num%10])
    if (num === 100) return 'CIEN'
    if (num < 200) return 'CIENTO ' + aTexto(num%100)
    if (num < 1000) {
      const centenas = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']
      return centenas[Math.floor(num/100)] + (num%100 === 0 ? '' : ' ' + aTexto(num%100))
    }
    if (num === 1000) return 'MIL'
    if (num < 2000) return 'MIL ' + aTexto(num%1000)
    if (num < 1000000) return aTexto(Math.floor(num/1000)) + ' MIL' + (num%1000 === 0 ? '' : ' ' + aTexto(num%1000))
    return num.toString()
  }
  
  const partes = parseFloat(monto).toFixed(2).split('.')
  const enteros = parseInt(partes[0], 10)
  const centavos = partes[1] || '00'
  
  let textoEnteros = aTexto(enteros).replace(/ UNO$/, ' UN').replace(/^UNO MIL/, 'UN MIL')
  return `${textoEnteros} ${centavos}/100 BOLIVIANOS`
}

async function cargar() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const r = await fetch('/api/compras/solicitudes/?bandeja=certificacion', {
      headers: { Authorization: `Token ${token()}` }
    })
    const d = await r.json()
    if (!r.ok) throw new Error('Error al cargar')
    items.value = Array.isArray(d) ? d : d.results || []
    if (itemActivo.value && !porCertificar.value.some(r=>r.id===itemActivo.value.id)) itemActivo.value = null
  } catch (e) {
    errorCarga.value = 'No se pudieron cargar los requerimientos. Pulse Actualizar para reintentar.'
  } finally {
    cargando.value = false
  }
}

function abrir(item) {
  itemActivo.value = item
  showDropdown.value = false
  formCert.partida = null
  formCert.partida_confirmada = false
  searchPartida.value = ''
  
  formCert.id_certificacion = `C-${Math.floor(Math.random()*100000000).toString().padStart(8, '0')}`
  formCert.fecha_emision = new Date().toISOString().split('T')[0]
  formCert.gestion = '2026'
  formCert.reparticion_emisora = 'DIRECCION ADMIN. FINANCIERO'
  formCert.tipo_cambio = 6.96
  formCert.fuente_financiamiento = '2 - Recursos Propios'
  
  formCert.unidad_solicitante = item.area_nombre || item.area || item.solicitante_nombre || ''
  formCert.doc_referencia = item.codigo
  formCert.informe_tecnico = `INF-TEC-${item.codigo}`
  formCert.glosa = item.descripcion || ''
  
  formCert.reparticion_programatica = '30020000'
  formCert.catprog = '00000001'
  
  formCert.monto_certificado = item.monto_estimado || 0
}

function getBase64Image(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      resolve(canvas.toDataURL('image/jpeg'));
    };
    img.onerror = (e) => reject(e);
    img.src = url;
  });
}

async function emitirCertificacion() {
  if (!formCert.partida || !formCert.monto_certificado) return
  
  procesando.value = true
  try {
    const doc = new jsPDF()
    
    // Attempt to add Logo
    try {
      const logoB64 = await getBase64Image('/img/emi.jpg')
      doc.addImage(logoB64, 'JPEG', 15, 15, 22, 22)
    } catch (e) {
      console.warn('Logo no cargado', e)
    }

    // Header Text
    doc.setFont("helvetica", "bold")
    doc.setFontSize(12)
    doc.text("ESCUELA MILITAR DE INGENIERÍA", 105, 20, { align: 'center' })
    doc.setFontSize(9)
    doc.text("MCAL. ANTONIO JOSÉ DE SUCRE", 105, 25, { align: 'center' })
    doc.setFont("helvetica", "normal")
    doc.text("BOLIVIA", 105, 30, { align: 'center' })
    
    // Title
    doc.setFontSize(16)
    doc.setFont("helvetica", "bold")
    doc.text("CERTIFICACIÓN PRESUPUESTARIA", 105, 45, { align: 'center' })
    doc.setFontSize(11)
    doc.setFont("helvetica", "normal")
    doc.text("Dirección Administrativa Financiera", 105, 52, { align: 'center' })
    
    // Main Box Background and Border
    doc.setDrawColor(0)
    doc.setLineWidth(0.3)
    doc.rect(15, 60, 180, 190) // Outer border
    
    // Row 1: Nro Certificación & Fecha
    doc.setFillColor(240, 240, 240)
    doc.rect(15, 60, 180, 10, 'F')
    doc.line(15, 70, 195, 70) // Separator
    
    doc.setFontSize(10)
    doc.setFont("helvetica", "bold")
    doc.text("Nro. Certificación:", 20, 67)
    doc.setFont("helvetica", "normal")
    doc.text(String(formCert.id_certificacion || ''), 55, 67)
    
    doc.setFont("helvetica", "bold")
    doc.text("Fecha de Emisión:", 135, 67)
    doc.setFont("helvetica", "normal")
    doc.text(String(formCert.fecha_emision || ''), 168, 67)
    
    // Row 2: Gestión & Fuente
    let y = 80
    doc.setFont("helvetica", "bold"); doc.text("Gestión:", 20, y); 
    doc.setFont("helvetica", "normal"); doc.text(String(formCert.gestion || ''), 55, y);
    
    doc.setFont("helvetica", "bold"); doc.text("Fuente de Fin.:", 110, y); 
    doc.setFont("helvetica", "normal"); doc.text(String(formCert.fuente_financiamiento || ''), 140, y);
    y += 10
    
    // Row 3: Unidad Solicitante
    doc.setFont("helvetica", "bold"); doc.text("Unidad Solicitante:", 20, y); 
    doc.setFont("helvetica", "normal"); doc.text(String(formCert.unidad_solicitante || ''), 55, y);
    y += 10
    
    // Row 4: Doc Ref
    doc.setFont("helvetica", "bold"); doc.text("Doc. Referencia:", 20, y); 
    doc.setFont("helvetica", "normal"); doc.text(String(formCert.doc_referencia || ''), 55, y);
    doc.setFont("helvetica", "bold"); doc.text("Inf. Técnico:", 110, y); 
    doc.setFont("helvetica", "normal"); doc.text(String(formCert.informe_tecnico || ''), 135, y);
    y += 15
    
    // Line separator
    doc.line(15, y-5, 195, y-5)
    
    // Imputación Presupuestaria Title
    doc.setFont("helvetica", "bold");
    doc.text("IMPUTACIÓN PRESUPUESTARIA", 105, y, { align: 'center' })
    y += 10
    
    // Headers for Imputación
    doc.setFillColor(240, 240, 240)
    doc.rect(15, y-5, 180, 8, 'F')
    doc.line(15, y-5, 195, y-5)
    doc.line(15, y+3, 195, y+3)
    
    doc.setFontSize(9)
    doc.text("PARTIDA", 20, y)
    doc.text("DESCRIPCIÓN", 45, y)
    doc.text("PROG.", 145, y)
    doc.text("CAT. PROG.", 170, y)
    y += 10
    
    // Values for Imputación
    doc.setFont("helvetica", "normal")
    doc.text(String(formCert.partida.codigo || ''), 20, y)
    doc.text(String(formCert.partida.descripcion || ''), 45, y, { maxWidth: 95 })
    doc.text(String(formCert.reparticion_programatica || ''), 145, y)
    doc.text(String(formCert.catprog || ''), 170, y)
    y += 20
    
    // Line separator
    doc.line(15, y-5, 195, y-5)
    
    // Glosa Title
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10)
    doc.text("GLOSA / DESCRIPCIÓN DEL GASTO:", 20, y)
    y += 7
    doc.setFont("helvetica", "normal");
    const splitGlosa = doc.splitTextToSize(String(formCert.glosa || 'Sin descripción'), 170)
    doc.text(splitGlosa, 20, y)
    
    // Valorization section at bottom of box
    doc.setFillColor(245, 245, 245)
    doc.rect(15, 220, 180, 30, 'F')
    doc.line(15, 220, 195, 220)
    
    doc.setFontSize(12)
    doc.setFont("helvetica", "bold")
    doc.text("MONTO TOTAL CERTIFICADO:", 20, 230)
    doc.setFontSize(14)
    doc.text(String(`Bs. ${parseFloat(formCert.monto_certificado).toFixed(2)}`), 130, 230)
    
    doc.setFontSize(10)
    doc.setFont("helvetica", "normal")
    doc.text("Son:", 20, 242)
    doc.text(String(montoALiteral(formCert.monto_certificado) || ''), 30, 242, { maxWidth: 160 })
    
    // Signatures
    doc.setFont("helvetica", "bold")
    doc.setFontSize(10)
    doc.line(40, 275, 85, 275)
    doc.text("Elaborado por", 62.5, 280, { align: 'center' })
    
    doc.line(125, 275, 170, 275)
    doc.text("Aprobado por", 147.5, 280, { align: 'center' })
    
    const pdfBlob = doc.output('blob')
    const fd = new FormData()
    fd.append('certificacion_presupuestaria', pdfBlob, `${formCert.id_certificacion}.pdf`)

    const r = await fetch(`/api/compras/solicitudes/${itemActivo.value.id}/certificar-daf/`, {
      method: 'POST',
      headers: { Authorization: `Token ${token()}` },
      body: fd
    })
    
    const d = await r.json().catch(()=>({}))
    // REQUERIMIENTO 9 (R09): saldo insuficiente conserva el formulario.
    if (!r.ok) {
      if (await mostrarErrorRegla(d)) return
      throw new Error(d.detalle || Object.values(d)[0] || 'Error al emitir.')
    }

    mostrarModalExito.value = true
    itemActivo.value = null
    window.dispatchEvent(new Event('sia-certificaciones-actualizadas'))
    await cargar()
  } catch (e) {
    alert(e.message)
  } finally {
    procesando.value = false
  }
}

onMounted(() => {
  if (!token()) router.push('/login')
  else cargar()
})
</script>

<style scoped>
/* ====== GESTIÓN DE TICKETS LAYOUT (from reference) ====== */
.barra-perfil { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 14px; }
.gestion-tickets-layout { display: flex; gap: 20px; height: calc(100vh - 232px); min-height: 460px; overflow: hidden; align-items: stretch; }
.gestion-left { width: 35%; display: flex; flex-direction: column; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; overflow: hidden; }
.gestion-left-header { padding: 15px 20px; border-bottom: 1px solid var(--sigta-borde-suave); display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.gestion-left-header h3 { margin: 0; font-size: 14px; color: var(--sigta-texto); }
.badge { background: #e0e7ff; color: var(--sigta-azul); font-size: 11px; padding: 4px 8px; border-radius: 20px; font-weight: bold; }
.gestion-lista { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
.ticket-item { padding: 14px; border: 1px solid var(--sigta-borde-suave); border-radius: 8px; cursor: pointer; transition: all 0.2s; background: var(--sigta-blanco); }
.ticket-item:hover { border-color: var(--sigta-borde); box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
.ticket-item.activo { border-color: var(--sigta-azul); background: #f8fafc; }
.ticket-item.t-validar { border-left: 4px solid var(--sigta-error); }
.ticket-item h4 { margin: 8px 0 4px; font-size: 14px; color: var(--sigta-texto); }
.ticket-item p { margin: 0; font-size: 11px; color: var(--sigta-texto-suave); }
.e-validar { background: #fee2e2; color: #b91c1c; }
.empty-list { text-align: center; padding: 30px; font-size: 12px; color: var(--sigta-texto-suave); }

.gestion-right { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.gestion-detalle-wrapper { display: flex; flex-direction: column; gap: 15px; height: 100%; overflow-y: auto; padding-right: 8px; }
.gestion-detalle-wrapper::-webkit-scrollbar { width: 6px; }
.gestion-detalle-wrapper::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

.ticket-header-card { background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; padding: 24px; flex-shrink: 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.t-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.t-head h2 { margin: 0; font-size: 20px; color: var(--sigta-azul); font-weight: 800; }
.codigo-badge { font-weight: bold; color: var(--sigta-texto-suave); font-size: 13px; background: #f1f5f9; padding: 4px 10px; border-radius: 6px; }
.t-meta { display: flex; gap: 16px; margin: 0 0 20px; font-size: 13px; color: var(--sigta-texto-suave); }
.t-meta span { display: flex; align-items: center; gap: 5px; }
.t-meta b { color: var(--sigta-texto); }

.t-content { display: flex; flex-direction: column; gap: 12px; }
.desc-box { background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid var(--sigta-borde-suave); }
.desc-box strong { display: block; font-size: 11px; color: var(--sigta-texto-suave); text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px; font-weight: bold; }
.desc-box p { margin: 0; font-size: 14px; line-height: 1.5; color: var(--sigta-texto); }

.evidence-box { display: flex; justify-content: space-between; align-items: center; background: #e0e7ff; border: 1px solid #c7d2fe; padding: 12px 16px; border-radius: 8px; }
.evidence-info strong { display: block; font-size: 13px; color: var(--sigta-azul); font-weight: bold; margin-bottom: 2px; }
.evidence-info span { font-size: 11px; color: #4338ca; }
.doc-links { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
.evidence-btn { background: var(--sigta-azul); color: var(--sigta-blanco); text-decoration: none; font-size: 12px; font-weight: bold; padding: 8px 16px; border-radius: 6px; transition: opacity 0.2s; white-space: nowrap; display: inline-flex; align-items: center; gap: 5px; }
.evidence-btn:hover { opacity: 0.9; }

.workflow-card { flex: 1; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; }
.wf-header { padding: 15px 20px; border-bottom: 1px solid var(--sigta-borde-suave); font-weight: bold; color: var(--sigta-texto); background: #f8fafc; }
.wf-body { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; position: relative; }
.wf-body::before { content: ''; position: absolute; left: 45px; top: 35px; bottom: 35px; width: 2px; background: var(--sigta-borde-suave); z-index: 1; }

.wf-step { display: flex; margin-bottom: 30px; position: relative; z-index: 2; }
.wf-step:last-child { margin-bottom: 0; }
.step-num { width: 42px; height: 42px; border-radius: 50%; background: var(--sigta-borde); color: var(--sigta-texto-suave); display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; border: 4px solid var(--sigta-blanco); transition: all 0.3s; }
.step-content { margin-left: 20px; flex: 1; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 10px; padding: 15px 20px; transition: all 0.3s; }
.step-content h4 { margin: 0 0 5px; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }
.step-content p { margin: 0 0 15px; font-size: 12px; color: var(--sigta-texto-suave); }
.step-badge { font-size: 10px; text-transform: uppercase; background: #f0fdf4; color: #166534; padding: 3px 8px; border-radius: 10px; }

.wf-step.active .step-num { background: var(--sigta-azul); color: var(--sigta-blanco); box-shadow: 0 0 0 4px rgba(0, 42, 92, 0.1); }
.wf-step.active .step-content { border-color: var(--sigta-azul); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.wf-step.locked { opacity: 0.5; pointer-events: none; }
.wf-step.locked .step-content { background: #f8fafc; }
.wf-step.completed .step-num { background: var(--sigta-azul-medio); color: var(--sigta-blanco); }
.wf-step.completed .step-content { border-color: var(--sigta-borde-suave); background: #f8fafc; }

.step-actions { display: flex; gap: 10px; }
.flex-btn { flex: 1; text-align: center; justify-content: center; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; border: none; }
.reject { background: var(--sigta-blanco); border: 1px solid var(--sigta-error); color: var(--sigta-error); padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; }
.primary { background: var(--sigta-azul) !important; color: var(--sigta-blanco) !important; border-color: var(--sigta-azul) !important; }
.empty { text-align: center; background: var(--sigta-blanco); border: 1px dashed var(--sigta-borde); padding: 65px; border-radius: 10px; color: var(--sigta-texto-suave); }
.empty > span { font-size: 31px; color: var(--sigta-exito); }
.top { display: flex; justify-content: space-between; gap: 8px; }
.top span { font-size: 12px; font-weight: 800; color: var(--sigta-azul); }
.top em { font-size: 10px; background: var(--sigta-azul-tenue); padding: 4px 8px; border-radius: 10px; font-style: normal; }

/* ====== BUSCADOR DE PARTIDAS ====== */
.search-results { width: 100%; border: 1px solid var(--sigta-borde); border-radius: 6px; margin-top: 4px; max-height: 200px; overflow-y: auto; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.search-item { padding: 10px 14px; font-size: 13px; cursor: pointer; border-bottom: 1px solid var(--sigta-borde-suave); }
.search-item:last-child { border-bottom: none; }
.search-item:hover { background: #f8fafc; color: var(--sigta-azul); }
.search-item.empty { color: var(--sigta-texto-suave); text-align: center; cursor: default; }
.search-item.empty:hover { background: #fff; color: var(--sigta-texto-suave); }

/* ====== FORMULARIO CERTIFICACIÓN ====== */
.cert-form fieldset { border: 1px solid var(--sigta-borde-suave); border-radius: 8px; padding: 15px 20px; margin-bottom: 20px; background: #fcfcfc; }
.cert-form legend { font-size: 11px; font-weight: 900; color: var(--sigta-azul); padding: 0 8px; letter-spacing: 0.5px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.form-grid .full-width { grid-column: 1 / -1; }
.cert-form .campo { margin: 0; }
.cert-form label { display: block; font-size: 11px; color: var(--sigta-texto-suave); margin-bottom: 4px; }
.text-input { width: 100%; padding: 9px 11px; border: 1px solid var(--sigta-borde); border-radius: 7px; font-family: inherit; font-size: 13px; color: var(--sigta-texto); }
.text-input.disabled { background: #f1f5f9; color: #64748b; cursor: not-allowed; }

/* ====== CABECERA COMPACTA ====== */
.compact-header { padding: 16px 20px !important; }
.compact-header .t-head { margin-bottom: 8px; }
.compact-header .t-head h2 { font-size: 16px; }
.compact-meta { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--sigta-texto-suave); margin-bottom: 12px; }
.compact-meta span { display: flex; align-items: center; gap: 4px; }
.compact-meta b { color: var(--sigta-texto); }

/* ====== SCROLL BODY CERTIFICACIÓN ====== */
.cert-scroll-body { flex: 1; overflow-y: auto; padding: 20px; }
.cert-scroll-body::-webkit-scrollbar { width: 6px; }
.cert-scroll-body::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

/* ====== PARTIDA SELECCIONADA ====== */
.partida-selected { display: flex; align-items: center; gap: 10px; margin-top: 8px; padding: 10px 14px; background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; font-size: 13px; color: #166534; }
.partida-change { margin-left: auto; background: none; border: 1px solid #dc2626; color: #dc2626; padding: 4px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: bold; }
.partida-change:hover { background: #fef2f2; }

/* ====== SEARCH TRIGGER ====== */
.search-trigger { cursor: pointer; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath fill='%2394a3b8' d='M6 8l4 4 4-4'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; background-size: 16px; }
.search-empty { color: var(--sigta-texto-suave); text-align: center; cursor: default; }
.search-empty:hover { background: #fff; color: var(--sigta-texto-suave); }

/* ====== BOTÓN EMITIR ====== */
.btn-emitir { width: 100%; padding: 14px; font-size: 15px; font-weight: bold; border: none; border-radius: 8px; background: #15803d; color: #fff; cursor: pointer; transition: background 0.2s; margin-top: 10px; }
.btn-emitir:hover { background: #166534; }
.btn-emitir:disabled { opacity: 0.5; cursor: not-allowed; }

@media(max-width:1050px) { .gestion-tickets-layout { flex-direction: column; height: auto; } .gestion-left { width: 100%; height: 300px; } }
@media(max-width:760px) { .form-grid { grid-template-columns: 1fr; } }
/* ====== MODAL DE ÉXITO ====== */
.detalle-modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(3px);
}
.success-modal {
  background: white;
  padding: 35px 40px;
  border-radius: 16px;
  text-align: center;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  animation: scaleIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes scaleIn {
  0% { transform: scale(0.8); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.success-icon {
  width: 80px;
  height: 80px;
  background: var(--sigta-exito-fondo, #dcfce7);
  color: var(--sigta-exito, #16a34a);
  font-size: 45px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}
.success-modal h2 {
  margin: 0 0 12px;
  color: var(--sigta-azul, #0f172a);
  font-size: 22px;
  font-weight: 800;
}
.success-modal p {
  color: var(--sigta-texto-suave, #64748b);
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 25px;
}
.btn-success-close {
  background: var(--sigta-exito, #16a34a);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 30px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}
.btn-success-close:hover {
  background: #15803d;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(22, 163, 74, 0.3);
}

.cert-bandeja { background:white; border:1px solid var(--sigta-borde); border-radius:14px; padding:24px; margin-top:24px; }
.cert-bandeja-head { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:22px; }
.cert-bandeja-head h2 { font-size:18px; margin:0 0 6px; color:var(--sigta-azul); }
.cert-bandeja-head p { margin:0; font-size:13px; color:var(--sigta-texto-suave); }
.cert-count,.cert-status { display:inline-block; white-space:nowrap; background:#fff6d8; color:#795a00; border-radius:20px; padding:8px 12px; font-size:12px; font-weight:700; }
.cert-search { display:block; font-size:13px; font-weight:700; color:var(--sigta-azul); margin-bottom:24px; }
.cert-search input { display:block; width:100%; box-sizing:border-box; margin-top:8px; padding:16px; font:inherit; font-weight:400; border:1px solid var(--sigta-borde); border-radius:9px; background:#f8fafd; }
.cert-search input:focus { outline:2px solid var(--sigta-azul); outline-offset:2px; }
.cert-table-wrap { overflow:auto; }.cert-table { width:100%; border-collapse:collapse; font-size:13px; text-align:left; }
.cert-table th { background:#f3f6fb; color:var(--sigta-texto-suave); padding:14px; font-size:11px; text-transform:uppercase; letter-spacing:.4px; }
.cert-table td { padding:18px 14px; border-bottom:1px solid #e8eef5; }.cert-table tbody tr:hover { background:#fafcff; }.cert-table small { display:block; margin-top:5px; color:var(--sigta-texto-suave); }
.cert-table strong { color:var(--sigta-azul); white-space:nowrap; }.cert-table button { white-space:nowrap; font-size:12px; }.cert-monto { white-space:nowrap; }.cert-empty { padding:32px!important; text-align:center; color:var(--sigta-texto-suave); }.cert-error { color:#a22b24; }
.cert-pasos { display:flex; gap:12px; list-style:none; padding:0; margin:20px 0; }.cert-pasos li { flex:1; display:flex; align-items:center; gap:10px; padding:12px; border:1px solid #dae4ef; border-radius:8px; background:#f5f8fc; font-size:12px; }.cert-pasos b { display:grid; place-items:center; width:26px; height:26px; flex-shrink:0; border-radius:50%; background:var(--sigta-azul); color:white; }
.workflow-card { flex:none; }.cert-scroll-body { overflow:visible; flex:none; }.compact-header { border:1px solid var(--sigta-borde); border-radius:10px; }.compact-meta { flex-wrap:wrap; }.doc-links { flex-wrap:wrap; }
.workflow-card .wf-header { background:var(--sigta-azul); color:white; }
button.search-item { display:block; width:100%; border:0; background:white; text-align:left; font:inherit; cursor:pointer; }
button.search-item:hover,button.search-item:focus-visible { background:var(--sigta-azul-tenue); }
@media(max-width:760px) { .cert-bandeja { padding:16px; }.cert-bandeja-head { align-items:flex-start; }.cert-pasos { flex-direction:column; }.cert-scroll-body { padding:14px; }.evidence-box { flex-direction:column; align-items:flex-start; }.barra-perfil { flex-wrap:wrap; } }
</style>
