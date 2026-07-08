import { createPinia } from 'pinia'
import type { App } from 'vue'

import router from '@/router'
import { installNaiveUi } from './naive'

export function installAppPlugins(app: App) {
  app.use(createPinia())
  app.use(router)
  installNaiveUi(app)
}
