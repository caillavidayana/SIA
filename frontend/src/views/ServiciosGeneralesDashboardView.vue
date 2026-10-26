<template>
  <div class="layout sigta-role-layout sia-gestion">
    <aside :class="{ abierto: menuAbierto }">
      <div class="brand-row">
        <div class="brand"><b><img src="/img/emi.jpg" alt="EMI"></b><div><strong>SIA</strong><small>Mantenimiento</small></div></div>
        <button type="button" class="menu-toggle" :aria-expanded="menuAbierto" aria-label="Mostrar opciones del menú" @click="menuAbierto = !menuAbierto"><span></span><span></span><span></span></button>
      </div>
      <p>GESTIÓN DE MANTENIMIENTO</p>
      <button v-for="m in menu" :key="m.id" :class="{active:vista===m.id}" @click="irA(m.id)"><span class="icon-badge" :style="{'--menu-icon':m.color,'--menu-icon-bg':m.color+'26'}"><IconoSigta :nombre="m.icono" :tamano="16" /></span>{{ m.nombre }}<em v-if="m.total!==undefined">{{ m.total }}</em></button>
      <div class="sidebar-watermark" aria-hidden="true">
        <img src="/img/marca-de-agua.png" alt="">
        <div class="wm-text"><b>EMI</b><span>Escuela Militar de Ingeniería</span><small>"Mcal. Antonio José de Sucre"</small></div>
      </div>
      <div class="bottom"><button class="logout" @click="mostrarLogout = true"><IconoSigta nombre="salir" :tamano="17" />Cerrar sesión</button></div>
    </aside>

    <LogoutModal :visible="mostrarLogout" @cancelar="mostrarLogout = false" @confirmar="confirmarSalida" />
    <TarjetaGuardado :visible="mostrarGuardadoOk" :texto="textoGuardado" :tipo="tipoGuardado" @cerrar="ocultarGuardado" />

    <main>
      <header>
        <div><h1>{{ titulo }}</h1><p>{{ subtitulo }}</p></div>

      
        <UsuarioHeader @actualizar="cargar" />
      </header>

      <p v-if="errorCarga" class="load-error">{{ errorCarga }}</p>

      <!-- ============================ RESUMEN ============================ -->
      <section v-if="vista==='resumen'">
        <div class="hero">
          <div><small>JEFATURA DE MANTENIMIENTO</small><h2>{{ saludo }}, {{ primerNombre }}</h2><p>Requerimientos que requieren su gestión hoy.</p></div>
          <span>MT</span>
        </div>
        <div class="stats">
          <article @click="irA('gestion')"><i class="badge" style="background:#3E7BD626;color:#3E7BD6"><IconoSigta nombre="tickets" :tamano="20" /></i><div><small>Gestión</small><b>{{ ticketsGestion.length }}</b><p>tickets pendientes</p></div></article>
          <article @click="irA('compra')"><i class="badge" style="background:#C79A1E26;color:#C79A1E"><IconoSigta nombre="compras" :tamano="20" /></i><div><small>Compras</small><b>{{ porEvaluarCompra.length }}</b><p>por evaluar</p></div></article>
          <article @click="irA('informe')"><i class="badge" style="background:#2FA85C26;color:#2FA85C"><IconoSigta nombre="validar" :tamano="20" /></i><div><small>Por verificar</small><b>{{ porVerificar.length }}</b><p>funcionamiento</p></div></article>
          <article @click="irA('informe')"><i class="badge" style="background:#7B6FD926;color:#7B6FD9"><IconoSigta nombre="conformidad" :tamano="20" /></i><div><small>Por informar</small><b>{{ porConformar.length + porInformar.length }}</b><p>conformidad</p></div></article>
        </div>
        <div class="panels">
          <section class="panel">
            <div class="panel-head"><div><h3>Proceso de mantenimiento</h3></div></div>
            <div class="process-grid">
              <button class="process-card" style="border-top-color:#3E7BD6" @click="irA('gestion')"><span class="process-num" style="background:#3E7BD626;color:#3E7BD6">01</span><div><b>Gestión integral de tickets</b><small>Validar, clasificar prioridad y designar técnico</small></div></button>
              <button class="process-card" style="border-top-color:#C79A1E" @click="irA('compra')"><span class="process-num" style="background:#C79A1E26;color:#C79A1E">02</span><div><b>Recibir requerimiento y cotización</b><small>Evaluar la viabilidad de la compra</small></div></button>
              <button class="process-card" style="border-top-color:#2FA85C" @click="irA('informe')"><span class="process-num" style="background:#2FA85C26;color:#2FA85C">03</span><div><b>Consultar conformidad</b><small>Consultar si el problema quedó resuelto</small></div></button>
              <button class="process-card" style="border-top-color:#7B6FD9" @click="irA('informe')"><span class="process-num" style="background:#7B6FD926;color:#7B6FD9">04</span><div><b>Conformidad e informe final</b><small>Cerrar el caso y elevarlo a la Dirección</small></div></button>
            </div>
          </section>
          <section class="panel">
            <div class="panel-head"><div><small>SEGUIMIENTO</small><h3>Reporte mensual</h3></div></div>
            <p class="copy">Consolidado de los mantenimientos finalizados en el periodo.</p>
            <button class="wide primary" @click="irA('reporte')">Ver reporte mensual →</button>
          </section>
        </div>
      </section>

      <!-- ========================= GESTIÓN DE TICKETS ========================= -->
      <section v-else-if="vista==='gestion'">
        <div class="gestion-toolbar"><label><IconoSigta nombre="buscar" :tamano="17" /><input v-model="busquedaTickets" placeholder="Buscar por código, título o solicitante"></label><span>{{ ticketsFiltrados.length }} ticket(s)</span></div>
        <div v-if="cargando" class="empty">Consultando tickets…</div>
        <div v-else class="gestion-kanban">
          <section v-for="columna in columnasGestion" :key="columna.id" :class="['gestion-columna',columna.id]">
            <div class="gestion-columna-head"><b><i aria-hidden="true"></i>{{ columna.nombre }}</b><em>{{ columna.items.length }}</em></div>
            <article v-for="r in columna.items" :key="r.id" class="gestion-ticket">
              <div class="gestion-ticket-head"><b>{{ r.codigo }}</b><span>{{ r.prioridad_jefatura || 'Sin clasificar' }}</span></div>
              <h3>{{ r.titulo }}</h3>
              <dl><div><dt>Solicitante</dt><dd>{{ r.solicitante_nombre }}</dd></div><div><dt>Ubicación</dt><dd>{{ r.ubicacion || 'Sin especificar' }}</dd></div><div><dt>Técnico</dt><dd>{{ r.auxiliar_asignado_nombre || 'Sin asignar' }}</dd></div><div><dt>SLA</dt><dd>{{ r.sla_horas ? r.sla_horas+' horas' : 'Sin asignar' }}</dd></div><div><dt>Estado</dt><dd>{{ r.estado_nombre || r.estado_codigo }}</dd></div></dl>
              <button type="button" @click="verItem(r)">Ver detalle</button>
            </article>
            <p v-if="!columna.items.length" class="empty-list">Sin tickets</p>
          </section>
        </div>
      </section>

      <!-- ===================== 4. VIABILIDAD COMPRA (NUEVO MAESTRO-DETALLE) ===================== -->
      <section v-else-if="vista==='compra'">
        <div class="gestion-toolbar"><label><IconoSigta nombre="buscar" :tamano="17" /><input v-model="busquedaCompra" placeholder="Buscar por código, título o solicitante"></label><span>{{ comprasFiltradas.length }} compra(s) por evaluar</span></div>
        <div class="viabilidad-cards"><article v-for="r in comprasFiltradas" :key="r.id"><div class="gestion-ticket-head"><b>{{ r.codigo }}</b><span>Por evaluar</span></div><h3>{{ r.titulo }}</h3><p><b>Técnico:</b> {{ r.auxiliar_asignado_nombre || 'Sin asignar' }}</p><p><b>Componente:</b> {{ r.producto_requerido }}</p><p><b>Costo estimado:</b> Bs. {{ r.costo_estimado || 'Sin especificar' }}</p><button class="sia-primary" @click="abrirCompra(r)">Ver detalle y validar viabilidad</button></article><div v-if="!comprasFiltradas.length" class="empty">No hay compras pendientes de evaluación.</div></div>
      </section>

      <!-- ======================= 5. VERIFICAR ======================= -->
      <section v-else-if="vista==='verificar'">
        <div class="instruction"><b>Conformidad del solicitante</b><span>El solicitante verifica el funcionamiento y registra su respuesta.</span></div>
        <div class="cards"><article v-for="r in porVerificar" :key="r.id"><div class="top"><span>{{ r.codigo }}</span></div><h3>{{ r.titulo }}</h3><p>Pendiente de respuesta del solicitante.</p><div class="actions"><button @click="verItem(r)">Ver detalle</button></div></article></div>
      </section>

      <!-- =============== 6. CONFORMIDAD E INFORME FINAL =============== -->
      <section v-else-if="vista==='informe'">
        <div class="gestion-toolbar"><label><IconoSigta nombre="buscar" :tamano="17" /><input v-model="busquedaInforme" placeholder="Buscar informe por código, título o solicitante"></label><span>{{ informesFiltrados.length }} informe(s)</span></div>
        <section class="panel"><div class="table-wrap"><table class="tabla-informes"><thead><tr><th>ID</th><th>Asunto</th><th>Solicitante</th><th>Técnico</th><th>Estado</th><th>Fecha</th><th></th></tr></thead><tbody><tr v-for="r in informesFiltrados" :key="r.id"><td><b>{{ r.codigo }}</b></td><td>{{ r.titulo }}</td><td>{{ r.solicitante_nombre }}</td><td>{{ r.auxiliar_asignado_nombre }}</td><td>{{ r.estado_nombre }}</td><td>{{ fecha(r.creado_en) }}</td><td><button class="sia-secondary" @click="abrirInforme(r)">Ver detalle</button></td></tr><tr v-if="!informesFiltrados.length"><td colspan="7" class="empty">No hay informes técnicos registrados.</td></tr></tbody></table></div></section>
      </section>

      <!-- ====================== REPORTE MENSUAL ====================== -->
      <section v-else-if="vista==='reporte'" class="vista-reporte">
        <div class="instruction"><b>Reporte mensual</b><span>Consolidado de los mantenimientos finalizados en el periodo.</span></div>

        <div class="panel reporte-filtros">
          <div class="actions" style="border:0;margin:0">
            <label class="campo">Año<input v-model="periodo.anio" type="number" min="2020" max="2100"></label>
            <label class="campo">Mes<input v-model="periodo.mes" type="number" min="1" max="12"></label>
            <button class="primary" :disabled="procesando" @click="cargarReporte">Consultar</button>
          </div>
        </div>

        <div v-if="reporte" class="reporte-cabecera">
          <div class="panel reporte-kpi">
            <p v-if="reporte" class="copy"><b>{{ reporte.total_finalizados }}</b> mantenimiento(s) finalizado(s) en {{ reporte.mes }}/{{ reporte.anio }}.</p>
          </div>

          <div v-if="reporte.total_finalizados" class="panel reporte-grafico">
            <span class="rg-titulo">Finalizados por día</span>
            <div class="rg-barras">
              <div v-for="d in reportePorDia" :key="`rg-${d.dia}`" class="rg-col" :title="`${d.dia}: ${d.total}`">
                <div class="rg-pista"><div :class="['rg-barra', d.total ? 'con-dato' : '']" :style="{ height: (d.total / reporteMaxDia * 100) + '%' }"></div></div>
                <small>{{ d.dia % 5 === 0 || d.dia === 1 ? d.dia : '' }}</small>
              </div>
            </div>
          </div>
        </div>

        <div v-if="reporte" class="panel reporte-lista">
          <article v-for="r in (reporte?.requerimientos || [])" :key="`rep-${r.id}`" class="reporte-item">
            <b>{{ r.codigo }}</b> — {{ r.titulo }} <small>({{ fecha(r.finalizado_en) }})</small>
          </article>
        </div>
      </section>
    </main>
    <ValidacionSolicitud v-if="validacionActiva" :registro="validacionActiva" :ocupado="procesando" :error="errorValidacion" @cerrar="validacionActiva = null" @validar="validar(validacionActiva)" @rechazar="rechazar(validacionActiva, $event)" />
    <ExpedienteSolicitudModal v-if="expedienteAbierto && itemActivo" :registro="itemActivo" @cerrar="expedienteAbierto=false" @evidencia="abrirEvidencia">
      <section v-if="itemActivo.estado_codigo==='RECIBIDO'" class="expediente-action"><h3>Validación del solicitante</h3><button class="sia-primary" :disabled="procesando" @click="validacionActiva=itemActivo">Validar requisitos</button></section>
      <section v-else-if="itemActivo.estado_codigo==='VALIDADO' && !itemActivo.clasificado_en" class="expediente-action">
        <small>PASO 2</small><h3>Clasificar prioridad y SLA</h3>
        <PrioridadSla v-model="formClasificar.prioridad" :opciones="prioridades" :disabled="!!itemActivo?.prioridad_automatica" />
        <label class="sia-field">Criterio técnico<textarea v-model="formClasificar.criterio_prioridad" rows="3" placeholder="Justifique la prioridad" /></label>
        <div class="expediente-actions"><button class="sia-primary" :disabled="procesando || !formClasificar.prioridad || !formClasificar.criterio_prioridad.trim()" @click="clasificar">Guardar y continuar</button></div>
      </section>
      <section v-else-if="itemActivo.estado_codigo==='VALIDADO'" class="expediente-action">
        <small>PASO 3</small><h3>Asignar técnico</h3>
        <label class="sia-field">Técnico activo de Mantenimiento<select v-model="formDesignar.tecnico_id"><option value="">Seleccione…</option><option v-for="t in tecnicos" :key="t.id" :value="t.id">{{ t.nombre_completo || t.email }} · {{ casosActivos(t.id) }} / {{t.limite_tickets}} casos activos</option></select></label>
        <div class="expediente-actions"><button class="sia-primary" :disabled="procesando || !formDesignar.tecnico_id" @click="confirmarAsignacion=true">Asignar técnico</button></div>
      </section>
