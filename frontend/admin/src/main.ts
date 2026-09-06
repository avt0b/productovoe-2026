import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { setSessionExpiredHandler } from './api/client'
import router from './router'
import './style.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Сервер мог погасить сессию сам (смена пароля, отключение учётки) —
// в этом случае клиент уводит на экран входа, а не показывает пустые таблицы.
setSessionExpiredHandler(() => {
  useAuthStore().dropSession()
  void router.push({ name: 'login' })
})

app.mount('#app')
