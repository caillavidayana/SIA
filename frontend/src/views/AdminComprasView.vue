<template>
  <div class="layout">

    <AdminMenu />

    <main class="main">

      <!-- =================================================
           ENCABEZADO
      ================================================== -->
      <header class="page-header">

        <div>
          <h1>
            {{
              vista === 'PENDIENTES'
                ? 'Autorizar compras'
                : 'Historial'
            }}
          </h1>

          <p v-if="vista === 'PENDIENTES'">
            {{ conteos.PENDIENTES }}
            {{ conteos.PENDIENTES === 1 ? 'solicitud' : 'solicitudes' }}
            de compra pendientes de aprobar o rechazar.
          </p>

          <p v-else>
            {{ conteos.APROBADA }}
            {{ conteos.APROBADA === 1 ? 'aprobada' : 'aprobadas' }}
            y
            {{ conteos.RECHAZADA }}
            {{ conteos.RECHAZADA === 1 ? 'rechazada' : 'rechazadas' }}.
            Solo consulta.
          </p>
        </div>

        <div class="header-actions">
          <select v-model="filtroProceso" class="filtro-estado" aria-label="Proceso">
            <option value="">Ambos procesos</option><option value="MANTENIMIENTO">Mantenimiento</option><option value="SOPORTE">Soporte técnico</option>
          </select>

          <select
            v-if="vista === 'HISTORIAL'"
            v-model="filtroHistorial"
            class="filtro-estado"
          >
            <option value="">Aprobadas y rechazadas</option>
            <option value="APROBADA">Solo aprobadas</option>
            <option value="RECHAZADA">Solo rechazadas</option>
          </select>



        </div>

      
        <UsuarioHeader @actualizar="cargarCompras" />
      </header>
      <CajaChicaPanel resumen />


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
        v-else-if="comprasFiltradas.length === 0"
        class="empty"
      >
        {{ mensajeVacio }}
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
            v-for="compra in comprasFiltradas"
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
                  :class="['view', { 'btn-evaluar': bucketEstado(compra.estado) === 'EN_ESPERA' }]"
                  @click="verDetalle(compra)"
                >
                  {{ bucketEstado(compra.estado) === 'EN_ESPERA' ? 'Evaluar' : 'Ver detalle' }}
                </button>

              </div>

            </div>

          </article>

        </div>

      </section>

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

        <div class="documento-body" @scroll="onModalScroll"><DocumentosExpediente v-if="compraSeleccionada" base="/api/compras/solicitudes" :id="compraSeleccionada.id" /><CotizacionesCompra v-if="compraSeleccionada" :id="compraSeleccionada.id" />

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


          <div class="documento-seccion">

            <div class="documento-titulo-fila">
              <IconoSigta class="documento-icono" nombre="almacen" :tamano="18" />
              <span class="documento-titulo">
                Producto o servicio a comprar
              </span>
            </div>

            <p class="doc-descripcion">
              {{ compraSeleccionada?.descripcion || 'Sin descripción registrada.' }}
            </p>

            <div class="doc-monto">
              <b>Monto estimado</b>
              <strong>
                {{
                  compraSeleccionada?.monto_estimado
                    ? `Bs ${Number(compraSeleccionada.monto_estimado).toFixed(2)}`
                    : 'No indicado'
                }}
              </strong>
            </div>

            <dl class="dl-grid">
              <div class="dl">
                <b>Tipo</b>
                <span>{{ compraSeleccionada?.tipo_nombre || compraSeleccionada?.tipo || 'No indicado' }}</span>
              </div>
              <div class="dl">
                <b>Cantidad</b>
                <span>{{ compraSeleccionada?.cantidad || 1 }}</span>
              </div>
              <div class="dl full">
                <b>Especificaciones</b>
                <span>{{ compraSeleccionada?.especificaciones || 'No registradas.' }}</span>
              </div>
              <div class="dl full">
                <b>Justificación</b>
                <span>{{ compraSeleccionada?.justificacion || 'No registrada.' }}</span>
              </div>
            </dl>

          </div>


          <div class="documento-seccion">

            <div class="documento-titulo-fila">
              <IconoSigta class="documento-icono" nombre="solicitudes" :tamano="18" />
              <span class="documento-titulo">
                Datos del expediente
              </span>
            </div>

            <dl class="dl-grid">

              <div class="dl full">
                <b>Solicitante</b>
                <button
                  v-if="compraSeleccionada?.solicitante"
                  type="button"
                  class="solicitante-link"
                  @click="abrirSolicitante(compraSeleccionada.solicitante)"
                >
                  <span>{{ compraSeleccionada?.solicitante_nombre || 'Sin información' }}</span>
                  <small v-if="compraSeleccionada?.solicitante_email">
                    {{ compraSeleccionada.solicitante_email }}
                  </small>
                </button>
                <span v-else>Sin información</span>
              </div>

              <div class="dl">
                <b>Área</b>
                <span>{{ compraSeleccionada?.area_nombre || 'No indicada' }}</span>
              </div>

              <div class="dl">
                <b>Vía de adquisición</b>
                <span>{{ compraSeleccionada?.via_nombre || 'No indicada' }}</span>
              </div>

              <div class="dl">
                <b>Fecha de registro</b>
                <span>{{ formatearFecha(compraSeleccionada?.creado_en) }}</span>
              </div>

              <div class="dl" v-if="compraSeleccionada?.monto_desembolsado">
                <b>Monto desembolsado</b>
                <span>Bs {{ Number(compraSeleccionada.monto_desembolsado).toFixed(2) }}</span>
              </div>

            </dl>

          </div>


          <div class="documento-seccion">

            <div class="documento-titulo-fila">
              <IconoSigta class="documento-icono" nombre="auditoria" :tamano="18" />
              <span class="documento-titulo">
                Documentos del expediente
              </span>
            </div>

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
              v-if="!mostrarFormRechazo"
            >
              <div v-if="haLeidoTodo" class="acciones-botones eval-mode">
                <button
                  class="btn-aprobar btn-eval-main"
                  :disabled="procesando"
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
                placeholder="Explique por qué se rechaza esta solicitud..."
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



          </div>

        </div>

      </div>
    </div>


    <!-- Confirmación propia de la autorización del Director. -->
    <div
      v-if="mostrarModalExito"
      class="detalle-modal-backdrop modal-exito-backdrop"
      @click.self="cerrarModalExito"
    >
      <section
        class="modal-exito-director"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-modal-exito"
      >
        <div class="modal-exito-icono" aria-hidden="true">✓</div>

        <h2 id="titulo-modal-exito">¡Autorizada con éxito!</h2>

        <p>
          La compra fue autorizada y el expediente fue derivado a
          Tesorería para realizar el desembolso.
        </p>

        <button
          type="button"
          class="modal-exito-boton"
          @click="cerrarModalExito"
        >
          Aceptar
        </button>
      </section>
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
</template>


