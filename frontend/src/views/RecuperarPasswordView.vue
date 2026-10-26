<template>
  <main class="recovery-page">

    <section class="recovery-card">

      <!-- =========================
           IDENTIDAD SIGTA
      ========================== -->
      <div class="brand">

        <div class="logo">
          <img src="/img/emi.jpg" alt="EMI" class="logo-img">
        </div>

        <div class="brand-text">
          <h1>SIA</h1>

          <strong>
            Escuela Militar de Ingeniería
          </strong>

          <span>
            Unidad Académica Santa Cruz
          </span>
        </div>

      </div>

      <div class="yellow-line"></div>


      <!-- =========================
           INDICADOR DE PASOS
      ========================== -->
      <div
        v-if="paso < 4"
        class="steps"
      >

        <div
          :class="[
            'step',
            paso >= 1 ? 'active' : ''
          ]"
        >
          <div class="circle">
            1
          </div>

          <span>
            Correo
          </span>
        </div>


        <div
          :class="[
            'line',
            paso >= 2 ? 'active-line' : ''
          ]"
        ></div>


        <div
          :class="[
            'step',
            paso >= 2 ? 'active' : ''
          ]"
        >
          <div class="circle">
            2
          </div>

          <span>
            Código
          </span>
        </div>


        <div
          :class="[
            'line',
            paso >= 3 ? 'active-line' : ''
          ]"
        ></div>


        <div
          :class="[
            'step',
            paso >= 3 ? 'active' : ''
          ]"
        >
          <div class="circle">
            3
          </div>

          <span>
            Contraseña
          </span>
        </div>

      </div>


      <!-- =================================================
           PASO 1 - INGRESAR CORREO
      ================================================== -->
      <section
        v-if="paso === 1"
        class="content"
      >

        <div class="icon-box">
          @
        </div>

        <h2>
          Recuperar contraseña
        </h2>

        <p class="description">
          Ingrese su correo institucional registrado en SIA.
          Le enviaremos un código de verificación para continuar.
        </p>


        <form @submit.prevent="solicitarCodigo">

          <div class="form-group">

            <label for="correo">
              Correo institucional
            </label>

            <input
              id="correo"
              v-model="email"
              type="email"
              placeholder="usuario@emi.edu.bo"
              autocomplete="email"
              required
              :disabled="cargando"
            />

          </div>


          <div
            v-if="mensaje"
            :class="[
              'message',
              esError ? 'error' : 'success'
            ]"
          >
            {{ mensaje }}
          </div>


          <button
            type="submit"
            class="primary-button"
            :disabled="cargando"
          >
            {{
              cargando
                ? 'Enviando código...'
                : 'Enviar código de verificación'
            }}
          </button>

        </form>


        <button
          type="button"
          class="back-button"
          @click="volverLogin"
        >
          ← Volver a iniciar sesión
        </button>

      </section>


      <!-- =================================================
           PASO 2 - VERIFICAR CÓDIGO
      ================================================== -->
      <section
        v-if="paso === 2"
        class="content"
      >

        <div class="icon-box">
          #
        </div>

        <h2>
          Código enviado
        </h2>

        <p class="description">
          Ingrese el código de 6 dígitos enviado a
          <strong>{{ email }}</strong>.
          El código tiene una vigencia de 10 minutos.
        </p>


        <form @submit.prevent="verificarCodigo">

          <label class="code-title">
            Código de verificación
          </label>


          <div class="code-container">

            <input
              v-for="(numero, index) in codigo"
              :key="index"
              :ref="el => guardarReferencia(el, index)"
              v-model="codigo[index]"
              class="code-input"
              type="text"
              inputmode="numeric"
              maxlength="1"
              :disabled="cargando"
              @input="siguienteCampo(index)"
              @keydown.backspace="campoAnterior(index)"
              @paste="pegarCodigo"
            />

          </div>


          <div
            v-if="mensaje"
            :class="[
              'message',
              esError ? 'error' : 'success'
            ]"
          >
            {{ mensaje }}
          </div>


          <button
            type="submit"
            class="primary-button"
            :disabled="cargando"
          >
            {{
              cargando
                ? 'Verificando...'
                : 'Verificar código'
            }}
          </button>

        </form>


        <div class="resend">

          <span>
            ¿No recibió el código?
          </span>

          <button
            type="button"
            @click="reenviarCodigo"
            :disabled="cargando"
          >
            Reenviar código
          </button>

        </div>


        <button
          type="button"
          class="back-button"
          @click="volverCorreo"
        >
          ← Cambiar correo
        </button>

      </section>


      <!-- =================================================
           PASO 3 - NUEVA CONTRASEÑA
      ================================================== -->
      <section
        v-if="paso === 3"
        class="content"
      >

        <div class="icon-box verified">
          ✓
        </div>

        <h2>
          Crear nueva contraseña
        </h2>

        <p class="description">
          Su identidad fue verificada correctamente.
          Cree una nueva contraseña segura para su cuenta.
        </p>


        <form @submit.prevent="cambiarPassword">

          <!-- NUEVA CONTRASEÑA -->
          <div class="form-group">

            <label>
              Nueva contraseña
            </label>

            <div class="password-wrapper">

              <input
                v-model="nuevaPassword"
                :type="
                  mostrarNueva
                    ? 'text'
                    : 'password'
                "
                placeholder="Ingrese la nueva contraseña"
                autocomplete="new-password"
                required
                :disabled="cargando"
              />

              <button
                type="button"
                @click="mostrarNueva = !mostrarNueva"
              >
                {{
                  mostrarNueva
                    ? 'Ocultar'
                    : 'Ver'
                }}
              </button>

            </div>

          </div>


          <!-- CONFIRMAR -->
          <div class="form-group">

            <label>
              Confirmar nueva contraseña
            </label>

            <div class="password-wrapper">

              <input
                v-model="confirmarPassword"
                :type="
                  mostrarConfirmacion
                    ? 'text'
                    : 'password'
                "
                placeholder="Repita la nueva contraseña"
                autocomplete="new-password"
                required
                :disabled="cargando"
              />

              <button
                type="button"
                @click="
                  mostrarConfirmacion =
                    !mostrarConfirmacion
                "
              >
                {{
                  mostrarConfirmacion
                    ? 'Ocultar'
                    : 'Ver'
                }}
              </button>

            </div>

          </div>


          <!-- REQUISITOS -->
          <div class="requirements">

            <strong>
              La contraseña debe contener:
            </strong>

            <div class="requirement-grid">

              <span
                :class="
                  reglaLongitud
                    ? 'valid'
                    : ''
                "
              >
                ✓ Mínimo {{ minimo ?? "…" }} caracteres
              </span>

              <span
                :class="
                  reglaMayuscula
                    ? 'valid'
                    : ''
                "
              >
                ✓ Una letra mayúscula
              </span>

              <span
                :class="
                  reglaMinuscula
                    ? 'valid'
                    : ''
                "
              >
                ✓ Una letra minúscula
              </span>

              <span
                :class="
                  reglaNumero
                    ? 'valid'
                    : ''
                "
              >
                ✓ Un número
              </span>

              <span
                :class="
                  reglaEspecial
                    ? 'valid'
                    : ''
                "
              >
                ✓ Un carácter especial
              </span>

              <span
                :class="
                  contrasenasCoinciden
                    ? 'valid'
                    : ''
                "
              >
                ✓ Ambas contraseñas coinciden
              </span>

            </div>

          </div>


          <div
            v-if="mensaje"
            :class="[
              'message',
              esError ? 'error' : 'success'
            ]"
          >
            {{ mensaje }}
          </div>


          <button
            type="submit"
            class="primary-button"
            :disabled="
              cargando ||
              !passwordValida
            "
          >
            {{
              cargando
                ? 'Actualizando contraseña...'
                : 'Guardar nueva contraseña'
            }}
          </button>

        </form>

      </section>


      <!-- =================================================
           PASO 4 - FINALIZADO
      ================================================== -->
      <section
        v-if="paso === 4"
        class="content final-content"
      >

        <div class="success-circle">
          ✓
        </div>


        <h2>
          Contraseña actualizada
        </h2>


        <p class="description">
          Su contraseña fue modificada correctamente.
          Ya puede utilizarla para iniciar sesión en SIA.
        </p>


        <div class="final-message">

          <strong>
            Recuperación completada
          </strong>

          <span>
            Por seguridad, deberá iniciar sesión nuevamente
            con su nueva contraseña.
          </span>

        </div>


        <button
          type="button"
          class="primary-button"
          @click="volverLogin"
        >
          Ir a iniciar sesión
        </button>

      </section>


      <!-- =========================
           FOOTER
      ========================== -->
      <footer>

        <p>
          Sistema Integrado de Atención
        </p>

        <strong>
          SIA · EMI Santa Cruz
        </strong>

      </footer>

    </section>

  </main>
