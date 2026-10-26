<template>

  <div class="layout">

    <AdminMenu v-if="route.meta.portalDirector" /><SolicitanteMenu v-else />


    <main class="content">

      <!-- ============================================
           ENCABEZADO
      ============================================= -->

      <header class="topbar">

        <div>

          <h1>
            {{ vistaVerificaciones ? 'Verificaciones pendientes' : 'Mis solicitudes' }}
          </h1>

          <p>
            {{ vistaVerificaciones
              ? 'Revise las soluciones técnicas finalizadas y confirme si el problema fue resuelto.'
              : 'Consulte y dé seguimiento a sus requerimientos de Soporte Técnico y Mantenimiento.' }}
          </p>

        </div>

        <button
          v-if="!vistaVerificaciones"
          class="btn-new"
          type="button"
          @click="mostrarCrear = !mostrarCrear"
        >
          ＋ Nueva solicitud
        </button>

      
        <UsuarioHeader @actualizar="cargarTodo" />
      </header>

      <section v-if="!vistaVerificaciones && mostrarCrear" class="create-panel">
        <button type="button" @click="router.push({ path: route.meta.portalDirector ? '/admin/nueva-solicitud/soporte' : '/usuario/soporte', query: { origen: route.meta.portalDirector ? '/admin/mis-solicitudes' : '/usuario/mis-solicitudes' } })">
          <span>🖥️</span>
          <div>
            <strong>Soporte Técnico</strong>
            <small>Equipos, redes, sistemas y dispositivos.</small>
          </div>
        </button>

        <button type="button" @click="router.push({ path: route.meta.portalDirector ? '/admin/nueva-solicitud/mantenimiento' : '/usuario/mantenimiento', query: { origen: route.meta.portalDirector ? '/admin/mis-solicitudes' : '/usuario/mis-solicitudes' } })">
          <span>🛠️</span>
          <div>
            <strong>Mantenimiento</strong>
            <small>Infraestructura, instalaciones y servicios.</small>
          </div>
        </button>
      </section>


      <!-- ============================================
           RESUMEN
      ============================================= -->

      <section v-if="!vistaVerificaciones" class="summary">

        <article>

          <span>
            Total
          </span>

          <strong>
            {{ solicitudes.length }}
          </strong>

          <small>
            Registros realizados
          </small>

        </article>


        <article>

          <span>
            Soporte Técnico
          </span>

          <strong>
            {{ soporte.length }}
          </strong>

          <small>
            Solicitudes de soporte
          </small>

        </article>


        <article>

          <span>
            Mantenimiento
          </span>

          <strong>
            {{ mantenimiento.length }}
          </strong>

          <small>
            Requerimientos de mantenimiento
          </small>

        </article>

      </section>


      <!-- ============================================
           FILTROS
      ============================================= -->

      <section v-if="!vistaVerificaciones" class="filters-card">

        <div class="search">

          <label>
            Buscar
          </label>

          <input
            v-model="busqueda"
            type="text"
            placeholder="Código, título, ubicación o proceso..."
          />

        </div>


        <div class="filter">

          <label>
            Proceso
          </label>

          <select
            v-model="filtroProceso"
          >

            <option value="">
              Todos
            </option>

            <option value="SOPORTE">
              Soporte Técnico
            </option>

            <option value="MANTENIMIENTO">
              Mantenimiento
            </option>

          </select>

        </div>


        <div class="filter">

          <label>
            Estado
          </label>

          <select
            v-model="filtroEstado"
          >

            <option value="">
              Todos
            </option>

            <option
              v-for="estado in estadosDisponibles"
              :key="estado.valor"
              :value="estado.valor"
            >
              {{ estado.etiqueta }}
            </option>

          </select>

        </div>

      </section>


      <!-- ============================================
           MENSAJES
      ============================================= -->

      <div
        v-if="mensaje"
        :class="[
          'alert',
          esError
            ? 'error'
            : 'success'
        ]"
      >
        {{ mensaje }}
      </div>


      <!-- ============================================
           LISTADO
      ============================================= -->

      <section v-if="vistaVerificaciones" class="verification-page">
        <div v-if="cargando" class="empty">Cargando verificaciones pendientes...</div>
        <div v-else-if="!verificacionesPendientes.length" class="empty">
          <span>✓</span>
          <h3>No tiene verificaciones pendientes</h3>
          <p>Los resultados técnicos que requieran su confirmación aparecerán aquí.</p>
        </div>
        <div v-else class="verification-list">
          <article v-for="item in verificacionesPendientes" :key="item.id" class="verification-card">
            <div class="verification-card__head">
              <strong>{{ item.codigo }}</strong>
              <span class="status warning">Pendiente de conformidad</span>
            </div>
            <h3>{{ item.titulo }}</h3>
            <dl>
              <div v-if="item.equipo_afectado"><dt>Equipo</dt><dd>{{ item.equipo_afectado }}</dd></div>
              <div v-if="item.ubicacion"><dt>Ubicación</dt><dd>{{ item.ubicacion }}</dd></div>
              <div v-if="item.tecnico_nombre"><dt>Técnico</dt><dd>{{ item.tecnico_nombre }}</dd></div>
              <div v-if="item.pruebas_en"><dt>Fecha de atención</dt><dd>{{ formatearFecha(item.pruebas_en) }}</dd></div>
            </dl>
            <button type="button" class="primary verification-open" @click="abrirVerificacion(item)">Ver resultado</button>
          </article>
        </div>
      </section>

      <section v-else class="requests-card">

        <div
          v-if="cargando"
          class="empty"
        >
          Cargando sus requerimientos...
        </div>


        <div
          v-else-if="
            solicitudesFiltradas.length === 0
          "
          class="empty"
        >

          <h3>
            No se encontraron solicitudes
          </h3>

          <p>
            Puede registrar una solicitud de soporte
            o un requerimiento de mantenimiento.
          </p>

          <button
            @click="mostrarCrear = true"
          >
            Nueva solicitud
          </button>

        </div>


        <div
          v-else
          class="request-list"
        >

          <article
            v-for="item in solicitudesFiltradas"
            :key="`${item.proceso}-${item.id}`"
            class="request"
          >

            <div class="request-main">

              <div class="request-code">

                <span
                  :class="[
                    'process-indicator',
                    claseProceso(item.proceso)
                  ]"
                ></span>

                <div>

                  <strong>
                    {{ item.codigo }}
                  </strong>

                  <small>
                    {{ item.modulo }}
                  </small>

                </div>

              </div>


              <div class="request-info">

                <h3>
                  {{
                    item.titulo
                    || 'Requerimiento institucional'
                  }}
                </h3>

                <p>
                  {{
                    item.descripcion
                    || 'Sin descripción registrada.'
                  }}
                </p>


                <div class="meta">

                  <span
                    v-if="item.area_nombre"
                  >
                    {{ item.area_nombre }}
                  </span>


                  <span
                    v-if="item.ubicacion"
                  >
                    {{ item.ubicacion }}
                  </span>


                  <span
                    v-if="item.detalle_tipo"
                  >
                    {{ item.detalle_tipo }}
                  </span>


                  <span
                    v-if="item.fecha"
                  >
                    {{ formatearFecha(item.fecha) }}
                  </span>

                </div>

              </div>

            </div>


            <div class="request-side">
              <span v-if="item.sla_estado==='VENCIDO'" class="status cancelled">Vencido</span>

              <span
                :class="[
                  'status',
                  claseEstado(item.estado_codigo)
                ]"
              >
                {{
                  etiquetaEstadoSolicitante(item)
                }}
              </span>


              <div class="actions">

                <button
                  class="view"
                  @click="verDetalle(item)"
                >
                  Ver detalles
                </button>


                <button v-if="item.proceso==='SOPORTE' && item.puede_reabrir" class="edit" @click="reabrir(item)">Reabrir ticket</button>
                <!--
                  La edición/anulación se conserva únicamente
                  para Soporte Técnico porque ese CRUD ya está
                  implementado en esta misma vista.
                -->

                <button
                  v-if="puedeEditarSoporte(item)"
                  class="edit"
                  @click="abrirEditarSoporte(item)"
                >
                  Editar
                </button>


                <button
                  v-if="puedeCancelar(item)"
                  class="cancel"
                  @click="solicitudPorCancelar = item"
                >
                  Cancelar
                </button>


                <button
                  v-if="item.proceso === 'SOPORTE' && item.estado_codigo === 'PENDIENTE_CONFORMIDAD'"
                  class="edit"
                  @click="abrirVerificacion(item)"
                >
                  Verificar funcionamiento
                </button>

                <button
                  v-if="item.proceso === 'MANTENIMIENTO' && item.estado_codigo === 'INFORME_REGISTRADO'"
                  class="edit"
                  @click="abrirVerificacion(item)"
                >
                  ¿Se solucionó?
                </button>

              </div>

            </div>

            <div
              v-if="solicitudPorCancelar?.proceso === item.proceso && solicitudPorCancelar?.id === item.id"
              class="cancel-confirmation"
            >
              <div>
                <strong>¿Está seguro de cancelar la solicitud?</strong>
                <span>{{ item.codigo }} quedará cancelada y la acción se registrará en el historial.</span>
              </div>
              <div class="cancel-confirmation__actions">
                <button type="button" class="confirm-no" @click="solicitudPorCancelar = null">No</button>
                <button type="button" class="confirm-yes" @click="anularSolicitud(item)">Sí</button>
              </div>
            </div>

          </article>

        </div>

      </section>

    </main>


    <!-- ============================================
         MODAL DETALLE GENERAL
    ============================================= -->

    <div
      v-if="mostrarDetalle"
      class="overlay"
      @click.self="cerrarDetalle"
    >

      <div class="modal detail-modal">

        <div class="modal-header">

          <div>

            <span class="modal-code">
              {{ solicitudSeleccionada?.codigo }}
            </span>

            <h2>
              {{ solicitudSeleccionada?.titulo }}
            </h2>

            <p>
              {{ solicitudSeleccionada?.modulo }}
            </p>

          </div>


          <button
            class="close"
            @click="cerrarDetalle"
          >
            ×
          </button>

        </div>



        <div class="detail-status">

          <span
            :class="[
              'status',
              claseEstado(
                solicitudSeleccionada?.estado_codigo
              )
            ]"
          >
            {{
              solicitudSeleccionada?.estado_nombre
              ||
              solicitudSeleccionada?.estado_codigo
              ||
              'Registrado'
            }}
          </span>

        </div>

        <div v-if="false" class="timeline">
          <div
            v-for="(paso, indice) in pasosSolicitud(solicitudSeleccionada)"
            :key="paso.nombre"
            :class="['timeline-step', { completado: paso.completado, actual: paso.actual }]"
          >
            <span>{{ paso.completado ? '✓' : indice + 1 }}</span>
            <small>{{ paso.nombre }}</small>
          </div>
        </div>


        <div class="detail-grid">

          <div>

            <label>
              <IconoSigta nombre="portal" :tamano="14" />
              <span>Proceso</span>
            </label>

            <p>
              {{ solicitudSeleccionada?.modulo }}
            </p>

          </div>


          <div>

            <label>
              <IconoSigta nombre="edificio" :tamano="14" />
              <span>Área</span>
            </label>

            <p>
              {{
                solicitudSeleccionada?.area_nombre
                || 'No indicada'
              }}
            </p>

          </div>


          <div
            v-if="
              solicitudSeleccionada?.ubicacion
            "
          >

            <label>
              <IconoSigta nombre="globo" :tamano="14" />
              <span>Ubicación</span>
            </label>

            <p>
              {{ solicitudSeleccionada?.ubicacion }}
            </p>

          </div>


          <div
            v-if="
              solicitudSeleccionada?.detalle_tipo
            "
          >

            <label>
              <IconoSigta nombre="filtro" :tamano="14" />
              <span>Tipo</span>
            </label>

            <p>
              {{ solicitudSeleccionada?.detalle_tipo }}
            </p>

          </div>


          <div class="full">

            <label>
              <IconoSigta nombre="reporte" :tamano="14" />
              <span>Descripción</span>
            </label>

            <p>
              {{
                solicitudSeleccionada?.descripcion
                || 'Sin descripción registrada.'
              }}
            </p>

          </div>


          <!-- SOPORTE -->

          <template
            v-if="
              solicitudSeleccionada?.proceso
              === 'SOPORTE'
            "
          >

            <div>

              <label>
                <IconoSigta nombre="etiqueta" :tamano="14" />
                <span>Categoría</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.categoria_nombre
                  || 'Sin categoría'
                }}
              </p>

            </div>


            <div>

              <label>
                <IconoSigta nombre="soporte" :tamano="14" />
                <span>Equipo afectado</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.equipo_afectado
                  || 'No indicado'
                }}
              </p>

            </div>


            <div class="full">

              <label>
                <IconoSigta nombre="auditoria" :tamano="14" />
                <span>Evidencia</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.evidencia
                  || 'Sin evidencia registrada'
                }}
              </p>

              <button
                v-if="solicitudSeleccionada?.evidencia_archivo_url"
                type="button"
                class="evidence-button"
                @click="visorEvidencia = solicitudSeleccionada.evidencia_archivo_url"
              >
                {{ esImagen(solicitudSeleccionada.evidencia_archivo_url) ? '👁 Ver evidencia' : '📄 Visualizar documento' }}
              </button>

            </div>


            <div class="full">

              <label>
                <IconoSigta nombre="validar" :tamano="14" />
                <span>Revisión del equipo</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.diagnostico
                  || 'Pendiente de revisión UTIC'
                }}
              </p>

            </div>


            <div class="full">

              <label>
                <IconoSigta nombre="mantenimiento" :tamano="14" />
                <span>Reparación técnica</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.solucion
                  || 'Pendiente'
                }}
              </p>

            </div>

          </template>


          <!-- MANTENIMIENTO -->

          <template
            v-if="
              solicitudSeleccionada?.proceso
              === 'MANTENIMIENTO'
            "
          >

            <div>

              <label>
                <IconoSigta nombre="mantenimiento" :tamano="14" />
                <span>Tipo de mantenimiento</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.tipo_nombre
                  ||
                  solicitudSeleccionada?.tipo
                  ||
                  'No indicado'
                }}
              </p>

            </div>


            <div>

              <label>
                <IconoSigta nombre="usuario_check" :tamano="14" />
                <span>Auxiliar asignado</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.auxiliar_asignado_nombre
                  || 'Pendiente de derivación'
                }}
              </p>

            </div>


            <div class="full">

              <label>
                <IconoSigta nombre="auditoria" :tamano="14" />
                <span>Evidencia</span>
              </label>

              <p>
                {{
                  solicitudSeleccionada?.evidencia
                  || 'Sin evidencia registrada'
                }}
              </p>

            </div>

          </template>

        </div>


        <section class="request-documents" aria-label="Informes y documentos de la solicitud">
          <div class="request-documents__heading">
            <IconoSigta nombre="reporte" :tamano="22" />
            <div>
              <h3>Informes y documentos</h3>
              <p>Consulte los informes emitidos y las constancias de su solicitud.</p>
            </div>
          </div>
          <div v-if="informesDisponibles.length" class="request-documents__links">
            <a v-for="informe in informesDisponibles" :key="informe.url" :href="informe.url" target="_blank" rel="noopener noreferrer" class="request-document-link">
              <IconoSigta nombre="reporte" :tamano="20" />
              <span><strong>{{ informe.nombre }}</strong><small>Ver informe PDF</small></span>
              <span aria-hidden="true">&#8599;</span>
            </a>
          </div>
          <DocumentosSolicitante v-if="solicitudSeleccionada" :base="solicitudSeleccionada.proceso === 'MANTENIMIENTO' ? '/api/mantenimiento/requerimientos' : '/api/soporte/tickets'" :id="solicitudSeleccionada.id" />
        </section>

        <div class="modal-footer">

          <button
            class="secondary"
            @click="cerrarDetalle"
          >
            Cerrar
          </button>


          <button
            v-if="
              puedeEditarSoporte(
                solicitudSeleccionada
              )
            "
            class="primary"
            @click="editarDesdeDetalle"
          >
            Editar solicitud de soporte
          </button>

        </div>

      </div>

    </div>


    <!-- ============================================
         MODAL EDITAR SOPORTE
    ============================================= -->

    <div
      v-if="mostrarEditar"
      class="overlay"
      @click.self="cerrarEditar"
    >

      <div class="modal">

        <div class="modal-header">

          <div>

            <span class="modal-code">
              {{ solicitudSeleccionada?.codigo }}
            </span>

            <h2>
              Editar solicitud de soporte
            </h2>

            <p>
              Puede modificarla mientras
              se encuentre en estado NUEVO.
            </p>

          </div>


          <button
            class="close"
            @click="cerrarEditar"
          >
            ×
          </button>

        </div>


        <form
          @submit.prevent="guardarEdicionSoporte"
        >

          <div class="form-grid">

            <div class="field full">

              <label>
                Título
              </label>

              <input
                v-model="form.titulo"
                type="text"
                required
              />

            </div>


            <div class="field full">

              <label>
                Descripción
              </label>

              <textarea
                v-model="form.descripcion"
                required
              ></textarea>

            </div>


            <div class="field">

              <label>
                Área
              </label>

              <select
                v-model="form.area"
                required
              >

                <option
                  v-for="area in areas"
                  :key="area.id"
                  :value="area.id"
                >
                  {{ area.nombre }}
                </option>

              </select>

            </div>


            <div class="field">

              <label>
                Categoría
              </label>

              <select
                v-model="form.categoria"
                required
              >

                <option
                  v-for="categoria in categorias"
                  :key="categoria.id"
                  :value="categoria.id"
                >
                  {{ categoria.nombre }}
                </option>

              </select>

            </div>


            <div class="field">

              <label>
                Ubicación
              </label>

              <input
                v-model="form.ubicacion"
                type="text"
                required
              />

            </div>


            <div class="field">

              <label>
                Equipo afectado
              </label>

              <input
                v-model="form.equipo_afectado"
                type="text"
                required
              />

            </div>


            <div class="field full">

              <label>
                Descripción de evidencia
              </label>

              <input
                v-model="form.evidencia"
                type="text"
              />

            </div>

          </div>


          <p
            v-if="mensajeModal"
            class="modal-error"
          >
            {{ mensajeModal }}
          </p>


          <div class="modal-footer">

            <button
              type="button"
              class="secondary"
              @click="cerrarEditar"
            >
              Cancelar
            </button>


            <button
              type="submit"
              class="primary"
              :disabled="guardando"
            >
              {{
                guardando
                  ? 'Guardando...'
                  : 'Guardar cambios'
              }}
            </button>

          </div>

        </form>

      </div>

    </div>

    <div
      v-if="mostrarVerificacion && solicitudSeleccionada"
      class="overlay verification-overlay"
      @click.self="cerrarVerificacion"
    >
      <section class="verification-modal">
        <header class="verification-modal__head">
          <button type="button" @click="cerrarVerificacion">← Volver</button>
          <div>
            <small>VERIFICACIÓN DE SERVICIO</small>
            <strong>{{ solicitudSeleccionada.codigo }}</strong>
            <h2>{{ solicitudSeleccionada.titulo }}</h2>
          </div>
          <button type="button" aria-label="Cerrar" @click="cerrarVerificacion">×</button>
        </header>

        <div class="verification-modal__body">
          <section class="result-section">
            <h3>Información original</h3>
            <div class="result-grid">
              <div class="wide-result"><small>Descripción inicial</small><p>{{ solicitudSeleccionada.descripcion }}</p></div>
              <div v-if="solicitudSeleccionada.ubicacion"><small>Ubicación</small><strong>{{ solicitudSeleccionada.ubicacion }}</strong></div>
              <div v-if="solicitudSeleccionada.equipo_afectado"><small>Equipo</small><strong>{{ solicitudSeleccionada.equipo_afectado }}</strong></div>
            </div>
            <div v-if="solicitudSeleccionada.evidencia_archivo_url" class="evidence-result">
              <img v-if="esImagen(solicitudSeleccionada.evidencia_archivo_url)" :src="solicitudSeleccionada.evidencia_archivo_url" alt="Evidencia original">
              <div><strong>Evidencia original del solicitante</strong><button type="button" class="evidence-button" @click="visorEvidencia=solicitudSeleccionada.evidencia_archivo_url">Ver evidencia</button></div>
            </div>
          </section>

          <section class="result-section">
            <h3>Resultado del trabajo</h3>
            <div class="result-grid">
              <div v-if="solicitudSeleccionada.tecnico_nombre"><small>Técnico responsable</small><strong>{{ solicitudSeleccionada.tecnico_nombre }}</strong></div>
              <div v-if="solicitudSeleccionada.auxiliar_asignado_nombre"><small>Técnico responsable</small><strong>{{ solicitudSeleccionada.auxiliar_asignado_nombre }}</strong></div>
              <div v-if="solicitudSeleccionada.diagnostico" class="wide-result"><small>Diagnóstico</small><p>{{ solicitudSeleccionada.diagnostico }}</p></div>
              <div v-if="solicitudSeleccionada.solucion" class="wide-result"><small>Trabajo realizado</small><p>{{ solicitudSeleccionada.solucion }}</p></div>
              <div v-if="solicitudSeleccionada.trabajo_realizado" class="wide-result"><small>Trabajo realizado</small><p>{{ solicitudSeleccionada.trabajo_realizado }}</p></div>
              <div v-if="solicitudSeleccionada.resultado_pruebas" class="wide-result"><small>Resultado de pruebas</small><p>{{ solicitudSeleccionada.resultado_pruebas }}</p></div>
              <div v-if="solicitudSeleccionada.proceso !== 'MANTENIMIENTO'"><small>Compra</small><strong>{{ solicitudSeleccionada.requiere_compra ? 'Sí' : 'No' }}</strong></div>
              <div v-if="solicitudSeleccionada.requiere_compra && solicitudSeleccionada.componente_requerido"><small>Componente</small><strong>{{ solicitudSeleccionada.componente_requerido }}</strong></div>
              <div v-if="solicitudSeleccionada.requiere_compra"><small>Cantidad</small><strong>{{ solicitudSeleccionada.cantidad_componente }}</strong></div>
              <div v-if="solicitudSeleccionada.producto_requerido"><small>Componente requerido</small><strong>{{ solicitudSeleccionada.producto_requerido }}</strong></div>
              <div v-if="solicitudSeleccionada.producto_requerido"><small>Cantidad</small><strong>{{ solicitudSeleccionada.cantidad_requerida }}</strong></div>
            </div>
            <div v-if="evidenciasTecnicas.length" class="technical-evidence-list">
              <strong>Evidencias técnicas</strong>
              <button v-for="archivo in evidenciasTecnicas" :key="archivo.url" type="button" class="evidence-button" @click="visorEvidencia=archivo.url">{{ archivo.nombre }}</button>
            </div>
          </section>

          <section class="verification-decision">
            <small>VERIFICACIÓN DEL FUNCIONAMIENTO</small>
            <h3>¿El problema fue resuelto satisfactoriamente?</h3>
            <p>Revise el trabajo registrado antes de comunicar su decisión.</p>
            <div>
              <button type="button" class="secondary danger-decision" @click="abrirConformidad(solicitudSeleccionada, false)">No estoy conforme</button>
              <button type="button" class="primary" @click="abrirConformidad(solicitudSeleccionada, true)">Estoy conforme</button>
            </div>
          </section>
        </div>
      </section>
    </div>

    <div
      v-if="conformidadPendiente"
      class="overlay conformity-overlay"
      @click.self="cerrarConformidad"
    >
      <section class="modal conformity-modal">
        <div class="modal-header">
          <div>
            <span class="modal-code">{{ conformidadPendiente.item.codigo }}</span>
            <h2>{{ conformidadPendiente.conforme ? 'Confirmar conformidad' : 'Informar no conformidad' }}</h2>
            <p>{{ conformidadPendiente.item.titulo }}</p>
          </div>
          <button type="button" class="close" aria-label="Cerrar" @click="cerrarConformidad">×</button>
        </div>

        <div class="conformity-message">
          <strong>{{ conformidadPendiente.conforme ? '¿Confirma que el problema fue resuelto satisfactoriamente?' : 'Indique qué inconveniente continúa presentándose.' }}</strong>
          <dl>
            <div><dt>Ticket</dt><dd>{{ conformidadPendiente.item.codigo }}</dd></div>
            <div v-if="conformidadPendiente.item.equipo_afectado"><dt>Equipo</dt><dd>{{ conformidadPendiente.item.equipo_afectado }}</dd></div>
          </dl>
          <p v-if="conformidadPendiente.conforme">Su conformidad será registrada y el Ticket continuará a la elaboración del informe final.</p>
          <p v-else>La orden volverá al especialista para una nueva atención y conservará todo el historial registrado.</p>
        </div>

        <div v-if="!conformidadPendiente.conforme" class="field conformity-reason">
          <label for="motivo-no-conformidad">Motivo / observación <span aria-hidden="true">*</span></label>
          <textarea id="motivo-no-conformidad" v-model="observacionConformidad" rows="4" maxlength="1000" placeholder="El equipo continúa presentando..." required></textarea>
          <small>{{ observacionConformidad.trim().length }}/1000</small>
        </div>

        <p v-if="mensajeConformidad" class="modal-error">{{ mensajeConformidad }}</p>

        <div class="modal-footer">
          <button type="button" class="secondary" :disabled="guardandoConformidad" @click="cerrarConformidad">Cancelar</button>
          <button
            type="button"
            class="primary"
            :disabled="guardandoConformidad || (!conformidadPendiente.conforme && !observacionConformidad.trim())"
            @click="confirmarConformidad"
          >
            {{ guardandoConformidad ? 'Guardando...' : (conformidadPendiente.conforme ? 'Confirmar conformidad' : 'Enviar observación') }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="mensajeResultado" class="overlay result-message" @click.self="mensajeResultado = null">
      <section>
        <span>✓</span>
        <h2>{{ mensajeResultado.titulo }}</h2>
        <p>{{ mensajeResultado.texto }}</p>
        <button type="button" class="primary" @click="mensajeResultado = null">Entendido</button>
      </section>
    </div>

    <div v-if="visorEvidencia" class="overlay evidence-viewer" @click.self="visorEvidencia = ''">
      <section>
        <header>
          <button type="button" @click="visorEvidencia = ''">← Volver al expediente</button>
          <strong>Evidencia {{ solicitudSeleccionada?.codigo }}</strong>
          <button type="button" aria-label="Cerrar" @click="visorEvidencia = ''">×</button>
        </header>
        <div class="viewer-body">
          <img v-if="esImagen(visorEvidencia)" :src="visorEvidencia" alt="Evidencia ampliada">
          <iframe v-else :src="visorEvidencia" title="Documento de evidencia"></iframe>
        </div>
      </section>
    </div>

  </div>

</template>


<script setup>
import { SigtaModal } from '../utils/swal'
import DocumentosSolicitante from '../components/DocumentosSolicitante.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'
import AdminMenu from '../components/AdminMenu.vue'

import {
  computed,
  onMounted,
  reactive,
  watch,
  ref
} from 'vue'

import {
  useRouter,
  useRoute
} from 'vue-router'

import SolicitanteMenu
  from '../components/SolicitanteMenu.vue'

import IconoSigta
  from '../components/IconoSigta.vue'


const router =
  useRouter()

const route =
  useRoute()


// ==========================================================
// DATOS
// ==========================================================

const soporte =
  ref([])

const mantenimiento =
  ref([])

const areas =
  ref([])

const categorias =
  ref([])


// ==========================================================
// ESTADO INTERFAZ
// ==========================================================

const cargando =
  ref(true)

const guardando =
  ref(false)

const mostrarCrear =
  ref(false)

const busqueda =
  ref('')

const filtroProceso =
  ref(
    typeof route.query.proceso === 'string'
      ? route.query.proceso
      : ''
  )

const filtroEstado =
  ref(
    typeof route.query.estado === 'string'
      ? route.query.estado
      : ''
  )

const mensaje =
  ref('')

const mensajeModal =
  ref('')

const esError =
  ref(false)

const mostrarDetalle =
  ref(false)

const mostrarVerificacion = ref(false)
const mensajeResultado = ref(null)

const mostrarEditar =
  ref(false)

const solicitudSeleccionada =
  ref(null)

const solicitudPorCancelar =
  ref(null)

const conformidadPendiente = ref(null)
const observacionConformidad = ref('')
const mensajeConformidad = ref('')
const guardandoConformidad = ref(false)
const visorEvidencia = ref('')

const vistaVerificaciones = computed(() => route.query.vista === 'verificaciones')
watch(() => route.query, query => {
  filtroProceso.value = typeof query.proceso === 'string' ? query.proceso : ''
  filtroEstado.value = typeof query.estado === 'string' ? query.estado : ''
  mostrarDetalle.value = false
})
const verificacionesPendientes = computed(() => solicitudes.value.filter(
  item => item.proceso === 'SOPORTE' && item.estado_codigo === 'PENDIENTE_CONFORMIDAD'
))
const informesDisponibles = computed(() => {
  const item = solicitudSeleccionada.value
  if (!item) return []
  return [
    { nombre: 'Informe de requerimiento de compra', url: item.informe_compra },
    { nombre: 'Informe final', url: item.informe_final_pdf_url },
    { nombre: 'Informe técnico', url: item.informe_tecnico_pdf_url },
    { nombre: 'Informe del jefe de carrera', url: item.informe_jefe_carrera_pdf_url },
  ].filter(informe => informe.url)
})
const evidenciasTecnicas = computed(() => {
  const item = solicitudSeleccionada.value
  if (!item) return []
  return [
    { nombre: 'Evidencia del diagnóstico', url: item.evidencia_diagnostico_url },
    { nombre: 'Evidencia de la intervención', url: item.evidencia_intervencion_url },
    { nombre: 'Evidencia de las pruebas', url: item.evidencia_pruebas_url },
  ].filter(archivo => archivo.url)
})


// ==========================================================
// FORMULARIO SOPORTE
// ==========================================================

const form =
  reactive({

    titulo: '',

    descripcion: '',

    area: '',

    categoria: '',

    ubicacion: '',

    equipo_afectado: '',

    evidencia: '',
  })


// ==========================================================
// TOKEN
// ==========================================================

const token = () =>
  localStorage.getItem(
    'sigta_token'
  )


const authHeaders = () => ({

  'Content-Type':
    'application/json',

  Accept:
    'application/json',

  Authorization:
    `Token ${token()}`,
})


// ==========================================================
// INICIO
// ==========================================================

onMounted(
  async () => {

    if (!token()) {

      router.push(
        '/login'
      )

      return
    }


    await cargarCatalogos()

    await cargarTodo()

    if (route.query.id && route.query.proceso) {
      const item = solicitudes.value.find(solicitud =>
        solicitud.proceso === route.query.proceso
        && Number(solicitud.id) === Number(route.query.id)
      )
      if (item) verDetalle(item)
    }
  }
)


// ==========================================================
// NORMALIZAR
// ==========================================================

function convertirLista(
  datos
) {

  if (
    Array.isArray(datos)
  ) {

    return datos
  }


  if (
    Array.isArray(
      datos?.results
    )
  ) {

    return datos.results
  }


  return []
}


// ==========================================================
// FETCH LISTA
// ==========================================================

async function cargarLista(
  url
) {

  const respuesta =
    await fetch(
      url,
      {
        headers: {

          Authorization:
            `Token ${token()}`,

          Accept:
            'application/json',
        }
      }
    )


  if (
    respuesta.status === 401
    ||
    respuesta.status === 403
  ) {

    cerrarSesion()

    throw new Error(
      'Sesión no autorizada.'
    )
  }


  if (!respuesta.ok) {

    throw new Error(
      `Error ${respuesta.status}`
    )
  }


  return convertirLista(
    await respuesta.json()
  )
}


// ==========================================================
// CARGAR TODO
// ==========================================================

async function reabrir(item) {
  const confirmacion=await SigtaModal.fire({title:'Reabrir ticket',text:'El ticket volverá a En proceso y conservará su cierre y expediente anterior.',icon:'question',showCancelButton:true,confirmButtonText:'Reabrir ticket',cancelButtonText:'Cancelar'})
  if(!confirmacion.isConfirmed)return
  try{
    const r=await fetch(`/api/soporte/tickets/${item.id}/reabrir-ticket/`,{method:'POST',headers:{Authorization:`Token ${token()}`}})
    const d=await r.json();if(!r.ok)throw new Error(d.detalle||'No fue posible reabrir el ticket.')
    await cargarTodo();mostrarMensaje('Ticket reabierto. La fecha de cierre y el expediente anterior se conservaron.')
  }catch(e){await SigtaModal.fire({title:'No se pudo reabrir',text:e.message,icon:'warning',confirmButtonText:'Entendido'})}
}

async function cargarTodo() {

  cargando.value =
    true


  try {

    const resultados =
      await Promise.allSettled([

        cargarLista(
          '/api/soporte/tickets/?propias=1'
        ),

        cargarLista(
          '/api/mantenimiento/requerimientos/?propias=1'
        ),
      ])

    soporte.value = resultados[0].status === 'fulfilled'
      ? resultados[0].value
      : []

    mantenimiento.value = resultados[1].status === 'fulfilled'
      ? resultados[1].value
      : []

    const fallos = resultados.filter(resultado => resultado.status === 'rejected')
    if (fallos.length) {
      console.error('Error parcial cargando solicitudes:', fallos.map(resultado => resultado.reason))
      mostrarMensaje('No fue posible cargar una parte de sus requerimientos.', true)
    }


  } catch (error) {

    console.error(
      'Error cargando solicitudes:',
      error
    )


    mostrarMensaje(
      'No fue posible cargar todos sus requerimientos.',
      true
    )


  } finally {

    cargando.value =
      false
  }
}


// ==========================================================
// SOLICITUDES UNIFICADAS
// ==========================================================

const solicitudes =
  computed(() => {

    const st =
      soporte.value.map(
        item => ({

          ...item,

          proceso:
            'SOPORTE',

          modulo:
            'Soporte Técnico',

          detalle_tipo:
            item.categoria_nombre
            || 'Soporte Técnico',

          estado_codigo:
            item.estado_codigo
            || item.estado,

          estado_nombre:
            item.estado_nombre
            || item.estado_codigo
            || item.estado,

          fecha:
            item.creado_en
            || item.fecha_creacion
            || item.created_at
            || null,
        })
      )


    const mt =
      mantenimiento.value.map(
        item => ({

          ...item,

          proceso:
            'MANTENIMIENTO',

          modulo:
            'Mantenimiento',

          detalle_tipo:
            item.tipo_nombre
            || item.tipo
            || 'Mantenimiento',

          estado_codigo:
            item.estado_codigo
            || item.estado,

          estado_nombre:
            item.estado_nombre
            || item.estado_codigo
            || item.estado,

          fecha:
            item.creado_en
            || item.created_at
            || null,
        })
      )


    return [
      ...st,
      ...mt
    ]
      .sort(
        (a, b) => {

          const fechaA =
            new Date(
              a.fecha
              || 0
            ).getTime()

          const fechaB =
            new Date(
              b.fecha
              || 0
            ).getTime()


          if (
            fechaA
            &&
            fechaB
          ) {

            return (
              fechaB
              -
              fechaA
            )
          }


          return (
            Number(b.id || 0)
            -
            Number(a.id || 0)
          )
        }
      )
  })


// ==========================================================
// FILTROS
// ==========================================================

const solicitudesFiltradas =
  computed(() => {

    const texto =
      busqueda.value
        .toLowerCase()
        .trim()


    return solicitudes.value.filter(
      item => {

        const textoGeneral =
          [
            item.codigo,
            item.titulo,
            item.descripcion,
            item.ubicacion,
            item.modulo,
            item.detalle_tipo,
            item.area_nombre,
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase()


        const coincideBusqueda =
          !texto
          ||
          textoGeneral.includes(
            texto
          )


        const coincideProceso =
          !filtroProceso.value
          ||
          item.proceso
          === filtroProceso.value


        const coincideEstado =
          !filtroEstado.value
          ||
          bucketEstado(
            item.estado_codigo
          )
          === filtroEstado.value


        return (
          coincideBusqueda
          &&
          coincideProceso
          &&
          coincideEstado
        )
      }
    )
  })


// ==========================================================
// ESTADOS DISPONIBLES (BUCKETS SIMPLIFICADOS)
// ==========================================================
//
// El solicitante no necesita ver los estados internos
// granulares del workflow (Asignado, En verificación,
// Derivado al auxiliar, etc.). Se agrupan en 3 buckets.
// ==========================================================

const estadosDisponibles = [

  { valor: 'PENDIENTES', etiqueta: 'Pendientes' },

  { valor: 'EN_PROCESO', etiqueta: 'En proceso' },

  { valor: 'POR_VALIDAR', etiqueta: 'Por validar' },

  { valor: 'FINALIZADAS', etiqueta: 'Finalizadas' },

  { valor: 'CANCELADAS', etiqueta: 'Canceladas / rechazadas' },
]


function bucketEstado(
  codigo
) {

  const estado =
    String(
      codigo
      || ''
    )
      .toUpperCase()
      .replaceAll(
        ' ',
        '_'
      )


  if (
    estado === 'PENDIENTE_CONFORMIDAD'
  ) {
    return 'POR_VALIDAR'
  }

  if (
    estado.includes(
      'ANUL'
    )
    ||
    estado.includes(
      'RECHAZ'
    )
  ) {

    return 'CANCELADAS'
  }


  if (
    estado === 'CERRADO'
    ||
    estado === 'RESUELTO'
    ||
    estado === 'FINALIZADO'
  ) {

    return 'FINALIZADAS'
  }

  if (['BORRADOR', 'NUEVO', 'RECIBIDO'].includes(estado)) {
    return 'PENDIENTES'
  }


  return 'EN_PROCESO'
}


// ==========================================================
// CLASE PROCESO
// ==========================================================

function claseProceso(
  proceso
) {

  if (
    proceso ===
    'SOPORTE'
  ) {

    return 'support'
  }


  if (
    proceso ===
    'MANTENIMIENTO'
  ) {

    return 'maintenance'
  }


  return 'generic'
}


// ==========================================================
// VER DETALLE
// ==========================================================

function verDetalle(
  item
) {

  solicitudSeleccionada.value =
    item



  mostrarDetalle.value =
    true
}


function cerrarDetalle() {

  mostrarDetalle.value =
    false


  solicitudSeleccionada.value =
    null

  if (route.query.origen === 'kanban') {
    router.push(route.meta.portalDirector ? '/admin/dashboard' : '/usuario/dashboard')
  }
}

// ==========================================================
// CATÁLOGOS SOPORTE
// ==========================================================

async function cargarCatalogos() {

  try {

    const [
      areasRespuesta,
      categoriasRespuesta
    ] =
      await Promise.all([

        fetch(
          '/api/usuarios/areas/',
          {
            headers: {

              Authorization:
                `Token ${token()}`,

              Accept:
                'application/json',
            }
          }
        ),

        fetch(
          '/api/soporte/categorias/',
          {
            headers: {

              Authorization:
                `Token ${token()}`,

              Accept:
                'application/json',
            }
          }
        ),
      ])


    if (
      areasRespuesta.status === 401
      ||
      areasRespuesta.status === 403
      ||
      categoriasRespuesta.status === 401
      ||
      categoriasRespuesta.status === 403
    ) {

      cerrarSesion()

      return
    }


    if (
      areasRespuesta.ok
    ) {

      areas.value =
        convertirLista(
          await areasRespuesta.json()
        )
    }


    if (
      categoriasRespuesta.ok
    ) {

      categorias.value =
        convertirLista(
          await categoriasRespuesta.json()
        )
    }


  } catch (error) {

    console.error(
      'Error cargando catálogos:',
      error
    )
  }
}


// ==========================================================
// SOPORTE - EDITAR
// ==========================================================

function puedeEditarSoporte(
  item
) {

  if (
    !item
    ||
    item.proceso !==
    'SOPORTE'
  ) {

    return false
  }


  return [
    'BORRADOR',
    'NUEVO'
  ].includes(
    item.estado_codigo
  )
}

function pasosSolicitud(item) {
  const estado = item?.estado_codigo || ''
  const nombres = ['Creada', 'Gestión UTIC', 'Atención técnica', 'Verificación del usuario', 'Informe final', 'Cerrada']
  const indiceActual = ['BORRADOR', 'NUEVO'].includes(estado)
    ? 0
    : ['EN_ANALISIS'].includes(estado)
      ? 1
      : ['ASIGNADO', 'EN_DIAGNOSTICO', 'EN_EJECUCION', 'EN_VERIFICACION'].includes(estado)
        ? 2
        : estado === 'PENDIENTE_CONFORMIDAD'
          ? 3
          : estado === 'PENDIENTE_INFORME_FINAL'
            ? 4
            : 5
  const finalizado = ['CERRADO', 'FINALIZADO', 'ARCHIVADO'].includes(estado)
  return nombres.map((nombre, indice) => ({
    nombre,
    completado: finalizado || indice < indiceActual,
    actual: !finalizado && indice === indiceActual,
  }))
}

function etiquetaEstadoSolicitante(item) {
  if (item?.estado_codigo === 'PENDIENTE_CONFORMIDAD') return 'Pendiente de verificación'
  if (item?.estado_codigo === 'PENDIENTE_INFORME_FINAL') return 'Pendiente de informe final'
  return item?.estado_nombre || item?.estado_codigo || 'Registrado'
}

function puedeCancelar(item) {
  if (!item) return false
  if (item.proceso === 'SOPORTE') return ['BORRADOR', 'NUEVO'].includes(item.estado_codigo)
  if (item.proceso === 'MANTENIMIENTO') return item.estado_codigo === 'RECIBIDO'
  return false
}


async function abrirEditarSoporte(
  item
) {

  if (
    areas.value.length === 0
    ||
    categorias.value.length === 0
  ) {

    await cargarCatalogos()
  }


  solicitudSeleccionada.value =
    item


  form.titulo =
    item.titulo
    || ''


  form.descripcion =
    item.descripcion
    || ''


  form.area =
    obtenerId(
      item.area
    )


  form.categoria =
    obtenerId(
      item.categoria
    )


  form.ubicacion =
    item.ubicacion
    || ''


  form.equipo_afectado =
    item.equipo_afectado
    || ''


  form.evidencia =
    item.evidencia
    || ''


  mensajeModal.value =
    ''


  mostrarEditar.value =
    true
}


function editarDesdeDetalle() {

  const item =
    solicitudSeleccionada.value


  mostrarDetalle.value =
    false


  abrirEditarSoporte(
    item
  )
}


function obtenerId(
  valor
) {

  if (
    typeof valor ===
    'number'
  ) {

    return valor
  }


  if (
    typeof valor ===
    'string'
    &&
    valor !== ''
  ) {

    const numero =
      Number(
        valor
      )


    return Number.isNaN(
      numero
    )
      ? ''
      : numero
  }


  if (
    valor
    &&
    typeof valor ===
    'object'
    &&
    valor.id
  ) {

    return Number(
      valor.id
    )
  }


  return ''
}


function cerrarEditar() {

  mostrarEditar.value =
    false


  mensajeModal.value =
    ''


  solicitudSeleccionada.value =
    null


  limpiarFormulario()
}


function limpiarFormulario() {

  form.titulo = ''

  form.descripcion = ''

  form.area = ''

  form.categoria = ''

  form.ubicacion = ''

  form.equipo_afectado = ''

  form.evidencia = ''
}


async function guardarEdicionSoporte() {

  mensajeModal.value =
    ''


  if (
    !form.area
  ) {

    mensajeModal.value =
      'Debe seleccionar un área.'

    return
  }


  if (
    !form.categoria
  ) {

    mensajeModal.value =
      'Debe seleccionar una categoría.'

    return
  }


  if (
    !solicitudSeleccionada.value
  ) {

    mensajeModal.value =
      'No existe una solicitud seleccionada.'

    return
  }


  guardando.value =
    true


  try {

    const respuesta =
      await fetch(
        `/api/soporte/tickets/${solicitudSeleccionada.value.id}/`,
        {

          method:
            'PATCH',

          headers:
            authHeaders(),

          body:
            JSON.stringify({

              titulo:
                form.titulo.trim(),

              descripcion:
                form.descripcion.trim(),

              area:
                Number(
                  form.area
                ),

              categoria:
                Number(
                  form.categoria
                ),

              ubicacion:
                form.ubicacion.trim(),

              equipo_afectado:
                form.equipo_afectado.trim(),

              evidencia:
                form.evidencia.trim(),
            })
        }
      )


    let datos = {}


    try {

      datos =
        await respuesta.json()

    } catch {

      datos = {}
    }


    if (!respuesta.ok) {

      mensajeModal.value =
        obtenerMensajeError(
          datos
        )


      return
    }


    cerrarEditar()


    mostrarMensaje(
      'Solicitud de soporte actualizada correctamente.'
    )


    await cargarTodo()


  } catch (error) {

    console.error(
      'Error modificando soporte:',
      error
    )


    mensajeModal.value =
      'No fue posible comunicarse con el servidor.'


  } finally {

    guardando.value =
      false
  }
}


// ==========================================================
// SOPORTE - ANULAR
// ==========================================================

async function anularSolicitud(
  item
) {

  try {

    const endpoint = item.proceso === 'MANTENIMIENTO'
      ? `/api/mantenimiento/requerimientos/${item.id}/`
      : `/api/soporte/tickets/${item.id}/`

    const respuesta =
      await fetch(
        endpoint,
        {

          method:
            'DELETE',

          headers:
            authHeaders(),
        }
      )


    let datos = {}


    try {

      datos =
        await respuesta.json()

    } catch {

      datos = {}
    }


    if (!respuesta.ok) {

      mostrarMensaje(
        datos.detalle
        ||
        'No se pudo cancelar la solicitud.',
        true
      )


      return
    }


    mostrarMensaje(
      'Solicitud cancelada correctamente.'
    )

    solicitudPorCancelar.value = null


    await cargarTodo()


  } catch (error) {

    console.error(
      'Error cancelando solicitud:',
      error
    )


    mostrarMensaje(
      'No fue posible cancelar la solicitud.',
      true
    )
  }
}


// ==========================================================
// INFORMAR CONFORMIDAD
// ==========================================================

function abrirConformidad(item, conforme) {
  conformidadPendiente.value = { item, conforme }
  observacionConformidad.value = ''
  mensajeConformidad.value = ''
}

function abrirVerificacion(item) {
  solicitudSeleccionada.value = item
  mostrarVerificacion.value = true
}

function cerrarVerificacion() {
  mostrarVerificacion.value = false
  solicitudSeleccionada.value = null
}

function cerrarConformidad() {
  if (guardandoConformidad.value) return
  conformidadPendiente.value = null
  observacionConformidad.value = ''
  mensajeConformidad.value = ''
}

function esImagen(url) {
  return /\.(png|jpe?g|gif|webp|bmp)(?:\?.*)?$/i.test(url || '')
}

async function confirmarConformidad() {
  const pendiente = conformidadPendiente.value
  if (!pendiente) return

  const observaciones = observacionConformidad.value.trim()
  if (!pendiente.conforme && !observaciones) {
    mensajeConformidad.value = 'Debe indicar por qué el problema continúa.'
    return
  }

  guardandoConformidad.value = true
  mensajeConformidad.value = ''

  try {

    const esMantenimiento = pendiente.item.proceso === 'MANTENIMIENTO'

    const url = esMantenimiento
      ? `/api/mantenimiento/requerimientos/${pendiente.item.id}/verificar-funcionamiento/`
      : `/api/soporte/tickets/${pendiente.item.id}/informar-conformidad/`

    const cuerpo = esMantenimiento
      ? { problema_resuelto: pendiente.conforme, observaciones }
      : { conformidad: pendiente.conforme, observaciones }

    const respuesta = await fetch(url, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(cuerpo),
    })

    let datos = {}

    try {
      datos = await respuesta.json()
    } catch {
      datos = {}
    }

    if (!respuesta.ok) {
      mensajeConformidad.value = datos.observaciones || datos.conformidad || datos.problema_resuelto || datos.detalle || 'No fue posible registrar la conformidad.'
      return
    }

    const conforme = pendiente.conforme
    conformidadPendiente.value = null
    observacionConformidad.value = ''
    mostrarVerificacion.value = false
    solicitudSeleccionada.value = null
    mensajeResultado.value = conforme
      ? {
          titulo: 'Conformidad registrada',
          texto: esMantenimiento
            ? 'Gracias. Quedó registrado que el problema fue resuelto. El Jefe de Mantenimiento confirmará el cierre.'
            : 'Gracias. El resultado fue confirmado correctamente. El Ticket continuará con su cierre administrativo.',
        }
      : {
          titulo: 'Observación enviada',
          texto: esMantenimiento
            ? 'El requerimiento volvió al técnico de mantenimiento para una nueva atención.'
            : 'La orden volvió al técnico responsable para una nueva atención y conservó su historial.',
        }

    await cargarTodo()

  } catch (error) {

    console.error('Error informando conformidad:', error)

    mensajeConformidad.value = 'No fue posible registrar la conformidad.'
  } finally {
    guardandoConformidad.value = false
  }
}


// ==========================================================
// MENSAJE BACKEND
// ==========================================================

function obtenerMensajeError(
  datos
) {

  if (
    datos?.detalle
  ) {

    return datos.detalle
  }


  if (
    datos?.detail
  ) {

    return datos.detail
  }


  const errores =
    Object.entries(
      datos
      ||
      {}
    )
      .map(
        ([campo, valor]) => {

          const texto =
            Array.isArray(
              valor
            )
              ? valor.join(', ')
              : String(valor)


          return (
            `${campo}: ${texto}`
          )
        }
      )
      .join(' | ')


  return (
    errores
    ||
    'No fue posible modificar la solicitud.'
  )
}


// ==========================================================
// MENSAJES
// ==========================================================

function mostrarMensaje(
  texto,
  error = false
) {

  mensaje.value =
    texto


  esError.value =
    error


  setTimeout(
    () => {

      mensaje.value =
        ''

    },
    3500
  )
}


// ==========================================================
// FECHA
// ==========================================================

function formatearFecha(
  fecha
) {

  if (!fecha) {

    return ''
  }


  try {

    return new Date(
      fecha
    ).toLocaleString(
      'es-BO',
      {
        dateStyle:
          'short',

        timeStyle:
          'short',
      }
    )

  } catch {

    return ''
  }
}


// ==========================================================
// ESTADO
// ==========================================================

function claseEstado(
  codigo
) {

  const estado =
    String(
      codigo
      || ''
    )
      .toUpperCase()
      .replaceAll(
        ' ',
        '_'
      )


  if (
    estado.includes(
      'ANUL'
    )
    ||
    estado.includes(
      'RECHAZ'
    )
  ) {

    return 'cancelled'
  }


  if (
    estado === 'CERRADO'
    ||
    estado === 'RESUELTO'
    ||
    estado === 'FINALIZADO'
  ) {

    return 'closed'
  }


  if (
    estado === 'NUEVO'
    ||
    estado === 'BORRADOR'
    ||
    estado === 'RECIBIDO'
  ) {

    return 'new'
  }


  return 'working'
}


// ==========================================================
// SESIÓN
// ==========================================================

function cerrarSesion() {

  localStorage.removeItem(
    'sigta_token'
  )


  localStorage.removeItem(
    'sigta_usuario'
  )


  router.push(
    '/login'
  )
}

</script>


<style scoped>

* {
  box-sizing: border-box;
}


/* ============================================
   LAYOUT
============================================ */

.layout {
  min-height: 100vh;
  display: flex;
  background: var(--sigta-azul-tenue);
  font-family: var(--sigta-fuente);
}


.content {
  flex: 1;
  min-width: 0;
  padding: 27px 30px 45px;
  overflow-x: hidden;
}


/* ============================================
   TOPBAR
============================================ */

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}