<script setup>
import CajaChicaPanel from '../components/CajaChicaPanel.vue'
import { mostrarErrorRegla } from '../utils/errorRegla'
import DocumentosExpediente from '../components/DocumentosExpediente.vue'
import CotizacionesCompra from '../components/CotizacionesCompra.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import { coincideProceso } from '../utils/portal'
import IconoSigta from '../components/IconoSigta.vue'

import {
  computed,
  onMounted,
  ref
} from 'vue'

import {
  useRoute,
  useRouter
} from 'vue-router'

import AdminMenu
  from '../components/AdminMenu.vue'


const router =
  useRouter()

const route =
  useRoute()


// ==========================================================
// DATOS
// ==========================================================

const compras =
  ref([])

const cargando =
  ref(true)

const mostrarModalExito =
  ref(false)


// ==========================================================
// FILTRO
// ==========================================================

// Reparto de las solicitudes entre las dos entradas de menú que
// comparten este componente:
//
//   "Solicitudes" (/admin/compras)   -> SOLO las que el Director
//                                       decide: la DAF ya
//                                       certificó y el expediente
//                                       espera su autorización.
//   "Historial"   (/admin/historial) -> SOLO las que él ya aprobó
//                                       o rechazó.
//
// Mientras el expediente está en revisión de la DAF (evaluación y
// certificación del presupuesto) NO aparece en ninguna de las dos:
// no es trabajo suyo ni una decisión que haya tomado. Al aprobar o
// rechazar, la solicitud cambia de estado y pasa sola al Historial.

// bucketEstado() ya distingue los dos casos:
//   EN_ESPERA        -> VERIFICADO_PENDIENTE_AUTORIZACION (él)
//   EN_REVISION_DAF  -> pendiente DAF / pendiente certificación
// así que basta con apoyarse en él.

const vista =
  computed(() =>
    route.meta.vista === 'HISTORIAL'
      ? 'HISTORIAL'
      : 'PENDIENTES'
  )


