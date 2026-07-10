<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { AtSign, BellRing, Copy, FileText, Link, LogOut, Pencil, Plus, Search, Send, ShieldCheck, Trash2, UsersRound } from '@lucide/vue'
import { useMessage } from 'naive-ui'

import type { WorkspaceTeamMessage, WorkspaceTeamRole } from '@/client/workspace'
import { buildTeamInviteUrl } from '@/client/workspace'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useAuthStore } from '@/stores/auth'

import { useWorkspaceStore } from '@/stores/workspace'

const auth = useAuthStore()
const workspace = useWorkspaceStore()
const message = useMessage()
const {
  activeTeamDetail, apiState, auditLogs, summary, teams,
  teamMessagesById, teamMessageSending, teamMessageTeamIdLoading,
} = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'team-chat')
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const activeTeamId = ref('')
const draftMessage = ref('')
const teamSearch = ref('')
const showMentionPanel = ref(false)
const mentionQuery = ref('')
const notices = ref<Array<{id:string;title:string;detail:string;type:'info'|'success'|'warning'}>>([])

// ── Modals ──
const showCreateTeam = ref(false); const newTeamName = ref(''); const newTeamDesc = ref('')
const showEditTeam = ref(false); const editTeamName = ref(''); const editTeamDesc = ref('')
const showInviteMember = ref(false); const inviteEmail = ref(''); const inviteRole = ref<WorkspaceTeamRole>('member')
const showJoinTeam = ref(false); const joinTeamId = ref(''); const joinToken = ref('')
const showDeleteConfirm = ref(false)

const fallbackTeam = computed(() => teams.value[0] ?? null)
const activeTeam = computed(() => teams.value.find(t => t.id === activeTeamId.value) ?? fallbackTeam.value)
const hasActiveTeam = computed(() => activeTeam.value !== null)
const totalUnread = computed(() => teams.value.reduce((s, t) => s + t.unread_count, 0))
const canManage = computed(() => activeTeam.value ? ['owner','admin','组长','管理员'].includes(activeTeam.value.role) : false)
const canMentionAll = computed(() => canManage.value)
const rawMessages = computed(() => activeTeam.value ? teamMessagesById.value[activeTeam.value.id] ?? [] : [])
const currentUserId = computed(() => auth.currentUser?.id ?? null)

const members = computed(() => (activeTeamDetail.value?.members ?? []).map(m => ({
  id: m.id, name: m.display_name || m.username, role: m.role as string, isOwner: m.role === 'owner',
})))
const memberCount = computed(() => members.value.length)
const roleLabel = (r: string) => ({ owner: '所有者', admin: '管理员', member: '成员', guest: '访客' }[r] || r)
const roleColor = (r: string) => r === 'owner' ? 'warning' : r === 'admin' ? 'info' : 'default'

const messages = computed(() => rawMessages.value.map(m => ({
  id: m.id, author: m.sender_name, time: new Date(m.created_at).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'}),
  content: m.content, mine: currentUserId.value !== null && m.sender_id === currentUserId.value,
  messageType: m.message_type,
})))

const mentionOptions = computed(() => {
  const keyword = mentionQuery.value.trim().toLowerCase()
  const opts = members.value.map(m => ({ id: m.id, label: `@${m.name}`, name: m.name, role: m.role }))
  const all = canMentionAll.value ? [{ id: 'mention-all', label: '@all', name: 'all', role: '提醒所有成员', all: true }, ...opts] : opts
  return keyword ? all.filter(o => o.label.toLowerCase().includes(keyword)) : all
})

// ── URL join detection ──
onMounted(async () => {
  await workspace.loadWorkspace()
  const q = new URLSearchParams(location.search)
  const joinId = q.get('join'); const joinTok = q.get('token')
  if (joinId && joinTok) { joinTeamId.value = joinId; joinToken.value = joinTok; showJoinTeam.value = true }
  const firstTeam = workspace.teams[0]
  if (firstTeam) { activeTeamId.value = firstTeam.id; await workspace.loadTeamDetail(firstTeam.id) }
})

