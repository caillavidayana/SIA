<template>

  <div class="usuario-layout">

    <SolicitanteMenu />

    <main class="usuario-content">

      <!-- =================================================
           ENCABEZADO
      ================================================== -->

      <header class="topbar">

        <div>

          <h1>
            Bienvenido a SIA
          </h1>

          <p>
            Registre, consulte y dé seguimiento
            a sus requerimientos institucionales.
          </p>

        </div>


        <div class="user-card">

          <div class="user-avatar">
            {{ inicialesUsuario }}
          </div>

          <div>

            <strong>
              {{
                usuario?.nombre
                || usuario?.nombre_completo
                || 'Usuario solicitante'
              }}
            </strong>

            <span>
              {{ usuario?.email || '' }}
            </span>

          </div>

        </div>

      
        <UsuarioHeader @actualizar="cargarTodo" />
      </header>


      <!-- =================================================
           REGISTRAR SOLICITUD
      ================================================== -->

      <section class="portal-card">

        <div class="section-header">

          <div>

            <h2>
              Registrar solicitud
            </h2>

            <p>
              Complete el formulario para reportar
              su problema. El equipo correspondiente
              le dará seguimiento.
            </p>

          </div>

        </div>


        <form
          class="request-form"
          @submit.prevent="enviarSolicitud"
        >

          <div class="categoria-toggle">

            <button
              type="button"
              class="categoria-btn"
              :class="{ activo: form.categoria === 'SOPORTE' }"
              @click="form.categoria = 'SOPORTE'"
            >
              <span class="categoria-icon">🎧</span>
              <span>Soporte Técnico</span>
            </button>

            <button
              type="button"
              class="categoria-btn"
              :class="{ activo: form.categoria === 'MANTENIMIENTO' }"
              @click="form.categoria = 'MANTENIMIENTO'"
            >
              <IconoSigta class="categoria-icon" nombre="mantenimiento" :tamano="22" />
              <span>Mantenimiento</span>
            </button>

          </div>


          <div class="field full">

            <label>
              Título del problema
              <span>*</span>
            </label>

            <input
              v-model="form.titulo"
              type="text"
              maxlength="200"
              placeholder="Ej. La impresora del laboratorio no enciende"
            />

          </div>


          <div class="field full">

            <label>
              Descripción de la falla
              <span>*</span>
            </label>

            <textarea
              v-model="form.descripcion"
              rows="4"
              placeholder="Describa con el mayor detalle posible lo que ocurre..."
            ></textarea>

          </div>


          <div class="field full">

            <label>
              Adjuntar foto
              <span>*</span>
            </label>

            <div
              v-if="!archivoSeleccionado"
              class="file-drop"
              @click="inputArchivo?.click()"
            >
              <span>📷 Seleccionar una foto</span>
            </div>

            <div
              v-else
              class="file-preview"
            >
              <img
                v-if="vistaPrevia"
                :src="vistaPrevia"
                alt="Vista previa"
              />

              <span>{{ archivoSeleccionado.name }}</span>

              <button
                type="button"
                @click="quitarArchivo"
              >
                Quitar
              </button>
            </div>

            <ArchivoInput
              ref="inputArchivo"
              type="file"
              accept="image/jpeg,image/png"
              class="input-oculto"
              @change="seleccionarArchivo" />

          </div>


          <p
            v-if="mensajeForm"
            class="form-mensaje"
            :class="{ error: esErrorForm }"
          >
            {{ mensajeForm }}
          </p>


          <div class="form-actions">

            <button
              type="submit"
              class="btn-enviar"
              :disabled="guardando"
            >
              {{ guardando ? 'Enviando...' : 'Enviar solicitud' }}
            </button>

          </div>

        </form>

      </section>


      <!-- =================================================
           SOLICITUDES RECIENTES
      ================================================== -->

      <section class="recent">

        <div class="recent-header">

          <div>

            <h2>
              Mis requerimientos recientes
            </h2>

            <p>
              Últimos registros de Soporte Técnico,
              Mantenimiento y Compras.
            </p>

          </div>


          <button
            class="view-all"
            @click="
              router.push(
                '/usuario/mis-solicitudes'
              )
            "
          >
            Ver todos
          </button>

        </div>


        <!-- CARGANDO -->

        <div
          v-if="cargando"
          class="empty"
        >
          Cargando requerimientos...
        </div>


        <!-- ERROR -->

        <div
          v-else-if="mensajeError"
          class="error-box"
        >
          {{ mensajeError }}
        </div>


        <!-- SIN SOLICITUDES -->

        <div
          v-else-if="
            recientes.length === 0
          "
          class="empty-state"
        >

          <div class="empty-icon">
            SG
          </div>

          <h3>
            Todavía no tiene requerimientos registrados
          </h3>

          <p>
            Cuando registre una solicitud de soporte,
            un requerimiento de mantenimiento o una
            solicitud de compra, aparecerá aquí para
            que pueda consultar su estado.
          </p>

        </div>


        <!-- LISTA -->

        <div
          v-else
          class="ticket-list"
        >

          <article
            v-for="item in recientes.slice(0, 6)"
            :key="`${item.modulo}-${item.id}`"
          >

            <div class="ticket-main">

              <div class="ticket-code">

                <span
                  class="status-dot"
                  :class="
                    claseEstadoGeneral(
                      item.estado_codigo
                    )
                  "
                ></span>


                <strong>
                  {{
                    item.codigo
                    || `Registro #${item.id}`
                  }}
                </strong>

              </div>


              <h3>
                {{
                  item.titulo
                  || 'Requerimiento institucional'
                }}
              </h3>


              <div class="ticket-meta">

                <span>
                  {{ item.modulo }}
                </span>

                <span
                  v-if="item.area_nombre"
                >
                  {{ item.area_nombre }}
                </span>

                <span
                  v-if="item.ubicacion"
                >
                  {{ item.ubicacion }}
                </span>

              </div>

            </div>


            <div class="ticket-actions">

              <span
                class="estado"
                :class="
                  claseEstadoGeneral(
                    item.estado_codigo
                  )
                "
              >
                {{
                  item.estado_nombre
                  || item.estado_codigo
                  || 'Registrado'
                }}
              </span>


              <button
                @click="
                  router.push(
                    '/usuario/mis-solicitudes'
                  )
                "
              >
                Ver
              </button>

            </div>

          </article>

        </div>

      </section>

    </main>


    <!-- =================================================
         MODAL ÉXITO
    ================================================== -->

    <div
      v-if="mostrarExito"
      class="detalle-modal-backdrop"
      @click.self="mostrarExito = false"
    >

      <div class="detalle-modal exito-modal">

        <div class="exito-icon">
          ✅
        </div>

        <h3>
          Solicitud enviada exitosamente
        </h3>

        <p>
          {{ mensajeExito }}
        </p>

        <button
          class="btn-enviar"
          @click="mostrarExito = false"
        >
          Aceptar
        </button>

      </div>

    </div>

  </div>

