<template>
  <section>
    <p>Elabore el acta al entregar el producto. El encargado de almacén y el receptor identificado deben firmar el documento impreso.</p>
    <label class="sia-field">Nombre completo de quien recibe<input v-model="recibe" :disabled="ocupado || generando || recuperando || solicitud.receptor_acta?.tecnico" maxlength="150" placeholder="Nombres y apellidos"></label>
    <label class="sia-field">Observaciones de entrega<textarea v-model="observaciones" :disabled="ocupado || generando || recuperando" maxlength="2000" rows="3" placeholder="Estado de los bienes y observaciones de la entrega"></textarea></label>
    <p v-if="recuperando" role="status">Consultando acta pendiente de firma…</p>
    <label class="acta-check"><input v-model="entregaFisica" type="checkbox" :disabled="ocupado || generando">Estoy realizando la entrega física del producto al receptor indicado.</label>
    <button class="sia-primary" :disabled="ocupado || generando || recuperando || !nombreValido || !entregaFisica" @click="generar">{{ generando ? 'Generando…' : documento ? 'Generar nueva acta PDF' : 'Generar acta PDF' }}</button>
    <div v-if="documento" class="acta-respaldo">
      <strong>Acta {{ documento.referencia }}</strong>
      <p>Entrega: {{ documento.datos.entrega }} · Recibe: {{ documento.datos.recibe }}</p>
      <button class="sia-secondary" @click="$emit('ver', documento.original_url, 'Acta de conformidad original')">Ver e imprimir acta PDF</button>
      <label class="sia-field">Subir el acta PDF con ambas firmas<ArchivoInput :key="documento.id" type="file" accept="application/pdf,.pdf" :disabled="ocupado || generando" @change="elegir" /></label>
      <p v-if="archivo">Seleccionado: {{ archivo.name }}</p>
      <label class="acta-check"><input v-model="confirmada" type="checkbox" :disabled="ocupado || generando">Confirmo que el PDF corresponde al acta generada y contiene las firmas de quien recibe y del encargado de almacén.</label>
    </div>
    <p v-if="error" class="acta-error" role="alert">{{ error }}</p>
  </section>
</template>
<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
const props = defineProps({ solicitud: { type: Object, required: true }, ocupado: Boolean })
const archivo = defineModel(), actaId = defineModel('actaId'), listo = defineModel('listo')
defineEmits(['ver'])
const recibe = ref(props.solicitud.receptor_acta?.nombre || props.solicitud.entregado_a || '')
const entregaFisica = ref(false), observaciones = ref(props.solicitud.observacion_salida || '')
const documento = ref(null), confirmada = ref(false), generando = ref(false), recuperando = ref(true), error = ref('')
let montado = true
onUnmounted(() => { montado = false })
const nombreValido = computed(() => props.solicitud.receptor_acta?.tecnico ? !!recibe.value.trim() : recibe.value.trim().split(/\s+/).length >= 2 && recibe.value.trim().split(/\s+/).every(p => /\p{L}/u.test(p)))
watch([recibe, observaciones], () => { documento.value = null; archivo.value = null; actaId.value = null; confirmada.value = false })
watch([documento, archivo, confirmada, generando, recuperando], () => { listo.value = !!(documento.value && archivo.value && confirmada.value && !generando.value && !recuperando.value) }, { immediate: true })
async function api(options) {
  const r = await fetch(`/api/compras/solicitudes/${props.solicitud.id}/actas-almacen/`, { ...options, headers: { Authorization: `Token ${localStorage.getItem('sigta_token')}`, ...options?.headers } })
  const datos = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(datos.detalle || Object.values(datos)[0] || 'No se pudo consultar el acta.')
  return datos
}
async function generar() {
  if (!nombreValido.value || !entregaFisica.value || generando.value || props.ocupado) return
  generando.value = true; error.value = ''
  try {
    const generado = await api({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ recibe: recibe.value.trim(), observaciones: observaciones.value.trim(), entrega_confirmada: entregaFisica.value }) })
    if (!montado) return
    documento.value = generado
    actaId.value = documento.value.id; archivo.value = null; confirmada.value = false
  } catch (e) { error.value = e.message } finally { generando.value = false }
}
function elegir(e) {
  archivo.value = null; confirmada.value = false; error.value = ''
  const nuevo = e.target.files?.[0]
  if (!nuevo) return
  if (!/\.pdf$/i.test(nuevo.name) || !nuevo.size || nuevo.size > 10 * 1024 * 1024) { error.value = 'Adjunte un PDF con contenido y de hasta 10 MB.'; e.target.value = ''; return }
  archivo.value = nuevo
}
onMounted(async () => {
  try {
    const actas = await api(), pendiente = actas.find(a => a.puede_reanudar && a.datos.recibe === recibe.value)
    if (!montado) return
    if (pendiente) {
      recibe.value = pendiente.datos.recibe; observaciones.value = pendiente.datos.observaciones || ''
      await nextTick()
      if (!montado) return
      documento.value = pendiente; actaId.value = pendiente.id
    }
  } catch (e) { error.value = e.message } finally { recuperando.value = false }
})
</script>
<style scoped>
p{font-size:13px;color:var(--sigta-texto-suave);line-height:1.6}.acta-respaldo{margin-top:20px;padding:18px;border:1px solid var(--sigta-borde);border-radius:9px;background:#f7faff}.acta-respaldo>strong{display:block;font-size:12px;overflow-wrap:anywhere}.acta-check{display:flex;align-items:flex-start;gap:10px;line-height:1.6;font-size:13px}.acta-check input{margin-top:5px}.acta-error{background:var(--sigta-error-fondo);color:var(--sigta-error);border-radius:7px;padding:12px}
</style>
