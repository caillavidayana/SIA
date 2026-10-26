<template>
  <div class="layout">

    <DafMenu />

    <TarjetaGuardado
      :visible="mostrarGuardadoOk"
      :texto="textoGuardado"
      :tipo="tipoGuardado"
      @cerrar="ocultarGuardado"
    />

    <main class="main">

      <!-- =================================================
           ENCABEZADO
      ================================================== -->
      <header class="page-header">

        <div>
          <h1>
            Solicitudes
          </h1>

          <p>
            Expedientes de compra pendientes de evaluación
            presupuestaria y certificación.
          </p>
        </div>

        <div class="header-actions">

          <select
            v-if="seccion === 'historial'"
            v-model="filtroEstado"
            class="filtro-estado"
          >
            <option value="">Todas las solicitudes</option>
            <option value="APROBADA">Solicitudes aprobadas</option>
            <option value="RECHAZADA">Solicitudes rechazadas</option>
          </select>



        </div>

      
        <UsuarioHeader @actualizar="cargarCompras" />
      </header>
      <CajaChicaPanel resumen />

      <!-- =================================================
           RESUMEN
           Solo cuenta las compras ya cargadas, por su estado
           existente. No consulta nada ni cambia el flujo.
      ================================================== -->
      <section
        v-if="seccion === 'dashboard' && !cargando && compras.length"
        class="daf-resumen"
      >
        <button type="button" class="daf-kpi k-espera" @click="irASolicitudes">
          <span>Pendientes de evaluación</span>
          <strong>{{ totalPendientes }}</strong>
        </button>

        <button type="button" class="daf-kpi k-certificar" @click="irACertificar">
          <span>Pendientes de certificación</span>
          <strong>{{ totalPorCertificar }}</strong>
        </button>

        <button type="button" class="daf-kpi k-aprobada" @click="irAHistorial('APROBADA')">
          <span>Aprobadas</span>
          <strong>{{ totalAprobadas }}</strong>
        </button>

        <button type="button" class="daf-kpi k-rechazada" @click="irAHistorial('RECHAZADA')">
          <span>Rechazadas</span>
          <strong>{{ totalRechazadas }}</strong>
        </button>
      </section>



      <template v-if="seccion !== 'dashboard'">
      <!-- =================================================
           CARGANDO
      ================================================== -->
      <div
        v-if="cargando"
        class="loading"
      >
        Cargando solicitudes de compra...
      </div>


      <!-- =================================================
           SIN REGISTROS
      ================================================== -->
      <div
        v-else-if="compras.length === 0"
        class="empty"
      >
        No existen solicitudes de compra registradas.
      </div>


      <div
        v-else-if="listaVisible.length === 0"
        class="empty"
      >
        No hay {{ etiquetaFiltroVacio(filtroEstado) }}.
      </div>


      <!-- =================================================
           LISTADO
      ================================================== -->
      <section
        v-else
        class="requests-card"
      >

        <div class="request-list">

          <article
            v-for="compra in listaVisible"
            :key="compra.id"
            class="request"
          >

            <div class="request-main">

              <div class="request-code">
                <strong>
                  {{ compra.codigo }}
                </strong>

                <small>
                  {{ compra.area_nombre || 'Área no indicada' }}
                </small>
              </div>


              <div class="request-info">

                <h3>
                  {{
                    compra.titulo
                    || compra.descripcion
                    || 'Solicitud de compra'
                  }}
                </h3>

                <div class="meta">

                  <span>
                    {{
                      compra.solicitante_nombre
                      || compra.solicitante_email
                      || 'Sin información'
                    }}
                  </span>

                  <span>
                    {{
                      compra.via_nombre
                      || 'Vía no indicada'
                    }}
                  </span>

                  <span v-if="compra.creado_en">
                    {{ formatearFecha(compra.creado_en) }}
                  </span>

                </div>

              </div>

            </div>


            <div class="request-side">

              <span
                :class="['status', claseBucket(bucketEstado(compra.estado))]"
              >
                {{ etiquetaBucket(bucketEstado(compra.estado)) }}
              </span>

              <div class="row-actions">

                <button
                  :class="puedeAprobar(compra) ? 'view btn-evaluar' : 'view'"
                  @click="verDetalle(compra)"
                >
                  {{ puedeAprobar(compra) ? 'Evaluar' : 'Ver detalle' }}
                </button>

              </div>

            </div>

          </article>

        </div>

      </section>
      </template>

    </main>


    <!-- =================================================
         DOCUMENTO DE DETALLE
    ================================================== -->

    <div
      v-if="mostrarDetalle"
      class="detalle-modal-backdrop"
      @click.self="cerrarDetalle"
    >
      <div class="detalle-modal documento-modal" @scroll="onModalScroll">

        <div class="detalle-modal-header">
          <div class="documento-header-titulo">

            <IconoSigta class="documento-header-icono" nombre="auditoria" :tamano="22" />

            <div>
              <h3>{{ compraSeleccionada?.codigo }}</h3>
              <small>{{ compraSeleccionada?.titulo }}</small>
            </div>

          </div>

          <button
            class="detalle-modal-close"
            @click="cerrarDetalle"
          >✕</button>
        </div>

        <div class="documento-body" @scroll="onModalScroll">
      <ResumenExpediente v-if="compraSeleccionada" :registro="compraSeleccionada" requerimiento />
      <CotizacionesCompra v-if="compraSeleccionada" :id="compraSeleccionada.id" :editable="false" />

          <div
            :class="['estado-banner', claseBucket(bucketEstado(compraSeleccionada?.estado))]"
          >
            <span class="estado-banner-icono">
              {{ iconoBucket(bucketEstado(compraSeleccionada?.estado)) }}
            </span>

            <div>
              <strong>{{ etiquetaBucket(bucketEstado(compraSeleccionada?.estado)) }}</strong>
              <span class="estado-banner-descripcion">
                {{ descripcionBucket(bucketEstado(compraSeleccionada?.estado)) }}
              </span>
            </div>
          </div>


          <div class="documento-columnas">

          <div class="documento-col">

          <div class="documento-seccion">

            <div class="documento-titulo-fila">
              <IconoSigta class="documento-icono" nombre="almacen" :tamano="22" />
              <span class="documento-titulo">
                Producto o servicio a comprar
              </span>
            </div>

            <h4>{{ compraSeleccionada?.titulo || 'Sin título' }}</h4>

            <p>{{ compraSeleccionada?.descripcion || 'Sin descripción registrada.' }}</p>


            <div class="documento-fila documento-fila-3">

              <div>
                <b>Tipo</b>
                <span>{{ compraSeleccionada?.tipo_nombre || compraSeleccionada?.tipo || 'No indicado' }}</span>
              </div>

              <div>
                <b>Cantidad</b>
                <span>{{ compraSeleccionada?.cantidad || 1 }}</span>
              </div>

              <div>
                <b>Monto estimado</b>
                <span>
                  {{
                    compraSeleccionada?.monto_estimado
                      ? `Bs ${Number(compraSeleccionada.monto_estimado).toFixed(2)}`
                      : 'No indicado'
                  }}
                </span>
              </div>

            </div>

            <div class="documento-fila documento-fila-1">

              <div>
                <b>Especificaciones</b>
                <span>{{ compraSeleccionada?.especificaciones || 'No registradas.' }}</span>
              </div>

              <div>
                <b>Justificación</b>
                <span>{{ compraSeleccionada?.justificacion || 'No registrada.' }}</span>
              </div>

            </div>

          </div>

          </div>


          <div class="documento-col">

          <div class="documento-seccion">

            <div class="documento-titulo-fila">
              <IconoSigta class="documento-icono" nombre="solicitudes" :tamano="22" />
              <span class="documento-titulo">
                Datos del expediente
              </span>
            </div>

            <div class="documento-fila documento-fila-2">

              <div>
                <b>Solicitante</b>
                <button
                  v-if="compraSeleccionada?.solicitante"
                  type="button"
                  class="solicitante-link"
                  @click="abrirSolicitante(compraSeleccionada.solicitante)"
                >
                  <span>
                    {{
                      compraSeleccionada?.solicitante_nombre
                      || 'Sin información'
                    }}
                  </span>
                  <small v-if="compraSeleccionada?.solicitante_email">
                    {{ compraSeleccionada.solicitante_email }}
                  </small>
                </button>
                <span v-else>Sin información</span>
              </div>

              <div>
                <b>Área</b>
                <span>{{ compraSeleccionada?.area_nombre || 'No indicada' }}</span>
              </div>

              <div>
                <!-- REQUERIMIENTO 8: continuidad de expedientes certificados anteriores. -->
                <button v-if="compraSeleccionada?.estado==='VERIFICADO_PENDIENTE_AUTORIZACION' && compraSeleccionada?.responsable_actual==='DAF'" class="sia-primary" :disabled="procesando" @click="ejecutarAccion('certificar-daf', {}, 'aprobar', false, 'Expediente derivado a Tesorería sin Director.')">Derivar a Tesorería</button>
                <b>Vía de adquisición</b>
                <select v-if="compraSeleccionada?.estado==='CREADO_PENDIENTE_DAF'" v-model="viaEvaluacion" aria-label="Vía de adquisición"><option value="CAJA_CHICA">Caja chica</option><option value="FINANZAS">Finanzas</option></select><span v-else>{{ compraSeleccionada?.via_nombre || 'No indicada' }}</span>
              </div>

              <div>
                <b>Fecha de registro</b>
                <span>{{ formatearFecha(compraSeleccionada?.creado_en) }}</span>
              </div>

            </div>

          </div>


          <div class="documento-seccion">

            <div class="documento-titulo-fila">
              <IconoSigta class="documento-icono" nombre="auditoria" :tamano="22" />
              <span class="documento-titulo">
                Documentos del expediente
              </span>
            </div>

            <CotizacionesExpediente :filas="compraSeleccionada?.cotizaciones" />
            <div class="documento-lista">

              <template
                v-for="doc in documentosExpediente"
                :key="doc.label"
              >

                <a
                  v-if="doc.url"
                  :href="doc.url"
                  target="_blank"
                  class="documento-item ok"
                >
                  <IconoSigta class="documento-item-icono" nombre="auditoria" :tamano="22" />
                  <span class="documento-item-label">{{ doc.label }}</span>
                  <span class="documento-item-accion">
                    Ver archivo
                    <span class="documento-item-ojo">👁</span>
                  </span>
                </a>

                <div
                  v-else
                  class="documento-item falta"
                >
                  <IconoSigta class="documento-item-icono" nombre="auditoria" :tamano="22" />
                  <span class="documento-item-label">{{ doc.label }}</span>
                  <small>{{ doc.pendienteTexto || 'No adjuntado' }}</small>
                </div>

              </template>

            </div>

          </div>

          </div>

          </div>


          <div
            class="documento-seccion motivo-rechazo"
            v-if="compraSeleccionada?.motivo_rechazo"
          >
            <span class="documento-titulo">
              Motivo de rechazo
            </span>

            <p>{{ compraSeleccionada.motivo_rechazo }}</p>
          </div>


          <!-- ACCIONES -->

          <div
            v-if="bucketEstado(compraSeleccionada?.estado) === 'EN_ESPERA'"
            class="documento-acciones"
          >

            <p
              v-if="errorAccion"
              class="accion-error"
            >
              {{ errorAccion }}
            </p>

            <div
              v-if="!mostrarFormRechazo && !mostrarFormCertificacion"
            >
              <div v-if="haLeidoTodo" class="acciones-botones eval-mode">
                <button
                  class="btn-aprobar btn-eval-main"
                  :disabled="procesando || documentosExpediente.some(doc => !doc.url)"
                  @click="iniciarAprobacion"
                >
                  APROBAR
                </button>

                <button
                  class="btn-rechazar btn-eval-main"
                  :disabled="procesando"
                  @click="abrirFormRechazo"
                >
                  RECHAZAR
                </button>
              </div>
              <div v-else class="scroll-lock-msg">
                <span>↓</span> Desliza hasta el final para habilitar la evaluación <span>↓</span>
              </div>
            </div>

            <div
              v-else-if="mostrarFormRechazo"
              class="form-rechazo"
            >
              <label>
                Motivo del rechazo
                <span>*</span>
              </label>

              <textarea
                v-model="motivoRechazoTexto"
                rows="3"
                placeholder="Explique por qué el expediente no califica..."
              ></textarea>

              <div class="acciones-botones">

                <button
                  class="btn-cancelar"
                  :disabled="procesando"
                  @click="cancelarRechazo"
                >
                  Cancelar
                </button>

                <button
                  class="btn-rechazar"
                  :disabled="procesando"
                  @click="confirmarRechazo"
                >
                  Confirmar rechazo
                </button>

              </div>
            </div>

            <div
              v-else-if="mostrarFormCertificacion"
              class="form-certificacion"
            >
              <p class="nota-tramite">
                Adjunte la certificación presupuestaria en PDF
                para derivar el expediente a Tesorería.
              </p>

              <label>
                Certificación presupuestaria (PDF)
                <span>*</span>
              </label>

              <ArchivoInput
                type="file"
                accept="application/pdf"
                @change="onSeleccionarCertificacion" />

              <span
                v-if="archivoCertificacion"
                class="archivo-seleccionado"
              >
                {{ archivoCertificacion.name }}
              </span>

              <div class="acciones-botones">

                <button
                  class="btn-cancelar"
                  :disabled="procesando"
                  @click="cancelarCertificacion"
                >
                  Cancelar
                </button>

                <button
                  class="btn-aprobar"
                  :disabled="procesando"
                  @click="confirmarCertificacion"
                >
                  Confirmar certificación
                </button>

              </div>
            </div>

          </div>

        </div>

      </div>
    </div>


    <!-- =================================================
         DATOS DEL SOLICITANTE
    ================================================== -->

    <div
      v-if="mostrarSolicitante"
      class="solicitante-modal-backdrop"
      @click.self="cerrarSolicitante"
    >
      <div class="detalle-modal">

        <div class="detalle-modal-header">
          <div>
            <h3>Datos del solicitante</h3>
          </div>

          <button
            class="detalle-modal-close"
            @click="cerrarSolicitante"
          >✕</button>
        </div>

        <div class="detalle-modal-body">

          <p
            v-if="cargandoSolicitante"
            class="detalle-vacio"
          >
            Cargando...
          </p>

          <template v-else-if="solicitanteDetalle">

            <div class="documento-fila">

              <div>
                <b>Nombre completo</b>
                <span>{{ solicitanteDetalle.nombre_completo || '—' }}</span>
              </div>

              <div>
                <b>Correo</b>
                <span>{{ solicitanteDetalle.email || '—' }}</span>
              </div>

            </div>

            <div class="documento-fila">

              <div>
                <b>Usuario</b>
                <span>{{ solicitanteDetalle.username || '—' }}</span>
              </div>

              <div>
                <b>Estado de la cuenta</b>
                <span>{{ solicitanteDetalle.is_active ? 'Activa' : 'Inactiva' }}</span>
              </div>

            </div>

            <div class="detalle-campo">
              <b>Roles</b>
              <span>
                {{
                  (solicitanteDetalle.roles || [])
                    .map(rol => rol.rol_nombre || rol.nombre)
                    .join(', ')
                  || 'Sin rol asignado'
                }}
              </span>
            </div>

          </template>

          <p
            v-else
            class="detalle-vacio"
          >
            No fue posible cargar los datos del solicitante.
          </p>

        </div>

      </div>
    </div>

  </div>
    <ModalSia v-if="rechazoPendiente" titulo="¿Está seguro de rechazar esta solicitud?" :ocupado="procesando" @cerrar="rechazoPendiente=null">
      <div class="daf-confirmacion-rechazo">
        <p>Se rechazará el expediente <strong>{{ rechazoPendiente.codigo }}</strong> y el motivo quedará registrado.</p>
        <div class="daf-motivo-confirmado"><small>Motivo del rechazo</small><p>{{ rechazoPendiente.motivo }}</p></div>
        <p>Revise el motivo antes de confirmar.</p>
        <p v-if="errorAccion" class="daf-confirmacion-error" role="alert">{{ errorAccion }}</p>
      </div>
      <template #acciones><button class="sia-secondary" :disabled="procesando" @click="rechazoPendiente=null">Volver sin rechazar</button><button class="daf-confirmar-rechazo" :disabled="procesando" @click="ejecutarRechazoConfirmado">{{ procesando ? 'Rechazando…' : 'Sí, rechazar solicitud' }}</button></template>
    </ModalSia>
