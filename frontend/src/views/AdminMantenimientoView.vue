<template>
  <div class="layout">

    <AdminMenu />

    <main class="main">

      <!-- =================================================
           ENCABEZADO
      ================================================== -->

      <header class="page-header">

        <div>
          <h1>
            Mantenimiento
          </h1>

          <p>
            Gestión y seguimiento de requerimientos de
            mantenimiento preventivo y correctivo.
          </p>
        </div>



      
        <UsuarioHeader @actualizar="cargarTodo" />
      </header>


      <!-- =================================================
           MENSAJES
      ================================================== -->

      <div
        v-if="mensaje"
        :class="[
          'message',
          mensajeError
            ? 'error'
            : 'success'
        ]"
      >
        {{ mensaje }}
      </div>


      <!-- =================================================
           INDICADORES
      ================================================== -->

      <section class="stats">

        <article>
          <span>
            Requerimientos abiertos
          </span>

          <strong>
            {{ abiertos }}
          </strong>

          <small>
            Pendientes de finalización
          </small>
        </article>


        <article>
          <span>
            Preventivos
          </span>

          <strong>
            {{ preventivos.length }}
          </strong>

          <small>
            Mantenimientos preventivos
          </small>
        </article>


        <article>
          <span>
            Correctivos
          </span>

          <strong>
            {{ correctivos.length }}
          </strong>

          <small>
            Mantenimientos correctivos
          </small>
        </article>


        <article>
          <span>
            Requerimientos finalizados
          </span>

          <strong>
            {{ contarEstado('FINALIZADO') }}
          </strong>

          <small>
            Trabajos concluidos
          </small>
        </article>

      </section>


      <!-- =================================================
           FLUJO
      ================================================== -->

      <section class="flow-summary">

        <div>

          <span class="section-label">
            FLUJO DE MANTENIMIENTO
          </span>

          <strong>
            Seguimiento del requerimiento
          </strong>

          <p>
            El proceso sigue las actividades definidas para
            Servicios Generales, Auxiliar de Servicios Generales
            y Almacén.
          </p>

        </div>


        <div class="flow-steps">

          <span>
            Derivar a su auxiliar
          </span>

          <span>
            ¿Requiere reposición de almacén?
          </span>

          <span>
            Verificar existencia del producto en almacén
          </span>

          <span>
            Realiza el mantenimiento
          </span>

          <span>
            Realiza un informe y fotografía del trabajo realizado
          </span>

          <span>
            Finalizar requerimiento de mantenimiento
          </span>

        </div>

      </section>


      <!-- =================================================
           CARGANDO
      ================================================== -->

      <div
        v-if="cargando"
        class="loading"
      >
        Cargando requerimientos de mantenimiento...
      </div>


      <!-- =================================================
           CONTENIDO
      ================================================== -->

      <template v-else>

        <!-- ===============================================
             PREVENTIVO
        ================================================ -->

        <section class="maintenance-section">

          <div class="section-title preventivo">

            <div>
              <strong>
                PREVENTIVO
              </strong>

              <span>
                Mantenimiento preventivo institucional
              </span>
            </div>

            <span class="section-count">
              {{ preventivos.length }}
            </span>

          </div>


          <div class="kanban-scroll">

            <div class="kanban">

              <section
                v-for="columna in columnas"
                :key="`PRE-${columna.codigo}`"
                class="column"
              >

                <header class="column-header">

                  <div>
                    <strong>
                      {{ columna.nombre }}
                    </strong>

                    <small>
                      {{ columna.descripcion }}
                    </small>
                  </div>

                  <span>
                    {{
                      requerimientosPorColumna(
                        preventivos,
                        columna.codigo
                      ).length
                    }}
                  </span>

                </header>


                <div class="column-body">

                  <article
                    v-for="item in requerimientosPorColumna(
                      preventivos,
                      columna.codigo
                    )"
                    :key="item.id"
                    class="request-card"
                    @click="abrirRequerimiento(item)"
                  >

                    <div class="card-top">

                      <strong>
                        {{ item.codigo }}
                      </strong>

                      <span class="type-badge preventive">
                        Preventivo
                      </span>

                    </div>


                    <h3>
                      {{ item.titulo }}
                    </h3>


                    <div class="card-info">

                      <div>
                        <span>
                          Área
                        </span>

                        <strong>
                          {{
                            item.area_nombre
                            || 'No indicada'
                          }}
                        </strong>
                      </div>


                      <div>
                        <span>
                          Ubicación
                        </span>

                        <strong>
                          {{
                            item.ubicacion
                            || 'No indicada'
                          }}
                        </strong>
                      </div>


                      <div>
                        <span>
                          Auxiliar
                        </span>

                        <strong>
                          {{
                            item.auxiliar_asignado_nombre
                            || 'Sin asignar'
                          }}
                        </strong>
                      </div>

                    </div>


                    <div class="card-footer">

                      <div>
                        <span>
                          Solicitante
                        </span>

                        <strong>
                          {{
                            item.solicitante_nombre
                            || '-'
                          }}
                        </strong>
                      </div>

                      <button
                        type="button"
                        @click.stop="
                          abrirRequerimiento(item)
                        "
                      >
                        Gestionar
                      </button>

                    </div>

                  </article>


                  <div
                    v-if="
                      requerimientosPorColumna(
                        preventivos,
                        columna.codigo
                      ).length === 0
                    "
                    class="empty-column"
                  >
                    Sin requerimientos
                  </div>

                </div>

              </section>

            </div>

          </div>

        </section>


        <!-- ===============================================
             CORRECTIVO
        ================================================ -->

        <section class="maintenance-section">

          <div class="section-title correctivo">

            <div>
              <strong>
                CORRECTIVO
              </strong>

              <span>
                Reparación de fallas detectadas
              </span>
            </div>

            <span class="section-count">
              {{ correctivos.length }}
            </span>

          </div>


          <div class="kanban-scroll">

            <div class="kanban">

              <section
                v-for="columna in columnas"
                :key="`COR-${columna.codigo}`"
                class="column"
              >

                <header class="column-header">

                  <div>
                    <strong>
                      {{ columna.nombre }}
                    </strong>

                    <small>
                      {{ columna.descripcion }}
                    </small>
                  </div>

                  <span>
                    {{
                      requerimientosPorColumna(
                        correctivos,
                        columna.codigo
                      ).length
                    }}
                  </span>

                </header>


                <div class="column-body">

                  <article
                    v-for="item in requerimientosPorColumna(
                      correctivos,
                      columna.codigo
                    )"
                    :key="item.id"
                    class="request-card"
                    @click="abrirRequerimiento(item)"
                  >

                    <div class="card-top">

                      <strong>
                        {{ item.codigo }}
                      </strong>

                      <span class="type-badge corrective">
                        Correctivo
                      </span>

                    </div>


                    <h3>
                      {{ item.titulo }}
                    </h3>


                    <div class="card-info">

                      <div>
                        <span>
                          Área
                        </span>

                        <strong>
                          {{
                            item.area_nombre
                            || 'No indicada'
                          }}
                        </strong>
                      </div>


                      <div>
                        <span>
                          Ubicación
                        </span>

                        <strong>
                          {{
                            item.ubicacion
                            || 'No indicada'
                          }}
                        </strong>
                      </div>


                      <div>
                        <span>
                          Auxiliar
                        </span>

                        <strong>
                          {{
                            item.auxiliar_asignado_nombre
                            || 'Sin asignar'
                          }}
                        </strong>
                      </div>

                    </div>


                    <div class="card-footer">

                      <div>
                        <span>
                          Solicitante
                        </span>

                        <strong>
                          {{
                            item.solicitante_nombre
                            || '-'
                          }}
                        </strong>
                      </div>

                      <button
                        type="button"
                        @click.stop="
                          abrirRequerimiento(item)
                        "
                      >
                        Gestionar
                      </button>

                    </div>

                  </article>


                  <div
                    v-if="
                      requerimientosPorColumna(
                        correctivos,
                        columna.codigo
                      ).length === 0
                    "
                    class="empty-column"
                  >
                    Sin requerimientos
                  </div>

                </div>

              </section>

            </div>

          </div>

        </section>

      </template>

    </main>


    <!-- =====================================================
         MODAL
    ====================================================== -->

    <div
      v-if="requerimientoSeleccionado"
      class="overlay"
      @click.self="cerrarRequerimiento"
    >

      <section class="modal">

        <!-- ===============================================
             HEADER
        ================================================ -->

        <header class="modal-header">

          <div>

            <span class="modal-code">
              {{ requerimientoSeleccionado.codigo }}
            </span>

            <h2>
              {{ requerimientoSeleccionado.titulo }}
            </h2>

            <p>
              Requerimiento de Mantenimiento
            </p>

          </div>


          <button
            class="close-button"
            type="button"
            @click="cerrarRequerimiento"
          >
            ×
          </button>

        </header>


        <!-- ===============================================
             ESTADO
        ================================================ -->

        <DocumentosExpediente v-if="requerimientoSeleccionado" base="/api/mantenimiento/requerimientos" :id="requerimientoSeleccionado.id" />
        <section class="status-grid">

          <article>

            <span>
              Estado
            </span>

            <strong>
              {{
                requerimientoSeleccionado.estado_nombre
                || requerimientoSeleccionado.estado_codigo
              }}
            </strong>

          </article>


          <article>

            <span>
              Tipo
            </span>

            <strong>
              {{
                requerimientoSeleccionado.tipo === 'PREVENTIVO'
                  ? 'Preventivo'
                  : 'Correctivo'
              }}
            </strong>

          </article>


          <article>

            <span>
              Auxiliar asignado
            </span>

            <strong>
              {{
                requerimientoSeleccionado.auxiliar_asignado_nombre
                || 'Sin asignar'
              }}
            </strong>

          </article>


          <article>

            <span>
              Compra vinculada
            </span>

            <strong>
              {{
                requerimientoSeleccionado.codigo_compra_vinculada
                || 'No'
              }}
            </strong>

          </article>

        </section>


        <!-- ===============================================
             DATOS GENERALES
        ================================================ -->

        <section class="modal-section">

          <div class="section-number">
            1
          </div>

          <div class="section-content">

            <h3>
              Información del requerimiento
            </h3>

            <div class="detail-grid">

              <div>
                <span>
                  Solicitante
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.solicitante_nombre
                    || '-'
                  }}
                </strong>
              </div>


              <div>
                <span>
                  Correo
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.solicitante_email
                    || '-'
                  }}
                </strong>
              </div>


              <div>
                <span>
                  Área solicitante
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.area_nombre
                    || '-'
                  }}
                </strong>
              </div>


              <div>
                <span>
                  Ubicación
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.ubicacion
                    || '-'
                  }}
                </strong>
              </div>

            </div>

          </div>

        </section>


        <!-- ===============================================
             DESCRIPCIÓN
        ================================================ -->

        <section class="modal-section">

          <div class="section-number">
            2
          </div>

          <div class="section-content">

            <h3>
              Descripción
            </h3>

            <div class="text-box">
              {{
                requerimientoSeleccionado.descripcion
                || 'Sin descripción.'
              }}
            </div>

          </div>

        </section>


        <!-- ===============================================
             EVIDENCIA
        ================================================ -->

        <section class="modal-section">

          <div class="section-number">
            3
          </div>

          <div class="section-content">

            <h3>
              Evidencia
            </h3>


            <div
              v-if="
                requerimientoSeleccionado.evidencia
                || requerimientoSeleccionado.evidencia_archivo_url
              "
              class="evidence-box"
            >

              <p
                v-if="
                  requerimientoSeleccionado.evidencia
                "
              >
                {{
                  requerimientoSeleccionado.evidencia
                }}
              </p>


              <a
                v-if="
                  requerimientoSeleccionado.evidencia_archivo_url
                "
                :href="
                  requerimientoSeleccionado.evidencia_archivo_url
                "
                target="_blank"
                rel="noopener"
              >
                Ver archivo cargado
              </a>

            </div>


            <div
              v-else
              class="empty-evidence"
            >
              No se cargó evidencia.
            </div>

          </div>

        </section>


        <!-- ===============================================
             PRODUCTO / ALMACÉN
        ================================================ -->

        <section
          v-if="
            requerimientoSeleccionado.requiere_reposicion !== null
          "
          class="modal-section"
        >

          <div class="section-number">
            4
          </div>

          <div class="section-content">

            <h3>
              Reposición y almacén
            </h3>

            <div class="detail-grid">

              <div>
                <span>
                  Requiere reposición
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.requiere_reposicion
                      ? 'Sí'
                      : 'No'
                  }}
                </strong>
              </div>


              <div>
                <span>
                  Disponible en almacén
                </span>

                <strong>
                  {{
                    textoBooleano(
                      requerimientoSeleccionado
                        .producto_disponible_almacen
                    )
                  }}
                </strong>
              </div>


              <div
                v-if="
                  requerimientoSeleccionado.producto_requerido
                "
              >
                <span>
                  Producto
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.producto_requerido
                  }}
                </strong>
              </div>


              <div
                v-if="
                  requerimientoSeleccionado.cantidad_requerida
                "
              >
                <span>
                  Cantidad
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado.cantidad_requerida
                  }}
                </strong>
              </div>


              <div
                v-if="
                  requerimientoSeleccionado
                    .especificacion_producto
                "
                class="full-width"
              >

                <span>
                  Especificación
                </span>

                <strong>
                  {{
                    requerimientoSeleccionado
                      .especificacion_producto
                  }}
                </strong>

              </div>

            </div>

          </div>

        </section>


        <!-- ===============================================
             TRABAJO
        ================================================ -->

        <section
          v-if="
            requerimientoSeleccionado.trabajo_realizado
            || requerimientoSeleccionado.informe_trabajo
          "
          class="modal-section"
        >

          <div class="section-number">
            5
          </div>

          <div class="section-content">

            <h3>
              Trabajo realizado
            </h3>


            <div
              v-if="
                requerimientoSeleccionado.trabajo_realizado
              "
              class="text-box block-space"
            >

              <strong class="mini-title">
                Mantenimiento realizado
              </strong>

              <p>
                {{
                  requerimientoSeleccionado.trabajo_realizado
                }}
              </p>

            </div>


            <div
              v-if="
                requerimientoSeleccionado.informe_trabajo
              "
              class="text-box block-space"
            >

              <strong class="mini-title">
                Informe
              </strong>

              <p>
                {{
                  requerimientoSeleccionado.informe_trabajo
                }}
              </p>

            </div>


            <a
              v-if="
                requerimientoSeleccionado.fotografia_trabajo_url
              "
              :href="
                requerimientoSeleccionado.fotografia_trabajo_url
              "
              target="_blank"
              rel="noopener"
              class="file-link"
            >
              Ver fotografía del trabajo
            </a>

          </div>

        </section>


        <!-- =================================================
             ACTIVIDADES
        ================================================== -->

        <section class="workflow-section">

          <span class="section-label">
            ACTIVIDAD DEL PROCESO
          </span>


          <!-- =============================================
               RECIBIDO
          ============================================== -->

          <div
            v-if="estadoActual === 'RECIBIDO'"
            class="action-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                1
              </span>

              <div>

                <h3>
                  Derivar a su auxiliar
                </h3>

                <p>
                  Servicios Generales debe seleccionar
                  al auxiliar responsable.
                </p>

              </div>

            </div>


            <div class="field">

              <label>
                Auxiliar de Servicios Generales
              </label>

              <select
                v-model="
                  formDerivar.auxiliar_id
                "
              >

                <option value="">
                  Seleccione un auxiliar
                </option>

                <option
                  v-for="usuario in auxiliares"
                  :key="usuario.id"
                  :value="usuario.id"
                >
                  {{
                    usuario.nombre_completo
                    || usuario.email
                  }}
                </option>

              </select>


              <small
                v-if="
                  auxiliares.length === 0
                "
              >
                No existen usuarios activos con rol
                AUXILIAR_SERVICIOS_GENERALES.
              </small>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="
                procesando
                || !formDerivar.auxiliar_id
              "
              @click="derivarAuxiliar"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : 'Derivar a su auxiliar'
              }}
            </button>

          </div>


          <!-- =============================================
               DERIVADO
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'DERIVADO'
            "
            class="action-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                2
              </span>

              <div>

                <h3>
                  ¿Requiere reposición de almacén?
                </h3>

                <p>
                  Determine si el mantenimiento necesita
                  algún producto o material de almacén.
                </p>

              </div>

            </div>


            <div class="decision-grid">

              <label
                :class="{
                  selected:
                    formReposicion.requiere_reposicion === false
                }"
              >

                <input
                  v-model="
                    formReposicion.requiere_reposicion
                  "
                  type="radio"
                  :value="false"
                />

                <strong>
                  No requiere reposición
                </strong>

                <span>
                  Puede realizarse directamente
                  el mantenimiento.
                </span>

              </label>


              <label
                :class="{
                  selected:
                    formReposicion.requiere_reposicion === true
                }"
              >

                <input
                  v-model="
                    formReposicion.requiere_reposicion
                  "
                  type="radio"
                  :value="true"
                />

                <strong>
                  Sí requiere reposición
                </strong>

                <span>
                  Se debe consultar existencia
                  en almacén.
                </span>

              </label>

            </div>


            <div
              v-if="
                formReposicion.requiere_reposicion === true
              "
              class="product-form"
            >

              <div class="field">

                <label>
                  Producto requerido
                </label>

                <input
                  v-model="
                    formReposicion.producto_requerido
                  "
                  placeholder="Ej.: foco LED, cable, cerradura..."
                />

              </div>


              <div class="field">

                <label>
                  Cantidad
                </label>

                <input
                  v-model.number="
                    formReposicion.cantidad_requerida
                  "
                  type="number"
                  min="1"
                />

              </div>


              <div class="field full-width">

                <label>
                  Especificación del producto
                </label>

                <textarea
                  v-model="
                    formReposicion.especificacion_producto
                  "
                  placeholder="Indique características necesarias..."
                ></textarea>

              </div>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="
                !puedeVerificarReposicion
              "
              @click="verificarReposicion"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : 'Registrar decisión de reposición'
              }}
            </button>

          </div>


          <!-- =============================================
               REVISIÓN DE ALMACÉN
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'REVISION_ALMACEN'
            "
            class="action-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                3
              </span>

              <div>

                <h3>
                  Hay producto en el almacén
                </h3>

                <p>
                  Registre si existe el producto solicitado.
                </p>

              </div>

            </div>


            <div class="product-summary">

              <span>
                Producto solicitado
              </span>

              <strong>
                {{
                  requerimientoSeleccionado.producto_requerido
                }}
              </strong>

              <small>
                Cantidad:
                {{
                  requerimientoSeleccionado.cantidad_requerida
                }}
              </small>

            </div>


            <div class="decision-grid">

              <label
                :class="{
                  selected:
                    formAlmacen.producto_disponible === true
                }"
              >

                <input
                  v-model="
                    formAlmacen.producto_disponible
                  "
                  type="radio"
                  :value="true"
                />

                <strong>
                  Hay producto en el almacén
                </strong>

                <span>
                  Entrega el producto al auxiliar de Servicios Generales.
                </span>

              </label>


              <label
                :class="{
                  selected:
                    formAlmacen.producto_disponible === false
                }"
              >

                <input
                  v-model="
                    formAlmacen.producto_disponible
                  "
                  type="radio"
                  :value="false"
                />

                <strong>
                  No hay producto en el almacén
                </strong>

                <span>
                  Reporta no existencia del producto y deriva al subproceso Compra Caja Chica.
                </span>

              </label>

            </div>


            <div class="field">

              <label>
                Observación de almacén
              </label>

              <textarea
                v-model="
                  formAlmacen.observacion_almacen
                "
                placeholder="Observación opcional..."
              ></textarea>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="
                procesando
                || formAlmacen.producto_disponible === null
              "
              @click="reportarExistencia"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : 'Registrar existencia en almacén'
              }}
            </button>

          </div>


          <!-- =============================================
               ESPERA DE COMPRA
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'EN_ESPERA_COMPRA'
            "
            class="action-card purchase-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                4
              </span>

              <div>

                <h3>
                  Subproceso Compra Caja Chica
                </h3>

                <p>
                  El producto no estaba disponible en
                  almacén. Registre la compra cuando
                  haya sido completada.
                </p>

              </div>

            </div>


            <div class="field">

              <label>
                Expediente de compra vinculado
              </label>

              <p v-if="requerimientoSeleccionado?.compra_vinculada">
                <strong>{{ requerimientoSeleccionado.compra_vinculada.codigo }}</strong>
                — {{ requerimientoSeleccionado.compra_vinculada.estado_nombre }}
              </p>

              <p v-else>
                Aún no se generó el expediente de compra para este requerimiento.
              </p>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="
                procesando
                || requerimientoSeleccionado?.compra_vinculada?.estado !== 'CERRADO_ARCHIVADO'
              "
              @click="registrarCompra"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : requerimientoSeleccionado?.compra_vinculada?.estado === 'CERRADO_ARCHIVADO'
                    ? 'Registrar producto recibido de Compra Caja Chica'
                    : 'Esperando que Compras cierre el expediente'
              }}
            </button>

          </div>


          <!-- =============================================
               EN MANTENIMIENTO - TRABAJO
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'EN_MANTENIMIENTO'
              && !requerimientoSeleccionado.trabajo_realizado
            "
            class="action-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                5
              </span>

              <div>

                <h3>
                  Realiza el mantenimiento
                </h3>

                <p>
                  Registre el trabajo efectuado por
                  el auxiliar de Servicios Generales.
                </p>

              </div>

            </div>


            <div class="field">

              <label>
                Trabajo realizado
              </label>

              <textarea
                v-model="
                  formTrabajo.trabajo_realizado
                "
                placeholder="Describa el mantenimiento realizado..."
              ></textarea>

            </div>


            <div class="field">

              <label>
                Observaciones
              </label>

              <textarea
                v-model="
                  formTrabajo.observaciones_trabajo
                "
                placeholder="Observaciones adicionales..."
              ></textarea>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="
                procesando
                || !formTrabajo.trabajo_realizado.trim()
              "
              @click="realizarMantenimiento"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : 'Registrar mantenimiento realizado'
              }}
            </button>

          </div>


          <!-- =============================================
               INFORME Y FOTOGRAFÍA
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'EN_MANTENIMIENTO'
              && requerimientoSeleccionado.trabajo_realizado
            "
            class="action-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                6
              </span>

              <div>

                <h3>
                  Realiza un informe y fotografía del trabajo realizado
                </h3>

                <p>
                  Registre el informe del trabajo y cargue
                  una fotografía como evidencia.
                </p>

              </div>

            </div>


            <div class="field">

              <label>
                Informe del trabajo
              </label>

              <textarea
                v-model="
                  formInforme.informe_trabajo
                "
                placeholder="Detalle el trabajo concluido..."
              ></textarea>

            </div>


            <div class="field">

              <label>
                Fotografía del trabajo
              </label>

              <ArchivoInput
                type="file"
                accept=".jpg,.jpeg,.png,.pdf"
                @change="seleccionarFotografia" />

              <small
                v-if="
                  formInforme.nombre_archivo
                "
              >
                Archivo seleccionado:
                {{ formInforme.nombre_archivo }}
              </small>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="
                procesando
                || !formInforme.informe_trabajo.trim()
              "
              @click="registrarInforme"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : 'Registrar informe y fotografía del trabajo realizado'
              }}
            </button>

          </div>


          <!-- =============================================
               INFORME REGISTRADO
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'INFORME_REGISTRADO'
            "
            class="action-card"
          >

            <div class="action-heading">

              <span class="step-circle">
                7
              </span>

              <div>

                <h3>
                  Finalizar requerimiento de mantenimiento
                </h3>

                <p>
                  El trabajo y el informe fueron registrados.
                  El requerimiento puede finalizarse.
                </p>

              </div>

            </div>


            <button
              class="primary-action"
              type="button"
              :disabled="procesando"
              @click="finalizarRequerimiento"
            >
              {{
                procesando
                  ? 'Procesando...'
                  : 'Finalizar requerimiento de mantenimiento'
              }}
            </button>

          </div>


          <!-- =============================================
               FINALIZADO
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'FINALIZADO'
            "
            class="complete-card"
          >

            <div class="complete-icon">
              ✓
            </div>

            <div>

              <h3>
                Requerimiento de mantenimiento finalizado
              </h3>

              <p>
                El trabajo de mantenimiento fue registrado
                y el requerimiento se encuentra concluido.
              </p>

            </div>

          </div>


          <!-- =============================================
               ANULADO
          ============================================== -->

          <div
            v-else-if="
              estadoActual === 'ANULADO'
            "
            class="cancelled-card"
          >
            Este requerimiento fue anulado.
          </div>

        </section>


        <!-- ===============================================
             FOOTER
        ================================================ -->

        <footer class="modal-footer">

          <button
            class="secondary-button"
            type="button"
            @click="cerrarRequerimiento"
          >
            Cerrar
          </button>

        </footer>

      </section>

    </div>

  </div>