</template>


<script setup>
import UsuarioHeader from '../components/UsuarioHeader.vue'
import IconoSigta from '../components/IconoSigta.vue'

import {
  computed,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref
} from 'vue'

import {
  useRouter
} from 'vue-router'

import SolicitanteMenu
  from '../components/SolicitanteMenu.vue'


const router =
  useRouter()


// ==========================================================
// DATOS
// ==========================================================

const usuario =
  ref(null)

const soporte =
  ref([])

const mantenimiento =
  ref([])

const compras =
  ref([])

const cargando =
  ref(true)

const mensajeError =
  ref('')


// ==========================================================
// TOKEN
// ==========================================================

const token = () =>
  localStorage.getItem(
    'sigta_token'
  )


// ==========================================================
// INICIALES
// ==========================================================

const inicialesUsuario =
  computed(() => {

    const nombre =
      usuario.value?.nombre
      ||
      usuario.value?.nombre_completo
      ||
      'Usuario'


    return nombre
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map(
        palabra =>
          palabra
            .charAt(0)
            .toUpperCase()
      )
      .join('')
  })


// ==========================================================
// INICIO
// ==========================================================

onMounted(
  async () => {

    const guardado =
      localStorage.getItem(
        'sigta_usuario'
      )


    if (
      !guardado
      ||
      !token()
    ) {

      router.push(
        '/login'
      )

      return
    }


    try {

      usuario.value =
        JSON.parse(
          guardado
        )

    } catch (error) {

      console.error(
        'Usuario guardado inválido:',
        error
      )


      cerrarSesion()

      return
    }


    await cargarTodo()
  }
)


// ==========================================================
// NORMALIZAR LISTA
// ==========================================================

