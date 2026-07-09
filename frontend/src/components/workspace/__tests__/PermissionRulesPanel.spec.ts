import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import {
  demoWorkspaceSnapshot,
  demoWorkspaceTeamDetail,
  type WorkspacePermissionRule,
} from '@/client/workspace'
import PermissionRulesPanel from '../PermissionRulesPanel.vue'

describe('PermissionRulesPanel', () => {
  it('shows inherited and direct override rules and emits create/delete actions', async () => {
    const rules: WorkspacePermissionRule[] = [
      createPermissionRule('rule-folder-deny', {
        action: 'read',
        effect: 'deny',
        inherit: true,
        resource_id: 'team-root',
        resource_label: '团队文件',
        resource_type: 'folder',
        subject_id: 'team-biology:guest',
        subject_label: '生物学实验 / 访客',
        subject_type: 'role',
      }),
      createPermissionRule('rule-file-override', {
        action: 'write',
        effect: 'allow',
        inherit: false,
        resource_id: 'file-weekly',
        resource_label: '小组周报.docx',
        resource_type: 'file',
        subject_id: 'team-biology:member',
        subject_label: '生物学实验 / 成员',
        subject_type: 'role',
      }),
    ]
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () =>
            h(PermissionRulesPanel, {
              activeFolderId: 'team-root',
              activeTeamDetail: demoWorkspaceTeamDetail,
              files: demoWorkspaceSnapshot.files,
              folders: [demoWorkspaceTeamDetail.root_folder],
              rules,
            }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const panel = wrapper.getComponent(PermissionRulesPanel)

    expect(wrapper.text()).toContain('权限规则')
    expect(wrapper.text()).toContain('生物学实验 / 访客')
    expect(wrapper.text()).toContain('团队文件')
    expect(wrapper.text()).toContain('继承')
    expect(wrapper.text()).toContain('直接覆盖')
    expect(wrapper.text()).toContain('拒绝')
    expect(wrapper.text()).toContain('允许')

    await wrapper.get('[data-testid="submit-permission-rule"]').trigger('click')
    await wrapper.get('[data-testid="delete-permission-rule-rule-folder-deny"]').trigger('click')

    expect(panel.emitted('create-rule')?.[0]?.[0]).toEqual({
      action: 'read',
      effect: 'deny',
      inherit: true,
      resourceId: 'team-root',
      resourceType: 'folder',
      subjectId: 'team-biology:guest',
      subjectType: 'role',
    })
    expect(panel.emitted('delete-rule')?.[0]).toEqual(['rule-folder-deny'])
  })
})

function createPermissionRule(
  id: string,
  overrides: Omit<WorkspacePermissionRule, 'created_at' | 'created_by' | 'id'>,
): WorkspacePermissionRule {
  return {
    created_at: '2026-07-08T08:00:00+08:00',
    created_by: 'xiaoming',
    id,
    ...overrides,
  }
}
