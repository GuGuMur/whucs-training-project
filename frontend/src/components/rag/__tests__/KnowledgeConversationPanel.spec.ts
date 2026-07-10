import { mount, shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import naive from 'naive-ui'

import type {
  WorkspaceKnowledgeConversation,
  WorkspaceKnowledgeMessage,
} from '@/client/workspace'
import KnowledgeCitationList from '@/components/rag/KnowledgeCitationList.vue'
import KnowledgeConversationPanel from '@/components/rag/KnowledgeConversationPanel.vue'

const conversation: WorkspaceKnowledgeConversation = {
  id: 'conv-course',
  kb_id: 'kb-course',
  message_count: 2,
  title: '考核方式',
  updated_at: '2026-07-11T08:10:00+08:00',
}

const messages: WorkspaceKnowledgeMessage[] = [
  {
    citations: [],
    content: '这门课怎么考核？',
    conversation_id: 'conv-course',
    created_at: '2026-07-11T08:09:00+08:00',
    id: 'msg-user',
    role: 'user',
  },
  {
    citations: [
      {
        chunk_id: 'chunk-1',
        document_id: 'doc-course',
        file_id: 'file-course',
        page_no: 1,
        paragraph_no: 2,
        snippet: '平时成绩占 40%，期末考试占 60%。',
        title: '课程大纲.md',
      },
    ],
    content: '平时成绩和期末考试共同组成。',
    conversation_id: 'conv-course',
    created_at: '2026-07-11T08:10:00+08:00',
    id: 'msg-assistant',
    role: 'assistant',
  },
]

describe('KnowledgeConversationPanel', () => {
  it('renders conversation history and citation snapshots', () => {
    const wrapper = shallowMount(KnowledgeConversationPanel, {
      props: {
        activeConversationId: conversation.id,
        conversations: [conversation],
        messages,
      },
    })

    expect(wrapper.text()).toContain('考核方式')
    expect(wrapper.text()).toContain('这门课怎么考核？')
    expect(wrapper.text()).toContain('平时成绩和期末考试共同组成。')
    expect(wrapper.findComponent(KnowledgeCitationList).props('citations')).toEqual(messages[1]!.citations)
  })

  it('emits ask-question with the current active conversation', async () => {
    const wrapper = mount(KnowledgeConversationPanel, {
      global: {
        plugins: [naive],
      },
      props: {
        activeConversationId: conversation.id,
        activeKbId: 'kb-course',
        conversations: [conversation],
        messages,
      },
    })

    await wrapper.find('textarea').setValue('还有补考安排吗？')
    await wrapper.find('[data-testid="submit-rag-question"]').trigger('click')

    expect(wrapper.emitted('ask-question')).toEqual([[
      {
        conversationId: conversation.id,
        kbId: 'kb-course',
        question: '还有补考安排吗？',
        topK: 5,
      },
    ]])
  })

  it('emits select-conversation when a history item is chosen', async () => {
    const wrapper = shallowMount(KnowledgeConversationPanel, {
      props: {
        conversations: [conversation],
        messages: [],
      },
    })

    await wrapper.find('[data-testid="select-conversation-conv-course"]').trigger('click')

    expect(wrapper.emitted('select-conversation')).toEqual([[conversation.id]])
  })

  it('supports starting a new conversation and deleting old conversations', async () => {
    const wrapper = mount(KnowledgeConversationPanel, {
      global: {
        plugins: [naive],
      },
      props: {
        activeConversationId: conversation.id,
        activeKbId: 'kb-course',
        conversations: [conversation],
        deletingConversationId: null,
        messages,
      },
    })

    await wrapper.find('[data-testid="start-new-conversation"]').trigger('click')
    await wrapper.find('[data-testid="delete-conversation-conv-course"]').trigger('click')

    expect(wrapper.emitted('start-new-conversation')).toEqual([[]])
    expect(wrapper.emitted('delete-conversation')).toEqual([[conversation.id]])
    expect(wrapper.text()).toContain('继续中')
  })
})