function convertirLista(
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
// CARGAR TODO
// ==========================================================

async function cargarTodo() {

  cargando.value =
    true

  mensajeError.value =
    ''


  try {

    await Promise.all([
      cargarSoporte(),
      cargarMantenimiento(),
      cargarCompras(),
    ])


  } catch (error) {

    console.error(
      'Error cargando portal:',
      error
    )


    mensajeError.value =
      'No fue posible cargar todos sus requerimientos.'


  } finally {

    cargando.value =
      false
  }
}


// ==========================================================
// FETCH AUXILIAR
// ==========================================================

async function cargarEndpoint(
  url
) {

  const respuesta =
    await fetch(
      url,
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
    ||
    respuesta.status === 403
  ) {

    cerrarSesion()

    throw new Error(
      'Sesión no autorizada.'
    )
  }


  if (
    !respuesta.ok
  ) {

    throw new Error(
      `Error ${respuesta.status}`
    )
  }


  return convertirLista(
    await respuesta.json()
  )
}


// ==========================================================
// SOPORTE
// ==========================================================

async function cargarSoporte() {

  try {

    soporte.value =
      await cargarEndpoint(
        '/api/soporte/tickets/'
      )


  } catch (error) {

    console.error(
      'Error cargando soporte:',
      error
    )

    soporte.value = []
  }
}


// ==========================================================
// MANTENIMIENTO
// ==========================================================

async function cargarMantenimiento() {

  try {

    mantenimiento.value =
      await cargarEndpoint(
        '/api/mantenimiento/requerimientos/'
      )


  } catch (error) {

    console.error(
      'Error cargando mantenimiento:',
      error
    )

    mantenimiento.value = []
  }
}


// ==========================================================
// COMPRAS
// ==========================================================

async function cargarCompras() {

  try {

    compras.value =
      await cargarEndpoint(
        '/api/compras/solicitudes/'
      )


  } catch (error) {

    console.error(
      'Error cargando compras:',
      error
    )

    compras.value = []
  }
}


// ==========================================================
// RECIENTES UNIFICADOS
// ==========================================================

const recientes =
  computed(() => {

    const st =
      soporte.value.map(
        item => ({

          ...item,

          modulo:
            'Soporte Técnico',

          estado_codigo:
            item.estado_codigo
            || item.estado,

          estado_nombre:
            item.estado_nombre
            || item.estado_codigo
            || item.estado,

          fecha_orden:
            item.creado_en
            || item.fecha_creacion
            || item.created_at
            || null,
        })
      )


    const mt =
      mantenimiento.value.map(
        item => ({

          ...item,

          modulo:
            'Mantenimiento',

          estado_codigo:
            item.estado_codigo
            || item.estado,

          estado_nombre:
            item.estado_nombre
            || item.estado_codigo
            || item.estado,

          fecha_orden:
            item.creado_en
            || item.created_at
            || null,
        })
      )


    const cp =
      compras.value.map(
        item => ({

          ...item,

          modulo:
            'Compras',

          titulo:
            item.titulo
            || item.descripcion
            || 'Solicitud de compra',

          estado_codigo:
            item.estado
            || item.estado_codigo,

          estado_nombre:
            item.estado_nombre
            || item.estado
            || 'Registrado',

          fecha_orden:
            item.creado_en
            || item.created_at
            || null,
        })
      )


    return [
      ...st,
      ...mt,
      ...cp
    ]
      .sort(
        (a, b) => {

          const fechaA =
            new Date(
              a.fecha_orden
              || 0
            ).getTime()

          const fechaB =
            new Date(
              b.fecha_orden
              || 0
            ).getTime()


          if (
            fechaA
            &&
            fechaB
          ) {

            return fechaB - fechaA
          }


          return (
            Number(b.id || 0)
            -
            Number(a.id || 0)
          )
        }
      )
  })


// ==========================================================
// ESTILO ESTADO GENERAL
// ==========================================================

function claseEstadoGeneral(
  valor
) {

  const estado =
    String(
      valor
      || ''
    )
      .toUpperCase()
      .replaceAll(' ', '_')


  if (
    estado.includes(
      'ANUL'
    )
    ||
    estado.includes(
      'RECHAZ'
    )
  ) {

    return 'status-cancelled'
  }


  if (
    estado === 'CERRADO'
    ||
    estado === 'RESUELTO'
    ||
    estado === 'FINALIZADO'
  ) {

    return 'status-closed'
  }


  if (
    estado === 'NUEVO'
    ||
    estado === 'RECIBIDO'
  ) {

    return 'status-new'
  }


  if (
    estado.includes('EJEC')
    ||
    estado.includes('ANAL')
    ||
    estado.includes('ASIGN')
    ||
    estado.includes('VERIFIC')
    ||
    estado.includes('DERIV')
    ||
    estado.includes('MANTENIMIENTO')
    ||
    estado.includes('APROB')
    ||
    estado.includes('COTIZ')
    ||
    estado.includes('TRANSITO')
    ||
    estado.includes('ESPERA')
  ) {

    return 'status-process'
  }


  return 'status-default'
}


// ==========================================================
// REGISTRAR SOLICITUD (FORMULARIO SIMPLIFICADO)
// ==========================================================

const form =
  reactive({

    categoria: 'SOPORTE',

    titulo: '',

    descripcion: '',
  })


const archivoSeleccionado =
  ref(null)

const vistaPrevia =
  ref(null)

const inputArchivo =
  ref(null)

const mensajeForm =
  ref('')

const esErrorForm =
  ref(false)

const guardando =
  ref(false)

const mostrarExito =
  ref(false)

const mensajeExito =
  ref('')


const endpointPorCategoria = {

  SOPORTE:
    '/api/soporte/tickets/',

  MANTENIMIENTO:
    '/api/mantenimiento/requerimientos/',
}


function liberarVistaPrevia() {

  if (
    vistaPrevia.value
  ) {

    URL.revokeObjectURL(
      vistaPrevia.value
    )
  }


  vistaPrevia.value =
    null
}


onBeforeUnmount(
  () => {

    liberarVistaPrevia()
  }
)


function seleccionarArchivo(
  evento
) {

  mensajeForm.value = ''

  esErrorForm.value = false


  const archivo =
    evento.target.files?.[0]


  if (
    !archivo
  ) {

    return
  }


  const tiposPermitidos = [

    'image/jpeg',

    'image/png',
  ]


  if (
    !tiposPermitidos.includes(
      archivo.type
    )
  ) {

    mensajeForm.value =
      'Solo puede adjuntar fotos en formato JPG, JPEG o PNG.'

    esErrorForm.value =
      true


    if (
      inputArchivo.value
    ) {

      inputArchivo.value.value = ''
    }


    return
  }


  const cincoMB =
    5 * 1024 * 1024


  if (
    archivo.size > cincoMB
  ) {

    mensajeForm.value =
      'La foto no puede superar los 5 MB.'

    esErrorForm.value =
      true


    if (
      inputArchivo.value
    ) {

      inputArchivo.value.value = ''
    }


    return
  }


  archivoSeleccionado.value =
    archivo


  liberarVistaPrevia()

  vistaPrevia.value =
    URL.createObjectURL(
      archivo
    )
}


function quitarArchivo() {

  archivoSeleccionado.value =
    null


  liberarVistaPrevia()


  if (
    inputArchivo.value
  ) {

    inputArchivo.value.value = ''
  }
}


function obtenerError(
  datos
) {

  if (
    datos.detalle
  ) {

    return datos.detalle
  }


  if (
    datos.detail
  ) {

    return datos.detail
  }


  const errores =
    Object.entries(
      datos
    )
      .map(
        ([campo, valor]) => {

          const texto =
            Array.isArray(valor)
              ? valor.join(', ')
              : String(valor)


          return (
            `${campo}: ${texto}`
          )
        }
      )
      .join(' | ')


  return (
    errores
    ||
    'Revise la información ingresada.'
  )
}


async function enviarSolicitud() {

  mensajeForm.value = ''

  esErrorForm.value = false


  if (
    !form.titulo.trim()
    ||
    !form.descripcion.trim()
  ) {

    mensajeForm.value =
      'Complete el título y la descripción del problema.'

    esErrorForm.value =
      true

    return
  }


  if (
    !archivoSeleccionado.value
  ) {

    mensajeForm.value =
      'Debe adjuntar una foto del problema.'

    esErrorForm.value =
      true

    return
  }


  guardando.value =
    true


  try {

    const datosFormulario =
      new FormData()


    datosFormulario.append(
      'titulo',
      form.titulo.trim()
    )


    datosFormulario.append(
      'descripcion',
      form.descripcion.trim()
    )


    if (
      archivoSeleccionado.value
    ) {

      datosFormulario.append(
        'evidencia_archivo',
        archivoSeleccionado.value
      )
    }


    const respuesta =
      await fetch(
        endpointPorCategoria[form.categoria],
        {

          method:
            'POST',

          headers: {

            Authorization:
              `Token ${token()}`,

            Accept:
              'application/json',
          },

          body:
            datosFormulario,
        }
      )


    let datos = {}

    try {

      datos =
        await respuesta.json()

    } catch {

      datos = {}
    }


    if (
      respuesta.status === 401
      ||
      respuesta.status === 403
    ) {

      cerrarSesion()

      return
    }


    if (
      !respuesta.ok
    ) {

      console.error(
        'Error registrando solicitud:',
        datos
      )


      mensajeForm.value =
        obtenerError(
          datos
        )

      esErrorForm.value =
        true

      return
    }


    const codigo =
      datos.ticket?.codigo
      ||
      datos.requerimiento?.codigo
      ||
      ''


    mensajeExito.value =
      codigo

        ? `Su solicitud ${codigo} fue registrada correctamente.`

        : 'Su solicitud fue registrada correctamente.'

    mostrarExito.value =
      true


    form.titulo = ''

    form.descripcion = ''

    quitarArchivo()


    await cargarTodo()


  } catch (error) {

    console.error(
      'Error registrando solicitud:',
      error
    )


    mensajeForm.value =
      'No fue posible registrar la solicitud. Intente nuevamente.'

    esErrorForm.value =
      true


  } finally {

    guardando.value =
      false
  }
}


// ==========================================================
// CERRAR SESIÓN
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

.usuario-layout {

  min-height: 100vh;

  display: flex;

  background: var(--sigta-azul-tenue);

  font-family: var(--sigta-fuente);
}


.usuario-content {

  flex: 1;

  min-width: 0;

  padding:
    28px
    30px;

  overflow-x: hidden;

  background-image:
    url('/img/marca-de-agua-body.png');

  background-repeat:
    no-repeat;

  background-position:
    top center;

  background-size:
    620px auto;

  background-attachment:
    fixed;
}


/* =========================================================
   TOPBAR
========================================================= */

.topbar {

  display: flex;

  justify-content:
    space-between;

  align-items: center;

  gap: 20px;

  margin-bottom: 22px;
}




.topbar h1 {

  margin: 0;

  color: var(--sigta-texto);

  font-size: 36px;
}


.topbar p {

  margin:
    5px
    0
    0;

  color: var(--sigta-texto);

  font-size: 17px;
}


/* =========================================================
   USUARIO
========================================================= */

.user-card {

  min-width: 190px;

  display: flex;

  align-items: center;

  justify-content:
    flex-end;

  gap: 9px;

  padding:
    10px
    13px;

  border-radius: 8px;

  background: white;

  box-shadow:
    0
    3px
    10px
    rgba(0,0,0,.06);
}


.user-avatar {

  width: 34px;

  height: 34px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 50%;

  background: var(--sigta-mostaza);

  color: var(--sigta-azul);

  font-size: 17px;

  font-weight: 900;
}


.user-card strong,
.user-card span {

  display: block;
}


.user-card strong {

  color: var(--sigta-texto);

  font-size: 19px;
}


.user-card span {

  margin-top: 2px;

  color: var(--sigta-texto);

  font-size: 16px;
}


/* =========================================================
   PANEL PRINCIPAL
========================================================= */

.portal-card {

  margin-bottom: 20px;

  padding: 21px;

  border-radius: 10px;

  background: var(--sigta-blanco);

  box-shadow:
    0
    4px
    14px
    rgba(0,0,0,.05);
}


.section-header h2 {

  margin: 0;

  color: var(--sigta-texto);

  font-size: 24px;
}


.section-header p {

  margin:
    4px
    0
    17px;

  color: var(--sigta-texto);

  font-size: 17px;
}


/* =========================================================
   FORMULARIO DE REGISTRO
========================================================= */

.request-form {

  display: flex;

  flex-direction: column;

  gap: 16px;
}


.categoria-toggle {

  display: flex;

  gap: 12px;
}


.categoria-btn {

  flex: 1;

  display: flex;

  align-items: center;

  justify-content: center;

  gap: 10px;

  min-height: 56px;

  border:
    2px solid var(--sigta-borde);

  border-radius: 9px;

  background: var(--sigta-azul-tenue);

  color: var(--sigta-texto);

  font-size: 18px;

  font-weight: 700;

  cursor: pointer;

  transition:
    border-color .15s,
    background .15s,
    color .15s;
}


.categoria-btn:hover {

  border-color: var(--sigta-azul);
}


.categoria-btn.activo {

  border-color: var(--sigta-azul);

  background: var(--sigta-azul-tenue);

  color: var(--sigta-azul);
}


.categoria-icon {

  font-size: 22px;
}


.field {

  display: flex;

  flex-direction: column;

  gap: 6px;
}


.field label {

  color: var(--sigta-texto);

  font-size: 17px;

  font-weight: 700;
}


.field label span {

  color: var(--sigta-error);
}


.field input[type="text"],
.field textarea {

  padding:
    14px
    15px;

  border:
    1px solid var(--sigta-borde);

  border-radius: 8px;

  background: white;

  color: var(--sigta-texto);

  font-family: inherit;

  font-size: 17px;
}


.field textarea {

  resize: vertical;
}


.field input[type="text"]:focus,
.field textarea:focus {

  outline: none;

  border-color: var(--sigta-azul);
}


.input-oculto {

  display: none;
}


.file-drop {

  display: flex;

  align-items: center;

  justify-content: center;

  min-height: 56px;

  border:
    2px dashed var(--sigta-borde);

  border-radius: 8px;

  background: var(--sigta-azul-tenue);

  color: var(--sigta-texto);

  font-size: 16px;

  cursor: pointer;

  transition:
    border-color .15s;
}


.file-drop:hover {

  border-color: var(--sigta-azul);
}


.file-preview {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 10px;

  border:
    1px solid var(--sigta-borde);

  border-radius: 8px;

  background: var(--sigta-azul-tenue);
}


.file-preview img {

  width: 48px;

  height: 48px;

  border-radius: 6px;

  object-fit: cover;
}


.file-preview span {

  flex: 1;

  min-width: 0;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

  color: var(--sigta-texto);

  font-size: 15px;
}


.file-preview button {

  padding:
    7px
    12px;

  border: none;

  border-radius: 6px;

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);

  font-size: 15px;

  font-weight: 700;

  cursor: pointer;
}