.topbar h1 {
  margin: 0;
  color: var(--sigta-texto);
  font-size: 33px;
}


.topbar p {
  margin: 5px 0 0;
  color: var(--sigta-texto-suave);
  font-size: 17px;
}


.btn-new {
  min-height: 41px;
  padding: 0 15px;
  border: none;
  border-radius: 7px;
  background: var(--sigta-mostaza);
  color: var(--sigta-texto);
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
}


/* ============================================
   RESUMEN
============================================ */

.summary {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 13px;
  margin-bottom: 17px;
}


.summary article {
  min-height: 104px;
  padding: 16px;
  border-top: 4px solid var(--sigta-mostaza);
  border-radius: 9px;
  background: white;
  box-shadow: 0 3px 12px rgba(0,0,0,.05);
}


.summary span,
.summary small {
  display: block;
}


.summary span {
  color: var(--sigta-texto-suave);
  font-size: 14px;
  font-weight: 800;
  text-transform: uppercase;
}


.summary strong {
  display: block;
  margin: 7px 0 4px;
  color: var(--sigta-azul);
  font-size: 31px;
}


.summary small {
  color: var(--sigta-texto-suave);
  font-size: 14px;
}


/* ============================================
   FILTROS
============================================ */

.filters-card {
  display: grid;
  grid-template-columns: 1fr 200px 220px;
  gap: 12px;
  margin-bottom: 16px;
  padding: 15px;
  border-radius: 9px;
  background: white;
  box-shadow: 0 3px 12px rgba(0,0,0,.04);
}


