import { computed, type Component, type Ref } from 'vue'
import { Bot, Database, FileText, ShieldCheck, Users } from '@lucide/vue'

import type { WorkspaceApiState } from '@/stores/workspace'

export interface WorkspaceNavItem {
  active?: boolean
  href?: string
  icon: Component
  label: string
  to?: string
}

export function useWorkspaceNavigation(apiState: Ref<WorkspaceApiState>, activeKey = 'workspace') {
  const navItems: WorkspaceNavItem[] = [
    { to: '/', label: '主页', icon: FileText, active: activeKey === 'workspace' },
    { to: '/rag', label: 'RAG 问答', icon: Database, active: activeKey === 'rag' },
    { to: '/workflow', label: '工具流', icon: Bot, active: activeKey === 'workflow' },
    { to: '/team-chat', label: '团队空间', icon: Users, active: activeKey === 'team-chat' },
    { to: '/permission-audit', label: '权限审计', icon: ShieldCheck, active: activeKey === 'permission-audit' },
  ]

  const apiStateLabel = computed(() => {
    if (apiState.value === 'live') {
      return '后端 API'
    }

    if (apiState.value === 'fallback') {
      return '演示数据（API 不可用）'
    }

    return '演示数据'
  })

  const apiStateType = computed<'success' | 'warning' | 'info'>(() => {
    if (apiState.value === 'live') {
      return 'success'
    }

    if (apiState.value === 'fallback') {
      return 'warning'
    }

    return 'info'
  })

  return {
    apiStateLabel,
    apiStateType,
    navItems,
  }
}
