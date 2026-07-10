export interface WorkspaceAuthSession {
  accessToken?: string
  displayName: string
  refreshToken?: string
  userId: string
}

export const workspaceSessionStorageKey = 'whu-workspace-session'

export function createAuthorizationHeader(token: string) {
  return { authorization: `Bearer ${token}` }
}

export function resolveWorkspaceToken(session?: WorkspaceAuthSession) {
  return session?.accessToken
}

function canUseLocalStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function loadStoredWorkspaceSession(): WorkspaceAuthSession | null {
  if (!canUseLocalStorage()) return null
  const raw = window.localStorage.getItem(workspaceSessionStorageKey)
  if (!raw) return null
  try {
    const s = JSON.parse(raw) as Partial<WorkspaceAuthSession>
    if (!s.accessToken && !s.refreshToken) return null
    return {
      accessToken: s.accessToken,
      displayName: s.displayName ?? '未知用户',
      refreshToken: s.refreshToken,
      userId: s.userId ?? 'unknown',
    }
  } catch { return null }
}

export function saveWorkspaceSession(session: WorkspaceAuthSession) {
  if (!canUseLocalStorage()) return
  window.localStorage.setItem(workspaceSessionStorageKey, JSON.stringify(session))
}

export function clearStoredWorkspaceSession() {
  if (!canUseLocalStorage()) return
  window.localStorage.removeItem(workspaceSessionStorageKey)
}