.search,
.filter {
  display: flex;
  flex-direction: column;
  gap: 5px;
}


.filters-card label {
  color: var(--sigta-texto-suave);
  font-size: 14px;
  font-weight: 800;
}


.filters-card input,
.filters-card select {
  width: 100%;
  height: 40px;
  padding: 0 11px;
  border: 1px solid var(--sigta-borde);
  border-radius: 6px;
  background: white;
  color: var(--sigta-azul);
  font-family: inherit;
  font-size: 15px;
  outline: none;
}


/* ============================================
   LISTADO
============================================ */

.requests-card {
  overflow: hidden;
  border-radius: 10px;
  background: white;
  box-shadow: 0 4px 14px rgba(0,0,0,.05);
}


.request-list {
  display: flex;
  flex-direction: column;
}


.request {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 17px 20px;
  border-bottom: 1px solid var(--sigta-azul-tenue);
  flex-wrap: wrap;
}

.cancel-confirmation {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: -4px;
  padding: 13px 15px;
  border-left: 4px solid var(--sigta-mostaza);
  border-radius: 7px;
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-azul);
}

.cancel-confirmation strong,
.cancel-confirmation span { display: block; }
.cancel-confirmation span { margin-top: 3px; color: var(--sigta-texto-suave); font-size: 13px; }
.cancel-confirmation__actions { display: flex; gap: 8px; }
.cancel-confirmation__actions button { min-width: 64px; padding: 9px 14px; border-radius: 7px; font-weight: 800; cursor: pointer; }
.confirm-no { border: 1px solid var(--sigta-borde); background: white; color: var(--sigta-texto); }
.confirm-yes { border: 0; background: var(--sigta-error); color: white; }


