import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { WorkspaceFile } from '@/client/workspace'
import FileWorkbench from '@/components/files/FileWorkbench.vue'
import FileDropdown from '@/components/files/FileDropdown.vue'

function createFile(overrides: Partial<WorkspaceFile> = {}): WorkspaceFile {
  return {
    id: 'file-reparse',
    name: '待解析资料.txt',
    folder_id: 'personal-root',
    type: 'txt',
    size: 24,
    sha256: 'abc123',
    permission_scope: '个人',
    parse_status: 'failed',
    tags: ['解析'],
    knowledge_base_ids: [],
    updated_at: '2026-07-10T13:00:00+08:00',
    ...overrides,
  }
}

describe('FileWorkbench', () => {
  it('emits reparse-file when the row reparse action is selected', async () => {
    const file = createFile()
    const wrapper = shallowMount(FileWorkbench, {
      props: {
        activeFolderId: null,
        files: [file],
        folders: [],
      },
    })

    wrapper.findComponent(FileDropdown).vm.$emit('reparse', file)
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('reparse-file')).toEqual([[file]])
  })

  it('opens preview by loading file content from the row action', async () => {
    const file = createFile({ parse_status: 'indexed' })
    const wrapper = shallowMount(FileWorkbench, {
      props: {
        activeFolderId: null,
        files: [file],
        folders: [],
      },
    })

    wrapper.findComponent(FileDropdown).vm.$emit('preview', file)
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('load-file-content')).toEqual([[file.id]])
  })

  it('passes the reparsing row state to the row dropdown', () => {
    const file = createFile()
    const wrapper = shallowMount(FileWorkbench, {
      props: {
        activeFolderId: null,
        files: [file],
        folders: [],
        reparsingFileId: file.id,
      },
    })

    expect(wrapper.findComponent(FileDropdown).props('reparsing')).toBe(true)
  })
})
