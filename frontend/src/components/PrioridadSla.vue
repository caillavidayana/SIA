<template>
  <div class="sla-prioridades" role="group" aria-label="Prioridad y tiempo de atención">
    <button v-for="p in opciones" :key="p.codigo" type="button" :class="{selected:modelValue===p.codigo}" :aria-pressed="modelValue===p.codigo" :disabled="disabled" @click="$emit('update:modelValue',p.codigo)">
      <b>{{ p.nombre }}</b><span>{{ p.horas }} horas</span>
    </button>
  </div>
</template>
<script setup>
defineProps({modelValue:String,opciones:Array,disabled:Boolean})
defineEmits(['update:modelValue'])
</script>
<style scoped>
.sla-prioridades{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}.sla-prioridades button{border:1px solid #cbd9e8;background:#fff;border-radius:8px;padding:15px 10px;color:var(--sigta-azul);cursor:pointer}.sla-prioridades b,.sla-prioridades span{display:block}.sla-prioridades span{margin-top:6px;font-size:12px;color:#64748b}.sla-prioridades .selected{border-color:var(--sigta-azul);box-shadow:inset 0 0 0 1px var(--sigta-azul);background:#eaf2fc}@media(max-width:650px){.sla-prioridades{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
