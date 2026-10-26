<template>
  <div class="layout sigta-role-layout tecnico-menu">
    <aside :class="{ abierto: menuAbierto }">
      <div class="brand-row">
        <div class="brand"><b><img src="/img/emi.jpg" alt="EMI"></b><div><strong>SIA</strong><small>Soporte Técnico</small></div></div>
        <button type="button" class="menu-toggle" :aria-expanded="menuAbierto" aria-label="Mostrar opciones del menú" @click="menuAbierto = !menuAbierto"><span></span><span></span><span></span></button>
      </div>
      <p>MI TRABAJO</p>
      <button v-for="m in menu" :key="m.id" :class="{active:vista===m.id}" @click="irA(m.id)"><IconoSigta class="nav-icon" :style="{color:m.color}" :nombre="m.icono" :tamano="17" />{{ m.nombre }}<em v-if="m.total!==undefined">{{ m.total }}</em></button>
      <div class="bottom"><button class="logout" @click="mostrarLogout = true"><IconoSigta nombre="salir" :tamano="17" />Cerrar sesión</button></div>
    </aside>

    <LogoutModal :visible="mostrarLogout" @cancelar="mostrarLogout = false" @confirmar="confirmarSalida" />
    <TarjetaGuardado :visible="mostrarGuardado" :texto="textoGuardado" :tipo="tipoGuardado" @cerrar="ocultarGuardado" />

    <main>
      <header>
        <div><h1>{{ titulo }}</h1><p>{{ subtitulo }}</p></div>
        <div class="header-actions"><button class="notification-bell" title="Notificaciones" @click="irA('notificaciones')">🔔<b v-if="notificacionesPendientes">{{notificacionesPendientes}}</b></button></div>
      
        <UsuarioHeader @actualizar="cargar" />
      </header>

      <!-- ============================================================
           RESUMEN
      ============================================================= -->
      <NotificacionesView v-if="vista==='notificaciones'" embedded @actualizadas="notificacionesPendientes=$event" />
      <section v-else-if="vista==='resumen'">
        <div class="hero">
          <div><small>ESPECIALISTA</small><h2>{{ saludo }}, {{ primerNombre }}</h2><p>Órdenes de trabajo que requieren su atención.</p></div>
          <span>TI</span>
        </div>

        <div v-if="conRetorno.length" class="alerta">
          <b>⚠ {{ conRetorno.length }} orden(es) devuelta(s): pruebas de usuario fallidas</b>
          <span>{{ conRetorno.map(t=>t.codigo).join(', ') }} — re-evalúe el equipo y repita la reparación.</span>
        </div>

        <div class="stats">
          <article @click="irA('misordenes')"><i class="blue"><IconoSigta nombre="tickets" :tamano="19" /></i><div><small>Órdenes nuevas</small><b>{{ porRecibir.length }}</b><p>asignadas por la jefatura</p></div></article>
          <article @click="irA('curso')"><i class="gold"><IconoSigta nombre="mantenimiento" :tamano="19" /></i><div><small>Trabajos en curso</small><b>{{ trabajosCurso.length }}</b><p>atención técnica activa</p></div></article>
          <article @click="irA('curso')"><i class="navy"><IconoSigta nombre="reloj" :tamano="19" /></i><div><small>En espera de compra</small><b>{{ esperandoCompra.length }}</b><p>flujo en pausa</p></div></article>
          <article @click="irA('curso')"><i class="green"><IconoSigta nombre="alerta" :tamano="19" /></i><div><small>Devueltas / retrabajo</small><b>{{ conRetorno.length }}</b><p>requieren nueva intervención</p></div></article>
        </div>

        <section class="panel"><div class="panel-head"><div><small>TRABAJO PRIORITARIO</small><h3>Órdenes que requieren atención</h3></div></div><div class="priority-list"><article v-for="t in trabajoPrioritario" :key="t.id"><div><b>{{t.codigo}} · {{t.titulo}}</b><small>{{t.ubicacion}} · {{etiquetaEstado(t)}} · {{textoSla(t)}}</small></div><button class="primary" @click="continuarOrden(t)">Continuar trabajo</button></article><div v-if="!trabajoPrioritario.length" class="empty compact">No tienes trabajos prioritarios pendientes.</div></div></section>
      </section>

      <section v-else-if="vista==='misordenes'"><div class="toolbar-unified"><label>⌕ <input v-model="busqueda" placeholder="Buscar orden asignada"></label><span>{{ordenesNuevas.length}} orden(es)</span></div><div class="instruction"><b>Revise antes de iniciar</b><span>Abra la orden para comprobar ubicación, equipo, descripción y evidencia. Desde el detalle podrá recibirla e iniciar el diagnóstico.</span></div><div class="cards"><article v-for="t in ordenesNuevas" :key="t.id"><div class="top"><span>{{t.codigo}}</span><em :class="claseSla(t)">{{etiquetaEstado(t)}}</em></div><h3>{{t.titulo}}</h3><ul class="datos"><li><b>Solicitante</b><span>{{t.solicitante_nombre}}</span></li><li><b>Prioridad / SLA</b><span>{{t.prioridad}} · {{textoSla(t)}}</span></li><li><b>Ubicación</b><span>{{t.ubicacion}}</span></li><li><b>Equipo</b><span>{{t.equipo_afectado}}</span></li><li><b>Asignada</b><span>{{fecha(t.asignado_en)}}</span></li></ul><div class="actions"><button class="primary" @click="verTicket(t)">Revisar orden</button></div></article><div v-if="!ordenesNuevas.length" class="empty"><span>✓</span><h3>No tienes órdenes nuevas</h3><p>Las órdenes recibidas se encuentran en Trabajos en curso.</p></div></div></section>

      <section v-else-if="vista==='curso'"><div class="work-filters"><label>Estado<select v-model="filtroCurso.estado"><option value="">Todos</option><option value="diagnostico">En diagnóstico</option><option value="reparacion">En reparación</option><option value="compra">En espera de compra</option><option value="pruebas">En pruebas</option><option value="retrabajo">Devuelta / retrabajo</option></select></label><label>Prioridad<select v-model="filtroCurso.prioridad"><option value="">Todas</option><option v-for="p in ['BAJA','MEDIA','ALTA','CRITICA']" :key="p">{{p}}</option></select></label><label>Buscar<input v-model="filtroCurso.texto" placeholder="Ticket o asunto"></label></div><div class="cards"><article v-for="t in trabajosFiltrados" :key="t.id"><div class="top"><span>{{t.codigo}}</span><em>{{etiquetaEstado(t)}}</em></div><h3>{{t.titulo}}</h3><ul class="datos"><li><b>Prioridad</b><span>{{t.prioridad}}</span></li><li><b>SLA</b><span>{{textoSla(t)}}</span></li><li v-if="t.estado_compra_componente"><b>Compra</b><span>{{t.estado_compra_componente}}</span></li><li v-if="Number(t.rework_count)"><b>Retrabajo</b><span>{{t.observaciones_usuario}}</span></li></ul><div class="actions"><button class="primary" @click="continuarOrden(t)">Continuar</button></div></article><div v-if="!trabajosFiltrados.length" class="empty"><span>✓</span><h3>No tienes trabajos pendientes</h3></div></div></section>

      <section v-else-if="vista==='cotizaciones'"><div class="cards"><article v-for="t in porCotizar" :key="t.id"><div class="top"><span>{{t.codigo}}</span><em>{{t.estado_compra_componente || 'Pendiente'}}</em></div><h3>{{t.titulo}}</h3><p>{{t.diagnostico}}</p><div class="actions"><button class="primary" @click="continuarOrden(t)">Llenar informe y cotización</button></div></article><div v-if="!porCotizar.length" class="empty">No hay cotizaciones pendientes.</div></div></section>

      <section v-else-if="vista==='historial'" class="panel">
        <div class="toolbar-unified"><label>⌕ <input v-model="busquedaHistorial" placeholder="Buscar por ticket o asunto"></label></div>
        <div class="table-wrap"><table class="history-table"><thead><tr><th>Ticket</th><th>Asunto</th><th>Prioridad</th><th>Estado</th><th>Fecha</th><th></th></tr></thead><tbody><tr v-for="t in historialFiltrado" :key="t.id"><td>{{t.codigo}}</td><td>{{t.titulo}}</td><td>{{t.prioridad||'s/d'}}</td><td>{{etiquetaEstado(t)}}</td><td>{{fecha(t.actualizado_en)}}</td><td><button class="refresh" @click="verTicket(t)">Ver orden</button></td></tr></tbody></table></div>
      </section>

      <!-- Pantallas internas del expediente: no forman parte del menú principal. -->
      <!-- ============================================================
           A. BANDEJA DE ÓRDENES DE TRABAJO
      ============================================================= -->
      <section v-else-if="vista==='ordenes' && !ordenAbierta">
        <div class="instruction"><b>Recibir orden de trabajo</b><span>Revise los datos y la evidencia cargados por el solicitante, y abra la hoja de trabajo para registrar el diagnóstico.</span></div>
        <div v-if="cargando" class="empty">Consultando órdenes…</div>
        <div v-else-if="porRecibir.length" class="cards">
          <article v-for="t in porRecibir" :key="t.id" :class="{ retorno: Number(t.rework_count) > 0 }">
            <div class="top"><span>{{ t.codigo }}</span><em :class="claseSla(t)">{{ etiquetaEstado(t) }}</em></div>
            <h3>{{ t.titulo }}</h3>
            <ul class="datos">
              <li><b>Asignada</b><span>{{ fecha(t.asignado_en) }}</span></li>
              <li><b>Prioridad</b><span>{{ t.prioridad || 's/d' }}</span></li>
              <li><b>SLA</b><span>{{ textoSla(t) }}</span></li>
              <li><b>Aula / ambiente</b><span>{{ t.ubicacion || 's/d' }}</span></li>
              <li v-if="t.referencia_ubicacion"><b>Referencia</b><span>{{ t.referencia_ubicacion }}</span></li>
              <li><b>Equipo</b><span>{{ t.equipo_afectado || 's/d' }}</span></li>
            </ul>
            <p>{{ (t.descripcion||'').slice(0,150) }}</p>
            <button v-if="t.evidencia_archivo_url" type="button" class="evidence-button" @click="abrirVisor(t.evidencia_archivo_url,t.codigo)">👁 Ver evidencia</button>
            <div class="actions">
              <button @click="verTicket(t)">Ver detalle</button>
              <button class="primary" @click="recibirOrden(t)">Recibir orden de trabajo</button>
            </div>
          </article>
        </div>
        <div v-else class="empty"><span>✓</span><h3>Bandeja al día</h3><p>No tiene órdenes de trabajo pendientes de recibir.</p></div>
      </section>

      <!-- ============================================================
           B / C. HOJA DE TRABAJO: DIAGNÓSTICO Y REQUERIMIENTO
      ============================================================= -->
      <section v-else-if="vista==='ordenes' && ordenAbierta" class="panel hoja">
        <div class="hoja-head">
          <div><small>ORDEN DE TRABAJO</small><h3>{{ ordenAbierta.codigo }} — {{ ordenAbierta.titulo }}</h3></div>
          <button class="refresh" @click="cerrarOrden">Cerrar hoja</button>
        </div>

        <div v-if="Number(ordenAbierta.rework_count) > 0" class="alerta">
          <b>⚠ Pruebas de usuario fallidas: re-evaluar equipo</b>
          <span>{{ ordenAbierta.observaciones_usuario || 'El solicitante reportó que el problema no fue resuelto.' }}</span>
        </div>

        <template v-if="!modoComponente">
          <label class="campo">Diagnóstico técnico inicial
            <textarea v-model="formDiagnostico.diagnostico" rows="4" placeholder="Resultado de la inspección técnica del equipo"></textarea>
          </label>
          <label class="campo">Acción recomendada / solución propuesta (opcional)
            <textarea v-model="formDiagnostico.plan_solucion" rows="3" placeholder="Acciones previstas para resolver el problema"></textarea>
          </label>
          <label class="campo">Observaciones
            <textarea v-model="formDiagnostico.observaciones_diagnostico" rows="2" placeholder="Hallazgos adicionales de la inspección"></textarea>
          </label>
          <label class="campo">Evidencia del diagnóstico
            <ArchivoInput type="file" accept="application/pdf,image/*" @change="formDiagnostico.archivo=$event.target.files?.[0]||null" />
          </label>

          <fieldset class="compuerta">
            <legend>¿Requiere compra de repuestos o insumos?</legend>
            <label><input v-model="formDiagnostico.requiere_compra" type="radio" :value="false"> No</label>
            <label><input v-model="formDiagnostico.requiere_compra" type="radio" :value="true"> Sí</label>
          </fieldset>

          <div class="actions">
            <button @click="cerrarOrden">Cancelar</button>
            <button class="primary" :disabled="procesando || !formDiagnostico.diagnostico.trim() || formDiagnostico.requiere_compra===null" @click="guardarDiagnostico">
              Guardar diagnóstico y continuar
            </button>
          </div>
        </template>

        <template v-else>
          <div class="instruction"><b>Realizar requerimiento de componente</b><span>El flujo técnico quedará en pausa hasta que la jefatura evalúe la viabilidad y Almacén entregue el componente.</span></div>
          <label class="campo">Informe de requerimiento
            <textarea v-model="formComponente.componente_requerido" rows="2" placeholder="Componente o insumo solicitado"></textarea>
          </label>
          <label class="campo">Cantidad
            <input v-model="formComponente.cantidad_componente" type="number" min="1">
          </label>
          <label class="campo">Características del componente
            <textarea v-model="formComponente.especificaciones_tecnicas" rows="3" placeholder="Marca, modelo, capacidad y demás especificaciones técnicas"></textarea>
          </label>
          <label class="campo">Justificación
            <textarea v-model="formComponente.justificacion_compra" rows="3" placeholder="Por qué es indispensable para resolver la orden"></textarea>
          </label>
          <label class="campo">Costo estimado (Bs.)
            <input v-monto inputmode="decimal" pattern="[0-9]+([.][0-9]{1,2})?" v-model="formComponente.costo_estimado" type="text" min="0" step="0.01">
          </label>
          <a v-if="ordenAbierta?.informe_compra" :href="ordenAbierta.informe_compra" target="_blank">Ver informe de requerimiento generado</a>
          <CotizacionesRequerimiento ref="cotizacionesFormulario" :expediente="ordenAbierta?.id" :guardadas="ordenAbierta?.cotizaciones || []" :monto="formComponente.costo_estimado" />
          <div class="actions">
            <button @click="cerrarOrden">Cancelar</button>
            <button :disabled="procesando" @click="guardarBorrador">Guardar borrador</button>
            <button class="primary" :disabled="procesando || !formComponente.componente_requerido.trim() || !formComponente.especificaciones_tecnicas.trim() || !formComponente.justificacion_compra.trim()" @click="enviarRequerimiento">Enviar requerimiento</button>
          </div>
        </template>
      </section>

      <!-- ============================================================
           EN ESPERA DE COMPRA
      ============================================================= -->
      <section v-else-if="vista==='compras'">
        <div class="instruction"><b>Requerimientos en curso</b><span>El flujo técnico está en pausa: se reanuda cuando Almacén registra la entrega del componente.</span></div>
        <div v-if="esperandoCompra.length" class="cards">
          <article v-for="t in esperandoCompra" :key="t.id">
            <div class="top"><span>{{ t.codigo }}</span><em>{{ etiquetaEstado(t) }}</em></div>
            <h3>{{ t.titulo }}</h3>
            <div class="purchase-status"><small>PRODUCTO SOLICITADO</small><strong>{{t.componente_requerido || 'Sin especificar'}}</strong><span>{{t.cantidad_componente || 1}} unidad(es) · {{t.especificaciones_tecnicas || 'Sin características registradas'}}</span></div>
            <ul class="datos">
              <li><b>Estado actual</b><span>{{ textoEspera(t) }}</span></li>
              <li><b>Costo estimado</b><span>{{ t.costo_estimado ? `Bs. ${t.costo_estimado}` : 's/d' }}</span></li>
              <li><b>Expediente</b><span>{{ t.codigo_compra_vinculada || 'aún no generado' }}</span></li>
            </ul>
            <button v-if="t.cotizacion_archivo_url" type="button" class="evidence-button purchase-doc" @click="abrirVisor(t.cotizacion_archivo_url,t.codigo)">📄 Ver cotización enviada</button>
            <div class="actions"><button @click="verTicket(t)">Ver detalle</button></div>
          </article>
        </div>
        <div v-else class="empty"><span>✓</span><h3>Sin requerimientos en curso</h3><p>Ninguna orden suya está esperando una compra.</p></div>
      </section>

      <!-- ============================================================
           D. REPARACIÓN, PRUEBAS E INFORME
      ============================================================= -->
      <section v-else-if="['trabajo','informes'].includes(vista)">
        <div class="instruction"><b>Reparación, pruebas e informe técnico</b><span>Documente la intervención, registre las pruebas y eleve el descargo a la jefatura.</span></div>

        <div v-if="!ticketActivo" class="cards">
          <article v-for="t in enTrabajo" :key="t.id" :class="{ retorno: Number(t.rework_count) > 0 }">
            <div class="top"><span>{{ t.codigo }}</span><em>{{ etiquetaEstado(t) }}</em></div>
            <h3>{{ t.titulo }}</h3>
            <div v-if="Number(t.rework_count) > 0" class="mini-alerta">⚠ Pruebas de usuario fallidas: re-evaluar equipo</div>
            <ul class="datos">
              <li><b>Prioridad</b><span>{{ t.prioridad || 's/d' }}</span></li>
              <li><b>SLA</b><span>{{ textoSla(t) }}</span></li>
              <li v-if="t.componente_entregado_en"><b>Componente</b><span>entregado {{ fecha(t.componente_entregado_en) }}</span></li>
            </ul>
            <p>{{ (t.diagnostico||t.descripcion||'').slice(0,150) }}</p>
            <div class="actions">
              <button @click="verTicket(t)">Ver detalle</button>
              <button class="primary" @click="abrirTrabajo(t)">{{ t.solucion ? 'Pruebas e informe' : 'Registrar reparación' }}</button>
            </div>
          </article>
          <div v-if="!enTrabajo.length" class="empty"><span>✓</span><h3>Bandeja al día</h3><p>No hay órdenes en reparación ni pendientes de pruebas.</p></div>
        </div>

        <div v-else class="panel hoja">
          <div class="hoja-head">
            <div><small>HOJA DE TRABAJO</small><h3>{{ ticketActivo.codigo }} — {{ ticketActivo.titulo }}</h3></div>
            <button class="refresh" @click="ticketActivo=null">Volver</button>
          </div>

          <div v-if="Number(ticketActivo.rework_count) > 0" class="alerta">
            <b>⚠ Pruebas de usuario fallidas: re-evaluar equipo</b>
            <span>{{ ticketActivo.observaciones_usuario || 'El solicitante reportó que el problema no fue resuelto.' }}</span>
          </div>

          <template v-if="!ticketActivo.solucion">
            <label class="campo">Detalles de la reparación o instalación realizada
              <textarea v-model="formIntervencion.solucion" rows="5" placeholder="Acciones correctivas aplicadas sobre el equipo"></textarea>
            </label>
            <label class="campo">Acciones realizadas
              <textarea v-model="formIntervencion.acciones_realizadas" rows="3" placeholder="Secuencia de acciones técnicas ejecutadas"></textarea>
            </label>
            <label class="campo">Repuestos o componentes utilizados
              <textarea v-model="formIntervencion.componentes_utilizados" rows="2" placeholder="Opcional"></textarea>
            </label>
            <label class="campo">Evidencia posterior a la intervención
              <ArchivoInput type="file" accept="application/pdf,image/*" @change="formIntervencion.archivo=$event.target.files?.[0]||null" />
            </label>
            <div class="actions">
              <button @click="ticketActivo=null">Cancelar</button>
              <button class="primary" :disabled="procesando || !formIntervencion.solucion.trim()" @click="registrarIntervencion">Guardar reparación</button>
            </div>
          </template>

          <template v-else>
            <p class="copy"><b>Reparación registrada:</b> {{ ticketActivo.solucion }}</p>
            <label class="campo">Resultados de las pruebas técnicas
              <textarea v-model="formPruebas.resultado_pruebas" rows="4" placeholder="Pruebas efectuadas y comportamiento del equipo"></textarea>
            </label>
            <fieldset class="compuerta"><legend>¿El equipo funciona técnicamente?</legend><label><input v-model="formPruebas.funciona_tecnicamente" type="radio" :value="true"> Sí</label><label><input v-model="formPruebas.funciona_tecnicamente" type="radio" :value="false"> No</label></fieldset>
            <label class="campo">Informe técnico con cuadros / evidencia de pruebas<ArchivoInput type="file" accept="application/pdf,image/*" @change="formPruebas.archivo=$event.target.files?.[0]||null" /></label>
            <div v-if="formPruebas.funciona_tecnicamente" class="report-preview"><b>Vista previa automática del informe</b><p><strong>Ticket:</strong> {{ticketActivo.codigo}} · {{ticketActivo.titulo}}<br><strong>Solicitante:</strong> {{ticketActivo.solicitante_nombre}}<br><strong>Diagnóstico:</strong> {{ticketActivo.diagnostico}}<br><strong>Intervención:</strong> {{ticketActivo.solucion}}<br><strong>Pruebas:</strong> {{formPruebas.resultado_pruebas}}<br><strong>Responsable:</strong> {{nombre}}</p></div>
            <label v-if="formPruebas.funciona_tecnicamente" class="campo">Conclusión técnica
              <textarea v-model="formPruebas.informe_tecnico" rows="3" placeholder="Conclusión técnica final"></textarea>
            </label>
            <div class="actions">
              <button @click="ticketActivo=null">Cancelar</button>
              <button class="primary" :disabled="procesando || !formPruebas.resultado_pruebas.trim() || formPruebas.funciona_tecnicamente===null || (formPruebas.funciona_tecnicamente && !formPruebas.informe_tecnico.trim())" @click="enviarInformeTecnico">{{formPruebas.funciona_tecnicamente===false?'Registrar prueba fallida':'Enviar informe técnico'}}</button>
            </div>
          </template>
        </div>
      </section>

      <!-- ============================================================
           APOYO
      ============================================================= -->
      <section v-else-if="vista==='apoyo'">
        <div class="instruction"><b>Tickets de apoyo</b><span>Órdenes donde usted colabora como especialista de apoyo; el responsable es otro técnico.</span></div>
        <div v-if="ticketsApoyo.length" class="cards">
          <article v-for="t in ticketsApoyo" :key="t.id">
            <div class="top"><span>{{ t.codigo }}</span><em>{{ etiquetaEstado(t) }}</em></div>
            <h3>{{ t.titulo }}</h3>
            <p>{{ (t.descripcion||'').slice(0,150) }}</p>
            <div class="actions"><button @click="verTicket(t)">Ver detalle</button></div>
          </article>
        </div>
        <div v-else class="empty"><span>✓</span><h3>Sin tickets de apoyo</h3><p>No participa como apoyo en ninguna orden.</p></div>
      </section>
    </main>

    <!-- ==============================================================
         DETALLE
    =============================================================== -->
    <div v-if="ticketDetalle" class="detalle-modal-backdrop" @click.self="ticketDetalle=null">
      <div class="detalle-modal">
        <div class="detalle-modal-header">
          <div><h3>{{ ticketDetalle.codigo }}</h3><small>{{ ticketDetalle.titulo }}</small></div>
          <button class="detalle-modal-close back-detail" @click="ticketDetalle=null">← Volver</button>
        </div>
        <div class="detalle-modal-body">
          <div class="detalle-fila">
            <div class="detalle-campo"><b>Estado</b><span>{{ etiquetaEstado(ticketDetalle) }}</span></div>
            <div class="detalle-campo"><b>Prioridad</b><span>{{ ticketDetalle.prioridad || 's/d' }}</span></div>
          </div>
          <div class="detalle-fila">
            <div class="detalle-campo"><b>Solicitante</b><span>{{ ticketDetalle.solicitante_nombre }}</span></div>
            <div class="detalle-campo"><b>SLA</b><span>{{ textoSla(ticketDetalle) }}</span></div>
          </div>
          <div class="detalle-campo"><b>Descripción</b><p>{{ ticketDetalle.descripcion || 's/d' }}</p></div>
          <div class="detalle-fila">
            <div class="detalle-campo"><b>Ubicación</b><span>{{ ticketDetalle.ubicacion || 's/d' }}<template v-if="ticketDetalle.referencia_ubicacion"><br><small>{{ ticketDetalle.referencia_ubicacion }}</small></template></span></div>
            <div class="detalle-campo"><b>Equipo afectado</b><span>{{ ticketDetalle.equipo_afectado || 's/d' }}</span></div>
          </div>
          <div class="detalle-campo" v-if="ticketDetalle.diagnostico"><b>Diagnóstico</b><p>{{ ticketDetalle.diagnostico }}</p></div>
          <div class="detalle-campo" v-if="ticketDetalle.plan_solucion"><b>Plan de solución</b><p>{{ ticketDetalle.plan_solucion }}</p></div>
          <div class="detalle-campo" v-if="ticketDetalle.componente_requerido"><b>Componente requerido</b><p>{{ ticketDetalle.componente_requerido }} — {{ ticketDetalle.especificaciones_tecnicas || 'sin especificaciones' }} — Bs. {{ ticketDetalle.costo_estimado || 's/d' }}</p></div>
          <div class="detalle-campo" v-if="ticketDetalle.motivo_no_viable"><b>Compra no viable</b><p>{{ ticketDetalle.motivo_no_viable }}</p></div>
          <ActasRecepcionTecnico v-if="ticketDetalle.compra_vinculada?.id" :compra-id="ticketDetalle.compra_vinculada.id" />
          <div class="detalle-campo" v-if="ticketDetalle.codigo_compra_vinculada"><b>Expediente de compra</b><span>{{ ticketDetalle.codigo_compra_vinculada }}</span></div>
          <div class="detalle-campo" v-if="ticketDetalle.solucion"><b>Intervención realizada</b><p>{{ ticketDetalle.solucion }}</p></div>
          <div class="detalle-campo" v-if="ticketDetalle.resultado_pruebas"><b>Resultado de pruebas técnicas</b><p>{{ ticketDetalle.resultado_pruebas }}</p></div>
          <div class="detalle-campo" v-if="ticketDetalle.informe_tecnico"><b>Informe técnico</b><p>{{ ticketDetalle.informe_tecnico }}</p></div>
          <div class="detalle-campo" v-if="ticketDetalle.observaciones_usuario"><b>Observaciones del solicitante</b><p>{{ ticketDetalle.observaciones_usuario }}</p></div>
          <div class="evidence-card" v-if="ticketDetalle.evidencia_archivo_url"><img v-if="esImagen(ticketDetalle.evidencia_archivo_url)" :src="ticketDetalle.evidencia_archivo_url" alt="Evidencia del solicitante"><div><b>Evidencia del solicitante</b><small>{{nombreArchivo(ticketDetalle.evidencia_archivo_url)}}</small><button type="button" class="evidence-button" @click="abrirVisor(ticketDetalle.evidencia_archivo_url,ticketDetalle.codigo)">{{esImagen(ticketDetalle.evidencia_archivo_url)?'👁 Ver evidencia':'📄 Visualizar documento'}}</button></div></div>
          <div class="evidence-card" v-if="ticketDetalle.cotizacion_archivo_url"><div class="doc-icon">PDF</div><div><b>Cotización</b><small>Documento asociado al requerimiento</small><button type="button" class="evidence-button" @click="abrirVisor(ticketDetalle.cotizacion_archivo_url,ticketDetalle.codigo)">📄 Visualizar documento</button></div></div>
          <div v-if="ticketDetalle.estado_codigo==='ASIGNADO'" class="receive-panel"><div><b>¿La información es suficiente?</b><small>Al recibir la orden se abrirá la hoja de diagnóstico técnico.</small></div><button class="primary" :disabled="procesando" @click="recibirDesdeDetalle(ticketDetalle)">{{procesando?'Recibiendo...':'Recibir orden e iniciar diagnóstico'}}</button></div>
        </div>
      </div>
    </div>
    <div v-if="visor.url" class="message-backdrop evidence-viewer" @click.self="cerrarVisor"><section><header><button type="button" @click="cerrarVisor">← Volver al expediente</button><div><small>EVIDENCIA DE LA ORDEN</small><h3>{{visor.codigo}}</h3></div><button type="button" aria-label="Cerrar" @click="cerrarVisor">×</button></header><div class="viewer-body"><img v-if="esImagen(visor.url)" :src="visor.url" alt="Evidencia ampliada"><iframe v-else :src="visor.url" title="Documento de evidencia"></iframe></div></section></div>
  </div>
