<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Plus, ShieldCheck, Trash2, UserPlus, Users } from '@lucide/vue'

import type {
  AuditLogEntry,
  TeamSummary,
  WorkspaceTeamCreateInput,
  WorkspaceTeamDetail,
  WorkspaceTeamInviteInput,
  WorkspaceTeamRole,
} from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const props = withDefaults(defineProps<{
  activeTeamDetail?: WorkspaceTeamDetail | null
  auditLogs: AuditLogEntry[]
  teamOperationLoading?: boolean
  teams: TeamSummary[]
}>(), {
  activeTeamDetail: null,
  teamOperationLoading: false,
})

const emit = defineEmits<{
  'create-team': [payload: WorkspaceTeamCreateInput]
  'invite-team-member': [teamId: string, payload: WorkspaceTeamInviteInput]
  'load-team-detail': [teamId: string]
  'remove-team-member': [teamId: string, memberId: string]
  'update-team-member-role': [teamId: string, memberId: string, role: WorkspaceTeamRole]
}>()

const createName = shallowRef('')
const createDescription = shallowRef('')
const inviteEmail = shallowRef('')
const inviteRole = shallowRef<WorkspaceTeamRole>('member')

const activeTeamId = computed(() => props.activeTeamDetail?.id ?? props.teams[0]?.id ?? '')
const canCreateTeam = computed(() => Boolean(createName.value.trim()))
const canInviteMember = computed(() => Boolean(activeTeamId.value && inviteEmail.value.trim()))

const inviteRoleOptions: Array<{ label: string; value: WorkspaceTeamRole }> = [
  { label: '??', value: 'member' },
  { label: '??', value: 'guest' },
  { label: '???', value: 'admin' },
]

const roleLabels: Record<WorkspaceTeamRole, string> = {
  admin: '???',
  guest: '??',
  member: '??',
  owner: '???',
}

function handleCreateTeam() {
  const name = createName.value.trim()
  if (!name) return

  const description = createDescription.value.trim()
  emit('create-team', { description: description || null, name })
  createName.value = ''
  createDescription.value = ''
}

function handleInviteMember() {
  const email = inviteEmail.value.trim()
  if (!activeTeamId.value || !email) return

  emit('invite-team-member', activeTeamId.value, { email, role: inviteRole.value })
  inviteEmail.value = ''
}

function roleLabel(role: WorkspaceTeamRole | string) {
  return roleLabels[role as WorkspaceTeamRole] ?? role
}

function statusType(role: WorkspaceTeamRole) {
  if (role === 'owner' || role === 'admin') return 'info'
  if (role === 'guest') return 'warning'
  return 'success'
}
</script>

