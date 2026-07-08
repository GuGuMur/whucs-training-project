import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { resolveWorkspaceToken } from '@/auth'
import {
  demoWorkspaceNarrative,
  demoWorkspaceSnapshot,
  fetchWorkspaceSnapshot,
  type WorkspaceNarrative,
  type WorkspaceSnapshot,
} from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'

export type WorkspaceApiState = 'demo' | 'live' | 'fallback'

export const useWorkspaceStore = defineStore('workspace', () => {
  const snapshot = shallowRef<WorkspaceSnapshot>(demoWorkspaceSnapshot)
  const narrative = shallowRef<WorkspaceNarrative>(demoWorkspaceNarrative)
  const loading = shallowRef(false)
  const apiState = shallowRef<WorkspaceApiState>('demo')

  const files = computed(() => snapshot.value.files)
  const indexedFiles = computed(() => snapshot.value.files.filter((file) => file.parse_status === 'indexed'))
  const tools = computed(() => snapshot.value.tools)
  const workflows = computed(() => snapshot.value.workflows)
  const teams = computed(() => snapshot.value.teams)
  const auditLogs = computed(() => snapshot.value.audit_logs)
  const summary = computed(() => snapshot.value.summary)

  async function loadWorkspace(token?: string) {
    const auth = useAuthStore()
    const accessToken = token ?? auth.session?.accessToken ?? resolveWorkspaceToken()

    if (!accessToken) {
      apiState.value = 'demo'
      snapshot.value = demoWorkspaceSnapshot
      narrative.value = demoWorkspaceNarrative
      return
    }

    loading.value = true
    try {
      snapshot.value = await fetchWorkspaceSnapshot(accessToken)
      narrative.value = demoWorkspaceNarrative
      apiState.value = 'live'
    } catch {
      snapshot.value = demoWorkspaceSnapshot
      narrative.value = demoWorkspaceNarrative
      apiState.value = 'fallback'
    } finally {
      loading.value = false
    }
  }

  return {
    apiState,
    auditLogs,
    files,
    indexedFiles,
    loadWorkspace,
    loading,
    narrative,
    summary,
    teams,
    tools,
    workflows,
  }
})
