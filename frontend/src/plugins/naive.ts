import naive, { type GlobalThemeOverrides } from 'naive-ui'
import type { App } from 'vue'

export const naiveThemeOverrides: GlobalThemeOverrides = {
  common: {
    bodyColor: '#F6F8FB',
    borderColor: '#D8E0EA',
    borderRadius: '6px',
    borderRadiusSmall: '6px',
    fontFamily:
      'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
    primaryColor: '#246BFE',
    primaryColorHover: '#1D5DE8',
    primaryColorPressed: '#1749B7',
    primaryColorSuppl: '#4A86FF',
    textColorBase: '#172033',
  },
  Button: {
    borderRadiusMedium: '6px',
    borderRadiusSmall: '6px',
  },
  Card: {
    borderRadius: '8px',
    color: '#FFFFFF',
  },
  DataTable: {
    borderColor: '#D8E0EA',
    thColor: '#EEF2F7',
    tdColorHover: '#E8F0FF',
  },
  Tag: {
    borderRadius: '999px',
  },
}

export function installNaiveUi(app: App) {
  app.use(naive)
}
