export type WorkspacePermissionScope = '个人' | '团队' | '系统'

export interface WorkspaceAuthSession {
  accessToken?: string
  displayName: string
  permissionScope: WorkspacePermissionScope
  refreshToken?: string
  userId: string
}

export const workspaceSessionStorageKey = 'whu-workspace-session'

export const demoWorkspaceAuthSession: WorkspaceAuthSession = {
  displayName: '演示用户',
  permissionScope: '个人',
  userId: 'demo-user',
}

export function createAuthorizationHeader(token: string) {
  return { authorization: `Bearer ${token}` }
}

export function resolveWorkspaceToken(session: WorkspaceAuthSession = demoWorkspaceAuthSession) {
  return session.accessToken
}

function canUseLocalStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function loadStoredWorkspaceSession(): WorkspaceAuthSession | null {
  if (!canUseLocalStorage()) {
    return null
  }

  const rawSession = window.localStorage.getItem(workspaceSessionStorageKey)
  if (!rawSession) {
    return null
  }

  try {
    const session = JSON.parse(rawSession) as Partial<WorkspaceAuthSession>
    if (!session.accessToken || !session.userId || !session.displayName) {
      return null
    }

    return {
      accessToken: session.accessToken,
      displayName: session.displayName,
      permissionScope: session.permissionScope ?? '个人',
      refreshToken: session.refreshToken,
      userId: session.userId,
    }
  } catch {
    return null
  }
}

export function saveWorkspaceSession(session: WorkspaceAuthSession) {
  if (canUseLocalStorage()) {
    window.localStorage.setItem(workspaceSessionStorageKey, JSON.stringify(session))
  }
}

export function clearStoredWorkspaceSession() {
  if (canUseLocalStorage()) {
    window.localStorage.removeItem(workspaceSessionStorageKey)
  }
}
