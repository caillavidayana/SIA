<template>

  <div class="layout">

    <!-- =====================================================
         MENÚ ÚNICO DEL SOLICITANTE
    ====================================================== -->

    <AdminMenu v-if="route.meta.portalDirector" /><SolicitanteMenu v-else />


    <main class="main">

      <!-- =================================================
           ENCABEZADO
      ================================================== -->

      <header class="topbar">

        <div>

          <h1>
            {{ configuracion.titulo }}
          </h1>

          <p>
            {{ configuracion.descripcion }}
          </p>

        </div>

      
        <UsuarioHeader />
      </header>


      <!-- =================================================
           FORMULARIO
      ================================================== -->

      <section class="form-card">

        <div class="form-columns">

        <div class="col">

        <!-- =================================================
             PASO 1
        ================================================== -->

        <div class="form-section">

          <div class="section-heading">

            <span class="number">
              1
            </span>

            <div>

              <h2>
                Información del problema
              </h2>

              <p>
                Describa claramente la incidencia detectada.
              </p>

            </div>

          </div>


          <div class="grid">

            <!-- TÍTULO -->

            <!-- REQUERIMIENTO 3 (R03): categoría del problema; prioridad en Jefatura. -->
            <div class="field full"><label>Categoría</label><select v-model="form.categoria"><option v-for="c in categorias" :key="c.id" :value="c.id">{{c.nombre}}</option></select></div>
            <div class="field full">

              <label>
                Título del problema
                <span>*</span>
              </label>

              <input
                v-model="form.titulo"
                type="text"
                maxlength="150"
                placeholder="Ej.: Computadora no enciende"
                required
              />

            </div>


            <!-- DESCRIPCIÓN -->

            <div class="field full">

              <label>
                Descripción
                <span>*</span>
              </label>

              <textarea
                v-model="form.descripcion"
                maxlength="1000"
                placeholder="Explique qué sucede, desde cuándo ocurre y cómo afecta su trabajo..."
                required
              ></textarea>

              <small class="counter">
                {{ form.descripcion.length }} / 1000 caracteres
              </small>

            </div>

          </div>

        </div>

        </div>

        <div class="col">

        <!-- =================================================
             PASO 2
        ================================================== -->

        <div class="form-section">

          <div class="section-heading">

            <span class="number">
              2
            </span>

            <div>

              <h2>
                Ubicación y equipo afectado
              </h2>

              <p>
                Indique dónde se encuentra el problema.
              </p>

            </div>

          </div>


          <div class="grid">


            <!-- AULA O AMBIENTE -->

            <div class="field">

              <label>
                Aula o ambiente
                <span>*</span>
              </label>

              <input
                v-model="form.ubicacion"
                type="text"
                maxlength="200"
                placeholder="Ej.: Aula C0-07, Laboratorio de Redes, Biblioteca"
                required
              />

            </div>


            <!-- REFERENCIA -->

            <div class="field">

              <label>
                Referencia
              </label>

              <input
                v-model="form.referencia_ubicacion"
                type="text"
                maxlength="200"
                placeholder="Ej.: Bloque B, segundo piso, frente a la cafetería"
              />

            </div>


            <!-- EQUIPO -->

            <div class="field">

              <label>
                Equipo afectado
                <span>*</span>
              </label>

              <input
                v-model="form.equipo_afectado"
                type="text"
                maxlength="200"
                placeholder="Ej.: PC, proyector, router, aire acondicionado"
                required
              />

            </div>

          </div>

        </div>

        </div>

        </div>


        <!-- =================================================
             PASO 3 - EVIDENCIA (FILA COMPLETA)
        ================================================== -->

        <div class="form-section form-section--full">

          <div class="section-heading">

            <span class="number">
              3
            </span>

            <div>

              <h2>
                Evidencia
              </h2>

              <p>
                Puede cargar una fotografía o documento
                que ayude a identificar el problema.
              </p>

            </div>

          </div>


          <!-- DESCRIPCIÓN EVIDENCIA -->

          <div class="field full">

            <label>
              Descripción de la evidencia
              <span class="optional">
                Opcional
              </span>
            </label>

            <textarea
              v-model="form.evidencia"
              class="evidence-text"
              maxlength="500"
              placeholder="Ej.: El equipo muestra una pantalla azul al encender..."
            ></textarea>

          </div>


          <!-- =================================================
               CARGA DE ARCHIVO
          ================================================== -->

          <div class="upload-container">


            <!-- INPUT OCULTO -->

            <ArchivoInput
              id="evidencia-archivo"
              ref="inputArchivo"
              class="file-input"
              type="file"
              accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
              @change="seleccionarArchivo" />


            <!-- CAJA PARA SELECCIONAR -->

            <label
              v-if="!archivoSeleccionado"
              for="evidencia-archivo"
              class="upload-box"
            >

              <div class="upload-icon">
                ↑
              </div>

              <div class="upload-text">

                <strong>
                  Cargar evidencia
                </strong>

                <small>
                  JPG, JPEG, PNG o PDF · Máximo 5 MB
                </small>

              </div>

            </label>


            <!-- =================================================
                 ARCHIVO SELECCIONADO
            ================================================== -->

            <div
              v-else
              class="selected-file-card"
            >


              <!-- PREVISUALIZACIÓN IMAGEN -->

              <div
                v-if="vistaPrevia"
                class="preview-wrapper"
              >

                <img
                  :src="vistaPrevia"
                  alt="Vista previa de evidencia"
                  class="preview-image"
                />

              </div>


              <!-- PDF -->

              <div
                v-else
                class="pdf-preview"
              >

                <div class="pdf-icon">
                  PDF
                </div>

              </div>


              <!-- DATOS -->

              <div class="file-information">

                <span class="file-label">
                  Archivo seleccionado
                </span>

                <strong>
                  {{ archivoSeleccionado.name }}
                </strong>

                <small>
                  {{
                    formatearTamano(
                      archivoSeleccionado.size
                    )
                  }}
                </small>

              </div>


              <!-- QUITAR -->

              <button
                type="button"
                class="remove-file"
                @click="quitarArchivo"
              >
                Quitar
              </button>

            </div>

          </div>

        </div>


        <!-- =================================================
             PRIORIDAD
        ================================================== -->

        <div class="priority-notice">

          <div class="notice-icon">
            i
          </div>


          <div>

            <strong>
              {{ configuracion.avisoTitulo }}
            </strong>

            <p>
              {{ configuracion.avisoDescripcion }}
            </p>

          </div>

        </div>


        <!-- =================================================
             MENSAJE
        ================================================== -->

        <SistemaNotificacion
          v-if="mensaje"
          :key="mensaje"
          :tipo="esError ? 'error' : 'exito'"
          :titulo="esError ? 'No se pudo registrar la solicitud' : 'Solicitud registrada correctamente'"
          :descripcion="mensaje"
          :duracion="esError ? 0 : 6000"
          @close="mensaje = ''"
        />


        <TarjetaGuardado
          :visible="mostrarGuardadoOk"
          :texto="textoGuardado"
          @cerrar="ocultarGuardado"
        />


        <!-- =================================================
             ACCIONES
        ================================================== -->

        <footer class="actions">

          <button
            type="button"
            class="cancel"
            :disabled="guardando"
            @click="
              router.push(
                route.meta.portalDirector ? '/admin/mis-solicitudes' : '/usuario/dashboard'
              )
            "
          >
            Cancelar
          </button>


          <button
            type="button"
            class="secondary"
            :disabled="guardando"
            @click="limpiarFormulario"
          >
            Limpiar
          </button>


          <button
            type="button"
            class="primary"
            :disabled="guardando"
            @click="crearTicket"
          >

            {{
              guardando
                ? 'Enviando...'
                : 'Enviar solicitud'
            }}

          </button>

        </footer>

      </section>

    </main>

  </div>