<template>
  <aside id="teams" class="grid gap-3.5 scroll-mt-24 max-md:scroll-mt-32" aria-label="???????">
    <NCard class="min-w-0 overflow-hidden" size="small">
      <template #header>
        <div class="flex items-center gap-2">
          <NIcon aria-hidden="true"><Users /></NIcon>
          <span>????</span>
        </div>
      </template>

      <NForm :show-feedback="false" label-placement="top">
        <div class="grid gap-2">
          <NInput v-model:value="createName" clearable placeholder="????" :disabled="teamOperationLoading" />
          <NInput
            v-model:value="createDescription"
            clearable
            placeholder="????"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 3 }"
            :disabled="teamOperationLoading"
          />
          <NButton
            data-testid="submit-create-team"
            type="primary"
            :disabled="!canCreateTeam"
            :loading="teamOperationLoading"
            @click="handleCreateTeam"
          >
            <template #icon><NIcon aria-hidden="true"><Plus /></NIcon></template>
            ????
          </NButton>
        </div>
      </NForm>

      <div class="mt-4 border-t border-line pt-3">
        <NEmpty v-if="!teams.length" size="small" description="????" />
        <NList v-else :show-divider="false">
          <NListItem v-for="team in teams" :key="team.id" class="!px-0 !py-2">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <p class="m-0 truncate text-ink text-14px font-700">{{ team.name }}</p>
                  <NTag size="small" round :bordered="false" :type="team.id === activeTeamId ? 'info' : 'default'">
                    {{ roleLabel(team.role) }}
                  </NTag>
                </div>
                <p class="m-0 mt-1 line-clamp-2 text-sub text-12px leading-[1.65]">
                  {{ team.description || '???????' }} ? {{ team.member_count }} ?
                </p>
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <NBadge :value="team.unread_count" type="info" />
                <NButton
                  :data-testid="'open-team-' + team.id"
                  size="tiny"
                  secondary
                  :loading="teamOperationLoading && team.id === activeTeamId"
                  @click="emit('load-team-detail', team.id)"
                >
                  ??
                </NButton>
              </div>
            </div>
          </NListItem>
        </NList>
      </div>
    </NCard>

    <NCard class="min-w-0 overflow-hidden" size="small">
      <template #header>
        <div class="flex items-center gap-2">
          <NIcon aria-hidden="true"><ShieldCheck /></NIcon>
          <span>?????</span>
        </div>
      </template>

      <div v-if="activeTeamDetail" class="grid gap-3">
        <div class="border border-line rounded-2 bg-#F8FAFD px-3 py-2">
          <p class="m-0 text-ink text-14px font-700">{{ activeTeamDetail.name }}</p>
          <p class="m-0 mt-1 text-sub text-12px leading-[1.65]">
            {{ roleLabel(activeTeamDetail.role) }} ? ??? {{ activeTeamDetail.root_folder.name }}
          </p>
        </div>

        <div class="grid grid-cols-[minmax(0,1fr)_112px_auto] gap-2 max-md:grid-cols-1">
          <NInput v-model:value="inviteEmail" clearable placeholder="????" :disabled="teamOperationLoading" />
          <NSelect v-model:value="inviteRole" :options="inviteRoleOptions" :disabled="teamOperationLoading" />
          <NButton
            data-testid="submit-team-invite"
            type="primary"
            :disabled="!canInviteMember"
            :loading="teamOperationLoading"
            @click="handleInviteMember"
          >
            <template #icon><NIcon aria-hidden="true"><UserPlus /></NIcon></template>
            ??
          </NButton>
        </div>

        <NList :show-divider="false">
          <NListItem v-for="member in activeTeamDetail.members" :key="member.id" class="!px-0 !py-2">
            <div class="flex items-center justify-between gap-3">
              <div class="min-w-0">
                <p class="m-0 truncate text-ink text-14px font-700">{{ member.display_name || member.username }}</p>
                <p class="m-0 mt-0.5 truncate text-sub text-12px">{{ member.email }}</p>
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <NTag size="small" round :bordered="false" :type="statusType(member.role)">
                  {{ roleLabel(member.role) }}
                </NTag>
                <NButton
                  v-if="member.role !== 'owner'"
                  :data-testid="'update-team-member-' + member.id + '-admin'"
                  size="tiny"
                  secondary
                  :disabled="member.role === 'admin'"
                  :loading="teamOperationLoading"
                  @click="emit('update-team-member-role', activeTeamDetail.id, member.id, 'admin')"
                >
                  ?????
                </NButton>
                <NButton
                  v-if="member.role !== 'owner'"
                  :data-testid="'remove-team-member-' + member.id"
                  size="tiny"
                  secondary
                  type="error"
                  :loading="teamOperationLoading"
                  @click="emit('remove-team-member', activeTeamDetail.id, member.id)"
                >
                  <template #icon><NIcon aria-hidden="true"><Trash2 /></NIcon></template>
                  ??
                </NButton>
              </div>
            </div>
          </NListItem>
        </NList>

        <div v-if="activeTeamDetail.invites.length" class="border-t border-line pt-3">
          <p class="m-0 mb-2 text-sub text-12px font-700">?????</p>
          <div v-for="invite in activeTeamDetail.invites" :key="invite.id" class="flex items-center justify-between gap-2 py-1 text-12px">
            <span class="min-w-0 truncate text-ink">{{ invite.email }}</span>
            <NTag size="small" round :bordered="false">{{ roleLabel(invite.role) }} ? {{ invite.status }}</NTag>
          </div>
        </div>
      </div>

      <NEmpty v-else size="small" description="?????" />
    </NCard>

    <NCard v-if="auth.canAccessPermissionAudit" id="audit" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" size="small">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <span>????</span>
          <RouterLink class="text-primary text-12px font-700 no-underline" to="/permission-audit">????</RouterLink>
        </div>
      </template>
      <NEmpty v-if="!auditLogs.length" size="small" description="??????" />
      <NList v-else :show-divider="false">
        <NListItem v-for="log in auditLogs" :key="log.id" class="!px-0 !py-2">
          <NThing :title="log.actor">
            <template #description>{{ log.action }} ? {{ log.resource_name }}</template>
          </NThing>
        </NListItem>
      </NList>
    </NCard>
  </aside>
</template>
