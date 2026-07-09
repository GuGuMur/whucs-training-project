import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import type { WorkspaceFolder } from '@/client/workspace'
import FolderTreePanel from '../FolderTreePanel.vue'

const folders: WorkspaceFolder[] = [
  {
    id: 'personal-root',
    name: '个人文件',
    parent_id: null,
    permission: '个人',
    scope: 'personal',
    children: [
      {
        id: 'folder-biology',
        name: '生物学实验',
        parent_id: 'personal-root',
        permission: '个人',
        scope: 'personal',
        children: [],
      },
    ],
  },
  {
    id: 'team-root',
    name: '团队文件',
    parent_id: null,
    permission: '团队',
    scope: 'team',
    children: [],
  },
]

function mountPanel(props: Partial<InstanceType<typeof FolderTreePanel>['$props']> = {}) {
  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(FolderTreePanel, {
            activeFolderId: 'folder-biology',
            folders,
            ...props,
          }),
      }),
  })

  const wrapper = mount(TestHost, { global: { plugins: [naive] } })
  return {
    panel: wrapper.getComponent(FolderTreePanel),
    wrapper,
  }
}

describe('FolderTreePanel', () => {
  it('renders the folder tree and active breadcrumbs', () => {
    const { wrapper } = mountPanel()

    expect(wrapper.text()).toContain('个人文件')
    expect(wrapper.text()).toContain('生物学实验')
    expect(wrapper.text()).toContain('团队文件')
    expect(wrapper.get('[data-testid="folder-breadcrumbs"]').text()).toContain('个人文件')
    expect(wrapper.get('[data-testid="folder-breadcrumbs"]').text()).toContain('生物学实验')
  })

  it('emits the selected folder id from a visible folder row', async () => {
    const { panel, wrapper } = mountPanel()

    await wrapper.get('[data-testid="folder-node-team-root"]').trigger('click')

    expect(panel.emitted('select-folder')?.[0]).toEqual(['team-root'])
  })

  it('emits a create payload from the create folder form', async () => {
    const { panel, wrapper } = mountPanel({ activeFolderId: 'personal-root' })

    await wrapper.get('[data-testid="open-create-folder"]').trigger('click')
    await wrapper.get('input[placeholder="文件夹名称"]').setValue(' 观察记录 ')
    await wrapper.get('[data-testid="submit-create-folder"]').trigger('click')

    expect(panel.emitted('create-folder')?.[0]?.[0]).toEqual({
      name: '观察记录',
      parentId: 'personal-root',
      scope: 'personal',
    })
  })

  it('emits rename and delete actions for the active folder', async () => {
    const { panel, wrapper } = mountPanel()

    await wrapper.get('input[placeholder="重命名目录"]').setValue(' 实验归档 ')
    await wrapper.get('[data-testid="submit-update-folder"]').trigger('click')
    await wrapper.get('[data-testid="delete-folder-folder-biology"]').trigger('click')

    expect(panel.emitted('update-folder')?.[0]).toEqual([
      'folder-biology',
      {
        name: '实验归档',
        parentId: 'personal-root',
      },
    ])
    expect(panel.emitted('delete-folder')?.[0]).toEqual(['folder-biology'])
  })
})