</template>


<script setup>
import CajaChicaPanel from '../components/CajaChicaPanel.vue'
import { mostrarErrorRegla } from '../utils/errorRegla'
import CotizacionesExpediente from '../components/CotizacionesExpediente.vue'
import ModalSia from '../components/ModalSia.vue'

import CotizacionesCompra from '../components/CotizacionesCompra.vue'
import ResumenExpediente from '../components/ResumenExpediente.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import IconoSigta from '../components/IconoSigta.vue'

import {
  computed,
  onMounted,
  ref,
  watch
} from 'vue'

import {
  useRoute,
  useRouter
} from 'vue-router'

import DafMenu
  from '../components/DafMenu.vue'

import TarjetaGuardado
  from '../components/TarjetaGuardado.vue'

import { usarGuardado }
  from '../utils/guardado.js'

const rechazoPendiente = ref(null)


const router =
  useRouter()

const {
  mostrar: mostrarGuardadoOk,
  texto: textoGuardado,
  tipo: tipoGuardado,
  animar: animarGuardado,
  animarError,
  ocultar: ocultarGuardado,
} = usarGuardado()


// ==========================================================
// DATOS
// ==========================================================

const compras =
  ref([])

const cargando =
  ref(true)


// ==========================================================
// FILTRO
// ==========================================================