</template>


<script setup>
import UsuarioHeader from './UsuarioHeader.vue'
import AdminMenu from '../components/AdminMenu.vue'

import {
  computed,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref
} from 'vue'

import {
  useRoute,
  useRouter
} from 'vue-router'

import SolicitanteMenu
  from '../components/SolicitanteMenu.vue'
import SistemaNotificacion from './SistemaNotificacion.vue'
import TarjetaGuardado from './TarjetaGuardado.vue'

import { usarGuardado }
  from '../utils/guardado.js'

const {
  mostrar: mostrarGuardadoOk,
  texto: textoGuardado,
  animar: animarGuardado,
  ocultar: ocultarGuardado,
} = usarGuardado()

const props = defineProps({
  tipoSolicitud: {
    type: String,
    required: true,
    validator: valor => ['UTIC', 'MANTENIMIENTO'].includes(valor),
  },
})

const esMantenimiento = computed(
  () => props.tipoSolicitud === 'MANTENIMIENTO'
)

const configuracion = computed(() => esMantenimiento.value
  ? {
      titulo: 'Registrar solicitud de mantenimiento',
      descripcion: 'Registre el problema detectado para que Servicios Generales pueda atenderlo.',
      avisoTitulo: 'La prioridad será clasificada por Servicios Generales',
      avisoDescripcion: 'La jefatura revisará la solicitud, clasificará su prioridad y asignará al responsable.',
    }
  : {
      titulo: 'Registrar solicitud de soporte',
      descripcion: 'Registre el problema detectado para que el equipo de UTIC pueda atenderlo.',
      avisoTitulo: 'La prioridad será clasificada por UTIC',
      avisoDescripcion: 'El Jefe de UTIC revisará la solicitud, clasificará su prioridad y asignará al especialista responsable.',
    }
)


