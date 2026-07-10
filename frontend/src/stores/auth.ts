import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import {
  clearStoredWorkspaceSession,
  createAuthorizationHeader,
  loadStoredWorkspaceSession,
  saveWorkspaceSession,
  type WorkspaceAuthSession,
} from '@/auth'
import {
  loginApiV2AuthLoginPost,
  meApiV2UsersMeGet,
  refreshApiV2AuthRefreshPost,
  registerApiV2AuthRegisterPost,
  updateMeApiV2UsersMePatch,
} from '@/client/generated'
import type { AuthResponse, UserCreate, UserPublic, UserUpdate } from '@/client/generated'

export interface LoginCredentials {
  account: string
  password: string
}

export type RegisterCredentials = UserCreate

interface WorkspaceApiError {
  code?: string
  detail?: Record<string, unknown>
  message?: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function toWorkspaceApiError(error: unknown): WorkspaceApiError | null {
  if (!isRecord(error)) return null
  return {
    code: typeof error.code === 'string' ? error.code : undefined,
    detail: isRecord(error.detail) ? error.detail : undefined,
    message: typeof error.message === 'string' ? error.message : undefined,
  }
}

function loginErrorMessage(error: unknown) {
  const apiError = toWorkspaceApiError(error)
  if (apiError?.code === 'ACCOUNT_LOCKED') {
    const retryAfterSeconds = apiError.detail?.retry_after_seconds
    if (typeof retryAfterSeconds === 'number' && retryAfterSeconds > 0)
      return `账户已临时锁定，请 ${Math.ceil(retryAfterSeconds / 60)} 分钟后再试`
    return apiError.message ?? '账户已临时锁定，请稍后再试'
  }
  if (apiError?.code === 'INVALID_CREDENTIALS') {
    const remainingAttempts = apiError.detail?.remaining_attempts
    if (typeof remainingAttempts === 'number' && remainingAttempts > 0)
      return `账号或密码不正确，还可尝试 ${remainingAttempts} 次`
  }
  return '账号或密码不正确'
}

export const useAuthStore = defineStore('auth', () => {
  const session = shallowRef<WorkspaceAuthSession | null>(loadStoredWorkspaceSession())
  const currentUser = shallowRef<UserPublic | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')

  const isAuthenticated = computed(() => Boolean(session.value?.accessToken))
  const displayName = computed(() => currentUser.value?.display_name ?? '未登录')
  const roles = computed(() => currentUser.value?.roles ?? [])
  const isAdmin = computed(() => roles.value.includes('admin') || roles.value.includes('super_admin'))

  function applyAuthResponse(payload: AuthResponse) {
    const next: WorkspaceAuthSession = {
      accessToken: payload.access_token,
      displayName: payload.user.display_name,
      refreshToken: payload.refresh_token,
      userId: String(payload.user.id),
    }
    session.value = next
    currentUser.value = payload.user
    errorMessage.value = ''
    saveWorkspaceSession(next)
  }

  function restoreLocalSession() {
    session.value = loadStoredWorkspaceSession()
    return session.value
  }

  async function restoreSession() {
    const s = restoreLocalSession()
    if (!s?.accessToken) { currentUser.value = null; return false }
    loading.value = true
    try {
      const r = await meApiV2UsersMeGet({ headers: createAuthorizationHeader(s.accessToken) })
      if (r.error || !r.data) { logout(); return false }
      currentUser.value = r.data.user
      session.value = { ...s, displayName: r.data.user.display_name, userId: String(r.data.user.id) }
      saveWorkspaceSession(session.value)
      return true
    } finally { loading.value = false }
  }

  async function loginWithPassword(credentials: LoginCredentials) {
    loading.value = true
    try {
      const r = await loginApiV2AuthLoginPost({ body: credentials })
      if (r.error || !r.data) { errorMessage.value = loginErrorMessage(r.error); throw r.error ?? new Error(errorMessage.value) }
      applyAuthResponse(r.data)
      return r.data
    } finally { loading.value = false }
  }

  async function refreshSession() {
    const s = restoreLocalSession()
    if (!s?.refreshToken) { logout(); return false }
    loading.value = true
    try {
      const r = await refreshApiV2AuthRefreshPost({ body: { refresh_token: s.refreshToken } })
      if (r.error || !r.data) { logout(); return false }
      applyAuthResponse(r.data)
      return r.data
    } finally { loading.value = false }
  }

  async function registerWithPassword(credentials: RegisterCredentials) {
    loading.value = true
    try {
      const r = await registerApiV2AuthRegisterPost({ body: credentials })
      if (r.error || !r.data) { errorMessage.value = '注册失败，请检查用户名、邮箱和密码'; throw r.error ?? new Error(errorMessage.value) }
      applyAuthResponse(r.data)
      return r.data
    } finally { loading.value = false }
  }

  async function updateProfile(payload: UserUpdate) {
    const token = session.value?.accessToken
    if (!token) throw new Error('未登录')
    loading.value = true
    try {
      const r = await updateMeApiV2UsersMePatch({ body: payload, headers: createAuthorizationHeader(token) })
      if (r.error || !r.data) { errorMessage.value = '更新失败'; throw r.error ?? new Error(errorMessage.value) }
      currentUser.value = r.data.user
      if (session.value) { session.value = { ...session.value, displayName: r.data.user.display_name }; saveWorkspaceSession(session.value) }
      return r.data
    } finally { loading.value = false }
  }

  function logout() {
    session.value = null
    currentUser.value = null
    errorMessage.value = ''
    clearStoredWorkspaceSession()
  }

  return {
    currentUser, errorMessage, loading, session,
    displayName, isAdmin, isAuthenticated, roles,
    loginWithPassword, logout, refreshSession, registerWithPassword,
    restoreLocalSession, restoreSession, updateProfile,
  }
})