.request:last-child {
  border-bottom: none;
}


.request-main {
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: 145px 1fr;
  gap: 15px;
}


.request-code {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}


.process-indicator {
  width: 7px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 10px;
  background: var(--sigta-texto-suave);
}


.process-indicator.support {
  background: var(--sigta-azul);
}


.process-indicator.maintenance {
  background: var(--sigta-mostaza);
}


.request-code strong,
.request-code small {
  display: block;
}


.request-code strong {
  color: var(--sigta-azul);
  font-size: 15px;
}


.request-code small {
  margin-top: 4px;
  color: var(--sigta-texto-suave);
  font-size: 13px;
}


.request-info h3 {
  margin: 0 0 5px;
  color: var(--sigta-azul);
  font-size: 18px;
}


.request-info p {
  max-width: 700px;
  margin: 0 0 8px;
  overflow: hidden;
  color: var(--sigta-texto-suave);
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}


.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}


.meta span {
  padding: 4px 6px;
  border-radius: 4px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
  font-size: 13px;
}


.request-side {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 9px;
}


/* ============================================
   ESTADO
============================================ */

.status {
  display: inline-block;
  padding: 5px 8px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 800;
}


.status.new {
  background: var(--sigta-azul-tenue);
  color: var(--sigta-azul);
}


