import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { saveWorkspaceSession } from '@/auth'
import * as workspaceClient from '@/client/workspace'
import type {
  WorkspaceFile,
  WorkspaceKnowledgeBase,
  WorkspaceKnowledgeDocument,
} from '@/client/workspace'
import { useWorkspaceStore } from '@/stores/workspace'
import { useKnowledgeStore } from '@/stores/knowledge'

const knowledgeBase: WorkspaceKnowledgeBase = {
  category: '教学资料',
  chunk_count: 2,
  description: '课程资料库',
  document_count: 1,
  freshness_policy: 'manual',
  id: 'kb-course',
  last_indexed_at: null,
  name: '课程知识库',
  scope_id: null,
  scope_type: 'personal',
  status: 'active',
  tags: ['课程', '期末'],
  updated_at: '2026-07-11T08:00:00+08:00',
}

const knowledgeDocument: WorkspaceKnowledgeDocument = {
  chunk_count: 2,
  error_message: null,
  file_id: 'file-course',
  file_name: '课程大纲.md',
  id: 'doc-course',
  index_status: 'indexed',
  kb_id: 'kb-course',
  updated_at: '2026-07-11T08:05:00+08:00',
}

function createIndexedFile(overrides: Partial<WorkspaceFile>): WorkspaceFile {
  return {
    folder_id: 'personal-root',
    id: 'file-personal',
    knowledge_base_ids: [],
    name: '个人资料.txt',
    parse_status: 'indexed',
    permission_scope: '个人',
    sha256: 'sha-file',
    size: 128,
    tags: [],
    type: 'txt',
    updated_at: '2026-07-11T08:00:00+08:00',
    ...overrides,
  }
}

function saveSession() {
  saveWorkspaceSession({
    accessToken: 'access-token',
    displayName: '小明',
    refreshToken: 'refresh-token',
    userId: '1',
  })
}