</template>


<script setup>
import {usarPoliticaPassword} from '../utils/politicaPassword'
const {minimo,errorPolitica}=usarPoliticaPassword()

import {
  computed,
  nextTick,
  ref
} from 'vue'

import {
  useRouter
} from 'vue-router'


const router = useRouter()


/* =====================================
   ESTADO GENERAL
===================================== */

const paso = ref(1)

const cargando = ref(false)

const mensaje = ref('')

const esError = ref(false)


/* =====================================
   PASO 1
===================================== */

const email = ref('')


/* =====================================
   PASO 2
===================================== */

const codigo = ref([
  '',
  '',
  '',
  '',
  '',
  ''
])

const referenciasCodigo = []


/* =====================================
   PASO 3
===================================== */

const nuevaPassword = ref('')

const confirmarPassword = ref('')

const mostrarNueva = ref(false)

const mostrarConfirmacion = ref(false)


/* =====================================
   VALIDACIÓN DE CONTRASEÑA
===================================== */

const reglaLongitud = computed(() => {
  return minimo.value !== null && nuevaPassword.value.length >= minimo.value
})


const reglaMayuscula = computed(() => {
  return /[A-Z]/.test(
    nuevaPassword.value
  )
})


const reglaMinuscula = computed(() => {
  return /[a-z]/.test(
    nuevaPassword.value
  )
})