</template>

<script setup>
import CotizacionesRequerimiento from '../components/CotizacionesRequerimiento.vue'
const cotizacionesFormulario = ref(null)

import ActasRecepcionTecnico from '../components/ActasRecepcionTecnico.vue'
import { solicitarFirma } from '../utils/firma'
import DocumentosExpediente from '../components/DocumentosExpediente.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import NotificacionesView from './NotificacionesView.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LogoutModal from '../components/LogoutModal.vue'
import IconoSigta from '../components/IconoSigta.vue'
import TarjetaGuardado from '../components/TarjetaGuardado.vue'
import { usarGuardado } from '../utils/guardado.js'

const router = useRouter()
const route = useRoute()
const { mostrar: mostrarGuardado, texto: textoGuardado, tipo: tipoGuardado, animar: animarGuardado, animarError, ocultar: ocultarGuardado } = usarGuardado()
const usuario = ref(JSON.parse(localStorage.getItem('sigta_usuario') || '{}'))
const seccionesValidas = ['resumen','misordenes','curso','cotizaciones','trabajo','informes','compras','historial','notificaciones']
const vistaInicial = seccionesValidas.includes(String(route.query.vista)) ? String(route.query.vista) : 'resumen'
const vista = ref(vistaInicial)
const menuAbierto = ref(false)
const tickets = ref([])
const notificacionesPendientes = ref(0)
const cargando = ref(false)
const procesando = ref(false)
const ticketActivo = ref(null)
const ordenAbierta = ref(null)
const modoComponente = ref(false)
const ticketDetalle = ref(null)
const busqueda = ref('')
const busquedaHistorial = ref('')
const filtroCurso = reactive({ estado: '', prioridad: '', texto: '' })
const visor = reactive({ url: '', codigo: '' })