<CotizacionesExpediente :filas="itemActivo?.cotizaciones" />
      <section v-if="cotizacionCompra" class="expediente-action">
        <h3>Cotizaci&#243;n / proforma del t&#233;cnico</h3>
        <div class="viabilidad-documentos"><article><i>CT</i><div><b>Proforma adjunta</b><small>Documento presentado por el t&#233;cnico de mantenimiento</small></div><button class="sia-primary" @click="abrirEvidencia(cotizacionCompra,'Proforma del tecnico')">Ver proforma</button></article></div>
      </section>
      <section v-if="itemActivo.estado_compra_componente==='SOLICITADA' || (itemActivo.estado_compra_componente==='VIABLE' && !itemActivo.derivado_compra) || itemActivo.compra_vinculada?.documentos_pendientes?.length" class="expediente-action">
        <small>{{ compraValidada ? 'VIABILIDAD VALIDADA' : 'REQUERIMIENTO DE COMPRA RECIBIDO' }}</small><h3>{{ compraValidada ? 'Adjuntar POA y proveído' : 'Validar viabilidad' }}</h3><p v-if="compraValidada">Adjunte el POA y el proveído para completar el expediente y elevarlo a Compras.</p><p v-else>Revise la cotización y el informe técnico. Si la compra no es viable, registre el motivo: el técnico será informado y el caso se cerrará sin compra.</p>
        <dl class="viabilidad-datos"><div><dt>Técnico</dt><dd>{{ itemActivo.auxiliar_asignado_nombre || 'Sin asignar' }}</dd></div><div><dt>Diagnóstico</dt><dd>{{ itemActivo.diagnostico }}</dd></div><div><dt>Componente / cantidad</dt><dd>{{ itemActivo.producto_requerido }} · {{ itemActivo.cantidad_requerida || 1 }}</dd></div><div><dt>Características</dt><dd>{{ itemActivo.especificacion_producto }}</dd></div><div><dt>Precio estimado</dt><dd>Bs. {{ itemActivo.costo_estimado || 'Sin especificar' }}</dd></div></dl>
        <div class="viabilidad-documentos"><article><i>IT</i><div><b>Informe técnico de requerimiento</b><small>Generado automáticamente con el diagnóstico y el requerimiento del técnico</small></div><button class="sia-primary" @click="abrirEvidencia(`${base}/${itemActivo.id}/informe-requerimiento-pdf/`,'Informe técnico de requerimiento')">Visualizar</button></article></div>
        <DecisionViabilidad v-model="decisionCompra" :validada="compraValidada" :ocupado="procesando" /><div v-if="compraValidada && decisionCompra==='si'" class="viabilidad-adjuntos"><label class="sia-field">POA<ArchivoInput type="file" accept=".pdf,.doc,.docx" @change="e=>formCompra.poa=e.target.files[0]" /></label><label class="sia-field">Proveído de jefatura<ArchivoInput type="file" accept=".pdf,.doc,.docx" @change="e=>formCompra.pedido=e.target.files[0]" /></label></div>
        <div class="expediente-actions"><button class="sia-primary" :disabled="procesando || !decisionCompra" @click="confirmarCompra(decisionCompra==='si')">{{ decisionCompra==='no' ? 'Continuar: compra no viable' : compraValidada ? 'Elevar expediente a Compras' : 'Confirmar viabilidad' }}</button></div>
      </section>
      <section v-if="itemActivo.informe_trabajo" class="expediente-action">
        <small>CIERRE TÉCNICO</small><h3>Informe del técnico de mantenimiento</h3><p class="informe-texto">{{ itemActivo.informe_trabajo }}</p>
        <dl class="viabilidad-datos"><div><dt>Diagnóstico</dt><dd>{{ itemActivo.diagnostico }}</dd></div><div><dt>Trabajo realizado</dt><dd>{{ itemActivo.trabajo_realizado }}</dd></div><div><dt>Pruebas técnicas</dt><dd>{{ itemActivo.resultado_pruebas }}</dd></div></dl>
        <div class="viabilidad-documentos"><article><i>PDF</i><div><b>Informe técnico del especialista</b><small>Documento con los datos y la firma registrada del técnico</small></div><button class="sia-primary" @click="visualizarInforme('Informe técnico de mantenimiento')">Abrir PDF</button></article><article v-if="itemActivo.fotografia_trabajo_url"><i>AN</i><div><b>Respaldo y cuadros técnicos</b><small>Adjunto registrado por el técnico</small></div><button class="sia-primary" @click="abrirEvidencia(itemActivo.fotografia_trabajo_url,'Respaldo y cuadros técnicos')">Visualizar</button></article></div>
        <p v-if="itemActivo.conformidad_solicitante!==true">Pendiente de conformidad del solicitante.</p><p v-else><b>Solicitante conforme:</b> {{ fecha(itemActivo.conformidad_solicitante_en) }}</p>
        <template v-if="itemActivo.conformidad_solicitante===true && ['INFORME_REGISTRADO','CONFORMIDAD_INFORMADA'].includes(itemActivo.estado_codigo)"><label class="sia-field">Informe final<textarea v-model="formInforme.informe_final" rows="5" placeholder="Registre el cierre del caso para Dirección"></textarea></label><div class="expediente-actions"><button class="sia-primary" :disabled="procesando || !formInforme.informe_final.trim()" @click="elaborarInforme">Validar y elevar informe</button></div></template>
        <template v-if="itemActivo.informe_final"><h3>Informe final validado</h3><p class="informe-texto">{{ itemActivo.informe_final }}</p><button class="sia-primary" @click="visualizarInforme('Informe final de mantenimiento')">Ver informe final</button></template>
      </section>
    </ExpedienteSolicitudModal>
    <div v-if="confirmacionCompra" class="asignacion-backdrop" @click.self="!procesando && (confirmacionCompra=null)"><section class="asignacion-confirm"><i>!</i><h3>{{ formCompra.viable ? (compraValidada ? 'Elevar expediente de compra' : 'Validar viabilidad de la compra') : 'Declarar compra no viable' }}</h3><p>{{ formCompra.viable ? (compraValidada ? 'Se elevará el expediente completo a la DAF.' : 'Se registrará la viabilidad y luego podrá adjuntar el POA y el proveído.') : 'El motivo será comunicado al técnico y el caso se cerrará sin compra.' }}</p><label v-if="!formCompra.viable" class="sia-field motivo-compra">Motivo de no viabilidad<textarea v-model="formCompra.motivo_no_viable" rows="4" placeholder="Explique por qué la compra no puede continuar…"></textarea></label><div class="expediente-actions"><button class="sia-secondary" :disabled="procesando" @click="confirmacionCompra=null">Cancelar</button><button class="sia-primary" :disabled="procesando || (!formCompra.viable && !formCompra.motivo_no_viable.trim())" @click="evaluarCompraUpload">Confirmar y notificar</button></div></section></div>
    <div v-if="confirmarAsignacion" class="asignacion-backdrop" @click.self="!procesando && (confirmarAsignacion=false)"><section class="asignacion-confirm"><i>!</i><h3>Confirmar asignación</h3><p>Se asignará la revisión al técnico seleccionado.</p><div class="asignacion-persona"><b>Técnico</b><span>{{ tecnicos.find(t=>String(t.id)===String(formDesignar.tecnico_id))?.nombre_completo }}</span></div><div class="expediente-actions"><button class="sia-secondary" :disabled="procesando" @click="confirmarAsignacion=false">Cancelar</button><button class="sia-primary" :disabled="procesando" @click="designar">Confirmar</button></div></section></div>
    <div v-if="visorEvidencia" class="mantenimiento-visor" @click.self="cerrarEvidencia"><section><header><button @click="cerrarEvidencia">← Volver al expediente</button><b>{{ visorTitulo }}</b><button aria-label="Cerrar" @click="cerrarEvidencia">×</button></header><div><img v-if="visorEsImagen" :src="visorEvidencia" alt="Evidencia del solicitante"><iframe v-else :src="visorEvidencia" title="Evidencia del solicitante" /></div></section></div>

    <!-- ============================ DETALLE ============================ -->
    <div v-if="detalle" class="detalle-modal-backdrop" @click.self="detalle=null">
      <div class="detalle-modal">
        <div class="detalle-modal-header">
          <div><h3>{{ detalle.codigo }}</h3><small>{{ detalle.titulo }}</small></div>
          <button class="detalle-modal-close" @click="detalle=null">✕</button>
        </div>
        <div class="detalle-modal-body">
          <div class="detalle-fila">
            <div class="detalle-campo"><b>Estado</b><span>{{ detalle.estado_nombre || detalle.estado_codigo }}</span></div>
            <div class="detalle-campo"><b>Prioridad</b><span>{{ detalle.prioridad_jefatura || 's/d' }}</span></div>
          </div>
          <div class="detalle-fila">
            <div class="detalle-campo"><b>Solicitante</b><span>{{ detalle.solicitante_nombre }}</span></div>
            <div class="detalle-campo"><b>Técnico</b><span>{{ detalle.auxiliar_nombre || 's/d' }}</span></div>
          </div>
          <div class="detalle-campo"><b>Descripción</b><p>{{ detalle.descripcion }}</p></div>
          <div class="detalle-campo"><b>Ubicación</b><span>{{ detalle.ubicacion || 's/d' }}</span></div>
          <div class="detalle-campo" v-if="detalle.motivo_rechazo"><b>Motivo del rechazo</b><p>{{ detalle.motivo_rechazo }}</p></div>
          <div class="detalle-campo" v-if="detalle.diagnostico"><b>Diagnóstico</b><p>{{ detalle.diagnostico }}</p></div>
          <div class="detalle-campo" v-if="detalle.plan_solucion"><b>Plan de solución</b><p>{{ detalle.plan_solucion }}</p></div>
          <div class="detalle-campo" v-if="detalle.producto_requerido"><b>Componente requerido</b><p>{{ detalle.producto_requerido }} — Bs. {{ detalle.costo_estimado || 's/d' }}</p></div>
          <div class="detalle-campo" v-if="proformaDe(detalle)"><b>Cotizaci&#243;n / proforma</b><button class="sia-primary" @click="abrirEvidencia(proformaDe(detalle),'Proforma del tecnico')">Ver proforma</button></div>
          <div class="detalle-campo" v-if="detalle.motivo_no_viable"><b>Compra no viable</b><p>{{ detalle.motivo_no_viable }}</p></div>
          <div class="detalle-campo" v-if="detalle.codigo_compra_vinculada"><b>Expediente de compra</b><span>{{ detalle.codigo_compra_vinculada }}</span></div>
          <div class="detalle-campo" v-if="detalle.trabajo_realizado"><b>Trabajo realizado</b><p>{{ detalle.trabajo_realizado }}</p></div>
          <div class="detalle-campo" v-if="detalle.resultado_pruebas"><b>Pruebas técnicas</b><p>{{ detalle.resultado_pruebas }}</p></div>
          <div class="detalle-campo" v-if="detalle.informe_trabajo"><b>Informe del técnico</b><p>{{ detalle.informe_trabajo }}</p></div>
          <div class="detalle-campo" v-if="detalle.informe_final"><b>Informe final</b><p>{{ detalle.informe_final }}</p></div>
          <div class="detalle-campo" v-if="detalle.evidencia_archivo_url"><b>Evidencia</b><a :href="detalle.evidencia_archivo_url" target="_blank">Abrir archivo →</a></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {reglas,cargarReglas} from '../utils/reglas'