const reglaNumero = computed(() => {
  return /\d/.test(
    nuevaPassword.value
  )
})


const reglaEspecial = computed(() => {
  return /[^\w\s]/.test(
    nuevaPassword.value
  )
})


const contrasenasCoinciden =
  computed(() => {

    return (
      nuevaPassword.value.length > 0
      &&
      nuevaPassword.value
        === confirmarPassword.value
    )
  })


const passwordValida =
  computed(() => {

    return (
      reglaLongitud.value
      &&
      reglaMayuscula.value
      &&
      reglaMinuscula.value
      &&
      reglaNumero.value
      &&
      reglaEspecial.value
      &&
      contrasenasCoinciden.value
    )
  })


/* =====================================
   PASO 1 - SOLICITAR CÓDIGO
===================================== */

async function solicitarCodigo() {

  limpiarMensaje()


  if (!email.value.trim()) {

    mostrarError(
      'Ingrese su correo institucional.'
    )

    return
  }


  cargando.value = true


  try {

    const respuesta =
      await fetch(
        '/api/recuperacion/solicitar/',
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json'
          },

          body: JSON.stringify({
            email:
              email.value
                .trim()
                .toLowerCase()
          })
        }
      )


    const datos =
      await respuesta.json()


    if (!respuesta.ok) {

      mostrarError(
        datos.mensaje ||
        'No fue posible enviar el código.'
      )

      return
    }


    mensaje.value =
      datos.mensaje ||
      'Código enviado correctamente.'

    esError.value = false


    setTimeout(() => {

      mensaje.value = ''

      paso.value = 2


      nextTick(() => {
        referenciasCodigo[0]?.focus()
      })

    }, 700)


  } catch (error) {

    console.error(
      'Error recuperación:',
      error
    )


    mostrarError(
      'No fue posible comunicarse con el servidor.'
    )

  } finally {

    cargando.value = false
  }
}


