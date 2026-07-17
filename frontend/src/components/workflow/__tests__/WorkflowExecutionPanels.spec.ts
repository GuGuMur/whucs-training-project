import { mount } from '@vue/test-utils'
import naive, { NSelect, NTimelineItem } from 'naive-ui'
import { describe, expect, it } from 'vitest'

import WorkflowDebugPanel from '../WorkflowDebugPanel.vue'
import WorkflowRunPanel from '../WorkflowRunPanel.vue'

describe('workflow execution panels', () => {
  it('shows successful and skipped node counts separately', () => {
    const wrapper = mount(WorkflowRunPanel, {
      global: { plugins: [naive] },
      props: {
        execution: {
          id: 'exec-1', workflow_id: 'wf-1', status: 'completed', output: {},
          node_executions: [
            { node_id: 'condition', name: '条件', tool_name: '', status: 'success', input: {}, output: { branch: 'true' } },
            { node_id: 'false-output', name: '假分支', tool_name: '', status: 'skipped', input: {}, output: {} },
          ],
        },
        inputs: [],
        loading: false,
        values: {},
      },
    })

    expect(wrapper.text()).toContain('成功 1 · 跳过 1')
  })

  it('renders file comparison inputs as file selectors', () => {
    const wrapper = mount(WorkflowRunPanel, {
      global: { plugins: [naive] },
      props: {
        execution: null,
        files: [
          {
            id: 'file-a', name: '基准.txt', folder_id: 'root', type: 'txt', size: 12,
            sha256: 'abc', parse_status: 'indexed', tags: [], updated_at: '2026-07-17T00:00:00Z',
            permission_scope: 'personal', knowledge_base_ids: [],
          },
          {
            id: 'file-b', name: '候选.txt', folder_id: 'root', type: 'txt', size: 13,
            sha256: 'def', parse_status: 'indexed', tags: [], updated_at: '2026-07-17T00:00:00Z',
            permission_scope: 'personal', knowledge_base_ids: [],
          },
        ],
        inputs: [
          { key: 'file_a', label: '选择待比对文件 · file_a' },
          { key: 'file_b', label: '选择待比对文件 · file_b' },
          { key: 'context_lines', label: '选择待比对文件 · context_lines' },
        ],
        loading: false,
        values: {},
      },
    })

    const selects = wrapper.findAllComponents(NSelect)
    expect(selects).toHaveLength(2)
    expect(selects[0]?.props('options')).toEqual([
      { label: '基准.txt · txt', value: 'file-a' },
      { label: '候选.txt · txt', value: 'file-b' },
    ])
    expect(wrapper.findAll('input')).toHaveLength(3)
  })

  it('renders a skipped debug node as an explicit timeline step', () => {
    const wrapper = mount(WorkflowDebugPanel, {
      global: { plugins: [naive] },
      props: {
        loading: false,
        session: null,
        steps: [{
          done: true, step: 2, node_id: 'false-output', node_name: '假分支', status: 'skipped',
          input: {}, output: {}, remaining: 0,
        }],
      },
    })

    expect(wrapper.text()).toContain('2. 假分支')
    expect(wrapper.findComponent(NTimelineItem).props('content')).toBe('skipped · 剩余 0')
  })
})
