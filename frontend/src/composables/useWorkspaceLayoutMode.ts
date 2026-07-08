import { onMounted, onUnmounted, shallowRef } from 'vue'

const mobileWorkspaceQuery = '(max-width: 767px)'

export function useWorkspaceLayoutMode() {
  const isMobileLayout = shallowRef(false)
  let mediaQuery: MediaQueryList | undefined

  function handleLayoutChange(event: MediaQueryListEvent) {
    isMobileLayout.value = event.matches
  }

  onMounted(() => {
    if (!window.matchMedia) {
      return
    }

    mediaQuery = window.matchMedia(mobileWorkspaceQuery)
    isMobileLayout.value = mediaQuery.matches
    mediaQuery.addEventListener('change', handleLayoutChange)
  })

  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', handleLayoutChange)
  })

  return { isMobileLayout }
}
