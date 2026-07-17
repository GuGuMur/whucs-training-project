import { mount } from '@vue/test-utils'
import naive from 'naive-ui'
import { describe, expect, it } from 'vitest'

import WorkflowNodePalette from '@/components/workflow/WorkflowNodePalette.vue'
import type { ToolDefinition } from '@/client/workspace'

const tool: ToolDefinition = {
  category: 'research',
  description: 'Search recent arXiv papers.',
  enabled: true,
  id: 'arxiv_search',
  input_schema: {
    properties: {
      query: { type: 'string' },
    },
    required: ['query'],
    type: 'object',
  },
  name: 'arxiv_search',
  output_schema: { type: 'object' },
  version: '1.0.0',
}

describe('WorkflowNodePalette', () => {
  it('renders input blocks and enabled tools', () => {
    const wrapper = mount(WorkflowNodePalette, {
      global: { plugins: [naive] },
      props: {
        inputKinds: ['text', 'knowledge_base'],
        tools: [tool],
      },
    })

    expect(wrapper.text()).toContain('文本输入')
    expect(wrapper.text()).toContain('知识库输入')
    expect(wrapper.text()).toContain('arxiv_search')
    expect(wrapper.text()).toContain('query')
    expect(wrapper.text()).toContain('条件分支')
    expect(wrapper.text()).toContain('数组循环')
  })

  it('emits an advanced-node payload', async () => {
    const wrapper = mount(WorkflowNodePalette, { global: { plugins: [naive] }, props: { tools: [] } })
    await wrapper.find('[data-testid="palette-advanced-aggregate"]').trigger('click')
    expect(wrapper.emitted('addNode')?.[0]?.[0]).toEqual({ kind: 'aggregate', label: '数据聚合' })
  })

  it('emits an input payload when a palette item is clicked', async () => {
    const wrapper = mount(WorkflowNodePalette, {
      global: { plugins: [naive] },
      props: { inputKinds: ['json'], tools: [] },
    })

    await wrapper.find('[data-testid="palette-input-json"]').trigger('click')

    const payload = wrapper.emitted('addNode')?.[0]?.[0]
    expect(payload).toMatchObject({
      input: {
        key: 'input_json',
        kind: 'json',
        label: 'JSON 输入',
      },
      kind: 'input',
      label: 'JSON 输入',
    })
  })

  it('writes drag data for tool nodes', async () => {
    const wrapper = mount(WorkflowNodePalette, {
      global: { plugins: [naive] },
      props: { tools: [tool] },
    })
    const data = new Map<string, string>()
    const dataTransfer = {
      effectAllowed: '',
      setData(type: string, value: string) {
        data.set(type, value)
      },
    }

    await wrapper.find('[data-testid="palette-tool-arxiv_search"]').trigger('dragstart', {
      dataTransfer,
    })

    expect(data.get('text/plain')).toBe('arxiv_search')
    expect(JSON.parse(data.get('application/x-whucs-workflow-node') ?? '{}')).toMatchObject({
      kind: 'tool',
      label: 'arxiv_search',
      toolName: 'arxiv_search',
    })
    expect(wrapper.emitted('nodeDragStart')?.[0]?.[0]).toMatchObject({
      kind: 'tool',
      toolName: 'arxiv_search',
    })
  })

  it('renders tools that do not provide a stable id', () => {
    const wrapper = mount(WorkflowNodePalette, {
      global: { plugins: [naive] },
      props: {
        tools: [
          {
            ...tool,
            id: '',
            name: 'kb_interest_extract',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('kb_interest_extract')
    expect(wrapper.find('[data-testid="palette-tool-kb_interest_extract"]').exists()).toBe(true)
  })
})
