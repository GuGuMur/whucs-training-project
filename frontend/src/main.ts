import './assets/main.css'
import 'virtual:uno.css'

import { createApp } from 'vue'

import App from './App.vue'
import { installAppPlugins } from './plugins'

const app = createApp(App)

installAppPlugins(app)

app.mount('#app')