</template>


<script setup>
import DocumentosExpediente from '../components/DocumentosExpediente.vue'
import UsuarioHeader from '../components/UsuarioHeader.vue'

import {
  computed,
  onMounted,
  reactive,
  ref
} from 'vue'

import {
  useRouter
} from 'vue-router'

import AdminMenu
  from '../components/AdminMenu.vue'


const router =
  useRouter()


// ==========================================================
// DATOS
// ==========================================================

const requerimientos =
  ref([])

const usuarios =
  ref([])

const requerimientoSeleccionado =
  ref(null)

const cargando =
  ref(true)

const procesando =
  ref(false)

const mensaje =
  ref('')

const mensajeError =
  ref(false)


// ==========================================================
// COLUMNAS
// ==========================================================

const columnas = [

  {
    codigo: 'RECIBIDO',
    nombre: 'Recibido',
    descripcion: 'Servicios Generales',
  },

  {
    codigo: 'DERIVADO',
    nombre: 'Derivado',
    descripcion: 'Auxiliar asignado',
  },

  {
    codigo: 'REVISION_ALMACEN',
    nombre: 'Verificación de almacén',
    descripcion: 'Existencia del producto',
  },

  {
    codigo: 'EN_ESPERA_COMPRA',
    nombre: 'Subproceso Compra Caja Chica',
    descripcion: 'Subproceso Compra Caja Chica',
  },

  {
    codigo: 'EN_MANTENIMIENTO',
    nombre: 'Mantenimiento en ejecución',
    descripcion: 'Realiza el mantenimiento',
  },

  {
    codigo: 'INFORME_REGISTRADO',
    nombre: 'Informe y fotografía registrados',
    descripcion: 'Informe del trabajo realizado',
  },

  {
    codigo: 'FINALIZADO',
    nombre: 'Requerimiento finalizado',
    descripcion: 'Mantenimiento concluido',
  },

]