watch(teams, (items) => { if (!activeTeamId.value && items[0]) activeTeamId.value = items[0].id }, { immediate: true })
watch(activeTeamId, (tid) => { if (tid) { void workspace.loadTeamMessages(tid); void workspace.loadTeamDetail(tid) } }, { immediate: true })
watch(() => activeTeamDetail.value?.invites, (invites) => {
  if (!invites) return
  const lastInvite = invites[invites.length - 1]
  if (lastInvite && lastInvite.token) {
    const url = buildTeamInviteUrl((activeTeam.value as any)?.id || '', lastInvite.token)
    navigator.clipboard.writeText(url).then(() => message.success('邀请链接已复制到剪贴板'))
  }
})

function selectTeam(teamId: string) { activeTeamId.value = teamId; showMentionPanel.value = false }

async function handleCreateTeam() {
  if (!newTeamName.value.trim()) return
  await workspace.createTeam({ name: newTeamName.value.trim(), description: newTeamDesc.value.trim() || null })
  showCreateTeam.value = false; newTeamName.value = ''; newTeamDesc.value = ''
  await workspace.loadWorkspace()
}

function openEditTeam() {
  if (!activeTeamDetail.value) return
  editTeamName.value = activeTeamDetail.value.name; editTeamDesc.value = activeTeamDetail.value.description || ''
  showEditTeam.value = true
}
async function handleEditTeam() {
  if (!activeTeam.value || !editTeamName.value.trim()) return
  await workspace.updateTeam(activeTeam.value.id, { name: editTeamName.value.trim(), description: editTeamDesc.value.trim() || null })
  showEditTeam.value = false
}

async function handleInviteMember() {
  if (!activeTeam.value) return
  try {
    await workspace.inviteTeamMember(activeTeam.value.id, { email: inviteEmail.value.trim() || 'member@example.com', role: inviteRole.value })
    showInviteMember.value = false
  } catch { message.error('生成邀请链接失败') }
}

async function handleJoinTeam() {
  if (!joinTeamId.value.trim() || !joinToken.value.trim()) return
  await workspace.joinTeam(joinTeamId.value.trim(), joinToken.value.trim())
  showJoinTeam.value = false; joinTeamId.value = ''; joinToken.value = ''
  await workspace.loadWorkspace()
}

async function handleDeleteTeam() {
  if (!activeTeam.value) return
  await workspace.deleteTeam(activeTeam.value.id); showDeleteConfirm.value = false
}

async function handleLeaveTeam() {
  if (!activeTeam.value) return
  await workspace.leaveTeam(activeTeam.value.id)
}

async function handlePromoteMember(memberId: string, role: WorkspaceTeamRole) {
  if (!activeTeam.value) return
  await workspace.updateTeamMemberRole(activeTeam.value.id, memberId, role)
}

async function handleRemoveMember(memberId: string) {
  if (!activeTeam.value) return
  await workspace.removeTeamMember(activeTeam.value.id, memberId)
}

async function sendMessage() {
  const content = draftMessage.value.trim()
  if (!content || !activeTeam.value) return
  await workspace.sendTeamMessage(activeTeam.value.id, { content, message_type: 'text', receiver_id: null })
  draftMessage.value = ''
  showMentionPanel.value = false
  void nextTick(() => { const list = document.querySelector('.message-list'); list?.scrollTo({ top: list.scrollHeight, behavior: 'smooth' }) })
}

function updateDraftMessage(value: string) {
  draftMessage.value = value
  showMentionPanel.value = /(?:^|\s)@[^\s@]*$/.test(value)
  if (showMentionPanel.value) mentionQuery.value = (value.match(/(?:^|\s)@([^\s@]*)$/) || ['',''])[1] || ''
}