import CotizacionesExpediente from '../components/CotizacionesExpediente.vue'
import { solicitarFirma } from '../utils/firma'
import DocumentosExpediente from '../components/DocumentosExpediente.vue'
import PrioridadSla from '../components/PrioridadSla.vue'
import DecisionViabilidad from '../components/DecisionViabilidad.vue'
import ExpedienteSolicitudModal from '../components/ExpedienteSolicitudModal.vue'
import ValidacionSolicitud from '../components/ValidacionSolicitud.vue'
import ResumenExpediente from '../components/ResumenExpediente.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import IconoSigta from '../components/IconoSigta.vue'
import LogoutModal from '../components/LogoutModal.vue'
import TarjetaGuardado from '../components/TarjetaGuardado.vue'
import { usarGuardado } from '../utils/guardado.js'

const router = useRouter()
const usuario = ref(JSON.parse(localStorage.getItem('sigta_usuario') || '{}'))
const vista = ref('gestion')
const menuAbierto = ref(false)
const items = ref([])
const tecnicos = ref([])
const cargando = ref(false)
const procesando = ref(false)
const errorCarga = ref('')
const itemActivo = ref(null)
const detalle = ref(null)
const expedienteAbierto=ref(false), confirmarAsignacion=ref(false), visorEvidencia=ref(''), visorEsImagen=ref(false), visorTitulo=ref('EVIDENCIA DEL SOLICITANTE'), confirmacionCompra=ref(null)
const prioridades=computed(()=>[{codigo:'BAJA',nombre:'Baja'},{codigo:'MEDIA',nombre:'Media'},{codigo:'ALTA',nombre:'Alta'},{codigo:'URGENTE',nombre:'Urgente'}].map(p=>({...p,horas:reglas.value?.sla_horas?.[p.codigo==='URGENTE'?'CRITICA':p.codigo]})))
const reporte = ref(null)

const nombre = computed(() => usuario.value.nombre || usuario.value.nombre_completo || 'Jefe de Mantenimiento')
const primerNombre = computed(() => nombre.value.split(' ')[0])
const iniciales = computed(() => nombre.value.split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase())
const saludo = computed(() => new Date().getHours() < 12 ? 'Buenos días' : new Date().getHours() < 19 ? 'Buenas tardes' : 'Buenas noches')

/* Bandejas del BPMN */
const porValidar = computed(() => items.value.filter(r => r.estado_codigo === 'RECIBIDO'))
const porClasificar = computed(() => items.value.filter(r => r.estado_codigo === 'VALIDADO' && !r.clasificado_en))
const porDesignar = computed(() => items.value.filter(r => r.estado_codigo === 'VALIDADO' && !!r.clasificado_en))
const ticketsGestion = computed(() => items.value.filter(r => ['RECIBIDO','VALIDADO','DERIVADO','EN_MANTENIMIENTO','EN_ESPERA_COMPRA','INFORME_REGISTRADO','CONFORMIDAD_INFORMADA'].includes(r.estado_codigo) && !r.informe_elevado_en))

/* Búsqueda, filtro y paginación de la bandeja de "Gestión de tickets" */
const busquedaTickets = ref('')
const filtroEstadoTickets = ref('TODOS')
const paginaTickets = ref(1)
const TICKETS_POR_PAGINA = 10

function etapaTicket(r) {
  if (r.estado_codigo === 'RECIBIDO') return 'RECIBIDO'
  if (!r.clasificado_en) return 'CLASIFICAR'
  return 'DESIGNAR'
}

const ticketsFiltrados = computed(() => {
  const texto = busquedaTickets.value.trim().toLowerCase()
  return ticketsGestion.value.filter(r => {
    if (filtroEstadoTickets.value !== 'TODOS' && etapaTicket(r) !== filtroEstadoTickets.value) return false
    if (!texto) return true
    return [r.codigo, r.titulo, r.solicitante_nombre].some(v => (v || '').toLowerCase().includes(texto))
  })
})

const totalPaginasTickets = computed(() => Math.max(1, Math.ceil(ticketsFiltrados.value.length / TICKETS_POR_PAGINA)))

const ticketsPaginados = computed(() => {
  const inicio = (paginaTickets.value - 1) * TICKETS_POR_PAGINA
  return ticketsFiltrados.value.slice(inicio, inicio + TICKETS_POR_PAGINA)
})

watch([busquedaTickets, filtroEstadoTickets], () => { paginaTickets.value = 1 })
watch(totalPaginasTickets, (total) => { if (paginaTickets.value > total) paginaTickets.value = total })

const porEvaluarCompra = computed(() => items.value.filter(r => (r.estado_compra_componente === 'SOLICITADA' || (r.estado_compra_componente==='VIABLE' && !r.derivado_compra) || r.compra_vinculada?.documentos_pendientes?.length)))
const porVerificar = computed(() => items.value.filter(r => r.estado_codigo === 'INFORME_REGISTRADO' && !r.verificado_en))
const porConformar = computed(() => items.value.filter(r => r.estado_codigo === 'INFORME_REGISTRADO' && !!r.verificado_en))
const porInformar = computed(() => items.value.filter(r => r.estado_codigo === 'CONFORMIDAD_INFORMADA' && !r.informe_elevado_en))
const pendientesInforme = computed(() => [...porVerificar.value, ...porConformar.value, ...porInformar.value])

/* Selector compacto de la bandeja de "Informes de los técnicos".
   Estado exclusivamente visual: controla el desplegable y filtra en
   memoria la MISMA lista `pendientesInforme`. No altera la carga de
   datos, la seleccion (`abrir`) ni el flujo de conformidad. */
const selectorInformeAbierto = ref(false)
const busquedaInforme = ref('')
const selectorTicketAbierto = ref(false)  /* solo abre/cierra el desplegable de Gestion de tickets */
const selectorCompraAbierto = ref(false)  /* solo abre/cierra el desplegable de Solicitar compra */
const busquedaCompra = ref('')

const comprasFiltradas = computed(() => {
  const texto = busquedaCompra.value.trim().toLowerCase()
  if (!texto) return porEvaluarCompra.value
  return porEvaluarCompra.value.filter(r =>
    [r.codigo, r.titulo, r.solicitante_nombre].some(v => (v || '').toLowerCase().includes(texto))
  )
})

const informesFiltrados = computed(() => {
  const texto = busquedaInforme.value.trim().toLowerCase()
  if (!texto) return items.value.filter(r=>!!r.informe_trabajo)
  return items.value.filter(r=>!!r.informe_trabajo).filter(r =>
    [r.codigo, r.titulo, r.solicitante_nombre].some(v => (v || '').toLowerCase().includes(texto))
  )
})

const columnasGestion=computed(()=>[
  {id:'validar',nombre:'Por validar',items:porValidar.value.filter(coincideBusqueda)},
  {id:'gestionar',nombre:'Por gestionar',items:[...porClasificar.value,...porDesignar.value].filter(coincideBusqueda)},
  {id:'atencion',nombre:'En atención',items:ticketsGestion.value.filter(r=>['DERIVADO','EN_MANTENIMIENTO','EN_ESPERA_COMPRA'].includes(r.estado_codigo)).filter(coincideBusqueda)},
  {id:'cerrar',nombre:'Por cerrar',items:pendientesInforme.value.filter(coincideBusqueda)},
])
function coincideBusqueda(r){const q=busquedaTickets.value.trim().toLowerCase();return !q || `${r.codigo} ${r.titulo} ${r.solicitante_nombre}`.toLowerCase().includes(q)}
const menu = computed(() => [
  { id: 'resumen', icono: 'inicio', nombre: 'Dashboard', color: '#F2C400' },
  { id: 'gestion', icono: 'tickets', nombre: 'Gestión de tickets', total: ticketsGestion.value.length, color: '#3E7BD6' },
  { id: 'compra', icono: 'compras', nombre: 'Solicitar compra', total: porEvaluarCompra.value.length, color: '#C79A1E' },
  { id: 'informe', icono: 'conformidad', nombre: 'Informes de los técnicos', total: pendientesInforme.value.length, color: '#7B6FD9' },
  { id: 'reporte', icono: 'reporte', nombre: 'Reporte mensual', color: '#D9538A' },
])

const titulo = computed(() => ({
  resumen: 'Dashboard del Jefe de Mantenimiento',
  gestion: 'Gestión de Tickets',
  compra: 'Recibir requerimiento y cotización',
  verificar: 'Verificar funcionamiento',
  informe: 'Conformidad e informe final',
  reporte: 'Reporte mensual',
}[vista.value]))

const subtitulo = computed(() => ({
  resumen: 'Validación, clasificación y seguimiento de los requerimientos de mantenimiento.',
  gestion: 'Validación, priorización y asignación de tickets en un solo flujo.',
  compra: 'Evalúe la viabilidad de los componentes solicitados por el técnico.',
  verificar: 'Confirme si la intervención resolvió el problema reportado.',
  informe: 'Cierre del caso y elevación del informe a la Dirección.',
  reporte: 'Consolidado mensual de mantenimientos finalizados.',
}[vista.value]))

