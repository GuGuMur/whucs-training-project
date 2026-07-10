<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { AtSign, BellRing, FileText, LockKeyhole, Paperclip, Plus, Search, Send, ShieldCheck, UsersRound } from '@lucide/vue'

import type { WorkspaceTeamMessage, WorkspaceTeamRole } from '@/client/workspace'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'

interface ChatMessage {
  id: string
  author: string
  role: string
  time: string
  content: string
  mine?: boolean
  mentions?: string[]
  messageType: WorkspaceTeamMessage['message_type']
}

interface TeamMember {
  id: string
  name: string
  role: string
  online: boolean
}

interface TeamNotice {
  id: string
  title: string
  detail: string
  type: 'info' | 'success' | 'warning'
}

interface MentionOption {
  id: string
  label: string
  name: string
  role: string
  online?: boolean
  all?: boolean
}

const auth = useAuthStore()
const workspace = useWorkspaceStore()
const {
  activeTeamDetail,
  apiState,
  auditLogs,
  summary,
  teams,
  teamMessagesById,
  teamMessageSending,
  teamMessageTeamIdLoading,
} = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'team-chat')
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const activeTeamId = ref('')
const draftMessage = ref('')
const teamSearch = ref('')
const composerRef = ref<HTMLElement | null>(null)
const showMentionPanel = ref(false)
const mentionQuery = ref('')

const fallbackTeam = computed(() =>
  teams.value[0] ?? null,
)
const activeTeam = computed(() => teams.value.find((team) => team.id === activeTeamId.value) ?? fallbackTeam.value)
const hasActiveTeam = computed(() => activeTeam.value !== null)
const totalUnread = computed(() => teams.value.reduce((sum, team) => sum + team.unread_count, 0))
const canMentionAll = computed(() => activeTeam.value ? ['owner', 'admin', '组长', '管理员'].includes(activeTeam.value.role) : false)
const rawMessages = computed(() => activeTeam.value ? teamMessagesById.value[activeTeam.value.id] ?? [] : [])
const currentUserId = computed(() => auth.currentUser?.id ?? null)

const members = computed<TeamMember[]>(() =>
  (activeTeamDetail.value?.members ?? []).map((member) => ({
    id: member.id,
    name: member.display_name || member.username,
    role: member.role,
    online: true,
  })),
)

const messages = computed<ChatMessage[]>(() =>
  rawMessages.value.map((message) => ({
    id: message.id,
    author: message.sender_name,
    role: memberRoleLabel(message.sender_name, message.message_type),
    time: formatMessageTime(message.created_at),
    content: message.content,
    mentions: mentionedTargets(message.content),
    mine: currentUserId.value !== null && message.sender_id === currentUserId.value,
    messageType: message.message_type,
  })),
)

const notices = ref<TeamNotice[]>([])
const showCreateTeam = ref(false)
const newTeamName = ref('')
const newTeamDesc = ref('')
const showInviteMember = ref(false)
const inviteEmail = ref('')
const inviteRole = ref<WorkspaceTeamRole>('member')
const showJoinTeam = ref(false)
const joinTeamId = ref('')
const joinToken = ref('')

async function handleCreateTeam() {
  if (!newTeamName.value.trim()) return
  await workspace.createTeam({ name: newTeamName.value.trim(), description: newTeamDesc.value.trim() })
  showCreateTeam.value = false
  newTeamName.value = ''
  newTeamDesc.value = ''
  await workspace.loadWorkspace()
}

async function handleInviteMember() {
  if (!inviteEmail.value.trim() || !activeTeam.value) return
  await workspace.inviteTeamMember(activeTeam.value.id, { email: inviteEmail.value.trim(), role: inviteRole.value })
  inviteEmail.value = ''
  showInviteMember.value = false
}

async function handleJoinTeam() {
  if (!joinTeamId.value.trim() || !joinToken.value.trim()) return
  await workspace.joinTeam(joinTeamId.value.trim(), joinToken.value.trim())
  showJoinTeam.value = false
  joinTeamId.value = ''
  joinToken.value = ''
  await workspace.loadWorkspace()
}