const nombre = computed(() => usuario.value.nombre || usuario.value.nombre_completo || 'Especialista')
const primerNombre = computed(() => nombre.value.split(' ')[0])
const iniciales = computed(() => nombre.value.split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase())
const saludo = computed(() => new Date().getHours() < 12 ? 'Buenos días' : new Date().getHours() < 19 ? 'Buenas tardes' : 'Buenas noches')

/* ==========================================================
   BANDEJAS

   Los estados del BPMN se muestran como etiquetas sobre los
   estados reales del ticket. EN_DIAGNOSTICO registra la recepción;
   la espera de compra combina EN_EJECUCION con
   EN_EJECUCION combinados con el estado del requerimiento de
   componente (SOLICITADA / VIABLE / ENTREGADA).
========================================================== */

const misTickets = computed(() => tickets.value.filter(t => Number(t.tecnico_asignado) === Number(usuario.value.id)))

// "Esperando compra": el requerimiento fue enviado y todavía no llega el
// componente. Mientras tanto el backend rechaza registrar la intervención.
const enEsperaDeCompra = t => ['SOLICITADA', 'VIABLE'].includes(t.estado_compra_componente)

const porRecibir = computed(() => misTickets.value.filter(t => t.estado_codigo === 'ASIGNADO'))
const trabajosCurso = computed(() => misTickets.value.filter(t => ['EN_DIAGNOSTICO','EN_EJECUCION'].includes(t.estado_codigo)))
const esperandoCompra = computed(() => misTickets.value.filter(t => t.estado_codigo === 'EN_EJECUCION' && enEsperaDeCompra(t)))
const porIntervenir = computed(() => misTickets.value.filter(t => t.estado_codigo === 'EN_EJECUCION' && !t.solucion && !enEsperaDeCompra(t)))
const porProbar = computed(() => misTickets.value.filter(t => t.estado_codigo === 'EN_EJECUCION' && !!t.solucion))
const enTrabajo = computed(() => vista.value==='informes' ? porProbar.value : porIntervenir.value)
const porCotizar = computed(() => trabajosCurso.value.filter(t=>t.estado_codigo==='EN_EJECUCION' && (t.requiere_compra || t.estado_compra_componente==='BORRADOR') && !enEsperaDeCompra(t) && t.estado_compra_componente!=='ENTREGADA'))
const conRetorno = computed(() => misTickets.value.filter(t => Number(t.rework_count) > 0 && t.estado_codigo === 'EN_EJECUCION'))
const ticketsApoyo = computed(() => tickets.value.filter(t => (t.especialistas_apoyo || []).map(Number).includes(Number(usuario.value.id))))
const ordenesNuevas = computed(() => porRecibir.value.filter(t => !busqueda.value.trim() || `${t.codigo} ${t.titulo}`.toLowerCase().includes(busqueda.value.toLowerCase())))
function etapaCurso(t){if(Number(t.rework_count)>0)return'retrabajo';if(t.estado_codigo==='EN_DIAGNOSTICO')return'diagnostico';if(enEsperaDeCompra(t))return'compra';return t.solucion?'pruebas':'reparacion'}
const trabajosFiltrados = computed(() => trabajosCurso.value.filter(t => (!filtroCurso.estado || etapaCurso(t)===filtroCurso.estado) && (!filtroCurso.prioridad || t.prioridad===filtroCurso.prioridad) && (!filtroCurso.texto.trim() || `${t.codigo} ${t.titulo}`.toLowerCase().includes(filtroCurso.texto.toLowerCase()))))
const trabajoPrioritario = computed(() => [...porRecibir.value,...trabajosCurso.value].sort((a,b)=>(a.sla_restante_minutos??Infinity)-(b.sla_restante_minutos??Infinity)).slice(0,5))

