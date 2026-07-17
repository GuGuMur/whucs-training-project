import { mount } from '@vue/test-utils'
import naive, { NTimelineItem } from 'naive-ui'
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
