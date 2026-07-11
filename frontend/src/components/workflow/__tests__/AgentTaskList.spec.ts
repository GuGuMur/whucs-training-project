import { mount } from '@vue/test-utils'
import naive from 'naive-ui'
import { describe, expect, it } from 'vitest'

import AgentTaskList from '@/components/workflow/AgentTaskList.vue'
import type { WorkspaceAgentTask } from '@/client/workspace'

const task: WorkspaceAgentTask = {
  final_answer: '高等数学周一上课。',
  id: 'task-course',
  messages: [],
  plan_revisions: [],
  result_view: { type: 'text', content: '高等数学周一上课。' },
  status: 'completed',
  steps: [
    {
      content: '高等数学周一上课。',
      phase: 'answer',
      status: 'success',
      title: '最终回答',
      type: 'answer',
    },
  ],
  task: '查询高等数学课程安排',
  tool_calls: [],
}

describe('AgentTaskList', () => {
  it('renders tasks as a list and emits selection', async () => {
    const wrapper = mount(AgentTaskList, {
      global: { plugins: [naive] },
      props: { activeTaskId: task.id, tasks: [task] },
    })

    expect(wrapper.text()).toContain('查询高等数学课程安排')
    expect(wrapper.findAll('.agent-task-list__item')).toHaveLength(1)

    await wrapper.find('.agent-task-list__item').trigger('click')

    expect(wrapper.emitted('selectTask')?.[0]).toEqual([task.id])
  })

  it('emits delete after confirmation', async () => {
    const wrapper = mount(AgentTaskList, {
      attachTo: document.body,
      global: { plugins: [naive] },
      props: { tasks: [task] },
    })

    await wrapper.find('button[aria-label="删除任务"]').trigger('click')
    await document.querySelector<HTMLElement>('.n-popconfirm .n-button--primary-type')?.click()

    expect(wrapper.emitted('deleteTask')?.[0]).toEqual([task.id])
    wrapper.unmount()
  })
})
