<template>
  <div class="layout sigta-role-layout sia-gestion">
    <aside :class="{ abierto: menuAbierto }">
      <div class="brand-row">
        <div class="brand"><b><img src="/img/emi.jpg" alt="EMI"></b><div><strong>SIA</strong><small>Mantenimiento</small></div></div>
        <button type="button" class="menu-toggle" :aria-expanded="menuAbierto" aria-label="Mostrar opciones del menú" @click="menuAbierto = !menuAbierto"><span></span><span></span><span></span></button>
      </div>
      <p>MI TRABAJO</p>
      <button v-for="m in menu" :key="m.id" class="mt-menu-item" :class="{active:vista===m.id}" @click="irA(m.id)"><span class="icon-badge" :style="{'--menu-icon':m.color,'--menu-icon-bg':m.color+'26'}"><IconoSigta :nombre="m.icono" :tamano="16" /></span>{{ m.nombre }}<em v-if="m.total!==undefined">{{ m.total }}</em></button>
      <div class="sidebar-watermark" aria-hidden="true">
        <img src="/img/marca-de-agua.png" alt="">
        <div class="wm-text"><b>EMI</b><span>Escuela Militar de Ingeniería</span><small>"Mcal. Antonio José de Sucre"</small></div>
      </div>
      <div class="bottom"><button class="logout" @click="mostrarLogout = true"><IconoSigta nombre="salir" :tamano="17" />Cerrar sesión</button></div>
    </aside>

    <LogoutModal :visible="mostrarLogout" @cancelar="mostrarLogout = false" @confirmar="confirmarSalida" />

    <main>
      <header>
        <div><h1>{{ titulo }}</h1><p>{{ subtitulo }}</p></div>

      
        <UsuarioHeader @actualizar="cargar" />
      </header>

      <div v-if="errorCarga" class="error-carga"><b>No se pudieron cargar los requerimientos.</b><span>{{ errorCarga }}</span></div>

      <NotificacionesView v-if="vista==='notificaciones'" embedded />
      <!-- ============================ RESUMEN ============================ -->
      <section v-if="vista==='resumen'">
        <div class="hero">
          <div><small>TÉCNICO DE MANTENIMIENTO</small><h2>{{ saludo }}, {{ primerNombre }}</h2><p>Órdenes de trabajo asignadas a usted.</p></div>
          <span>MT</span>
        </div>

        <div v-if="conRetorno.length" class="alerta">
          <b>⚠ {{ conRetorno.length }} orden(es) devuelta(s) por la jefatura</b>
          <span>{{ conRetorno.map(r=>r.codigo).join(', ') }} — el problema no quedó resuelto; repita la intervención.</span>
        </div>

        <div class="stats">
          <article @click="irA('ordenes')"><i class="badge" style="background:#3E7BD626;color:#3E7BD6"><IconoSigta nombre="tickets" :tamano="20" /></i><div><small>Órdenes por recibir</small><b>{{ porRecibir.length }}</b><p>designadas por la jefatura</p></div></article>
          <article @click="irA('trabajo')"><i class="badge" style="background:#E08A1E26;color:#E08A1E"><IconoSigta nombre="mantenimiento" :tamano="20" /></i><div><small>En reparación</small><b>{{ porReparar.length }}</b><p>trabajo en curso</p></div></article>
          <article @click="irA('trabajo')"><i class="badge" style="background:#2FA85C26;color:#2FA85C"><IconoSigta nombre="validar" :tamano="20" /></i><div><small>Por probar</small><b>{{ porProbar.length }}</b><p>pruebas e informe</p></div></article>
          <article @click="irA('recepcion')"><i class="badge" style="background:#1FA39626;color:#1FA396"><IconoSigta nombre="almacen" :tamano="20" /></i><div><small>Por recibir</small><b>{{ porRecibirComponente.length }}</b><p>componente y acta</p></div></article>
        </div>

        <div class="panels">
          <section class="panel">
            <div class="panel-head"><div><h3>Atención del mantenimiento</h3></div></div>
            <div class="process-grid">
              <button class="process-card" style="border-top-color:#3E7BD6" @click="irA('ordenes')"><span class="process-num" style="background:#3E7BD626;color:#3E7BD6">01</span><div><b>Recibir orden de trabajo</b><small>Tomar conocimiento del requerimiento designado</small></div></button>
              <button class="process-card" style="border-top-color:#E08A1E" @click="irA('ordenes')"><span class="process-num" style="background:#E08A1E26;color:#E08A1E">02</span><div><b>Inspección técnica y diagnóstico</b><small>Determinar la falla y si requiere compra</small></div></button>
              <button class="process-card" style="border-top-color:#C79A1E" @click="irA('compras')"><span class="process-num" style="background:#C79A1E26;color:#C79A1E">03</span><div><b>Realizar requerimiento</b><small>Características del componente y cotización</small></div></button>
              <button class="process-card" style="border-top-color:#1FA396" @click="irA('recepcion')"><span class="process-num" style="background:#1FA39626;color:#1FA396">04</span><div><b>Recibir componente y acta</b><small>Confirmar la entrega de Almacén</small></div></button>
              <button class="process-card" style="border-top-color:#7B6FD9" @click="irA('trabajo')"><span class="process-num" style="background:#7B6FD926;color:#7B6FD9">05</span><div><b>Reparación o instalación</b><small>Ejecutar y registrar la intervención</small></div></button>
              <button class="process-card" style="border-top-color:#2FA85C" @click="irA('trabajo')"><span class="process-num" style="background:#2FA85C26;color:#2FA85C">06</span><div><b>Pruebas e informe a la jefatura</b><small>Comprobar el funcionamiento y elevar el informe</small></div></button>
            </div>
          </section>
          <section class="panel">
            <div class="panel-head"><div><small>SEGUIMIENTO</small><h3>Historial</h3></div></div>
            <p class="copy">Consulte los requerimientos que ya atendió y su estado actual.</p>
            <button class="wide primary" @click="irA('historial')">Ver historial →</button>
          </section>
        </div>
      </section>

            <!-- ==================== A. ÓRDENES DE TRABAJO (MASTER-DETAIL) ==================== -->
      <section v-else-if="vista==='recepcion'">
<TablaTecnicoMantenimiento titulo="Componentes y actas pendientes de recepción" :registros="porRecibirComponente"><template #acciones="{registro}"><button class="secundario" @click="verItem(registro)">Ver detalles</button><button @click="abrirRecepcion(registro)">Recibir componente</button></template></TablaTecnicoMantenimiento>
</section>

      <!-- ==================== MODAL: RECEPCIÓN DE COMPONENTE ==================== -->
      <div v-if="recepcionActiva" class="detalle-modal-backdrop" @click.self="cerrarRecepcion">
        <div class="detalle-modal orden-modal">
          <div class="detalle-modal-header">
            <div><h3>{{ recepcionActiva.titulo }}</h3><small>{{ recepcionActiva.codigo }}</small></div>
            <button class="detalle-modal-close" @click="cerrarRecepcion">✕</button>
          </div>
          <div class="detalle-modal-body">
            <div class="ticket-header-card"><div class="t-meta"><span><b>Componente:</b> {{ recepcionActiva.producto_requerido || 's/d' }}</span><span><b>Cantidad:</b> {{ recepcionActiva.cantidad_requerida || 1 }} unid.</span></div></div>
            <ActasRecepcionTecnico v-if="recepcionActiva.compra_vinculada?.id" :compra-id="recepcionActiva.compra_vinculada.id" />
            <div class="workflow-card"><div class="wf-header">Recepción de componente</div><div class="wf-body">
              <div class="wf-step" :class="{active:pasoRecepcion===1,completed:pasoRecepcion>1}"><div class="step-num">1</div><div class="step-content"><h4>Revisar acta de conformidad</h4><p>Verifique que el componente y el acta remitidos por Almacén correspondan al requerimiento.</p><div v-if="pasoRecepcion===1" class="step-form"><div class="evidence-box"><div class="evidence-info"><strong>Acta de conformidad</strong><span>{{ recepcionActiva.codigo_compra_vinculada }}</span></div><button v-if="recepcionActiva.compra_vinculada?.acta_conformidad" class="evidence-btn" @click="abrirEvidencia(recepcionActiva.compra_vinculada.acta_conformidad, 'Acta de conformidad')">Abrir acta</button><span v-else class="sin-adjunto">Acta no disponible</span></div><div class="step-actions"><button class="reject" @click="cerrarRecepcion">Cancelar</button><button class="flex-btn primary" :disabled="!recepcionActiva.compra_vinculada?.acta_conformidad" @click="pasoRecepcion=2">Aprobar y continuar</button></div></div></div></div>
              <div class="wf-step" :class="{active:pasoRecepcion===2,completed:pasoRecepcion>2,locked:pasoRecepcion<2}"><div class="step-num">2</div><div class="step-content"><h4>Confirmar recepción del componente</h4><p>Confirme que recibió físicamente el componente y el acta.</p><div v-if="pasoRecepcion===2" class="step-form"><label class="campo">Descripción de recepción<textarea v-model="formRecepcion.observacion" rows="3" placeholder="Estado del componente, embalaje u observación relevante..."></textarea></label><label class="confirmacion"><input v-model="formRecepcion.confirmado" type="checkbox"> Confirmo que recibí el componente y revisé el acta de conformidad.</label><div class="step-actions"><button class="reject" @click="pasoRecepcion=1">Retroceder</button><button class="flex-btn primary" :disabled="!formRecepcion.confirmado" @click="pasoRecepcion=3">Continuar</button></div></div></div></div>
              <div class="wf-step" :class="{active:pasoRecepcion===3,locked:pasoRecepcion<3}"><div class="step-num">3</div><div class="step-content"><h4>Habilitar reparación y pruebas</h4><p>Al confirmar, el requerimiento pasará a su bandeja de reparación y pruebas.</p><div v-if="pasoRecepcion===3" class="step-form"><div class="step-actions"><button class="reject" @click="pasoRecepcion=2">Retroceder</button><button class="flex-btn primary" :disabled="procesando" @click="confirmarRecepcion">Confirmar recepción</button></div></div></div></div>
            </div></div>
          </div>
        </div>
      </div>

      <section v-else-if="vista==='ordenes'">