const filtroEstado =
  ref('')

const comprasFiltradas =
  computed(() => {

    if (!filtroEstado.value) {
      return compras.value
    }

    return compras.value.filter(
      compra =>
        bucketEstado(compra.estado)
        === filtroEstado.value
    )
  })


/* ==========================================================
   AGRUPACION VISUAL: SOLICITUDES / HISTORIAL
   Solo reparte en pantalla las MISMAS compras ya cargadas,
   usando bucketEstado(), que es la clasificacion que el modulo
   ya aplicaba. No hay estados nuevos ni consultas nuevas.
   ========================================================== */

const route = useRoute()

function seccionDe(valor) {
  return ['historial', 'dashboard'].includes(valor)
    ? valor
    : 'solicitudes'
}

const seccion = ref(seccionDe(route.query.seccion))

/* El menu lateral entra con ?seccion=historial; al cambiar de entrada
   la pestana visible se sincroniza. Solo afecta que lista se muestra. */
watch(
  () => route.query.seccion,
  valor => {
    seccion.value = seccionDe(valor)
  }
)

const comprasEnGestion = computed(() =>
  compras.value.filter(
    compra => bucketEstado(compra.estado) === 'EN_ESPERA'
  )
)

const comprasHistorial = computed(() =>
  comprasFiltradas.value.filter(
    compra => bucketEstado(compra.estado) !== 'EN_ESPERA'
  )
)

