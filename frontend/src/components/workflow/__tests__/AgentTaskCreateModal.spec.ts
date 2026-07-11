import { mount } from '@vue/test-utils'
import naive from 'naive-ui'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import AgentTaskCreateModal from '@/components/workflow/AgentTaskCreateModal.vue'

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

describe('AgentTaskCreateModal', () => {
  it('previews and confirms a streaming task from the modal', async () => {
    const wrapper = mount(AgentTaskCreateModal, {
      attachTo: document.body,
      global: { plugins: [naive] },
      props: { planPreview, show: true },
    })

    await nextTick()
    const textarea = document.querySelector<HTMLTextAreaElement>('textarea')
    expect(textarea).toBeTruthy()
    textarea!.value = '查询高等数学课程安排'
    textarea!.dispatchEvent(new Event('input'))
    await nextTick()
    findButton('预览计划').click()
    await nextTick()

    expect(wrapper.emitted('preview')?.[0]).toEqual([{
      contextFileIds: [],
      kbId: null,
      task: '查询高等数学课程安排',
    }])

    findButton('确认并流式执行').click()
    await nextTick()

    expect(wrapper.emitted('stream')?.[0]).toEqual([{
      contextFileIds: [],
      kbId: null,
      task: '查询高等数学课程安排',
    }])
    const showEvents = wrapper.emitted('update:show') ?? []
    expect(showEvents[showEvents.length - 1]).toEqual([false])
    wrapper.unmount()
  })
})

function findButton(label: string) {
  const button = [...document.querySelectorAll<HTMLButtonElement>('button')]
    .find((item) => item.textContent?.includes(label))
  expect(button).toBeTruthy()
  return button!
}