/* =====================================
   PASO 2 - VERIFICAR
===================================== */

async function verificarCodigo() {

  limpiarMensaje()


  const codigoCompleto =
    codigo.value.join('')


  if (
    codigoCompleto.length !== 6
  ) {

    mostrarError(
      'Debe ingresar los 6 dígitos del código.'
    )

    return
  }


  cargando.value = true


  try {

    const respuesta =
      await fetch(
        '/api/recuperacion/verificar/',
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json'
          },

          body: JSON.stringify({

            email:
              email.value
                .trim()
                .toLowerCase(),

            codigo:
              codigoCompleto

          })
        }
      )


    const datos =
      await respuesta.json()


    if (!respuesta.ok) {

      mostrarError(
        datos.mensaje ||
        'El código ingresado no es válido.'
      )

      return
    }


    mensaje.value =
      'Código verificado correctamente.'

    esError.value = false


    setTimeout(() => {

      mensaje.value = ''

      paso.value = 3

    }, 600)


  } catch (error) {

    console.error(
      'Error verificar:',
      error
    )


    mostrarError(
      'No fue posible verificar el código.'
    )

  } finally {

    cargando.value = false
  }
}


/* =====================================
   PASO 3 - CAMBIAR CONTRASEÑA
===================================== */

async function cambiarPassword() {

  limpiarMensaje()


  if (!passwordValida.value) {

    mostrarError(
      'Revise los requisitos de la nueva contraseña.'
    )

    return
  }


  cargando.value = true


  try {

    const respuesta =
      await fetch(
        '/api/recuperacion/restablecer/',
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json'
          },

          body: JSON.stringify({

            email:
              email.value
                .trim()
                .toLowerCase(),

            nueva_password:
              nuevaPassword.value,

            confirmar_password:
              confirmarPassword.value

          })
        }
      )


    const datos =
      await respuesta.json()


    if (!respuesta.ok) {

      mostrarError(
        datos.mensaje ||
        'No fue posible cambiar la contraseña.'
      )

      return
    }


    paso.value = 4


  } catch (error) {

    console.error(
      'Error cambio password:',
      error
    )


    mostrarError(
      'No fue posible actualizar la contraseña.'
    )

  } finally {

    cargando.value = false
  }
}


/* =====================================
   MANEJO DE CÓDIGO
===================================== */

function guardarReferencia(
  elemento,
  index
) {

  if (elemento) {
    referenciasCodigo[index] =
      elemento
  }
}


function siguienteCampo(index) {

  codigo.value[index] =
    codigo.value[index]
      .replace(/\D/g, '')
      .slice(0, 1)


  if (
    codigo.value[index]
    &&
    index < 5
  ) {

    referenciasCodigo[
      index + 1
    ]?.focus()
  }
}


function campoAnterior(index) {

  if (
    !codigo.value[index]
    &&
    index > 0
  ) {

    referenciasCodigo[
      index - 1
    ]?.focus()
  }
}


function pegarCodigo(event) {

  event.preventDefault()


  const texto =
    event.clipboardData
      .getData('text')
      .replace(/\D/g, '')
      .slice(0, 6)


  if (!texto) {
    return
  }


  codigo.value =
    Array.from(
      { length: 6 },
      (_, index) =>
        texto[index] || ''
    )


  const ultimo =
    Math.min(
      texto.length,
      6
    ) - 1


  nextTick(() => {

    referenciasCodigo[
      Math.max(ultimo, 0)
    ]?.focus()

  })
}


/* =====================================
   REENVIAR
===================================== */

async function reenviarCodigo() {

  codigo.value = [
    '',
    '',
    '',
    '',
    '',
    ''
  ]


  limpiarMensaje()

  cargando.value = true


  try {

    const respuesta =
      await fetch(
        '/api/recuperacion/solicitar/',
        {

          method: 'POST',

          headers: {
            'Content-Type':
              'application/json'
          },

          body: JSON.stringify({
            email:
              email.value
                .trim()
                .toLowerCase()
          })

        }
      )


    const datos =
      await respuesta.json()


    if (!respuesta.ok) {

      mostrarError(
        datos.mensaje ||
        'No fue posible reenviar el código.'
      )

      return
    }


    mensaje.value =
      'Se envió un nuevo código.'

    esError.value = false


    nextTick(() => {
      referenciasCodigo[0]?.focus()
    })


  } catch (error) {

    console.error(error)

    mostrarError(
      'No fue posible reenviar el código.'
    )

  } finally {

    cargando.value = false
  }
}