.status.working {
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-mostaza-oscuro);
}


.status.closed {
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
}


.status.cancelled {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
}


/* ============================================
   ACCIONES
============================================ */

.actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 5px;
}


.actions button {
  padding: 6px 8px;
  border: none;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}


.actions .view {
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
}


.actions .edit {
  background: var(--sigta-azul-tenue);
  color: var(--sigta-azul);
}


.actions .cancel {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
}


/* ============================================
   VACÍO
============================================ */

.empty {
  padding: 45px 20px;
  text-align: center;
  color: var(--sigta-texto-suave);
  font-size: 15px;
}


.empty h3 {
  color: var(--sigta-azul);
  font-size: 18px;
}


.empty p {
  max-width: 470px;
  margin: 6px auto 14px;
  line-height: 1.5;
}


.empty button {
  padding: 9px 13px;
  border: none;
  border-radius: 6px;
  background: var(--sigta-azul);
  color: white;
  font-size: 14px;
  cursor: pointer;
}


/* ============================================
   ALERTA
============================================ */

.alert {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 7px;
  font-size: 15px;
}


.alert.success {
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
}


.alert.error {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
}


/* ============================================
   MODAL
============================================ */

.overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(7,35,60,.6);
}


.modal {
  width: 100%;
  max-width: 650px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 24px;
  border-top: 4px solid var(--sigta-mostaza);
  border-radius: 12px;
  background: white;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}