/* =========================================================
   ROUTER
========================================================= */

const router =
  useRouter()

const route =
  useRoute()


/* =========================================================
   CATÁLOGOS
========================================================= */

const areas =
  ref([])

const categorias =
  ref([])


/* =========================================================
   ESTADOS
========================================================= */

const mensaje =
  ref('')

const esError =
  ref(false)

const guardando =
  ref(false)


/* =========================================================
   ARCHIVO
========================================================= */

const archivoSeleccionado =
  ref(null)

const inputArchivo =
  ref(null)

const vistaPrevia =
  ref(null)


/* =========================================================
   FORMULARIO
========================================================= */

const form =
  reactive({

    titulo: '',

    descripcion: '',

    area: '',

    categoria: '',
    prioridad: 'MEDIA',

    ubicacion: '',
    referencia_ubicacion: '',

    equipo_afectado: '',

    evidencia: '',
  })


/* =========================================================
   TOKEN
========================================================= */

const token = () =>
  localStorage.getItem(
    'sigta_token'
  )


/* =========================================================
   HEADERS PARA GET
========================================================= */

function headersAuth() {

  return {

    Authorization:
      `Token ${token()}`,

    Accept:
      'application/json',
  }
}


/* =========================================================
   INICIO
========================================================= */

onMounted(
  async () => {

    if (
      !token()
    ) {

      router.push(
        '/login'
      )

      return
    }


    await cargarCatalogos()
  }
)


/* =========================================================
   LIMPIAR URL DE PREVISUALIZACIÓN
========================================================= */

onBeforeUnmount(
  () => {

    liberarVistaPrevia()
  }
)


/* =========================================================
   CARGAR CATÁLOGOS
========================================================= */

async function cargarCatalogos() {

  try {
    const areasRespuesta = await fetch(
      '/api/usuarios/areas/',
      { headers: headersAuth() }
    )

    const categoriasRespuesta = await fetch('/api/soporte/categorias/', { headers: headersAuth() })

    if (
      [401, 403].includes(areasRespuesta.status)
      || [401, 403].includes(categoriasRespuesta?.status)
    ) {

      cerrarSesion()

      return
    }


    if (!areasRespuesta.ok) {

      throw new Error(
        'No fue posible cargar las áreas.'
      )
    }


    if (categoriasRespuesta && !categoriasRespuesta.ok) {

      throw new Error(
        'No fue posible cargar las categorías.'
      )
    }


    const datosAreas = await areasRespuesta.json()
    const datosCategorias = categoriasRespuesta
      ? await categoriasRespuesta.json()
      : []

    areas.value =
      convertirLista(
        datosAreas
      )


    categorias.value =
      convertirLista(
        datosCategorias
      )

    const codigoArea = esMantenimiento.value ? 'MANTENIMIENTO' : 'UTIC'
    form.area = areas.value.find(
      area => String(area.codigo || '').toUpperCase() === codigoArea
    )?.id || areas.value[0]?.id || ''

    form.categoria = categorias.value.find(
      categoria => String(categoria.codigo || '').toUpperCase() === 'OTRO'
    )?.id || categorias.value[0]?.id || ''


  } catch (error) {

    console.error(
      'Error cargando catálogos:',
      error
    )


    mostrarMensaje(
      error.message
      ||
      'No se pudieron cargar los datos.',
      true
    )
  }
}


