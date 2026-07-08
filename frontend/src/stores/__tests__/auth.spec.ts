import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { createAuthorizationHeader, loadStoredWorkspaceSession } from '@/auth'
import {
  loginApiV1AuthLoginPost,
  meApiV1UsersMeGet,
  refreshApiV1AuthRefreshPost,
  registerApiV1AuthRegisterPost,
  updateMeApiV1UsersMePatch,
} from '@/client/generated'
import { useAuthStore } from '../auth'

vi.mock('@/client/generated', () => ({
  loginApiV1AuthLoginPost: vi.fn(),
  meApiV1UsersMeGet: vi.fn(),
  refreshApiV1AuthRefreshPost: vi.fn(),
  registerApiV1AuthRegisterPost: vi.fn(),
  updateMeApiV1UsersMePatch: vi.fn(),
}))

const loginApi = vi.mocked(loginApiV1AuthLoginPost)
const meApi = vi.mocked(meApiV1UsersMeGet)
const refreshApi = vi.mocked(refreshApiV1AuthRefreshPost)
const registerApi = vi.mocked(registerApiV1AuthRegisterPost)
const updateMeApi = vi.mocked(updateMeApiV1UsersMePatch)

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('logs in with the generated auth client and persists the session', async () => {
    loginApi.mockResolvedValue({
      data: {
        access_token: 'access-token',
        expires_in: 1800,
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        user: {
          display_name: '小明',
          email: 'xiaoming@example.com',
          id: 7,
          roles: ['user'],
          username: 'xiaoming',
        },
      },
      error: undefined,
    })

    const auth = useAuthStore()

    await auth.loginWithPassword({ account: 'xiaoming', password: 'Str0ngPass!' })

    expect(loginApi).toHaveBeenCalledWith({
      body: { account: 'xiaoming', password: 'Str0ngPass!' },
    })
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.session?.accessToken).toBe('access-token')
    expect(auth.currentUser?.username).toBe('xiaoming')
    expect(loadStoredWorkspaceSession()?.accessToken).toBe('access-token')
    expect(createAuthorizationHeader('access-token')).toEqual({ authorization: 'Bearer access-token' })
  })

  it('hydrates the current user from a stored session token', async () => {
    localStorage.setItem(
      'whu-workspace-session',
      JSON.stringify({
        accessToken: 'stored-token',
        displayName: '旧会话',
        permissionScope: '个人',
        refreshToken: 'stored-refresh-token',
        userId: '3',
      }),
    )
    meApi.mockResolvedValue({
      data: {
        user: {
          display_name: '恢复用户',
          email: 'recover@example.com',
          id: 3,
          roles: ['user'],
          username: 'recover',
        },
      },
      error: undefined,
    })

    const auth = useAuthStore()

    await auth.restoreSession()

    expect(meApi).toHaveBeenCalledWith({
      headers: { authorization: 'Bearer stored-token' },
    })
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.currentUser?.display_name).toBe('恢复用户')
  })

  it('registers a new user through the generated auth client', async () => {
    registerApi.mockResolvedValue({
      data: {
        access_token: 'new-access-token',
        expires_in: 1800,
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
        user: {
          display_name: 'new-user',
          email: 'new-user@example.com',
          id: 8,
          roles: ['user'],
          username: 'new-user',
        },
      },
      error: undefined,
    })

    const auth = useAuthStore()

    await auth.registerWithPassword({
      email: 'new-user@example.com',
      password: 'Str0ngPass!',
      username: 'new-user',
    })

    expect(registerApi).toHaveBeenCalledWith({
      body: {
        email: 'new-user@example.com',
        password: 'Str0ngPass!',
        username: 'new-user',
      },
    })
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.session?.accessToken).toBe('new-access-token')
  })

  it('refreshes a stored session through the generated auth client', async () => {
    localStorage.setItem(
      'whu-workspace-session',
      JSON.stringify({
        accessToken: 'old-access-token',
        displayName: '旧会话',
        permissionScope: '个人',
        refreshToken: 'old-refresh-token',
        userId: '9',
      }),
    )
    refreshApi.mockResolvedValue({
      data: {
        access_token: 'rotated-access-token',
        expires_in: 1800,
        refresh_token: 'rotated-refresh-token',
        token_type: 'bearer',
        user: {
          display_name: '刷新用户',
          email: 'refresh@example.com',
          id: 9,
          roles: ['user'],
          username: 'refresh',
        },
      },
      error: undefined,
    })

    const auth = useAuthStore()

    await auth.refreshSession()

    expect(refreshApi).toHaveBeenCalledWith({
      body: { refresh_token: 'old-refresh-token' },
    })
    expect(auth.session?.accessToken).toBe('rotated-access-token')
    expect(auth.session?.refreshToken).toBe('rotated-refresh-token')
    expect(auth.currentUser?.display_name).toBe('刷新用户')
    expect(loadStoredWorkspaceSession()?.accessToken).toBe('rotated-access-token')
  })

  it('updates the current user profile through the generated auth client', async () => {
    localStorage.setItem(
      'whu-workspace-session',
      JSON.stringify({
        accessToken: 'profile-access-token',
        displayName: '旧资料',
        permissionScope: '个人',
        refreshToken: 'profile-refresh-token',
        userId: '12',
      }),
    )
    updateMeApi.mockResolvedValue({
      data: {
        user: {
          display_name: '小明同学',
          email: 'xiaoming-profile@example.com',
          id: 12,
          roles: ['user'],
          username: 'xiaoming',
        },
      },
      error: undefined,
    })

    const auth = useAuthStore()
    auth.restoreLocalSession()

    await auth.updateProfile({
      display_name: '小明同学',
      email: 'xiaoming-profile@example.com',
    })

    expect(updateMeApi).toHaveBeenCalledWith({
      body: {
        display_name: '小明同学',
        email: 'xiaoming-profile@example.com',
      },
      headers: { authorization: 'Bearer profile-access-token' },
    })
    expect(auth.currentUser?.display_name).toBe('小明同学')
    expect(auth.session?.displayName).toBe('小明同学')
    expect(loadStoredWorkspaceSession()?.displayName).toBe('小明同学')
  })
})
