import { mount } from '@vue/test-utils'
import naive from 'naive-ui'
import { describe, expect, it } from 'vitest'

import AgentTaskComposer from '@/components/workflow/AgentTaskComposer.vue'

const planPreview = {
  answer_strategy: 'tool',
  intent: '查询课程',
  missing_fields: [],
  requires_confirmation: true,
  risk_level: 'medium' as const,
  risk_reason: '将调用课程查询工具。',
  steps: [
    {
      arguments: { query: '高等数学' },
      rationale: '查询课程安排',
      risk_level: 'medium' as const,
      risk_reason: '读取课程数据',
      tool_name: 'course_lookup',
    },
  ],
}

describe('AgentTaskComposer', () => {
  it('previews once and confirms with the selected execution mode', async () => {
    const wrapper = mount(AgentTaskComposer, {
      global: { plugins: [naive] },
      props: { planPreview },
    })

    await wrapper.find('textarea').setValue('查询高等数学课程安排')
    await wrapper.findAll('button').find((button) => button.text().includes('预览计划'))?.trigger('click')

    expect(wrapper.emitted('preview')?.[0]).toEqual([{
      contextFileIds: [],
      kbId: null,
      task: '查询高等数学课程安排',
    }])
    expect(wrapper.text()).toContain('确认并流式执行')
    const buttonLabels = wrapper.findAll('button').map((button) => button.text().trim())
    expect(buttonLabels).not.toContain('流式执行')

    await wrapper.findAll('button').find((button) => button.text().includes('确认并流式执行'))?.trigger('click')
    expect(wrapper.emitted('stream')?.[0]).toEqual([{
      contextFileIds: [],
      kbId: null,
      task: '查询高等数学课程安排',
    }])
  })

  it('confirms as non-streaming when stream output is disabled', async () => {
    const wrapper = mount(AgentTaskComposer, {
      global: { plugins: [naive] },
      props: { planPreview },
    })

    await wrapper.find('textarea').setValue('查询高等数学课程安排')
    await wrapper.find('.n-switch').trigger('click')
    await wrapper.findAll('button').find((button) => button.text().includes('确认执行'))?.trigger('click')

    expect(wrapper.emitted('submit')?.[0]).toEqual([{
      contextFileIds: [],
      kbId: null,
      task: '查询高等数学课程安排',
    }])
    expect(wrapper.emitted('stream')).toBeUndefined()
  })
})