const historialFiltrado = computed(() => {
  const q = busquedaHistorial.value.trim().toLowerCase()
  return misTickets.value.filter(t => ['EN_VERIFICACION','PENDIENTE_CONFORMIDAD','PENDIENTE_INFORME_FINAL','CERRADO','CERRADO_SIN_COMPRA','FINALIZADO','RECHAZADO'].includes(t.estado_codigo) && (!q || `${t.codigo} ${t.titulo}`.toLowerCase().includes(q)))
})

const menu = computed(() => [
  { id: 'resumen', icono: 'inicio', nombre: 'Dashboard', color: '#F2C400' },
  { id: 'misordenes', icono: 'tickets', nombre: 'Mis órdenes', total: porRecibir.value.length, color: '#3E7BD6' },
  { id: 'curso', icono: 'actividades', nombre: 'Trabajos en curso', total: trabajosCurso.value.length, color: '#C79A1E' },
  { id: 'cotizaciones', icono: 'compras', nombre: 'Cotizaciones y requerimientos', total: porCotizar.value.length, color: '#7B6FD9' },
  { id: 'trabajo', icono: 'editar', nombre: 'Trabajos y anotaciones', total: porIntervenir.value.length, color: '#2E9E6B' },
  { id: 'informes', icono: 'conformidad', nombre: 'Pruebas e informes', total: porProbar.value.length, color: '#D9538A' },
  { id: 'compras', icono: 'almacen', nombre: 'Seguimiento de compras', total: esperandoCompra.value.length, color: '#3E7BD6' },
  { id: 'notificaciones', icono: 'notificaciones', nombre: 'Notificaciones', total: notificacionesPendientes.value, color: '#E08A00' },
  { id: 'historial', icono: 'historial', nombre: 'Historial', color: '#6B7C93' },
])

