import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import WorkspaceView from '../WorkspaceView.vue'

describe('WorkspaceView', () => {
  it('renders the report-aligned intelligent file workspace', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(WorkspaceView) }),
    })

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, createTestingPinia({ createSpy: vi.fn, stubActions: false })],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('智能文件工作台')
    expect(wrapper.text()).toContain('显微镜实验报告.pdf')
    expect(wrapper.text()).toContain('已入库')
    expect(wrapper.text()).toContain('引用来源')
    expect(wrapper.text()).toContain('显微镜相关实验步骤包括')
    expect(wrapper.text()).toContain('file_search')
    expect(wrapper.text()).toContain('report_generate')
    expect(wrapper.text()).toContain('新文件自动摘要')
    expect(wrapper.text()).toContain('生物学实验')
    expect(wrapper.text()).toContain('审计日志')
  })
})
