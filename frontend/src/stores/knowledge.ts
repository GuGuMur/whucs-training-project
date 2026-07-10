import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { requireAccessToken, resolveOptionalAccessToken } from '@/auth'
import {
  addKnowledgeDocument,
  askWorkspaceQuestion,
  createKnowledgeBase,
  listKnowledgeBases,
  listKnowledgeDocuments,
  type WorkspaceKnowledgeBase,
  type WorkspaceKnowledgeBaseCreateInput,
  type WorkspaceKnowledgeDocument,
  type WorkspaceNarrative,
  type WorkspaceQuestionInput,
} from '@/client/workspace'
import { useWorkspaceStore } from '@/stores/workspace'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const knowledgeBases = shallowRef<WorkspaceKnowledgeBase[]>([])
  const activeKnowledgeBaseId = shallowRef<string | null>(null)
  const knowledgeDocumentsByKbId = shallowRef<Record<string, WorkspaceKnowledgeDocument[]>>({})
  const narrative = shallowRef<WorkspaceNarrative>({ answer: '', citations: [], agentSteps: [] })

  const knowledgeOperationLoading = shallowRef(false)
  const addingKnowledgeDocument = shallowRef(false)
  const askingQuestion = shallowRef(false)

  const errorMessage = shallowRef('')

  const activeKnowledgeBase = computed(
    () => knowledgeBases.value.find((kb) => kb.id === activeKnowledgeBaseId.value) ?? null,
  )

  const activeKnowledgeDocuments = computed(() =>
    activeKnowledgeBaseId.value ? knowledgeDocumentsByKbId.value[activeKnowledgeBaseId.value] ?? [] : [],
  )

  const indexedFiles = computed(() => {
    const workspace = useWorkspaceStore()
    return workspace.files.filter((file) => file.parse_status === 'indexed')
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
    const nextPayload: WorkspaceKnowledgeBaseCreateInput = {
      description: payload.description?.trim() || null,
      name: payload.name.trim(),
    }

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
      conversationId: payload.conversationId ?? null,
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
    activeKnowledgeBaseId.value = kbId
    if (resolveOptionalAccessToken()) {
      await loadKnowledgeDocuments(kbId)
    }
  }

  // ── Helpers ──

  function resetKnowledge() {
    knowledgeBases.value = []
    activeKnowledgeBaseId.value = null
    knowledgeDocumentsByKbId.value = {}
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
    knowledgeDocumentsByKbId,
    narrative,
    knowledgeOperationLoading,
    addingKnowledgeDocument,
    askingQuestion,
    errorMessage,
    // computed
    activeKnowledgeBase,
    activeKnowledgeDocuments,
    indexedFiles,
    // actions
    loadKnowledgeBases,
    createKnowledgeBase: createKnowledgeBaseAction,
    createKnowledgeBaseAction,
    loadKnowledgeDocuments,
    addKnowledgeDocumentAction,
    askKnowledgeQuestion,
    selectKnowledgeBase,
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
