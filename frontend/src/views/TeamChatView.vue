<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { AtSign, BellRing, FileText, LockKeyhole, Paperclip, Search, Send, ShieldCheck, UsersRound } from '@lucide/vue'

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
  attachment?: string
  mentions?: string[]
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
const { apiState, auditLogs, summary, teams } = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'team-chat')
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const activeTeamId = ref('')
const draftMessage = ref('')
const composerRef = ref<HTMLElement | null>(null)
const showMentionPanel = ref(false)
const mentionQuery = ref('')

const fallbackTeam = computed(() =>
  teams.value[0] ?? { id: 'team-demo', name: '课程协作小组', role: '组长', member_count: 5, unread_count: 0 },
)
const activeTeam = computed(() => teams.value.find((team) => team.id === activeTeamId.value) ?? fallbackTeam.value)
const totalUnread = computed(() => teams.value.reduce((sum, team) => sum + team.unread_count, 0))
const canMentionAll = computed(() => /组长|管理员/.test(activeTeam.value.role))

const messages = ref<ChatMessage[]>([
  {
    id: 'msg-1',
    author: '林予安',
    role: '组长',
    time: '09:18',
    content: '我把需求规格说明书放到团队文件夹了，今天先集中确认聊天、批注和周报生成这条流程。',
    attachment: '需求规格说明书.md',
  },
  {
    id: 'msg-2',
    author: '周明',
    role: '成员',
    time: '09:26',
    content: '已看。团队协作这里需要能看到实时群聊、成员在线状态、文件引用和未读提醒，刷新后聊天记录还要保留。',
  },
  {
    id: 'msg-3',
    author: '智能助手',
    role: 'Agent',
    time: '09:31',
    content: '已根据团队文件生成待办摘要：补充 WebSocket 重连、消息持久化、@ 提醒和权限校验验收点。',
    attachment: '团队周报草稿.docx',
  },
  {
    id: 'msg-4',
    author: '我',
    role: '成员',
    time: '09:42',
    content: '收到，我先把聊天页面接到独立路由，后续再接真实 WebSocket。',
    mine: true,
  },
])

const members = computed<TeamMember[]>(() => [
  { id: 'member-1', name: '林予安', role: '组长', online: true },
  { id: 'member-2', name: '周明', role: '资料整理', online: true },
  { id: 'member-3', name: '陈可', role: '报告撰写', online: false },
  { id: 'member-4', name: '智能助手', role: 'Agent', online: true },
])

const notices = ref<TeamNotice[]>([
  { id: 'notice-1', title: '@ 提醒', detail: '周明在需求文档批注中提到了你', type: 'info' },
  { id: 'notice-2', title: '文件更新', detail: '团队周报草稿已生成新版本', type: 'success' },
  { id: 'notice-3', title: '权限变更', detail: '访客仅可查看共享资料文件夹', type: 'warning' },
])

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

onMounted(() => {
  void workspace.loadWorkspace()
})

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

function sendMessage() {
  const content = draftMessage.value.trim()
  if (!content) return

  const mentions = mentionedTargets(content)
  messages.value.push({
    id: `msg-${Date.now()}`,
    author: '我',
    role: activeTeam.value.role,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    content,
    mentions,
    mine: true,
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
          <NInput placeholder="搜索团队或成员" size="small" clearable>
            <template #prefix>
              <NIcon aria-hidden="true"><Search /></NIcon>
            </template>
          </NInput>

          <button
            v-for="team in teams"
            :key="team.id"
            class="team-row"
            :class="team.id === activeTeam.id ? 'is-active' : ''"
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
        </aside>

        <main class="chat-main" aria-label="团队聊天窗口">
          <header class="chat-toolbar">
            <div>
              <strong>{{ activeTeam.name }}</strong>
              <span>群聊 · WebSocket 待接入 · 历史消息已持久化展示</span>
            </div>
            <NSpace :size="8">
              <NButton size="small" secondary @click="openMentionPanel">
                <template #icon><NIcon><AtSign /></NIcon></template>
                提醒成员
              </NButton>
              <NButton size="small" secondary type="primary">
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
                <button v-if="message.attachment" class="attachment-pill" type="button">
                  <Paperclip :size="14" />
                  {{ message.attachment }}
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
            <NButton type="primary" attr-type="submit">
              <template #icon><NIcon><Send /></NIcon></template>
              发送
            </NButton>
          </form>
        </main>

        <aside class="context-panel" aria-label="团队上下文">
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