// ==========================================================
// FORMULARIOS
// ==========================================================

const formDerivar =
  reactive({
    auxiliar_id: '',
  })


const formReposicion =
  reactive({
    requiere_reposicion: null,
    producto_requerido: '',
    cantidad_requerida: 1,
    especificacion_producto: '',
  })


const formAlmacen =
  reactive({
    producto_disponible: null,
    observacion_almacen: '',
  })




const formTrabajo =
  reactive({
    trabajo_realizado: '',
    observaciones_trabajo: '',
  })


const formInforme =
  reactive({
    informe_trabajo: '',
    fotografia_trabajo: null,
    nombre_archivo: '',
  })


// ==========================================================
// TOKEN
// ==========================================================

function token() {

  return localStorage.getItem(
    'sigta_token'
  )
}


function headersJson() {

  return {
    Authorization:
      `Token ${token()}`,

    Accept:
      'application/json',

    'Content-Type':
      'application/json',
  }
}


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


    await cargarTodo()
  }
)


// ==========================================================
// NORMALIZAR
// ==========================================================

function normalizarLista(
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
// CARGAR TODO
// ==========================================================

async function cargarTodo() {

  cargando.value =
    true


  try {

    await Promise.all([
      cargarRequerimientos(),
      cargarUsuarios(),
    ])

  } finally {

    cargando.value =
      false
  }
}


// ==========================================================
// REQUERIMIENTOS
// ==========================================================

async function cargarRequerimientos() {

  try {

    const respuesta =
      await fetch(
        '/api/mantenimiento/requerimientos/',
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

      return
    }


    if (!respuesta.ok) {

      throw new Error(
        `Error ${respuesta.status}`
      )
    }


    requerimientos.value =
      normalizarLista(
        await respuesta.json()
      )


  } catch (error) {

    console.error(
      'Error mantenimiento:',
      error
    )


    mostrarMensaje(
      'No fue posible cargar los requerimientos de mantenimiento.',
      true
    )
  }
}


// ==========================================================
// USUARIOS
// ==========================================================

async function cargarUsuarios() {

  try {

    const respuesta =
      await fetch(
        '/api/usuarios/usuarios/',
        {
          headers: {
            Authorization:
              `Token ${token()}`,

            Accept:
              'application/json',
          }
        }
      )


    if (!respuesta.ok) {

      return
    }


    usuarios.value =
      normalizarLista(
        await respuesta.json()
      )


  } catch (error) {

    console.error(
      'Error usuarios:',
      error
    )
  }
}


// ==========================================================
// AUXILIARES
// ==========================================================

const auxiliares =
  computed(() => {

    return usuarios.value.filter(
      usuario => {

        if (
          usuario.is_active === false
        ) {

          return false
        }


        if (
          !Array.isArray(
            usuario.roles
          )
        ) {

          return false
        }


        return usuario.roles.some(
          asignacion => {

            return (
              String(
                asignacion?.rol_codigo
                || ''
              )
                .trim()
                .toUpperCase()
              ===
              'AUXILIAR_SERVICIOS_GENERALES'
            )
          }
        )
      }
    )
  })


// ==========================================================
// PREVENTIVOS / CORRECTIVOS
// ==========================================================

const preventivos =
  computed(() => {

    return requerimientos.value.filter(
      item =>
        String(
          item.tipo
          || ''
        )
          .toUpperCase()
        ===
        'PREVENTIVO'
    )
  })


const correctivos =
  computed(() => {

    return requerimientos.value.filter(
      item =>
        String(
          item.tipo
          || ''
        )
          .toUpperCase()
        ===
        'CORRECTIVO'
    )
  })


// ==========================================================
// ESTADO
// ==========================================================

function estadoItem(
  item
) {

  return String(
    item?.estado_codigo
    || ''
  )
    .trim()
    .toUpperCase()
    .replace(
      /\s+/g,
      '_'
    )
}


const estadoActual =
  computed(() => {

    return estadoItem(
      requerimientoSeleccionado.value
    )
  })


// ==========================================================
// COLUMNAS
// ==========================================================

function requerimientosPorColumna(
  lista,
  estado
) {

  return lista.filter(
    item =>
      estadoItem(item)
      ===
      estado
  )
}


// ==========================================================
// INDICADORES
// ==========================================================

function contarEstado(
  estado
) {

  return requerimientos.value.filter(
    item =>
      estadoItem(item)
      ===
      estado
  ).length
}


const abiertos =
  computed(() => {

    return requerimientos.value.filter(
      item =>
        ![
          'FINALIZADO',
          'ANULADO'
        ].includes(
          estadoItem(item)
        )
    ).length
  })


// ==========================================================
// ABRIR / CERRAR
// ==========================================================

function abrirRequerimiento(
  item
) {

  requerimientoSeleccionado.value = {
    ...item
  }


  reiniciarFormularios()
}


function cerrarRequerimiento() {

  requerimientoSeleccionado.value =
    null
}


// ==========================================================
// REINICIAR FORMULARIOS
// ==========================================================

function reiniciarFormularios() {

  Object.assign(
    formDerivar,
    {
      auxiliar_id: '',
    }
  )


  Object.assign(
    formReposicion,
    {
      requiere_reposicion: null,
      producto_requerido: '',
      cantidad_requerida: 1,
      especificacion_producto: '',
    }
  )


  Object.assign(
    formAlmacen,
    {
      producto_disponible: null,
      observacion_almacen: '',
    }
  )


  Object.assign(
    formTrabajo,
    {
      trabajo_realizado: '',
      observaciones_trabajo: '',
    }
  )


  Object.assign(
    formInforme,
    {
      informe_trabajo: '',
      fotografia_trabajo: null,
      nombre_archivo: '',
    }
  )
}


// ==========================================================
// VALIDACIÓN REPOSICIÓN
// ==========================================================

const puedeVerificarReposicion =
  computed(() => {

    if (
      procesando.value
    ) {

      return false
    }


    if (
      formReposicion.requiere_reposicion
      === null
    ) {

      return false
    }


    if (
      formReposicion.requiere_reposicion
      === true
    ) {

      return Boolean(
        formReposicion
          .producto_requerido
          .trim()
      )
      &&
      Number(
        formReposicion
          .cantidad_requerida
      ) > 0
    }


    return true
  })


// ==========================================================
// EJECUTAR JSON
// ==========================================================

async function ejecutarAccion(
  endpoint,
  body = {}
) {

  if (
    !requerimientoSeleccionado.value
  ) {

    return null
  }


  procesando.value =
    true


  try {

    const respuesta =
      await fetch(
        `/api/mantenimiento/requerimientos/${requerimientoSeleccionado.value.id}/${endpoint}/`,
        {
          method:
            'POST',

          headers:
            headersJson(),

          body:
            JSON.stringify(
              body
            ),
        }
      )


    const datos =
      await leerJson(
        respuesta
      )


    if (
      !respuesta.ok
    ) {

      throw new Error(
        obtenerError(
          datos
        )
      )
    }


    mostrarMensaje(
      datos.mensaje
      ||
      'Acción realizada correctamente.'
    )


    await actualizarSeleccionado()


    return datos


  } catch (error) {

    console.error(
      error
    )


    mostrarMensaje(
      error.message
      ||
      'No fue posible realizar la acción.',
      true
    )


    return null


  } finally {

    procesando.value =
      false
  }
}


// ==========================================================
// ACTUALIZAR SELECCIONADO
// ==========================================================

async function actualizarSeleccionado() {

  const id =
    requerimientoSeleccionado
      .value
      ?.id


  await cargarRequerimientos()


  if (!id) {

    return
  }


  const actualizado =
    requerimientos.value.find(
      item =>
        Number(item.id)
        ===
        Number(id)
    )


  if (
    actualizado
  ) {

    requerimientoSeleccionado.value = {
      ...actualizado
    }
  }
}


// ==========================================================
// 1. DERIVAR
// ==========================================================

async function derivarAuxiliar() {

  // El BPMN separa la derivación en tres actos de la jefatura: validar el
  // ticket, clasificar su prioridad y designar al técnico. Desde este panel
  // de supervisión se ejecutan en secuencia.
  if (!formDerivar.auxiliar_id) {

    mensaje.value = 'Seleccione al técnico responsable.'
    mensajeError.value = true

    return
  }

  const estado =
    requerimientoSeleccionado.value?.estado_codigo

  if (estado === 'RECIBIDO') {

    await ejecutarAccion('validar-ticket', { es_valido: true })
  }

  if (!requerimientoSeleccionado.value?.prioridad_jefatura) {

    await ejecutarAccion(
      'clasificar-prioridad',
      {
        prioridad: 'MEDIA',
        criterio_prioridad: 'Prioridad asignada desde el panel de supervisión.',
      }
    )
  }

  await ejecutarAccion(
    'designar-revision',
    {
      tecnico_id:
        Number(
          formDerivar.auxiliar_id
        ),
    }
  )
}


// ==========================================================
// 2. REPOSICIÓN
// ==========================================================

async function verificarReposicion() {

  // En el BPMN vigente el técnico no "verifica reposición": realiza un
  // requerimiento de componente con su cotización, o registra el
  // diagnóstico cuando no hace falta comprar nada.
  if (formReposicion.requiere_reposicion) {

    await ejecutarAccion(
      'solicitar-requerimiento',
      {
        producto_requerido: formReposicion.producto_requerido,
        cantidad_requerida: Number(formReposicion.cantidad_requerida) || 1,
        especificacion_producto: formReposicion.especificacion_producto,
      }
    )

    return
  }

  await ejecutarAccion(
    'registrar-diagnostico',
    {
      diagnostico:
        formReposicion.especificacion_producto
        || 'Diagnóstico registrado desde el panel de supervisión.',
      plan_solucion: 'Intervención sin requerimiento de componentes.',
    }
  )
}


// ==========================================================
// 3. ALMACÉN
// ==========================================================

async function reportarExistencia() {

  // La consulta de stock desapareció del proceso: hoy la jefatura evalúa
  // la viabilidad de la compra desde su propio panel.
  mensaje.value =
    'La viabilidad de la compra se evalúa desde el panel del Jefe de Mantenimiento.'

  mensajeError.value = true
}


// ==========================================================
// 4. COMPRA
// ==========================================================

async function registrarCompra() {

  // El backend ya no recibe un código a mano: confirma el
  // expediente real vinculado al requerimiento
  // y exige que Compras lo haya cerrado y archivado.
  await ejecutarAccion(
    'registrar-compra',
    {}
  )
}


// ==========================================================
// 5. MANTENIMIENTO
// ==========================================================

async function realizarMantenimiento() {

  await ejecutarAccion(
    'realizar-mantenimiento',
    {
      trabajo_realizado:
        formTrabajo
          .trabajo_realizado
          .trim(),

      observaciones_trabajo:
        formTrabajo
          .observaciones_trabajo
          .trim(),
    }
  )
}


// ==========================================================
// ARCHIVO INFORME
// ==========================================================

function seleccionarFotografia(
  event
) {

  const archivo =
    event.target.files?.[0]
    ||
    null


  formInforme.fotografia_trabajo =
    archivo


  formInforme.nombre_archivo =
    archivo
      ? archivo.name
      : ''
}


// ==========================================================
// 6. INFORME
// ==========================================================

async function registrarInforme() {

  if (
    !requerimientoSeleccionado.value
  ) {

    return
  }


  procesando.value =
    true


  try {

    const formData =
      new FormData()


    formData.append(
      'informe_trabajo',
      formInforme
        .informe_trabajo
        .trim()
    )


    if (
      formInforme.fotografia_trabajo
    ) {

      formData.append(
        'fotografia_trabajo',
        formInforme.fotografia_trabajo
      )
    }


    const respuesta =
      await fetch(
        `/api/mantenimiento/requerimientos/${requerimientoSeleccionado.value.id}/registrar-informe/`,
        {
          method:
            'POST',

          headers: {
            Authorization:
              `Token ${token()}`,

            Accept:
              'application/json',
          },

          body:
            formData,
        }
      )


    const datos =
      await leerJson(
        respuesta
      )


    if (
      !respuesta.ok
    ) {

      throw new Error(
        obtenerError(
          datos
        )
      )
    }


    mostrarMensaje(
      datos.mensaje
      ||
      'Informe y fotografía registrados correctamente.'
    )


    await actualizarSeleccionado()


  } catch (error) {

    console.error(
      error
    )


    mostrarMensaje(
      error.message
      ||
      'No fue posible registrar el informe.',
      true
    )


  } finally {

    procesando.value =
      false
  }
}


// ==========================================================
// 7. FINALIZAR
// ==========================================================

async function finalizarRequerimiento() {

  // El proceso termina cuando la Dirección acusa recibo del informe final.
  await ejecutarAccion(
    'recibir-informe'
  )
}


// ==========================================================
// BOOLEANOS
// ==========================================================

function textoBooleano(
  valor
) {

  if (
    valor === true
  ) {

    return 'Sí'
  }


  if (
    valor === false
  ) {

    return 'No'
  }


  return 'Pendiente'
}


// ==========================================================
// JSON
// ==========================================================

async function leerJson(
  respuesta
) {

  try {

    return await respuesta.json()

  } catch {

    return {}
  }
}


// ==========================================================
// ERROR
// ==========================================================

function obtenerError(
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


  const entrada =
    Object.entries(
      datos
      ||
      {}
    )[0]


  if (
    !entrada
  ) {

    return (
      'Revise la información ingresada.'
    )
  }


  const [
    campo,
    valor
  ] =
    entrada


  return (
    `${campo}: ${
      Array.isArray(valor)
        ? valor.join(', ')
        : String(valor)
    }`
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


  mensajeError.value =
    error


  setTimeout(
    () => {

      mensaje.value =
        ''

    },
    5000
  )
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


/* =========================================================
   LAYOUT
========================================================= */

.layout {
  min-height: 100vh;
  display: flex;
  background: var(--sigta-azul-tenue);
  font-family: var(--sigta-fuente);
}


.main {
  flex: 1;
  min-width: 0;
  padding: 27px;
  overflow-x: hidden;
}


/* =========================================================
   HEADER
========================================================= */

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}


.breadcrumb {
  display: block;
  margin-bottom: 6px;
  color: var(--sigta-texto-suave);
  font-size: 9px;
}


.page-header h1 {
  margin: 0;
  color: var(--sigta-texto);
  font-size: 27px;
}


.page-header p {
  margin: 5px 0 0;
  color: var(--sigta-texto-suave);
  font-size: 11px;
}


.refresh-button {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--sigta-azul);
  border-radius: 7px;
  background: white;
  color: var(--sigta-azul);
  font-size: 9px;
  font-weight: 800;
  cursor: pointer;
}


/* =========================================================
   MENSAJES
========================================================= */

.message {
  margin-bottom: 15px;
  padding: 11px 13px;
  border-radius: 7px;
  font-size: 9px;
}


.message.success {
  background: var(--sigta-exito-fondo);
  color: var(--sigta-exito);
}


.message.error {
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
}


/* =========================================================
   STATS
========================================================= */

.stats {
  display: grid;
  grid-template-columns: repeat(4,1fr);
  gap: 13px;
  margin-bottom: 17px;
}


.stats article {
  min-height: 105px;
  padding: 17px;
  border-top: 4px solid var(--sigta-mostaza);
  border-radius: 9px;
  background: white;
  box-shadow: 0 3px 12px rgba(0,0,0,.05);
}


.stats span {
  display: block;
  color: var(--sigta-texto-suave);
  font-size: 8px;
  font-weight: 800;
  text-transform: uppercase;
}


.stats strong {
  display: block;
  margin: 7px 0 4px;
  color: var(--sigta-azul);
  font-size: 26px;
}


.stats small {
  color: var(--sigta-texto-suave);
  font-size: 8px;
}


/* =========================================================
   FLOW
========================================================= */

.flow-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 20px;
  padding: 15px 17px;
  border-left: 4px solid var(--sigta-mostaza);
  border-radius: 8px;
  background: white;
}