/* Conteos del resumen. Se apoyan en bucketEstado() y en el estado
   crudo de cada compra; las cuatro cifras no se solapan entre si. */

const totalPendientes = computed(() => comprasEnGestion.value.length)

/* Misma condicion que la bandeja de "Emitir Certificación"
   (DafEmitirView): ademas del estado, el expediente debe estar
   completo. Contar solo por estado daba un numero mayor que el de
   esa pantalla. */
const listaPorCertificar = computed(() =>
  compras.value.filter(
    compra =>
      compra.estado === 'EVALUADO_PENDIENTE_CERTIFICACION'
      && !compra.certificacion_presupuestaria
      && compra.informe
      && compra.poa
      && compra.proforma
      && (
        !['SOPORTE', 'MANTENIMIENTO'].includes(compra.origen_modulo)
        || compra.pedido
      )
  )
)

const totalPorCertificar = computed(() => listaPorCertificar.value.length)

const totalAprobadas = computed(() =>
  compras.value.filter(
    compra =>
      bucketEstado(compra.estado) === 'APROBADA'
      &&
      String(compra.estado || '').toUpperCase()
      !== 'EVALUADO_PENDIENTE_CERTIFICACION'
  ).length
)

const totalRechazadas = computed(() =>
  compras.value.filter(
    compra => bucketEstado(compra.estado) === 'RECHAZADA'
  ).length
)


/* Navegacion del resumen: reutiliza la seccion visual y el
   filtroEstado que ya existian, y la ruta /daf/emitir que ya existe. */
function irASolicitudes() {
  router.push({ path: '/daf/dashboard', query: { seccion: 'solicitudes' } })
}

function irAHistorial(bucket) {
  filtroEstado.value = bucket
  router.push({ path: '/daf/dashboard', query: { seccion: 'historial' } })
}

function irACertificar() {
  router.push('/daf/emitir')
}


const listaVisible = computed(() =>
  seccion.value === 'historial'
    ? comprasHistorial.value
    : comprasEnGestion.value
)


// ==========================================================
// DETALLE (DOCUMENTO)
// ==========================================================

const mostrarDetalle =
  ref(false)

const haLeidoTodo =
  ref(false)

const viaEvaluacion = ref('CAJA_CHICA')
const compraSeleccionada =
  ref(null)

const documentosExpediente =
  computed(() => {

    const c =
      compraSeleccionada.value

    if (!c) {
      return []
    }

    return [
      { label: 'Informe', url: c.informe },
      { label: 'POA', url: c.poa },
      { label: 'Proforma', url: c.proforma },
      ...(['SOPORTE','MANTENIMIENTO'].includes(c.origen_modulo) ? [{ label: 'Proveído de jefatura', url: c.pedido }] : []),
    ]
  })

const procesando =
  ref(false)

const mostrarFormRechazo =
  ref(false)

const motivoRechazoTexto =
  ref('')

const mostrarFormCertificacion =
  ref(false)

const archivoCertificacion =
  ref(null)

const errorAccion =
  ref('')


function resetearFormularios() {

  mostrarFormRechazo.value =
    false

  motivoRechazoTexto.value =
    ''

  mostrarFormCertificacion.value =
    false

  archivoCertificacion.value =
    null

  errorAccion.value =
    ''
}


function verDetalle(
  compra
) {

  viaEvaluacion.value = compra.via_adquisicion || 'CAJA_CHICA'
  compraSeleccionada.value =
    compra

  mostrarDetalle.value =
    true

  haLeidoTodo.value = false

  resetearFormularios()

  setTimeout(() => {
    // Check if scrollable content is small enough to not need scrolling
    const modals = document.querySelectorAll('.detalle-modal, .documento-body')
    for (const m of modals) {
      if (m.scrollHeight <= m.clientHeight + 10) {
        haLeidoTodo.value = true
      }
    }
  }, 100)
}

function onModalScroll(e) {
  const { scrollTop, scrollHeight, clientHeight } = e.target
  // Si llegó cerca del final (margen de 20px)
  if (scrollTop + clientHeight >= scrollHeight - 20) {
    haLeidoTodo.value = true
  }
}


function rechazarDesdeLista(
  compra
) {

  viaEvaluacion.value = compra.via_adquisicion || 'CAJA_CHICA'
  compraSeleccionada.value =
    compra

  mostrarDetalle.value =
    true

  resetearFormularios()

  mostrarFormRechazo.value =
    true
}


async function aprobarDesdeLista(
  compra
) {

  viaEvaluacion.value = compra.via_adquisicion || 'CAJA_CHICA'
  compraSeleccionada.value =
    compra

  if (
    compra.estado === 'EVALUADO_PENDIENTE_CERTIFICACION'
  ) {

    mostrarDetalle.value =
      true

    resetearFormularios()

    mostrarFormCertificacion.value =
      true

    return
  }

  await aprobarCompra()
}


function cerrarDetalle() {

  rechazoPendiente.value = null

  mostrarDetalle.value =
    false

  compraSeleccionada.value =
    null

  resetearFormularios()
}


// ==========================================================
// DATOS DEL SOLICITANTE
// ==========================================================

const mostrarSolicitante =
  ref(false)

const solicitanteDetalle =
  ref(null)

const cargandoSolicitante =
  ref(false)