const mentionOptions = computed<MentionOption[]>(() => {
  const keyword = mentionQuery.value.trim().toLowerCase()
  const memberOptions: MentionOption[] = members.value.map((member) => ({
    id: member.id,
    label: `@${member.name}`,
    name: member.name,
    role: member.role,
    online: member.online,
  }))
  const options = canMentionAll.value
    ? [{ id: 'mention-all', label: '@all', name: 'all', role: '提醒所有成员', all: true }, ...memberOptions]
    : memberOptions

  if (!keyword) return options
  return options.filter((option) => option.label.toLowerCase().includes(keyword) || option.role.toLowerCase().includes(keyword))
})

onMounted(async () => {
  await workspace.loadWorkspace()
  const firstTeam = workspace.teams[0]
  if (firstTeam) {
    activeTeamId.value = firstTeam.id
    await workspace.loadTeamDetail(firstTeam.id)
  }
})

watch(
  teams,
  (items) => {
    if (!activeTeamId.value && items[0]) {
      activeTeamId.value = items[0].id
    }
  },
  { immediate: true },
)

watch(
  activeTeamId,
  (teamId) => {
    if (teamId) {
      void workspace.loadTeamMessages(teamId)
    }
  },
  { immediate: true },
)

function selectTeam(teamId: string) {
  activeTeamId.value = teamId
  showMentionPanel.value = false
}

function openMentionPanel() {
  mentionQuery.value = ''
  showMentionPanel.value = true
}

function updateDraftMessage(value: string) {
  draftMessage.value = value
  const match = value.match(/(?:^|\s)@([^\s@]*)$/)
  if (match) {
    mentionQuery.value = match[1] ?? ''
    showMentionPanel.value = true
    return
  }
  showMentionPanel.value = false
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key === '@') {
    openMentionPanel()
  }
  if (event.key === 'Escape') {
    showMentionPanel.value = false
  }
}

function insertMention(option: MentionOption) {
  const mentionText = `${option.label} `
  const hasOpenMention = /(?:^|\s)@[^\s@]*$/.test(draftMessage.value)
  draftMessage.value = hasOpenMention
    ? draftMessage.value.replace(/(?:^|\s)@[^\s@]*$/, (match) => `${match.startsWith(' ') ? ' ' : ''}${mentionText}`)
    : `${draftMessage.value}${draftMessage.value.endsWith(' ') || !draftMessage.value ? '' : ' '}${mentionText}`
  showMentionPanel.value = false
  mentionQuery.value = ''
  void nextTick(() => composerRef.value?.querySelector('textarea')?.focus())
}

function mentionedTargets(content: string) {
  const names = members.value.map((member) => member.name)
  const targets = names.filter((name) => content.includes(`@${name}`))
  if (content.includes('@all') && canMentionAll.value) {
    return ['all', ...targets]
  }
  return targets
}

function memberRoleLabel(senderName: string, messageType: WorkspaceTeamMessage['message_type']) {
  if (messageType === 'system') {
    return 'system'
  }
  const member = activeTeamDetail.value?.members.find(
    (item) => item.username === senderName || item.display_name === senderName,
  )
  return member?.role ?? 'member'
}