.section-label {
  display: block;
  margin-bottom: 4px;
  color: var(--sigta-azul);
  font-size: 7px;
  font-weight: 900;
  letter-spacing: .8px;
}


.flow-summary strong {
  color: var(--sigta-texto);
  font-size: 11px;
}


.flow-summary p {
  margin: 4px 0 0;
  color: var(--sigta-texto-suave);
  font-size: 8px;
}


.flow-steps {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 5px;
}


.flow-steps span {
  padding: 5px 7px;
  border-radius: 5px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


/* =========================================================
   SECTION
========================================================= */

.maintenance-section {
  margin-bottom: 25px;
  padding-bottom: 12px;
  border-radius: 9px;
  background: white;
  box-shadow: 0 3px 12px rgba(0,0,0,.04);
}


.section-title {
  min-height: 53px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  border-radius: 8px 8px 0 0;
}


.section-title strong,
.section-title span {
  display: block;
}


.section-title strong {
  font-size: 11px;
}


.section-title > div > span {
  margin-top: 3px;
  font-size: 8px;
}


.section-count {
  min-width: 27px;
  height: 27px;
  display: flex !important;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: white;
  font-size: 8px;
  font-weight: 900;
}


.preventivo {
  border-bottom: 2px solid var(--sigta-texto-suave);
  background: var(--sigta-azul-tenue);
  color: var(--sigta-azul);
}


.correctivo {
  border-bottom: 2px solid var(--sigta-mostaza);
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-mostaza);
}