async function abrirSolicitante(
  usuarioId
) {

  mostrarSolicitante.value =
    true

  cargandoSolicitante.value =
    true

  solicitanteDetalle.value =
    null

  try {

    const respuesta =
      await fetch(
        `/api/usuarios/usuarios/${usuarioId}/`,
        {
          headers: {
            Authorization: `Token ${token()}`,
            Accept: 'application/json',
          }
        }
      )

    if (
      respuesta.status === 401
    ) {

      cerrarSesion()

      return
    }

    if (respuesta.ok) {

      solicitanteDetalle.value =
        await respuesta.json()
    }

  } catch (error) {

    console.error(
      'Error cargando datos del solicitante:',
      error
    )

  } finally {

    cargandoSolicitante.value =
      false
  }
}


function cerrarSolicitante() {

  mostrarSolicitante.value =
    false

  solicitanteDetalle.value =
    null
}


// ==========================================================
// DECISIÓN (EVALUAR / CERTIFICAR)
// ==========================================================
//
// DAF interviene en 2 compuertas del BPMN de Compra Caja
// Chica: evaluar si el expediente (Informe, POA, Pedido,
// Proforma) califica presupuestariamente, y luego emitir la
// Certificación Presupuestaria en PDF para derivar el
// expediente a Tesorería. Cualquier otra etapa del proceso
// queda fuera de este panel.
// ==========================================================

function puedeAprobar(
  compra
) {

  return (
    bucketEstado(compra?.estado)
    === 'EN_ESPERA'
  )
}


function puedeRechazar(
  compra
) {

  return (
    compra?.estado
    === 'CREADO_PENDIENTE_DAF'
  )
}


function abrirFormRechazo() {

  resetearFormularios()

  mostrarFormRechazo.value =
    true
}


function cancelarRechazo() {

  resetearFormularios()
}


function abrirFormCertificacion() {

  resetearFormularios()

  mostrarFormCertificacion.value =
    true
}


function cancelarCertificacion() {

  resetearFormularios()
}


function onSeleccionarCertificacion(
  evento
) {

  errorAccion.value =
    ''

  archivoCertificacion.value =
    evento.target.files?.[0]
    || null
}


function iniciarAprobacion() {
  aprobarCompra()
}


async function confirmarCertificacion() {

  const archivo =
    archivoCertificacion.value

  if (!archivo) {

    errorAccion.value =
      'Debe adjuntar el PDF de la certificación presupuestaria.'

    return
  }

  if (
    !archivo.name.toLowerCase().endsWith('.pdf')
  ) {

    errorAccion.value =
      'La certificación debe ser un archivo PDF.'

    return
  }

  const datosFormulario =
    new FormData()

  datosFormulario.append(
    'certificacion_presupuestaria',
    archivo
  )

  await ejecutarAccion(
    'certificar-daf',
    datosFormulario,
    'aprobar',
    true,
    'Certificación presupuestaria registrada y derivada a Tesorería.'
  )
}


async function aprobarCompra() {

  if (!compraSeleccionada.value) {
    return
  }

  const confirmar =
    await window.sigtaConfirm(
      `¿Confirma que la solicitud ${compraSeleccionada.value.codigo} califica presupuestariamente?`
    )

  if (!confirmar) {
    return
  }

  const estado =
    compraSeleccionada.value.estado

  if (
    estado !== 'CREADO_PENDIENTE_DAF'
  ) {
    return
  }

  await ejecutarAccion(
    'evaluar-daf',
    { califica: true, via_adquisicion: viaEvaluacion.value },
    'aprobar',
    false,
    'Solicitud calificada como viable presupuestariamente.'
  )
}


async function confirmarRechazo() {

  const motivo =
    motivoRechazoTexto.value.trim()

  if (!motivo) {

    errorAccion.value =
      'Debe indicar el motivo del rechazo.'

    return
  }

  if (
    compraSeleccionada.value?.estado
    !== 'CREADO_PENDIENTE_DAF'
  ) {

    errorAccion.value =
      'La solicitud ya fue evaluada: solo corresponde emitir la certificación presupuestaria.'

    return
  }

  errorAccion.value = ''
  rechazoPendiente.value = { id: compraSeleccionada.value.id, codigo: compraSeleccionada.value.codigo, motivo }
}

async function ejecutarRechazoConfirmado() {
  const pendiente = rechazoPendiente.value
  if (procesando.value || !pendiente) return
  if (compraSeleccionada.value?.id !== pendiente.id || compraSeleccionada.value?.estado !== 'CREADO_PENDIENTE_DAF') {
    rechazoPendiente.value = null
    return
  }
  await ejecutarAccion(
    'evaluar-daf',
    { califica: false, motivo: pendiente.motivo },
    'rechazar',
    false,
    'Solicitud rechazada.'
  )
  if (!errorAccion.value) rechazoPendiente.value = null
}


async function ejecutarAccion(
  endpoint,
  body,
  tipo,
  esArchivo = false,
  mensajeExito = ''
) {

  procesando.value =
    true

  errorAccion.value =
    ''

  try {

    const headers = {
      Authorization: `Token ${token()}`,
      Accept: 'application/json',
    }

    if (!esArchivo) {
      headers['Content-Type'] = 'application/json'
    }

    const respuesta =
      await fetch(
        `/api/compras/solicitudes/${compraSeleccionada.value.id}/${endpoint}/`,
        {
          method: 'POST',
          headers,
          body: esArchivo ? body : JSON.stringify(body),
        }
      )

    let datos = {}

    try {
      datos = await respuesta.json()
    } catch {
      datos = {}
    }

    if (
      respuesta.status === 401
    ) {

      cerrarSesion()

      return
    }

    if (!respuesta.ok) {
      await mostrarErrorRegla(datos)

      errorAccion.value =
        datos.detalle
        || `No fue posible ${tipo === 'aprobar' ? 'registrar' : 'rechazar'} la solicitud.`

      return
    }

    cerrarDetalle()

    window.dispatchEvent(new Event('sia-certificaciones-actualizadas'))
    await cargarCompras()

    await animarGuardado(
      mensajeExito
      || (tipo === 'aprobar' ? 'Acción registrada correctamente.' : 'Solicitud rechazada.')
    )

  } catch (error) {

    console.error(
      'Error ejecutando la decisión:',
      error
    )

    errorAccion.value =
      'No fue posible comunicarse con el servidor.'

  } finally {

    procesando.value =
      false
  }
}


