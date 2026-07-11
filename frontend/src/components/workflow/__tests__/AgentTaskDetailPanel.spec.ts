import { mount } from '@vue/test-utils'
import naive from 'naive-ui'
import { describe, expect, it } from 'vitest'

import type { WorkspaceAgentTask } from '@/client/workspace'
import AgentTaskDetailPanel from '@/components/workflow/AgentTaskDetailPanel.vue'

const task: WorkspaceAgentTask = {
  final_answer: '高等数学周一上课。',
  id: 'task-1',
  messages: [
    { id: 'msg-1', role: 'user', content: '查询高等数学上课时间' },
    { id: 'msg-2', role: 'assistant', content: '高等数学周一上课。' },
    { id: 'msg-3', role: 'system', content: '历史摘要：用户一直在查课程', metadata: { kind: 'history_summary' } },
  ],
  plan_revisions: [
    {
      id: 'plan-1',
      plan_json: { plan_steps: [{ tool_name: 'course_lookup' }] },
      reason: '任务规划',
      revision_no: 0,
    },
  ],
  result_view: { type: 'text', content: '高等数学周一上课。' },
  status: 'completed',
  steps: [],
  task: '查询课程',
  tool_calls: [
    {
      id: 'call-1',
      input_json: { query: '高等数学' },
      latency_ms: 15,
      output_json: { time: '周一' },
      status: 'success',
      tool_name: 'course_lookup',
    },
  ],
}

describe('AgentTaskDetailPanel', () => {
  it('renders messages, tool calls, and plan revisions', async () => {
    const wrapper = mount(AgentTaskDetailPanel, {
      global: { plugins: [naive] },
      props: { activeTask: task, taskHistory: [task] },
    })

    expect(wrapper.text()).toContain('高等数学周一上课')
    expect(wrapper.text()).toContain('历史摘要')
    expect(wrapper.text()).toContain('对话')
    expect(wrapper.text()).toContain('工具耗时')
    await wrapper.find('[data-name="tools"]').trigger('click')
    expect(wrapper.text()).toContain('course_lookup')
    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('输入摘要')
    expect(wrapper.text()).toContain('输出摘要')
    await wrapper.find('[data-name="plans"]').trigger('click')
    expect(wrapper.text()).toContain('任务规划')
    expect(wrapper.text()).toContain('第 1 版')
    expect(wrapper.text()).toContain('计划路径')
  })

  it('emits follow-up and cancel events', async () => {
    const wrapper = mount(AgentTaskDetailPanel, {
      global: { plugins: [naive] },
      props: {
        activeTask: { ...task, status: 'running' },
      },
    })

    await wrapper.find('textarea').setValue('继续查询考试时间')
    await wrapper.findAll('button').find((button) => button.text().includes('继续对话'))?.trigger('click')
    expect(wrapper.emitted('continue')?.[0]).toEqual([{ message: '继续查询考试时间', inputs: {} }])

    await wrapper.findAll('button').find((button) => button.text().includes('取消任务'))?.trigger('click')
    expect(wrapper.emitted('cancel')?.[0]).toEqual(['task-1'])
  })
})