/* =========================================================
   KANBAN
========================================================= */

.kanban-scroll {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 10px 12px 14px;
}


.kanban-scroll::-webkit-scrollbar {
  height: 11px;
}


.kanban-scroll::-webkit-scrollbar-track {
  background: var(--sigta-borde);
  border-radius: 10px;
}


.kanban-scroll::-webkit-scrollbar-thumb {
  background: var(--sigta-texto-suave);
  border-radius: 10px;
}


.kanban {
  width: max-content;
  min-width: max-content;
  display: flex;
  gap: 10px;
}


.column {
  width: 220px;
  min-width: 220px;
  flex-shrink: 0;
}


.column-header {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 7px 7px 0 0;
  background: var(--sigta-azul-texto-claro);
}


.column-header strong {
  display: block;
  color: var(--sigta-azul);
  font-size: 9px;
}


.column-header small {
  display: block;
  margin-top: 3px;
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.column-header > span {
  width: 23px;
  height: 23px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--sigta-azul);
  color: white;
  font-size: 8px;
  font-weight: 900;
}


.column-body {
  min-height: 380px;
  padding: 8px;
  border-radius: 0 0 7px 7px;
  background: var(--sigta-azul-tenue);
}


/* =========================================================
   CARD
========================================================= */

.request-card {
  margin-bottom: 8px;
  padding: 10px;
  border-left: 3px solid var(--sigta-texto-suave);
  border-radius: 7px;
  background: white;
  box-shadow: 0 2px 7px rgba(0,0,0,.06);
  cursor: pointer;
}


