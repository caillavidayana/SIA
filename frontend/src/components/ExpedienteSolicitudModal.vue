<template>
  <div class="expediente-backdrop" @click.self="$emit('cerrar')">
    <section class="expediente-modal" role="dialog" aria-modal="true" :aria-label="`Expediente ${registro.codigo}`">
      <header class="expediente-head">
        <button type="button" @click="$emit('cerrar')">← Volver</button>
        <div><small>EXPEDIENTE {{ registro.codigo }}</small><h2>{{ registro.titulo }}</h2></div>
        <button type="button" aria-label="Cerrar" @click="$emit('cerrar')">×</button>
      </header>
      <div class="expediente-body">
        <section class="expediente-datos">
          <h3>Información original del ticket</h3>
          <dl>
            <div><dt>Solicitante</dt><dd>{{ registro.solicitante_nombre }}</dd></div>
            <div><dt>Correo</dt><dd>{{ registro.solicitante_email || 'Sin especificar' }}</dd></div>
            <div><dt>Área</dt><dd>{{ registro.area_nombre || 'Sin especificar' }}</dd></div>
            <div><dt>Ubicación</dt><dd>{{ registro.ubicacion || 'Sin especificar' }}</dd></div>
            <div><dt>Referencia</dt><dd>{{ registro.referencia_ubicacion || 'Sin referencia' }}</dd></div>
            <div><dt>Equipo</dt><dd>{{ registro.equipo_afectado || 'Sin especificar' }}</dd></div>
            <div v-if="registro.sla_fecha_limite"><dt>Fecha límite de atención</dt><dd>{{ new Date(registro.sla_fecha_limite).toLocaleString('es-BO',{timeZone:'America/La_Paz'}) }} · {{ registro.sla_estado==='VENCIDO'?'Vencido':registro.sla_horas+' horas' }}</dd></div>
          </dl>
          <div class="expediente-descripcion"><b>Descripción / requerimiento</b><p>{{ registro.descripcion || 'Sin descripción' }}</p></div>
          <div v-if="registro.evidencia_archivo_url" class="expediente-evidencia">
            <b>Evidencia del solicitante</b>
            <img v-if="esImagen(registro.evidencia_archivo_url)" :src="registro.evidencia_archivo_url" alt="Evidencia del solicitante">
            <button type="button" @click="$emit('evidencia', registro.evidencia_archivo_url)">Ver evidencia</button>
          </div>
        </section>
        <details v-for="(ciclo,i) in registro.historial_reaperturas || []" :key="i" class="expediente-descripcion"><summary>Ciclo anterior · cierre {{ new Date(ciclo.cerrado_en).toLocaleString('es-BO') }}</summary><p>{{ ciclo.textos?.solucion }}</p><p>{{ ciclo.textos?.informe_final }}</p><button v-for="(ruta,campo) in ciclo.archivos" :key="campo" type="button" @click="$emit('evidencia','/media/'+ruta)">Ver {{ campo.replaceAll('_',' ') }}</button></details>
        <slot />
      </div>
    </section>
  </div>
</template>
<script setup>
defineProps({ registro: { type: Object, required: true } })
defineEmits(['cerrar', 'evidencia'])
function esImagen(url) { return /\.(png|jpe?g|gif|webp)(\?|$)/i.test(url || '') }
</script>
<style scoped>
.expediente-backdrop{position:fixed;inset:0;z-index:1100;background:#082b4fcc;display:grid;place-items:center;padding:20px;font-family:var(--sigta-fuente);color:var(--sigta-texto)}
.expediente-modal{width:min(1050px,96vw);max-height:92vh;display:flex;flex-direction:column;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 20px 65px #082b4f40}
.expediente-head{display:flex;align-items:center;justify-content:space-between;gap:16px;background:var(--sigta-azul);color:#fff;padding:18px 22px;margin:0;flex-shrink:0}
.expediente-head h2{margin:4px 0 0;font-size:20px;color:#fff}.expediente-head small{color:#fff}.expediente-head button{background:#ffffff12;border:1px solid #ffffff55;color:#fff;border-radius:7px;padding:9px 12px;cursor:pointer}
.expediente-body{padding:20px;overflow:auto}.expediente-datos{border:1px solid #dbe5f0;border-radius:10px;padding:18px;background:#fff}.expediente-datos h3{margin:0 0 14px;font-size:16px;color:var(--sigta-azul)}
dl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0}dl>div{padding:10px;background:#f5f8fc;border-radius:6px}dt{font-size:11px;color:#64748b}dd{margin:5px 0 0;overflow-wrap:anywhere;font-size:13px}.expediente-descripcion{margin-top:16px;padding:14px;background:#f5f8fc;border-radius:8px}.expediente-descripcion p{white-space:pre-wrap;line-height:1.6;margin:8px 0 0}.expediente-evidencia{display:flex;flex-direction:column;gap:10px;margin-top:14px;padding:14px;background:#f7faff;border:1px solid #d6e1ed;border-radius:10px}.expediente-evidencia img{width:min(360px,100%);max-height:230px;object-fit:contain}.expediente-evidencia button{align-self:flex-start;background:var(--sigta-azul);color:#fff;border:0;border-radius:7px;padding:10px 14px;font-weight:700;cursor:pointer}
@media(max-width:760px){.expediente-backdrop{padding:7px}.expediente-modal{width:100%;max-height:98vh}.expediente-head{padding:14px;gap:10px}.expediente-head h2{font-size:16px}dl{grid-template-columns:1fr 1fr}.expediente-body{padding:14px}}
</style>
