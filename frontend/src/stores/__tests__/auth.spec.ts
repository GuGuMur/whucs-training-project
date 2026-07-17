import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { createAuthorizationHeader, loadStoredWorkspaceSession } from '@/auth'
import {
  loginApiV2AuthLoginPost,
  meApiV2UsersMeGet,
  refreshApiV2AuthRefreshPost,
  registerApiV2AuthRegisterPost,
  updateMeApiV2UsersMePatch,
} from '@/client/generated'
import { useAuthStore } from '../auth'

type ErrorResponse = {
  code: string
  detail?: Record<string, unknown>
  message: string
}

vi.mock('@/client/generated', () => ({
  loginApiV2AuthLoginPost: vi.fn(),
  meApiV2UsersMeGet: vi.fn(),
  refreshApiV2AuthRefreshPost: vi.fn(),
  registerApiV2AuthRegisterPost: vi.fn(),
  updateMeApiV2UsersMePatch: vi.fn(),
}))

const loginApi = vi.mocked(loginApiV2AuthLoginPost)
const meApi = vi.mocked(meApiV2UsersMeGet)
const refreshApi = vi.mocked(refreshApiV2AuthRefreshPost)
const registerApi = vi.mocked(registerApiV2AuthRegisterPost)
const updateMeApi = vi.mocked(updateMeApiV2UsersMePatch)

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

  it('shows account lockout details from generated login errors', async () => {
    const lockedError: ErrorResponse = {
      code: 'ACCOUNT_LOCKED',
      detail: {
        failed_attempts: 5,
        locked_until: '2026-07-08T14:30:00+08:00',
        max_attempts: 5,
        retry_after_seconds: 299,
      },
      message: '账户已被临时锁定，请稍后再试',
    }

    loginApi.mockResolvedValue({
      data: undefined,
      error: lockedError as never,
    })

    const auth = useAuthStore()

    await expect(auth.loginWithPassword({ account: 'xiaoming', password: 'WrongPass!' })).rejects.toEqual(lockedError)

    expect(auth.errorMessage).toBe('账户已临时锁定，请 5 分钟后再试')
    expect(auth.isAuthenticated).toBe(false)
    expect(loadStoredWorkspaceSession()).toBeNull()
  })

  it('hydrates the current user from a stored session token', async () => {
    localStorage.setItem(
      'whu-workspace-session',
      JSON.stringify({
        accessToken: 'stored-token',
        displayName: '旧会话',
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
    expect(auth.verificationState).toBe('verified')
  })

  it('verifies a local session before treating it as authenticated access', async () => {
    localStorage.setItem('whu-workspace-session', JSON.stringify({
      accessToken: 'unverified-token', displayName: '待验证', refreshToken: 'refresh-token', userId: '3',
    }))
    meApi.mockResolvedValue({ data: undefined, error: { code: 'INVALID_TOKEN', message: 'invalid' } as never })
    const auth = useAuthStore()

    await expect(auth.verifySession()).resolves.toBe(false)

    expect(auth.verificationState).toBe('unknown')
    expect(auth.isAuthenticated).toBe(false)
  })

  it('refreshes an expired access token during protected-route verification', async () => {
    localStorage.setItem('whu-workspace-session', JSON.stringify({
      accessToken: 'expired-token', displayName: '旧用户', refreshToken: 'valid-refresh', userId: '9',
    }))
    meApi.mockResolvedValue({ data: undefined, error: { code: 'TOKEN_EXPIRED', message: 'expired' } as never })
    refreshApi.mockResolvedValue({
      data: {
        access_token: 'new-token', expires_in: 1800, refresh_token: 'new-refresh', token_type: 'bearer',
        user: { display_name: '刷新用户', email: 'refresh@example.com', id: 9, roles: ['user'], username: 'refresh' },
      },
      error: undefined,
    })
    const auth = useAuthStore()

    await expect(auth.verifySession()).resolves.toBe(true)

    expect(refreshApi).toHaveBeenCalledWith({ body: { refresh_token: 'valid-refresh' } })
    expect(auth.verificationState).toBe('verified')
    expect(auth.session?.accessToken).toBe('new-token')
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
