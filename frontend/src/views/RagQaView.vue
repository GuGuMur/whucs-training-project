<script setup lang="ts">
import { computed, onMounted, shallowRef, watch } from 'vue'
import { storeToRefs } from 'pinia'

import type {
  WorkspaceKnowledgeBase,
  WorkspaceKnowledgeBaseCreateInput,
  WorkspaceKnowledgeBaseUpdateInput,
  WorkspaceQuestionInput,
} from '@/client/workspace'
import KnowledgeBaseManager from '@/components/rag/KnowledgeBaseManager.vue'
import KnowledgeBaseSidebar from '@/components/rag/KnowledgeBaseSidebar.vue'
import KnowledgeConversationPanel from '@/components/rag/KnowledgeConversationPanel.vue'
import KnowledgeFilePicker from '@/components/rag/KnowledgeFilePicker.vue'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const knowledge = useKnowledgeStore()

const { apiState, summary } = storeToRefs(workspace)
const {
  activeConversationId,
  activeKnowledgeBase,
  activeKnowledgeBaseId,
  activeKnowledgeDocuments,
  addingKnowledgeDocument,
  askingQuestion,
  conversationLoading,
  deletingConversationId,
  deletingKnowledgeBaseId,
  indexedFiles,
  knowledgeBases,
  knowledgeConversationsByKbId,
  knowledgeMessagesByConversationId,
  knowledgeOperationLoading,
  reindexingKnowledgeBaseId,
} = storeToRefs(knowledge)

const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'rag')
const layout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const managerVisible = shallowRef(false)
const editingKnowledgeBase = shallowRef<WorkspaceKnowledgeBase | null>(null)
const activeWorkTab = shallowRef<'files' | 'conversations'>('files')

const activeConversations = computed(() =>
  activeKnowledgeBaseId.value
    ? knowledgeConversationsByKbId.value[activeKnowledgeBaseId.value] ?? []
    : [],
)
const activeMessages = computed(() =>
  activeConversationId.value
    ? knowledgeMessagesByConversationId.value[activeConversationId.value] ?? []
    : [],
)
const managerMode = computed(() => (editingKnowledgeBase.value ? 'edit' : 'create'))
const reindexingActiveKnowledgeBase = computed(
  () => Boolean(activeKnowledgeBaseId.value && reindexingKnowledgeBaseId.value === activeKnowledgeBaseId.value),
)

onMounted(async () => {
  await workspace.loadWorkspace()
  await knowledge.loadKnowledgeBases()
  if (activeKnowledgeBaseId.value) {
    await loadKnowledgeBaseDetail(activeKnowledgeBaseId.value)
  }
})

watch(activeKnowledgeBaseId, async (kbId, previousKbId) => {
  if (!kbId || kbId === previousKbId) return
  await loadKnowledgeBaseDetail(kbId)
})

async function loadKnowledgeBaseDetail(kbId: string) {
  await Promise.all([
    knowledge.loadKnowledgeDocuments(kbId),
    knowledge.loadKnowledgeConversations(kbId),
  ])
}

async function selectKnowledgeBase(kbId: string) {
  await knowledge.selectKnowledgeBase(kbId)
  await loadKnowledgeBaseDetail(kbId)
}

function openCreateManager() {
  editingKnowledgeBase.value = null
  managerVisible.value = true
}

function openEditManager(kb: WorkspaceKnowledgeBase) {
  editingKnowledgeBase.value = kb
  managerVisible.value = true
}

async function createKnowledgeBase(payload: WorkspaceKnowledgeBaseCreateInput) {
  const created = await knowledge.createKnowledgeBase(payload)
  managerVisible.value = false
  await loadKnowledgeBaseDetail(created.id)
}

async function updateKnowledgeBase(kbId: string, payload: WorkspaceKnowledgeBaseUpdateInput) {
  await knowledge.updateKnowledgeBase(kbId, payload)
  managerVisible.value = false
}

async function archiveKnowledgeBase(kbId: string) {
  await knowledge.updateKnowledgeBase(kbId, { status: 'archived' })
  managerVisible.value = false
}

async function deleteKnowledgeBase(kbId: string) {
  await knowledge.deleteKnowledgeBase(kbId)
  managerVisible.value = false
}

async function batchAddFiles(fileIds: string[]) {
  if (!activeKnowledgeBaseId.value) return
  await knowledge.batchAddKnowledgeFiles(activeKnowledgeBaseId.value, fileIds)
}

