import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import type { AuditLogEntry, TeamSummary, WorkspaceNotification, WorkspaceTeamDetail } from '@/client/workspace'
import TeamAuditPanel from '../TeamAuditPanel.vue'

const teams: TeamSummary[] = [
  {
    description: '课程资料协作',
    id: 'team-algo',
    member_count: 2,
    name: '算法课程小组',
    role: 'owner',
    root_folder_id: 'team-algo-root',
    unread_count: 0,
  },
]

const auditLogs: AuditLogEntry[] = [
  {
    action: 'team.create',
    actor: 'xiaoming',
    created_at: '2026-07-08T08:00:00+08:00',
    id: 'audit-1',
    resource_name: '算法课程小组',
    resource_type: 'team',
  },
]

const activeTeamDetail: WorkspaceTeamDetail = {
  description: '课程资料协作',
  id: 'team-algo',
  invites: [],
  member_count: 2,
  members: [
    {
      display_name: '小明',
      email: 'xiaoming@example.com',
      id: 'member-1',
      joined_at: '2026-07-08T08:00:00+08:00',
      role: 'owner',
      status: 'active',
      team_id: 'team-algo',
      user_id: 1,
      username: 'xiaoming',
    },
    {
      display_name: '小红',
      email: 'xiaohong@example.com',
      id: 'member-2',
      joined_at: '2026-07-08T08:00:00+08:00',
      role: 'member',
      status: 'active',
      team_id: 'team-algo',
      user_id: 2,
      username: 'xiaohong',
    },
  ],
  name: '算法课程小组',
  role: 'owner',
  root_folder: {
    children: [],
    id: 'team-algo-root',
    name: '算法课程小组',
    parent_id: null,
    permission: '管理',
    scope: 'team',
    team_id: 'team-algo',
  },
  unread_count: 0,
}

const notifications: WorkspaceNotification[] = [
  {
    content: '李老师回复了 小组周报.docx 的批注',
    created_at: '2026-07-09T12:00:00Z',
    id: 'noti-1',
    is_read: false,
    target_id: 'file-weekly',
    target_type: 'file',
    title: '批注收到回复',
    type: 'annotation',
    user_id: 1,
  },
]

function mountPanel() {
  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(TeamAuditPanel, {
            activeTeamDetail,
            auditLogs,
            markingNotificationId: null,
            notifications,
            notificationsLoading: false,
            teamOperationLoading: false,
            teams,
          }),
      }),
  })
  const wrapper = mount(TestHost, {
    global: {
      plugins: [naive, createPinia()],
      stubs: {
        RouterLink: true,
      },
    },
  })
  return {
    panel: wrapper.getComponent(TeamAuditPanel),
    wrapper,
  }
}

describe('TeamAuditPanel', () => {
  it('emits team creation and team detail loading actions', async () => {
    const { panel, wrapper } = mountPanel()

    await wrapper.get('[data-testid="create-team-name"] input').setValue(' 工程实践小组 ')
    await wrapper.get('[data-testid="create-team-description"] textarea').setValue(' 实验数据共享 ')
    await wrapper.get('[data-testid="submit-create-team"]').trigger('click')
    await wrapper.get('[data-testid="open-team-team-algo"]').trigger('click')

    expect(panel.emitted('create-team')?.[0]?.[0]).toEqual({
      description: '实验数据共享',
      name: '工程实践小组',
    })
    expect(panel.emitted('load-team-detail')?.[0]).toEqual(['team-algo'])
  })

  it('emits invite, role update, and remove-member actions from the member manager', async () => {
    const { panel, wrapper } = mountPanel()

    await wrapper.get('[data-testid="team-invite-email"] input').setValue('xiaohong@example.com')
    await wrapper.get('[data-testid="submit-team-invite"]').trigger('click')
    await wrapper.get('[data-testid="update-team-member-member-2-admin"]').trigger('click')
    await wrapper.get('[data-testid="remove-team-member-member-2"]').trigger('click')

    expect(panel.emitted('invite-team-member')?.[0]).toEqual([
      'team-algo',
      { email: 'xiaohong@example.com', role: 'member' },
    ])
    expect(panel.emitted('update-team-member-role')?.[0]).toEqual(['team-algo', 'member-2', 'admin'])
    expect(panel.emitted('remove-team-member')?.[0]).toEqual(['team-algo', 'member-2'])
  })

  it('forwards notification read actions from the inbox', async () => {
    const { panel, wrapper } = mountPanel()

    expect(wrapper.text()).toContain('批注收到回复')
    await wrapper.get('[data-testid="mark-notification-noti-1-read"]').trigger('click')

    expect(panel.emitted('mark-notification-read')?.[0]).toEqual(['noti-1'])
  })
})
