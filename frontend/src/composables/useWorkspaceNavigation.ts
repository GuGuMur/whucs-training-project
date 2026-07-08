import { computed, type Component, type Ref } from 'vue'
import { Bot, Database, FileText, ShieldCheck, Users } from '@lucide/vue'

import type { WorkspaceApiState } from '@/stores/workspace'

export interface WorkspaceNavItem {
  active?: boolean
  href: string
  icon: Component
  label: string
}

export function useWorkspaceNavigation(apiState: Ref<WorkspaceApiState>) {
  const navItems: WorkspaceNavItem[] = [
    { href: '#files', label: '个人文件', icon: FileText, active: true },
    { href: '#rag', label: '知识库', icon: Database },
    { href: '#automation', label: '智能体', icon: Bot },
    { href: '#teams', label: '团队空间', icon: Users },
    { href: '#audit', label: '权限审计', icon: ShieldCheck },
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