.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
  color: var(--sigta-azul);
  font-size: 8px;
}


.type-badge {
  padding: 3px 5px;
  border-radius: 4px;
  font-size: 6px;
  font-weight: 800;
}


.type-badge.preventive {
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
}


.type-badge.corrective {
  background: var(--sigta-mostaza-suave);
  color: var(--sigta-mostaza);
}


.request-card h3 {
  margin: 8px 0;
  color: var(--sigta-azul);
  font-size: 10px;
  line-height: 1.4;
}


.card-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}


.card-info span,
.card-footer span {
  display: block;
  color: var(--sigta-texto-suave);
  font-size: 6px;
}


.card-info strong,
.card-footer strong {
  display: block;
  margin-top: 2px;
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 7px;
  margin-top: 9px;
  padding-top: 8px;
  border-top: 1px solid var(--sigta-azul-tenue);
}


.card-footer button {
  flex-shrink: 0;
  padding: 5px 7px;
  border: none;
  border-radius: 5px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-azul);
  font-size: 7px;
  cursor: pointer;
}


/* =========================================================
   MODAL
========================================================= */

.overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  background: rgba(5,31,53,.68);
}


.modal {
  width: 900px;
  max-width: 100%;
  max-height: 94vh;
  overflow-y: auto;
  border-top: 4px solid var(--sigta-mostaza);
  border-radius: 11px;
  background: white;
  box-shadow: 0 20px 60px rgba(0,0,0,.28);
}