const filtroHistorial =
  ref('')


const filtroProceso = ref(typeof route.query.proceso === 'string' ? route.query.proceso : '')
const comprasPorProceso = computed(() => compras.value.filter(c=>coincideProceso(c,filtroProceso.value)))

const conteos =
  computed(() => {

    const total = {
      PENDIENTES: 0,
      APROBADA: 0,
      RECHAZADA: 0,
    }

    for (const compra of comprasPorProceso.value) {

      const bucket =
        bucketEstado(compra.estado)

      if (bucket === 'EN_ESPERA') {
        total.PENDIENTES += 1
      }

      else if (bucket === 'APROBADA') {
        total.APROBADA += 1
      }

      else if (bucket === 'RECHAZADA') {
        total.RECHAZADA += 1
      }

      // EN_REVISION_DAF no se cuenta: no es del Director.
    }

    total.HISTORIAL =
      total.APROBADA
      + total.RECHAZADA

    return total
  })


const comprasFiltradas =
  computed(() => {

    if (vista.value === 'PENDIENTES') {

      return comprasPorProceso.value.filter(
        compra =>
          bucketEstado(compra.estado)
          === 'EN_ESPERA'
      )
    }

    return comprasPorProceso.value.filter(
      compra => {

        const bucket =
          bucketEstado(compra.estado)

        // Solo lo ya decidido por el Director. Lo que sigue en
        // revisión de la DAF no entra en el historial.
        if (
          bucket !== 'APROBADA'
          && bucket !== 'RECHAZADA'
        ) {
          return false
        }

        if (!filtroHistorial.value) {
          return true
        }

        return bucket === filtroHistorial.value
      }
    )
  })


const mensajeVacio =
  computed(() => {

    if (vista.value === 'PENDIENTES') {
      return (
        'No hay solicitudes esperando su autorización. '
        + 'Aparecerán aquí cuando la DAF certifique el '
        + 'presupuesto.'
      )
    }

    return (
      {
        APROBADA: 'Todavía no hay solicitudes aprobadas.',
        RECHAZADA: 'Todavía no hay solicitudes rechazadas.',
      }[filtroHistorial.value]
      || 'Todavía no hay solicitudes resueltas.'
    )
  })


// ==========================================================
// DETALLE (DOCUMENTO)
// ==========================================================

const mostrarDetalle =
  ref(false)