/* =========================================================
   CONVERTIR LISTA
========================================================= */

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


/* =========================================================
   SELECCIONAR ARCHIVO
========================================================= */

function seleccionarArchivo(
  evento
) {

  mensaje.value = ''

  esError.value = false


  const archivo =
    evento.target.files?.[0]


  if (
    !archivo
  ) {

    return
  }


  /* ===============================================
     TIPOS PERMITIDOS
  ================================================ */

  const tiposPermitidos = [

    'image/jpeg',

    'image/png',

    'application/pdf',
  ]


  if (
    !tiposPermitidos.includes(
      archivo.type
    )
  ) {

    mostrarMensaje(
      'Solo puede adjuntar archivos JPG, JPEG, PNG o PDF.',
      true
    )


    limpiarInputArchivo()

    return
  }


  /* ===============================================
     TAMAÑO MÁXIMO 5 MB
  ================================================ */

  const cincoMB =
    5 * 1024 * 1024


  if (
    archivo.size > cincoMB
  ) {

    mostrarMensaje(
      'El archivo no puede superar los 5 MB.',
      true
    )


    limpiarInputArchivo()

    return
  }


  /* ===============================================
     GUARDAR
  ================================================ */

  archivoSeleccionado.value =
    archivo


  /* ===============================================
     PREVISUALIZACIÓN SI ES IMAGEN
  ================================================ */

  liberarVistaPrevia()


  if (
    archivo.type.startsWith(
      'image/'
    )
  ) {

    vistaPrevia.value =
      URL.createObjectURL(
        archivo
      )
  }
}


/* =========================================================
   QUITAR ARCHIVO
========================================================= */

function quitarArchivo() {

  archivoSeleccionado.value =
    null


  liberarVistaPrevia()


  limpiarInputArchivo()
}


/* =========================================================
   LIMPIAR INPUT
========================================================= */

function limpiarInputArchivo() {

  if (
    inputArchivo.value
  ) {

    inputArchivo.value.value =
      ''
  }
}


/* =========================================================
   LIBERAR PREVIEW
========================================================= */

function liberarVistaPrevia() {

  if (
    vistaPrevia.value
  ) {

    URL.revokeObjectURL(
      vistaPrevia.value
    )


    vistaPrevia.value =
      null
  }
}


/* =========================================================
   FORMATEAR TAMAÑO
========================================================= */

function formatearTamano(
  bytes
) {

  if (
    !bytes
  ) {

    return '0 KB'
  }


  if (
    bytes < 1024
  ) {

    return `${bytes} bytes`
  }


  if (
    bytes < 1024 * 1024
  ) {

    return `${
      (
        bytes / 1024
      ).toFixed(1)
    } KB`
  }


  return `${
    (
      bytes
      /
      1024
      /
      1024
    ).toFixed(2)
  } MB`
}


/* =========================================================
   REGISTRAR SOLICITUD DE SOPORTE
========================================================= */

