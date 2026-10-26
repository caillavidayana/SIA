<template>
  <Teleport to="body">
    <div v-if="visible" class="caja-overlay">
      <section
        class="caja-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="caja-titulo"
      >
        <div class="caja-encabezado">
          <div class="caja-icono">!</div>
          <div>
            <span class="caja-etiqueta">AVISO PRESUPUESTARIO</span>
            <h2 id="caja-titulo">Límite de Caja Chica superado</h2>
          </div>
        </div>

        <div class="caja-contenido">
          <p class="caja-descripcion">
            El monto solicitado supera el límite permitido para
            Caja Chica. La solicitud podrá continuar y será
            gestionada mediante Finanzas.
          </p>

          <div class="caja-resumen">
            <div class="caja-dato">
              <span>Límite permitido</span>
              <strong>{{ moneda(limite) }}</strong>
            </div>

            <div class="caja-dato">
              <span>Monto solicitado</span>
              <strong>{{ moneda(monto) }}</strong>
            </div>
          </div>

          <div class="caja-exceso">
            <span>Monto excedido</span>
            <strong>{{ moneda(exceso) }}</strong>
          </div>

          <div class="caja-destino">
            <span class="caja-punto"></span>
            <div>
              <small>VÍA DE ADQUISICIÓN</small>
              <strong>Finanzas</strong>
            </div>
          </div>
        </div>

        <div class="caja-acciones">
          <button
            type="button"
            class="caja-cancelar"
            @click="$emit('cancelar')"
          >
            Volver al formulario
          </button>

          <button
            type="button"
            class="caja-continuar"
            @click="$emit('continuar')"
          >
            Entendido, continuar
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  monto: { type: Number, required: true },
  limite: { type: Number, required: true },
})

defineEmits(['cancelar', 'continuar'])

const exceso = computed(() =>
  Math.max(0, props.monto - props.limite)
)

function moneda(valor) {
  return `Bs ${Number(valor).toLocaleString('es-BO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}
</script>

<style scoped>
.caja-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: rgba(10, 24, 46, 0.68);
  backdrop-filter: blur(5px);
}

.caja-modal {
  width: 100%;
  max-width: 530px;
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25);
  animation: cajaEntrada 0.25s ease-out;
  font-family: inherit;
}

.caja-encabezado {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 28px 30px;
  background: #f7f9fc;
  border-top: 5px solid #c99a35;
  border-bottom: 1px solid #e8edf3;
}

.caja-icono {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #fff0cc;
  color: #9b6a12;
  font-size: 28px;
  font-weight: 800;
}

.caja-etiqueta {
  color: #b17b1d;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.4px;
}

.caja-encabezado h2 {
  margin: 6px 0 0;
  color: #173b66;
  font-size: 21px;
  line-height: 1.3;
}

.caja-contenido {
  padding: 25px 30px;
}

.caja-descripcion {
  margin: 0 0 22px;
  color: #536176;
  font-size: 14px;
  line-height: 1.7;
}

.caja-resumen {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.caja-dato {
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 17px;
  background: #f3f6fa;
  border: 1px solid #e5eaf1;
  border-radius: 11px;
}

.caja-dato span,
.caja-exceso span {
  color: #64748b;
  font-size: 12px;
}

.caja-dato strong {
  color: #173b66;
  font-size: 21px;
}

.caja-exceso {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 17px;
  padding: 15px 2px;
  border-bottom: 1px solid #e5eaf1;
}

.caja-exceso strong {
  color: #bd5b30;
  font-size: 19px;
}

.caja-destino {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 15px;
  background: #eef4fb;
  border-radius: 11px;
}

.caja-punto {
  width: 11px;
  height: 11px;
  background: #173b66;
  border-radius: 50%;
}

.caja-destino div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.caja-destino small {
  color: #718096;
  font-size: 10px;
  letter-spacing: 1px;
}

.caja-destino strong {
  color: #173b66;
  font-size: 15px;
}

.caja-acciones {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 30px 26px;
}

.caja-acciones button {
  min-height: 44px;
  padding: 0 17px;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
}

.caja-cancelar {
  background: #fff;
  border: 1px solid #d6deea;
  color: #536176;
}

.caja-continuar {
  background: #173b66;
  border: 1px solid #173b66;
  color: #fff;
}

.caja-continuar:hover {
  background: #24558b;
}

@keyframes cajaEntrada {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 550px) {
  .caja-encabezado,
  .caja-contenido,
  .caja-acciones {
    padding-left: 18px;
    padding-right: 18px;
  }

  .caja-resumen {
    grid-template-columns: 1fr;
  }

  .caja-acciones {
    flex-direction: column;
  }
}
</style>