// ==========================================================
// TOKEN
// ==========================================================

function token() {

  return localStorage.getItem(
    'sigta_token'
  )
}


// ==========================================================
// INICIO
// ==========================================================

onMounted(
  async () => {

    if (!token()) {

      router.push(
        '/login'
      )

      return
    }


    await cargarCompras()
  }
)


// ==========================================================
// NORMALIZAR
// ==========================================================

function normalizarLista(
  datos
) {

  if (
    Array.isArray(datos)
  ) {

    return datos
  }


  if (
    Array.isArray(
      datos?.results
    )
  ) {

    return datos.results
  }


  return []
}


// ==========================================================
// CARGAR COMPRAS
// ==========================================================

async function cargarCompras() {

  cargando.value =
    true


  try {

    const respuesta =
      await fetch(
        '/api/compras/solicitudes/',
        {
          headers: {

            Authorization:
              `Token ${token()}`,

            Accept:
              'application/json',
          }
        }
      )


    if (
      respuesta.status === 401
    ) {

      cerrarSesion()

      return
    }


    if (!respuesta.ok) {
      await mostrarErrorRegla(datos)

      console.error(
        'Compras:',
        respuesta.status
      )

      compras.value = []

      return
    }


    const datos =
      await respuesta.json()


    compras.value =
      normalizarLista(
        datos
      )
      .sort(
        (a, b) => {

          const fechaA =
            new Date(a.creado_en || 0).getTime()

          const fechaB =
            new Date(b.creado_en || 0).getTime()

          return fechaB - fechaA
        }
      )


  } catch (error) {

    console.error(
      'Error cargando compras:',
      error
    )

    compras.value = []


  } finally {

    cargando.value =
      false
  }
}


// ==========================================================
// ESTADO (AGRUPACIÓN VISUAL SIMPLIFICADA PARA DAF)
// ==========================================================
//
// Para DAF, "en espera" son únicamente los 2 estados que le
// corresponde resolver: CREADO_PENDIENTE_DAF (evaluar) y
// EVALUADO_PENDIENTE_CERTIFICACION (certificar). Cualquier
// estado posterior ya avanzó fuera de su bandeja.
// ==========================================================

function bucketEstado(
  estado
) {

  const codigo =
    String(
      estado
      || ''
    )
      .trim()
      .toUpperCase()


  if (
    codigo === 'RECHAZADO'
    ||
    codigo === 'ANULADO'
  ) {

    return 'RECHAZADA'
  }


  if (
    codigo === 'CREADO_PENDIENTE_DAF'
  ) {

    return 'EN_ESPERA'
  }


  return 'APROBADA'
}


function etiquetaBucket(
  bucket
) {

  return (
    {
      EN_ESPERA: 'Aprobación en espera',
      APROBADA: 'Aprobada',
      RECHAZADA: 'Rechazada',
    }[bucket]
    || bucket
  )
}


function etiquetaFiltroVacio(
  bucket
) {

  return (
    {
      APROBADA: 'solicitudes aprobadas',
      RECHAZADA: 'solicitudes rechazadas',
    }[bucket]
    || 'solicitudes'
  )
}


function claseBucket(
  bucket
) {

  return (
    {
      EN_ESPERA: 'working',
      APROBADA: 'closed',
      RECHAZADA: 'cancelled',
    }[bucket]
    || 'working'
  )
}


function iconoBucket(
  bucket
) {

  return (
    {
      EN_ESPERA: '⏳',
      APROBADA: '✅',
      RECHAZADA: '❌',
    }[bucket]
    || '⏳'
  )
}


function descripcionBucket(
  bucket
) {

  return (
    {
      EN_ESPERA: 'El expediente se encuentra pendiente de evaluación o certificación.',
      APROBADA: 'El expediente ya fue evaluado y certificado por la DAF.',
      RECHAZADA: 'El expediente fue rechazado.',
    }[bucket]
    || ''
  )
}


// ==========================================================
// FECHA
// ==========================================================

function formatearFecha(
  fecha
) {

  if (!fecha) {

    return ''
  }


  try {

    return new Date(
      fecha
    ).toLocaleString(
      'es-BO',
      {
        dateStyle: 'short',
        timeStyle: 'short',
      }
    )

  } catch {

    return ''
  }
}


// ==========================================================
// SESIÓN
// ==========================================================

function cerrarSesion() {

  localStorage.removeItem(
    'sigta_token'
  )

  localStorage.removeItem(
    'sigta_usuario'
  )

  router.push(
    '/login'
  )
}

</script>


<style scoped>
/* ==========================================================
   RESUMEN DE SOLICITUDES
   ========================================================== */

.daf-resumen {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.daf-kpi {
  display: block;
  width: 100%;
  text-align: left;
  font-family: inherit;
  cursor: pointer;
  transition: box-shadow .2s ease, transform .2s ease;
  padding: 16px 18px;
  border: 1px solid var(--sigta-borde);
  border-top: 3px solid var(--sigta-borde);
  border-radius: 11px;
  background: var(--sigta-blanco);
  box-shadow: 0 3px 12px rgba(11, 40, 79, .05);
}

.daf-kpi span {
  display: block;
  color: var(--sigta-texto-suave);
  font-size: 10.5px;
  font-weight: 800;
  letter-spacing: .3px;
  text-transform: uppercase;
  line-height: 1.3;
  min-height: 26px;
}

.daf-kpi strong {
  display: block;
  margin-top: 6px;
  color: var(--sigta-texto);
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
}

.daf-kpi:hover {
  box-shadow: 0 10px 22px rgba(11, 40, 79, .12);
  transform: translateY(-2px);
}

.k-espera { border-top-color: var(--sigta-mostaza); }
.k-certificar { border-top-color: var(--sigta-azul-medio); }
.k-aprobada { border-top-color: var(--sigta-exito); }
.k-rechazada { border-top-color: var(--sigta-error); }

@media (max-width: 1050px) {
  .daf-resumen { grid-template-columns: 1fr 1fr; }
}



* {
  box-sizing: border-box;
}


/* =========================================================
   LAYOUT
========================================================= */

.layout {
  min-height: 100vh;
  display: flex;
  background: var(--sigta-azul-tenue);
  font-family: var(--sigta-fuente);
}


.main {
  flex: 1;
  min-width: 0;
  padding: 27px;
  overflow-x: hidden;
}


/* =========================================================
   HEADER
========================================================= */

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
}


