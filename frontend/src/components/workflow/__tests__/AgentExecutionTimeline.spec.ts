import { shallowMount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { AgentStep } from '@/client/workspace'
import AgentExecutionTimeline from '@/components/workflow/AgentExecutionTimeline.vue'

const steps: AgentStep[] = [
  {
    content: '理解用户要查询课程时间。',
    phase: 'understand',
    status: 'success',
    title: '理解任务',
    type: 'thought',
  },
  {
    content: '调用课程查询工具。',
    input_json: { query: '高等数学' },
    metadata: { latency_ms: 32, retry_count: 1 },
    output_json: { room: 'A101', time: '周一' },
    phase: 'call',
    status: 'success',
    title: '查询课程',
    tool_name: 'course_lookup',
    type: 'action',
  },
  {
    content: '规划调用顺序。',
    input_json: { planned_tools: [['course_lookup', { query: '高等数学' }], ['calculator', { expression: '1 + 1' }]] },
    phase: 'plan',
    status: 'success',
    title: '规划步骤',
    type: 'thought',
  },
  {
    content: '缺少课程名称。',
    error_message: 'course_name is required',
    phase: 'observe',
    status: 'needs_clarification',
    title: '需要补充信息',
    type: 'observation',
  },
]

describe('AgentExecutionTimeline', () => {
  it('renders phase labels, tool parameters, and clarification errors', () => {
    const wrapper = shallowMount(AgentExecutionTimeline, {
      props: { steps },
    })

    expect(wrapper.text()).toContain('理解')
    expect(wrapper.text()).toContain('调用')
    expect(wrapper.text()).toContain('观察')
    expect(wrapper.text()).toContain('course_lookup')
    expect(wrapper.text()).toContain('calculator')
    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('32 ms')
    expect(wrapper.text()).toContain('重试 1')
    expect(wrapper.text()).toContain('输出摘要')
    expect(wrapper.text()).toContain('course_name is required')
    expect(wrapper.text()).toContain('需要补充')
  })
})