const base = '/api/mantenimiento/requerimientos'
const token = () => localStorage.getItem('sigta_token')

async function cargar() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const r = await fetch(`${base}/`, { headers: { Authorization: `Token ${token()}` } })

    if (r.status === 401 || r.status === 403) {
      salir()
      return
    }

    if (!r.ok) {
      throw new Error('No fue posible cargar los requerimientos de mantenimiento.')
    }

    const d = await r.json()
    items.value = Array.isArray(d) ? d : (d.results || [])
    const rt = await fetch('/api/usuarios/usuarios-por-rol/?rol=AUXILIAR_SERVICIOS_GENERALES', {
      headers: { Authorization: `Token ${token()}` },
    })
    tecnicos.value = rt.ok ? await rt.json() : []
  } catch (e) {
    console.error('No fue posible cargar Mantenimiento.', e)
    errorCarga.value = e.message || 'No fue posible cargar los requerimientos. Intente actualizar nuevamente.'
  } finally {
    cargando.value = false
  }
}

async function postAccion(item, endpoint, body) {
  procesando.value = true
  try {
    const r = await fetch(`${base}/${item.id}/${endpoint}/`, {
      method: 'POST',
      headers: { Authorization: `Token ${token()}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.detalle || Object.values(d)[0] || 'No fue posible completar la acción.')
    await cargar()
    
    if ((vista.value === 'gestion' || vista.value === 'informe') && itemActivo.value) {
      const found = items.value.find(i => i.id === itemActivo.value.id);
      const permaneceEnGestion = vista.value === 'gestion'
        && ticketsGestion.value.some(r=>r.id===found?.id)
      const permaneceEnInforme = vista.value === 'informe'
        && ['INFORME_REGISTRADO','CONFORMIDAD_INFORMADA'].includes(found?.estado_codigo)
        && !found?.informe_elevado_en

      if (found && (permaneceEnGestion || permaneceEnInforme)) {
        itemActivo.value = found;
      } else {
        itemActivo.value = null;
      }
    } else if(itemActivo.value) {
      itemActivo.value=items.value.find(r=>r.id===itemActivo.value.id)||null;
    }
    
    return d
  } finally {
    procesando.value = false
  }
}

function irA(id) {
  vista.value = id
  menuAbierto.value = false
  itemActivo.value = null
}

function abrir(item) {
  decisionCompra.value = item.estado_compra_componente==='VIABLE'||item.compra_vinculada?'si':''
  itemActivo.value = item
  formClasificar.prioridad = item.prioridad_automatica || item.prioridad_jefatura || ''
  formClasificar.criterio_prioridad = ''
  formDesignar.tecnico_id = ''
  formCompra.viable = true
  formCompra.motivo_no_viable = ''
  formCompra.informe = item.informe_compra || item.compra_vinculada?.informe || null
  formCompra.proforma = item.cotizacion_archivo || item.compra_vinculada?.proforma || null
  formCompra.poa = null
  formCompra.pedido = null
  formInforme.informe_final = ''
}

function verItem(item) { if(item.estado_compra_componente==='SOLICITADA' || (item.estado_compra_componente==='VIABLE' && !item.derivado_compra) || item.compra_vinculada?.documentos_pendientes?.length){abrirCompra(item);return} if(item.informe_trabajo){abrirInforme(item);return} if(['RECIBIDO','VALIDADO'].includes(item.estado_codigo)){abrir(item);expedienteAbierto.value=true}else detalle.value=item }

function fecha(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' }) : 's/d'
}

const mostrarLogout = ref(false)
const { mostrar: mostrarGuardadoOk, texto: textoGuardado, tipo: tipoGuardado, animar: animarGuardado, animarError, ocultar: ocultarGuardado } = usarGuardado()

function salir() {
  localStorage.removeItem('sigta_token')
  localStorage.removeItem('sigta_usuario')
  router.push('/login')
}

function confirmarSalida() {
  mostrarLogout.value = false
  salir()
}

/* Acciones del flujo */
const validacionActiva = ref(null), errorValidacion = ref('')
function casosActivos(id) { return tecnicos.value.find(t=>Number(t.id)===Number(id))?.carga_activa || 0 }
async function validar(item) {
  try {
    await postAccion(item, 'validar-ticket', { es_valido: true })
    validacionActiva.value = null
    expedienteAbierto.value = true
  } catch (e) { await animarError(e.message) }
}

async function rechazar(item, motivo) {
  if (!motivo?.trim()) return
  try {
    await postAccion(item, 'validar-ticket', { es_valido: false, motivo_rechazo: motivo.trim() })
    validacionActiva.value = null
    expedienteAbierto.value = false
    await animarGuardado('Solicitud rechazada con motivo registrado.')
  } catch (e) { await animarError(e.message) }
}

const formClasificar = reactive({ prioridad: '', criterio_prioridad: '' })
async function clasificar() {
  try {
    await postAccion(itemActivo.value, 'clasificar-prioridad', {
      prioridad: formClasificar.prioridad,
      criterio_prioridad: formClasificar.criterio_prioridad.trim(),
    })
    await animarGuardado('Prioridad clasificada correctamente.')
  } catch (e) { await animarError(e.message) }
}

const formDesignar = reactive({ tecnico_id: '' })
async function designar() {
  try {
    await postAccion(itemActivo.value, 'designar-revision', { tecnico_id: Number(formDesignar.tecnico_id) })
    expedienteAbierto.value = false
    confirmarAsignacion.value = false
    await animarGuardado('Técnico asignado correctamente.')
  } catch (e) { await animarError(e.message) }
}

const decisionCompra=ref('')
const compraValidada=computed(()=>itemActivo.value?.estado_compra_componente==='VIABLE' || !!itemActivo.value?.compra_vinculada)
const informeCompra=computed(()=>itemActivo.value?.informe_compra || itemActivo.value?.compra_vinculada?.informe)
function proformaDe(item){return item?.cotizacion_archivo_url || item?.cotizacion_archivo || item?.compra_vinculada?.proforma}
const cotizacionCompra=computed(()=>proformaDe(itemActivo.value))
function abrirInforme(item){abrir(item);expedienteAbierto.value=true}
async function visualizarInforme(tipo){try{const r=await fetch(`${base}/${itemActivo.value.id}/documentos/`,{headers:{Authorization:`Token ${token()}`}});if(!r.ok)throw new Error('No se pudieron consultar los informes.');const docs=await r.json();const doc=[...docs].reverse().find(d=>d.tipo===tipo);if(!doc)throw new Error('Este expediente antiguo no tiene un PDF registrado. Puede consultar el texto del informe y sus adjuntos.');await abrirEvidencia(`${base}/${itemActivo.value.id}/documentos/${doc.id}/pdf/`,tipo)}catch(e){await animarError(e.message)}}
function abrirCompra(item){abrir(item);expedienteAbierto.value=true;confirmacionCompra.value=null}
async function confirmarCompra(viable){formCompra.viable=viable;formCompra.motivo_no_viable='';if(viable && compraValidada.value && (!formCompra.poa || !formCompra.pedido)){await animarError('Adjunte el POA y el proveído para elevar el expediente. El informe técnico y la cotización se incorporan automáticamente.');return}confirmacionCompra.value=viable?'validar':'rechazar'}
const formCompra = reactive({ viable: true, motivo_no_viable: '', informe: null, proforma: null, poa: null, pedido: null })

async function evaluarCompraUpload() {
  procesando.value = true
  try {
    if (formCompra.viable && compraValidada.value && (!formCompra.poa || !formCompra.pedido)) {
      throw new Error("Adjunte el POA y el proveído para elevar la compra.")
    }

    const fd = new FormData()
    fd.append("viable", formCompra.viable ? "true" : "false")
    if (!formCompra.viable) fd.append("motivo_no_viable", formCompra.motivo_no_viable.trim())
    
    if (formCompra.viable) {
      if (formCompra.poa instanceof File) fd.append("poa", formCompra.poa)
      if (formCompra.pedido instanceof File) fd.append("pedido", formCompra.pedido)
    }

    const validandoViabilidad=formCompra.viable && !compraValidada.value
    const id=itemActivo.value.id
    const r = await fetch(`${base}/${id}/${validandoViabilidad ? "validar-viabilidad-compra" : formCompra.viable && itemActivo.value.compra_vinculada?.documentos_pendientes?.length ? "completar-expediente" : "evaluar-viabilidad-compra"}/`, {
      method: 'POST',
      headers: { Authorization: `Token ${token()}` },
      body: fd,
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.detalle || Object.values(d)[0] || 'No fue posible completar la acción.')

    await cargar()
    confirmacionCompra.value=null
    if(validandoViabilidad){itemActivo.value=items.value.find(r=>r.id===id);formCompra.informe=itemActivo.value?.informe_compra;formCompra.proforma=itemActivo.value?.cotizacion_archivo;await animarGuardado('Viabilidad validada. Ahora adjunte el POA y el proveído.');return}
    expedienteAbierto.value=false
    await animarGuardado(d?.mensaje || 'Evaluación de compra registrada.')
    itemActivo.value = null
  } catch (e) { await animarError(e.message) }
  finally { procesando.value = false }
}

async function evaluarCompra() {
  try {
    const d = await postAccion(itemActivo.value, 'evaluar-viabilidad-compra', {
      viable: formCompra.viable,
      motivo_no_viable: formCompra.motivo_no_viable.trim(),
    })
    alert(d?.mensaje || 'Evaluación registrada.')
  } catch (e) { alert(e.message) }
}

const formInforme = reactive({ informe_final: '' })
async function elaborarInforme() {
  const firma = await solicitarFirma('Informe final de mantenimiento', itemActivo.value.codigo)
  if (!firma) return
  try {
    await postAccion(itemActivo.value, 'elaborar-informe-final', { informe_final: formInforme.informe_final.trim(), firma })
    await animarGuardado('Informe final validado y elevado a la Dirección.')
  } catch (e) { await animarError(e.message) }
}

const periodo = reactive({ anio: new Date().getFullYear(), mes: new Date().getMonth() + 1 })
async function cargarReporte() {
  procesando.value = true
  try {
    const r = await fetch(`${base}/reporte-mensual/?anio=${periodo.anio}&mes=${periodo.mes}`, {
      headers: { Authorization: `Token ${token()}` },
    })
    reporte.value = r.ok ? await r.json() : null
  } finally {
    procesando.value = false
  }
}

/* Derivados unicamente para la representacion visual del reporte.
   No consultan nada ni tocan el flujo Anio -> Mes -> Consultar: leen el
   mismo objeto `reporte` que ya dejo cargado cargarReporte(). */
const reportePorDia = computed(() => {
  const filas = reporte.value?.requerimientos || []
  const dias = reporte.value ? new Date(reporte.value.anio, reporte.value.mes, 0).getDate() : 0
  const conteo = new Array(dias).fill(0)
  filas.forEach(r => {
    const f = r.finalizado_en ? new Date(r.finalizado_en) : null
    if (f && !isNaN(f.getTime())) {
      const d = f.getDate()
      if (d >= 1 && d <= dias) conteo[d - 1] += 1
    }
  })
  return conteo.map((total, i) => ({ dia: i + 1, total }))
})

const reporteMaxDia = computed(() => Math.max(1, ...reportePorDia.value.map(d => d.total)))

let intervaloActualizacion = null

async function abrirEvidencia(url,titulo="Evidencia del solicitante"){try{const r=await fetch(url,{headers:{Authorization:`Token ${token()}`},cache:'no-store'});if(!r.ok)throw new Error('No se pudo visualizar la evidencia.');const archivo=await r.blob();cerrarEvidencia();visorEsImagen.value=archivo.type.startsWith('image/');visorEvidencia.value=URL.createObjectURL(archivo);visorTitulo.value=titulo.toUpperCase()}catch(e){await animarError(e.message)}}
function cerrarEvidencia(){if(visorEvidencia.value)URL.revokeObjectURL(visorEvidencia.value);visorEvidencia.value=''}
onMounted(() => {
  cargarReglas().catch(console.error)
  cargar()
  intervaloActualizacion = setInterval(cargar, 30000)
})

onUnmounted(() => {
  if (intervaloActualizacion) clearInterval(intervaloActualizacion)
})
</script>

<style scoped>
*{box-sizing:border-box}.layout{min-height:100vh;background:var(--sigta-fondo);color:var(--sigta-texto);font-family:var(--sigta-fuente)}aside{position:fixed;inset:0 auto 0 0;width:var(--sigta-sidebar);background:var(--sigta-azul);color:var(--sigta-blanco);padding:22px 16px;display:flex;flex-direction:column}.brand,.profile{display:flex;align-items:center;gap:12px}.brand{padding:0 10px 20px;border-bottom:1px solid rgba(255,255,255,.2)}.brand>b{background:var(--sigta-mostaza);color:var(--sigta-azul);padding:14px 10px;border-radius:9px}.brand strong,.brand small,.profile b,.profile small{display:block}.brand strong{font-size:23px}.brand small,.profile small{color:var(--sigta-azul-texto-claro);margin-top:3px}.profile{padding:22px 10px}.profile>i{width:42px;height:42px;border-radius:50%;background:var(--sigta-mostaza);color:var(--sigta-azul);display:grid;place-items:center;font-style:normal;font-weight:900}aside>p{font-size:10px;color:var(--sigta-azul-texto-claro);font-weight:800;letter-spacing:1.4px;margin:14px 10px 8px}aside button{border:0;background:transparent;color:var(--sigta-blanco);border-radius:8px;padding:12px;display:flex;gap:11px;align-items:center;text-align:left;cursor:pointer;margin:2px 0;width:100%}aside button .icon-badge{flex-shrink:0;width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center}aside button em{margin-left:auto;background:rgba(255,255,255,.16);padding:2px 8px;border-radius:10px;font-style:normal}aside button.active,aside button:hover{background:rgba(255,255,255,.13)}.bottom{margin-top:auto;border-top:1px solid rgba(255,255,255,.2);padding-top:10px}.bottom button{width:100%}.bottom .logout{gap:14px!important;border:1px solid var(--sigta-mostaza)!important;border-radius:8px!important;background:transparent!important;color:#fff!important;box-shadow:inset 0 0 0 1px rgba(255,199,44,.35)!important;transition:transform .3s cubic-bezier(.34,1.55,.5,1),background .2s ease,color .2s ease,box-shadow .2s ease!important}.bottom .logout .icono-sigta{color:var(--sigta-mostaza);transition:color .2s ease}.bottom .logout:hover{background:#FFB300!important;color:var(--sigta-azul)!important;transform:scale(1.09)!important;box-shadow:0 14px 32px rgba(255,159,0,.55)!important}.bottom .logout:hover .icono-sigta{color:var(--sigta-azul)}main{margin-left:var(--sigta-sidebar);padding:30px 38px 55px;max-width:1650px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:27px}header small{color:var(--sigta-texto-suave)}h1{font-size:var(--sigta-titulo);margin:6px 0}header p{margin:0;color:var(--sigta-texto-suave)}.refresh{border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-azul);padding:10px 14px;border-radius:8px;cursor:pointer}.hero{background:linear-gradient(120deg,var(--sigta-azul),var(--sigta-azul-medio));color:var(--sigta-blanco);border-radius:13px;padding:28px 30px;display:flex;justify-content:space-between;align-items:center}.hero small,.panel-head small{font-size:10px;font-weight:800;letter-spacing:1.4px;color:var(--sigta-mostaza-clara)}.hero h2{font-size:24px;margin:7px 0}.hero p{margin:0;color:var(--sigta-azul-texto-claro)}.hero>span{width:68px;height:68px;border:1px solid var(--sigta-mostaza);border-radius:50%;display:grid;place-items:center;font-weight:900}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:18px 0}.stats article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:19px;display:flex;gap:13px;cursor:pointer}.stats i,.flow i{font-style:normal;width:37px;height:37px;border-radius:8px;display:grid;place-items:center;color:var(--sigta-blanco);font-size:10px;font-weight:900}.blue{background:var(--sigta-azul)}.gold{background:var(--sigta-mostaza);color:var(--sigta-texto)!important}.green{background:var(--sigta-azul-medio)}.navy{background:var(--sigta-azul-medio)}.stats small,.stats b,.stats p{display:block}.stats b{font-size:25px;margin:3px 0}.stats p{font-size:11px;color:var(--sigta-texto-suave);margin:0}.panels{display:grid;grid-template-columns:2fr 1fr;gap:18px}.panel{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:11px;padding:22px}.panel-head h3{margin:5px 0 14px}.flow{width:100%;border:0;border-top:1px solid var(--sigta-borde-suave);background:var(--sigta-blanco);padding:15px 2px;display:flex;gap:13px;align-items:center;text-align:left;cursor:pointer}.flow div{flex:1}.flow b,.flow small{display:block}.flow small{color:var(--sigta-texto-suave);margin-top:4px}.flow>strong{font-size:20px}.copy{color:var(--sigta-texto-suave);font-size:12px;line-height:1.7}.wide{width:100%;padding:10px;border-radius:7px;border:1px solid var(--sigta-borde);cursor:pointer}.primary{background:var(--sigta-azul)!important;color:var(--sigta-blanco)!important;border-color:var(--sigta-azul)!important}.instruction{background:var(--sigta-mostaza-suave);border-left:4px solid var(--sigta-mostaza);padding:14px 17px;margin-bottom:17px;border-radius:7px}.instruction b,.instruction span{display:block}.instruction span{font-size:12px;color:var(--sigta-alerta);margin-top:4px}.mini-alerta{background:var(--sigta-error-fondo);color:var(--sigta-error);font-size:11px;font-weight:700;padding:7px 9px;border-radius:6px;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px}.cards article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:19px}.cards article.retorno{border-color:var(--sigta-error);box-shadow:inset 3px 0 var(--sigta-error)}.top{display:flex;justify-content:space-between;gap:8px}.top span{font-size:12px;font-weight:800;color:var(--sigta-azul)}.top em{font-size:10px;background:var(--sigta-azul-tenue);padding:4px 8px;border-radius:10px;font-style:normal}.cards h3{font-size:17px;margin:15px 0 7px}.cards article>p{font-size:12px;color:var(--sigta-texto-suave);min-height:42px}.datos{list-style:none;margin:0 0 10px;padding:0;display:grid;gap:4px}.datos li{display:flex;justify-content:space-between;gap:10px;font-size:11px;border-bottom:1px dashed var(--sigta-borde-suave);padding-bottom:3px}.datos b{color:var(--sigta-texto-suave)}.datos span{color:var(--sigta-texto-suave);text-align:right}.adjunto{display:inline-block;font-size:11px;color:var(--sigta-azul);margin-bottom:10px;text-decoration:none}.actions{display:flex;gap:7px;border-top:1px solid var(--sigta-borde-suave);padding-top:13px;margin-top:10px;align-items:flex-end}.actions button{flex:1;padding:9px 6px;border-radius:7px;border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-texto);font-weight:700;cursor:pointer}.actions button:disabled{opacity:.55;cursor:not-allowed}.reject{color:var(--sigta-error)!important;border-color:var(--sigta-error)!important}.empty{text-align:center;background:var(--sigta-blanco);border:1px dashed var(--sigta-borde);padding:65px;border-radius:10px;color:var(--sigta-texto-suave)}.empty>span{font-size:31px;color:var(--sigta-exito)}.campo{display:block;margin:14px 0;font-size:12px;font-weight:700;color:var(--sigta-texto)}.campo input,.campo select,.campo textarea{display:block;width:100%;margin-top:6px;padding:9px 11px;border:1px solid var(--sigta-borde);border-radius:7px;font-family:inherit;font-size:13px;font-weight:400;color:var(--sigta-texto)}.reporte-item{padding:9px 0;border-top:1px solid var(--sigta-borde-suave);font-size:13px}.detalle-modal-backdrop{position:fixed;inset:0;background:rgba(18,58,107,.55);display:grid;place-items:center;padding:20px;z-index:20}.detalle-modal{background:var(--sigta-blanco);border-radius:14px;width:min(700px,100%);max-height:88vh;display:flex;flex-direction:column}.detalle-modal-header{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--sigta-borde-suave)}.detalle-modal-header h3{margin:0}.detalle-modal-header small{color:var(--sigta-texto-suave)}.detalle-modal-close{border:0;background:transparent;font-size:20px;cursor:pointer;color:var(--sigta-texto-suave)}.detalle-modal-body{padding:20px 24px;overflow-y:auto;display:grid;gap:14px}.detalle-fila{display:grid;grid-template-columns:1fr 1fr;gap:14px}.detalle-campo b{display:block;font-size:11px;color:var(--sigta-texto-suave);margin-bottom:4px}.detalle-campo span,.detalle-campo p{font-size:13px;color:var(--sigta-texto);margin:0}

/* ====== MARCA DE AGUA DEL SIDEBAR ====== */
.sidebar-watermark { flex: 1; min-height: 90px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 8px; padding: 10px 0 4px; }
.sidebar-watermark img { width: 65%; max-width: 130px; max-height: 110px; object-fit: contain; opacity: .15; }
.wm-text { text-align: center; opacity: .55; }
.wm-text b { display: block; font-size: 12px; letter-spacing: 1.4px; }
.wm-text span { display: block; margin-top: 3px; color: var(--sigta-azul-texto-claro); font-size: 9.5px; line-height: 1.3; }
.wm-text small { display: block; margin-top: 2px; color: var(--sigta-azul-texto-claro); font-size: 9px; font-style: italic; }

/* ====== TARJETAS NUMERADAS DEL PROCESO ====== */
.process-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 4px; }
.process-card { display: flex; gap: 12px; align-items: flex-start; text-align: left; width: 100%; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-top: 4px solid var(--sigta-azul); border-radius: 10px; padding: 15px; cursor: pointer; transition: box-shadow .2s, transform .2s; }
.process-card:hover { box-shadow: 0 6px 16px rgba(0,0,0,.08); transform: translateY(-1px); }
.process-num { flex-shrink: 0; width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 900; }
.process-card div { flex: 1; }
.process-card b { display: block; color: var(--sigta-texto); font-size: 13.5px; }
.process-card small { display: block; color: var(--sigta-texto-suave); font-size: 11.5px; margin-top: 3px; line-height: 1.4; }

/* ====== NUEVOS ESTILOS: GESTIÓN DE TICKETS ====== */
.gestion-tickets-layout { display: flex; gap: 20px; height: calc(100vh - 160px); overflow: hidden; align-items: stretch; }
.gestion-left { width: 35%; display: flex; flex-direction: column; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; overflow: hidden; }
.gestion-left-header { padding: 15px 20px; border-bottom: 1px solid var(--sigta-borde-suave); display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.gestion-left-header h3 { margin: 0; font-size: 14px; color: var(--sigta-texto); }
.badge { background: #e0e7ff; color: var(--sigta-azul); font-size: 11px; padding: 4px 8px; border-radius: 20px; font-weight: bold; }
.gestion-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; padding: 14px 14px 0; }
.g-stat { display: flex; align-items: center; gap: 8px; background: #f8fafc; border: 1px solid var(--sigta-borde-suave); border-radius: 8px; padding: 8px 10px; }
.g-stat i.badge { flex-shrink: 0; width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; padding: 0; }
.g-stat small { display: block; font-size: 9.5px; color: var(--sigta-texto-suave); }
.g-stat b { display: block; font-size: 16px; color: var(--sigta-texto); }
.gestion-filtros { display: flex; flex-direction: column; gap: 8px; padding: 12px 14px; border-bottom: 1px solid var(--sigta-borde-suave); }
.g-buscar { display: flex; align-items: center; gap: 8px; border: 1px solid var(--sigta-borde); border-radius: 8px; padding: 8px 10px; color: var(--sigta-texto-suave); }
.g-buscar input { border: 0; outline: none; flex: 1; font-size: 12.5px; font-family: inherit; color: var(--sigta-texto); }
.gestion-filtros select { border: 1px solid var(--sigta-borde); border-radius: 8px; padding: 8px 10px; font-size: 12.5px; font-family: inherit; color: var(--sigta-texto); background: var(--sigta-blanco); }
.gestion-lista { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
.gestion-paginacion { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 10px; border-top: 1px solid var(--sigta-borde-suave); font-size: 12px; color: var(--sigta-texto-suave); }
.gestion-paginacion button { width: 28px; height: 28px; border-radius: 6px; border: 1px solid var(--sigta-borde); background: var(--sigta-blanco); cursor: pointer; font-size: 14px; }
.gestion-paginacion button:disabled { opacity: .4; cursor: not-allowed; }
.ticket-item { padding: 14px; border: 1px solid var(--sigta-borde-suave); border-radius: 8px; cursor: pointer; transition: all 0.2s; background: var(--sigta-blanco); }
.ticket-item:hover { border-color: var(--sigta-borde); box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
.ticket-item.activo { border-color: var(--sigta-azul); background: #f8fafc; }
.ticket-item.t-validar { border-left: 4px solid var(--sigta-error); }
.ticket-item.t-clasificar { border-left: 4px solid var(--sigta-mostaza); }
.ticket-item.t-designar { border-left: 4px solid var(--sigta-azul); }
.ticket-item h4 { margin: 8px 0 4px; font-size: 14px; color: var(--sigta-texto); }
.ticket-item p { margin: 0; font-size: 11px; color: var(--sigta-texto-suave); }
.e-validar { background: #fee2e2; color: #b91c1c; }
.e-clasificar { background: #fef3c7; color: #b45309; }
.e-designar { background: #e0e7ff; color: #4338ca; }
.empty-list { text-align: center; padding: 30px; font-size: 12px; color: var(--sigta-texto-suave); }

.gestion-right { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.gestion-detalle-wrapper { display: flex; flex-direction: column; gap: 15px; height: 100%; }
.ticket-header-card { background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; padding: 24px; flex-shrink: 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.t-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.t-head h2 { margin: 0; font-size: 20px; color: var(--sigta-azul); font-weight: 800; }
.codigo-badge { font-weight: bold; color: var(--sigta-texto-suave); font-size: 13px; background: #f1f5f9; padding: 4px 10px; border-radius: 6px; }
.t-meta { display: flex; gap: 16px; margin: 0 0 20px; font-size: 13px; color: var(--sigta-texto-suave); }
.t-meta span { display: flex; align-items: center; gap: 5px; }
.t-meta b { color: var(--sigta-texto); }

.t-content { display: flex; flex-direction: column; gap: 12px; }
.desc-box { background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid var(--sigta-borde-suave); }
.desc-box strong { display: block; font-size: 11px; color: var(--sigta-texto-suave); text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px; font-weight: bold; }
.desc-box p { margin: 0; font-size: 14px; line-height: 1.5; color: var(--sigta-texto); }

.evidence-box { display: flex; justify-content: space-between; align-items: center; background: #e0e7ff; border: 1px solid #c7d2fe; padding: 12px 16px; border-radius: 8px; }
.evidence-info strong { display: block; font-size: 13px; color: var(--sigta-azul); font-weight: bold; margin-bottom: 2px; }
.evidence-info span { font-size: 11px; color: #4338ca; }
.evidence-btn { background: var(--sigta-azul); color: var(--sigta-blanco); text-decoration: none; font-size: 12px; font-weight: bold; padding: 8px 16px; border-radius: 6px; transition: opacity 0.2s; white-space: nowrap; }
.evidence-btn:hover { opacity: 0.9; }

.workflow-card { flex: 1; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; }
.wf-header { padding: 15px 20px; border-bottom: 1px solid var(--sigta-borde-suave); font-weight: bold; color: var(--sigta-texto); background: #f8fafc; }
.wf-body { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; position: relative; }
.wf-body::before { content: ''; position: absolute; left: 45px; top: 35px; bottom: 35px; width: 2px; background: var(--sigta-borde-suave); z-index: 1; }

.wf-step { display: flex; margin-bottom: 30px; position: relative; z-index: 2; }
.wf-step:last-child { margin-bottom: 0; }
.step-num { width: 42px; height: 42px; border-radius: 50%; background: var(--sigta-borde); color: var(--sigta-texto-suave); display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; border: 4px solid var(--sigta-blanco); transition: all 0.3s; }
.step-content { margin-left: 20px; flex: 1; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 10px; padding: 15px 20px; transition: all 0.3s; }
.step-content h4 { margin: 0 0 5px; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }
.step-content p { margin: 0 0 15px; font-size: 12px; color: var(--sigta-texto-suave); }
.step-badge { font-size: 10px; text-transform: uppercase; background: #f0fdf4; color: #166534; padding: 3px 8px; border-radius: 10px; }

.wf-step.active .step-num { background: var(--sigta-azul); color: var(--sigta-blanco); box-shadow: 0 0 0 4px rgba(0, 42, 92, 0.1); }
.wf-step.active .step-content { border-color: var(--sigta-azul); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.wf-step.locked { opacity: 0.5; pointer-events: none; }
.wf-step.locked .step-content { background: #f8fafc; }
.wf-step.completed .step-num { background: var(--sigta-azul-medio); color: var(--sigta-blanco); }
.wf-step.completed .step-content { border-color: var(--sigta-borde-suave); background: #f8fafc; }

.step-actions { display: flex; gap: 10px; }
.flex-btn { flex: 1; text-align: center; justify-content: center; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; border: none; }
.reject { background: var(--sigta-blanco); border: 1px solid var(--sigta-error); color: var(--sigta-error); padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; }
.p-options { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 15px; }
.p-options label { border: 1px solid var(--sigta-borde); border-radius: 6px; padding: 8px; text-align: center; font-size: 12px; font-weight: bold; cursor: pointer; color: var(--sigta-texto-suave); }
.p-options label:has(input:checked) { background: #e0e7ff; border-color: var(--sigta-azul); color: var(--sigta-azul); }
.p-options input { display: none; }
textarea { width: 100%; border: 1px solid var(--sigta-borde); border-radius: 6px; padding: 10px; font-family: inherit; font-size: 13px; resize: vertical; margin-bottom: 15px; }
.full-select { width: 100%; border: 1px solid var(--sigta-borde); border-radius: 6px; padding: 10px; font-family: inherit; font-size: 13px; color: var(--sigta-texto); background: #fff; margin-bottom: 15px; }
.step-btn { width: 100%; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; border: none; background: var(--sigta-azul); color: var(--sigta-blanco); font-size: 14px; text-align: center; }
.load-error { margin: -10px 0 18px; padding: 12px 14px; border-left: 4px solid var(--sigta-error); border-radius: 7px; background: var(--sigta-error-fondo); color: var(--sigta-error); font-size: 13px; font-weight: 700; }

@media(max-width:1050px){.stats{grid-template-columns:1fr 1fr}.panels{grid-template-columns:1fr}.cards{grid-template-columns:1fr 1fr}.gestion-tickets-layout{flex-direction:column;height:auto}.gestion-left{width:100%;height:300px}}@media(max-width:760px){aside{position:static;width:100%}main{margin:0;padding:20px}.stats,.cards,.process-grid{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column;gap:12px}.detalle-fila{grid-template-columns:1fr}.p-options{grid-template-columns:1fr 1fr}}

/* ==================================================================
   AJUSTE VISUAL COMPARTIDO - PANTALLAS MAESTRO-DETALLE
   Alcance: .vista-compacta (Gestion de tickets, Solicitar compra,
   Informes de los tecnicos). Ninguna regla toca las clases base,
   de modo que las demas vistas y dashboards quedan igual que antes.
   Filosofia: listado secundario compacto -> contenido principal
   protagonista -> menos espacio muerto y menos scroll.
   ================================================================== */

/* ---------- 1. PANEL IZQUIERDO (listado secundario) ---------- */
.vista-compacta .gestion-left { width: 27%; min-width: 250px; }
.vista-compacta .gestion-left-header { padding: 11px 15px; }
.vista-compacta .gestion-lista { padding: 8px; gap: 6px; }
.vista-compacta .ticket-item { padding: 9px 11px; }
.vista-compacta .ticket-item .top span { font-size: 11px; }
.vista-compacta .ticket-item .top em { font-size: 9px; padding: 3px 7px; }
.vista-compacta .ticket-item h4 { margin: 4px 0 2px; font-size: 12.5px; line-height: 1.3; }
.vista-compacta .ticket-item p { font-size: 10.5px; line-height: 1.35; }
.vista-compacta .empty-list { padding: 18px 14px; }
.vista-compacta .gestion-paginacion { padding: 7px 10px; font-size: 11px; }
.vista-compacta .gestion-paginacion button { width: 24px; height: 24px; font-size: 13px; }

/* ---------- 2. CABECERA DEL ELEMENTO (resumen compacto) ---------- */
.vista-compacta .gestion-detalle-wrapper { gap: 12px; }
.vista-compacta .ticket-header-card { padding: 14px 18px; }
.vista-compacta .t-head { margin-bottom: 6px; }
.vista-compacta .t-head h2 { font-size: 17px; }
.vista-compacta .codigo-badge { font-size: 12px; padding: 3px 9px; }
.vista-compacta .t-meta { margin: 0 0 10px; font-size: 12px; flex-wrap: wrap; row-gap: 4px; }
.vista-compacta .t-content { gap: 10px; }
.vista-compacta .desc-box { padding: 10px 14px; }
.vista-compacta .desc-box strong { margin-bottom: 4px; }
.vista-compacta .desc-box p { font-size: 12.5px; line-height: 1.45; }
.vista-compacta .evidence-box { padding: 9px 14px; }
.vista-compacta .evidence-btn { padding: 7px 13px; }

/* ---------- 3. TARJETA DE FLUJO (contenido principal) ---------- */
.vista-compacta .workflow-card { box-shadow: 0 6px 18px rgba(0,0,0,.07); }
.vista-compacta .wf-header { display: flex; align-items: center; gap: 10px; padding: 12px 18px; font-size: 14.5px; color: var(--sigta-azul); }
.vista-compacta .wf-header::before { content: ''; width: 4px; height: 17px; border-radius: 3px; background: var(--sigta-mostaza); flex-shrink: 0; }
.vista-compacta .wf-body { padding: 16px 18px; }
.vista-compacta .wf-body::before { left: 34px; top: 26px; bottom: 26px; }
.vista-compacta .wf-step { margin-bottom: 12px; }
.vista-compacta .step-num { width: 32px; height: 32px; font-size: 13px; border-width: 3px; }
.vista-compacta .step-content { margin-left: 14px; padding: 11px 14px; }
.vista-compacta .step-content h4 { margin: 0 0 3px; font-size: 14px; gap: 10px; }
.vista-compacta .step-content p { margin: 0 0 8px; font-size: 11.5px; line-height: 1.4; }
.vista-compacta .step-badge { font-size: 9.5px; padding: 3px 7px; }
.vista-compacta .adjunto { margin-bottom: 6px; }
.vista-compacta .campo { margin: 8px 0; }
.vista-compacta .step-content input[type=file] { width: 100%; margin-top: 6px; padding: 7px 9px; font-size: 11.5px; font-family: inherit; color: var(--sigta-texto-suave); background: #f8fafc; border: 1px dashed var(--sigta-borde); border-radius: 7px; cursor: pointer; }
.vista-compacta .step-content textarea { margin-bottom: 10px; font-size: 12.5px; }
.vista-compacta .step-content .full-select { margin-bottom: 10px; padding: 8px 10px; font-size: 12.5px; }
.vista-compacta .step-btn { padding: 10px; font-size: 13px; }
.vista-compacta .p-options { gap: 8px; margin-bottom: 10px; }
.vista-compacta .p-options label { padding: 7px 6px; font-size: 11.5px; }

/* ---------- 4. AJUSTES PROPIOS DE CADA SECCION ---------- */

/* Gestion de tickets: cabecera del panel izquierdo mas densa
   para que la lista gane la altura que sobraba */
.vista-gestion .gestion-stats { gap: 6px; padding: 10px 10px 0; }
.vista-gestion .g-stat { padding: 6px 8px; gap: 7px; }
.vista-gestion .g-stat i.badge { width: 24px; height: 24px; border-radius: 6px; }
.vista-gestion .g-stat b { font-size: 14px; }
.vista-gestion .gestion-filtros { gap: 6px; padding: 9px 10px; }
.vista-gestion .g-buscar { padding: 6px 9px; }
.vista-gestion .g-buscar input,
.vista-gestion .gestion-filtros select { font-size: 11.5px; }
.vista-gestion .gestion-filtros select { padding: 6px 9px; }

/* Solicitar compra: los 4 datos del componente en fila,
   aprovechando el ancho en lugar de apilarse */
.vista-compra .desc-box { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 5px 18px; }
.vista-compra .desc-box strong { grid-column: 1 / -1; }

/* Informes de los tecnicos: dos columnas.
   Izquierda = selector compacto + informacion. Derecha = flujo.
   El desplegable se superpone, por eso la fila permite overflow. */
.vista-informe { height: calc(100vh - 232px); min-height: 460px; overflow: visible; gap: 16px; }
.vista-informe .informe-col-izq { width: 47%; min-width: 320px; display: flex; flex-direction: column; gap: 12px; overflow: visible; }
.vista-informe .informe-col-der { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
.vista-informe .informe-col-izq .ticket-header-card { flex: 1; min-height: 0; overflow-y: auto; }
.vista-informe .informe-col-izq .empty,
.vista-informe .informe-col-der .empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; margin: 0; }
.vista-informe .informe-col-der .workflow-card { flex: 1; min-height: 0; }
.vista-informe .desc-box strong + p { margin-bottom: 8px; }
.vista-informe .desc-box strong ~ strong { margin-top: 4px; display: block; }
/* La tarjeta de flujo tiene dos .wf-body hermanos: el bloque de
   revision y el de los pasos. La regla base da flex:1 a los dos, asi
   que se repartian la altura a medias y el primero (titulo + dos
   botones) dejaba un hueco enorme. Aqui el bloque de revision pasa a
   ocupar solo lo que mide su contenido y los pasos se quedan con el
   resto; la linea guia vertical tampoco se dibuja en ese bloque. */
.vista-informe .wf-body:not(:last-child) { flex: 0 0 auto; overflow: visible; padding-bottom: 14px; border-bottom: 1px solid var(--sigta-borde-suave); }
.vista-informe .wf-body:not(:last-child)::before { content: none; }
.vista-informe .wf-body:last-child { padding-top: 14px; }
.vista-informe .wf-body .actions { margin-top: 0; padding-top: 10px; gap: 10px; }
.vista-informe .wf-body > h4 { margin: 0 0 4px; font-size: 14px; }
.vista-informe .wf-body .actions button { padding: 10px 6px; }

/* Selector compacto de informe */
.selector-informe { position: relative; flex-shrink: 0; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 10px; padding: 10px 12px; }
.selector-label { display: block; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: var(--sigta-texto-suave); margin-bottom: 6px; }
.selector-trigger { display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; padding: 9px 12px; font-family: inherit; font-size: 13px; color: var(--sigta-texto); background: #f8fafc; border: 1px solid var(--sigta-borde); border-radius: 8px; cursor: pointer; }
.selector-trigger:hover { border-color: var(--sigta-azul); }
.selector-valor { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.selector-valor b { color: var(--sigta-azul); }
.selector-valor.vacio { color: var(--sigta-texto-suave); }
.selector-flecha { font-style: normal; color: var(--sigta-texto-suave); transition: transform .2s; }
.selector-flecha.abierta { transform: rotate(180deg); }
.selector-panel { position: absolute; z-index: 15; top: calc(100% - 2px); left: 12px; right: 12px; max-height: 320px; display: flex; flex-direction: column; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 10px; box-shadow: 0 12px 28px rgba(18,58,107,.16); overflow: hidden; }
.selector-panel .g-buscar { margin: 10px 10px 8px; padding: 7px 10px; }
.selector-panel .g-buscar input { font-size: 12px; }
.selector-cabecera { display: grid; grid-template-columns: 105px 1fr 88px; gap: 8px; padding: 7px 12px; font-size: 9.5px; font-weight: 800; letter-spacing: .6px; text-transform: uppercase; color: var(--sigta-texto-suave); background: #f8fafc; border-top: 1px solid var(--sigta-borde-suave); border-bottom: 1px solid var(--sigta-borde-suave); }
.selector-lista { overflow-y: auto; padding: 4px; }
.selector-fila { display: grid; grid-template-columns: 105px 1fr 88px; gap: 8px; align-items: center; width: 100%; text-align: left; padding: 8px 8px; font-family: inherit; background: transparent; border: 0; border-radius: 7px; cursor: pointer; }
.selector-fila:hover { background: #f1f5f9; }
.selector-fila.activo { background: var(--sigta-azul-tenue); }
.selector-fila .c-codigo { font-size: 11.5px; font-weight: 800; color: var(--sigta-azul); }
.selector-fila .c-titulo { font-size: 12.5px; color: var(--sigta-texto); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.selector-fila em { font-size: 9px; font-style: normal; text-align: center; padding: 3px 6px; border-radius: 10px; line-height: 1.3; }
.selector-panel .empty-list { padding: 16px 12px; }

/* ---------- 5. ESPACIO SOBRANTE EN GESTION DE TICKETS Y SOLICITAR COMPRA ----------
   Dos causas detectadas, ambas de estilo:
   a) .gestion-left se estiraba a toda la altura de la fila (align-items:
      stretch) aunque la bandeja tuviera cuatro tarjetas, dejando una caja
      blanca casi vacia. Ahora mide lo que mide su contenido y solo llega
      al tope -conservando su scroll interno- cuando hay muchos elementos.
   b) el estado vacio era una caja con 65px de relleno pegada al borde
      superior; ahora se centra y ocupa la columna de forma natural.
   La tarjeta de flujo mantiene su flex:1 a proposito: es lo que permite
   que .wf-body haga scroll cuando el expediente tiene muchos pasos. */
.vista-gestion .gestion-right > .empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 28px; margin: 0; }

/* Solicitar compra: mismo patron que Informes de los tecnicos.
   Izquierda = selector compacto + detalles del componente.
   Derecha = armado del expediente, protagonista a toda la altura. */
.vista-compra { overflow: visible; gap: 16px; }
.vista-compra .compra-col-izq { width: 42%; min-width: 320px; display: flex; flex-direction: column; gap: 12px; overflow: visible; }
.vista-compra .compra-col-der { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
.vista-compra .compra-col-izq .ticket-header-card { flex: 0 1 auto; min-height: 0; overflow-y: auto; }
.vista-compra .compra-col-der .workflow-card { flex: 1; min-height: 0; }
.vista-compra .compra-col-der > .empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 28px; margin: 0; }
.selector-compra .selector-encabezado { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 6px; }
.selector-compra .selector-label { margin-bottom: 0; }
.selector-compra .selector-cabecera,
.selector-compra .selector-fila { grid-template-columns: 105px 1fr 84px; }
.selector-compra .selector-fila { align-items: start; }
.selector-compra .c-titulo { display: block; overflow: hidden; }
.selector-compra .c-titulo b { display: block; font-size: 12.5px; color: var(--sigta-texto); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.selector-compra .c-titulo small { display: block; margin-top: 2px; font-size: 10.5px; color: var(--sigta-texto-suave); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.selector-compra .selector-fila em { align-self: center; }

/* Gestion de tickets: la informacion del ticket pasa a la columna
   izquierda, debajo de la bandeja, y la consola se queda sola a la
   derecha ocupando toda la altura disponible.
   La bandeja mide lo que mide su contenido y se topa al 52% cuando hay
   muchos tickets (su scroll interno es el de .gestion-lista, intacto);
   la informacion toma el resto con scroll propio. */
.vista-gestion .gestion-col-izq { width: 40%; min-width: 330px; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
.vista-gestion .gestion-col-izq .gestion-left { width: 100%; min-width: 0; align-self: stretch; flex: 0 0 auto; max-height: none; }
.vista-gestion .gestion-resumen .gestion-stats { padding: 10px; }

/* Selector de ticket: mismo componente visual que el de informes, con
   el buscador y el <select> de estados existentes dentro del panel. */
.selector-ticket .selector-panel { max-height: 430px; }

/* Unidad de busqueda + filtro + seleccion de ticket: un solo bloque.
   El buscador y el <select> de estados conservan su markup; solo pasan
   a compartir contenedor con el selector, y el panel desplegable deja
   de flotar para quedar pegado al disparador. */
.bloque-seleccion { flex: 0 0 auto; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; }
.bloque-seleccion .gestion-filtros { padding: 12px 12px 11px; border-bottom: 1px solid var(--sigta-borde-suave); }
.bloque-seleccion .selector-informe { border: 0; border-radius: 0; padding: 11px 12px 12px; background: transparent; }
.bloque-seleccion .selector-trigger.abierto { border-color: var(--sigta-azul); border-bottom-color: var(--sigta-borde); border-radius: 8px 8px 0 0; }
.bloque-seleccion .selector-panel { position: static; margin-top: -1px; max-height: 330px; border-radius: 0 0 8px 8px; box-shadow: none; }
.bloque-seleccion .selector-panel .selector-cabecera { border-top: 0; }
/* el buscador y el filtro de estados viven dentro del desplegable,
   igual que en Informes de los tecnicos y Solicitar compra */
.selector-panel .gestion-filtros { padding: 10px; gap: 6px; border-bottom: 1px solid var(--sigta-borde-suave); }
.selector-panel .gestion-filtros .g-buscar { margin: 0; padding: 7px 10px; }
.selector-panel .gestion-filtros .g-buscar input,
.selector-panel .gestion-filtros select { font-size: 12px; }
.selector-panel .gestion-filtros select { padding: 7px 9px; }
.selector-ticket .selector-cabecera,
.selector-ticket .selector-fila { grid-template-columns: 96px 1fr 104px; }
.selector-ticket .selector-fila em { white-space: normal; line-height: 1.25; }
.selector-ticket .gestion-paginacion { border-top: 1px solid var(--sigta-borde-suave); padding: 7px 10px; }
.vista-gestion .gestion-col-izq .ticket-header-card { flex: 1 1 auto; min-height: 0; overflow-y: auto; }
.vista-gestion .gestion-right > .workflow-card { flex: 1; min-height: 0; }

/* ---------- REPORTE MENSUAL ----------
   Solo presentacion: filtros en una barra, el total como cifra
   protagonista y una grafica de barras construida con los mismos
   requerimientos que la consulta ya devuelve. */
.vista-reporte .reporte-filtros { padding: 14px 18px; margin-bottom: 14px; }
.vista-reporte .reporte-filtros .actions { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.vista-reporte .reporte-filtros .campo { margin: 0; width: 120px; }
.vista-reporte .reporte-filtros .campo input { margin-top: 5px; }
.vista-reporte .reporte-filtros button { flex: 0 0 auto; padding: 9px 22px; border-radius: 7px; border: 0; cursor: pointer; }

.vista-reporte .reporte-cabecera { display: grid; grid-template-columns: minmax(220px, 1fr) 2.2fr; gap: 14px; margin-bottom: 14px; align-items: stretch; }
.vista-reporte .reporte-kpi { display: flex; flex-direction: column; justify-content: center; padding: 18px 22px; border-left: 4px solid var(--sigta-mostaza); }
.vista-reporte .reporte-kpi .copy { font-size: 13px; line-height: 1.5; color: var(--sigta-texto-suave); }
.vista-reporte .reporte-kpi .copy b { display: block; font-size: 44px; line-height: 1; font-weight: 800; color: var(--sigta-azul); margin-bottom: 6px; }

.vista-reporte .reporte-grafico { padding: 14px 18px 10px; display: flex; flex-direction: column; }
.rg-titulo { display: block; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: var(--sigta-texto-suave); margin-bottom: 12px; }
.rg-barras { display: flex; align-items: flex-end; gap: 3px; flex: 1; min-height: 116px; }
.rg-col { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 5px; }
.rg-pista { width: 100%; height: 96px; display: flex; align-items: flex-end; background: linear-gradient(to top, var(--sigta-borde-suave) 1px, transparent 1px) 0 100% / 100% 24px repeat-y; border-radius: 3px; }
.rg-barra { width: 100%; min-height: 2px; border-radius: 3px 3px 0 0; background: var(--sigta-borde); transition: height .25s ease; }
.rg-barra.con-dato { background: var(--sigta-azul); }
.rg-col small { font-size: 9px; color: var(--sigta-texto-suave); height: 11px; line-height: 11px; }

.vista-reporte .reporte-lista { padding: 6px 20px 14px; }
.vista-reporte .reporte-item { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; padding: 11px 0; }
.vista-reporte .reporte-item:first-child { border-top: 0; }
.vista-reporte .reporte-item b { color: var(--sigta-azul); font-size: 12px; background: var(--sigta-azul-tenue); padding: 3px 9px; border-radius: 6px; }
.vista-reporte .reporte-item small { margin-left: auto; color: var(--sigta-texto-suave); font-size: 11.5px; white-space: nowrap; }

@media (max-width: 1050px) { .vista-reporte .reporte-cabecera { grid-template-columns: 1fr; } }

/* ---------- 6. RESPONSIVE: se respeta el apilado original ---------- */
@media (max-width: 1050px) { .vista-compra { height: auto; flex-direction: column; } .vista-compra .compra-col-izq { width: 100%; min-width: 0; } .vista-compacta .gestion-left { width: 100%; min-width: 0; align-self: stretch; max-height: none; } .vista-gestion .gestion-col-izq { width: 100%; min-width: 0; } .vista-gestion .gestion-col-izq .gestion-left { max-height: none; } .vista-gestion .gestion-col-izq .ticket-header-card { overflow: visible; } .vista-informe { height: auto; flex-direction: column; } .vista-informe .informe-col-izq { width: 100%; min-width: 0; } .vista-informe .informe-col-izq .ticket-header-card { flex: none; overflow: visible; } }
@media (max-width: 760px) { .vista-compra .desc-box { grid-template-columns: 1fr; } }
</style>

<style scoped>
 .gestion-toolbar{display:flex;gap:14px;align-items:center;margin-bottom:18px}.gestion-toolbar label{display:flex;align-items:center;gap:10px;flex:1;background:#fff;border:1px solid #d6e1ed;padding:12px;border-radius:9px}.gestion-toolbar input{border:0;outline:0;width:100%;font:inherit}
.gestion-kanban{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;align-items:start}
.gestion-columna{--columna-color:#d9a514;border:1px solid #f0dfa8;border-top:4px solid var(--columna-color);border-radius:11px;padding:12px;background:#fdf6e0;min-width:0}
.gestion-columna.gestionar{--columna-color:#2563a6;background:#e8f1fb;border-color:#c3d9f0;border-top-color:var(--columna-color)}
.gestion-columna.atencion{--columna-color:#159071;background:#e3f7f0;border-color:#b9e6d4;border-top-color:var(--columna-color)}
.gestion-columna.cerrar{--columna-color:#744aa4;background:#f1e9fa;border-color:#dcc7ef;border-top-color:var(--columna-color)}
.gestion-columna-head{display:flex;align-items:center;justify-content:space-between;color:var(--sigta-azul);margin:4px 2px 14px;font-size:12px}.gestion-columna-head b{display:flex;align-items:center;gap:8px}.gestion-columna-head i{width:9px;height:9px;border-radius:50%;background:var(--columna-color)}.gestion-columna-head em{font-style:normal;background:white;padding:4px 9px;border-radius:12px}
.gestion-ticket{background:white;border:1px solid #d6e1ed;border-top:3px solid var(--columna-color);border-radius:9px;padding:14px;margin-bottom:10px;transition:transform .15s,box-shadow .15s}.gestion-ticket:hover{transform:translateY(-2px);box-shadow:0 6px 16px #17324f18}.gestion-ticket:last-of-type{margin-bottom:0}.gestion-ticket-head{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:12px}.gestion-ticket-head span{background:#eef4fb;padding:6px 10px;border-radius:14px;font-weight:700}.gestion-ticket h3{font-size:14px;margin:15px 0;overflow-wrap:anywhere}.gestion-ticket dl>div{display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-top:1px solid #edf1f6;font-size:11px}.gestion-ticket dt{color:#64748b}.gestion-ticket dd{margin:0;text-align:right;overflow-wrap:anywhere}.gestion-ticket>button{width:100%;margin-top:12px;padding:9px;border:1px solid var(--sigta-azul);border-radius:7px;background:white;color:var(--sigta-azul);font-weight:800;cursor:pointer}.gestion-ticket>button:hover{background:var(--sigta-azul);color:white}.gestion-ticket>button:focus-visible{outline:2px solid var(--columna-color);outline-offset:3px}.gestion-columna>.empty-list{padding:20px 10px;margin:0;background:white;border:1px solid #d6e1ed;border-radius:9px;text-align:center;color:#64748b;font-size:12px}

.expediente-action{margin-top:18px;background:#f6f9fd;border:1px solid #dce6f1;border-radius:10px;padding:18px}.expediente-action h3{margin:7px 0 15px;font-size:17px}.expediente-action>small{color:#64748b;font-size:10px;font-weight:800}.expediente-prioridades{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.expediente-prioridades button{border:1px solid #cbd9e8;background:#fff;border-radius:8px;padding:15px 10px;color:var(--sigta-azul);cursor:pointer}.expediente-prioridades b,.expediente-prioridades span{display:block}.expediente-prioridades span{margin-top:6px;font-size:12px;color:#64748b}.expediente-prioridades .selected{border-color:var(--sigta-azul);box-shadow:inset 0 0 0 1px var(--sigta-azul);background:#eaf2fc}.expediente-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:15px}
.asignacion-backdrop{position:fixed;inset:0;z-index:1600;background:#082b4fcc;display:grid;place-items:center;padding:20px}.asignacion-confirm{width:min(470px,94vw);background:#fff;border-top:4px solid var(--sigta-mostaza);border-radius:13px;padding:25px;text-align:center}.asignacion-confirm>i{width:44px;height:44px;border-radius:50%;background:#fff2c8;color:#9b7100;display:grid;place-items:center;margin:auto;font-style:normal;font-size:22px;font-weight:900}.asignacion-confirm>p{color:#64748b}.asignacion-persona{display:flex;justify-content:space-between;gap:12px;margin-top:12px}
.mantenimiento-visor{position:fixed;inset:0;z-index:1700;background:#082b4fcc;display:grid;place-items:center;padding:20px}.mantenimiento-visor>section{width:min(1100px,94vw);background:#fff;border-radius:14px;overflow:hidden}.mantenimiento-visor header{display:flex;justify-content:space-between;align-items:center;background:var(--sigta-azul);padding:16px;color:white}.mantenimiento-visor header button{border:1px solid #ffffff55;border-radius:7px;padding:9px;background:transparent;color:#fff;cursor:pointer}.mantenimiento-visor section>div{height:75vh;padding:16px;display:grid;place-items:center}.mantenimiento-visor img{max-width:100%;max-height:100%;object-fit:contain}.mantenimiento-visor iframe{width:100%;height:100%;border:0}
@media(max-width:1150px){.gestion-kanban{grid-template-columns:1fr 1fr}}@media(max-width:650px){.gestion-kanban{grid-template-columns:1fr}.expediente-prioridades{grid-template-columns:1fr 1fr}.gestion-toolbar{flex-wrap:wrap}.mantenimiento-visor header>b{display:none}}
</style>

<style scoped>
.viabilidad-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.viabilidad-cards>article{background:#fff;border:1px solid #d6e1ed;border-radius:10px;padding:18px}.viabilidad-cards h3{font-size:17px}.viabilidad-cards p{font-size:13px;color:#526a82}.viabilidad-datos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.viabilidad-datos dt{font-size:11px;color:#64748b}.viabilidad-datos dd{margin:6px 0 0;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere}.viabilidad-documentos{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0}.viabilidad-documentos article{display:grid;grid-template-columns:42px 1fr auto;gap:12px;align-items:center;background:#fff;border:1px solid #d6e1ed;border-radius:10px;padding:13px}.viabilidad-documentos i{display:grid;place-items:center;width:42px;height:42px;background:#eef4fb;border-radius:9px;font-style:normal;font-size:11px;font-weight:800}.viabilidad-documentos b,.viabilidad-documentos small{display:block}.viabilidad-documentos small{margin-top:5px;color:#64748b}.viabilidad-adjuntos{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.viabilidad-adjuntos .sia-field{padding:12px;border:1px dashed #b8c8da;border-radius:8px;background:#fff;margin:0}.no-viable{color:#b42318;border-color:#efb5b5;background:#fff7f7}.motivo-compra{text-align:left}@media(max-width:900px){.viabilidad-cards,.viabilidad-datos{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:760px){.viabilidad-cards,.viabilidad-datos,.viabilidad-documentos,.viabilidad-adjuntos{grid-template-columns:1fr}.viabilidad-documentos article{grid-template-columns:42px 1fr}.viabilidad-documentos button{grid-column:1/-1}}
</style>

<style scoped>
.tabla-informes{width:100%;border-collapse:collapse}.tabla-informes th,.tabla-informes td{padding:13px;text-align:left;border-bottom:1px solid #e5edf5;font-size:13px}.tabla-informes th{color:#64748b;background:#f5f8fc;font-size:11px}.informe-texto{white-space:pre-wrap;line-height:1.6}.table-wrap{overflow:auto}
</style>
