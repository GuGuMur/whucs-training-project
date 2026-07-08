import { defineConfig, presetWind3 } from 'unocss'

export default defineConfig({
  presets: [presetWind3()],
  theme: {
    colors: {
      canvas: '#F6F8FB',
      surface: '#FFFFFF',
      muted: '#EEF2F7',
      ink: '#172033',
      sub: '#5D6B82',
      line: '#D8E0EA',
      primary: '#246BFE',
      primarySoft: '#E8F0FF',
      success: '#1F9D55',
      warning: '#C98600',
      danger: '#D92D20',
      knowledge: '#6D5DF6',
    },
  },
  shortcuts: {
    'app-panel': 'border border-line rounded-2 bg-surface',
    'panel-title': 'm-0 text-ink text-16px font-700',
    'panel-subtitle': 'm-0 text-sub text-13px',
    'btn-primary':
      'inline-flex min-h-34px items-center justify-center border border-primary rounded-1.5 bg-primary px-3 text-white text-13px font-700',
    'btn-secondary':
      'inline-flex min-h-34px items-center justify-center border border-line rounded-1.5 bg-surface px-3 text-ink text-13px font-650',
    'status-chip-base':
      'inline-flex min-w-58px items-center justify-center border rounded-full px-2 py-0.5 text-12px font-600 leading-[1.4] whitespace-nowrap',
    'mono-chip': 'rounded-full bg-muted px-2 py-0.75 text-sub text-12px font-mono',
  },
})
