<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DataTableColumns } from 'naive-ui'

import { storeToRefs } from 'pinia'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'

interface AuditLogEntry {
  id: string; actor: string; action: string; resource_type: string; resource_name: string; created_at: string
}

const auth = useAuthStore()
const workspace = useWorkspaceStore()
const { apiState, auditLogs, summary } = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'permission-audit')

const selectedResourceType = ref('全部')
const selectedActor = ref('全部')
const keyword = ref('')

const visibleAuditLogs = computed(() => auditLogs.value)

const resourceTypeOptions = computed(() => ['全部', ...new Set(visibleAuditLogs.value.map((l) => l.resource_type))])
const actorOptions = computed(() => ['全部', ...new Set(visibleAuditLogs.value.map((l) => l.actor))])
const filteredLogs = computed(() =>
  visibleAuditLogs.value.filter((log) => {
    const mr = selectedResourceType.value === '全部' || log.resource_type === selectedResourceType.value
    const ma = selectedActor.value === '全部' || log.actor === selectedActor.value
    const q = keyword.value.trim().toLowerCase()
    return mr && ma && (!q || log.action.toLowerCase().includes(q) || log.resource_name.toLowerCase().includes(q))
  }),
)

const columns: DataTableColumns<AuditLogEntry> = [
  { title: '操作者', key: 'actor', width: 120 },
  { title: '操作', key: 'action', width: 200 },
  { title: '资源类型', key: 'resource_type', width: 120 },
  { title: '资源名称', key: 'resource_name' },
  { title: '时间', key: 'created_at', width: 180 },
]
</script>

<template>
  <component :is="isMobileLayout ? MobileWorkspaceLayout : DesktopWorkspaceLayout" :api-state-label="apiStateLabel" :api-state-type="apiStateType" :nav-items="navItems" :unread-notifications="summary.unread_notifications" page-title="权限审计">
    <div class="grid gap-4">
      <div class="flex items-center justify-between">
        <h2 class="m-0 text-ink text-30px font-800">权限审计</h2>
        <NTag v-if="auth.isAdmin" type="success" round>管理员可见</NTag>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <NSelect v-model:value="selectedResourceType" :options="resourceTypeOptions.map((o) => ({ label: o, value: o }))" placeholder="资源类型" style="width:160px" />
        <NSelect v-model:value="selectedActor" :options="actorOptions.map((o) => ({ label: o, value: o }))" placeholder="操作者" style="width:160px" />
        <NInput v-model:value="keyword" placeholder="搜索审计日志" clearable style="width:240px" />
      </div>

      <NCard size="small" title="审计日志">
        <NDataTable :columns="columns" :data="filteredLogs" size="small" :row-key="(row: AuditLogEntry) => row.id" />
        <template #footer>
          <span class="text-sub text-13px">共 {{ filteredLogs.length }} 条记录</span>
        </template>
      </NCard>
    </div>
  </component>
</template>