.page-header h1 {
  margin: 0;
  color: var(--sigta-texto);
  font-size: 33px;
}


.page-header p {
  margin: 5px 0 0;
  color: var(--sigta-texto-suave);
  font-size: 17px;
}


.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}


.filtro-estado {
  min-height: 41px;
  padding: 0 12px;
  border: 1px solid var(--sigta-borde);
  border-radius: 7px;
  background: white;
  color: var(--sigta-texto);
  font-family: inherit;
  font-size: 15px;
  outline: none;
}


.refresh-button {
  min-height: 41px;
  padding: 0 15px;
  border: 1px solid var(--sigta-azul);
  border-radius: 7px;
  background: white;
  color: var(--sigta-azul);
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
}


.refresh-button:disabled {
  opacity: .6;
  cursor: not-allowed;
}


/* =========================================================
   LISTADO
========================================================= */

.requests-card {
  overflow: hidden;
  border-radius: 10px;
  background: white;
  box-shadow: 0 4px 14px rgba(0,0,0,.05);
}


.request-list {
  display: flex;
  flex-direction: column;
}


.request {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 17px 20px;
  border-bottom: 1px solid var(--sigta-azul-tenue);
}


.request:last-child {
  border-bottom: none;
}


.request-main {
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: 155px 1fr;
  gap: 15px;
}


.request-code strong {
  display: block;
  color: var(--sigta-azul);
  font-size: 15px;
}


.request-code small {
  display: block;
  margin-top: 4px;
  color: var(--sigta-texto-suave);
  font-size: 13px;
}


.request-info h3 {
  margin: 0 0 5px;
  color: var(--sigta-azul);
  font-size: 18px;
}


.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}


.meta span {
  padding: 4px 6px;
  border-radius: 4px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
  font-size: 13px;
}


.request-side {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 9px;
}


/* =========================================================
   ESTADO
========================================================= */

.status {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}


.status.working {
  background: var(--sigta-mostaza);
  color: var(--sigta-azul);
}

.status.closed {
  background: #dcfce7;
  color: #15803d;
}

.status.cancelled {
  background: #fee2e2;
  color: #b91c1c;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.view,
.row-aprobar,
.row-rechazar {
  padding: 6px 12px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.view:hover,
.row-aprobar:hover,
.row-rechazar:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.view {
  background: var(--sigta-blanco);
  border-color: var(--sigta-borde-suave);
  color: var(--sigta-azul);
}

.view.btn-evaluar {
  background: var(--sigta-exito);
  color: white;
  border-color: var(--sigta-exito);
  font-weight: 800;
}
.view.btn-evaluar:hover {
  background: #166534;
}

.row-aprobar {
  background: var(--sigta-exito-fondo);
  border-color: #bbf7d0;
  color: var(--sigta-exito);
}

.row-rechazar {
  background: var(--sigta-error-fondo);
  border-color: #fecaca;
  color: var(--sigta-error);
}


/* =========================================================
   VACÍOS
========================================================= */

.loading,
.empty {
  padding: 45px 20px;
  text-align: center;
  color: var(--sigta-texto-suave);
  font-size: 16px;
}


.empty {
  border-radius: 10px;
  background: white;
}


/* =========================================================
   DOCUMENTO DE DETALLE
========================================================= */

.documento-modal {
  max-width: 1060px;
  max-height: 94vh;
}


.documento-modal .detalle-modal-header {
  padding: 14px 22px 10px;
}


.documento-modal .detalle-modal-header h3 {
  font-size: 20px;
}


.documento-modal .detalle-modal-header small {
  font-size: 13px;
}


.documento-body {
  padding: 12px 26px 16px;
}


.estado-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px 14px;
  border-radius: 8px;
}


.estado-banner-icono {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,.6);
  font-size: 19px;
}


.estado-banner strong {
  display: block;
  font-size: 18px;
  font-weight: 800;
}


.estado-banner-descripcion {
  display: block;
  margin-top: 2px;
  font-size: 15px;
  font-weight: 500;
  opacity: .85;
}


.estado-banner.working {
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-mostaza-oscuro);
}


.estado-banner.closed {
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
}


.estado-banner.cancelled {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
}


.documento-seccion {
  padding: 12px 0;
  border-top: 1px solid var(--sigta-azul-tenue);
}


.documento-seccion:first-of-type {
  border-top: none;
  padding-top: 0;
}


.documento-header-titulo {
  display: flex;
  align-items: center;
  gap: 12px;
}


.documento-header-icono {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--sigta-mostaza-suave);
  font-size: 17px;
}


.documento-titulo-fila {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--sigta-azul-tenue);
}


.documento-icono {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-mostaza-oscuro);
  font-size: 13px;
}


.documento-titulo {
  display: block;
  margin-bottom: 8px;
  color: var(--sigta-azul);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: .6px;
  text-transform: uppercase;
}


.documento-titulo-fila .documento-titulo {
  margin-bottom: 0;
}


.documento-seccion h4 {
  margin: 0 0 6px;
  color: var(--sigta-texto);
  font-size: 21px;
}


.documento-seccion > p {
  margin: 0 0 10px;
  color: var(--sigta-azul);
  font-size: 17px;
  line-height: 1.5;
  white-space: pre-wrap;
}


.documento-seccion b {
  display: block;
  margin-bottom: 4px;
  color: var(--sigta-azul-medio);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .6px;
  text-transform: uppercase;
}


.documento-columnas {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 30px;
}


.documento-col {
  min-width: 0;
}


.documento-fila {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 10px;
  margin-bottom: 8px;
}


.documento-fila-3 {
  grid-template-columns: repeat(3, 1fr);
}


.documento-fila-2 {
  grid-template-columns: repeat(2, 1fr);
}


.documento-fila-1 {
  grid-template-columns: 1fr;
  gap: 10px;
}


