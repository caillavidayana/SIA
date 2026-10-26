import { createApp } from 'vue'
import App from './App.vue'
import ArchivoInput from './components/ArchivoInput.vue'
import router from './router'
import { monto } from './utils/monto'
import './assets/role-theme.css'
import './assets/tema-sigta.css'
import './assets/gestion-sia.css'
import './utils/swal' // <-- INICIALIZACIÓN DE MODALES GLOBALES

const app = createApp(App)
app.directive('monto', monto)
app.component('ArchivoInput', ArchivoInput)

app.use(router)

app.mount('#app')
