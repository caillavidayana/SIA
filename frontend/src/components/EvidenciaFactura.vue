<template>
  <div>
    <label class="sia-secondary">Seleccionar factura<ArchivoInput type="file" accept="application/pdf,image/*" @change="elegir" /></label>
    <label class="sia-secondary">Tomar fotografía<ArchivoInput type="file" accept="image/*" capture="environment" @change="elegir" /></label>
    <p v-if="modelValue">{{ modelValue.name }} <button type="button" @click="$emit('update:modelValue',null)">Quitar / reemplazar</button></p>
    <img v-if="preview && modelValue?.type.startsWith('image/')" :src="preview" alt="Previsualización de factura">
    <a v-else-if="preview" :href="preview" target="_blank" rel="noopener">Previsualizar documento</a>
  </div>
</template>
<script setup>
import { onUnmounted, ref, watch } from 'vue'
const props=defineProps({modelValue: Object}), emit=defineEmits(['update:modelValue']), preview=ref('')
function elegir(e){emit('update:modelValue',e.target.files?.[0]||null);e.target.value=''}
watch(()=>props.modelValue,archivo=>{if(preview.value)URL.revokeObjectURL(preview.value);preview.value=archivo?URL.createObjectURL(archivo):''},{immediate:true})
onUnmounted(()=>{if(preview.value)URL.revokeObjectURL(preview.value)})
</script>
<style scoped>input {display:block;margin-top:8px;max-width:100%;}img {display:block;max-width:100%;max-height:250px;margin:12px 0;}.sia-secondary {margin:6px 8px 6px 0;}</style>