.documento-fila > div span {
  display: block;
  color: var(--sigta-texto);
  font-size: 17px;
}


.solicitante-link {
  display: block;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
}


.solicitante-link span {
  display: block;
  color: var(--sigta-azul);
  font-size: 14px;
  font-weight: 700;
  text-decoration: underline;
}


.solicitante-link:hover span {
  color: var(--sigta-azul);
}


.solicitante-link small {
  display: block;
  margin-top: 2px;
  color: var(--sigta-texto);
  font-size: 13px;
}


.solicitante-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(10, 20, 35, .55);
}


.documento-lista {
  display: flex;
  flex-direction: column;
  gap: 6px;
}


.documento-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 7px 12px;
  border: none;
  border-radius: 7px;
  font-family: inherit;
  text-align: left;
  text-decoration: none;
}


.documento-item-icono {
  flex-shrink: 0;
  font-size: 16px;
}


.documento-item-label {
  flex: 1;
  color: var(--sigta-texto);
  font-size: 14px;
  font-weight: 700;
}


.documento-item small {
  font-size: 13px;
}


.documento-item-accion {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}


.documento-item-ojo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255,255,255,.6);
  font-size: 11px;
}


.documento-item.ok {
  background: var(--sigta-exito-fondo);
}


.documento-item.ok .documento-item-accion {
  color: var(--sigta-exito);
  font-weight: 700;
}


.documento-item.falta {
  background: var(--sigta-azul-tenue);
}


.documento-item.falta small {
  color: var(--sigta-texto-suave);
}


.motivo-rechazo {
  padding: 14px;
  border: none;
  border-radius: 8px;
  background: var(--sigta-error-fondo);
}


.motivo-rechazo .documento-titulo {
  color: var(--sigta-error);
}


.motivo-rechazo p {
  margin: 0;
  color: var(--sigta-error);
  font-size: 14px;
  line-height: 1.5;
}


/* =========================================================
   ACCIONES DE DECISIÓN
========================================================= */

.documento-acciones {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--sigta-azul-tenue);
}


.nota-tramite {
  margin: 0;
  padding: 12px 14px;
  border-radius: 7px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
  font-size: 14px;
  line-height: 1.5;
}


.accion-error {
  margin: 0 0 10px;
  padding: 10px 12px;
  border-radius: 7px;
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
  font-size: 14px;
}


.acciones-botones {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.eval-mode {
  flex-direction: column;
  align-items: center;
  margin-top: 10px;
  gap: 8px;
}

.scroll-lock-msg {
  text-align: center;
  padding: 15px;
  margin-top: 15px;
  background: #f1f5f9;
  border-radius: 8px;
  color: var(--sigta-azul);
  font-weight: bold;
  font-size: 13px;
  border: 1px dashed #cbd5e1;
  animation: pulse 2s infinite;
}
.scroll-lock-msg span {
  display: inline-block;
  animation: bounce 2s infinite;
}
@keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(3px); } }

.btn-aprobar,
.btn-rechazar,
.btn-cancelar {
  min-height: 40px;
  padding: 0 16px;
  border: none;
  border-radius: 7px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}

.btn-eval-main {
  width: 100%;
  min-height: 42px;
  font-size: 15px;
  letter-spacing: 0.5px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.btn-eval-main:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.btn-aprobar {
  background: var(--sigta-exito);
  color: white;
}


.btn-rechazar {
  background: var(--sigta-error);
  color: white;
}


.btn-cancelar {
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
}


.btn-aprobar:disabled,
.btn-rechazar:disabled,
.btn-cancelar:disabled {
  opacity: .6;
  cursor: not-allowed;
}


.form-rechazo label {
  display: block;
  margin-bottom: 6px;
  color: var(--sigta-azul);
  font-size: 14px;
  font-weight: 700;
}


.form-rechazo label span {
  color: var(--sigta-error);
}


.form-rechazo textarea {
  width: 100%;
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid var(--sigta-borde);
  border-radius: 7px;
  background: white;
  color: var(--sigta-texto);
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  outline: none;
}


.form-certificacion .nota-tramite {
  margin-bottom: 12px;
}


.form-certificacion label {
  display: block;
  margin-bottom: 6px;
  color: var(--sigta-azul);
  font-size: 14px;
  font-weight: 700;
}


.form-certificacion label span {
  color: var(--sigta-error);
}


.form-certificacion input[type="file"] {
  width: 100%;
  margin-bottom: 8px;
  font-size: 14px;
}


.archivo-seleccionado {
  display: block;
  margin-bottom: 10px;
  color: var(--sigta-texto-suave);
  font-size: 13px;
}


/* =========================================================
   RESPONSIVE
========================================================= */

@media (max-width: 760px) {

  .layout {
    display: block;
  }


  .main {
    padding: 16px;
  }


  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }


  .header-actions {
    width: 100%;
  }


  .filtro-estado {
    flex: 1;
  }


  .request {
    align-items: flex-start;
    flex-direction: column;
  }


  .request-main {
    grid-template-columns: 1fr;
  }


  .request-side {
    width: 100%;
    align-items: flex-start;
  }


  .documento-fila {
    grid-template-columns: 1fr;
  }


  .documento-columnas {
    grid-template-columns: 1fr;
  }

}

</style>

<style scoped>
.documento-columnas { grid-template-columns:1fr; }.search-box,.buscador { width:100%;max-width:none; }
</style>

<style scoped>
.daf-confirmacion-rechazo{font-size:14px;line-height:1.7}.daf-motivo-confirmado{padding:16px 18px;border-radius:9px;background:#f7f9fc;border:1px solid var(--sigta-borde);margin:18px 0}.daf-motivo-confirmado small{display:block;color:var(--sigta-texto-suave);font-weight:700}.daf-motivo-confirmado p{white-space:pre-wrap;overflow-wrap:anywhere;margin:8px 0 0}.daf-confirmar-rechazo{border:0;border-radius:8px;padding:11px 16px;background:var(--sigta-error);color:white;font:inherit;font-weight:700;cursor:pointer}.daf-confirmar-rechazo:disabled{opacity:.6;cursor:wait}.daf-confirmacion-error{color:var(--sigta-error)}
</style>