<TablaTecnicoMantenimiento titulo="Órdenes de trabajo" :registros="bandejaOrdenes"><template #acciones="{registro}"><button @click="abrirOrdenModal(registro)">Ver detalle y diagnóstico</button></template></TablaTecnicoMantenimiento>
</section>

      <section v-else-if="vista==='cotizaciones'">
<TablaTecnicoMantenimiento titulo="Cotizaciones y requerimientos" :registros="bandejaOrdenes"><template #acciones="{registro}"><button class="secundario" @click="verItem(registro)">Ver detalles</button><button @click="recibirOrden(registro)">Llenar informe y cotización</button></template></TablaTecnicoMantenimiento>
</section>

      <!-- ==================== MODAL: CONSOLA DE DIAGNÓSTICO ==================== -->
      <ExpedienteSolicitudModal v-if="ordenAbierta" :registro="ordenAbierta" @cerrar="cerrarOrden" @evidencia="abrirEvidencia">
        <section v-if="modoComponente" class="antecedente-tecnico"><h3>Diagnóstico y plan de solución</h3><p><b>Diagnóstico:</b> {{ ordenAbierta.diagnostico }}</p><p><b>Plan de solución:</b> {{ ordenAbierta.plan_solucion }}</p></section>
            <div class="workflow-card">
              <div class="wf-header">Diagnóstico y acciones</div>
              <div class="wf-body">

                <!-- PASO 1: DIAGNÓSTICO -->
                <div :class="['wf-step', modoComponente ? 'completed' : 'active']">
                  <div class="step-num">1</div>
                  <div class="step-content">
                    <h4>Inspección técnica y diagnóstico <span v-if="modoComponente" class="step-badge">✓ Registrado</span></h4>
                    <p v-if="!modoComponente">Registre los resultados de la inspección inicial.</p>
                    <div v-if="!modoComponente">
                      <label class="campo">Diagnóstico
                        <textarea v-model="formDiagnostico.diagnostico" rows="3" placeholder="Falla detectada y componente afectado"></textarea>
                      </label>
                      <label class="campo">Plan de solución
                        <textarea v-model="formDiagnostico.plan_solucion" rows="2" placeholder="Acciones previstas para resolver el problema"></textarea>
                      </label>

                      <fieldset class="compuerta" style="margin-bottom: 15px; border: 1px solid var(--sigta-borde); padding: 10px; border-radius: 6px;">
                        <legend style="font-size:12px; font-weight:bold; color:var(--sigta-texto-suave);">¿Requiere compra de componentes?</legend>
                        <label style="margin-right:15px; cursor:pointer;"><input v-model="formDiagnostico.requiere_compra" type="radio" :value="false"> No</label>
                        <label style="cursor:pointer;"><input v-model="formDiagnostico.requiere_compra" type="radio" :value="true"> Sí</label>
                      </fieldset>

                      <button class="primary step-btn" :disabled="procesando||!formDiagnostico.diagnostico.trim()||!formDiagnostico.plan_solucion.trim()" @click="guardarDiagnostico">
                        {{ formDiagnostico.requiere_compra ? 'Guardar y realizar requerimiento' : 'Guardar diagnóstico' }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- PASO 2: REQUERIMIENTO DE COMPRA -->
                <div v-if="formDiagnostico.requiere_compra" :class="['wf-step', !modoComponente ? 'locked' : 'active']">
                  <div class="step-num">2</div>
                  <div class="step-content">
                    <h4>Realizar requerimiento de compra</h4>
                    <p>Complete la solicitud del repuesto necesario.</p>
                    <div v-if="modoComponente" class="cotizacion-form">
                      <label class="campo">Componente requerido
                        <input v-model="formComponente.producto_requerido" placeholder="Ej.: Compresor 12000 BTU" class="full-select">
                      </label>
                      <label class="campo">Características del componente
                        <textarea v-model="formComponente.especificacion_producto" rows="2" placeholder="Marca, modelo, voltaje..."></textarea>
                      </label>
                      <label class="campo">Cantidad
                        <input v-model="formComponente.cantidad_requerida" type="number" min="1" class="full-select">
                      </label>
                      <label class="campo">Costo estimado (Bs.)
                        <input v-monto inputmode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" v-model="formComponente.costo_estimado" type="text" min="0" max="9999999999.99" step="0.01" class="full-select">
                      </label>
                      <a v-if="ordenAbierta?.informe_compra" :href="ordenAbierta.informe_compra" target="_blank">Ver informe de requerimiento generado</a>
                      <CotizacionesRequerimiento ref="cotizacionesFormulario" :expediente="ordenAbierta?.id" :guardadas="ordenAbierta?.cotizaciones || []" :monto="formComponente.costo_estimado" />

                      <div class="step-actions mt-2">
                        <button class="reject" @click="cerrarOrden">Cancelar</button>
                        <button class="step-btn" :disabled="procesando" @click="guardarBorradorCompra">Guardar borrador</button><button class="primary flex-btn" :disabled="procesando||!formComponente.producto_requerido.trim()" @click="enviarRequerimiento">Enviar requerimiento</button>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
      </ExpedienteSolicitudModal>

      <!-- ==================== EN ESPERA DE COMPRA ==================== -->
      <section v-else-if="vista==='compras'">
<TablaTecnicoMantenimiento titulo="Requerimientos en espera de compra" :registros="enEsperaCompra" @ver="verItem" />
</section>

      <!-- ============= D. REPARACIÓN, PRUEBAS E INFORME ============= -->
      <section v-else-if="['trabajo','informes'].includes(vista)">
<TablaTecnicoMantenimiento :key="vista" :titulo="vista==='informes' ? 'Pruebas e informes pendientes' : 'Trabajos y anotaciones'" :registros="enTrabajo"><template #acciones="{registro}"><button class="secundario" @click="verItem(registro)">Ver detalles</button><button @click="abrirTrabajo(registro)">{{ vista==='informes' ? 'Registrar pruebas e informe' : 'Continuar trabajo' }}</button></template></TablaTecnicoMantenimiento>
</section>

      <!-- ==================== MODAL: REPARACIÓN, PRUEBAS E INFORME ==================== -->
      <div v-if="itemActivo" class="detalle-modal-backdrop" @click.self="cerrarTrabajo">
        <div class="detalle-modal orden-modal">
          <div class="detalle-modal-header">
            <div><h3>{{ itemActivo.titulo }}</h3><small>{{ itemActivo.codigo }}</small></div>
            <button class="detalle-modal-close" @click="cerrarTrabajo">✕</button>
          </div>
          <div class="detalle-modal-body">
            <div class="ticket-header-card"><div class="t-meta"><span><b>Solicitante:</b> {{ itemActivo.solicitante_nombre || 's/d' }}</span><span><b>Ubicación:</b> {{ itemActivo.ubicacion || 's/d' }}</span></div><div class="desc-box">{{ itemActivo.diagnostico || itemActivo.descripcion }}</div></div>
            <div class="workflow-card"><div class="wf-header">Flujo de reparación y pruebas</div><div class="wf-body">
              <div class="wf-step" :class="{active:pasoTrabajo===1,completed:pasoTrabajo>1}"><div class="step-num">1</div><div class="step-content"><h4>Revisar requerimiento y documentación</h4><p v-if="pasoTrabajo===1">Revise el detalle, diagnóstico, evidencia y antecedentes antes de intervenir el equipo.</p><div v-if="pasoTrabajo===1" class="step-form"><div class="revision-documentos"><div><b>Descripción del requerimiento</b><span>{{ itemActivo.descripcion || 'Sin descripción registrada.' }}</span></div><div><b>Diagnóstico técnico</b><span>{{ itemActivo.diagnostico || 'Sin diagnóstico registrado.' }}</span></div><div><b>Plan de solución</b><span>{{ itemActivo.plan_solucion || 'Sin plan registrado.' }}</span></div><a v-if="itemActivo.evidencia_archivo_url" :href="itemActivo.evidencia_archivo_url" target="_blank" class="evidence-btn">Abrir evidencia reportada</a><span v-else class="sin-adjunto">No existe evidencia adjunta.</span><button v-if="itemActivo.compra_vinculada?.acta_conformidad" class="evidence-btn" @click="abrirEvidencia(itemActivo.compra_vinculada.acta_conformidad, 'Acta de conformidad')">Abrir acta de conformidad</button><span v-if="itemActivo.compra_vinculada && !itemActivo.compra_vinculada.acta_conformidad" class="sin-adjunto">La compra vinculada no tiene acta disponible.</span></div><button class="detalle-btn" @click="verItem(itemActivo)">Ver detalle completo</button><div v-if="pasoTrabajo===1" class="step-actions"><button class="reject" @click="cerrarTrabajo">Cancelar</button><button class="flex-btn primary" @click="pasoTrabajo=2">Siguiente</button></div></div></div></div>
              <div class="wf-step" :class="{active:pasoTrabajo===2,completed:pasoTrabajo>2,locked:pasoTrabajo<2}"><div class="step-num">2</div><div class="step-content"><h4>Registrar reparación o instalación</h4><p v-if="pasoTrabajo===2">El técnico documenta el trabajo ejecutado. Puede completar o corregir la información antes de continuar.</p><div v-if="pasoTrabajo===2" class="step-form"><label class="campo">Reparación o instalación realizada<textarea v-model="formTrabajo.trabajo_realizado" rows="5" placeholder="Trabajo ejecutado sobre el equipo o instalación"></textarea></label><label class="campo">Observaciones<textarea v-model="formTrabajo.observaciones_trabajo" rows="2" placeholder="Observaciones de la intervención"></textarea></label><div v-if="pasoTrabajo===2" class="step-actions"><button class="reject" @click="pasoTrabajo=1">Retroceder</button><button class="flex-btn primary" :disabled="procesando||!formTrabajo.trabajo_realizado.trim()" @click="registrarTrabajo">Guardar reparación y continuar</button></div></div></div></div>
              <div class="wf-step" :class="{active:pasoTrabajo===3,completed:pasoTrabajo>3,locked:pasoTrabajo<3}"><div class="step-num">3</div><div class="step-content"><h4>Registrar pruebas técnicas</h4><p v-if="pasoTrabajo===3">El técnico registra las pruebas efectuadas y su resultado antes de preparar el informe.</p><div v-if="pasoTrabajo===3" class="step-form"><label class="campo">Resultado de las pruebas técnicas<textarea v-model="formPruebas.resultado_pruebas" rows="4" placeholder="Pruebas efectuadas y comportamiento del equipo"></textarea></label><div v-if="pasoTrabajo===3" class="step-actions"><button class="reject" @click="pasoTrabajo=2">Retroceder</button><button class="flex-btn primary" :disabled="procesando||!formPruebas.resultado_pruebas.trim()" @click="registrarPruebas">Guardar pruebas y continuar</button></div></div></div></div>
              <div class="wf-step" :class="{active:pasoTrabajo===4,locked:pasoTrabajo<4}"><div class="step-num">4</div><div class="step-content"><h4>Elaborar informe al Jefe de Mantenimiento</h4><p v-if="pasoTrabajo===4">Redacte el informe con el resumen del trabajo, las pruebas y el resultado. Al enviarlo, el Jefe de Mantenimiento recibirá el caso.</p><div v-if="pasoTrabajo===4" class="step-form"><label class="campo">Informe al Jefe de Mantenimiento<textarea v-model="formInforme.informe_trabajo" rows="6" placeholder="Describa el trabajo realizado, componentes utilizados, pruebas efectuadas y resultado final."></textarea></label><label class="campo">Informe técnico con cuadros / fotografía del trabajo<ArchivoInput type="file" accept="application/pdf,image/*" @change="onFotografia" /></label><div class="step-actions"><button class="reject" @click="pasoTrabajo=3">Retroceder</button><button class="flex-btn primary" :disabled="procesando||!formInforme.informe_trabajo.trim()" @click="registrarInforme">{{ procesando ? 'Enviando...' : 'Enviar informe al Jefe de Mantenimiento' }}</button></div></div></div></div>
            </div></div>
          </div>
        </div>
      </div>

      <!-- =========================== HISTORIAL =========================== -->
      <section v-else-if="vista==='historial'">
<TablaTecnicoMantenimiento titulo="Historial de requerimientos" :registros="misItems" @ver="verItem" />
</section>
    </main>

    <!-- ============================ DETALLE ============================ -->
    <ExpedienteSolicitudModal v-if="detalle" :registro="detalle" @cerrar="detalle=null" @evidencia="abrirEvidencia">
      <div class="mt-detalle-cabecera"><span class="mt-estado">{{ detalle.estado_nombre || detalle.estado_codigo }}</span><span v-if="detalle.prioridad_jefatura">Prioridad: {{ detalle.prioridad_jefatura }}</span></div>
      <InformesTecnicoMantenimiento :id="detalle.id" @ver="abrirEvidencia" />
      <div v-if="detalle.fotografia_trabajo_url || detalle.informe_compra" class="mt-componente"><h3>Informes y anexos adjuntos</h3><button v-if="detalle.fotografia_trabajo_url" class="sia-secondary" @click="abrirEvidencia(detalle.fotografia_trabajo_url, 'Informe técnico adjunto')">Ver informe o fotografía adjunta</button><button v-if="detalle.informe_compra" class="sia-secondary" @click="abrirEvidencia(detalle.informe_compra, 'Informe de requerimiento')">Ver informe de requerimiento</button></div>
      <ActasRecepcionTecnico v-if="detalle.compra_vinculada?.id" :compra-id="detalle.compra_vinculada.id" />
      <div v-if="detalle.producto_requerido" class="mt-componente"><h3>Componente requerido</h3><p>{{ detalle.producto_requerido }} · {{ detalle.cantidad_requerida || 1 }} unidades · Bs. {{ detalle.costo_estimado || 'Sin registro' }}</p><button v-if="detalle.compra_vinculada?.acta_conformidad" class="sia-secondary" @click="abrirEvidencia(detalle.compra_vinculada.acta_conformidad, 'Acta de conformidad')">Ver acta de conformidad</button></div>
    </ExpedienteSolicitudModal>
    <div v-if="visorEvidencia" class="tecnico-visor" @click.self="cerrarEvidencia"><section><header><button @click="cerrarEvidencia">← Volver al expediente</button><b>{{ visorNombre }}</b><button aria-label="Cerrar" @click="cerrarEvidencia">×</button></header><div><img v-if="visorEsImagen" :src="visorEvidencia" alt="Evidencia del expediente"><iframe v-else-if="visorEsPdf" :src="visorEvidencia" :title="visorNombre" /><p v-else>Descargue el documento para abrirlo con su aplicación correspondiente.</p></div><footer class="mt-visor-footer"><a :href="visorEvidencia" :download="visorArchivo">Descargar {{ visorEsPdf ? 'PDF' : 'documento' }}</a></footer></section></div>
  </div>
</template>

<script setup>
import NotificacionesView from './NotificacionesView.vue'
import CotizacionesRequerimiento from '../components/CotizacionesRequerimiento.vue'
const cotizacionesFormulario = ref(null)

import ActasRecepcionTecnico from '../components/ActasRecepcionTecnico.vue'
import { solicitarFirma } from '../utils/firma'
import TablaTecnicoMantenimiento from '../components/TablaTecnicoMantenimiento.vue'
import InformesTecnicoMantenimiento from '../components/InformesTecnicoMantenimiento.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import IconoSigta from '../components/IconoSigta.vue'
import ExpedienteSolicitudModal from '../components/ExpedienteSolicitudModal.vue'
import LogoutModal from '../components/LogoutModal.vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const usuario = ref(JSON.parse(localStorage.getItem('sigta_usuario') || '{}'))
const vista = ref(route.query.vista === 'historial' ? 'historial' : 'ordenes')
const menuAbierto = ref(false)
const items = ref([])
const cargando = ref(false)
const errorCarga = ref('')
const procesando = ref(false)
const itemActivo = ref(null)
const pasoTrabajo = ref(1)
const ordenAbierta = ref(null)
const recepcionActiva = ref(null)
const pasoRecepcion = ref(1)
const modoComponente = ref(false)
const detalle = ref(null)
const visorEvidencia=ref(''), visorEsImagen=ref(false), visorEsPdf=ref(false), visorNombre=ref('Documento del expediente'), visorArchivo=ref('documento.pdf')
let consultaVisor=0

const nombre = computed(() => usuario.value.nombre || usuario.value.nombre_completo || 'Técnico de Mantenimiento')
const primerNombre = computed(() => nombre.value.split(' ')[0])
const iniciales = computed(() => nombre.value.split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase())
const saludo = computed(() => new Date().getHours() < 12 ? 'Buenos días' : new Date().getHours() < 19 ? 'Buenas tardes' : 'Buenas noches')

const misItems = computed(() => items.value.filter(r => Number(r.auxiliar_asignado) === Number(usuario.value.id)))
const enCompra = r => ['SOLICITADA', 'VIABLE'].includes(r.estado_compra_componente)

const porRecibir = computed(() => misItems.value.filter(r => r.estado_codigo === 'DERIVADO'))
const porRecibirComponente = computed(() => misItems.value.filter(r => r.estado_compra_componente === 'PENDIENTE_RECEPCION_TECNICO'))
const enEsperaCompra = computed(() => misItems.value.filter(r => r.estado_codigo === 'EN_ESPERA_COMPRA' || enCompra(r)))
const costoTotalEspera = computed(() => enEsperaCompra.value.reduce((total, r) => total + Number(r.costo_estimado || 0), 0).toFixed(2))
const porReparar = computed(() => misItems.value.filter(r => r.estado_codigo === 'EN_MANTENIMIENTO' && !r.trabajo_realizado && !enCompra(r)))
const porProbar = computed(() => misItems.value.filter(r => r.estado_codigo === 'EN_MANTENIMIENTO' && !!r.trabajo_realizado && !enCompra(r)))
const busquedaTrabajos = ref('')
const trabajosFiltrados = computed(() => enTrabajo.value.filter(r => [r.codigo,r.titulo,r.ubicacion].some(v => String(v||'').toLowerCase().includes(busquedaTrabajos.value.trim().toLowerCase()))))
const enTrabajo = computed(() => vista.value==='informes' ? porProbar.value : porReparar.value)
const porCotizar = computed(() => misItems.value.filter(r=>r.estado_codigo==='EN_MANTENIMIENTO' && (!r.estado_compra_componente || r.estado_compra_componente==='BORRADOR')))
const conRetorno = computed(() => misItems.value.filter(r => Number(r.rework_count) > 0 && r.estado_codigo === 'EN_MANTENIMIENTO'))

/* Búsqueda de la bandeja de "Órdenes de Trabajo" / "Cotizaciones", organizada
   en columnas por prioridad (en vez de una sola lista con paginación). */
const bandejaOrdenes = computed(() => vista.value === 'cotizaciones' ? porCotizar.value : porRecibir.value)
const busquedaOrdenes = ref('')

const ordenesFiltradas = computed(() => {
  const texto = busquedaOrdenes.value.trim().toLowerCase()
  if (!texto) return bandejaOrdenes.value
  return bandejaOrdenes.value.filter(r => [r.codigo, r.titulo, r.ubicacion].some(v => (v || '').toLowerCase().includes(texto)))
})

const NIVELES_PRIORIDAD = [
  { id: 'critica', nombre: 'Urgente', match: v => v === 'URGENTE' || v === 'CRITICA' || v === 'CRÍTICA' },
  { id: 'alta', nombre: 'Alta', match: v => v === 'ALTA' },
  { id: 'media', nombre: 'Media', match: v => v === 'MEDIA' },
  { id: 'baja', nombre: 'Baja', match: v => v === 'BAJA' },
]

const columnasPrioridad = computed(() => {
  const lista = ordenesFiltradas.value
  const usados = new Set()
  const columnas = NIVELES_PRIORIDAD.map(nivel => {
    const items = lista.filter(r => nivel.match(String(r.prioridad_jefatura || '').toUpperCase()))
    items.forEach(r => usados.add(r.id))
    return { id: nivel.id, nombre: nivel.nombre, items }
  })
  const sinPrioridad = lista.filter(r => !usados.has(r.id))
  if (sinPrioridad.length) columnas.push({ id: 'sin-prioridad', nombre: 'Sin prioridad', items: sinPrioridad })
  return columnas
})

const menu = computed(() => [
  { id: 'resumen', icono: 'inicio', nombre: 'Dashboard', color: '#F2C400' },
  { id: 'ordenes', icono: 'tickets', nombre: 'Órdenes de trabajo', total: porRecibir.value.length, color: '#3E7BD6' },
  { id: 'recepcion', icono: 'almacen', nombre: 'Recibir componente y acta', total: porRecibirComponente.value.length, color: '#1FA396' },
  { id: 'trabajo', icono: 'mantenimiento', nombre: 'Trabajos y anotaciones', total: porReparar.value.length, color: '#E08A1E' },
  { id: 'cotizaciones', icono: 'compras', nombre: 'Cotizaciones y requerimientos', total: porCotizar.value.length, color: '#C79A1E' },
  { id: 'informes', icono: 'validar', nombre: 'Pruebas e informes', total: porProbar.value.length, color: '#2FA85C' },
  { id: 'compras', icono: 'compras', nombre: 'En espera de compra', total: enEsperaCompra.value.length, color: '#7B6FD9' },
  { id: 'notificaciones', icono: 'notificaciones', nombre: 'Notificaciones', color: '#123A6B' },
  { id: 'historial', icono: 'historial', nombre: 'Historial', color: '#D9538A' },
])

const titulo = computed(() => ({
  notificaciones: 'Notificaciones',
  resumen: 'Panel del Técnico de Mantenimiento',
  ordenes: ordenAbierta.value ? 'Inspección técnica y diagnóstico' : 'Bandeja de órdenes de trabajo',
  recepcion: 'Recibir componente y acta',
  trabajo: 'Reparación, pruebas e informe',
  cotizaciones: 'Cotizaciones y requerimientos',
  informes: 'Pruebas e informes técnicos',
  compras: 'Requerimientos en espera de compra',
  historial: 'Historial de requerimientos',
}[vista.value]))

const subtitulo = computed(() => ({
  resumen: 'Diagnóstico, reparación y pruebas de los requerimientos asignados a usted.',
  ordenes: 'Requerimientos designados por la jefatura de mantenimiento.',
  recepcion: 'Componentes entregados por Almacén que requieren su confirmación.',
  trabajo: 'Intervención técnica e informe dirigido a la jefatura.',
  compras: 'Requerimientos cuyo trabajo está en pausa hasta recibir el componente.',
  historial: 'Todos los requerimientos que usted atendió.',
}[vista.value]))

function etiqueta(r) {
  if (enCompra(r)) return 'En espera de compra'
  if (!r.trabajo_realizado) return 'En reparación'
  if (!r.resultado_pruebas) return 'Por probar'
  return 'Por informar'
}

function colorEtiqueta(r) {
  if (enCompra(r)) return '#1FA396'
  if (!r.trabajo_realizado) return '#E08A1E'
  if (!r.resultado_pruebas) return '#2FA85C'
  return '#7B6FD9'
}

function colorCompra(r) {
  return r.estado_compra_componente === 'VIABLE' ? '#2FA85C' : '#E08A1E'
}

const ESTADOS_HISTORIAL = {
  DERIVADO: { color: '#3E7BD6', icono: 'solicitudes' },
  EN_MANTENIMIENTO: { color: '#E08A1E', icono: 'mantenimiento' },
  EN_ESPERA_COMPRA: { color: '#E08A1E', icono: 'compras' },
  EN_VERIFICACION: { color: '#7B6FD9', icono: 'validar' },
  PENDIENTE_CONFORMIDAD: { color: '#7B6FD9', icono: 'notificaciones' },
  CONFORMIDAD_INFORMADA: { color: '#1FA396', icono: 'validar' },
  PENDIENTE_INFORME_FINAL: { color: '#D9538A', icono: 'reporte' },
  INFORME_REGISTRADO: { color: '#D9538A', icono: 'reporte' },
  FINALIZADO: { color: '#2FA85C', icono: 'etiqueta' },
  CERRADO: { color: '#2FA85C', icono: 'etiqueta' },
  RECHAZADO: { color: '#D64545', icono: 'error' },
  CERRADO_SIN_COMPRA: { color: '#D64545', icono: 'error' },
}
function colorHistorial(r) {
  return ESTADOS_HISTORIAL[r.estado_codigo]?.color || '#64748B'
}
function iconoHistorial(r) {
  return ESTADOS_HISTORIAL[r.estado_codigo]?.icono || 'historial'
}

function siguientePaso(r) {
  if (!r.trabajo_realizado) return 'Registrar reparación'
  if (!r.resultado_pruebas) return 'Registrar pruebas'
  return 'Elaborar informe'
}

function fecha(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' }) : 's/d'
}

const base = '/api/mantenimiento/requerimientos'
const token = () => localStorage.getItem('sigta_token')

function cerrarSesionExpirada() {
  localStorage.removeItem('sigta_token')
  localStorage.removeItem('sigta_usuario')
  router.replace({ path: '/login', query: { motivo: 'sesion-expirada' } })
}

async function cargar() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const r = await fetch(`${base}/`, { headers: { Authorization: `Token ${token()}` } })
    if (r.status === 401) {
      cerrarSesionExpirada()
      return
    }
    if (!r.ok) throw new Error(`El servidor respondió con código ${r.status}.`)
    const d = await r.json()
    items.value = Array.isArray(d) ? d : (d.results || [])
    if (ordenAbierta.value) ordenAbierta.value = items.value.find(x => x.id === ordenAbierta.value.id) || null
    if (itemActivo.value) itemActivo.value = items.value.find(x => x.id === itemActivo.value.id) || null
    if (recepcionActiva.value) recepcionActiva.value = items.value.find(x => x.id === recepcionActiva.value.id) || null
  } catch (e) {
    items.value = []
    errorCarga.value = e.message || 'Intente actualizar nuevamente.'
  } finally {
    cargando.value = false
  }
}

