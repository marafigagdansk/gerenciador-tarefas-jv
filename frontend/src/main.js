import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { onUnauthorized } from './api'
import { useAuthStore } from './stores/auth'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// Sessão expirada/inválida: limpa estado e volta ao login
onUnauthorized(() => {
  useAuthStore().logout()
  if (router.currentRoute.value.name !== 'login') router.push({ name: 'login' })
})

app.mount('#app')
