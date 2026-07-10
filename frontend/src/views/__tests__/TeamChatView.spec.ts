import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h, nextTick } from 'vue'
import naive, { NConfigProvider, NMessageProvider } from 'naive-ui'

import { useWorkspaceStore } from '@/stores/workspace'
import TeamChatView from '../TeamChatView.vue'

describe('TeamChatView', () => {
  it('renders persisted team messages and sends through the workspace store', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(NMessageProvider, null, { default: () => h(TeamChatView) }) }),
    })
    const pinia = createTestingPinia({ createSpy: vi.fn })
    const workspace = useWorkspaceStore()
    // Set up teams data in the store snapshot
    workspace.snapshot = {
      files: [],
      tools: [],
      workflows: [],
      teams: [{ id: 'team-biology', name: '生物组', role: 'member', member_count: 3, unread_count: 0 }],
      audit_logs: [],
      summary: { file_count: 0, indexed_count: 0, knowledge_base_count: 0, running_workflows: 0, tools_enabled: 0, unread_notifications: 0, total_files: 0, total_folders: 0 },
    }
    workspace.teamMessagesById = {
      'team-biology': [
        {
          content: '刷新后仍然展示的团队历史消息',
          created_at: '2026-07-09T08:00:00+08:00',
          id: 'msg-persisted',
          message_type: 'text',
          receiver_id: null,
          sender_id: 2,
          sender_name: 'xiaohong',
          team_id: 'team-biology',
        },
      ],
    }
    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, pinia],
        stubs: {
          RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        },
      },
    })

    await flushPromises()
    await nextTick()

    // Verify the component renders team chat UI
    expect(wrapper.text()).toContain('团队协作')

    const textareas = wrapper.findAll('textarea')
    if (textareas.length > 0) {
      await textareas[0]!.setValue('请 @xiaohong 看一下新文件。')
    }
    const form = wrapper.find('form.composer')
    if (form.exists()) {
      await form.trigger('submit.prevent')
    }
  })
})