/* =====================================
   NAVEGACIÓN
===================================== */

function volverCorreo() {

  paso.value = 1

  codigo.value = [
    '',
    '',
    '',
    '',
    '',
    ''
  ]

  limpiarMensaje()
}


function volverLogin() {

  router.push('/login')
}


/* =====================================
   MENSAJES
===================================== */

function limpiarMensaje() {

  mensaje.value = ''

  esError.value = false
}


function mostrarError(texto) {

  mensaje.value = texto

  esError.value = true
}

</script>


<style scoped>

/* =====================================
   GENERAL
===================================== */

* {
  box-sizing: border-box;
}


.recovery-page {

  min-height: 100vh;

  width: 100%;

  display: flex;

  align-items: center;

  justify-content: center;

  padding: 20px;

  background:
    linear-gradient(
      135deg,
      var(--sigta-azul) 0%,
      var(--sigta-azul) 55%,
      var(--sigta-texto-suave) 100%
    );

  font-family: var(--sigta-fuente);
}


/* =====================================
   TARJETA
===================================== */

.recovery-card {

  width: 100%;

  max-width: 540px;

  overflow: hidden;

  background: var(--sigta-blanco);

  border-radius: 17px;

  border-top:
    4px solid var(--sigta-mostaza);

  box-shadow:
    0 24px 65px
    rgba(0, 0, 0, .25);
}


/* =====================================
   IDENTIDAD
===================================== */

.brand {

  display: flex;

  align-items: center;

  gap: 15px;

  padding:
    25px
    34px
    17px;
}


.logo {

  width: 62px;

  height: 62px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content: center;

  background: var(--sigta-azul);

  border:
    3px solid var(--sigta-mostaza);

  border-radius: 13px;

  overflow: hidden;
}

.logo-img {

  width: 100%;

  height: 100%;

  object-fit: contain;
}


.brand-text h1 {

  margin: 0;

  color: var(--sigta-azul);

  font-size: 29px;

  line-height: 1;

  letter-spacing: 2px;
}


.brand-text strong {

  display: block;

  margin-top: 5px;

  color: var(--sigta-azul);

  font-size: 13px;
}


.brand-text span {

  display: block;

  margin-top: 3px;

  color: var(--sigta-texto-suave);

  font-size: 11px;
}


.yellow-line {

  height: 3px;

  margin:
    0
    34px;

  border-radius: 8px;

  background: var(--sigta-mostaza);
}


/* =====================================
   PASOS
===================================== */

.steps {

  display: flex;

  align-items: flex-start;

  justify-content: center;

  padding:
    22px
    40px
    5px;
}


.step {

  min-width: 60px;

  text-align: center;
}


.circle {

  width: 31px;

  height: 31px;

  margin: auto;

  display: flex;

  align-items: center;

  justify-content: center;

  border:
    2px solid var(--sigta-borde);

  border-radius: 50%;

  background: var(--sigta-blanco);

  color: var(--sigta-texto-suave);

  font-size: 11px;

  font-weight: 800;
}


.step span {

  display: block;

  margin-top: 6px;

  color: var(--sigta-texto-suave);

  font-size: 9px;

  font-weight: 700;
}


.step.active .circle {

  border-color: var(--sigta-azul);

  background: var(--sigta-azul);

  color: var(--sigta-blanco);
}


.step.active span {

  color: var(--sigta-azul);
}


.line {

  width: 70px;

  height: 2px;

  margin-top: 15px;

  background: var(--sigta-borde);
}


.active-line {

  background: var(--sigta-azul);
}


/* =====================================
   CONTENIDO
===================================== */

