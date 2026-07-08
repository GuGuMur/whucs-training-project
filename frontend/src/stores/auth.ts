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
  loginApiV1AuthLoginPost,
  meApiV1UsersMeGet,
  refreshApiV1AuthRefreshPost,
  registerApiV1AuthRegisterPost,
  updateMeApiV1UsersMePatch,
} from '@/client/generated'
import type { AuthResponse, UserCreate, UserPublic, UserUpdate } from '@/client/generated'

export interface LoginCredentials {
  account: string
  password: string
}

export type RegisterCredentials = UserCreate

export const useAuthStore = defineStore('auth', () => {
  const session = shallowRef<WorkspaceAuthSession | null>(loadStoredWorkspaceSession())
  const currentUser = shallowRef<UserPublic | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')

  const isAuthenticated = computed(() => Boolean(session.value?.accessToken))
  const displayName = computed(() => currentUser.value?.display_name ?? session.value?.displayName ?? '未登录')
  const roles = computed(() => currentUser.value?.roles ?? [])

  function applyAuthResponse(payload: AuthResponse) {
    const nextSession: WorkspaceAuthSession = {
      accessToken: payload.access_token,
      displayName: payload.user.display_name,
      permissionScope: payload.user.roles.includes('admin') ? '系统' : '个人',
      refreshToken: payload.refresh_token,
      userId: String(payload.user.id),
    }

    session.value = nextSession
    currentUser.value = payload.user
    errorMessage.value = ''
    saveWorkspaceSession(nextSession)
  }

  function restoreLocalSession() {
    session.value = loadStoredWorkspaceSession()
    return session.value
  }

  async function restoreSession() {
    const storedSession = restoreLocalSession()
    if (!storedSession?.accessToken) {
      currentUser.value = null
      return false
    }

    loading.value = true
    try {
      const response = await meApiV1UsersMeGet({
        headers: createAuthorizationHeader(storedSession.accessToken),
      })

      if (response.error || !response.data) {
        logout()
        return false
      }

      currentUser.value = response.data.user
      session.value = {
        ...storedSession,
        displayName: response.data.user.display_name,
        permissionScope: response.data.user.roles.includes('admin') ? '系统' : storedSession.permissionScope,
        userId: String(response.data.user.id),
      }
      saveWorkspaceSession(session.value)
      return true
    } finally {
      loading.value = false
    }
  }

  async function loginWithPassword(credentials: LoginCredentials) {
    loading.value = true
    try {
      const response = await loginApiV1AuthLoginPost({
        body: credentials,
      })

      if (response.error || !response.data) {
        errorMessage.value = '账号或密码不正确'
        throw response.error ?? new Error(errorMessage.value)
      }

      applyAuthResponse(response.data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function refreshSession() {
    const storedSession = restoreLocalSession()
    if (!storedSession?.refreshToken) {
      logout()
      return false
    }

    loading.value = true
    try {
      const response = await refreshApiV1AuthRefreshPost({
        body: { refresh_token: storedSession.refreshToken },
      })

      if (response.error || !response.data) {
        logout()
        return false
      }

      applyAuthResponse(response.data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function registerWithPassword(credentials: RegisterCredentials) {
    loading.value = true
    try {
      const response = await registerApiV1AuthRegisterPost({
        body: credentials,
      })

      if (response.error || !response.data) {
        errorMessage.value = '注册失败，请检查用户名、邮箱和密码'
        throw response.error ?? new Error(errorMessage.value)
      }

      applyAuthResponse(response.data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(payload: UserUpdate) {
    const storedSession = restoreLocalSession()
    if (!storedSession?.accessToken) {
      logout()
      return false
    }

    loading.value = true
    try {
      const response = await updateMeApiV1UsersMePatch({
        body: payload,
        headers: createAuthorizationHeader(storedSession.accessToken),
      })

      if (response.error || !response.data) {
        errorMessage.value = '资料更新失败，请检查邮箱是否已被使用'
        throw response.error ?? new Error(errorMessage.value)
      }

      currentUser.value = response.data.user
      session.value = {
        ...storedSession,
        displayName: response.data.user.display_name,
        permissionScope: response.data.user.roles.includes('admin') ? '系统' : storedSession.permissionScope,
        userId: String(response.data.user.id),
      }
      errorMessage.value = ''
      saveWorkspaceSession(session.value)
      return response.data
    } finally {
      loading.value = false
    }
  }

  function logout() {
    session.value = null
    currentUser.value = null
    errorMessage.value = ''
    clearStoredWorkspaceSession()
  }

  return {
    currentUser,
    displayName,
    errorMessage,
    isAuthenticated,
    loading,
    loginWithPassword,
    logout,
    refreshSession,
    registerWithPassword,
    restoreLocalSession,
    restoreSession,
    roles,
    session,
    updateProfile,
  }
})
