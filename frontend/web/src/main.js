import '@app/styles/main.css'

import { createApp } from 'vue'
import App from '@app/App.vue'
import router from '@app/router.js'

const app = createApp(App)

app.use(router)

app.mount('#app')
