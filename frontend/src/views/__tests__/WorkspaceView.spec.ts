import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import WorkspaceView from '../WorkspaceView.vue'

describe('WorkspaceView', () => {
  it('renders the report-aligned intelligent file workspace and hides audit entry for non-admin users', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(WorkspaceView) }),
    })

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, createTestingPinia({ createSpy: vi.fn, stubActions: false })],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('\u667a\u80fd\u6587\u4ef6\u5de5\u4f5c\u53f0')
    expect(wrapper.text()).toContain('\u663e\u5fae\u955c\u5b9e\u9a8c\u62a5\u544a.pdf')
    expect(wrapper.text()).toContain('file_search')
    expect(wrapper.text()).toContain('report_generate')
    expect(wrapper.text()).toContain('\u65b0\u6587\u4ef6\u81ea\u52a8\u6458\u8981')
    expect(wrapper.text()).toContain('\u751f\u7269\u5b66\u5b9e\u9a8c')
    expect(wrapper.text()).not.toContain('\u5ba1\u8ba1\u65e5\u5fd7')
  })
})