.detail-modal {
  max-width: 740px;
}

.conformity-modal {
  max-width: 520px;
}

.verification-page {
  min-width: 0;
}

.verification-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 16px;
}

.verification-card {
  padding: 20px;
  border: 1px solid var(--sigta-borde);
  border-top: 3px solid var(--sigta-mostaza);
  border-radius: 11px;
  background: white;
}

.verification-card__head,
.verification-card dl div,
.verification-decision > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.verification-card h3 {
  margin: 18px 0;
  color: var(--sigta-texto);
}

.verification-card dl {
  margin: 0 0 18px;
}

.verification-card dl div {
  padding: 7px 0;
  border-bottom: 1px solid var(--sigta-borde);
}

.verification-card dt {
  color: var(--sigta-texto-suave);
  font-size: 12px;
}

.verification-card dd {
  margin: 0;
  color: var(--sigta-texto);
  font-size: 13px;
  font-weight: 700;
  text-align: right;
}

.verification-open {
  width: 100%;
  padding: 11px;
  border: 0;
  border-radius: 8px;
}

.verification-modal {
  width: min(980px, 95vw);
  max-height: 94vh;
  overflow: hidden;
  border-radius: 14px;
  background: white;
}

.verification-modal__head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: start;
  gap: 18px;
  padding: 19px 22px;
  background: var(--sigta-azul);
  color: white;
}