async function postAccion(item, endpoint, body, esFormData = false) {
  procesando.value = true
  try {
    const headers = { Authorization: `Token ${token()}` }
    if (!esFormData) headers['Content-Type'] = 'application/json'
    const r = await fetch(`${base}/${item.id}/${endpoint}/`, {
      method: 'POST',
      headers,
      body: esFormData ? body : JSON.stringify(body || {}),
    })
    const d = await r.json().catch(() => ({}))
    if (r.status === 401) {
      cerrarSesionExpirada()
      throw new Error('La sesión expiró. Inicie sesión nuevamente.')
    }
    if (!r.ok) throw new Error(d.detalle || Object.values(d)[0] || 'No fue posible completar la acción.')
    await cargar()
    return d
  } finally {
    procesando.value = false
  }
}

function irA(id) {
  vista.value = id
  menuAbierto.value = false
  ordenAbierta.value = null
  itemActivo.value = null
  pasoTrabajo.value = 1
  recepcionActiva.value = null
  pasoRecepcion.value = 1
  modoComponente.value = false
}

function verItem(item) { detalle.value = item }
watch(() => route.query.requerimiento, id => {
  if (id) { vista.value='historial'; detalle.value=items.value.find(r=>String(r.id)===String(id)) || null }
})

const mostrarLogout = ref(false)

