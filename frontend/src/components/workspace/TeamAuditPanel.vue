<script setup lang="ts">
import type { AuditLogEntry, TeamSummary } from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

defineProps<{
  teams: TeamSummary[]
  auditLogs: AuditLogEntry[]
}>()
</script>

<template>
  <aside id="teams" class="grid gap-3.5 scroll-mt-24 max-md:scroll-mt-32" aria-label="团队协作与审计">
    <NCard class="min-w-0 overflow-hidden" size="small" title="团队协作">
      <NList>
        <NListItem v-for="team in teams" :key="team.id">
          <NThing :title="team.name">
            <template #description>{{ team.role }} · {{ team.member_count }} 人</template>
            <template #header-extra>
              <NBadge :value="team.unread_count" type="info" />
            </template>
          </NThing>
        </NListItem>
      </NList>
    </NCard>

    <NCard v-if="auth.canAccessPermissionAudit" id="audit" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" size="small">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <span>审计日志</span>
          <RouterLink class="text-primary text-12px font-700 no-underline" to="/permission-audit">查看全部</RouterLink>
        </div>
      </template>
      <NList>
        <NListItem v-for="log in auditLogs" :key="log.id">
          <NThing :title="log.actor">
            <template #description>{{ log.action }} · {{ log.resource_name }}</template>
          </NThing>
        </NListItem>
      </NList>
    </NCard>
  </aside>
</template>
