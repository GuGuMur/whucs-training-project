import { beforeEach, describe, expect, it } from 'vitest'
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
    expect(router.currentRoute.value.query.redirect).toBe('/')
  })

  it('allows workspace access after restoring a local auth session', async () => {
    saveWorkspaceSession({
      accessToken: 'stored-token',
      displayName: '演示用户',
      permissionScope: '个人',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    const auth = useAuthStore()
    auth.restoreLocalSession()
    const router = createAppRouter(createMemoryHistory())

    await router.push('/')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('workspace')
  })

  it('protects the profile route with the same auth guard', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/profile')
    await router.isReady()

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/profile')
  })
})