describe('knowledge store refactor actions', () => {
  beforeEach(() => {
    window.localStorage.clear()
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('creates knowledge bases with scope, category, tags, and freshness policy', async () => {
    saveSession()
    const createSpy = vi.spyOn(workspaceClient, 'createKnowledgeBase').mockResolvedValue(knowledgeBase)
    const knowledge = useKnowledgeStore()

    await knowledge.createKnowledgeBase({
      category: ' 教学资料 ',
      description: ' 课程资料库 ',
      freshnessPolicy: 'on_file_update',
      name: ' 课程知识库 ',
      scopeId: null,
      scopeType: 'personal',
      tags: [' 课程 ', '期末', '课程', ''],
    } as never)

    expect(createSpy).toHaveBeenCalledWith('access-token', {
      category: '教学资料',
      description: '课程资料库',
      freshnessPolicy: 'on_file_update',
      name: '课程知识库',
      scopeId: null,
      scopeType: 'personal',
      tags: ['课程', '期末'],
    })
    expect(knowledge.knowledgeBases[0]).toEqual(knowledgeBase)
  })

  it('creates team scoped knowledge bases with normalized team metadata', async () => {
    saveSession()
    const teamKnowledgeBase: WorkspaceKnowledgeBase = {
      ...knowledgeBase,
      id: 'kb-team-course',
      scope_id: 'team-biology',
      scope_type: 'team',
    }
    const createSpy = vi.spyOn(workspaceClient, 'createKnowledgeBase').mockResolvedValue(teamKnowledgeBase)
    const knowledge = useKnowledgeStore()

    await knowledge.createKnowledgeBase({
      category: ' 团队资料 ',
      description: ' 生物组共享资料 ',
      freshnessPolicy: 'manual',
      name: ' 团队知识库 ',
      scopeId: 'team-biology',
      scopeType: 'team',
      tags: ['共享'],
    })

    expect(createSpy).toHaveBeenCalledWith('access-token', {
      category: '团队资料',
      description: '生物组共享资料',
      freshnessPolicy: 'manual',
      name: '团队知识库',
      scopeId: 'team-biology',
      scopeType: 'team',
      tags: ['共享'],
    })
    expect(knowledge.activeKnowledgeBaseId).toBe('kb-team-course')
  })

  it('updates category and tags then deletes the knowledge base', async () => {
    saveSession()
    const updatedKnowledgeBase = {
      ...knowledgeBase,
      category: '复习资料',
      tags: ['复习', '重点'],
    }
    const updateSpy = vi.spyOn(workspaceClient, 'updateKnowledgeBase').mockResolvedValue(updatedKnowledgeBase)
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteKnowledgeBase').mockResolvedValue()
    const knowledge = useKnowledgeStore()
    knowledge.knowledgeBases = [knowledgeBase]
    knowledge.activeKnowledgeBaseId = knowledgeBase.id
    knowledge.knowledgeDocumentsByKbId = { [knowledgeBase.id]: [knowledgeDocument] }

    await knowledge.updateKnowledgeBase(knowledgeBase.id, {
      category: ' 复习资料 ',
      tags: ['复习', '重点', '复习'],
    })
    await knowledge.deleteKnowledgeBase(knowledgeBase.id)

    expect(updateSpy).toHaveBeenCalledWith('access-token', knowledgeBase.id, {
      category: '复习资料',
      tags: ['复习', '重点'],
    })
    expect(deleteSpy).toHaveBeenCalledWith('access-token', knowledgeBase.id)
    expect(knowledge.knowledgeBases).toEqual([])
    expect(knowledge.knowledgeDocumentsByKbId[knowledgeBase.id]).toBeUndefined()
  })

  it('batch adds and removes files while keeping document membership current', async () => {
    saveSession()
    const addedDocument = { ...knowledgeDocument, id: 'doc-added', file_id: 'file-added' }
    const batchAddSpy = vi
      .spyOn(workspaceClient, 'batchAddKnowledgeFiles')
      .mockResolvedValue({ added: [addedDocument], removed: [], skipped: [] })
    const batchRemoveSpy = vi
      .spyOn(workspaceClient, 'batchRemoveKnowledgeFiles')
      .mockResolvedValue({ added: [], removed: ['file-added'], skipped: [] })
    const knowledge = useKnowledgeStore()
    knowledge.knowledgeBases = [knowledgeBase]
    knowledge.knowledgeDocumentsByKbId = {
      'kb-course': [knowledgeDocument],
    }

    await knowledge.batchAddKnowledgeFiles('kb-course', ['file-added'])
    await knowledge.batchRemoveKnowledgeFiles('kb-course', ['file-added'])

    expect(batchAddSpy).toHaveBeenCalledWith('access-token', 'kb-course', ['file-added'])
    expect(batchRemoveSpy).toHaveBeenCalledWith('access-token', 'kb-course', ['file-added'])
    expect(knowledge.knowledgeDocumentsByKbId['kb-course']).toEqual([knowledgeDocument])
  })

  it('reindexes a knowledge base and exposes the queued status', async () => {
    saveSession()
    const reindexSpy = vi
      .spyOn(workspaceClient, 'reindexKnowledgeBase')
      .mockResolvedValue({ kb_id: 'kb-course', status: 'queued' })
    const knowledge = useKnowledgeStore()

    const result = await knowledge.reindexKnowledgeBase('kb-course')

    expect(reindexSpy).toHaveBeenCalledWith('access-token', 'kb-course')
    expect(result).toEqual({ kb_id: 'kb-course', status: 'queued' })
    expect(knowledge.reindexingKnowledgeBaseId).toBeNull()
  })

  it('filters addable indexed files by the active knowledge base scope', () => {
    const knowledge = useKnowledgeStore()
    const workspace = useWorkspaceStore()
    const teamKnowledgeBase: WorkspaceKnowledgeBase = {
      ...knowledgeBase,
      id: 'kb-team-course',
      scope_id: 'team-course',
      scope_type: 'team',
    }
    const personalFile = createIndexedFile({
      folder_id: 'personal-root',
      id: 'file-personal',
      name: '个人资料.txt',
      permission_scope: '个人',
    })
    const teamFile = createIndexedFile({
      folder_id: 'folder-team-team-course',
      id: 'file-team',
      name: '团队资料.txt',
      permission_scope: '团队',
    })

    workspace.snapshot = {
      audit_logs: [],
      files: [personalFile, teamFile],
      summary: {
        file_count: 2,
        indexed_count: 2,
        knowledge_base_count: 2,
        running_workflows: 0,
        tools_enabled: 0,
        unread_notifications: 0,
      },
      teams: [],
      tools: [],
      workflows: [],
    }
    knowledge.knowledgeBases = [knowledgeBase, teamKnowledgeBase]

    knowledge.activeKnowledgeBaseId = knowledgeBase.id
    expect(knowledge.indexedFiles.map((file) => file.id)).toEqual(['file-personal'])

    knowledge.activeKnowledgeBaseId = teamKnowledgeBase.id
    expect(knowledge.indexedFiles.map((file) => file.id)).toEqual(['file-team'])
  })

  it('loads conversation summaries and detail messages', async () => {
    saveSession()
    const conversation = {
      id: 'conv-course',
      kb_id: 'kb-course',
      message_count: 2,
      title: '课程考核方式',
      updated_at: '2026-07-11T08:10:00+08:00',
    }
    const userMessage = {
      citations: [],
      content: '怎么考核？',
      conversation_id: 'conv-course',
      created_at: '2026-07-11T08:09:00+08:00',
      id: 'msg-user',
      role: 'user' as const,
    }
    const assistantMessage = {
      citations: [],
      content: '平时成绩和期末考试共同组成。',
      conversation_id: 'conv-course',
      created_at: '2026-07-11T08:10:00+08:00',
      id: 'msg-assistant',
      role: 'assistant' as const,
    }
    const listSpy = vi
      .spyOn(workspaceClient, 'listKnowledgeConversations')
      .mockResolvedValue({ items: [conversation] })
    const detailSpy = vi
      .spyOn(workspaceClient, 'getKnowledgeConversation')
      .mockResolvedValue({ conversation, messages: [userMessage, assistantMessage] })
    const knowledge = useKnowledgeStore()

    await knowledge.loadKnowledgeConversations('kb-course')
    await knowledge.loadKnowledgeConversation('conv-course')

    expect(listSpy).toHaveBeenCalledWith('access-token', 'kb-course')
    expect(detailSpy).toHaveBeenCalledWith('access-token', 'conv-course')
    expect(knowledge.knowledgeConversationsByKbId['kb-course']).toEqual([conversation])
    expect(knowledge.knowledgeMessagesByConversationId['conv-course']).toEqual([
      userMessage,
      assistantMessage,
    ])
  })

  it('starts a new conversation and deletes an old conversation from local state', async () => {
    saveSession()
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteKnowledgeConversation').mockResolvedValue()
    const conversation = {
      id: 'conv-course',
      kb_id: 'kb-course',
      message_count: 2,
      title: '课程考核方式',
      updated_at: '2026-07-11T08:10:00+08:00',
    }
    const knowledge = useKnowledgeStore()
    knowledge.activeConversationId = conversation.id
    knowledge.knowledgeConversationsByKbId = { 'kb-course': [conversation] }
    knowledge.knowledgeMessagesByConversationId = {
      [conversation.id]: [
        {
          citations: [],
          content: '怎么考核？',
          conversation_id: conversation.id,
          created_at: '2026-07-11T08:09:00+08:00',
          id: 'msg-user',
          role: 'user',
        },
      ],
    }

    knowledge.startNewConversation()
    expect(knowledge.activeConversationId).toBeNull()

    knowledge.activeConversationId = conversation.id
    await knowledge.deleteKnowledgeConversation(conversation.id)

    expect(deleteSpy).toHaveBeenCalledWith('access-token', conversation.id)
    expect(knowledge.activeConversationId).toBeNull()
    expect(knowledge.knowledgeConversationsByKbId['kb-course']).toEqual([])
    expect(knowledge.knowledgeMessagesByConversationId[conversation.id]).toBeUndefined()
  })

  it('asks a question and stores the returned conversation id for follow-up turns', async () => {
    saveSession()
    const askSpy = vi.spyOn(workspaceClient, 'askWorkspaceQuestion').mockResolvedValue({
      answer: '平时成绩和期末考试共同组成。',
      citations: [
        {
          chunk_id: 'chunk-course',
          document_id: 'doc-course',
          file_id: 'file-course',
          page_no: 1,
          paragraph_no: 2,
          snippet: '平时成绩占 40%，期末考试占 60%。',
          title: '课程大纲.md',
        },
      ],
      conversation_id: 'conv-course',
      message_id: 'msg-assistant',
    })
    const knowledge = useKnowledgeStore()

    await knowledge.askKnowledgeQuestion({
      kbId: 'kb-course',
      question: ' 这门课怎么考核？ ',
      topK: 3,
    })
    await knowledge.askKnowledgeQuestion({
      kbId: 'kb-course',
      question: ' 那补考呢？ ',
    })

    expect(askSpy).toHaveBeenNthCalledWith(1, 'access-token', {
      conversationId: null,
      kbId: 'kb-course',
      question: '这门课怎么考核？',
      topK: 3,
    })
    expect(askSpy).toHaveBeenNthCalledWith(2, 'access-token', {
      conversationId: 'conv-course',
      kbId: 'kb-course',
      question: '那补考呢？',
      topK: 5,
    })
    expect(knowledge.activeConversationId).toBe('conv-course')
    expect(knowledge.narrative.answer).toContain('平时成绩')
    expect(knowledge.narrative.citations[0]?.title).toBe('课程大纲.md')
  })
})
