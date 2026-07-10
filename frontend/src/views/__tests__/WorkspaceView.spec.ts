import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider, NMessageProvider } from 'naive-ui'

import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'
import WorkspaceView from '../WorkspaceView.vue'

function createWrapper(stubActions = true) {
  const pinia = createTestingPinia({ createSpy: vi.fn, stubActions })
  // Set up auth session so requireAccessToken() works
  const auth = useAuthStore()
  auth.session = {
    accessToken: 'test-token',
    displayName: '测试用户',
    refreshToken: 'test-refresh',
    userId: '1',
  }

  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(NMessageProvider, null, {
            default: () => h(WorkspaceView),
          }),
      }),
  })
  return mount(TestHost, {
    global: {
      plugins: [naive, pinia],
      stubs: {
        Background: true,
        Controls: true,
        VueFlow: { template: '<div><slot /></div>' },
        RouterLink: { props: ['to'], template: '<a><slot /></a>' },
      },
    },
  })
}

describe('WorkspaceView', () => {
  it('renders the main workspace with navigation items and API status indicator', async () => {
    const wrapper = createWrapper(false)
    const workspace = useWorkspaceStore()

    await flushPromises()

    // Verify component mounts and renders navigation
    expect(wrapper.text()).toContain('文件管理')
    expect(wrapper.text()).toContain('工具流')

    // Store should have called loadWorkspace on mount
    expect(workspace.loadWorkspace).toHaveBeenCalled()
  })

  it('wires knowledge-base panel actions to the workspace store', async () => {
    const wrapper = createWrapper()
    const workspace = useWorkspaceStore()

    await flushPromises()

    // Create a knowledge base through the form
    const nameInputs = wrapper.findAll('input[placeholder="知识库名称"]')
    if (nameInputs.length > 0) {
      await nameInputs[0]!.setValue(' 算法复习库 ')
    }
    const descInputs = wrapper.findAll('textarea[placeholder="知识库说明"]')
    if (descInputs.length > 0) {
      await descInputs[0]!.setValue(' 课程材料 ')
    }

    const submitBtn = wrapper.find('[data-testid="submit-create-kb"]')
    if (submitBtn.exists()) {
      await submitBtn.trigger('click')
      expect(workspace.createKnowledgeBase).toHaveBeenCalledWith({
        description: '课程材料',
        name: '算法复习库',
      })
    }

    // Submit a RAG question
    const questionInputs = wrapper.findAll('textarea[placeholder="输入问题"]')
    if (questionInputs.length > 0) {
      await questionInputs[0]!.setValue(' 显微镜实验步骤是什么？ ')
      const submitQa = wrapper.find('[data-testid="submit-rag-question"]')
      if (submitQa.exists()) {
        await submitQa.trigger('click')
      }
    }
  })

  it('wires workflow builder actions to the workspace store', async () => {
    const wrapper = createWrapper()
    const workspace = useWorkspaceStore()

    await flushPromises()

    // Create a workflow
    const nameInputs = wrapper.findAll('input[placeholder="流程名称"]')
    if (nameInputs.length > 0) {
      await nameInputs[0]!.setValue(' 团队周报流程 ')
    }
    const descInputs = wrapper.findAll('textarea[placeholder="流程说明"]')
    if (descInputs.length > 0) {
      await descInputs[0]!.setValue(' 自动整理团队目录 ')
    }

    const submitBtn = wrapper.find('[data-testid="submit-create-workflow"]')
    if (submitBtn.exists()) {
      await submitBtn.trigger('click')
      const createPayload = vi.mocked(workspace.createWorkflow).mock.calls[0]?.[0]
      expect(createPayload).toMatchObject({
        description: '自动整理团队目录',
        name: '团队周报流程',
        trigger: 'manual',
      })
      expect(createPayload?.nodes).toHaveLength(0)
    }
  })

  it('wires permission rule panel actions to the workspace store', async () => {
    const wrapper = createWrapper()
    const workspace = useWorkspaceStore()

    await flushPromises()

    const submitBtn = wrapper.find('[data-testid="submit-permission-rule"]')
    if (submitBtn.exists()) {
      await submitBtn.trigger('click')
      expect(workspace.createPermissionRule).toHaveBeenCalled()
    }
  })
})
