import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import type { WorkspaceFile, WorkspaceFileAnnotation } from '@/client/workspace'
import FileAnnotationPanel from '../FileAnnotationPanel.vue'

const file: WorkspaceFile = {
  id: 'file-weekly',
  folder_id: 'team-root',
  knowledge_base_ids: [],
  name: '小组周报.docx',
  parse_status: 'indexed',
  permission_scope: '团队',
  sha256: 'sha-weekly',
  size: 1200,
  tags: ['团队'],
  type: 'docx',
  updated_at: '2026-07-09T08:00:00+08:00',
}

const annotations: WorkspaceFileAnnotation[] = [
  {
    author_id: 1,
    author_name: 'xiaoming',
    content: '<script>alert(1)</script> 需要补充实验样本',
    created_at: '2026-07-09T08:00:00+08:00',
    file_id: 'file-weekly',
    id: 'anno-1',
    position: { page: 2, selected_text: '实验样本' },
    replies: [
      {
        annotation_id: 'anno-1',
        author_id: 2,
        author_name: 'team-owner',
        content: '已补充来源说明',
        created_at: '2026-07-09T08:10:00+08:00',
        file_id: 'file-weekly',
        id: 'reply-1',
        updated_at: '2026-07-09T08:10:00+08:00',
      },
    ],
    updated_at: '2026-07-09T08:00:00+08:00',
  },
]

describe('FileAnnotationPanel', () => {
  it('renders annotations and emits create, reply, and delete events', async () => {
    const TestHost = defineComponent({
      setup: () => () =>
        h(NConfigProvider, null, {
          default: () => h(FileAnnotationPanel, { annotations, file }),
        }),
    })
    const wrapper = mount(TestHost, { global: { plugins: [naive] } })
    const panel = wrapper.getComponent(FileAnnotationPanel)

    expect(wrapper.text()).toContain('<script>alert(1)</script> 需要补充实验样本')
    expect(wrapper.html()).not.toContain('<script>alert(1)</script><span')
    expect(wrapper.text()).toContain('已补充来源说明')

    await wrapper.get('textarea[placeholder="添加文件批注"]').setValue(' 请确认图表单位 ')
    await wrapper.get('[data-testid="submit-file-annotation"]').trigger('click')
    await wrapper.get('textarea[placeholder="回复批注"]').setValue(' 已确认 ')
    await wrapper.get('[data-testid="reply-annotation-anno-1"]').trigger('click')
    await wrapper.get('[data-testid="delete-annotation-reply-1"]').trigger('click')

    expect(panel.emitted('create-annotation')?.[0]).toEqual([
      'file-weekly',
      { content: '请确认图表单位', position: null },
    ])
    expect(panel.emitted('reply-annotation')?.[0]).toEqual(['anno-1', { content: '已确认' }])
    expect(panel.emitted('delete-annotation')?.[0]).toEqual(['file-weekly', 'reply-1'])
  })
})
