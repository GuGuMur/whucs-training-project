import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h, nextTick } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import { useWorkspaceStore } from '@/stores/workspace'
import TeamChatView from '../TeamChatView.vue'

describe('TeamChatView', () => {
  it('renders persisted team messages and sends through the workspace store', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(TeamChatView) }),
    })
    const pinia = createTestingPinia({ createSpy: vi.fn })
    const workspace = useWorkspaceStore()
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

    expect(workspace.loadTeamMessages).toHaveBeenCalledWith('team-biology')
    expect(wrapper.text()).toContain('刷新后仍然展示的团队历史消息')

    await wrapper.get('textarea').setValue('请 @xiaohong 看一下新文件。')
    await wrapper.get('form.composer').trigger('submit.prevent')

    expect(workspace.sendTeamMessage).toHaveBeenCalledWith('team-biology', {
      content: '请 @xiaohong 看一下新文件。',
      message_type: 'text',
      receiver_id: null,
    })
  })
})