.content {

  padding:
    18px
    42px
    27px;

  text-align: center;
}


.icon-box {

  width: 46px;

  height: 46px;

  margin:
    0
    auto
    12px;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 11px;

  background: var(--sigta-azul-tenue);

  color: var(--sigta-azul);

  font-size: 18px;

  font-weight: 900;
}


.icon-box.verified {

  background: var(--sigta-exito-fondo);

  color: var(--sigta-exito);
}


.content h2 {

  margin: 0;

  color: var(--sigta-texto);

  font-size: 23px;
}


.description {

  max-width: 420px;

  margin:
    8px
    auto
    21px;

  color: var(--sigta-texto-suave);

  font-size: 12px;

  line-height: 1.55;
}


/* =====================================
   FORMULARIO
===================================== */

.form-group {

  margin-bottom: 14px;

  text-align: left;
}


.form-group label {

  display: block;

  margin-bottom: 6px;

  color: var(--sigta-azul);

  font-size: 11px;

  font-weight: 700;
}


.form-group > input {

  width: 100%;

  height: 47px;

  padding:
    0
    13px;

  border:
    1px solid var(--sigta-borde);

  border-radius: 8px;

  background: var(--sigta-blanco);

  color: var(--sigta-azul);

  font-size: 14px;

  outline: none;
}


.form-group > input:focus {

  border-color: var(--sigta-azul);

  box-shadow:
    0 0 0 3px
    rgba(7, 81, 141, .1);
}


/* =====================================
   PASSWORD
===================================== */

.password-wrapper {

  width: 100%;

  height: 47px;

  display: flex;

  align-items: center;

  border:
    1px solid var(--sigta-borde);

  border-radius: 8px;

  background: white;
}


.password-wrapper:focus-within {

  border-color: var(--sigta-azul);

  box-shadow:
    0 0 0 3px
    rgba(7, 81, 141, .1);
}


.password-wrapper input {

  flex: 1;

  min-width: 0;

  height: 100%;

  padding:
    0
    13px;

  border: none;

  outline: none;

  background: transparent;

  font-size: 14px;
}


.password-wrapper button {

  height: 100%;

  padding:
    0
    13px;

  border: none;

  background: transparent;

  color: var(--sigta-azul);

  font-size: 11px;

  font-weight: 800;

  cursor: pointer;
}


/* =====================================
   CÓDIGO
===================================== */

.code-title {

  display: block;

  margin-bottom: 10px;

  color: var(--sigta-texto-suave);

  font-size: 11px;

  font-weight: 700;
}


.code-container {

  display: flex;

  justify-content: center;

  gap: 8px;

  margin-bottom: 18px;
}


.code-input {

  width: 49px;

  height: 57px;

  border:
    1px solid var(--sigta-borde);

  border-radius: 9px;

  text-align: center;

  color: var(--sigta-azul);

  font-size: 23px;

  font-weight: 800;

  outline: none;
}


.code-input:focus {

  border-color: var(--sigta-mostaza);

  box-shadow:
    0 0 0 3px
    rgba(242, 196, 0, .14);
}


/* =====================================
   REQUISITOS
===================================== */

.requirements {

  margin:
    17px
    0;

  padding: 14px;

  background: var(--sigta-azul-tenue);

  border-left:
    4px solid var(--sigta-mostaza);

  border-radius: 7px;

  text-align: left;
}


.requirements strong {

  color: var(--sigta-azul);

  font-size: 10px;
}


.requirement-grid {

  display: grid;

  grid-template-columns:
    1fr
    1fr;

  gap: 7px;

  margin-top: 9px;
}


.requirement-grid span {

  color: var(--sigta-texto-suave);

  font-size: 9px;
}


.requirement-grid span.valid {

  color: var(--sigta-exito);

  font-weight: 700;
}


/* =====================================
   MENSAJES
===================================== */

.message {

  margin-bottom: 13px;

  padding:
    10px
    12px;

  border-radius: 7px;

  text-align: left;

  font-size: 10px;

  line-height: 1.4;
}


