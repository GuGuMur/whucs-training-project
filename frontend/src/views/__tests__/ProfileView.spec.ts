import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'
import { createMemoryHistory, createRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import ProfileView from '../ProfileView.vue'

describe('ProfileView', () => {
  it('renders profile details and submits updates through the auth store', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(ProfileView) }),
    })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/profile', name: 'profile', component: ProfileView }],
    })
    await router.push('/profile')
    await router.isReady()

    const wrapper = mount(TestHost, {
      global: {
        plugins: [
          naive,
          router,
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                currentUser: {
                  display_name: '旧资料',
                  email: 'old-profile@example.com',
                  id: 12,
                  roles: ['user'],
                  username: 'xiaoming',
                },
                session: {
                  accessToken: 'profile-access-token',
                  displayName: '旧资料',
                  refreshToken: 'profile-refresh-token',
                  userId: '12',
                },
              },
            },
          }),
        ],
      },
    })
    const auth = useAuthStore()

    expect(wrapper.text()).toContain('个人资料')
    expect(wrapper.text()).toContain('xiaoming')
    expect(wrapper.text()).toContain('old-profile@example.com')

    await wrapper.find('input[placeholder="例如：小明同学"]').setValue('小明同学')
    await wrapper.find('input[placeholder="用于登录和系统通知"]').setValue('xiaoming-profile@example.com')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(auth.updateProfile).toHaveBeenCalledWith({
      display_name: '小明同学',
      email: 'xiaoming-profile@example.com',
    })
  })
})
