<template><div class="prioridad-r03"><label>Prioridad<select :value="prioridad || modelValue" :disabled="!!prioridad" aria-label="Prioridad del ticket" @change="$emit('update:modelValue',$event.target.value)"><option value="BAJA">Baja</option><option value="MEDIA">Media</option><option value="ALTA">Alta</option></select></label><p v-if="prioridad">Asignada automáticamente por la categoría o la descripción del problema. Jefatura conservará la revisión del ticket.</p><p v-if="horas">Plazo de atención: {{ horas }} horas desde el registro del ticket.</p><p v-if="error" role="alert">{{ error }}</p></div></template>
<script setup>
import {computed,onMounted,ref} from 'vue'
import {reglas,cargarReglas} from '../utils/reglas'
import {prioridadAutomatica} from '../utils/reglasCore'
const props=defineProps({titulo:String,descripcion:String,categoria:[Object,String],modelValue:{type:String,default:'MEDIA'}})
defineEmits(['update:modelValue'])
const error=ref('')
const prioridad=computed(()=>prioridadAutomatica(props.titulo,props.descripcion,props.categoria,reglas.value))
const horas=computed(()=>reglas.value?.sla_horas?.[prioridad.value||props.modelValue])
onMounted(async()=>{try{await cargarReglas()}catch(e){error.value=e.message}})
</script>
<style scoped>
.prioridad-r03{margin:16px 0;padding:16px;background:var(--sigta-azul-tenue);border-left:4px solid var(--sigta-mostaza);border-radius:8px}label{display:grid;gap:7px;font-size:13px;font-weight:700;color:var(--sigta-azul)}select{padding:10px;border:1px solid var(--sigta-borde);border-radius:7px;color:var(--sigta-azul);background:white;opacity:1}p{font-size:12px;line-height:1.6;color:var(--sigta-texto-suave);margin-bottom:0}
</style>