.verification-modal__head small,
.verification-modal__head strong,
.verification-modal__head h2 {
  display: block;
  color: white;
}

.verification-modal__head small {
  color: var(--sigta-mostaza-clara);
  font-weight: 800;
  letter-spacing: 1px;
}

.verification-modal__head h2 {
  margin: 4px 0 0;
  font-size: 20px;
}

.verification-modal__head button {
  border: 1px solid rgba(255,255,255,.4);
  border-radius: 7px;
  background: rgba(255,255,255,.1);
  color: white;
  padding: 8px 11px;
  cursor: pointer;
}

.verification-modal__body {
  max-height: calc(94vh - 100px);
  overflow-y: auto;
  padding: 22px;
}

.result-section {
  margin-bottom: 18px;
  padding: 18px;
  border: 1px solid var(--sigta-borde);
  border-radius: 10px;
}

.result-section h3 {
  margin: 0 0 15px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 11px;
}

.result-grid > div {
  padding: 12px;
  border-radius: 8px;
  background: #f5f8fc;
}

.result-grid small,
.result-grid strong {
  display: block;
}

.result-grid small {
  margin-bottom: 5px;
  color: var(--sigta-texto-suave);
}

.result-grid p {
  margin: 0;
  white-space: pre-line;
}

.wide-result {
  grid-column: 1 / -1;
}

.evidence-result {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 14px;
}

.evidence-result img {
  width: 150px;
  height: 95px;
  border-radius: 8px;
  object-fit: cover;
}

.evidence-result strong,
.technical-evidence-list > strong {
  display: block;
}

.technical-evidence-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 14px;
}

.technical-evidence-list > strong {
  flex-basis: 100%;
}

.verification-decision {
  padding: 20px;
  border-left: 4px solid var(--sigta-mostaza);
  border-radius: 10px;
  background: var(--sigta-mostaza-suave);
}

.verification-decision > small {
  color: var(--sigta-azul);
  font-weight: 900;
  letter-spacing: 1px;
}

.verification-decision h3 {
  margin: 7px 0;
}

.verification-decision > div {
  justify-content: flex-end;
  margin-top: 16px;
}

.verification-decision button {
  padding: 11px 16px;
  border-radius: 8px;
}

.danger-decision {
  color: var(--sigta-error);
  border-color: var(--sigta-error);
}

.conformity-message dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin: 14px 0;
}

.conformity-message dl div {
  padding: 9px;
  border-radius: 7px;
  background: white;
}

.conformity-message dt {
  color: var(--sigta-texto-suave);
  font-size: 11px;
}

.conformity-message dd {
  margin: 3px 0 0;
  font-weight: 800;
}

.result-message {
  z-index: 1300;
}

.result-message section {
  width: min(470px, 94vw);
  padding: 28px;
  border-top: 4px solid var(--sigta-mostaza);
  border-radius: 13px;
  background: white;
  color: var(--sigta-texto);
  text-align: center;
}