function salir() {
  localStorage.removeItem('sigta_token')
  localStorage.removeItem('sigta_usuario')
  router.push('/login')
}

function confirmarSalida() {
  mostrarLogout.value = false
  salir()
}

/* ---------- Diagnóstico y requerimiento ---------- */
const formDiagnostico = reactive({ diagnostico: '', plan_solucion: '', requiere_compra: false })
const formComponente = reactive({
  via_compra: 'CAJA_CHICA', producto_requerido: '', especificacion_producto: '',
  cantidad_requerida: 1, costo_estimado: '', archivos: [], informe: null,
})
const formTrabajo = reactive({ trabajo_realizado: '', observaciones_trabajo: '' })
const formPruebas = reactive({ resultado_pruebas: '' })
const formInforme = reactive({ informe_trabajo: '', fotografia: null })
const formRecepcion = reactive({ confirmado: false, observacion: '' })

function abrirRecepcion(item) {
  recepcionActiva.value = item
  pasoRecepcion.value = 1
  formRecepcion.confirmado = false
  formRecepcion.observacion = ''
}

function cerrarRecepcion() {
  recepcionActiva.value = null
  pasoRecepcion.value = 1
}

async function confirmarRecepcion() {
  try {
    await postAccion(recepcionActiva.value, 'recibir-componente-acta', {
      observacion_recepcion_componente: formRecepcion.observacion.trim(),
    })
    cerrarRecepcion()
    vista.value = 'trabajo'
    alert('Recepción registrada. Ya puede realizar la reparación y las pruebas.')
  } catch (e) { alert(e.message) }
}