async function crearTicket() {

  mensaje.value = ''

  esError.value = false


  /* ===============================================
     VALIDACIÓN
  ================================================ */

  if (
    !form.titulo.trim()
    ||
    !form.descripcion.trim()
    ||
    !form.area
    ||
    !form.ubicacion.trim()
    ||
    !form.equipo_afectado.trim()
  ) {

    mostrarMensaje(
      'Complete todos los campos obligatorios.',
      true
    )

    return
  }


  guardando.value =
    true


  try {

    /* ===============================================
       FORMDATA

       IMPORTANTE:
       Ya NO usamos JSON.stringify porque
       ahora enviamos un archivo.
    ================================================ */

    const datosFormulario =
      new FormData()


    datosFormulario.append(
      'titulo',
      form.titulo.trim()
    )


    if (form.categoria) datosFormulario.append('categoria', String(form.categoria))

    datosFormulario.append(
      'descripcion',
      form.descripcion.trim()
    )


    datosFormulario.append(
      'area',
      String(
        form.area
      )
    )


    if (esMantenimiento.value) {
      datosFormulario.append('tipo', 'CORRECTIVO')
    }




    datosFormulario.append('ubicacion', form.ubicacion.trim())

    datosFormulario.append(
      'referencia_ubicacion',
      form.referencia_ubicacion.trim()
    )


    datosFormulario.append(
      'equipo_afectado',
      form.equipo_afectado.trim()
    )


    datosFormulario.append(
      'evidencia',
      form.evidencia.trim()
    )


    /* ===============================================
       ADJUNTO
    ================================================ */

    if (
      archivoSeleccionado.value
    ) {

      datosFormulario.append(
        'evidencia_archivo',
        archivoSeleccionado.value
      )
    }


    /* ===============================================
       PETICIÓN

       NO PONER CONTENT-TYPE.
       El navegador crea multipart/form-data
       automáticamente.
    ================================================ */

    const respuesta =
      await fetch(
        esMantenimiento.value
          ? '/api/mantenimiento/requerimientos/'
          : '/api/soporte/tickets/',
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


    /* ===============================================
       RESPUESTA
    ================================================ */

    let datos = {}


    try {

      datos =
        await respuesta.json()

    } catch {

      datos = {}
    }


    /* ===============================================
       SESIÓN
    ================================================ */

    if (
      respuesta.status === 401
      ||
      respuesta.status === 403
    ) {

      cerrarSesion()

      return
    }


    /* ===============================================
       ERROR
    ================================================ */

    if (
      !respuesta.ok
    ) {

      console.error(
        'Error creando ticket:',
        datos
      )


      mostrarMensaje(
        obtenerError(
          datos
        ),
        true
      )


      return
    }


    /* ===============================================
       ÉXITO
    ================================================ */

    const codigo =
      datos.ticket?.codigo
      || datos.requerimiento?.codigo
      ||
      datos.codigo
      ||
      ''


    window.dispatchEvent(new CustomEvent('sigta:solicitud-creada', {
      detail: { tipo: props.tipoSolicitud, id: datos.ticket?.id || datos.requerimiento?.id }
    }))

    limpiarFormulario(false)

    await animarGuardado(
      codigo
        ? `Solicitud ${codigo} registrada correctamente.`
        : 'Solicitud registrada correctamente.'
    )

    const origen = typeof route.query.origen === 'string'
      && (route.query.origen.startsWith('/usuario/') || (route.meta.portalDirector && ['/admin/dashboard','/admin/mis-solicitudes'].includes(route.query.origen)))
      ? route.query.origen
      : route.meta.portalDirector ? '/admin/mis-solicitudes' : '/usuario/dashboard'
    router.push(origen)


  } catch (error) {

    console.error(
      'Error creando ticket:',
      error
    )


    mostrarMensaje(
      'No fue posible comunicarse con el servidor.',
      true
    )

  } finally {

    guardando.value =
      false
  }
}


/* =========================================================
   ERROR BACKEND
========================================================= */

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


/* =========================================================
   MENSAJE
========================================================= */

function mostrarMensaje(
  texto,
  error = false
) {

  mensaje.value =
    texto


  esError.value =
    error
}


/* =========================================================
   LIMPIAR FORMULARIO
========================================================= */

function limpiarFormulario(limpiarMensaje = true) {

  form.titulo = ''

  form.descripcion = ''

  form.ubicacion = ''

  form.referencia_ubicacion = ''

  form.equipo_afectado = ''

  form.evidencia = ''


  quitarArchivo()


  if (limpiarMensaje) {
    mensaje.value = ''
    esError.value = false
  }
}


/* =========================================================
   CERRAR SESIÓN
========================================================= */

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

  padding:
    16px
    24px
    20px;

  overflow-x: hidden;
}


/* =========================================================
   HEADER
========================================================= */

.topbar {

  max-width: 1180px;

  margin:
    0
    auto
    12px;
}




.topbar h1 {

  margin: 0;

  color: var(--sigta-azul);

  font-size: 23px;
}


.topbar p {

  margin:
    3px
    0
    0;

  color: var(--sigta-texto-suave);

  font-size: 14px;
}


/* =========================================================
   TARJETA FORMULARIO
========================================================= */