const haLeidoTodo = ref(false)

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
      { label: 'Certificación presupuestaria', url: c.certificacion_presupuestaria },
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

  compraSeleccionada.value =
    compra

  mostrarDetalle.value =
    true
    
  haLeidoTodo.value = false

  resetearFormularios()

  setTimeout(() => {
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
  if (scrollTop + clientHeight >= scrollHeight - 20) {
    haLeidoTodo.value = true
  }
}


function rechazarDesdeLista(
  compra
) {

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

  mostrarDetalle.value =
    false

  compraSeleccionada.value =
    null

  resetearFormularios()
}


function cerrarModalExito() {

  mostrarModalExito.value =
    false
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
// DECISIÓN (APROBAR / RECHAZAR)
// ==========================================================
//
// El BPMN de Compra Caja Chica exige, antes de aprobar, el
// expediente completo: INFORME, POA, PEDIDO y PROFORMA (los
// sube la Unidad Solicitante al crear la solicitud) y la
// CERTIFICACIÓN PRESUPUESTARIA (la genera OAF/DAF, en PDF).
// Cuando la solicitud está en EVALUADO_PENDIENTE_CERTIFICACION,
// "Aprobar" pide adjuntar ese PDF (DAF se lo hace llegar al
// administrador) en vez de un simple sí/no. Rechazar, en
// cambio, no necesita ningún documento adicional y está
// disponible en cualquier estado "en espera".
// ==========================================================

function puedeAprobar(compra) {
  return compra?.puede_aprobar === true
}


function puedeRechazar(
  compra
) {

  return (
    bucketEstado(compra?.estado)
    === 'EN_ESPERA'
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


function iniciarAprobacion() {
  aprobarCompra()
}


async function aprobarCompra() {

  if (!compraSeleccionada.value) {
    return
  }

  const confirmar =
    await window.sigtaConfirm(
      `¿Confirma aprobar la solicitud ${compraSeleccionada.value.codigo}? Será enviada a Tesorería para su desembolso.`
    )

  if (!confirmar) {
    return
  }

  const estado =
    compraSeleccionada.value.estado

  if (estado !== 'VERIFICADO_PENDIENTE_AUTORIZACION') {
    errorAccion.value = 'Esta solicitud no está lista para su autorización o ya fue procesada.'
    return
  }

  await ejecutarAccion(
    'visto-bueno-director',
    {},
    'aprobar'
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

  const estado =
    compraSeleccionada.value.estado

  const endpoint =
    estado === 'CREADO_PENDIENTE_DAF'
      ? 'evaluar-daf'
      : 'rechazar'

  const body =
    estado === 'CREADO_PENDIENTE_DAF'
      ? { califica: false, motivo }
      : { motivo }

  await ejecutarAccion(
    endpoint,
    body,
    'rechazar'
  )
}


async function ejecutarAccion(
  endpoint,
  body,
  tipo,
  esArchivo = false
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
        || `No fue posible ${tipo === 'aprobar' ? 'aprobar' : 'rechazar'} la solicitud.`

      return
    }

    cerrarDetalle()

    await cargarCompras()

    if (tipo === 'aprobar') {
      mostrarModalExito.value = true
    } else {
      if (window.sigtaAlert) await window.sigtaAlert('La solicitud ha sido rechazada exitosamente.');
      else alert('La solicitud ha sido rechazada exitosamente.');
    }

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
        '/api/compras/solicitudes/?bandeja=direccion',
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
// ESTADO (AGRUPACIÓN VISUAL SIMPLIFICADA)
// ==========================================================
//
// Estados reales del modelo SolicitudCompra (flujo de Caja
// Chica): CREADO_PENDIENTE_DAF, EVALUADO_PENDIENTE_CERTIFICACION,
// VERIFICADO_PENDIENTE_AUTORIZACION,
// APROBADO_PARA_DESEMBOLSO, FONDOS_DESEMBOLSADOS, COMPRA_REGISTRADA,
// COMPRADO_Y_ENTREGADO, DESCARGO_PENDIENTE_LIQUIDACION,
// CERRADO_ARCHIVADO, RECHAZADO, ANULADO.
//
// Se agrupan en 3 buckets para el solicitante/administrador:
// EN_ESPERA, APROBADA, RECHAZADA.
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
    codigo === 'APROBADO_PARA_DESEMBOLSO'
    ||
    codigo === 'FONDOS_DESEMBOLSADOS'
    ||
    codigo === 'COMPRA_REGISTRADA'
    ||
    codigo === 'COMPRADO_Y_ENTREGADO'
    ||
    codigo === 'DESCARGO_PENDIENTE_LIQUIDACION'
    ||
    codigo === 'CERRADO_ARCHIVADO'
  ) {

    return 'APROBADA'
  }


  if (
    codigo === 'CREADO_PENDIENTE_DAF'
    ||
    codigo === 'EVALUADO_PENDIENTE_CERTIFICACION'
  ) {

    return 'EN_REVISION_DAF'
  }

  if (
    codigo === 'VERIFICADO_PENDIENTE_AUTORIZACION'
  ) {

    return 'EN_ESPERA'
  }


  return 'EN_REVISION_DAF' // Una etapa desconocida no habilita autorización.
}


function etiquetaBucket(
  bucket
) {

  return (
    {
      EN_REVISION_DAF: 'En revisión DAF',
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
      EN_REVISION_DAF: 'abierto',
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
      EN_ESPERA: 'La solicitud se encuentra pendiente de aprobación.',
      APROBADA: 'La solicitud fue aprobada.',
      RECHAZADA: 'La solicitud fue rechazada.',
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
  padding: 5px 8px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 800;
}


.status.working {
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-mostaza-oscuro);
}

.status.abierto {
  background: #e0f2fe;
  color: #0284c7;
}


.status.closed {
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
}


.status.cancelled {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
}


.row-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}


.view,
.row-aprobar,
.row-rechazar {
  padding: 6px 8px;
  border: none;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}


.view {
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
}

.view.btn-evaluar {
  background: var(--sigta-exito);
  color: white;
  font-weight: 800;
  border: none;
}
.view.btn-evaluar:hover {
  background: #166534;
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
  max-width: 640px;
}


.documento-modal .detalle-modal-header h3 {
  font-size: 20px;
}


.documento-modal .detalle-modal-header small {
  font-size: 13px;
}


.documento-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--sigta-azul-tenue);
}


.estado-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 0;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, .05);
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