const titulo = computed(() => ({
  notificaciones: 'Notificaciones',
  resumen: 'Panel del Especialista',
  misordenes: 'Mis órdenes',
  curso: 'Trabajos en curso',
  cotizaciones: 'Cotizaciones y requerimientos',
  informes: 'Pruebas e informes técnicos',
  historial: 'Historial de órdenes',
  ordenes: ordenAbierta.value ? 'Inspección y diagnóstico' : 'Bandeja de órdenes de trabajo',
  trabajo: 'Reparación, pruebas e informe',
  compras: 'Requerimientos en espera de compra',
  apoyo: 'Tickets de apoyo',
}[vista.value]))

const subtitulo = computed(() => ({
  notificaciones: 'Decisiones y novedades relacionadas con sus tickets.',
  resumen: 'Diagnóstico, reparación y pruebas técnicas de las órdenes asignadas a usted.',
  misordenes: 'Expedientes asignados a usted, organizados por su etapa actual.',
  curso: 'Órdenes recibidas que todavía requieren atención técnica.',
  historial: 'Consulta de órdenes y trazabilidad de su trabajo técnico.',
  ordenes: 'Órdenes designadas por la jefatura tras clasificar prioridad y SLA.',
  trabajo: 'Intervención técnica y descargo dirigido a la jefatura.',
  compras: 'Órdenes cuyo flujo técnico está en pausa hasta recibir el componente.',
  apoyo: 'Órdenes donde colabora como especialista de apoyo.',
}[vista.value]))

/* ==========================================================
   ETIQUETAS DEL BPMN
========================================================== */

function etiquetaEstado(t) {
  if (!t) return ''
  if (t.estado_codigo === 'ASIGNADO') return Number(t.rework_count) > 0 ? 'Reasignada' : 'Orden asignada'
  if (t.estado_codigo === 'EN_EJECUCION') {
    if (t.estado_compra_componente === 'SOLICITADA') return 'Requiere compra'
    if (t.estado_compra_componente === 'VIABLE') return 'En espera de compra'
    if (t.estado_compra_componente === 'ENTREGADA' && !t.solucion) return 'Repuestos entregados'
    return t.solucion ? 'Por probar' : 'En reparación'
  }
  if (t.estado_codigo === 'EN_VERIFICACION') return 'En verificación de jefatura'
  return t.estado_nombre || t.estado_codigo
}

function textoEspera(t) {
  if (t.estado_compra_componente === 'SOLICITADA') return 'Pendiente de que la jefatura evalúe la viabilidad de la compra.'
  return 'Compra en curso: el componente será entregado por Almacén.'
}

function textoSla(t) {
  if (!t?.sla_horas) return 's/d'
  if (t.sla_estado==='CUMPLIDO') return `${t.sla_horas} h · cumplido`
  if (t.sla_estado==='INCUMPLIDO') return `${t.sla_horas} h · atención finalizada fuera de plazo`
  const minutos = Number(t.sla_restante_minutos)
  if (!Number.isFinite(minutos)) return `${t.sla_horas} h`
  if (minutos <= 0) return `${t.sla_horas} h · vencido`
  return `${t.sla_horas} h · quedan ${Math.floor(minutos / 60)}h ${minutos % 60}m`
}

function claseSla(t) {
  return t?.sla_estado === 'VENCIDO' ? 'vencido' : ''
}

function fecha(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' }) : 's/d'
}

/* ==========================================================
   DATOS
========================================================== */

function token() { return localStorage.getItem('sigta_token') }

async function cargar() {
  cargando.value = true
  try {
    const [r,nr] = await Promise.all([fetch('/api/soporte/tickets/', { headers: { Authorization: `Token ${token()}` } }),fetch('/api/soporte/notificaciones/',{headers:{Authorization:`Token ${token()}`}})])
    const d = await r.json().catch(() => ({})),nd=nr.ok?await nr.json():[]
    if (!r.ok) throw new Error(d.detalle || 'No fue posible actualizar las órdenes.')
    tickets.value = Array.isArray(d) ? d : (d.results || [])
    const ns=Array.isArray(nd)?nd:nd.results||[];notificacionesPendientes.value=ns.filter(n=>!n.leida).length
    // Mantiene sincronizada la orden abierta tras cada acción.
    if (ordenAbierta.value) ordenAbierta.value = tickets.value.find(t => t.id === ordenAbierta.value.id) || null
    if (ticketActivo.value) ticketActivo.value = tickets.value.find(t => t.id === ticketActivo.value.id) || null
    if(route.query.ticket&&!ticketDetalle.value)ticketDetalle.value=tickets.value.find(t=>String(t.id)===String(route.query.ticket))||null
  } finally {
    cargando.value = false
  }
}

async function postAccion(ticket, endpoint, body, esFormData = false) {
  if(endpoint === 'pruebas-tecnicas'){const firma=await solicitarFirma('Informe técnico de soporte',ticket.codigo);if(!firma)throw new Error('Firma cancelada.');if(esFormData)body.append('firma',JSON.stringify(firma));else body={...body,firma}}
  if (procesando.value) throw new Error('La acción ya se está procesando.')
  procesando.value = true
  try {
    const headers = { Authorization: `Token ${token()}` }
    if (!esFormData) headers['Content-Type'] = 'application/json'
    const r = await fetch(`/api/soporte/tickets/${ticket.id}/${endpoint}/`, {
      method: 'POST',
      headers,
      body: esFormData ? body : JSON.stringify(body || {}),
    })
    const texto = await r.text()
    let d = {}
    try { d = texto ? JSON.parse(texto) : {} } catch { d = {} }
    const primerError = Object.values(d).find(valor => typeof valor === 'string')
    if (!r.ok) throw new Error(d.detalle || primerError || texto || `No fue posible completar la acción (HTTP ${r.status}).`)
    if (d.ticket) {
      const indice = tickets.value.findIndex(item => item.id === d.ticket.id)
      if (indice >= 0) tickets.value.splice(indice, 1, d.ticket)
      else tickets.value.unshift(d.ticket)
      if (ordenAbierta.value?.id === d.ticket.id) ordenAbierta.value = d.ticket
      if (ticketActivo.value?.id === d.ticket.id) ticketActivo.value = d.ticket
    }
    try { await cargar() } catch (error) { console.error('No se pudo refrescar la bandeja:', error) }
    return d
  } finally {
    procesando.value = false
  }
}

function irA(id) {
  vista.value = id
  menuAbierto.value = false
  ordenAbierta.value = null
  ticketActivo.value = null
  modoComponente.value = false
}

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

function verTicket(t) { ticketDetalle.value = t }
function esImagen(url) { return /\.(png|jpe?g|gif|webp)(\?|$)/i.test(url || '') }
function nombreArchivo(url) { return decodeURIComponent((url || '').split('/').pop().split('?')[0]) }
function abrirVisor(url, codigo) { visor.url = url; visor.codigo = codigo }
function cerrarVisor() { visor.url = ''; visor.codigo = '' }

async function aceptarOrden(t) {
  if (procesando.value) return
  try {
    const datos = await postAccion(t, 'iniciar-atencion', {})
    recibirOrden(datos.ticket || tickets.value.find(item => item.id === t.id) || t)
    vista.value = 'ordenes'
    mostrarMensaje('Orden recibida', `${t.codigo} pasó a Trabajos en curso. Registre el diagnóstico técnico.`)
    return true
  } catch (e) { mostrarMensaje('No fue posible recibir la orden', String(e.message), 'error'); return false }
}

async function recibirDesdeDetalle(t) { if (await aceptarOrden(t)) ticketDetalle.value = null }