.result-message section > span {
  display: grid;
  width: 48px;
  height: 48px;
  margin: auto;
  place-items: center;
  border-radius: 50%;
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
  font-size: 25px;
  font-weight: 900;
}

.result-message button {
  padding: 10px 19px;
  border: 0;
  border-radius: 8px;
}

.conformity-message {
  margin: 8px 0 18px;
  padding: 16px;
  border-left: 4px solid var(--sigta-mostaza);
  border-radius: 8px;
  background: #f4f8fc;
  color: var(--sigta-texto);
}

.conformity-message p {
  margin: 7px 0 0;
  color: var(--sigta-texto-suave);
  line-height: 1.5;
}

.conformity-reason textarea {
  resize: vertical;
}

.conformity-reason small {
  display: block;
  margin-top: 5px;
  color: var(--sigta-texto-suave);
  text-align: right;
}

.request-documents {
  margin: 22px 0;
  padding: 20px;
  border: 1px solid #dce5ef;
  border-radius: 14px;
  background: #f7f9fc;
}
.request-documents__heading { display: flex; align-items: center; gap: 12px; color: var(--sigta-azul); }
.request-documents__heading h3 { margin: 0; font-size: 16px; }
.request-documents__heading p { margin: 5px 0 0; font-size: 13px; color: var(--sigta-texto-suave); }
.request-documents__links { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(230px, 100%), 1fr)); gap: 10px; margin: 16px 0; }
.request-document-link { display: flex; align-items: center; gap: 12px; padding: 14px; border: 1px solid #dce5ef; border-radius: 10px; background: white; color: var(--sigta-azul); text-decoration: none; transition: border-color .15s, box-shadow .15s; }
.request-document-link:hover { border-color: var(--sigta-azul); box-shadow: 0 3px 12px #123a6b12; }
.request-document-link > span:first-of-type { flex: 1; }
.request-document-link strong, .request-document-link small { display: block; }
.request-document-link strong { font-size: 13px; }
.request-document-link small { margin-top: 5px; font-size: 12px; color: var(--sigta-texto-suave); }
.request-document-link:focus-visible { outline: 2px solid var(--sigta-azul); outline-offset: 3px; }

.evidence-button {
  margin-top: 8px;
  padding: 9px 13px;
  border: 1px solid var(--sigta-azul);
  border-radius: 7px;
  background: white;
  color: var(--sigta-azul);
  font-weight: 800;
  cursor: pointer;
}

.evidence-viewer {
  z-index: 1200;
}

.evidence-viewer > section {
  width: min(1000px, 96vw);
  max-height: 92vh;
  overflow: hidden;
  border-radius: 12px;
  background: white;
}

.evidence-viewer header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 14px 18px;
  background: var(--sigta-azul);
  color: white;
}

.evidence-viewer header button {
  border: 1px solid rgba(255,255,255,.45);
  border-radius: 7px;
  background: rgba(255,255,255,.12);
  color: white;
  padding: 8px 11px;
  cursor: pointer;
}

.evidence-viewer .viewer-body {
  display: grid;
  min-height: 420px;
  max-height: calc(92vh - 65px);
  place-items: center;
  overflow: auto;
  padding: 18px;
  background: #edf3f9;
}

.evidence-viewer img {
  max-width: 100%;
  max-height: calc(92vh - 105px);
  object-fit: contain;
}

.evidence-viewer iframe {
  width: 100%;
  min-height: 70vh;
  border: 0;
  background: white;
}

@media (max-width: 700px) {
  .verification-modal {
    width: 95vw;
  }

  .verification-modal__head {
    grid-template-columns: auto 1fr auto;
    padding: 14px;
  }

  .verification-modal__head h2 {
    font-size: 16px;
  }

  .verification-modal__body {
    padding: 13px;
  }

  .result-grid,
  .conformity-message dl {
    grid-template-columns: 1fr;
  }

  .wide-result {
    grid-column: auto;
  }

  .evidence-result,
  .verification-decision > div {
    align-items: stretch;
    flex-direction: column;
  }

  .evidence-result img {
    width: 100%;
    height: auto;
    max-height: 230px;
  }

  .verification-decision button {
    width: 100%;
  }
}


.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 15px;
}


.modal-header h2 {
  margin: 3px 0;
  color: var(--sigta-texto);
  font-size: 25px;
}


.modal-header p {
  margin: 4px 0 0;
  color: var(--sigta-texto-suave);
  font-size: 15px;
}


.modal-code {
  color: var(--sigta-azul);
  font-size: 14px;
  font-weight: 800;
}


.close {
  border: none;
  background: transparent;
  color: var(--sigta-texto-suave);
  font-size: 33px;
  cursor: pointer;
}


.detail-status {
  margin-bottom: 16px;
}

.create-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin: -4px 0 20px;
}

.create-panel button {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--sigta-azul-texto-claro);
  border-radius: 12px;
  background: white;
  color: var(--sigta-texto);
  text-align: left;
  cursor: pointer;
}

.create-panel button:hover {
  border-color: var(--sigta-mostaza);
  box-shadow: 0 7px 18px rgba(23, 50, 74, .1);
  transform: translateY(-1px);
}

.create-panel button > span {
  font-size: 28px;
}

.create-panel strong,
.create-panel small {
  display: block;
}

.create-panel small {
  margin-top: 4px;
  color: var(--sigta-texto-suave);
}

@media (max-width: 760px) {
  .create-panel { grid-template-columns: 1fr; }
}

.timeline { display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:4px 0 22px; }
.timeline-step { position:relative;text-align:center;color:var(--sigta-texto-suave); }
.timeline-step::before { content:'';position:absolute;top:14px;left:-50%;width:100%;height:3px;background:var(--sigta-borde); }
.timeline-step:first-child::before { display:none; }
.timeline-step span { position:relative;z-index:1;display:grid;place-items:center;width:30px;height:30px;margin:auto auto 7px;border-radius:50%;background:var(--sigta-azul-texto-claro);font-weight:800; }
.timeline-step small { font-size:10px; }
.timeline-step.completado span,.timeline-step.actual span { background:var(--sigta-texto-suave);color:white; }
.timeline-step.completado::before,.timeline-step.actual::before { background:var(--sigta-texto-suave); }
.timeline-step.actual small { color:var(--sigta-texto);font-weight:800; }


.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}


.detail-grid > div {
  padding: 11px 13px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: var(--sigta-azul-tenue);
  transition: border-color .15s, background .15s;
}


.detail-grid > div:hover {
  border-color: var(--sigta-azul-texto-claro);
  background: white;
}


.detail-grid .full {
  grid-column: 1 / -1;
}


.detail-grid label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--sigta-texto-suave);
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
}


.detail-grid label :deep(.icono-sigta) {
  flex-shrink: 0;
  color: var(--sigta-azul-medio);
}


.detail-grid p {
  margin: 5px 0 0;
  color: var(--sigta-azul);
  font-size: 15px;
  line-height: 1.5;
}


.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 13px;
}


.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}


.field.full {
  grid-column: 1 / -1;
}


.field label {
  color: var(--sigta-azul);
  font-size: 15px;
  font-weight: 700;
}


.field input,
.field select,
.field textarea {
  width: 100%;
  padding: 10px 11px;
  border: 1px solid var(--sigta-borde);
  border-radius: 7px;
  font-family: inherit;
  font-size: 15px;
  outline: none;
}


.field textarea {
  min-height: 105px;
  resize: vertical;
}


.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}


.modal-footer button {
  min-height: 38px;
  padding: 0 14px;
  border-radius: 7px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}


.secondary {
  border: 1px solid var(--sigta-borde);
  background: white;
  color: var(--sigta-texto-suave);
}


.primary {
  border: none;
  background: var(--sigta-azul);
  color: white;
}


.modal-error {
  padding: 9px;
  border-radius: 6px;
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
  font-size: 15px;
}


/* ============================================
   RESPONSIVE
============================================ */

@media (max-width: 1000px) {

  .summary {
    grid-template-columns: repeat(2,1fr);
  }


  .filters-card {
    grid-template-columns: 1fr 1fr;
  }


  .search {
    grid-column: 1 / -1;
  }

}


@media (max-width: 760px) {

  .layout {
    display: block;
  }


  .content {
    padding: 16px;
  }


  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }


  .filters-card {
    grid-template-columns: 1fr;
  }


  .search {
    grid-column: auto;
  }


  .request {
    align-items: flex-start;
    flex-direction: column;
  }


  .request-main {
    grid-template-columns: 1fr;
  }


  .request-side {
    width: 100%;
    align-items: flex-start;
  }


  .actions {
    justify-content: flex-start;
  }


  .request-info p {
    white-space: normal;
  }


  .detail-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }


  .detail-grid .full,
  .field.full {
    grid-column: auto;
  }

}


@media (max-width: 480px) {

  .summary {
    grid-template-columns: 1fr;
  }


  .modal {
    padding: 18px;
  }

}

</style>
