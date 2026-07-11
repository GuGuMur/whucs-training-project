import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type {
  WorkspaceFile,
  WorkspaceKnowledgeDocument,
} from '@/client/workspace'
import KnowledgeFilePicker from '@/components/rag/KnowledgeFilePicker.vue'

function createFile(overrides: Partial<WorkspaceFile> = {}): WorkspaceFile {
  return {
    folder_id: 'personal-root',
    id: 'file-course',
    knowledge_base_ids: [],
    name: '课程大纲.md',
    parse_status: 'indexed',
    permission_scope: '个人',
    sha256: 'sha-course',
    size: 128,
    tags: ['课程'],
    type: 'md',
    updated_at: '2026-07-11T08:00:00+08:00',
    ...overrides,
  }
}

function createDocument(overrides: Partial<WorkspaceKnowledgeDocument> = {}): WorkspaceKnowledgeDocument {
  return {
    chunk_count: 3,
    error_message: null,
    file_id: 'file-course',
    file_name: '课程大纲.md',
    id: 'doc-course',
    index_status: 'indexed',
    kb_id: 'kb-course',
    updated_at: '2026-07-11T08:05:00+08:00',
    ...overrides,
  }
}

describe('KnowledgeFilePicker', () => {
  it('emits batch add with selected indexed files', async () => {
    const wrapper = shallowMount(KnowledgeFilePicker, {
      props: {
        activeKbId: 'kb-course',
        documents: [],
        files: [
          createFile(),
          createFile({ id: 'file-not-ready', name: '未解析.txt', parse_status: 'failed' }),
        ],
      },
    })

    await wrapper.find('[data-testid="select-file-file-course"]').trigger('click')
    await wrapper.find('[data-testid="batch-add-files"]').trigger('click')

    expect(wrapper.emitted('batch-add')).toEqual([[['file-course']]])
  })

  it('emits batch remove for selected knowledge documents', async () => {
    const wrapper = shallowMount(KnowledgeFilePicker, {
      props: {
        activeKbId: 'kb-course',
        documents: [createDocument()],
        files: [],
      },
    })

    await wrapper.find('[data-testid="select-document-file-course"]').trigger('click')
    await wrapper.find('[data-testid="batch-remove-files"]').trigger('click')

    expect(wrapper.emitted('batch-remove')).toEqual([[['file-course']]])
  })

  it('shows index status labels for documents', () => {
    const wrapper = shallowMount(KnowledgeFilePicker, {
      props: {
        activeKbId: 'kb-course',
        documents: [createDocument({ index_status: 'failed', error_message: '解析失败' })],
        files: [createFile({ parse_status: 'indexed' })],
      },
    })

    expect(wrapper.text()).toContain('索引失败')
    expect(wrapper.text()).toContain('解析失败')
  })
})