function continuarOrden(t) {
  if (t.estado_codigo === 'ASIGNADO') { aceptarOrden(t); return }
  if (t.estado_codigo === 'EN_DIAGNOSTICO') { recibirOrden(t); vista.value = 'ordenes'; return }
  if (t.estado_codigo === 'EN_EJECUCION' && (t.estado_compra_componente === 'BORRADOR' || (t.requiere_compra && !t.estado_compra_componente))) {
    recibirOrden(t)
    modoComponente.value = true
    vista.value = 'ordenes'
    return
  }
  if (t.estado_codigo === 'EN_EJECUCION' && !enEsperaDeCompra(t)) {
    abrirTrabajo(t)
    vista.value = t.solucion ? 'informes' : 'trabajo'
    return
  }
  verTicket(t)
}

function mostrarMensaje(titulo, texto, tipo = 'ok') {
  const combinado = titulo && texto ? `${titulo}. ${texto}` : (texto || titulo)
  if (tipo === 'error') animarError(combinado)
  else animarGuardado(combinado)
}

/* ==========================================================
   A. RECIBIR ORDEN DE TRABAJO
========================================================== */

const formDiagnostico = reactive({ diagnostico: '', plan_solucion: '', observaciones_diagnostico: '', requiere_compra: null, archivo: null })
const formComponente = reactive({ via_compra: 'CAJA_CHICA', componente_requerido: '', cantidad_componente: 1, especificaciones_tecnicas: '', justificacion_compra: '', proveedor_cotizacion: '', costo_estimado: '', archivo: null })
const formIntervencion = reactive({ solucion: '', acciones_realizadas: '', componentes_utilizados: '', archivo: null })
const formPruebas = reactive({ resultado_pruebas: '', funciona_tecnicamente: null, informe_tecnico: '', archivo: null })

function recibirOrden(t) {
  ordenAbierta.value = t
  modoComponente.value = false
  formDiagnostico.diagnostico = ''
  formDiagnostico.plan_solucion = ''
  formDiagnostico.observaciones_diagnostico = t.observaciones_diagnostico || ''
  formDiagnostico.requiere_compra = null
  Object.assign(formComponente, { via_compra:t.via_compra||'CAJA_CHICA', componente_requerido:t.componente_requerido||'', cantidad_componente:t.cantidad_componente||1, especificaciones_tecnicas:t.especificaciones_tecnicas||'', justificacion_compra:t.justificacion_compra||'', proveedor_cotizacion:t.proveedor_cotizacion||'', costo_estimado:t.costo_estimado||'', archivo:null })
}

function cerrarOrden() {
  ordenAbierta.value = null
  modoComponente.value = false
}

/* ==========================================================
   B. DIAGNÓSTICO Y COMPUERTA "¿REQUIERE COMPRA?"
========================================================== */

async function guardarDiagnostico() {
  try {
    const datos = new FormData()
    datos.append('diagnostico', formDiagnostico.diagnostico.trim())
    datos.append('plan_solucion', formDiagnostico.plan_solucion.trim())
    datos.append('observaciones_diagnostico', formDiagnostico.observaciones_diagnostico.trim())
    datos.append('requiere_compra', String(formDiagnostico.requiere_compra))
    if (formDiagnostico.archivo) datos.append('evidencia_diagnostico', formDiagnostico.archivo)
    await postAccion(ordenAbierta.value, 'registrar-diagnostico', datos, true)
    if (formDiagnostico.requiere_compra) {
      // El requerimiento se registra sobre el ticket ya en ejecución.
      cerrarOrden()
      vista.value = 'cotizaciones'
    } else {
      cerrarOrden()
      vista.value = 'trabajo'
    }
  } catch (e) { mostrarMensaje('No se pudo completar la acción', String(e.message), 'error') }
}

/* ==========================================================
   C. REQUERIMIENTO DE COMPONENTE
========================================================== */

function datosRequerimiento() {
  const datos = new FormData()
  for (const campo of ['componente_requerido','cantidad_componente','especificaciones_tecnicas','justificacion_compra','proveedor_cotizacion','costo_estimado']) datos.append(campo, formComponente[campo] ?? '')
  cotizacionesFormulario.value?.adjuntar(datos)
  return datos
}

async function guardarBorrador() {
  try {
    await postAccion(ordenAbierta.value, 'guardar-borrador-requerimiento', datosRequerimiento(), true)
    cotizacionesFormulario.value?.limpiar()
    mostrarMensaje('Borrador guardado', 'Puede salir y continuar después desde Trabajos en curso.')
  } catch (e) { mostrarMensaje('No se pudo guardar el borrador', String(e.message), 'error') }
}

async function enviarRequerimiento() {
  if (!(await cotizacionesFormulario.value?.validar())) return
  try {
    await postAccion(ordenAbierta.value, 'solicitar-requerimiento-componente', datosRequerimiento(), true)
    cerrarOrden()
    vista.value = 'curso'
    mostrarMensaje('Requerimiento enviado', 'El Jefe UTIC recibió el requerimiento. La orden permanece visible en Trabajos en curso.')
  } catch (e) { mostrarMensaje('No se pudo enviar el requerimiento', String(e.message), 'error') }
}

/* ==========================================================
   D. REPARACIÓN, PRUEBAS E INFORME TÉCNICO
========================================================== */

function abrirTrabajo(t) {
  ticketActivo.value = t
  formIntervencion.solucion = ''
  formPruebas.resultado_pruebas = ''
  formPruebas.informe_tecnico = ''
}

async function registrarIntervencion() {
  try {
    const datos = new FormData()
    datos.append('solucion', formIntervencion.solucion.trim())
    datos.append('acciones_realizadas', formIntervencion.acciones_realizadas.trim())
    datos.append('componentes_utilizados', formIntervencion.componentes_utilizados.trim())
    if (formIntervencion.archivo) datos.append('evidencia_intervencion', formIntervencion.archivo)
    await postAccion(ticketActivo.value, 'registrar-intervencion', datos, true)
    vista.value = 'informes'
  } catch (e) { mostrarMensaje('No se pudo completar la acción', String(e.message), 'error') }
}

async function enviarInformeTecnico() {
  try {
    const datos = new FormData()
    datos.append('resultado_pruebas', formPruebas.resultado_pruebas.trim())
    datos.append('funciona_tecnicamente', String(formPruebas.funciona_tecnicamente))
    datos.append('informe_tecnico', formPruebas.informe_tecnico.trim())
    if (formPruebas.archivo) datos.append('evidencia_pruebas', formPruebas.archivo)
    await postAccion(ticketActivo.value, 'pruebas-tecnicas', datos, true)
    ticketActivo.value = null
    mostrarMensaje(formPruebas.funciona_tecnicamente ? 'Informe enviado correctamente' : 'Prueba fallida registrada', formPruebas.funciona_tecnicamente ? 'El ticket fue enviado al solicitante para verificar el funcionamiento.' : 'La orden continúa en proceso para una nueva intervención.')
  } catch (e) { mostrarMensaje('No se pudo registrar la prueba', String(e.message), 'error') }
}

onMounted(cargar)
watch(() => route.query, consulta => {
  if (seccionesValidas.includes(String(consulta.vista))) irA(String(consulta.vista))
  if (consulta.ticket) {
    ticketDetalle.value = tickets.value.find(t => String(t.id) === String(consulta.ticket)) || null
    if (!ticketDetalle.value) cargar()
  }
})
</script>

<style scoped>
/* Mismo distintivo de icono que el resto de los paneles por rol. */
aside button .icon-badge { flex-shrink: 0; width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }

*{box-sizing:border-box}.layout{min-height:100vh;background:var(--sigta-azul-tenue);color:var(--sigta-texto);font-family: var(--sigta-fuente)}aside{position:fixed;inset:0 auto 0 0;width:var(--sigta-sidebar);background:var(--sigta-azul);color:white;padding:22px 16px;display:flex;flex-direction:column}.brand,.profile{display:flex;align-items:center;gap:12px}.brand{padding:0 10px 20px;border-bottom:1px solid #ffffff20}.brand>b{background:var(--sigta-mostaza-clara);color:var(--sigta-azul);padding:14px 10px;border-radius:9px}.brand strong,.brand small,.profile b,.profile small{display:block}.brand strong{font-size:23px}.brand small,.profile small{color:var(--sigta-azul-texto-claro);margin-top:3px}.profile{padding:22px 10px}.profile>i{width:42px;height:42px;border-radius:50%;background:var(--sigta-mostaza-clara);color:var(--sigta-azul);display:grid;place-items:center;font-style:normal;font-weight:900}aside>p{font-size:10px;color:var(--sigta-texto-suave);font-weight:800;letter-spacing:1.4px;margin:14px 10px 8px}aside button{border:0;background:transparent;color:var(--sigta-azul-texto-claro);border-radius:8px;padding:12px;display:flex;gap:11px;align-items:center;text-align:left;cursor:pointer;margin:2px 0;width:100%}aside button>span{font-size:10px;font-weight:900;width:28px}aside button :deep(.icono-sigta){flex-shrink:0}aside button em{margin-left:auto;background:#ffffff1c;padding:2px 8px;border-radius:10px;font-style:normal}aside button.active,aside button:hover{background:#ffffff14;box-shadow:inset 3px 0 var(--sigta-mostaza-clara)}.bottom{margin-top:auto;border-top:1px solid #ffffff20;padding-top:10px}.bottom button{width:100%}.bottom .logout{gap:14px!important;border:1px solid var(--sigta-mostaza)!important;border-radius:8px!important;background:transparent!important;color:#fff!important;box-shadow:inset 0 0 0 1px rgba(255,199,44,.35)!important;transition:transform .3s cubic-bezier(.34,1.55,.5,1),background .2s ease,color .2s ease,box-shadow .2s ease!important}.bottom .logout .icono-sigta{color:var(--sigta-mostaza);transition:color .2s ease}.bottom .logout:hover{background:#FFB300!important;color:var(--sigta-azul)!important;transform:scale(1.09)!important;box-shadow:0 14px 32px rgba(255,159,0,.55)!important}.bottom .logout:hover .icono-sigta{color:var(--sigta-azul)}main{margin-left:var(--sigta-sidebar);padding:30px 38px 55px;max-width:1650px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:27px}header small{color:var(--sigta-texto-suave)}h1{font-size:29px;margin:6px 0}header p{margin:0;color:var(--sigta-texto-suave)}.refresh{border:1px solid var(--sigta-azul-texto-claro);background:white;color:var(--sigta-texto-suave);padding:10px 14px;border-radius:8px;cursor:pointer}.hero{background:linear-gradient(120deg,var(--sigta-azul),var(--sigta-texto-suave));color:white;border-radius:13px;padding:28px 30px;display:flex;justify-content:space-between;align-items:center}.hero small,.panel-head small,.hoja-head small{font-size:10px;font-weight:800;letter-spacing:1.4px;color:var(--sigta-mostaza-clara)}.hero h2{font-size:24px;margin:7px 0}.hero p{margin:0;color:var(--sigta-azul-texto-claro)}.hero>span{width:68px;height:68px;border:1px solid #edc65a88;border-radius:50%;display:grid;place-items:center;font-weight:900}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:18px 0}.stats article{background:white;border:1px solid var(--sigta-borde);border-radius:10px;padding:19px;display:flex;gap:13px;cursor:pointer}.stats i,.flow i{font-style:normal;width:37px;height:37px;border-radius:8px;display:grid;place-items:center;color:white;font-size:10px;font-weight:900}.blue{background:var(--sigta-azul)}.gold{background:var(--sigta-mostaza)}.green{background:var(--sigta-azul-medio)}.navy{background:var(--sigta-azul-medio)}.stats small,.stats b,.stats p{display:block}.stats b{font-size:25px;margin:3px 0}.stats p{font-size:11px;color:var(--sigta-texto-suave);margin:0}.panels{display:grid;grid-template-columns:2fr 1fr;gap:18px}.panel{background:white;border:1px solid var(--sigta-borde);border-radius:11px;padding:22px}.panel-head h3{margin:5px 0 14px}.flow{width:100%;border:0;border-top:1px solid var(--sigta-borde);background:white;padding:15px 2px;display:flex;gap:13px;align-items:center;text-align:left;cursor:pointer}.flow div{flex:1}.flow b,.flow small{display:block}.flow small{color:var(--sigta-texto-suave);margin-top:4px}.flow>strong{font-size:20px}.copy{color:var(--sigta-texto-suave);font-size:12px;line-height:1.7}.wide{width:100%;padding:10px;border-radius:7px;border:1px solid var(--sigta-borde);cursor:pointer}.primary{background:var(--sigta-azul)!important;color:white!important;border-color:var(--sigta-azul)!important}.instruction{background:var(--sigta-mostaza-suave);border-left:4px solid var(--sigta-mostaza);padding:14px 17px;margin-bottom:17px;border-radius:7px}.instruction b,.instruction span{display:block}.instruction span{font-size:12px;color:var(--sigta-texto-suave);margin-top:4px}.alerta{background:var(--sigta-error-fondo);border-left:4px solid var(--sigta-error);padding:14px 17px;margin:0 0 17px;border-radius:7px}.alerta b,.alerta span{display:block}.alerta b{color:var(--sigta-error)}.alerta span{font-size:12px;color:var(--sigta-error);margin-top:4px}.mini-alerta{background:var(--sigta-error-fondo);color:var(--sigta-error);font-size:11px;font-weight:700;padding:7px 9px;border-radius:6px;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.cards article{background:white;border:1px solid var(--sigta-borde);border-radius:10px;padding:19px}.cards article.retorno{border-color:var(--sigta-error);box-shadow:inset 3px 0 var(--sigta-error)}.top{display:flex;justify-content:space-between;gap:8px}.top span{font-size:12px;font-weight:800;color:var(--sigta-texto-suave)}.top em{font-size:10px;background:var(--sigta-azul-tenue);padding:4px 8px;border-radius:10px;font-style:normal;white-space:nowrap}.top em.vencido{background:var(--sigta-error-fondo);color:var(--sigta-error)}.cards h3{font-size:17px;margin:15px 0 7px}.cards article>p{font-size:12px;color:var(--sigta-texto-suave);min-height:42px}.datos{list-style:none;margin:0 0 10px;padding:0;display:grid;gap:4px}.datos li{display:flex;justify-content:space-between;gap:10px;font-size:11px;border-bottom:1px dashed var(--sigta-azul-tenue);padding-bottom:3px}.datos b{color:var(--sigta-texto-suave)}.datos span{color:var(--sigta-texto-suave);text-align:right}.adjunto{display:inline-block;font-size:11px;color:var(--sigta-texto-suave);margin-bottom:10px;text-decoration:none}.actions{display:flex;gap:7px;border-top:1px solid var(--sigta-borde);padding-top:13px;margin-top:10px}.actions button{flex:1;padding:9px 6px;border-radius:7px;border:1px solid var(--sigta-borde);background:white;color:var(--sigta-texto-suave);font-weight:700;cursor:pointer}.actions button:disabled{opacity:.55;cursor:not-allowed}.empty{text-align:center;background:white;border:1px dashed var(--sigta-borde);padding:65px;border-radius:10px;color:var(--sigta-texto-suave)}.empty>span{font-size:31px;color:var(--sigta-exito)}.campo{display:block;margin:14px 0;font-size:12px;font-weight:700;color:var(--sigta-texto-suave)}.campo input,.campo select,.campo textarea{display:block;width:100%;margin-top:6px;padding:9px 11px;border:1px solid var(--sigta-azul-texto-claro);border-radius:7px;font-family:inherit;font-size:13px;font-weight:400;color:var(--sigta-texto)}.hoja{max-width:820px}.hoja-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.hoja-head h3{margin:5px 0 0}.compuerta{border:1px solid var(--sigta-borde);border-radius:8px;padding:12px 15px;margin:16px 0;display:flex;gap:22px;align-items:center}.compuerta legend{font-size:12px;font-weight:700;color:var(--sigta-texto-suave);padding:0 6px}.compuerta label{font-size:13px;display:flex;align-items:center;gap:6px;font-weight:600}.compuerta input{margin:0}.detalle-modal-backdrop{position:fixed;inset:0;background:#0d1a31aa;display:grid;place-items:center;padding:20px;z-index:20}.detalle-modal{background:white;border-radius:14px;width:min(700px,100%);max-height:88vh;display:flex;flex-direction:column}.detalle-modal-header{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--sigta-borde)}.detalle-modal-header h3{margin:0}.detalle-modal-header small{color:var(--sigta-texto-suave)}.detalle-modal-close{border:0;background:transparent;font-size:20px;cursor:pointer;color:var(--sigta-texto-suave)}.detalle-modal-body{padding:20px 24px;overflow-y:auto;display:grid;gap:14px}.detalle-fila{display:grid;grid-template-columns:1fr 1fr;gap:14px}.detalle-campo b{display:block;font-size:11px;color:var(--sigta-texto-suave);margin-bottom:4px}.detalle-campo span,.detalle-campo p{font-size:13px;color:var(--sigta-azul);margin:0}@media(max-width:1050px){.stats{grid-template-columns:1fr 1fr}.panels{grid-template-columns:1fr}.cards{grid-template-columns:1fr 1fr}}@media(max-width:720px){aside{position:static;width:100%}main{margin:0;padding:20px}.stats,.cards{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column;gap:12px}.detalle-fila{grid-template-columns:1fr}}
/* El tema global de rol oculta el icono de .stats y apila la tarjeta en
   bloque (pensado para Admin); aquí se restaura el icono junto al texto. */
main .stats article{display:flex!important;align-items:center!important}
main .stats article>i.gold,main .stats article>i.blue,main .stats article>i.green,main .stats article>i.navy{display:flex!important;align-items:center;justify-content:center}
.message-backdrop{position:fixed;inset:0;background:#0d1a3188;display:grid;place-items:center;z-index:80;padding:20px}
.toolbar-unified{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;color:var(--sigta-texto-suave)}.toolbar-unified label{width:360px;background:#fff;border:1px solid var(--sigta-borde);border-radius:8px;padding:10px}.toolbar-unified input{border:0;outline:0;width:90%}.kanban-unified{display:grid;grid-template-columns:repeat(4,minmax(230px,1fr));gap:13px;align-items:start}.kanban-col{background:#eaf0f7;border:1px solid var(--sigta-borde);border-radius:11px;padding:11px}.kanban-title{display:flex;justify-content:space-between;padding:5px 3px 13px}.kanban-title em{font-style:normal;background:#fff;border-radius:12px;padding:3px 8px}.orden-card{background:#fff;border:1px solid var(--sigta-borde);border-radius:9px;padding:14px;margin-bottom:10px}.orden-card.retorno{border-left:4px solid var(--sigta-error)}.orden-card h3{font-size:14px}.compra-indicator{font-size:10px;background:var(--sigta-mostaza-suave);padding:7px;border-radius:6px}.compact{padding:18px}.table-wrap{overflow:auto}.history-table{width:100%;border-collapse:collapse;min-width:700px}.history-table th,.history-table td{text-align:left;padding:11px;border-bottom:1px solid var(--sigta-borde);font-size:12px}.history-table th{color:var(--sigta-texto-suave);font-size:10px;text-transform:uppercase}@media(max-width:1100px){.kanban-unified{grid-template-columns:repeat(2,1fr)}}@media(max-width:720px){.kanban-unified{grid-template-columns:1fr}.toolbar-unified{align-items:flex-start;flex-direction:column;gap:10px}.toolbar-unified label{width:100%}.hoja{max-width:100%}.compuerta{align-items:flex-start;flex-direction:column}}
</style>
<style scoped>
.header-actions{display:flex;gap:9px}.notification-bell{position:relative;border:1px solid var(--sigta-borde);background:#fff;border-radius:8px;padding:8px 12px;cursor:pointer}.notification-bell b{position:absolute;right:-5px;top:-7px;background:var(--sigta-error);color:#fff;border-radius:12px;padding:2px 6px;font-size:10px}@media(max-width:720px){.header-actions{width:100%}.header-actions>*{flex:1}}
</style>
<style scoped>
.evidence-button{display:inline-block;background:var(--sigta-azul)!important;color:#fff!important;border:0;text-decoration:none;padding:9px 13px;border-radius:7px;font-weight:800;font-size:12px;cursor:pointer;transition:background .18s,transform .18s}.evidence-button:hover{background:#174b7c!important;transform:translateY(-1px)}
.purchase-status{display:grid;gap:5px;margin:13px 0;padding:13px;border-radius:9px;background:#f4f8fc;border-left:4px solid var(--sigta-mostaza)}.purchase-status small{color:var(--sigta-texto-suave);font-size:9px;font-weight:900;letter-spacing:1px}.purchase-status strong{color:var(--sigta-azul)}.purchase-status span{font-size:11px;color:var(--sigta-texto-suave);line-height:1.45}.purchase-doc{width:100%;margin:3px 0 7px}.receive-panel{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:15px;border-radius:9px;background:var(--sigta-mostaza-suave);border-left:4px solid var(--sigta-mostaza)}.receive-panel b,.receive-panel small{display:block}.receive-panel small{margin-top:4px;color:var(--sigta-texto-suave)}.receive-panel button{border:0;border-radius:7px;padding:11px 14px;font-weight:800;white-space:nowrap;cursor:pointer}
.decision-notices{display:grid;gap:10px;margin:17px 0}.decision-notices article{display:grid;grid-template-columns:42px 1fr auto;align-items:center;gap:13px;background:#fff7f7;border:1px solid #efc4c4;border-left:4px solid var(--sigta-error);border-radius:9px;padding:14px}.decision-notices i{width:38px;height:38px;display:grid;place-items:center;border-radius:50%;background:var(--sigta-error-fondo);color:var(--sigta-error);font-style:normal;font-weight:900}.decision-notices small,.decision-notices b,.decision-notices span{display:block}.decision-notices small{font-size:9px;color:var(--sigta-error);font-weight:900;letter-spacing:1px}.decision-notices p{margin:4px 0;color:var(--sigta-texto)}.decision-notices span{font-size:11px;color:var(--sigta-texto-suave)}.decision-notices button{border:1px solid var(--sigta-error);background:#fff;color:var(--sigta-error);border-radius:7px;padding:9px 12px;font-weight:800;cursor:pointer}
.evidence-viewer{z-index:100}.evidence-viewer>section{width:min(1000px,92vw);max-height:90vh;background:#fff;border-radius:14px;overflow:hidden}.evidence-viewer header{display:flex;justify-content:space-between;align-items:center;margin:0;padding:15px 18px;background:var(--sigta-azul);color:#fff}.evidence-viewer header button{border:1px solid #ffffff55;background:#ffffff12;color:#fff;border-radius:7px;padding:9px 12px;cursor:pointer}.evidence-viewer header h3{margin:3px 0}.viewer-body{height:min(74vh,760px);padding:18px;display:grid;place-items:center;background:#eef3f8}.viewer-body img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}.viewer-body iframe{width:100%;height:100%;border:0;background:#fff}
@media(max-width:720px){.evidence-button{width:100%}.receive-panel{align-items:stretch;flex-direction:column}.receive-panel button{white-space:normal}.decision-notices article{grid-template-columns:36px 1fr}.decision-notices button{grid-column:1/-1;width:100%}.evidence-viewer>section{width:95vw}.evidence-viewer header>div{display:none}.viewer-body{height:78vh;padding:8px}}
.receive-panel{grid-column:1/-1}.receive-panel>div{flex:1;min-width:0}
</style>
<style scoped>
.detalle-modal{width:min(920px,94vw)}
.detalle-modal-header{background:var(--sigta-azul);color:#fff}.detalle-modal-header small{color:#d8e5f2}.back-detail{width:auto;color:#fff!important;font-size:13px!important;font-weight:700}
.detalle-modal-body{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.detalle-campo{background:#f6f9fc;border-radius:8px;padding:12px}.detalle-campo:has(>p){grid-column:1/-1}
.evidence-card{grid-column:1/-1;display:flex;align-items:center;gap:16px;border:1px solid var(--sigta-borde);border-radius:10px;padding:14px;background:#fff}.evidence-card img{width:150px;height:95px;object-fit:cover;border-radius:7px}.evidence-card b,.evidence-card small{display:block}.evidence-card small{color:var(--sigta-texto-suave);margin:4px 0 10px}.evidence-card a{display:inline-block;background:var(--sigta-azul);color:#fff;text-decoration:none;padding:8px 12px;border-radius:7px;font-weight:700;font-size:12px}.doc-icon{width:62px;height:62px;border-radius:8px;background:var(--sigta-error-fondo);color:var(--sigta-error);display:grid;place-items:center;font-weight:900}
.priority-list article{display:flex;align-items:center;justify-content:space-between;gap:15px;border-top:1px solid var(--sigta-borde);padding:13px 2px}.priority-list small{display:block;color:var(--sigta-texto-suave);margin-top:4px}.priority-list button{border:0;border-radius:7px;padding:9px 12px}.work-filters{display:grid;grid-template-columns:1fr 1fr 2fr;gap:12px;margin-bottom:16px}.work-filters label{font-size:11px;font-weight:700;color:var(--sigta-texto-suave)}.work-filters select,.work-filters input{display:block;width:100%;margin-top:5px;padding:9px;border:1px solid var(--sigta-borde);border-radius:7px;background:#fff}.report-preview{background:#f5f8fc;border:1px solid var(--sigta-borde);border-radius:9px;padding:14px}.report-preview p{font-size:12px;line-height:1.6;color:var(--sigta-texto-suave)}
@media(max-width:720px){.work-filters,.detalle-modal-body{grid-template-columns:1fr}.evidence-card{align-items:flex-start;flex-direction:column}.evidence-card img{width:100%;height:auto;max-height:220px}.priority-list article{align-items:flex-start;flex-direction:column}.priority-list button{width:100%}}
</style>

<style scoped>
.tecnico-menu>aside>button{gap:11px;min-height:42px;padding:0 12px;border-radius:8px;font-size:13px;font-weight:600}.tecnico-menu>aside>button :deep(.icono-sigta){flex-shrink:0}.tecnico-menu>aside .brand{display:flex;gap:11px;align-items:center}.tecnico-menu>aside>p{letter-spacing:1.4px;font-size:10px}.tecnico-menu>aside>button em{margin-left:auto}.tecnico-menu>aside>button.active{color:var(--sigta-mostaza)!important}
</style>