.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 20px 22px;
  border-bottom: 1px solid var(--sigta-borde);
}


.modal-code {
  color: var(--sigta-azul);
  font-size: 8px;
  font-weight: 900;
}


.modal-header h2 {
  margin: 5px 0 0;
  color: var(--sigta-texto);
  font-size: 19px;
}


.modal-header p {
  margin: 4px 0 0;
  color: var(--sigta-texto-suave);
  font-size: 8px;
}


.close-button {
  border: none;
  background: transparent;
  color: var(--sigta-texto-suave);
  font-size: 25px;
  cursor: pointer;
}


/* =========================================================
   STATUS
========================================================= */

.status-grid {
  display: grid;
  grid-template-columns: repeat(4,1fr);
  gap: 8px;
  padding: 13px 22px;
  background: var(--sigta-azul-tenue);
}


.status-grid article {
  padding: 8px;
  border-radius: 6px;
  background: white;
}


.status-grid span,
.status-grid strong {
  display: block;
}


.status-grid span {
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.status-grid strong {
  margin-top: 4px;
  color: var(--sigta-azul);
  font-size: 9px;
}


/* =========================================================
   MODAL SECTION
========================================================= */

.modal-section {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 17px 22px;
  border-bottom: 1px solid var(--sigta-azul-tenue);
}


.section-number,
.step-circle {
  width: 25px;
  height: 25px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--sigta-azul);
  color: white;
  font-size: 8px;
  font-weight: 900;
}


