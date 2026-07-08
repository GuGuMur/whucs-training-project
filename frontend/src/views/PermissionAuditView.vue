<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import type { DataTableColumns } from 'naive-ui'
import { NTag } from 'naive-ui'
import { Activity, AlertTriangle, ArrowLeft, FileKey2, Filter, ShieldCheck, UserCheck } from '@lucide/vue'

import type { AuditLogEntry } from '@/client/workspace'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

interface PermissionRule {
  id: string
  target: string
  scope: string
  permission: string
  inherited: boolean
  updatedAt: string
}

const workspace = useWorkspaceStore()
const { apiState, auditLogs, summary } = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'permission-audit')
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const selectedResourceType = ref('全部')
const selectedActor = ref('全部')
const keyword = ref('')

const permissionRules: PermissionRule[] = [
  { id: 'rule-team-read', target: '团队资料文件夹', scope: '课程小组成员', permission: '读写', inherited: false, updatedAt: '2026-07-08 09:10' },
  { id: 'rule-guest-readonly', target: '共享资料', scope: '访客', permission: '只读', inherited: true, updatedAt: '2026-07-08 09:22' },
  { id: 'rule-tool-execute', target: 'report_generate', scope: '组长 / 管理员', permission: '允许执行', inherited: false, updatedAt: '2026-07-08 10:05' },
]

const resourceTypeOptions = computed(() => ['全部', ...new Set(auditLogs.value.map((log) => log.resource_type))])
const actorOptions = computed(() => ['全部', ...new Set(auditLogs.value.map((log) => log.actor))])
const filteredLogs = computed(() =>
  auditLogs.value.filter((log) => {
    const matchesResource = selectedResourceType.value === '全部' || log.resource_type === selectedResourceType.value
    const matchesActor = selectedActor.value === '全部' || log.actor === selectedActor.value
    const query = keyword.value.trim().toLowerCase()
    const matchesKeyword =
      !query ||
      log.action.toLowerCase().includes(query) ||
      log.resource_name.toLowerCase().includes(query) ||
      log.actor.toLowerCase().includes(query)
    return matchesResource && matchesActor && matchesKeyword
  }),
)

const riskyLogs = computed(() => auditLogs.value.filter((log) => /delete|permission|tool\.publish|execute/.test(log.action)))
const resourceBreakdown = computed(() => {
  const counts = new Map<string, number>()
  for (const log of auditLogs.value) {
    counts.set(log.resource_type, (counts.get(log.resource_type) ?? 0) + 1)
  }
  return [...counts.entries()].map(([label, count]) => ({ label, count }))
})

const columns = computed<DataTableColumns<AuditLogEntry>>(() => [
  {
    title: '操作者',
    key: 'actor',
    width: 120,
    render: (row) => h('strong', { class: 'text-ink text-13px' }, row.actor),
  },
  {
    title: '动作',
    key: 'action',
    minWidth: 170,
    render: (row) => h(NTag, { size: 'small', round: true, bordered: false, type: actionTone(row.action) }, { default: () => row.action }),
  },
  { title: '资源类型', key: 'resource_type', width: 120 },
  { title: '资源名称', key: 'resource_name', minWidth: 190 },
  {
    title: '时间',
    key: 'created_at',
    width: 170,
    render: (row) => formatTime(row.created_at),
  },
])

onMounted(() => {
  void workspace.loadWorkspace()
})

function actionTone(action: string) {
  if (/delete|failed|deny/.test(action)) return 'error'
  if (/permission|tool\.publish|execute/.test(action)) return 'warning'
  if (/login|register|refresh/.test(action)) return 'info'
  return 'default'
}

function formatTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <component
    :is="workspaceLayout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
  >
    <section class="audit-page">
      <div class="audit-heading">
        <div>
          <p class="eyebrow">权限与审计 · RBAC / 资源边界 / 操作追踪</p>
          <h2>权限审计中心</h2>
          <span>集中查看团队资源访问、工具执行、权限变更和关键操作记录。</span>
        </div>
        <RouterLink class="btn-secondary no-underline" to="/">
          <NIcon aria-hidden="true" class="mr-1.5"><ArrowLeft /></NIcon>
          返回工作台
        </RouterLink>
      </div>

      <div class="summary-grid">
        <NCard size="small" :bordered="false" class="metric-card">
          <div class="metric-icon is-primary"><NIcon><Activity /></NIcon></div>
          <span>审计事件</span>
          <strong>{{ auditLogs.length }}</strong>
        </NCard>
        <NCard size="small" :bordered="false" class="metric-card">
          <div class="metric-icon is-warning"><NIcon><AlertTriangle /></NIcon></div>
          <span>需关注事件</span>
          <strong>{{ riskyLogs.length }}</strong>
        </NCard>
        <NCard size="small" :bordered="false" class="metric-card">
          <div class="metric-icon is-success"><NIcon><ShieldCheck /></NIcon></div>
          <span>权限规则</span>
          <strong>{{ permissionRules.length }}</strong>
        </NCard>
        <NCard size="small" :bordered="false" class="metric-card">
          <div class="metric-icon is-info"><NIcon><UserCheck /></NIcon></div>
          <span>操作者</span>
          <strong>{{ actorOptions.length - 1 }}</strong>
        </NCard>
      </div>

      <div class="audit-shell">
        <main class="audit-main">
          <NCard size="small" :bordered="false" class="audit-card" content-class="!p-0">
            <template #header>
              <div class="card-heading">
                <div>
                  <h3>审计日志</h3>
                  <p>按操作者、资源类型和关键字筛选关键操作。</p>
                </div>
                <NTag type="info" round>{{ filteredLogs.length }} 条</NTag>
              </div>
            </template>

            <div class="filter-bar">
              <NInput v-model:value="keyword" clearable placeholder="搜索动作、资源或操作者">
                <template #prefix><NIcon><Filter /></NIcon></template>
              </NInput>
              <NSelect v-model:value="selectedResourceType" :options="resourceTypeOptions.map((label) => ({ label, value: label }))" />
              <NSelect v-model:value="selectedActor" :options="actorOptions.map((label) => ({ label, value: label }))" />
            </div>

            <NDataTable
              class="max-md:hidden"
              :columns="columns"
              :data="filteredLogs"
              :pagination="false"
              :bordered="false"
              :row-key="(row: AuditLogEntry) => row.id"
              :scroll-x="760"
              size="small"
            />

            <NList class="hidden max-md:block" :show-divider="false">
              <NListItem v-for="log in filteredLogs" :key="log.id" class="!px-4 !py-3">
                <div class="mobile-log">
                  <strong>{{ log.actor }}</strong>
                  <NTag size="small" round :bordered="false" :type="actionTone(log.action)">{{ log.action }}</NTag>
                  <span>{{ log.resource_type }} · {{ log.resource_name }}</span>
                  <small>{{ formatTime(log.created_at) }}</small>
                </div>
              </NListItem>
            </NList>
          </NCard>
        </main>

        <aside class="audit-side">
          <NCard size="small" title="资源类型分布" :bordered="false" class="audit-card">
            <div class="breakdown-list">
              <div v-for="item in resourceBreakdown" :key="item.label" class="breakdown-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
              </div>
            </div>
          </NCard>

          <NCard size="small" title="权限规则快照" :bordered="false" class="audit-card">
            <div class="rule-list">
              <article v-for="rule in permissionRules" :key="rule.id" class="rule-row">
                <div class="rule-icon"><NIcon><FileKey2 /></NIcon></div>
                <div>
                  <strong>{{ rule.target }}</strong>
                  <span>{{ rule.scope }} · {{ rule.permission }}</span>
                  <small>{{ rule.inherited ? '继承父级权限' : '单独配置' }} · {{ rule.updatedAt }}</small>
                </div>
              </article>
            </div>
          </NCard>
        </aside>
      </div>
    </section>
  </component>
</template>

<style scoped>
.audit-page { display: grid; gap: 14px; min-width: 0; }
.audit-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.audit-heading .eyebrow { margin: 0 0 4px; color: #64748b; font-size: 13px; }
.audit-heading h2 { margin: 0; color: #172033; font-size: 30px; font-weight: 800; line-height: 1.2; }
.audit-heading span { display: block; margin-top: 6px; color: #64748b; font-size: 14px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.metric-card { border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04); }
.metric-card :deep(.n-card__content) { display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: 10px; align-items: center; }
.metric-card span { color: #64748b; font-size: 12px; }
.metric-card strong { display: block; color: #172033; font-size: 24px; font-weight: 800; line-height: 1.1; }
.metric-icon { display: grid; width: 40px; height: 40px; grid-row: span 2; place-items: center; border-radius: 8px; font-size: 20px; }
.metric-icon.is-primary { color: #246bfe; background: rgba(36, 107, 254, 0.1); }
.metric-icon.is-warning { color: #d97706; background: rgba(217, 119, 6, 0.1); }
.metric-icon.is-success { color: #16a34a; background: rgba(22, 163, 74, 0.1); }
.metric-icon.is-info { color: #0891b2; background: rgba(8, 145, 178, 0.1); }
.audit-shell { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 14px; align-items: start; }
.audit-main, .audit-side { min-width: 0; }
.audit-side { display: grid; gap: 14px; }
.audit-card { overflow: hidden; border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04); }
.card-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.card-heading h3 { margin: 0; color: #172033; font-size: 17px; font-weight: 800; }
.card-heading p { margin: 4px 0 0; color: #64748b; font-size: 12px; }
.filter-bar { display: grid; grid-template-columns: minmax(260px, 1fr) 180px 180px; gap: 10px; padding: 12px; border-bottom: 1px solid #e8eef6; background: #f8fafc; }
.breakdown-list, .rule-list { display: grid; gap: 10px; }
.breakdown-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 9px 10px; background: #f8fafc; border: 1px solid #e8eef6; border-radius: 8px; }
.breakdown-row span { color: #475569; font-size: 13px; }
.breakdown-row strong { color: #172033; }
.rule-row { display: grid; grid-template-columns: 36px minmax(0, 1fr); gap: 10px; align-items: start; }
.rule-icon { display: grid; width: 34px; height: 34px; place-items: center; color: #246bfe; background: rgba(36, 107, 254, 0.1); border-radius: 8px; }
.rule-row strong, .rule-row span, .rule-row small { display: block; }
.rule-row strong { color: #172033; font-size: 13px; }
.rule-row span { margin-top: 2px; color: #475569; font-size: 12px; }
.rule-row small { margin-top: 3px; color: #64748b; font-size: 12px; }
.mobile-log { display: grid; gap: 6px; }
.mobile-log strong { color: #172033; }
.mobile-log span, .mobile-log small { color: #64748b; font-size: 12px; }
@media (max-width: 1100px) { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .audit-shell { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .audit-heading { align-items: flex-start; flex-direction: column; } .summary-grid, .filter-bar { grid-template-columns: 1fr; } }
</style>
