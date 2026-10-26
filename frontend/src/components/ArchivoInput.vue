<template>
  <span class="archivo-selector">
    <input ref="entrada" v-bind="$attrs" class="archivo-nativo" type="file" @change="cambiar">
    <button type="button" :disabled="$attrs.disabled" @click="entrada?.click()">{{ $attrs.multiple !== undefined && $attrs.multiple !== false ? 'Seleccionar archivos' : 'Seleccionar archivo' }}</button>
    <span>{{ nombres || 'Ningún archivo seleccionado' }}</span>
  </span>
</template>
<script setup>
import { ref } from 'vue'
defineOptions({ inheritAttrs: false })
const emit=defineEmits(['change'])
const entrada=ref(null), nombres=ref('')
function cambiar(evento){nombres.value=Array.from(evento.target.files||[]).map(f=>f.name).join(', ');emit('change',evento)}
defineExpose({focus:()=>entrada.value?.focus(),click:()=>entrada.value?.click(),get files(){return entrada.value?.files},get value(){return entrada.value?.value},set value(v){if(entrada.value)entrada.value.value=v}})
</script>
<style scoped>
.archivo-selector{display:flex;align-items:center;gap:12px;flex-wrap:wrap;width:100%;padding:10px;border:1px solid var(--sigta-borde,#cbd8e6);border-radius:8px;background:#fff;color:var(--sigta-azul,#123a6b);font-size:13px;box-sizing:border-box}.archivo-selector .archivo-nativo{position:absolute;width:1px;height:1px;opacity:0;padding:0;border:0;overflow:hidden}.archivo-selector button{background:var(--sigta-azul,#123a6b);color:white;padding:9px 13px;border:0;border-radius:6px;cursor:pointer;font:inherit;font-weight:700}.archivo-selector>span{overflow-wrap:anywhere;min-width:0;flex:1}.archivo-selector:focus-within{outline:2px solid var(--sigta-mostaza,#ffc72c);outline-offset:2px}
</style>
