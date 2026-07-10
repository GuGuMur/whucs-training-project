import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { requireAccessToken, resolveOptionalAccessToken } from '@/auth'
import {
  addKnowledgeDocument,
  askWorkspaceQuestion,
  batchAddKnowledgeFiles,
  batchRemoveKnowledgeFiles,
  createKnowledgeBase,
  deleteKnowledgeBase,
  deleteKnowledgeConversation,
  getKnowledgeConversation,
  listKnowledgeBases,
  listKnowledgeConversations,
  listKnowledgeDocuments,
  reindexKnowledgeBase as reindexKnowledgeBaseClient,
  updateKnowledgeBase,
  type WorkspaceKnowledgeConversation,
  type WorkspaceKnowledgeConversationDetailResponse,
  type WorkspaceKnowledgeBase,
  type WorkspaceKnowledgeBaseCreateInput,
  type WorkspaceKnowledgeBaseUpdateInput,
  type WorkspaceKnowledgeDocument,
  type WorkspaceKnowledgeFileBatchResponse,
  type WorkspaceKnowledgeMessage,
  type WorkspaceKnowledgeReindexResponse,
  type WorkspaceNarrative,
  type WorkspaceQuestionInput,
} from '@/client/workspace'
import { useWorkspaceStore } from '@/stores/workspace'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const knowledgeBases = shallowRef<WorkspaceKnowledgeBase[]>([])
  const activeKnowledgeBaseId = shallowRef<string | null>(null)
  const activeConversationId = shallowRef<string | null>(null)
  const selectedFileIds = shallowRef<string[]>([])
  const knowledgeDocumentsByKbId = shallowRef<Record<string, WorkspaceKnowledgeDocument[]>>({})
  const knowledgeConversationsByKbId = shallowRef<Record<string, WorkspaceKnowledgeConversation[]>>({})
  const knowledgeMessagesByConversationId = shallowRef<Record<string, WorkspaceKnowledgeMessage[]>>({})
  const narrative = shallowRef<WorkspaceNarrative>({ answer: '', citations: [], agentSteps: [] })

  const knowledgeOperationLoading = shallowRef(false)
  const addingKnowledgeDocument = shallowRef(false)
  const askingQuestion = shallowRef(false)
  const deletingKnowledgeBaseId = shallowRef<string | null>(null)
  const deletingConversationId = shallowRef<string | null>(null)
  const reindexingKnowledgeBaseId = shallowRef<string | null>(null)
  const conversationLoading = shallowRef(false)

  const errorMessage = shallowRef('')

  const activeKnowledgeBase = computed(
    () => knowledgeBases.value.find((kb) => kb.id === activeKnowledgeBaseId.value) ?? null,
  )

  const activeKnowledgeDocuments = computed(() =>
    activeKnowledgeBaseId.value ? knowledgeDocumentsByKbId.value[activeKnowledgeBaseId.value] ?? [] : [],
  )

  const indexedFiles = computed(() => {
    const workspace = useWorkspaceStore()
    const files = workspace.files.filter((file) => file.parse_status === 'indexed')
    const knowledgeBase = activeKnowledgeBase.value
    if (!knowledgeBase) return files
    if (knowledgeBase.scope_type === 'team') {
      const teamRootFolderId = knowledgeBase.scope_id ? `folder-team-${knowledgeBase.scope_id}` : ''
      return files.filter((file) =>
        file.permission_scope === '团队'
        && (!teamRootFolderId || file.folder_id === teamRootFolderId),
      )
    }
    return files.filter((file) => file.permission_scope !== '团队')
  })

  // ── Actions ──

  async function loadKnowledgeBases(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      return { items: knowledgeBases.value }
    }

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listKnowledgeBases(accessToken)
      knowledgeBases.value = cloneKnowledgeBases(response.items)
      ensureActiveKnowledgeBaseSelection()
      return response
    } catch (error) {
      errorMessage.value = '知识库列表加载失败，请稍后重试'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function createKnowledgeBaseAction(payload: WorkspaceKnowledgeBaseCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload = normalizeKnowledgeBaseCreatePayload(payload)

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const created = await createKnowledgeBase(accessToken, nextPayload)
      upsertKnowledgeBase(created, true)
      activeKnowledgeBaseId.value = created.id
      knowledgeDocumentsByKbId.value = {
        ...knowledgeDocumentsByKbId.value,
        [created.id]: knowledgeDocumentsByKbId.value[created.id] ?? [],
      }
      return created
    } catch (error) {
      errorMessage.value = '知识库创建失败，请检查名称后重试'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function updateKnowledgeBaseAction(
    kbId: string,
    payload: WorkspaceKnowledgeBaseUpdateInput,
  ) {
    const accessToken = requireAccessToken()
    const nextPayload = normalizeKnowledgeBaseUpdatePayload(payload)

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const updated = await updateKnowledgeBase(accessToken, kbId, nextPayload)
      upsertKnowledgeBase(updated)
      activeKnowledgeBaseId.value = updated.id
      return updated
    } catch (error) {
      errorMessage.value = '知识库更新失败，请检查分类、标签和权限'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function deleteKnowledgeBaseAction(kbId: string) {
    const accessToken = requireAccessToken()

    deletingKnowledgeBaseId.value = kbId
    errorMessage.value = ''
    try {
      await deleteKnowledgeBase(accessToken, kbId)
      knowledgeBases.value = knowledgeBases.value.filter((item) => item.id !== kbId)
      const { [kbId]: _documents, ...remainingDocuments } = knowledgeDocumentsByKbId.value
      const { [kbId]: _conversations, ...remainingConversations } = knowledgeConversationsByKbId.value
      knowledgeDocumentsByKbId.value = remainingDocuments
      knowledgeConversationsByKbId.value = remainingConversations
      ensureActiveKnowledgeBaseSelection()
    } catch (error) {
      errorMessage.value = '知识库删除失败，请检查管理权限'
      throw error
    } finally {
      deletingKnowledgeBaseId.value = null
    }
  }

  async function loadKnowledgeDocuments(kbId: string, token?: string) {
    const accessToken = requireAccessToken(token)

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listKnowledgeDocuments(accessToken, kbId)
      knowledgeDocumentsByKbId.value = {
        ...knowledgeDocumentsByKbId.value,
        [kbId]: response.items,
      }
      activeKnowledgeBaseId.value = kbId
      return response
    } catch (error) {
      errorMessage.value = '知识库文档加载失败，请稍后重试'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function batchAddKnowledgeFilesAction(
    kbId: string,
    fileIds: string[],
  ): Promise<WorkspaceKnowledgeFileBatchResponse> {
    const accessToken = requireAccessToken()
    const nextFileIds = normalizeIds(fileIds)

    addingKnowledgeDocument.value = true
    errorMessage.value = ''
    try {
      const response = await batchAddKnowledgeFiles(accessToken, kbId, nextFileIds)
      for (const document of response.added ?? []) {
        upsertKnowledgeDocument(kbId, document)
      }
      activeKnowledgeBaseId.value = kbId
      return response
    } catch (error) {
      errorMessage.value = '批量入库失败，请检查文件解析状态和权限'
      throw error
    } finally {
      addingKnowledgeDocument.value = false
    }
  }

  async function batchRemoveKnowledgeFilesAction(
    kbId: string,
    fileIds: string[],
  ): Promise<WorkspaceKnowledgeFileBatchResponse> {
    const accessToken = requireAccessToken()
    const nextFileIds = normalizeIds(fileIds)

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await batchRemoveKnowledgeFiles(accessToken, kbId, nextFileIds)
      removeKnowledgeDocumentsByFileIds(kbId, response.removed ?? nextFileIds)
      activeKnowledgeBaseId.value = kbId
      return response
    } catch (error) {
      errorMessage.value = '批量移除文件失败，请检查知识库权限'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function reindexKnowledgeBase(kbId: string): Promise<WorkspaceKnowledgeReindexResponse> {
    const accessToken = requireAccessToken()

    reindexingKnowledgeBaseId.value = kbId
    errorMessage.value = ''
    try {
      const response = await reindexKnowledgeBaseClient(accessToken, kbId)
      return response
    } catch (error) {
      errorMessage.value = '知识库重建索引失败，请稍后重试'
      throw error
    } finally {
      reindexingKnowledgeBaseId.value = null
    }
  }

  async function loadKnowledgeConversations(kbId: string, token?: string) {
    const accessToken = requireAccessToken(token)

    conversationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listKnowledgeConversations(accessToken, kbId)
      knowledgeConversationsByKbId.value = {
        ...knowledgeConversationsByKbId.value,
        [kbId]: response.items,
      }
      activeKnowledgeBaseId.value = kbId
      if (!response.items.some((conversation) => conversation.id === activeConversationId.value)) {
        activeConversationId.value = null
      }
      return response
    } catch (error) {
      errorMessage.value = '知识库对话列表加载失败，请稍后重试'
      throw error
    } finally {
      conversationLoading.value = false
    }
  }

  async function loadKnowledgeConversation(
    conversationId: string,
    token?: string,
  ): Promise<WorkspaceKnowledgeConversationDetailResponse> {
    const accessToken = requireAccessToken(token)

    conversationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await getKnowledgeConversation(accessToken, conversationId)
      knowledgeMessagesByConversationId.value = {
        ...knowledgeMessagesByConversationId.value,
        [conversationId]: response.messages,
      }
      knowledgeConversationsByKbId.value = {
        ...knowledgeConversationsByKbId.value,
        [response.conversation.kb_id]: upsertConversation(
          knowledgeConversationsByKbId.value[response.conversation.kb_id] ?? [],
          response.conversation,
        ),
      }
      activeKnowledgeBaseId.value = response.conversation.kb_id
      activeConversationId.value = response.conversation.id
      return response
    } catch (error) {
      errorMessage.value = '知识库对话加载失败，请稍后重试'
      throw error
    } finally {
      conversationLoading.value = false
    }
  }

  async function deleteKnowledgeConversationAction(conversationId: string) {
    const accessToken = requireAccessToken()

    deletingConversationId.value = conversationId
    errorMessage.value = ''
    try {
      await deleteKnowledgeConversation(accessToken, conversationId)
      const nextConversationsByKbId = Object.fromEntries(
        Object.entries(knowledgeConversationsByKbId.value).map(([kbId, conversations]) => [
          kbId,
          conversations.filter((conversation) => conversation.id !== conversationId),
        ]),
      )
      const { [conversationId]: _messages, ...remainingMessages } = knowledgeMessagesByConversationId.value
      knowledgeConversationsByKbId.value = nextConversationsByKbId
      knowledgeMessagesByConversationId.value = remainingMessages
      if (activeConversationId.value === conversationId) {
        activeConversationId.value = null
      }
    } catch (error) {
      errorMessage.value = '知识库对话删除失败，请稍后重试'
      throw error
    } finally {
      deletingConversationId.value = null
    }
  }

  async function addKnowledgeDocumentAction(kbId: string, fileId: string) {
    const accessToken = requireAccessToken()

    addingKnowledgeDocument.value = true
    errorMessage.value = ''
    try {
      const document = await addKnowledgeDocument(accessToken, kbId, fileId)
      upsertKnowledgeDocument(kbId, document)
      markFileIndexedInKnowledgeBase(fileId, kbId)
      activeKnowledgeBaseId.value = kbId
      return document
    } catch (error) {
      errorMessage.value = '文档入库失败，请检查文件解析状态和权限'
      throw error
    } finally {
      addingKnowledgeDocument.value = false
    }
  }

  async function askKnowledgeQuestion(payload: WorkspaceQuestionInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceQuestionInput = {
      conversationId: payload.conversationId ?? activeConversationId.value,
      kbId: payload.kbId,
      question: payload.question.trim(),
      topK: payload.topK ?? 5,
    }

    askingQuestion.value = true
    errorMessage.value = ''
    try {
      const response = await askWorkspaceQuestion(accessToken, nextPayload)
      narrative.value = {
        ...narrative.value,
        answer: response.answer,
        citations: response.citations,
      }
      activeConversationId.value = response.conversation_id
      activeKnowledgeBaseId.value = payload.kbId
      return response
    } catch (error) {
      errorMessage.value = '知识库问答失败，请稍后重试'
      throw error
    } finally {
      askingQuestion.value = false
    }
  }

  async function selectKnowledgeBase(kbId: string) {
    if (!knowledgeBases.value.some((kb) => kb.id === kbId)) {
      return
    }
    if (activeKnowledgeBaseId.value !== kbId) {
      activeConversationId.value = null
    }
    activeKnowledgeBaseId.value = kbId
    if (resolveOptionalAccessToken()) {
      await loadKnowledgeDocuments(kbId)
    }
  }

  function startNewConversation() {
    activeConversationId.value = null
  }

  // ── Helpers ──

  function resetKnowledge() {
    knowledgeBases.value = []
    activeKnowledgeBaseId.value = null
    activeConversationId.value = null
    selectedFileIds.value = []
    knowledgeDocumentsByKbId.value = {}
    knowledgeConversationsByKbId.value = {}
    knowledgeMessagesByConversationId.value = {}
    narrative.value = { answer: '', citations: [], agentSteps: [] }
  }

  function ensureActiveKnowledgeBaseSelection() {
    if (!knowledgeBases.value.some((kb) => kb.id === activeKnowledgeBaseId.value)) {
      activeKnowledgeBaseId.value = knowledgeBases.value[0]?.id ?? null
    }
  }

  function upsertKnowledgeBase(knowledgeBase: WorkspaceKnowledgeBase, moveToFront = false) {
    const existing = knowledgeBases.value.some((item) => item.id === knowledgeBase.id)
    knowledgeBases.value = moveToFront
      ? [knowledgeBase, ...knowledgeBases.value.filter((item) => item.id !== knowledgeBase.id)]
      : existing
        ? knowledgeBases.value.map((item) => (item.id === knowledgeBase.id ? knowledgeBase : item))
        : [knowledgeBase, ...knowledgeBases.value]
  }

  function upsertKnowledgeDocument(kbId: string, document: WorkspaceKnowledgeDocument) {
    const currentDocuments = knowledgeDocumentsByKbId.value[kbId] ?? []
    const nextDocuments = [
      document,
      ...currentDocuments.filter((item) => item.id !== document.id),
    ]
    knowledgeDocumentsByKbId.value = {
      ...knowledgeDocumentsByKbId.value,
      [kbId]: nextDocuments,
    }
    const knowledgeBase = knowledgeBases.value.find((item) => item.id === kbId)
    if (knowledgeBase) {
      upsertKnowledgeBase({
        ...knowledgeBase,
        chunk_count: nextDocuments.reduce((sum, item) => sum + item.chunk_count, 0),
        document_count: nextDocuments.length,
        updated_at: document.updated_at,
      })
    }
  }

  function setSelectedFileIds(fileIds: string[]) {
    selectedFileIds.value = normalizeIds(fileIds)
  }

  function removeKnowledgeDocumentsByFileIds(kbId: string, fileIds: string[]) {
    const removeSet = new Set(fileIds)
    const currentDocuments = knowledgeDocumentsByKbId.value[kbId] ?? []
    const nextDocuments = currentDocuments.filter((item) => !removeSet.has(item.file_id))
    knowledgeDocumentsByKbId.value = {
      ...knowledgeDocumentsByKbId.value,
      [kbId]: nextDocuments,
    }
    const knowledgeBase = knowledgeBases.value.find((item) => item.id === kbId)
    if (knowledgeBase) {
      upsertKnowledgeBase({
        ...knowledgeBase,
        chunk_count: nextDocuments.reduce((sum, item) => sum + item.chunk_count, 0),
        document_count: nextDocuments.length,
        updated_at: new Date().toISOString(),
      })
    }
  }

  function normalizeKnowledgeBaseCreatePayload(
    payload: WorkspaceKnowledgeBaseCreateInput,
  ): WorkspaceKnowledgeBaseCreateInput {
    return {
      category: payload.category?.trim() || null,
      description: payload.description?.trim() || null,
      freshnessPolicy: payload.freshnessPolicy ?? 'manual',
      name: payload.name.trim(),
      scopeId: payload.scopeId ?? null,
      scopeType: payload.scopeType ?? 'personal',
      tags: normalizeTags(payload.tags ?? []),
    }
  }

  function normalizeKnowledgeBaseUpdatePayload(
    payload: WorkspaceKnowledgeBaseUpdateInput,
  ): WorkspaceKnowledgeBaseUpdateInput {
    const nextPayload: WorkspaceKnowledgeBaseUpdateInput = {}
    if ('category' in payload) {
      nextPayload.category = payload.category?.trim() || null
    }
    if ('description' in payload) {
      nextPayload.description = payload.description?.trim() || null
    }
    if ('freshnessPolicy' in payload) {
      nextPayload.freshnessPolicy = payload.freshnessPolicy ?? null
    }
    if ('name' in payload) {
      nextPayload.name = payload.name?.trim() || null
    }
    if ('status' in payload) {
      nextPayload.status = payload.status ?? null
    }
    if ('tags' in payload) {
      nextPayload.tags = payload.tags ? normalizeTags(payload.tags) : null
    }
    return nextPayload
  }

  function normalizeTags(tags: string[]): string[] {
    return Array.from(new Set(tags.map((tag) => tag.trim()).filter(Boolean)))
  }

  function normalizeIds(ids: string[]): string[] {
    return Array.from(new Set(ids.map((id) => id.trim()).filter(Boolean)))
  }

  function upsertConversation(
    conversations: WorkspaceKnowledgeConversation[],
    conversation: WorkspaceKnowledgeConversation,
  ) {
    return [
      conversation,
      ...conversations.filter((item) => item.id !== conversation.id),
    ].sort((a, b) => b.updated_at.localeCompare(a.updated_at))
  }

  function markFileIndexedInKnowledgeBase(_fileId: string, _kbId: string) {
    // Cross-store mutation: updates workspace store's snapshot.files.
    // Execute via useWorkspaceStore().snapshot when that ref is exported.
    // For now, the knowledge store tracks document associations independently
    // via knowledgeDocumentsByKbId.
  }

  return {
    // state
    knowledgeBases,
    activeKnowledgeBaseId,
    activeConversationId,
    selectedFileIds,
    knowledgeDocumentsByKbId,
    knowledgeConversationsByKbId,
    knowledgeMessagesByConversationId,
    narrative,
    knowledgeOperationLoading,
    addingKnowledgeDocument,
    askingQuestion,
    deletingKnowledgeBaseId,
    deletingConversationId,
    reindexingKnowledgeBaseId,
    conversationLoading,
    errorMessage,
    // computed
    activeKnowledgeBase,
    activeKnowledgeDocuments,
    indexedFiles,
    // actions
    loadKnowledgeBases,
    createKnowledgeBase: createKnowledgeBaseAction,
    createKnowledgeBaseAction,
    updateKnowledgeBase: updateKnowledgeBaseAction,
    updateKnowledgeBaseAction,
    deleteKnowledgeBase: deleteKnowledgeBaseAction,
    deleteKnowledgeBaseAction,
    loadKnowledgeDocuments,
    addKnowledgeDocumentAction,
    batchAddKnowledgeFiles: batchAddKnowledgeFilesAction,
    batchAddKnowledgeFilesAction,
    batchRemoveKnowledgeFiles: batchRemoveKnowledgeFilesAction,
    batchRemoveKnowledgeFilesAction,
    reindexKnowledgeBase,
    loadKnowledgeConversations,
    loadKnowledgeConversation,
    deleteKnowledgeConversation: deleteKnowledgeConversationAction,
    deleteKnowledgeConversationAction,
    askKnowledgeQuestion,
    selectKnowledgeBase,
    startNewConversation,
    setSelectedFileIds,
    // helpers
    resetKnowledge,
    ensureActiveKnowledgeBaseSelection,
  }
})

// ── Module-level clone helpers ──

function cloneKnowledgeBases(list: WorkspaceKnowledgeBase[]): WorkspaceKnowledgeBase[] {
  return list.map((kb) => ({ ...kb }))
}

function cloneKnowledgeDocumentMap(
  documents: Record<string, WorkspaceKnowledgeDocument[]>,
): Record<string, WorkspaceKnowledgeDocument[]> {
  return Object.fromEntries(
    Object.entries(documents).map(([kbId, items]) => [
      kbId,
      items.map((item) => ({ ...item })),
    ]),
  )
}