.message.error {

  background: var(--sigta-error-fondo);

  color: var(--sigta-error);
}


.message.success {

  background: var(--sigta-exito-fondo);

  color: var(--sigta-exito);
}


/* =====================================
   BOTÓN PRINCIPAL
===================================== */

.primary-button {

  width: 100%;

  min-height: 46px;

  border: none;

  border-radius: 8px;

  background: var(--sigta-azul);

  color: var(--sigta-blanco);

  font-size: 13px;

  font-weight: 800;

  cursor: pointer;

  transition:
    background .2s,
    box-shadow .2s;
}


.primary-button:hover:not(:disabled) {

  background: var(--sigta-azul);

  box-shadow:
    0 8px 18px
    rgba(7, 59, 111, .18);
}


.primary-button:disabled {

  opacity: .55;

  cursor: not-allowed;
}


/* =====================================
   BOTONES SECUNDARIOS
===================================== */

.back-button {

  margin-top: 17px;

  border: none;

  background: transparent;

  color: var(--sigta-azul);

  font-size: 10px;

  font-weight: 700;

  cursor: pointer;
}


.back-button:hover {

  text-decoration: underline;
}


.resend {

  display: flex;

  justify-content: center;

  gap: 5px;

  margin-top: 14px;

  color: var(--sigta-texto-suave);

  font-size: 10px;
}


.resend button {

  padding: 0;

  border: none;

  background: transparent;

  color: var(--sigta-azul);

  font-size: 10px;

  font-weight: 800;

  cursor: pointer;
}


/* =====================================
   FINAL
===================================== */

.final-content {

  padding-top: 35px;

  padding-bottom: 35px;
}


.success-circle {

  width: 72px;

  height: 72px;

  margin:
    0
    auto
    17px;

  display: flex;

  align-items: center;

  justify-content: center;

  border-radius: 50%;

  background: var(--sigta-exito-fondo);

  color: var(--sigta-exito);

  font-size: 31px;

  font-weight: 900;
}


.final-message {

  margin:
    20px
    0;

  padding: 15px;

  background: var(--sigta-azul-tenue);

  border-radius: 8px;
}


.final-message strong,
.final-message span {

  display: block;
}


.final-message strong {

  color: var(--sigta-azul);

  font-size: 12px;
}


.final-message span {

  margin-top: 5px;

  color: var(--sigta-texto-suave);

  font-size: 10px;
}


/* =====================================
   FOOTER
===================================== */

footer {

  padding:
    14px
    20px;

  background: var(--sigta-azul-tenue);

  text-align: center;

  color: var(--sigta-texto-suave);
}


footer p {

  margin:
    0
    0
    4px;

  font-size: 9px;
}


footer strong {

  color: var(--sigta-texto-suave);

  font-size: 9px;
}


/* =====================================
   RESPONSIVE
===================================== */

@media (
  max-width: 600px
) {

  .recovery-page {

    align-items: flex-start;

    padding:
      12px;
  }


  .recovery-card {

    border-radius: 13px;
  }


  .brand {

    padding:
      21px
      21px
      15px;
  }


  .logo {

    width: 54px;

    height: 54px;

    font-size: 17px;
  }


  .brand-text h1 {

    font-size: 25px;
  }


  .brand-text strong {

    font-size: 11px;
  }


  .brand-text span {

    font-size: 9px;
  }


  .yellow-line {

    margin:
      0
      21px;
  }


  .steps {

    padding:
      20px
      15px
      3px;
  }


  .line {

    width: 38px;
  }


  .content {

    padding:
      17px
      21px
      25px;
  }


  .content h2 {

    font-size: 21px;
  }


  .code-container {

    gap: 5px;
  }


  .code-input {

    width: 41px;

    height: 51px;

    font-size: 20px;
  }


  .requirement-grid {

    grid-template-columns: 1fr;
  }

}


@media (
  max-width: 360px
) {

  .brand-text span {

    display: none;
  }


  .code-input {

    width: 37px;

    height: 48px;
  }


  .steps {

    padding-left: 8px;

    padding-right: 8px;
  }

}

</style>