.form-mensaje {

  margin: 0;

  padding:
    10px
    14px;

  border-radius: 7px;

  background: var(--sigta-exito-fondo);

  color: var(--sigta-exito);

  font-size: 16px;
}


.form-mensaje.error {

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);
}


.form-actions {

  display: flex;

  justify-content: flex-end;
}


.btn-enviar {

  min-height: 50px;

  padding:
    0
    26px;

  border: none;

  border-radius: 8px;

  background: var(--sigta-azul);

  color: white;

  font-size: 17px;

  font-weight: 800;

  cursor: pointer;

  transition:
    opacity .15s;
}


.btn-enviar:disabled {

  opacity: .6;

  cursor: default;
}


/* =========================================================
   MODAL ÉXITO
========================================================= */

.exito-modal {

  max-width: 420px;

  padding:
    36px
    30px;

  text-align: center;
}


.exito-icon {

  font-size: 48px;

  margin-bottom: 12px;
}


.exito-modal h3 {

  margin: 0;

  color: var(--sigta-texto);

  font-size: 22px;
}


.exito-modal p {

  margin:
    10px
    0
    22px;

  color: var(--sigta-texto);

  font-size: 16px;

  line-height: 1.5;
}


.exito-modal .btn-enviar {

  width: 100%;
}


