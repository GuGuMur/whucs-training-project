import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import type {
  WorkspaceWorkflow,
  WorkspaceWorkflowCreateInput,
  WorkspaceWorkflowValidation,
} from '@/client/workspace'
import AgentWorkflowPanel from '../AgentWorkflowPanel.vue'

const workflow: WorkspaceWorkflow = {
  description: '汇总团队文件并生成 Markdown 周报',
  edges: [
    { id: 'edge-input-search', source: 'input', target: 'search' },
    { id: 'edge-search-report', source: 'search', target: 'report' },
  ],
  id: 'workflow-weekly',
  name: '团队周报生成',
  node_count: 3,
  nodes: [
    {
      id: 'input',
      name: '选择团队文件',
      parameters: { source: 'team-folder' },
      type: 'trigger',
    },
    {
      id: 'search',
      name: '检索文件',
      parameters: { query: '周报' },
      tool_name: 'file_search',
      type: 'tool',
    },
    {
      id: 'report',
      name: '生成周报',
      parameters: { format: 'markdown' },
      tool_name: 'report_generate',
      type: 'tool',
    },
  ],
  status: 'draft',
  trigger: 'manual',
  version: '0.1.0',
}

const validation: WorkspaceWorkflowValidation = {
  edge_count: 2,
  issues: [],
  node_count: 3,
  valid: true,
}

function mountPanel() {
  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(AgentWorkflowPanel, {
            activeWorkflowId: 'workflow-weekly',
            agentSteps: [],
            files: [],
            knowledgeBases: [
              {
                chunk_count: 1,
                description: '需求文档、课程资料和团队协作记录',
                document_count: 1,
                id: 'kb-course',
                name: '软件工程课程知识库',
                status: 'active',
                updated_at: '2026-07-08T08:00:00+08:00',
              },
            ],
            tools: [],
            workflowExecution: null,
            workflowOperationLoading: false,
            workflowValidation: validation,
            workflows: [workflow],
          }),
      }),
  })
  const wrapper = mount(TestHost, {
    global: {
      plugins: [naive],
      stubs: {
        Background: true,
        Controls: true,
        VueFlow: { template: '<div data-testid="workflow-canvas"><slot /></div>' },
      },
    },
  })
  return {
    panel: wrapper.getComponent(AgentWorkflowPanel),
    wrapper,
  }
}

describe('AgentWorkflowPanel', () => {
  it('emits workflow creation, selection, validation, publication, execution, and save events', async () => {
    const { panel, wrapper } = mountPanel()

    await wrapper.get('input[placeholder="流程名称"]').setValue(' 团队周报流程 ')
    await wrapper.get('textarea[placeholder="流程说明"]').setValue(' 自动整理团队目录 ')
    await wrapper.get('[data-testid="submit-create-workflow"]').trigger('click')
    await wrapper.get('[data-testid="select-workflow-workflow-weekly"]').trigger('click')
    await wrapper.get('textarea[placeholder="流程描述"]').setValue(' 汇总团队文件并输出 Markdown ')
    await wrapper.get('[data-testid="save-workflow-workflow-weekly"]').trigger('click')
    await wrapper.get('[data-testid="validate-workflow-workflow-weekly"]').trigger('click')
    await wrapper.get('[data-testid="publish-workflow-workflow-weekly"]').trigger('click')
    await wrapper.get('[data-testid="execute-workflow-workflow-weekly"]').trigger('click')

    const createPayload = panel.emitted('create-workflow')?.[0]?.[0] as WorkspaceWorkflowCreateInput | undefined
    if (!createPayload) {
      throw new Error('create-workflow event was not emitted')
    }
    expect(createPayload).toMatchObject({
      description: '自动整理团队目录',
      name: '团队周报流程',
      trigger: 'manual',
    })
    expect(createPayload.nodes).toHaveLength(4)
    expect(createPayload.edges).toHaveLength(3)
    expect(panel.emitted('select-workflow')?.[0]).toEqual(['workflow-weekly'])
    expect(panel.emitted('update-workflow')?.[0]).toEqual([
      'workflow-weekly',
      {
        description: '汇总团队文件并输出 Markdown',
        edges: workflow.edges,
        name: workflow.name,
        nodes: workflow.nodes,
        trigger: workflow.trigger,
      },
    ])
    expect(panel.emitted('validate-workflow')?.[0]).toEqual(['workflow-weekly'])
    expect(panel.emitted('publish-workflow')?.[0]).toEqual(['workflow-weekly'])
    expect(panel.emitted('execute-workflow')?.[0]).toEqual([
      'workflow-weekly',
      { fileId: 'file-microscope', targetKbId: 'kb-course' },
    ])
  })

  it('renders the workflow canvas, validation state, and tool timeline', () => {
    const { wrapper } = mountPanel()

    expect(wrapper.find('[data-testid="workflow-canvas"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('校验通过')
    expect(wrapper.text()).toContain('团队周报生成')
    expect(wrapper.text()).toContain('report_generate')
  })
})