function insertMention(option: any) {
  draftMessage.value = draftMessage.value.replace(/(?:^|\s)@[^\s@]*$/, (m) => `${m.startsWith(' ') ? ' ' : ''}${option.label} `)
  showMentionPanel.value = false
}

function openMentionPanel() {
  mentionQuery.value = ''
  showMentionPanel.value = true
}

function insertFileRef() { draftMessage.value += ' [文件] ' }
</script>

<template>
  <component :is="workspaceLayout" :api-state-label="apiStateLabel" :api-state-type="apiStateType" :nav-items="navItems"
    :unread-notifications="summary.unread_notifications" page-title="团队协作">
    <div class="chat-shell">
      <!-- Team list sidebar -->
      <aside class="conversation-list" aria-label="团队列表">
        <NInput v-model:value="teamSearch" placeholder="搜索团队…" size="small" clearable>
          <template #prefix><NIcon><Search /></NIcon></template>
        </NInput>
        <button v-for="team in teams" :key="team.id" class="team-row" :class="team.id === activeTeam?.id ? 'is-active' : ''" @click="selectTeam(team.id)">
          <span class="team-avatar"><UsersRound :size="17" /></span>
          <span class="team-copy"><strong>{{ team.name }}</strong><small>{{ team.role }} · {{ team.member_count }} 人</small></span>
          <NBadge v-if="team.unread_count" :value="team.unread_count" type="info" />
        </button>
        <div class="flex gap-2 px-3 pb-3">
          <NButton size="tiny" secondary @click="showCreateTeam = true"><template #icon><NIcon :size="14"><Plus /></NIcon></template>新建</NButton>
          <NButton size="tiny" secondary @click="showJoinTeam = true"><template #icon><NIcon :size="14"><Link /></NIcon></template>加入</NButton>
        </div>
      </aside>

      <!-- Chat main -->
      <main v-if="hasActiveTeam" class="chat-main" aria-label="聊天窗口">
        <header class="chat-toolbar">
          <div><strong>{{ activeTeam?.name }}</strong><span>群聊 · {{ memberCount }} 人</span></div>
          <NSpace :size="8">
            <NButton size="small" secondary @click="openMentionPanel"><template #icon><NIcon><AtSign /></NIcon></template>提醒</NButton>
            <NButton size="small" secondary @click="insertFileRef"><template #icon><NIcon><FileText /></NIcon></template>引用文件</NButton>
          </NSpace>
        </header>
        <div class="message-list">
          <article v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.mine ? 'is-mine' : ''">
            <NAvatar round :size="34">{{ msg.author.slice(0,1) }}</NAvatar>
            <div class="message-body"><div class="message-meta"><strong>{{ msg.author }}</strong><time>{{ msg.time }}</time></div><p>{{ msg.content }}</p></div>
          </article>
        </div>
        <form class="composer" @submit.prevent="sendMessage">
          <div class="composer-input">
            <div v-if="showMentionPanel" class="mention-panel">
              <button v-for="opt in mentionOptions" :key="opt.id" class="mention-option" @mousedown.prevent="insertMention(opt)">
                <span class="mention-avatar" :class="(opt as any).all ? 'is-all' : ''">{{ (opt as any).all ? 'ALL' : opt.name.slice(0,1) }}</span>
                <span><strong>{{ opt.label }}</strong><small>{{ opt.role }}</small></span>
              </button>
            </div>
            <NInput :value="draftMessage" type="textarea" placeholder="输入 @ 提醒成员…" :autosize="{ minRows: 2, maxRows: 4 }"
              @keydown.esc="showMentionPanel = false" @update:value="updateDraftMessage" />
          </div>
          <NButton type="primary" attr-type="submit" :loading="teamMessageSending"><template #icon><NIcon><Send /></NIcon></template>发送</NButton>
        </form>
      </main>

      <!-- Empty state -->
      <div v-if="!hasActiveTeam" class="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <NIcon :size="48" color="#94a3b8"><UsersRound /></NIcon>
        <p class="m-0 text-ink text-16px font-700">暂无团队</p>
        <p class="m-0 text-sub text-13px">创建或加入一个团队开始协作</p>
        <NSpace>
          <NButton type="primary" size="small" @click="showCreateTeam = true"><template #icon><NIcon :size="14"><Plus /></NIcon></template>新建团队</NButton>
          <NButton size="small" secondary @click="showJoinTeam = true">加入团队</NButton>
        </NSpace>
      </div>

      <!-- Context panel -->
      <aside v-if="hasActiveTeam" class="context-panel" aria-label="团队管理">
        <!-- Team info card -->
        <NCard size="small" :bordered="false" class="context-card">
          <template #header>
            <div class="flex items-center justify-between gap-2">
              <strong class="text-ink">{{ activeTeam?.name }}</strong>
              <NButton v-if="canManage" size="tiny" text @click="openEditTeam"><template #icon><NIcon :size="14"><Pencil /></NIcon></template></NButton>
            </div>
          </template>
          <p class="m-0 text-sub text-12px leading-[1.6]">{{ activeTeamDetail?.description || '暂无团队描述' }}</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <NTag size="small" :bordered="false" :type="roleColor(activeTeam?.role || '')">{{ roleLabel(activeTeam?.role || '') }}</NTag>
            <NTag size="small" :bordered="false">{{ memberCount }} 人</NTag>
          </div>
        </NCard>

        <!-- Members -->
        <NCard size="small" title="成员" :bordered="false" class="context-card">
          <div class="member-list">
            <div v-for="m in members" :key="m.id" class="member-row">
              <div><strong>{{ m.name }}</strong><small>{{ roleLabel(m.role) }}</small></div>
              <NSpace v-if="canManage && !m.isOwner" :size="4">
                <NButton size="tiny" secondary @click="handlePromoteMember(m.id, m.role === 'admin' ? 'member' : 'admin')">
                  {{ m.role === 'admin' ? '降级' : '提升' }}
                </NButton>
                <NButton size="tiny" secondary type="error" @click="handleRemoveMember(m.id)">
                  <template #icon><NIcon :size="12"><Trash2 /></NIcon></template>
                </NButton>
              </NSpace>
            </div>
          </div>
          <NButton size="tiny" secondary block class="mt-2" @click="showInviteMember = true">
            <template #icon><NIcon :size="14"><Plus /></NIcon></template>邀请成员
          </NButton>
        </NCard>

        <!-- Actions -->
        <NCard size="small" :bordered="false" class="context-card">
          <NButton size="tiny" secondary block class="mb-2" @click="showInviteMember = true">
            <template #icon><NIcon :size="14"><Link /></NIcon></template>邀请成员（生成链接）
          </NButton>
          <NButton v-if="activeTeam?.role === 'owner'" size="tiny" secondary block type="error" class="mb-2" @click="showDeleteConfirm = true">
            <template #icon><NIcon :size="14"><Trash2 /></NIcon></template>解散团队
          </NButton>
          <NButton v-else size="tiny" secondary block @click="handleLeaveTeam">
            <template #icon><NIcon :size="14"><LogOut /></NIcon></template>离开团队
          </NButton>
        </NCard>

        <!-- Notices -->
        <NCard size="small" title="通知" :bordered="false" class="context-card" v-if="notices.length">
          <div class="notice-list">
            <div v-for="n in notices" :key="n.id" class="notice-row">
              <NIcon :class="`notice-${n.type}`"><BellRing /></NIcon>
              <div><strong>{{ n.title }}</strong><small>{{ n.detail }}</small></div>
            </div>
          </div>
        </NCard>
      </aside>
    </div>
  </component>

  <!-- Modals -->
  <NModal v-model:show="showCreateTeam" title="新建团队"><NCard style="width:420px" title="新建团队" :bordered="false" size="small">
    <NFormItem label="团队名称"><NInput v-model:value="newTeamName" placeholder="例如：课程项目组" /></NFormItem>
    <NFormItem label="描述"><NInput v-model:value="newTeamDesc" placeholder="可选描述" /></NFormItem>
    <NSpace justify="end"><NButton @click="showCreateTeam = false">取消</NButton><NButton type="primary" @click="handleCreateTeam">创建</NButton></NSpace>
  </NCard></NModal>

  <NModal v-model:show="showEditTeam" title="编辑团队"><NCard style="width:420px" title="编辑团队信息" :bordered="false" size="small">
    <NFormItem label="团队名称"><NInput v-model:value="editTeamName" /></NFormItem>
    <NFormItem label="描述"><NInput v-model:value="editTeamDesc" type="textarea" :autosize="{minRows:2,maxRows:3}" /></NFormItem>
    <NSpace justify="end"><NButton @click="showEditTeam = false">取消</NButton><NButton type="primary" @click="handleEditTeam">保存</NButton></NSpace>
  </NCard></NModal>

  <NModal v-model:show="showInviteMember" title="生成邀请链接"><NCard style="width:420px" title="生成邀请链接" :bordered="false" size="small">
    <p class="m-0 mb-3 text-sub text-13px">生成邀请链接后自动复制到剪贴板，发送给团队成员即可加入。</p>
    <NFormItem label="角色"><NSelect v-model:value="inviteRole" :options="[{label:'成员',value:'member'},{label:'访客',value:'guest'},{label:'管理员',value:'admin'}]" /></NFormItem>
    <NSpace justify="end"><NButton @click="showInviteMember = false">取消</NButton><NButton type="primary" @click="handleInviteMember">生成链接</NButton></NSpace>
  </NCard></NModal>

  <NModal v-model:show="showJoinTeam" title="加入团队"><NCard style="width:420px" title="加入团队" :bordered="false" size="small">
    <NFormItem label="团队 ID"><NInput v-model:value="joinTeamId" placeholder="输入团队 ID" /></NFormItem>
    <NFormItem label="邀请码"><NInput v-model:value="joinToken" placeholder="输入邀请码" /></NFormItem>
    <NSpace justify="end"><NButton @click="showJoinTeam = false">取消</NButton><NButton type="primary" @click="handleJoinTeam">加入</NButton></NSpace>
  </NCard></NModal>

  <NModal v-model:show="showDeleteConfirm" preset="card" title="解散团队" style="width:400px">
    <p class="m-0">确定要解散 <strong>{{ activeTeam?.name }}</strong> 吗？所有消息和数据将被删除，此操作不可撤销。</p>
    <template #footer><NSpace justify="end"><NButton @click="showDeleteConfirm = false">取消</NButton><NButton type="error" @click="handleDeleteTeam">确认解散</NButton></NSpace></template>
  </NModal>