function formatMessageTime(createdAt: string) {
  return new Date(createdAt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function sendMessage() {
  const content = draftMessage.value.trim()
  if (!content || !activeTeam.value) return

  const mentions = mentionedTargets(content)
  await workspace.sendTeamMessage(activeTeam.value.id, {
    content,
    message_type: 'text',
    receiver_id: null,
  })
  if (mentions.length) {
    notices.value.unshift({
      id: `notice-${Date.now()}`,
      title: mentions.includes('all') ? '@all 提醒' : '@ 成员提醒',
      detail: mentions.includes('all') ? `你在 ${activeTeam.value.name} 提醒了所有成员` : `你提醒了 ${mentions.join('、')}`,
      type: 'info',
    })
  }
  draftMessage.value = ''
  showMentionPanel.value = false
}
</script>

<template>
  <component
    :is="workspaceLayout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
    page-title="团队协作"
  >
    <section class="team-chat-page">
      <div class="chat-heading">
        <div>
          <p class="eyebrow">团队协作 · 群聊 / 批注 / 通知</p>
          <h2>团队协作聊天</h2>
          <span>围绕团队空间、共享文件、实时消息、成员权限和审计记录进行协同。</span>
        </div>
        <NSpace align="center">
          <NTag type="info" round>{{ totalUnread }} 条未读</NTag>
          <RouterLink class="btn-secondary no-underline" to="/">
            返回工作台
          </RouterLink>
        </NSpace>
      </div>

      <div class="chat-shell">
        <aside class="conversation-list" aria-label="团队会话列表">
          <NInput v-model:value="teamSearch" placeholder="搜索团队或成员" size="small" clearable>
            <template #prefix>
              <NIcon aria-hidden="true"><Search /></NIcon>
            </template>
          </NInput>

          <button
            v-for="team in teams"
            :key="team.id"
            class="team-row"
            :class="team.id === activeTeam?.id ? 'is-active' : ''"
            type="button"
            @click="selectTeam(team.id)"
          >
            <span class="team-avatar"><UsersRound :size="17" /></span>
            <span class="team-copy">
              <strong>{{ team.name }}</strong>
              <small>{{ team.role }} · {{ team.member_count }} 人</small>
            </span>
            <NBadge v-if="team.unread_count" :value="team.unread_count" type="info" />
          </button>
          <div class="flex gap-2 px-3 pb-3">
            <NButton size="tiny" secondary @click="showCreateTeam = true">
              <template #icon><NIcon :size="14"><component :is="Plus" /></NIcon></template>
              新建团队
            </NButton>
            <NButton size="tiny" secondary @click="showJoinTeam = true">
              <template #icon><NIcon :size="14"><component :is="Plus" /></NIcon></template>
              加入
            </NButton>
          </div>
        </aside>

        <main v-if="hasActiveTeam" class="chat-main" aria-label="团队聊天窗口">
          <header class="chat-toolbar">
            <div>
              <strong>{{ activeTeam.name }}</strong>
              <span>群聊 · 历史消息</span>
            </div>
            <NSpace :size="8">
              <NTag v-if="teamMessageTeamIdLoading === activeTeam.id" size="small" type="info" :bordered="false">
                加载历史
              </NTag>
              <NButton size="small" secondary @click="openMentionPanel">
                <template #icon><NIcon><AtSign /></NIcon></template>
                提醒成员
              </NButton>
              <NButton size="small" secondary type="primary" @click="draftMessage += ' [文件] '">
                <template #icon><NIcon><FileText /></NIcon></template>
                引用文件
              </NButton>
            </NSpace>
          </header>

          <div class="message-list">
            <article v-for="message in messages" :key="message.id" class="message-row" :class="message.mine ? 'is-mine' : ''">
              <NAvatar round :size="34">{{ message.author.slice(0, 1) }}</NAvatar>
              <div class="message-body">
                <div class="message-meta">
                  <strong>{{ message.author }}</strong>
                  <NTag size="small" :bordered="false">{{ message.role }}</NTag>
                  <time>{{ message.time }}</time>
                </div>
                <p>{{ message.content }}</p>
                <div v-if="message.mentions?.length" class="mention-tags">
                  <NTag v-for="target in message.mentions" :key="target" size="small" type="info" :bordered="false">
                    @{{ target }}
                  </NTag>
                </div>
                <button v-if="message.messageType === 'file'" class="attachment-pill" type="button">
                  <Paperclip :size="14" />
                  文件消息
                </button>
              </div>
            </article>
          </div>

          <form class="composer" @submit.prevent="sendMessage">
            <div ref="composerRef" class="composer-input">
              <div v-if="showMentionPanel" class="mention-panel">
                <button
                  v-for="option in mentionOptions"
                  :key="option.id"
                  class="mention-option"
                  type="button"
                  @mousedown.prevent="insertMention(option)"
                >
                  <span class="mention-avatar" :class="option.all ? 'is-all' : ''">{{ option.all ? 'ALL' : option.name.slice(0, 1) }}</span>
                  <span>
                    <strong>{{ option.label }}</strong>
                    <small>{{ option.role }}{{ option.online === false ? ' · 离线' : option.online ? ' · 在线' : '' }}</small>
                  </span>
                </button>
                <div v-if="!mentionOptions.length" class="mention-empty">没有匹配成员</div>
              </div>
              <NInput
                :value="draftMessage"
                type="textarea"
                placeholder="输入 @ 可选择成员，组长可使用 @all 提醒所有人"
                :autosize="{ minRows: 2, maxRows: 4 }"
                @keydown="handleComposerKeydown"
                @update:value="updateDraftMessage"
              />
            </div>
            <NButton type="primary" attr-type="submit" :loading="teamMessageSending">
              <template #icon><NIcon><Send /></NIcon></template>
              发送
            </NButton>
          </form>
        </main>

        <!-- Empty state when no team exists -->
        <div v-if="!hasActiveTeam" class="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <NIcon :size="48" color="#94a3b8"><UsersRound /></NIcon>
          <p class="m-0 text-ink text-16px font-700">暂无团队</p>
          <p class="m-0 text-sub text-13px">创建或加入一个团队开始协作</p>
          <NSpace>
            <NButton type="primary" size="small" @click="showCreateTeam = true">
              <template #icon><NIcon :size="14"><Plus /></NIcon></template>
              新建团队
            </NButton>
            <NButton size="small" secondary @click="showJoinTeam = true">加入团队</NButton>
          </NSpace>
        </div>

        <aside v-if="hasActiveTeam" class="context-panel" aria-label="团队上下文">
          <NCard size="small" title="成员与权限" :bordered="false" class="context-card">
            <div class="member-list">
              <div v-for="member in members" :key="member.id" class="member-row">
                <span class="presence" :class="member.online ? 'is-online' : ''"></span>
                <div>
                  <strong>{{ member.name }}</strong>
                  <small>{{ member.role }}</small>
                </div>
                <NIcon class="permission-icon" aria-hidden="true"><ShieldCheck /></NIcon>
              </div>
            </div>
            <NButton size="tiny" secondary block class="mt-2" @click="showInviteMember = true">
              <template #icon><NIcon :size="14"><Plus /></NIcon></template>
              邀请成员
            </NButton>
          </NCard>

          <NCard size="small" title="通知中心" :bordered="false" class="context-card">
            <div class="notice-list">
              <div v-for="notice in notices" :key="notice.id" class="notice-row">
                <NIcon aria-hidden="true" :class="`notice-${notice.type}`"><BellRing /></NIcon>
                <div>
                  <strong>{{ notice.title }}</strong>
                  <small>{{ notice.detail }}</small>
                </div>
              </div>
            </div>
          </NCard>

          <NCard size="small" title="权限审计" :bordered="false" class="context-card">
            <NList>
              <NListItem v-for="log in auditLogs" :key="log.id">
                <NThing :title="log.actor">
                  <template #description>
                    <span class="audit-line"><LockKeyhole :size="14" />{{ log.action }} · {{ log.resource_name }}</span>
                  </template>
                </NThing>
              </NListItem>
            </NList>
          </NCard>
        </aside>
      </div>
    </section>
  </component>

  <!-- Create Team Modal -->
  <NModal v-model:show="showCreateTeam" title="新建团队">
    <NCard style="width:420px" title="新建团队" :bordered="false" size="small">
      <NFormItem label="团队名称">
        <NInput v-model:value="newTeamName" placeholder="例如：课程项目组" />
      </NFormItem>
      <NFormItem label="团队描述">
        <NInput v-model:value="newTeamDesc" placeholder="可选描述" />
      </NFormItem>
      <NSpace justify="end">
        <NButton @click="showCreateTeam = false">取消</NButton>
        <NButton type="primary" @click="handleCreateTeam">创建</NButton>
      </NSpace>
    </NCard>
  </NModal>

  <!-- Invite Member Modal -->
  <NModal v-model:show="showInviteMember" title="邀请成员">
    <NCard style="width:420px" title="邀请成员" :bordered="false" size="small">
      <NFormItem label="邮箱">
        <NInput v-model:value="inviteEmail" placeholder="member@example.com" />
      </NFormItem>
      <NFormItem label="角色">
        <NSelect v-model:value="inviteRole" :options="[{ label: '成员', value: 'member' }, { label: '访客', value: 'guest' }, { label: '管理员', value: 'admin' }]" />
      </NFormItem>
      <NSpace justify="end">
        <NButton @click="showInviteMember = false">取消</NButton>
        <NButton type="primary" @click="handleInviteMember">发送邀请</NButton>
      </NSpace>
    </NCard>
  </NModal>

  <!-- Join Team Modal -->
  <NModal v-model:show="showJoinTeam" title="加入团队">
    <NCard style="width:420px" title="加入团队" :bordered="false" size="small">
      <NFormItem label="团队 ID">
        <NInput v-model:value="joinTeamId" placeholder="输入团队 ID 或从邀请链接获取" />
      </NFormItem>
      <NFormItem label="邀请码">
        <NInput v-model:value="joinToken" placeholder="输入邀请码" />
      </NFormItem>
      <NSpace justify="end">
        <NButton @click="showJoinTeam = false">取消</NButton>
        <NButton type="primary" @click="handleJoinTeam">加入团队</NButton>
      </NSpace>
    </NCard>
  </NModal>
</template>

<style scoped>
.team-chat-page { display: grid; gap: 14px; min-width: 0; }
.chat-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.chat-heading .eyebrow { margin: 0 0 4px; color: #64748b; font-size: 13px; }
.chat-heading h2 { margin: 0; color: #172033; font-size: 30px; font-weight: 800; line-height: 1.2; }
.chat-heading span { display: block; margin-top: 6px; color: #64748b; font-size: 14px; }
.chat-shell { display: grid; grid-template-columns: 240px minmax(0, 1fr) 300px; min-height: calc(100vh - 170px); overflow: hidden; border: 1px solid #d8e0ea; border-radius: 8px; background: #fff; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08); }
.conversation-list { display: grid; align-content: start; gap: 10px; padding: 12px; background: #f8fafc; border-right: 1px solid #e8eef6; }
.team-row { display: grid; grid-template-columns: 36px minmax(0, 1fr) auto; gap: 9px; align-items: center; width: 100%; padding: 9px; text-align: left; cursor: pointer; background: #fff; border: 1px solid #e8eef6; border-radius: 8px; transition: border-color 0.18s ease, box-shadow 0.18s ease; }
.team-row:hover, .team-row.is-active { border-color: #246bfe; box-shadow: 0 8px 18px rgba(36, 107, 254, 0.1); }
.team-avatar { display: grid; width: 34px; height: 34px; place-items: center; color: #246bfe; background: rgba(36, 107, 254, 0.1); border-radius: 8px; }
.team-copy { min-width: 0; }
.team-copy strong, .team-copy small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.team-copy strong { color: #172033; font-size: 13px; }
.team-copy small { margin-top: 2px; color: #64748b; font-size: 12px; }
.chat-main { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; min-width: 0; background: #fff; }
.chat-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #e8eef6; }
.chat-toolbar strong, .chat-toolbar span { display: block; }
.chat-toolbar strong { color: #172033; font-size: 15px; font-weight: 800; }
.chat-toolbar span { margin-top: 2px; color: #64748b; font-size: 12px; }
.message-list { display: grid; align-content: start; gap: 13px; overflow: auto; min-height: 0; padding: 16px 14px; background: linear-gradient(180deg, #ffffff, #f8fbff); }
.message-row { display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 10px; align-items: start; }
.message-row.is-mine { grid-template-columns: minmax(0, 1fr) 34px; }
.message-row.is-mine :deep(.n-avatar) { grid-column: 2; grid-row: 1; }
.message-row.is-mine .message-body { grid-column: 1; grid-row: 1; justify-self: end; background: #eaf2ff; border-color: #c6dcff; }
.message-body { max-width: min(560px, 100%); padding: 10px 12px; background: #fff; border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05); }
.message-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; color: #64748b; font-size: 12px; }
.message-meta strong { color: #172033; }
.message-body p { margin: 7px 0 0; color: #334155; font-size: 13px; line-height: 1.65; }
.mention-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.attachment-pill { display: inline-flex; gap: 6px; align-items: center; margin-top: 8px; padding: 5px 8px; color: #246bfe; cursor: pointer; background: rgba(36, 107, 254, 0.08); border: 1px solid rgba(36, 107, 254, 0.18); border-radius: 8px; }
.composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: end; padding: 12px; border-top: 1px solid #e8eef6; background: #fff; }
.composer-input { position: relative; min-width: 0; }
.mention-panel { position: absolute; right: 0; bottom: calc(100% + 8px); z-index: 5; display: grid; width: min(340px, 100%); max-height: 260px; overflow: auto; padding: 8px; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 18px 36px rgba(15, 23, 42, 0.16); }
.mention-option { display: grid; grid-template-columns: 38px minmax(0, 1fr); gap: 9px; align-items: center; width: 100%; padding: 8px; text-align: left; cursor: pointer; background: transparent; border: 0; border-radius: 8px; }
.mention-option:hover { background: #f1f5ff; }
.mention-avatar { display: grid; width: 34px; height: 34px; place-items: center; color: #246bfe; font-size: 13px; font-weight: 800; background: rgba(36, 107, 254, 0.1); border-radius: 8px; }
.mention-avatar.is-all { color: #7c3aed; background: rgba(124, 58, 237, 0.1); font-size: 11px; }
.mention-option strong, .mention-option small { display: block; }
.mention-option strong { color: #172033; font-size: 13px; }
.mention-option small, .mention-empty { color: #64748b; font-size: 12px; }
.mention-empty { padding: 10px; text-align: center; }
.context-panel { display: grid; align-content: start; gap: 12px; overflow: auto; padding: 12px; background: #f8fafc; border-left: 1px solid #e8eef6; }
.context-card { overflow: hidden; border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04); }
.member-list, .notice-list { display: grid; gap: 10px; }
.member-row, .notice-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 9px; align-items: center; }
.notice-row { grid-template-columns: 30px minmax(0, 1fr); }
.member-row strong, .member-row small, .notice-row strong, .notice-row small { display: block; }
.member-row strong, .notice-row strong { color: #172033; font-size: 13px; }
.member-row small, .notice-row small { margin-top: 2px; color: #64748b; font-size: 12px; line-height: 1.45; }
.presence { width: 9px; height: 9px; background: #cbd5e1; border-radius: 999px; }
.presence.is-online { background: #22c55e; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12); }
.permission-icon { color: #0f766e; }
.notice-info { color: #246bfe; }
.notice-success { color: #16a34a; }
.notice-warning { color: #d97706; }
.audit-line { display: inline-flex; gap: 6px; align-items: center; }
@media (max-width: 1200px) { .chat-shell { grid-template-columns: 220px minmax(0, 1fr); } .context-panel { grid-column: 1 / -1; grid-template-columns: repeat(3, minmax(0, 1fr)); border-left: 0; border-top: 1px solid #e8eef6; } }
@media (max-width: 820px) { .chat-heading { align-items: flex-start; flex-direction: column; } .chat-shell, .context-panel { grid-template-columns: 1fr; } .conversation-list { border-right: 0; border-bottom: 1px solid #e8eef6; } .chat-toolbar, .composer { align-items: flex-start; flex-direction: column; } .composer { display: flex; } .composer-input { width: 100%; } }
</style>