.estado-banner.abierto {
  background: #e0f2fe;
  color: #0284c7;
}


.estado-banner.closed {
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
}


.estado-banner.cancelled {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
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


/* Cada sección es una tarjeta blanca sobre el fondo azul tenue */
.documento-seccion {
  padding: 16px;
  border: 1px solid var(--sigta-borde);
  border-radius: 12px;
  background: var(--sigta-blanco);
  box-shadow: 0 2px 8px rgba(11, 40, 79, .04);
}

.documento-seccion:first-of-type { padding-top: 16px; }


.documento-titulo-fila {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
}


.documento-icono {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-azul);
}


.documento-titulo {
  display: block;
  color: var(--sigta-texto-suave);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .5px;
  text-transform: uppercase;
}


/* Descripción del producto/servicio */
.doc-descripcion {
  margin: 0 0 14px;
  color: var(--sigta-texto);
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
}


/* Monto destacado */
.doc-monto {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--sigta-mostaza-suave);
  border: 1px solid var(--sigta-mostaza-clara);
}

.doc-monto b {
  color: var(--sigta-mostaza-oscuro);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .5px;
  text-transform: uppercase;
}

.doc-monto strong {
  color: var(--sigta-azul-oscuro);
  font-size: 20px;
  font-weight: 800;
  white-space: nowrap;
}


/* Rejilla de pares dato/valor */
.dl-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  margin: 0;
  border: 1px solid var(--sigta-borde-suave);
  border-radius: 10px;
  overflow: hidden;
  background: var(--sigta-borde-suave);
}

.dl {
  padding: 10px 12px;
  background: var(--sigta-blanco);
}

.dl.full { grid-column: 1 / -1; }

.dl b {
  display: block;
  margin-bottom: 3px;
  color: var(--sigta-texto-suave);
  font-size: 10.5px;
  font-weight: 800;
  letter-spacing: .4px;
  text-transform: uppercase;
}

.dl > span {
  display: block;
  color: var(--sigta-texto);
  font-size: 14px;
  line-height: 1.45;
  white-space: pre-wrap;
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
  gap: 8px;
}


.documento-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 9px;
  font-family: inherit;
  text-align: left;
  text-decoration: none;
  transition: transform .12s ease, box-shadow .12s ease;
}

a.documento-item.ok:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(11, 40, 79, .08);
}


.documento-item-icono {
  flex-shrink: 0;
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
  border-color: #bfe6cf;
}

.documento-item.ok .documento-item-icono { color: var(--sigta-exito); }


.documento-item.ok .documento-item-accion {
  color: var(--sigta-exito);
  font-weight: 700;
}


.documento-item.falta {
  background: var(--sigta-azul-tenue);
  border-color: var(--sigta-borde-suave);
}

.documento-item.falta .documento-item-icono { color: var(--sigta-texto-tenue); }


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
  margin-top: 16px;
  padding-top: 16px;
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
  margin-top: 15px;
  gap: 12px;
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

.btn-eval-main {
  width: 100%;
  min-height: 50px;
  font-size: 16px;
  letter-spacing: 0.5px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.btn-eval-main:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

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
   MODAL DE ÉXITO — AUTORIZACIÓN DEL DIRECTOR
========================================================= */

.modal-exito-backdrop {
  z-index: 400;
  background: rgba(10, 20, 35, .55);
  backdrop-filter: blur(2px);
}


.modal-exito-director {
  width: min(440px, 100%);
  padding: 34px 38px;
  border-radius: 14px;
  background: var(--sigta-blanco);
  box-shadow: 0 18px 45px rgba(10, 20, 35, .24);
  text-align: center;
}


.modal-exito-icono {
  display: grid;
  width: 74px;
  height: 74px;
  margin: 0 auto 18px;
  place-items: center;
  border-radius: 50%;
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
  font-size: 42px;
  font-weight: 800;
}


.modal-exito-director h2 {
  margin: 0 0 10px;
  color: var(--sigta-azul);
  font-size: 24px;
}


.modal-exito-director p {
  margin: 0 0 24px;
  color: var(--sigta-texto-suave);
  font-size: 15px;
  line-height: 1.5;
}


.modal-exito-boton {
  width: 100%;
  min-height: 46px;
  border: 0;
  border-radius: 8px;
  background: var(--sigta-exito);
  color: var(--sigta-blanco);
  font-family: inherit;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
}


.modal-exito-boton:hover {
  filter: brightness(.92);
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

}

</style>
