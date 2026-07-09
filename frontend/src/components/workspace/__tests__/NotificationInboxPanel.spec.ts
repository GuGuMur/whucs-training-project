import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import type { WorkspaceNotification } from '@/client/workspace'
import NotificationInboxPanel from '../NotificationInboxPanel.vue'

const unreadNotification: WorkspaceNotification = {
  content: '李老师回复了 小组周报.docx 的批注',
  created_at: '2026-07-09T12:00:00Z',
  id: 'noti-1',
  is_read: false,
  target_id: 'file-weekly',
  target_type: 'file',
  title: '批注收到回复',
  type: 'annotation',
  user_id: 1,
}

const readNotification: WorkspaceNotification = {
  content: '王老师邀请你加入算法课程小组',
  created_at: '2026-07-09T11:00:00Z',
  id: 'noti-2',
  is_read: true,
  target_id: 'team-algo',
  target_type: 'team',
  title: '团队邀请',
  type: 'invite',
  user_id: 1,
}

function mountPanel() {
  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(NotificationInboxPanel, {
            markingNotificationId: null,
            notifications: [unreadNotification, readNotification],
            notificationsLoading: false,
          }),
      }),
  })
  const wrapper = mount(TestHost, {
    global: {
      plugins: [naive],
    },
  })
  return {
    panel: wrapper.getComponent(NotificationInboxPanel),
    wrapper,
  }
}

describe('NotificationInboxPanel', () => {
  it('renders notifications and emits mark-read for unread items', async () => {
    const { panel, wrapper } = mountPanel()

    expect(wrapper.text()).toContain('批注收到回复')
    expect(wrapper.text()).toContain('李老师回复了 小组周报.docx 的批注')
    expect(wrapper.text()).toContain('团队邀请')

    await wrapper.get('[data-testid="mark-notification-noti-1-read"]').trigger('click')

    expect(panel.emitted('mark-notification-read')?.[0]).toEqual(['noti-1'])
    expect(wrapper.find('[data-testid="mark-notification-noti-2-read"]').exists()).toBe(false)
  })
})