/* =========================================================
   RECIENTES
========================================================= */

.recent {

  padding: 21px;

  border-radius: 10px;

  background: white;

  box-shadow:
    0
    4px
    14px
    rgba(0,0,0,.05);
}


.recent-header {

  display: flex;

  align-items: center;

  justify-content:
    space-between;

  gap: 15px;

  margin-bottom: 12px;

  padding: 16px 18px;

  border-radius: 9px;

  background: var(--sigta-azul-texto-claro);
}


.recent-header h2 {

  margin: 0;

  color: var(--sigta-texto);

  font-size: 24px;
}


.recent-header p {

  margin:
    4px
    0
    0;

  color: var(--sigta-texto);

  font-size: 17px;
}


.view-all {

  min-height: 34px;

  padding:
    0
    11px;

  border:
    1px solid var(--sigta-borde);

  border-radius: 6px;

  background: white;

  color: var(--sigta-azul);

  font-size: 17px;

  font-weight: 700;

  cursor: pointer;
}


/* =========================================================
   LISTA RECIENTE
========================================================= */

.ticket-list {

  display: flex;

  flex-direction: column;
}


.ticket-list article {

  display: flex;

  align-items: center;

  justify-content:
    space-between;

  gap: 15px;

  padding:
    13px
    4px;

  border-top:
    1px solid var(--sigta-azul-tenue);
}


