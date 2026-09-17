import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './app/router'
import './style.css'

const app = createApp(App)
// Pinia раньше роутера: охранник маршрутов читает сессию из хранилища.
app.use(createPinia())
app.use(router)

// Монтируем после первой навигации — иначе на долю секунды мелькнёт
// каркас с вкладками даже у экрана входа.
void router.isReady().then(() => app.mount('#app'))
