import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import { demoWorkspaceSnapshot, type WorkspaceKnowledgeBase, type WorkspaceKnowledgeDocument } from '@/client/workspace'
import RagInsightPanel from '../RagInsightPanel.vue'

const knowledgeBase: WorkspaceKnowledgeBase = {
  chunk_count: 1,
  description: '算法课程实验记录',
  document_count: 1,
  id: 'kb-algo',
  name: '算法实验知识库',
  status: 'active',
  updated_at: '2026-07-08T08:00:00+08:00',
}

const knowledgeDocument: WorkspaceKnowledgeDocument = {
  chunk_count: 1,
  file_id: 'file-microscope',
  file_name: '显微镜实验报告.pdf',
  id: 'doc-kb-algo-file-microscope',
  index_status: 'indexed',
  kb_id: 'kb-algo',
  updated_at: '2026-07-08T08:05:00+08:00',
}

function mountPanel() {
  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(RagInsightPanel, {
            activeKnowledgeBaseId: 'kb-algo',
            addingKnowledgeDocument: false,
            askingQuestion: false,
            indexedFiles: demoWorkspaceSnapshot.files,
            knowledgeBases: [knowledgeBase],
            knowledgeDocuments: [knowledgeDocument],
            loadingKnowledge: false,
            narrative: {
              agentSteps: [],
              answer: '归并排序先递归拆分序列，再合并有序子序列。',
              citations: [
                {
                  chunk_id: 'chunk-sort-1',
                  document_id: 'doc-kb-algo-file-microscope',
                  file_id: 'file-microscope',
                  page_no: 1,
                  paragraph_no: 1,
                  snippet: '归并排序先递归拆分序列，再合并有序子序列。',
                  title: '显微镜实验报告.pdf',
                },
              ],
            },
          }),
      }),
  })
  const wrapper = mount(TestHost, { global: { plugins: [naive] } })
  return {
    panel: wrapper.getComponent(RagInsightPanel),
    wrapper,
  }
}

describe('RagInsightPanel', () => {
  it('emits knowledge-base creation, selection, document indexing, and question events', async () => {
    const { panel, wrapper } = mountPanel()

    await wrapper.get('input[placeholder="知识库名称"]').setValue(' 算法复习库 ')
    await wrapper.get('textarea[placeholder="知识库说明"]').setValue(' 期末复习材料 ')
    await wrapper.get('[data-testid="submit-create-kb"]').trigger('click')
    await wrapper.get('[data-testid="select-kb-kb-algo"]').trigger('click')
    await wrapper.get('[data-testid="add-kb-document-file-microscope"]').trigger('click')
    await wrapper.get('textarea[placeholder="输入问题"]').setValue(' 归并排序的步骤是什么？ ')
    await wrapper.get('[data-testid="submit-rag-question"]').trigger('click')

    expect(panel.emitted('create-knowledge-base')?.[0]?.[0]).toEqual({
      description: '期末复习材料',
      name: '算法复习库',
    })
    expect(panel.emitted('select-knowledge-base')?.[0]).toEqual(['kb-algo'])
    expect(panel.emitted('add-knowledge-document')?.[0]).toEqual(['kb-algo', 'file-microscope'])
    expect(panel.emitted('ask-question')?.[0]?.[0]).toEqual({
      kbId: 'kb-algo',
      question: '归并排序的步骤是什么？',
      topK: 5,
    })
  })

  it('renders answer citations and indexed document status', () => {
    const { wrapper } = mountPanel()

    expect(wrapper.text()).toContain('归并排序先递归拆分序列')
    expect(wrapper.text()).toContain('显微镜实验报告.pdf')
    expect(wrapper.text()).toContain('已索引')
  })
})