.ticket-main {

  min-width: 0;

  flex: 1;
}


.ticket-code {

  display: flex;

  align-items: center;

  gap: 6px;
}


.ticket-list strong {

  color: var(--sigta-azul);

  font-size: 17px;
}


.ticket-list h3 {

  margin:
    5px
    0;

  color: var(--sigta-texto);

  font-size: 20px;
}


.ticket-meta {

  display: flex;

  flex-wrap: wrap;

  gap: 6px;
}


.ticket-meta span {

  padding:
    4px
    6px;

  border-radius: 4px;

  background: var(--sigta-azul-tenue);

  color: var(--sigta-texto);

  font-size: 15px;
}


.ticket-actions {

  flex-shrink: 0;

  display: flex;

  align-items: center;

  gap: 8px;
}


.ticket-actions button {

  padding:
    6px
    9px;

  border: none;

  border-radius: 5px;

  background: var(--sigta-azul-tenue);

  color: var(--sigta-azul);

  font-size: 16px;

  font-weight: 700;

  cursor: pointer;
}


/* =========================================================
   ESTADOS
========================================================= */

.estado {

  padding:
    5px
    8px;

  border-radius: 20px;

  font-size: 16px;

  font-weight: 700;
}


.status-dot {

  width: 7px;

  height: 7px;

  flex-shrink: 0;

  border-radius: 50%;
}


