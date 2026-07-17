import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory } from 'vue-router'

import { saveWorkspaceSession } from '@/auth'
import { useAuthStore } from '@/stores/auth'
import { createAppRouter } from '../index'

describe('auth router guard', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('redirects protected workspace routes to login when no session exists', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/files')
  })

  it('allows workspace access after restoring a local auth session', async () => {
    saveWorkspaceSession({
      accessToken: 'stored-token',
      displayName: '演示用户',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const auth = useAuthStore()
    const verify = vi.spyOn(auth, 'verifySession').mockResolvedValue(true)
    const router = createAppRouter(createMemoryHistory())

    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('files')
    expect(verify).toHaveBeenCalledOnce()
  })

  it('rejects an unverified stored token and preserves the protected target', async () => {
    saveWorkspaceSession({
      accessToken: 'invalid-token', displayName: '无效用户', refreshToken: 'invalid-refresh', userId: '7',
    })
    const auth = useAuthStore()
    vi.spyOn(auth, 'verifySession').mockResolvedValue(false)
    const router = createAppRouter(createMemoryHistory())

    await router.push('/workflow')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/workflow')
  })

  it('protects the profile route with the same auth guard', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/profile')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/profile')
  })
})
