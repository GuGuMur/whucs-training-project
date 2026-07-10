import { computed, type Component, type Ref } from 'vue'
import { Bot, Database, FolderOpen, ShieldCheck, Users } from '@lucide/vue'

import { useAuthStore } from '@/stores/auth'
import type { WorkspaceApiState } from '@/stores/workspace'

export interface WorkspaceNavItem {
  active?: boolean
  href?: string
  icon: Component
  label: string
  to?: string
}

export function useWorkspaceNavigation(apiState: Ref<WorkspaceApiState>, activeKey = 'files') {
  const auth = useAuthStore()
  const navItems = computed<WorkspaceNavItem[]>(() => {
    const items: WorkspaceNavItem[] = [
      { to: '/files', label: '文件管理', icon: FolderOpen, active: activeKey === 'files' },
      { to: '/rag', label: 'RAG 问答', icon: Database, active: activeKey === 'rag' },
      { to: '/workflow', label: '工具流', icon: Bot, active: activeKey === 'workflow' },
      { to: '/team-chat', label: '团队空间', icon: Users, active: activeKey === 'team-chat' },
    ]

    if (auth.isAdmin) {
      items.push({ to: '/permission-audit', label: '权限审计', icon: ShieldCheck, active: activeKey === 'permission-audit' })
    }

    return items
  })

  const apiStateLabel = computed(() => {
    if (apiState.value === 'live') {
      return '后端 API'
    }

    if (apiState.value === 'fallback') {
      return '连接异常'
    }

    return '连接异常'
  })

  const apiStateType = computed<'success' | 'warning' | 'info'>(() => {
    if (apiState.value === 'live') {
      return 'success'
    }

    if (apiState.value === 'fallback') {
      return 'warning'
    }

    return 'warning'
  })

  return {
    apiStateLabel,
    apiStateType,
    navItems,
  }
}