function recibirOrden(item) {
  ordenAbierta.value = item
  modoComponente.value = vista.value === 'cotizaciones' || item.estado_compra_componente === 'BORRADOR'
  formDiagnostico.diagnostico = item.diagnostico || ''
  formDiagnostico.plan_solucion = item.plan_solucion || ''
  formDiagnostico.requiere_compra = vista.value === 'cotizaciones' || Boolean(item.requiere_reposicion)
  formComponente.via_compra = item.via_compra || 'CAJA_CHICA'
  formComponente.producto_requerido = item.producto_requerido || ''
  formComponente.especificacion_producto = item.especificacion_producto || ''
  formComponente.cantidad_requerida = item.cantidad_requerida || 1
  formComponente.costo_estimado = item.costo_estimado || ''
  formComponente.archivos = []
  formComponente.informe = null
}

const abrirOrdenModal = recibirOrden
async function abrirEvidencia(url, nombre = 'Documento del expediente') {
  const actual=++consultaVisor
  try {
    const destino=new URL(url,window.location.origin)
    if(destino.origin!==window.location.origin || !/^\/(api|media)\//.test(destino.pathname))throw new Error('El documento no pertenece al sistema.')
    const r=await fetch(destino.pathname,{headers:{Authorization:`Token ${localStorage.getItem('sigta_token')}`},cache:'no-store'})
    if(!r.ok)throw new Error('No se pudo abrir el documento.')
    const archivo=await r.blob(), pdf=(await archivo.slice(0,5).text())==='%PDF-'
    if(actual!==consultaVisor)return
    if(archivo.type.includes('json') || archivo.type.includes('text/html'))throw new Error('El servidor no devolvió el documento solicitado.')
    if(visorEvidencia.value)URL.revokeObjectURL(visorEvidencia.value)
    visorEsPdf.value=pdf || /\.pdf$/i.test(destino.pathname)
    const tipo=visorEsPdf.value ? 'application/pdf' : archivo.type
    visorEsImagen.value=tipo.startsWith('image/')
    visorNombre.value=typeof nombre==='string' ? nombre : 'Documento del expediente'
    const original=decodeURIComponent(destino.pathname.split('/').pop() || '')
    const extension=visorEsPdf.value ? '.pdf' : tipo==='image/png' ? '.png' : tipo==='image/jpeg' ? '.jpg' : tipo==='image/webp' ? '.webp' : original.includes('.') ? '.'+original.split('.').pop() : ''
    visorArchivo.value=visorNombre.value.replace(/[^\p{L}\p{N} -]/gu,'')+extension
    visorEvidencia.value=URL.createObjectURL(new Blob([archivo],{type:tipo}))
  } catch(e) { if(actual===consultaVisor)alert(e.message) }
}
function cerrarEvidencia(){consultaVisor++;if(visorEvidencia.value)URL.revokeObjectURL(visorEvidencia.value);visorEvidencia.value=''}

function cerrarOrden() {
  ordenAbierta.value = null
  modoComponente.value = false
}

function retroceder() {
  modoComponente.value = false
}

async function guardarDiagnostico() {
  try {
    await postAccion(ordenAbierta.value, 'registrar-diagnostico', {
      diagnostico: formDiagnostico.diagnostico.trim(),
      plan_solucion: formDiagnostico.plan_solucion.trim(),
    })
    const requiereCompra = formDiagnostico.requiere_compra
    cerrarOrden()
    vista.value = requiereCompra ? 'cotizaciones' : 'trabajo'
  } catch (e) { alert(e.message) }
}

function adjuntarCotizacionesR02(datos) {
  cotizacionesFormulario.value?.adjuntar(datos)
}

async function guardarBorradorCompra() {
  try {
    const fd = new FormData()
    for (const campo of ['producto_requerido','especificacion_producto','cantidad_requerida','costo_estimado']) fd.append(campo, formComponente[campo] ?? '')
    adjuntarCotizacionesR02(fd)
    if (formComponente.informe) fd.append('informe_compra', formComponente.informe)
    const d = await postAccion(ordenAbierta.value, 'guardar-borrador-requerimiento', fd, true)
    if(d.requerimiento) ordenAbierta.value=d.requerimiento
    cotizacionesFormulario.value?.limpiar()
    alert('Borrador guardado. Puede continuar después desde Cotizaciones y requerimientos.')
  } catch(e) { alert(e.message) }
}

async function enviarRequerimiento() {
  if (!formComponente.costo_estimado || !Number.isFinite(Number(formComponente.costo_estimado)) || Number(formComponente.costo_estimado) < 0) {
    alert('Ingrese un costo estimado válido antes de enviar el requerimiento.')
    return
  }
  if (!(await cotizacionesFormulario.value?.validar())) return
  procesando.value = true
  try {
    const token = localStorage.getItem('sigta_token');
    
    // 1. Guardar diagnóstico primero (solo si aún está en DERIVADO)
    if (ordenAbierta.value.estado_codigo === 'DERIVADO') {
      const respDiag = await fetch(`/api/mantenimiento/requerimientos/${ordenAbierta.value.id}/registrar-diagnostico/`, {
        method: 'POST',
        headers: { Authorization: `Token ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          diagnostico: formDiagnostico.diagnostico.trim(),
          plan_solucion: formDiagnostico.plan_solucion.trim(),
        })
      })
      
      if (!respDiag.ok) {
        const d = await respDiag.json().catch(() => ({}))
        throw new Error(d.detalle || 'Error al guardar el diagnóstico.')
      }
      
      // Marcar localmente para no repetir en caso de que el paso 2 falle
      ordenAbierta.value.estado_codigo = 'EN_MANTENIMIENTO';
    }

    // 2. Solicitar requerimiento
    const datos = new FormData()
    datos.append('producto_requerido', formComponente.producto_requerido.trim())
    datos.append('especificacion_producto', formComponente.especificacion_producto.trim())
    datos.append('cantidad_requerida', String(formComponente.cantidad_requerida || 1))
    if (formComponente.costo_estimado) datos.append('costo_estimado', formComponente.costo_estimado)
    adjuntarCotizacionesR02(datos)
    if (formComponente.informe) datos.append('informe_compra', formComponente.informe)
    
    await postAccion(ordenAbierta.value, 'solicitar-requerimiento', datos, true)
    
    cerrarOrden()
    vista.value = 'compras'
    alert('Requerimiento derivado al Jefe de Mantenimiento para proceder con la solicitud de compra.')
  } catch (e) { alert(e.message) }
  finally { procesando.value = false }
}

/* ---------- Reparación, pruebas e informe ---------- */
function abrirTrabajo(item) {
  itemActivo.value = item
  pasoTrabajo.value = item.resultado_pruebas ? 4 : item.trabajo_realizado ? 3 : 1
  formTrabajo.trabajo_realizado = item.trabajo_realizado || ''
  formTrabajo.observaciones_trabajo = item.observaciones_trabajo || ''
  formPruebas.resultado_pruebas = item.resultado_pruebas || ''
  formInforme.informe_trabajo = item.informe_trabajo || ''
  formInforme.fotografia = null
}

function cerrarTrabajo() {
  itemActivo.value = null
  pasoTrabajo.value = 1
}

async function registrarTrabajo() {
  try {
    await postAccion(itemActivo.value, 'realizar-mantenimiento', {
      trabajo_realizado: formTrabajo.trabajo_realizado.trim(),
      observaciones_trabajo: formTrabajo.observaciones_trabajo.trim(),
    })
    pasoTrabajo.value = 3
    vista.value = 'informes'
  } catch (e) { alert(e.message) }
}

async function registrarPruebas() {
  try {
    await postAccion(itemActivo.value, 'pruebas-tecnicas', {
      resultado_pruebas: formPruebas.resultado_pruebas.trim(),
    })
    pasoTrabajo.value = 4
  } catch (e) { alert(e.message) }
}

function onFotografia(evento) {
  formInforme.fotografia = evento.target.files?.[0] || null
}

async function registrarInforme() {
  if (!formInforme.informe_trabajo.trim()) {
    pasoTrabajo.value = 4
    alert('Debe registrar el informe de trabajo antes de enviarlo a la jefatura.')
    return
  }
  try {
    const firma = await solicitarFirma('Informe técnico de mantenimiento', itemActivo.value.codigo)
    if (!firma) return
    const datos = new FormData()
    datos.append('firma', JSON.stringify(firma))
    datos.append('informe_trabajo', formInforme.informe_trabajo.trim())
    if (formInforme.fotografia) datos.append('fotografia_trabajo', formInforme.fotografia)
    await postAccion(itemActivo.value, 'registrar-informe', datos, true)
    itemActivo.value = null
    alert('Informe enviado. La jefatura verificará el funcionamiento.')
  } catch (e) { alert(e.message) }
}

let intervaloActualizacion = null

onMounted(() => {
  cargar()
  intervaloActualizacion = setInterval(cargar, 30000)
})

onUnmounted(() => {
  cerrarEvidencia()
  if (intervaloActualizacion) clearInterval(intervaloActualizacion)
})
</script>

<style scoped>
*{box-sizing:border-box}.layout{min-height:100vh;background:var(--sigta-fondo);color:var(--sigta-texto);font-family:var(--sigta-fuente)}aside{position:fixed;inset:0 auto 0 0;width:var(--sigta-sidebar);background:var(--sigta-azul);color:var(--sigta-blanco);padding:22px 16px;display:flex;flex-direction:column}.brand,.profile{display:flex;align-items:center;gap:12px}.brand{padding:0 10px 20px;border-bottom:1px solid rgba(255,255,255,.2)}.brand>b{background:var(--sigta-mostaza);color:var(--sigta-azul);padding:14px 10px;border-radius:9px}.brand strong,.brand small,.profile b,.profile small{display:block}.brand strong{font-size:23px}.brand small,.profile small{color:var(--sigta-azul-texto-claro);margin-top:3px}.profile{padding:22px 10px}.profile>i{width:42px;height:42px;border-radius:50%;background:var(--sigta-mostaza);color:var(--sigta-azul);display:grid;place-items:center;font-style:normal;font-weight:900}aside>p{font-size:10px;color:var(--sigta-azul-texto-claro);font-weight:800;letter-spacing:1.4px;margin:14px 10px 8px}aside button{border:0;background:transparent;color:var(--sigta-blanco);border-radius:8px;padding:12px;display:flex;gap:11px;align-items:center;text-align:left;cursor:pointer;margin:2px 0;width:100%}aside button .icon-badge{flex-shrink:0;width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center}aside button em{margin-left:auto;background:rgba(255,255,255,.16);padding:2px 8px;border-radius:10px;font-style:normal}aside button.active,aside button:hover{background:rgba(255,255,255,.13)}.bottom{margin-top:auto;border-top:1px solid rgba(255,255,255,.2);padding-top:10px}.bottom button{width:100%}.bottom .logout{gap:14px!important;border:1px solid var(--sigta-mostaza)!important;border-radius:8px!important;background:transparent!important;color:#fff!important;box-shadow:inset 0 0 0 1px rgba(255,199,44,.35)!important;transition:transform .3s cubic-bezier(.34,1.55,.5,1),background .2s ease,color .2s ease,box-shadow .2s ease!important}.bottom .logout .icono-sigta{color:var(--sigta-mostaza);transition:color .2s ease}.bottom .logout:hover{background:#FFB300!important;color:var(--sigta-azul)!important;transform:scale(1.09)!important;box-shadow:0 14px 32px rgba(255,159,0,.55)!important}.bottom .logout:hover .icono-sigta{color:var(--sigta-azul)}main{margin-left:var(--sigta-sidebar);padding:30px 38px 55px;max-width:1650px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:27px}header small{color:var(--sigta-texto-suave)}h1{font-size:var(--sigta-titulo);margin:6px 0}header p{margin:0;color:var(--sigta-texto-suave)}.refresh{border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-azul);padding:10px 14px;border-radius:8px;cursor:pointer}.hero{background:linear-gradient(120deg,var(--sigta-azul),var(--sigta-azul-medio));color:var(--sigta-blanco);border-radius:13px;padding:28px 30px;display:flex;justify-content:space-between;align-items:center}.hero small,.panel-head small,.hoja-head small{font-size:10px;font-weight:800;letter-spacing:1.4px;color:var(--sigta-mostaza-clara)}.hero h2{font-size:24px;margin:7px 0}.hero p{margin:0;color:var(--sigta-azul-texto-claro)}.hero>span{width:68px;height:68px;border:1px solid var(--sigta-mostaza);border-radius:50%;display:grid;place-items:center;font-weight:900}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:18px 0}.stats article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:19px;display:flex;gap:13px;cursor:pointer}.stats i,.flow i{font-style:normal;width:37px;height:37px;border-radius:8px;display:grid;place-items:center;color:var(--sigta-blanco);font-size:10px;font-weight:900}.blue{background:var(--sigta-azul)}.gold{background:var(--sigta-mostaza);color:var(--sigta-texto)!important}.green{background:var(--sigta-azul-medio)}.navy{background:var(--sigta-azul-medio)}.stats small,.stats b,.stats p{display:block}.stats b{font-size:25px;margin:3px 0}.stats p{font-size:11px;color:var(--sigta-texto-suave);margin:0}.panels{display:grid;grid-template-columns:2fr 1fr;gap:18px}.panel{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:11px;padding:22px}.panel-head h3{margin:5px 0 14px}.flow{width:100%;border:0;border-top:1px solid var(--sigta-borde-suave);background:var(--sigta-blanco);padding:15px 2px;display:flex;gap:13px;align-items:center;text-align:left;cursor:pointer}.flow div{flex:1}.flow b,.flow small{display:block}.flow small{color:var(--sigta-texto-suave);margin-top:4px}.flow>strong{font-size:20px}.copy{color:var(--sigta-texto-suave);font-size:12px;line-height:1.7}.wide{width:100%;padding:10px;border-radius:7px;border:1px solid var(--sigta-borde);cursor:pointer}.primary{background:var(--sigta-azul)!important;color:var(--sigta-blanco)!important;border-color:var(--sigta-azul)!important}.instruction{background:var(--sigta-mostaza-suave);border-left:4px solid var(--sigta-mostaza);padding:14px 17px;margin-bottom:17px;border-radius:7px}.instruction b,.instruction span{display:block}.instruction span{font-size:12px;color:var(--sigta-alerta);margin-top:4px}.alerta{background:var(--sigta-error-fondo);border-left:4px solid var(--sigta-error);padding:14px 17px;margin:0 0 17px;border-radius:7px}.alerta b,.alerta span{display:block}.alerta b{color:var(--sigta-error)}.alerta span{font-size:12px;color:var(--sigta-error);margin-top:4px}.mini-alerta{background:var(--sigta-error-fondo);color:var(--sigta-error);font-size:11px;font-weight:700;padding:7px 9px;border-radius:6px;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.cards article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:10px;padding:19px}.cards article.retorno{border-color:var(--sigta-error);box-shadow:inset 3px 0 var(--sigta-error)}.top{display:flex;justify-content:space-between;gap:8px}.top span{font-size:12px;font-weight:800;color:var(--sigta-azul)}.top em{font-size:10px;background:var(--sigta-azul-tenue);padding:4px 8px;border-radius:10px;font-style:normal;white-space:nowrap}.cards h3{font-size:17px;margin:15px 0 7px}.cards article>p{font-size:12px;color:var(--sigta-texto-suave);min-height:42px}.datos{list-style:none;margin:0 0 10px;padding:0;display:grid;gap:4px}.datos li{display:flex;justify-content:space-between;gap:10px;font-size:11px;border-bottom:1px dashed var(--sigta-borde-suave);padding-bottom:3px}.datos b{color:var(--sigta-texto-suave)}.datos span{color:var(--sigta-texto-suave);text-align:right}.adjunto{display:inline-block;font-size:11px;color:var(--sigta-azul);margin-bottom:10px;text-decoration:none}.actions{display:flex;gap:7px;border-top:1px solid var(--sigta-borde-suave);padding-top:13px;margin-top:10px}.actions button{flex:1;padding:9px 6px;border-radius:7px;border:1px solid var(--sigta-borde);background:var(--sigta-blanco);color:var(--sigta-texto);font-weight:700;cursor:pointer}.actions button:disabled{opacity:.55;cursor:not-allowed}.empty{text-align:center;background:var(--sigta-blanco);border:1px dashed var(--sigta-borde);padding:65px;border-radius:10px;color:var(--sigta-texto-suave)}.empty>span{font-size:31px;color:var(--sigta-exito)}.campo{display:block;margin:14px 0;font-size:12px;font-weight:700;color:var(--sigta-texto)}.campo input,.campo select,.campo textarea{display:block;width:100%;margin-top:6px;padding:9px 11px;border:1px solid var(--sigta-borde);border-radius:7px;font-family:inherit;font-size:13px;font-weight:400;color:var(--sigta-texto)}.hoja{max-width:820px}.hoja-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.hoja-head h3{margin:5px 0 0}.compuerta{border:1px solid var(--sigta-borde);border-radius:8px;padding:12px 15px;margin:16px 0;display:flex;gap:22px;align-items:center}.compuerta legend{font-size:12px;font-weight:700;color:var(--sigta-texto);padding:0 6px}.compuerta label{font-size:13px;display:flex;align-items:center;gap:6px;font-weight:600}.compuerta input{margin:0}.detalle-modal-backdrop{position:fixed;inset:0;background:rgba(18,58,107,.55);display:grid;place-items:center;padding:20px;z-index:20}.detalle-modal{background:var(--sigta-blanco);border-radius:14px;width:min(700px,100%);max-height:88vh;display:flex;flex-direction:column}.detalle-modal-header{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--sigta-borde-suave)}.detalle-modal-header h3{margin:0}.detalle-modal-header small{color:var(--sigta-texto-suave)}.detalle-modal-close{border:0;background:transparent;font-size:20px;cursor:pointer;color:var(--sigta-texto-suave)}.detalle-modal-body{padding:20px 24px;overflow-y:auto;display:grid;gap:14px}.detalle-fila{display:grid;grid-template-columns:1fr 1fr;gap:14px}.detalle-campo b{display:block;font-size:11px;color:var(--sigta-texto-suave);margin-bottom:4px}.detalle-campo span,.detalle-campo p{font-size:13px;color:var(--sigta-texto);margin:0}
/* ====== MARCA DE AGUA DEL SIDEBAR ====== */
.sidebar-watermark { flex: 1; min-height: 40px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 6px; padding: 8px 0 4px; overflow: hidden; }
.sidebar-watermark img { width: 60%; max-width: 110px; max-height: 90px; object-fit: contain; opacity: .15; }
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

/* ====== NUEVOS ESTILOS: GESTIÓN DE TICKETS (MASTER-DETAIL) ====== */
.gestion-tickets-layout { display: flex; gap: 20px; height: calc(100vh - 160px); overflow: hidden; align-items: stretch; }
.gestion-left { width: 35%; display: flex; flex-direction: column; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; overflow: hidden; }
.gestion-left-header { padding: 15px 20px; border-bottom: 1px solid var(--sigta-borde-suave); display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.gestion-left-header h3 { margin: 0; font-size: 14px; color: var(--sigta-texto); }
.badge { background: #e0e7ff; color: var(--sigta-azul); font-size: 11px; padding: 4px 8px; border-radius: 20px; font-weight: bold; }
.gestion-filtros { padding: 12px 14px; border-bottom: 1px solid var(--sigta-borde-suave); }
.g-buscar { display: flex; align-items: center; gap: 8px; border: 1px solid var(--sigta-borde); border-radius: 8px; padding: 8px 10px; color: var(--sigta-texto-suave); }
.g-buscar input { border: 0; outline: none; flex: 1; font-size: 12.5px; font-family: inherit; color: var(--sigta-texto); }
.gestion-paginacion { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 10px; border-top: 1px solid var(--sigta-borde-suave); font-size: 12px; color: var(--sigta-texto-suave); }
.gestion-paginacion button { width: 28px; height: 28px; border-radius: 6px; border: 1px solid var(--sigta-borde); background: var(--sigta-blanco); cursor: pointer; font-size: 14px; }
.gestion-paginacion button:disabled { opacity: .4; cursor: not-allowed; }
.mini-badge { flex-shrink: 0; width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
.top-left { display: flex; align-items: center; gap: 6px; }
.gestion-lista { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
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
.ticket-header-card { background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; padding: 13px 16px; flex-shrink: 0; }
.t-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
.t-head h2 { margin: 0; font-size: 18px; color: var(--sigta-texto); }
.codigo-badge { font-weight: bold; color: var(--sigta-azul); font-size: 14px; }
.t-meta { margin: 0 0 8px; font-size: 12px; color: var(--sigta-texto-suave); display: flex; gap: 16px; flex-wrap: wrap; }
.desc-box { background: #f8fafc; padding: 7px 10px; border-radius: 8px; font-size: 13px; line-height: 1.35; color: var(--sigta-texto); border: 1px solid var(--sigta-borde-suave); }

.workflow-card { flex: 1; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; }
.wf-header { padding: 10px 16px; border-bottom: 1px solid var(--sigta-borde-suave); font-weight: bold; color: var(--sigta-texto); background: #f8fafc; }
.wf-body { flex: 1; overflow-y: auto; padding: 12px 16px; display: flex; flex-direction: column; position: relative; }
.wf-body::before { content: ''; position: absolute; left: 39px; top: 28px; bottom: 28px; width: 2px; background: var(--sigta-borde-suave); z-index: 1; }

.wf-step { display: flex; margin-bottom: 8px; position: relative; z-index: 2; }
.wf-step:last-child { margin-bottom: 0; }
.step-num { width: 36px; height: 36px; border-radius: 50%; background: var(--sigta-borde); color: var(--sigta-texto-suave); display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; border: 4px solid var(--sigta-blanco); transition: all 0.3s; }
.step-content { margin-left: 16px; flex: 1; background: var(--sigta-blanco); border: 1px solid var(--sigta-borde); border-radius: 10px; padding: 10px 15px; transition: all 0.3s; }
.step-content h4 { margin: 0 0 5px; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }
.step-content p { margin: 0 0 8px; font-size: 12px; color: var(--sigta-texto-suave); }
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
.step-btn { width: 100%; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; border: none; background: var(--sigta-azul); color: var(--sigta-blanco); font-size: 14px; text-align: center; margin-top:10px; }
.error-carga{background:var(--sigta-error-fondo);border-left:4px solid var(--sigta-error);padding:12px 16px;border-radius:7px;margin:-10px 0 17px}.error-carga b,.error-carga span{display:block}.error-carga b{color:var(--sigta-error);font-size:13px}.error-carga span{color:var(--sigta-error);font-size:12px;margin-top:3px}
.detalle-btn{width:100%;background:var(--sigta-blanco);border:1px solid var(--sigta-borde);color:var(--sigta-azul);padding:8px;border-radius:6px;font-weight:700;cursor:pointer;margin:0 0 8px}
.revision-documentos,.registro-resumen,.envio-resumen{display:grid;gap:6px;background:#f8fafc;border:1px solid var(--sigta-borde-suave);border-radius:8px;padding:10px;margin:0 0 8px}.revision-documentos>div{display:grid;gap:2px;padding-bottom:6px;border-bottom:1px solid var(--sigta-borde-suave)}.revision-documentos>div:last-of-type{border-bottom:0;padding-bottom:0}.revision-documentos b,.registro-resumen b,.envio-resumen b{font-size:11px;color:var(--sigta-texto-suave)}.revision-documentos span,.registro-resumen span,.envio-resumen span{font-size:12px;color:var(--sigta-texto);line-height:1.45}.envio-resumen{grid-template-columns:auto 1fr}.envio-resumen b{align-self:start}
.gold-badge{background:#fef3c7;color:#854d0e}.item-meta{margin-top:6px!important;color:var(--sigta-mostaza-oscuro)!important;font-weight:700}.item-meta.next-step{display:inline-block;border:1px solid var(--sigta-mostaza);border-radius:20px;padding:5px 13px;font-size:11px;transition:background .15s ease,color .15s ease}
.cards article.clickable{cursor:pointer;border-top:3px solid var(--accent,var(--sigta-borde))!important;transition:box-shadow .15s ease,transform .15s ease}
.cards article.clickable .item-meta.next-step{color:var(--accent,var(--sigta-mostaza-oscuro))!important;border-color:var(--accent,var(--sigta-mostaza))!important}
.cards article.clickable:hover{box-shadow:0 6px 16px rgba(23,50,79,.1);transform:translateY(-2px)}
.cards article.clickable:hover .item-meta.next-step{background:var(--accent,var(--sigta-mostaza));color:#fff!important;border-color:var(--accent,var(--sigta-mostaza))!important}.selector-vacio{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:var(--sigta-texto-suave)}.selector-vacio>span{font-size:30px;color:var(--sigta-exito)}.evidence-box{display:flex;align-items:center;justify-content:space-between;gap:12px;background:#f8fafc;border:1px solid var(--sigta-borde-suave);border-radius:8px;padding:12px;margin:14px 0}.evidence-info{display:flex;flex-direction:column;gap:3px}.evidence-info strong{font-size:13px}.evidence-info span,.sin-adjunto{font-size:11px;color:var(--sigta-texto-suave)}.evidence-btn{background:var(--sigta-azul);color:var(--sigta-blanco);padding:7px 11px;border-radius:6px;text-decoration:none;font-size:11px;font-weight:700}.confirmacion{display:flex;gap:8px;align-items:flex-start;margin:14px 0 18px;font-size:12px;font-weight:700;line-height:1.45}.confirmacion input{margin:2px 0 0;width:auto}

/* ====== ÓRDENES DE TRABAJO: COLUMNAS POR PRIORIDAD ====== */
.gestion-filtros.standalone{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:0;border:0;margin-bottom:16px}
.gestion-filtros.standalone .g-buscar{flex:1;max-width:420px;background:var(--sigta-blanco)}
.kanban-prioridad{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;align-items:start}
.kanban-col{background:#eef2f7;border:1px solid var(--sigta-borde);border-radius:11px;padding:11px;min-width:0}
.kanban-col.critica{background:#fdeceb;border-color:#f3c2bd}
.kanban-col.alta{background:#fdf3e4;border-color:#f0d5a8}
.kanban-col.media{background:#e8f1fb;border-color:#c3d9f0}
.kanban-col.baja{background:#e8f7ee;border-color:#b9e6c9}
.kanban-col.sin-prioridad{background:#f1f2f4;border-color:#dbdee2}
.kanban-col-head{display:flex;align-items:center;gap:8px;padding:5px 3px 12px}
.kanban-col-head i{width:9px;height:9px;border-radius:50%;background:#789;flex-shrink:0}
.kanban-col.critica .kanban-col-head i{background:var(--sigta-error)}
.kanban-col.alta .kanban-col-head i{background:#E08A1E}
.kanban-col.media .kanban-col-head i{background:#3E7BD6}
.kanban-col.baja .kanban-col-head i{background:#2FA85C}
.kanban-col.sin-prioridad .kanban-col-head i{background:#8892a0}
.kanban-col-head b{font-size:13px;color:var(--sigta-texto)}
.kanban-col-head em{margin-left:auto;font-style:normal;background:var(--sigta-blanco);border-radius:12px;padding:3px 9px;font-size:11px;font-weight:800;color:var(--sigta-texto-suave)}
.kanban-card{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-top:3px solid #789;border-radius:9px;padding:13px;margin-bottom:9px;cursor:pointer;transition:box-shadow .15s,transform .15s}
.kanban-card:hover{box-shadow:0 6px 14px rgba(23,50,79,.09);transform:translateY(-2px)}
.kanban-col.critica .kanban-card{border-top-color:var(--sigta-error)}
.kanban-col.alta .kanban-card{border-top-color:#E08A1E}
.kanban-col.media .kanban-card{border-top-color:#3E7BD6}
.kanban-col.baja .kanban-card{border-top-color:#2FA85C}
.kanban-card .top{margin:0}
.kanban-card h4{margin:8px 0 4px;font-size:13px;color:var(--sigta-texto)}
.kanban-card p{margin:0;font-size:11px;color:var(--sigta-texto-suave)}
.empty-list-mini{text-align:center;padding:18px 8px;font-size:11px;color:var(--sigta-texto-suave)}

/* ====== MODAL DE LA CONSOLA DE DIAGNÓSTICO ====== */
.orden-modal{width:min(1040px,96vw)!important;max-width:1040px!important;max-height:98vh!important;height:98vh!important}
.orden-modal .detalle-modal-body{flex:1 1 auto!important}
.orden-modal .detalle-modal-header{padding:11px 18px}
.orden-modal .detalle-modal-body{padding:10px 18px;gap:8px}
.orden-modal .ticket-header-card{margin-bottom:0}
.orden-modal .workflow-card{overflow:visible}
.orden-modal .wf-body{overflow:visible}

/* ====== EN ESPERA DE COMPRA: MINI-ESTADÍSTICAS Y TARJETAS ====== */
.mini-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 20px}
.mini-stats article{background:var(--sigta-blanco);border:1px solid var(--sigta-borde);border-radius:12px;padding:16px;display:flex;align-items:center;gap:12px}
.mini-stat-icon{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.mini-stat-icon.blue{background:#e8f1fb;color:#3E7BD6}
.mini-stat-icon.orange{background:#fdf3e4;color:#E08A1E}
.mini-stat-icon.green{background:#e8f7ee;color:#2FA85C}
.mini-stat-icon.purple{background:#efe9fb;color:#7B6FD9}
.mini-stats b{display:block;font-size:19px;color:var(--sigta-texto)}
.mini-stats span{display:block;font-size:11px;color:var(--sigta-texto-suave);margin-top:2px;line-height:1.3}

.compra-cards{grid-template-columns:repeat(2,1fr)}
.compra-card{padding:0;overflow:hidden;display:flex;flex-direction:column}
.compra-card-head{display:flex;gap:12px;align-items:flex-start;padding:18px 18px 14px}
.compra-avatar{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.compra-card-title{flex:1;min-width:0}
.compra-card-title small{display:block;font-size:11px;font-weight:800;color:var(--sigta-texto-suave)}
.compra-card-title h3{margin:2px 0 3px;font-size:16px;color:var(--sigta-texto)}
.compra-card-title p{margin:0;font-size:12px;color:var(--sigta-texto-suave)}
.compra-card-title p b{color:var(--sigta-texto-suave);font-weight:700}
.compra-card-head .detalle-pill{display:inline-flex;align-items:center;gap:4px;flex-shrink:0}
.compra-row{display:flex;align-items:center;gap:8px;padding:9px 18px;font-size:12px;color:var(--sigta-texto-suave);border-top:1px dashed var(--sigta-borde-suave)}
.compra-row :deep(.icono-sigta){color:var(--accent,var(--sigta-texto-suave));flex-shrink:0}
.compra-row b{margin-left:auto;color:var(--sigta-texto);font-weight:700;font-size:12.5px}
.compra-footer{margin-top:auto;display:flex;align-items:center;justify-content:space-between;gap:12px;background:#eef6fb;padding:12px 18px}
.compra-info{display:flex;align-items:center;gap:7px;font-size:11.5px;color:var(--sigta-azul);line-height:1.4}
.compra-info :deep(.icono-sigta){flex-shrink:0}
.compra-detalle-btn{display:inline-flex;align-items:center;gap:6px;background:var(--sigta-azul-oscuro,#0f2647);color:#fff;border:0;padding:9px 14px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap;transition:background .15s ease}
.compra-detalle-btn:hover{background:var(--sigta-azul)}
.compra-detalle-btn span{font-size:16px;line-height:1}

/* ====== HISTORIAL: TARJETAS CON COLOR POR ESTADO ====== */
.historial-cards{grid-template-columns:repeat(2,1fr)}
.historial-card{display:flex;flex-direction:column}
.cards article.historial-card{border-top:4px solid var(--accent,var(--sigta-borde))!important}
.historial-card-head{display:flex;gap:12px;align-items:flex-start;margin-bottom:10px}
.historial-avatar{width:42px;height:42px;border-radius:11px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.historial-card-title{flex:1;min-width:0}
.historial-card-title small{display:block;font-size:11px;font-weight:800;color:var(--sigta-texto-suave)}
.historial-card-title h3{margin:2px 0 0!important;font-size:15.5px}
.historial-card-head .detalle-pill{flex-shrink:0;white-space:nowrap}
.historial-card>p{font-size:12px;color:var(--sigta-texto-suave);line-height:1.5;min-height:auto!important;margin:0 0 14px}
.historial-btn{margin-top:auto;width:100%;display:inline-flex;align-items:center;justify-content:center;gap:6px;color:#fff!important;border:0;padding:9px;border-radius:8px;font-size:12.5px;font-weight:700;cursor:pointer;transition:filter .15s ease}
.historial-btn:hover{filter:brightness(.9)}
.historial-btn span{font-size:15px;line-height:1}

/* ====== MODAL "VER DETALLE" (solo lectura) ====== */
.detalle-modal:not(.orden-modal){border-top:4px solid var(--accent,var(--sigta-mostaza))}
.detalle-top-row{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:2px}
.detalle-pill{display:inline-block;padding:5px 13px;border-radius:20px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.3px}
.detalle-pill.outline{background:transparent;border:1px solid var(--sigta-borde);color:var(--sigta-texto-suave)}
.detalle-meta-line{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--sigta-texto-suave)}
.detalle-meta-line :deep(.icono-sigta){color:var(--sigta-texto-suave)}
.detalle-bloque{background:#f8fafc;border-left:3px solid var(--accent,var(--sigta-borde));border-radius:8px;padding:11px 14px}
.detalle-bloque b{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.4px;color:var(--sigta-texto-suave);margin-bottom:5px}
.detalle-bloque b :deep(.icono-sigta){flex-shrink:0;color:var(--accent,var(--sigta-mostaza))}
.detalle-bloque.alerta-bloque b :deep(.icono-sigta){color:var(--sigta-error)}
.detalle-bloque p,.detalle-bloque span{margin:0;font-size:13px;color:var(--sigta-texto);line-height:1.5;white-space:pre-line}
.detalle-bloque.alerta-bloque{background:var(--sigta-error-fondo);border-left-color:var(--sigta-error)}
.detalle-bloque.alerta-bloque b{color:var(--sigta-error)}
.detalle-evidencia-btn{display:inline-flex;align-items:center;gap:7px;background:var(--sigta-azul);color:#fff!important;padding:9px 15px;border-radius:7px;text-decoration:none;font-size:12px;font-weight:700;justify-self:start}
.detalle-evidencia-btn:hover{background:var(--sigta-azul-oscuro,var(--sigta-azul-medio))}

@media(max-width:1050px){.stats{grid-template-columns:1fr 1fr}.panels{grid-template-columns:1fr}.cards{grid-template-columns:1fr 1fr}}@media(max-width:760px){aside{position:static;width:100%}main{margin:0;padding:20px}.stats,.cards,.process-grid{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column;gap:12px}.detalle-fila{grid-template-columns:1fr}.gestion-filtros.standalone{flex-direction:column;align-items:stretch}.gestion-filtros.standalone .g-buscar{max-width:none}}
.cotizaciones-r02{grid-column:1/-1;background:#f7faff;border:1px solid #d7e3f2;border-radius:9px;padding:14px}.cotizaciones-r02 p{margin:7px 0;font-size:12px}.lista-cotizaciones-r02{list-style:none;padding:0;margin:7px 0}.lista-cotizaciones-r02 li{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:7px 0;border-bottom:1px solid #d7e3f2;overflow-wrap:anywhere}.lista-cotizaciones-r02 button{border:1px solid #b8cde1;border-radius:6px;padding:5px 10px;cursor:pointer;background:white;color:#123a6b}.aviso-cotizaciones-r02{color:#a15b09;font-weight:700}
</style>

<style scoped>
.cotizacion-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 16px}.cotizacion-form .step-actions,.cotizacion-form>a{grid-column:1/-1}.kanban-card:focus-visible{outline:2px solid var(--sigta-azul);outline-offset:3px}@media(max-width:650px){.cotizacion-form{grid-template-columns:1fr}}
.sia-gestion .tablero-ordenes{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;align-items:start}.sia-gestion .tablero-ordenes .kanban-col{display:block!important;margin:0;min-height:160px}.orden-datos{display:grid;gap:8px;margin:14px 0}.orden-datos>div{display:flex;justify-content:space-between;gap:10px;font-size:12px}.orden-datos dt{color:#64748b}.orden-datos dd{margin:0;text-align:right;overflow-wrap:anywhere}.orden-ver{width:100%;background:#f5f9ff;color:var(--sigta-azul);border:1px solid #b8cde1;border-radius:7px;padding:10px;font-weight:700;cursor:pointer}.cotizaciones-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.cotizaciones-cards>article{background:#fff;border:1px solid #d6e1ed;border-radius:10px;padding:19px}.cotizaciones-cards h3{font-size:17px;margin:15px 0 7px}.cotizaciones-cards>article>p{color:#64748b;font-size:13px;line-height:1.5}.antecedente-tecnico{margin:16px 0;padding:16px;background:#f6f9fd;border:1px solid #dce6f1;border-radius:10px}.antecedente-tecnico h3{margin:0 0 10px}.antecedente-tecnico p{line-height:1.5;white-space:pre-wrap}.tecnico-visor{position:fixed;inset:0;z-index:1800;background:#082b4fcc;display:grid;place-items:center;padding:20px}.tecnico-visor>section{width:min(1100px,94vw);background:#fff;border-radius:14px;overflow:hidden}.tecnico-visor header{display:flex;justify-content:space-between;align-items:center;background:var(--sigta-azul);padding:16px;color:#fff;margin:0}.tecnico-visor header button{border:1px solid #ffffff55;border-radius:7px;padding:9px;background:transparent;color:#fff;cursor:pointer}.tecnico-visor section>div{height:75vh;padding:16px;display:grid;place-items:center}.tecnico-visor img{max-width:100%;max-height:100%;object-fit:contain}.tecnico-visor iframe{width:100%;height:100%;border:0}
@media(max-width:1150px){.sia-gestion .tablero-ordenes,.cotizaciones-cards{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.sia-gestion .tablero-ordenes,.cotizaciones-cards{grid-template-columns:1fr}.tecnico-visor header>b{display:none}}
</style>

<style scoped>
.mt-menu-item{border:1px solid #ffffff18!important;background:#ffffff07!important;border-radius:8px!important;min-height:52px!important;margin:5px 0!important;padding:10px 12px!important}.mt-menu-item.active{border-color:#ffca2844!important;border-left:3px solid var(--sigta-mostaza)!important;background:#ffffff22!important}.mt-menu-item:hover{background:#ffffff16!important}.mt-detalle-cabecera{display:flex;gap:14px;align-items:center;margin:16px 0;font-size:12px;color:#607795}.mt-estado{display:inline-block;background:#e8f0fa;color:var(--sigta-azul);border-radius:8px;padding:8px 12px;font-weight:700}.mt-componente{margin-top:18px;border:1px solid #d7e3f2;background:#f7faff;border-radius:12px;padding:20px}.mt-componente h3{font-size:16px;margin:0 0 10px}.mt-componente p{font-size:13px;line-height:1.6}.mt-visor-footer{padding:14px 20px;border-top:1px solid #d7e3f2;text-align:right}.mt-visor-footer a{display:inline-block;padding:10px 16px;border-radius:7px;background:var(--sigta-azul);color:white;text-decoration:none;font-size:13px;font-weight:700}.tecnico-visor section>div{height:68vh}.tecnico-visor header>b{font-size:14px;max-width:60%;overflow-wrap:anywhere}
</style>