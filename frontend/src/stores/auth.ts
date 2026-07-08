import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import {
  clearStoredWorkspaceSession,
  createAuthorizationHeader,
  normalizeWorkspaceAccessRole,
  loadStoredWorkspaceSession,
  saveWorkspaceSession,
  type WorkspaceAccessRole,
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
  accessRole?: WorkspaceAccessRole
  account: string
  password: string
}

export type RegisterCredentials = UserCreate & { accessRole?: WorkspaceAccessRole }

export const accessRoleLabels: Record<WorkspaceAccessRole, string> = {
  super_admin: '超级管理员',
  admin: '管理员',
  user: '普通用户',
  readonly: '\u6e38\u5ba2\u767b\u9646',
}

export const useAuthStore = defineStore('auth', () => {
  const session = shallowRef<WorkspaceAuthSession | null>(loadStoredWorkspaceSession())
  const currentUser = shallowRef<UserPublic | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')

  const isAuthenticated = computed(() => Boolean(session.value?.accessToken))
  const displayName = computed(() => currentUser.value?.display_name ?? session.value?.displayName ?? '未登录')
  const roles = computed(() => currentUser.value?.roles ?? [])
  const selectedAccessRole = computed(() => session.value?.accessRole ?? inferAccessRole(currentUser.value?.roles ?? []))
  const selectedAccessRoleLabel = computed(() => accessRoleLabels[selectedAccessRole.value])

  function inferAccessRole(roles: string[]): WorkspaceAccessRole {
    if (roles.includes('super_admin')) return 'super_admin'
    if (roles.includes('admin')) return 'admin'
    if (roles.includes('readonly') || roles.includes('guest')) return 'readonly'
    return 'user'
  }

  function scopeForAccessRole(accessRole: WorkspaceAccessRole) {
    if (accessRole === 'super_admin' || accessRole === 'admin') return '系统'
    if (accessRole === 'user') return '团队'
    return '个人'
  }

  function applyAuthResponse(payload: AuthResponse, requestedAccessRole?: WorkspaceAccessRole) {
    const accessRole = normalizeWorkspaceAccessRole(requestedAccessRole ?? inferAccessRole(payload.user.roles))
    const nextSession: WorkspaceAuthSession = {
      accessRole,
      accessToken: payload.access_token,
      displayName: payload.user.display_name,
      permissionScope: scopeForAccessRole(accessRole),
      refreshToken: payload.refresh_token,
      userId: String(payload.user.id),
    }

    session.value = nextSession
    currentUser.value = payload.user
    errorMessage.value = ''
    saveWorkspaceSession(nextSession)
  }

  function applyGuestSession() {
    const guestUser: UserPublic = {
      display_name: '游客',
      email: 'guest@example.com',
      id: 0,
      roles: ['guest'],
      username: 'guest',
    }
    const nextSession: WorkspaceAuthSession = {
      accessRole: 'readonly',
      accessToken: 'guest-demo-token',
      displayName: '游客',
      permissionScope: '个人',
      userId: 'guest',
    }

    session.value = nextSession
    currentUser.value = guestUser
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

    if (storedSession.accessRole === 'readonly' && storedSession.userId === 'guest') {
      currentUser.value = {
        display_name: '游客',
        email: 'guest@example.com',
        id: 0,
        roles: ['guest'],
        username: 'guest',
      }
      return true
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

      const accessRole = normalizeWorkspaceAccessRole(storedSession.accessRole)
      currentUser.value = response.data.user
      session.value = {
        ...storedSession,
        accessRole,
        displayName: response.data.user.display_name,
        permissionScope: scopeForAccessRole(accessRole),
        userId: String(response.data.user.id),
      }
      saveWorkspaceSession(session.value)
      return true
    } finally {
      loading.value = false
    }
  }

  async function loginWithPassword(credentials: LoginCredentials) {
    const { accessRole, ...loginPayload } = credentials
    loading.value = true
    try {
      const response = await loginApiV1AuthLoginPost({
        body: loginPayload,
      })

      if (response.error || !response.data) {
        errorMessage.value = '账号或密码不正确'
        throw response.error ?? new Error(errorMessage.value)
      }

      applyAuthResponse(response.data, accessRole)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function loginAsGuest() {
    loading.value = true
    try {
      applyGuestSession()
      return true
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

      applyAuthResponse(response.data, normalizeWorkspaceAccessRole(storedSession.accessRole))
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function registerWithPassword(credentials: RegisterCredentials) {
    const { accessRole, ...registerPayload } = credentials
    loading.value = true
    try {
      const response = await registerApiV1AuthRegisterPost({
        body: registerPayload,
      })

      if (response.error || !response.data) {
        errorMessage.value = '注册失败，请检查用户名、邮箱和密码'
        throw response.error ?? new Error(errorMessage.value)
      }

      applyAuthResponse(response.data, accessRole)
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

      const accessRole = normalizeWorkspaceAccessRole(storedSession.accessRole)
      currentUser.value = response.data.user
      session.value = {
        ...storedSession,
        accessRole,
        displayName: response.data.user.display_name,
        permissionScope: scopeForAccessRole(accessRole),
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
    loginAsGuest,
    loginWithPassword,
    logout,
    refreshSession,
    registerWithPassword,
    restoreLocalSession,
    restoreSession,
    roles,
    selectedAccessRole,
    selectedAccessRoleLabel,
    session,
    updateProfile,
  }
})