.form-card {

  width: 100%;

  max-width: 1180px;

  margin: auto;

  overflow: hidden;

  border-top:
    4px solid var(--sigta-mostaza);

  border-radius: 10px;

  background: var(--sigta-blanco);

  box-shadow:
    0
    4px
    18px
    rgba(0,0,0,.06);
}


.form-columns {

  display: grid;

  grid-template-columns: 1fr 1fr;

  align-items: start;
}


.col {

  display: flex;

  flex-direction: column;
}


.col:first-child {

  border-right:
    1px solid var(--sigta-borde);
}


.form-section {

  padding:
    14px
    20px;
}


.col > .form-section:not(:last-child) {

  border-bottom:
    1px solid var(--sigta-borde);
}


.form-section--full {

  border-top:
    1px solid var(--sigta-borde);
}


/* =========================================================
   TÍTULOS SECCIÓN
========================================================= */

.section-heading {

  display: flex;

  align-items: flex-start;

  gap: 8px;

  margin-bottom: 10px;
}


.number {

  width: 22px;

  height: 22px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 50%;

  background: var(--sigta-azul);

  color: var(--sigta-blanco);

  font-size: 12px;

  font-weight: 800;
}


.section-heading h2 {

  margin: 0;

  color: var(--sigta-azul);

  font-size: 15.5px;
}


.section-heading p {

  margin:
    2px
    0
    0;

  color: var(--sigta-texto-suave);

  font-size: 12px;
}


/* =========================================================
   GRID
========================================================= */

.grid {

  display: grid;

  grid-template-columns:
    1fr
    1fr;

  gap: 10px;
}


/* =========================================================
   CAMPOS
========================================================= */

.field {

  min-width: 0;

  display: flex;

  flex-direction: column;

  gap: 4px;
}


.field.full {

  grid-column:
    1 / -1;
}


.field label {

  color: var(--sigta-azul);

  font-size: 13px;

  font-weight: 700;
}


.field label span {

  color: var(--sigta-error);
}


.field label
.optional {

  margin-left: 4px;

  color: var(--sigta-texto-suave);

  font-size: 11.5px;

  font-weight: 400;
}


.field input,
.field select,
.field textarea {

  width: 100%;

  padding:
    9px
    11px;

  border:
    1px solid var(--sigta-azul-texto-claro);

  border-radius: 6px;

  background: var(--sigta-blanco);

  color: var(--sigta-azul);

  font-family: inherit;

  font-size: 14px;

  outline: none;
}


.field select {

  min-height: 36px;

  cursor: pointer;
}


.field textarea {

  min-height: 88px;

  resize: vertical;

  line-height: 1.45;
}


.field textarea.evidence-text {

  min-height: 40px;
}


.field input:focus,
.field select:focus,
.field textarea:focus {

  border-color: var(--sigta-texto-suave);

  box-shadow:
    0
    0
    0
    3px
    rgba(23,91,150,.09);
}


.field small {

  color: var(--sigta-texto-suave);

  font-size: 11px;
}


.counter {

  align-self: flex-end;
}


/* =========================================================
   UPLOAD
========================================================= */

.upload-container {

  margin-top: 8px;
}


.file-input {

  position: absolute;

  width: 1px;

  height: 1px;

  opacity: 0;

  pointer-events: none;
}


.upload-box {

  min-height: 0;

  display: flex;

  flex-direction: row;

  align-items: center;

  justify-content: flex-start;

  gap: 10px;

  padding: 10px 12px;

  border:
    2px dashed var(--sigta-azul-texto-claro);

  border-radius: 8px;

  background: var(--sigta-azul-tenue);

  cursor: pointer;

  text-align: left;

  transition:
    border-color .2s,
    background .2s;
}


.upload-box:hover {

  border-color: var(--sigta-texto-suave);

  background: var(--sigta-azul-tenue);
}


.upload-icon {

  width: 28px;

  height: 28px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 50%;

  background: var(--sigta-blanco);

  color: var(--sigta-azul);

  font-size: 16px;

  font-weight: 700;
}


.upload-text {

  display: flex;

  flex-direction: column;

  gap: 1px;

  min-width: 0;
}


.upload-box strong {

  color: var(--sigta-azul);

  font-size: 13.5px;
}


.upload-box small {

  color: var(--sigta-texto-suave);

  font-size: 11px;
}


/* =========================================================
   ARCHIVO SELECCIONADO
========================================================= */

