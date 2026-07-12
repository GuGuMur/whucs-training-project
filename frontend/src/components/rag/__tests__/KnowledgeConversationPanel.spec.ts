import { mount, shallowMount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'
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
    content: '平时成绩和期末考试共同组成。[来源 1]',
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
    expect(wrapper.html()).toContain('href="#citation-1"')
    expect(wrapper.findComponent(KnowledgeCitationList).props('citations')).toEqual(messages[1]!.citations)
  })

  it('emits ask-question-stream with the current active conversation', async () => {
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

    expect(wrapper.emitted('ask-question-stream')).toEqual([[
      {
        conversationId: conversation.id,
        kbId: 'kb-course',
        question: '还有补考安排吗？',
        topK: 8,
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

  it('renders streaming citation cards while answer is generating', () => {
    const wrapper = shallowMount(KnowledgeConversationPanel, {
      props: {
        activeConversationId: conversation.id,
        activeKbId: 'kb-course',
        isStreaming: true,
        streamingAnswer: '课程考核包含平时作业和期末考试。[来源 1]',
        streamingCitations: [
          {
            chunk_id: 'chunk-stream',
            document_id: 'doc-course',
            file_id: 'file-course',
            page_no: 2,
            paragraph_no: 3,
            snippet: '课程考核包含平时作业和期末考试。',
            title: '课程大纲.md',
          },
        ],
      },
    })

    expect(wrapper.html()).toContain('href="#citation-1"')
    expect(wrapper.findComponent(KnowledgeCitationList).props('citations')).toEqual([
      {
        chunk_id: 'chunk-stream',
        document_id: 'doc-course',
        file_id: 'file-course',
        page_no: 2,
        paragraph_no: 3,
        snippet: '课程考核包含平时作业和期末考试。',
        title: '课程大纲.md',
      },
    ])
  })

  it('does not force-scroll to the bottom while streaming tokens arrive', async () => {
    const scrollTo = vi.fn()
    Object.defineProperty(HTMLElement.prototype, 'scrollTo', {
      configurable: true,
      value: scrollTo,
    })
    const wrapper = mount(KnowledgeConversationPanel, {
      global: {
        plugins: [naive],
      },
      props: {
        activeConversationId: conversation.id,
        activeKbId: 'kb-course',
        isStreaming: true,
        messages,
        streamingAnswer: '课程考核',
      },
    })

    await wrapper.setProps({ streamingAnswer: '课程考核包含平时作业和期末考试。' })
    await nextTick()

    expect(scrollTo).not.toHaveBeenCalled()
  })

  it('reveals the latest submitted question instead of pinning the answer to the bottom', async () => {
    const scrollIntoView = vi.fn()
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView,
    })
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
    const followUp: WorkspaceKnowledgeMessage = {
      citations: [],
      content: '补考怎么安排？',
      conversation_id: conversation.id,
      created_at: '2026-07-11T08:11:00+08:00',
      id: 'msg-user-follow-up',
      role: 'user',
    }

    await wrapper.find('textarea').setValue(followUp.content)
    await wrapper.find('[data-testid="submit-rag-question"]').trigger('click')
    await wrapper.setProps({ messages: [...messages, followUp] })
    await nextTick()

    expect(scrollIntoView).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' })
  })
})
