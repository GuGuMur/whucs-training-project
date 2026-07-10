import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'
import { createMemoryHistory, createRouter } from 'vue-router'

import LoginView from '../LoginView.vue'

describe('LoginView', () => {
  it('renders a report-aligned login form for the protected workspace', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(LoginView) }),
    })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/login', name: 'login', component: LoginView }],
    })
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, router, createTestingPinia({ createSpy: vi.fn })],
      },
    })

    expect(wrapper.text()).toContain('智能文件管理平台')
    expect(wrapper.text()).toContain('账号')
    expect(wrapper.text()).toContain('密码')
    expect(wrapper.text()).toContain('进入工作台')
    expect(wrapper.text()).toContain('注册账号')
    expect(wrapper.text()).toContain('文件管理')
    expect(wrapper.text()).toContain('团队协作')
  })
})