.estado.status-new,
.status-dot.status-new {

  background: var(--sigta-azul-tenue);

  color: var(--sigta-azul);
}


.status-dot.status-new {

  background: var(--sigta-texto-suave);
}


.estado.status-process {

  background: var(--sigta-mostaza-suave);

  color: var(--sigta-mostaza-oscuro);
}


.status-dot.status-process {

  background: var(--sigta-mostaza);
}


.estado.status-closed {

  background: var(--sigta-exito-fondo);

  color: var(--sigta-exito);
}


.status-dot.status-closed {

  background: var(--sigta-exito);
}


.estado.status-cancelled {

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);
}


.status-dot.status-cancelled {

  background: var(--sigta-error);
}


.estado.status-default {

  background: var(--sigta-azul-tenue);

  color: var(--sigta-texto-suave);
}


.status-dot.status-default {

  background: var(--sigta-texto-suave);
}


/* =========================================================
   ESTADO VACÍO
========================================================= */

.empty {

  padding: 30px;

  text-align: center;

  color: var(--sigta-texto);

  font-size: 18px;
}


.empty-state {

  padding:
    35px
    20px;

  text-align: center;
}


.empty-icon {

  width: 42px;

  height: 42px;

  margin:
    0
    auto
    10px;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 50%;

  background: var(--sigta-azul-tenue);

  color: var(--sigta-azul);

  font-size: 17px;

  font-weight: 900;
}


.empty-state h3 {

  margin: 0;

  color: var(--sigta-texto);

  font-size: 21px;
}


.empty-state p {

  max-width: 470px;

  margin:
    7px
    auto
    14px;

  color: var(--sigta-texto);

  font-size: 17px;

  line-height: 1.5;
}


/* =========================================================
   ERROR
========================================================= */

.error-box {

  padding: 14px;

  border-radius: 7px;

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);

  font-size: 18px;
}


/* =========================================================
   RESPONSIVE
========================================================= */

@media (
  max-width: 760px
) {

  .usuario-layout {

    display: block;
  }


  .usuario-content {

    padding: 18px;
  }


  .topbar {

    align-items:
      flex-start;

    flex-direction:
      column;
  }


  .user-card {

    justify-content:
      flex-start;
  }


  .recent-header {

    align-items:
      flex-start;
  }


  .ticket-list article {

    align-items:
      flex-start;

    flex-direction:
      column;
  }


  .ticket-actions {

    width: 100%;

    justify-content:
      space-between;
  }


  .categoria-toggle {

    flex-direction: column;
  }

}



</style>