</template>

<style scoped>
.chat-shell { display: grid; grid-template-columns: 240px minmax(0, 1fr) 280px; min-height: calc(100vh - 170px); overflow: hidden; border: 1px solid #d8e0ea; border-radius: 8px; background: #fff; box-shadow: 0 10px 28px rgba(15,23,42,0.08); }
.conversation-list { display: grid; align-content: start; gap: 10px; padding: 12px; background: #f8fafc; border-right: 1px solid #e8eef6; max-height: calc(100vh - 170px); overflow-y: auto; }
.team-row { display: grid; grid-template-columns: 36px minmax(0, 1fr) auto; gap: 9px; align-items: center; width: 100%; padding: 9px; text-align: left; cursor: pointer; background: #fff; border: 1px solid #e8eef6; border-radius: 8px; transition: border-color 0.18s, box-shadow 0.18s; }
.team-row:hover, .team-row.is-active { border-color: #246bfe; box-shadow: 0 8px 18px rgba(36,107,254,0.1); }
.team-avatar { display: grid; width: 34px; height: 34px; place-items: center; color: #246bfe; background: rgba(36,107,254,0.1); border-radius: 8px; }
.team-copy { min-width: 0; }
.team-copy strong, .team-copy small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.team-copy strong { color: #172033; font-size: 13px; }
.team-copy small { color: #64748b; font-size: 12px; }
.chat-main { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; min-width: 0; background: #fff; }
.chat-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #e8eef6; }
.chat-toolbar strong { color: #172033; font-size: 15px; font-weight: 800; display: block; }
.chat-toolbar span { color: #64748b; font-size: 12px; display: block; margin-top: 2px; }
.message-list { display: grid; align-content: start; gap: 13px; overflow: auto; min-height: 0; padding: 16px 14px; background: linear-gradient(180deg,#fff,#f8fbff); }
.message-row { display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 10px; align-items: start; }
.message-row.is-mine { grid-template-columns: minmax(0, 1fr) 34px; }
.message-row.is-mine :deep(.n-avatar) { grid-column: 2; grid-row: 1; }
.message-row.is-mine .message-body { grid-column: 1; grid-row: 1; justify-self: end; background: #eaf2ff; border-color: #c6dcff; }
.message-body { max-width: min(560px, 100%); padding: 10px 12px; background: #fff; border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 18px rgba(15,23,42,0.05); }
.message-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; color: #64748b; font-size: 12px; }
.message-meta strong { color: #172033; }
.message-body p { margin: 7px 0 0; color: #334155; font-size: 13px; line-height: 1.65; }
.composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: end; padding: 12px; border-top: 1px solid #e8eef6; background: #fff; }
.composer-input { position: relative; min-width: 0; }
.mention-panel { position: absolute; right: 0; bottom: calc(100% + 8px); z-index: 5; display: grid; width: min(340px, 100%); max-height: 260px; overflow: auto; padding: 8px; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 18px 36px rgba(15,23,42,0.16); }
.mention-option { display: grid; grid-template-columns: 38px minmax(0, 1fr); gap: 9px; align-items: center; width: 100%; padding: 8px; text-align: left; cursor: pointer; background: transparent; border: 0; border-radius: 8px; }
.mention-option:hover { background: #f1f5ff; }
.mention-avatar { display: grid; width: 34px; height: 34px; place-items: center; color: #246bfe; font-size: 13px; font-weight: 800; background: rgba(36,107,254,0.1); border-radius: 8px; }
.mention-avatar.is-all { color: #7c3aed; background: rgba(124,58,237,0.1); font-size: 11px; }
.mention-option strong, .mention-option small { display: block; }
.mention-option strong { color: #172033; font-size: 13px; }
.mention-option small { color: #64748b; font-size: 12px; }
.context-panel { display: grid; align-content: start; gap: 12px; overflow: auto; max-height: calc(100vh - 170px); padding: 12px; background: #f8fafc; border-left: 1px solid #e8eef6; }
.context-card { overflow: hidden; border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 18px rgba(15,23,42,0.04); }
.member-list, .notice-list { display: grid; gap: 10px; }
.member-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: center; }
.notice-row { display: grid; grid-template-columns: 30px minmax(0, 1fr); gap: 9px; align-items: center; }
.member-row strong, .member-row small { display: block; }
.member-row strong { color: #172033; font-size: 13px; }
.member-row small { margin-top: 2px; color: #64748b; font-size: 12px; }
.notice-info { color: #246bfe; } .notice-success { color: #16a34a; } .notice-warning { color: #d97706; }
@media (max-width: 1200px) { .chat-shell { grid-template-columns: 220px minmax(0, 1fr); } .context-panel { grid-column: 1/-1; grid-template-columns: repeat(3, minmax(0, 1fr)); border-left: 0; border-top: 1px solid #e8eef6; } }
@media (max-width: 820px) { .chat-shell, .context-panel { grid-template-columns: 1fr; } .conversation-list { border-right: 0; border-bottom: 1px solid #e8eef6; } .chat-toolbar, .composer { flex-direction: column; align-items: flex-start; } .composer { display: flex; } .composer-input { width: 100%; } }
</style>