.section-content {
  flex: 1;
  min-width: 0;
}


.section-content h3 {
  margin: 3px 0 11px;
  color: var(--sigta-texto);
  font-size: 11px;
}


.detail-grid {
  display: grid;
  grid-template-columns: repeat(2,1fr);
  gap: 9px;
}


.detail-grid > div {
  padding: 9px;
  border-radius: 6px;
  background: var(--sigta-azul-tenue);
}


.detail-grid .full-width {
  grid-column: 1 / -1;
}


.detail-grid span,
.detail-grid strong {
  display: block;
}


.detail-grid span {
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.detail-grid strong {
  margin-top: 4px;
  color: var(--sigta-texto-suave);
  font-size: 9px;
}


.text-box {
  padding: 10px;
  border-radius: 6px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
  font-size: 9px;
  line-height: 1.55;
}


.block-space {
  margin-bottom: 8px;
}


.text-box p {
  margin: 5px 0 0;
}


.mini-title {
  color: var(--sigta-azul);
  font-size: 8px;
}


/* =========================================================
   EVIDENCIA
========================================================= */

.evidence-box {
  padding: 11px;
  border: 1px dashed var(--sigta-texto-suave);
  border-radius: 7px;
  background: var(--sigta-azul-tenue);
}


.evidence-box p {
  margin: 0 0 8px;
  color: var(--sigta-texto-suave);
  font-size: 8px;
}


.evidence-box a,
.file-link {
  color: var(--sigta-azul);
  font-size: 8px;
  font-weight: 800;
  text-decoration: none;
}


.empty-evidence {
  padding: 10px;
  border-radius: 6px;
  background: var(--sigta-azul-tenue);
  color: var(--sigta-texto-suave);
  font-size: 8px;
}


/* =========================================================
   WORKFLOW
========================================================= */

.workflow-section {
  padding: 19px 22px;
  background: var(--sigta-azul-tenue);
}


.action-card {
  margin-top: 9px;
  padding: 15px;
  border: 1px solid var(--sigta-azul-texto-claro);
  border-radius: 8px;
  background: white;
}


.action-heading {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}


.action-heading h3 {
  margin: 2px 0 3px;
  color: var(--sigta-texto);
  font-size: 11px;
}


.action-heading p {
  margin: 0;
  color: var(--sigta-texto-suave);
  font-size: 8px;
  line-height: 1.45;
}


/* =========================================================
   FIELD
========================================================= */

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 12px;
}


.field label {
  color: var(--sigta-azul);
  font-size: 8px;
  font-weight: 800;
}


.field input,
.field select,
.field textarea {
  width: 100%;
  padding: 9px 10px;
  border: 1px solid var(--sigta-borde);
  border-radius: 6px;
  background: white;
  color: var(--sigta-azul);
  font-family: inherit;
  font-size: 9px;
  outline: none;
}


.field textarea {
  min-height: 80px;
  resize: vertical;
}


.field small {
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.product-form {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 9px;
  margin-top: 6px;
}


.product-form .full-width {
  grid-column: 1 / -1;
}


/* =========================================================
   DECISION
========================================================= */

.decision-grid {
  display: grid;
  grid-template-columns: repeat(2,1fr);
  gap: 9px;
  margin-top: 13px;
}


.decision-grid label {
  min-height: 75px;
  padding: 11px;
  border: 1px solid var(--sigta-borde);
  border-radius: 7px;
  cursor: pointer;
}


.decision-grid label.selected {
  border-color: var(--sigta-azul);
  background: var(--sigta-azul-tenue);
}


.decision-grid strong,
.decision-grid span {
  display: block;
  margin-left: 22px;
}


.decision-grid strong {
  margin-top: -17px;
  color: var(--sigta-azul);
  font-size: 9px;
}


.decision-grid span {
  margin-top: 4px;
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.product-summary {
  margin-top: 12px;
  padding: 11px;
  border-radius: 7px;
  background: var(--sigta-azul-tenue);
}


.product-summary span,
.product-summary strong,
.product-summary small {
  display: block;
}


.product-summary span {
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


.product-summary strong {
  margin-top: 4px;
  color: var(--sigta-azul);
  font-size: 11px;
}


.product-summary small {
  margin-top: 3px;
  color: var(--sigta-texto-suave);
  font-size: 7px;
}


/* =========================================================
   BUTTON
========================================================= */

.primary-action {
  min-height: 38px;
  margin-top: 14px;
  padding: 0 14px;
  border: none;
  border-radius: 6px;
  background: var(--sigta-azul);
  color: white;
  font-size: 8px;
  font-weight: 800;
  cursor: pointer;
}


.primary-action:disabled {
  opacity: .5;
  cursor: not-allowed;
}


.purchase-card {
  border-left: 4px solid var(--sigta-mostaza);
}


/* =========================================================
   COMPLETE
========================================================= */

.complete-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 14px;
  border: 1px solid var(--sigta-exito);
  border-radius: 8px;
  background: var(--sigta-exito-fondo);
}


.complete-icon {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--sigta-exito);
  color: white;
  font-weight: 900;
}


.complete-card h3 {
  margin: 0;
  color: var(--sigta-exito);
  font-size: 10px;
}


.complete-card p {
  margin: 4px 0 0;
  color: var(--sigta-exito);
  font-size: 8px;
}


.cancelled-card {
  margin-top: 10px;
  padding: 13px;
  border-radius: 7px;
  background: var(--sigta-error-fondo);
  color: var(--sigta-error);
  font-size: 8px;
}


/* =========================================================
   FOOTER
========================================================= */

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: 14px 22px;
  border-top: 1px solid var(--sigta-azul-tenue);
}


.secondary-button {
  min-height: 35px;
  padding: 0 13px;
  border: 1px solid var(--sigta-borde);
  border-radius: 6px;
  background: white;
  color: var(--sigta-texto-suave);
  font-size: 8px;
  font-weight: 700;
  cursor: pointer;
}


.loading,
.empty-column {
  padding: 28px 8px;
  color: var(--sigta-texto-suave);
  text-align: center;
  font-size: 8px;
}


/* =========================================================
   RESPONSIVE
========================================================= */

@media (max-width: 1000px) {

  .stats {
    grid-template-columns: repeat(2,1fr);
  }


  .flow-summary {
    align-items: flex-start;
    flex-direction: column;
  }


  .flow-steps {
    justify-content: flex-start;
  }


  .status-grid {
    grid-template-columns: repeat(2,1fr);
  }
}


@media (max-width: 760px) {

  .layout {
    display: block;
  }


  .main {
    padding: 16px;
  }


  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }


  .stats,
  .status-grid,
  .detail-grid,
  .decision-grid,
  .product-form {
    grid-template-columns: 1fr;
  }


  .detail-grid .full-width,
  .product-form .full-width {
    grid-column: auto;
  }
}

</style>