async function batchRemoveFiles(fileIds: string[]) {
  if (!activeKnowledgeBaseId.value) return
  await knowledge.batchRemoveKnowledgeFiles(activeKnowledgeBaseId.value, fileIds)
}

async function askQuestion(payload: WorkspaceQuestionInput) {
  const response = await knowledge.askKnowledgeQuestion(payload)
  await knowledge.loadKnowledgeConversations(payload.kbId)
  await knowledge.loadKnowledgeConversation(response.conversation_id)
}

async function selectConversation(conversationId: string) {
  activeWorkTab.value = 'conversations'
  await knowledge.loadKnowledgeConversation(conversationId)
}

function startNewConversation() {
  activeWorkTab.value = 'conversations'
  knowledge.startNewConversation()
}

async function deleteConversation(conversationId: string) {
  await knowledge.deleteKnowledgeConversation(conversationId)
}

async function reindexActiveKnowledgeBase() {
  if (!activeKnowledgeBaseId.value) return
  await knowledge.reindexKnowledgeBase(activeKnowledgeBaseId.value)
}
</script>

<template>
  <component
    :is="layout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
    page-title="RAG 知识问答"
  >
    <div class="grid grid-cols-[300px_minmax(0,1fr)] gap-4 max-lg:grid-cols-1">
      <NCard size="small" class="min-w-0">
        <KnowledgeBaseSidebar
          :active-kb-id="activeKnowledgeBaseId"
          :knowledge-bases="knowledgeBases"
          :loading="knowledgeOperationLoading"
          @create="openCreateManager"
          @delete="deleteKnowledgeBase"
          @edit="openEditManager"
          @select="selectKnowledgeBase"
        />
      </NCard>

      <NCard size="small" class="min-w-0">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div class="min-w-0">
            <h1 class="m-0 truncate text-ink text-18px font-800">
              {{ activeKnowledgeBase?.name || '选择或创建知识库' }}
            </h1>
            <p class="m-0 mt-1 text-sub text-12px">
              {{ activeKnowledgeBase?.category || '未分类' }} ·
              {{ activeKnowledgeBase?.document_count ?? 0 }} 文档 ·
              {{ activeKnowledgeBase?.freshness_policy === 'on_file_update' ? '文件更新时刷新' : '手动刷新' }}
            </p>
          </div>
          <NButton
            size="small"
            secondary
            :disabled="!activeKnowledgeBaseId"
            :loading="reindexingActiveKnowledgeBase"
            @click="reindexActiveKnowledgeBase"
          >
            重建索引
          </NButton>
        </div>

        <NTabs v-model:value="activeWorkTab" type="line" animated>
          <NTabPane name="files" tab="文件管理">
            <div class="pt-2">
              <KnowledgeFilePicker
                :active-kb-id="activeKnowledgeBaseId"
                :adding="addingKnowledgeDocument"
                :documents="activeKnowledgeDocuments"
                :files="indexedFiles"
                :loading="knowledgeOperationLoading"
                :removing="knowledgeOperationLoading"
                @batch-add="batchAddFiles"
                @batch-remove="batchRemoveFiles"
              />
            </div>
          </NTabPane>

          <NTabPane name="conversations" tab="对话记录">
            <div class="pt-2">
              <KnowledgeConversationPanel
                :active-conversation-id="activeConversationId"
                :active-kb-id="activeKnowledgeBaseId"
                :asking="askingQuestion"
                :conversations="activeConversations"
                :deleting-conversation-id="deletingConversationId"
                :loading="conversationLoading"
                :messages="activeMessages"
                @ask-question="askQuestion"
                @delete-conversation="deleteConversation"
                @select-conversation="selectConversation"
                @start-new-conversation="startNewConversation"
              />
            </div>
          </NTabPane>
        </NTabs>
      </NCard>
    </div>

    <NModal v-model:show="managerVisible" preset="card" class="max-w-680px" title="知识库配置">
      <KnowledgeBaseManager
        :knowledge-base="editingKnowledgeBase"
        :loading="knowledgeOperationLoading || deletingKnowledgeBaseId === editingKnowledgeBase?.id"
        :mode="managerMode"
        @archive="archiveKnowledgeBase"
        @create="createKnowledgeBase"
        @delete="deleteKnowledgeBase"
        @update="updateKnowledgeBase"
      />
    </NModal>
  </component>
</template>