.selected-file-card {

  display: flex;

  align-items: center;

  gap: 10px;

  padding: 8px 10px;

  border:
    1px solid var(--sigta-azul-texto-claro);

  border-radius: 8px;

  background: var(--sigta-azul-tenue);
}


.preview-wrapper {

  width: 40px;

  height: 40px;

  flex-shrink: 0;

  overflow: hidden;

  border-radius: 6px;

  background: var(--sigta-azul-texto-claro);
}


.preview-image {

  width: 100%;

  height: 100%;

  object-fit: cover;
}


.pdf-preview {

  width: 40px;

  height: 40px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 6px;

  background: var(--sigta-error-fondo);
}


.pdf-icon {

  color: var(--sigta-error);

  font-size: 12px;

  font-weight: 900;
}


.file-information {

  flex: 1;

  min-width: 0;
}


.file-information
.file-label {

  display: none;
}


.file-information strong {

  display: block;

  overflow: hidden;

  color: var(--sigta-azul);

  font-size: 13.5px;

  text-overflow: ellipsis;

  white-space: nowrap;
}


.file-information small {

  display: block;

  margin-top: 1px;

  color: var(--sigta-texto-suave);

  font-size: 11px;
}


.remove-file {

  flex-shrink: 0;

  padding:
    5px
    9px;

  border: none;

  border-radius: 6px;

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);

  font-size: 12px;

  font-weight: 700;

  cursor: pointer;
}


/* =========================================================
   PRIORIDAD
========================================================= */

.priority-notice {

  margin:
    12px
    20px
    0;

  display: flex;

  align-items: center;

  gap: 9px;

  padding: 8px 12px;

  border-left:
    4px solid var(--sigta-mostaza);

  border-radius: 6px;

  background: var(--sigta-azul-tenue);
}


.notice-icon {

  width: 19px;

  height: 19px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 50%;

  background: var(--sigta-azul);

  color: white;

  font-size: 12px;

  font-weight: 700;
}


.priority-notice strong {

  color: var(--sigta-azul);

  font-size: 13px;
}


.priority-notice p {

  margin:
    1px
    0
    0;

  color: var(--sigta-texto-suave);

  font-size: 12px;

  line-height: 1.3;
}


/* =========================================================
   MENSAJES
========================================================= */

.message {

  margin:
    16px
    26px
    0;

  padding:
    11px
    13px;

  border-radius: 6px;

  font-size: 16px;
}


.message-error {

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);
}


.message-success {

  background: var(--sigta-exito-fondo);

  color: var(--sigta-exito);
}


/* =========================================================
   ACCIONES
========================================================= */

.actions {

  display: flex;

  justify-content: center;

  gap: 9px;

  padding:
    12px
    20px;

  background: var(--sigta-azul-tenue);
}


.actions button {

  min-height: 38px;

  padding:
    0
    18px;

  border-radius: 7px;

  font-size: 14px;

  font-weight: 700;

  cursor: pointer;
}


.actions button:disabled {

  opacity: .6;

  cursor: not-allowed;
}


.cancel {

  border:
    1px solid var(--sigta-borde);

  background: white;

  color: var(--sigta-texto-suave);
}


.secondary {

  border:
    1px solid var(--sigta-azul);

  background: white;

  color: var(--sigta-azul);
}


.primary {

  border: none;

  background: var(--sigta-azul);

  color: white;
}


.primary:hover:not(:disabled) {

  background: var(--sigta-azul);
}


/* =========================================================
   RESPONSIVE
========================================================= */

@media (
  max-width: 980px
) {

  .form-columns {

    grid-template-columns: 1fr;
  }


  .col:first-child {

    border-right: none;

    border-bottom:
      1px solid var(--sigta-borde);
  }

}


@media (
  max-width: 760px
) {

  .layout {

    display: block;
  }


  .main {

    padding: 17px;
  }


  .grid {

    grid-template-columns:
      1fr;
  }


  .field.full {

    grid-column: auto;
  }


  .actions {

    flex-direction:
      column-reverse;
  }


  .actions button {

    width: 100%;
  }


  .selected-file-card {

    align-items:
      flex-start;

    flex-wrap: wrap;
  }


  .file-information {

    min-width:
      calc(100% - 110px);
  }

}

</style>
