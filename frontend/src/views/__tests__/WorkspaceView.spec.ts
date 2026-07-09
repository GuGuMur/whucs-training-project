import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { defineComponent, h } from 'vue'
import naive, { NConfigProvider } from 'naive-ui'

import { useWorkspaceStore } from '@/stores/workspace'
import WorkspaceView from '../WorkspaceView.vue'

describe('WorkspaceView', () => {
  it('renders the report-aligned intelligent file workspace and hides audit entry for non-admin users', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(WorkspaceView) }),
    })

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, createTestingPinia({ createSpy: vi.fn, stubActions: false })],
        stubs: {
          Background: true,
          Controls: true,
          VueFlow: { template: '<div><slot /></div>' },
        },
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

  it('wires knowledge-base panel actions to the workspace store', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(WorkspaceView) }),
    })

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, createTestingPinia({ createSpy: vi.fn })],
        stubs: {
          Background: true,
          Controls: true,
          VueFlow: { template: '<div><slot /></div>' },
        },
      },
    })
    const workspace = useWorkspaceStore()

    await flushPromises()
    await wrapper.get('input[placeholder="知识库名称"]').setValue(' 算法复习库 ')
    await wrapper.get('textarea[placeholder="知识库说明"]').setValue(' 课程材料 ')
    await wrapper.get('[data-testid="submit-create-kb"]').trigger('click')
    await wrapper.get('[data-testid="select-kb-kb-biology"]').trigger('click')
    await wrapper.get('[data-testid="add-kb-document-file-requirements"]').trigger('click')
    await wrapper.get('textarea[placeholder="输入问题"]').setValue(' 显微镜实验步骤是什么？ ')
    await wrapper.get('[data-testid="submit-rag-question"]').trigger('click')

    expect(workspace.createKnowledgeBase).toHaveBeenCalledWith({
      description: '课程材料',
      name: '算法复习库',
    })
    expect(workspace.selectKnowledgeBase).toHaveBeenCalledWith('kb-biology')
    expect(workspace.addKnowledgeDocument).toHaveBeenCalledWith('kb-biology', 'file-requirements')
    expect(workspace.askKnowledgeQuestion).toHaveBeenCalledWith({
      kbId: 'kb-biology',
      question: '显微镜实验步骤是什么？',
      topK: 5,
    })
  })

  it('wires workflow builder actions to the workspace store', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(WorkspaceView) }),
    })

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, createTestingPinia({ createSpy: vi.fn })],
        stubs: {
          Background: true,
          Controls: true,
          VueFlow: { template: '<div><slot /></div>' },
        },
      },
    })
    const workspace = useWorkspaceStore()

    await flushPromises()
    await wrapper.get('input[placeholder="流程名称"]').setValue(' 团队周报流程 ')
    await wrapper.get('textarea[placeholder="流程说明"]').setValue(' 自动整理团队目录 ')
    await wrapper.get('[data-testid="submit-create-workflow"]').trigger('click')
    await wrapper.get('[data-testid="select-workflow-new-file-auto-summary"]').trigger('click')
    await wrapper.get('[data-testid="validate-workflow-new-file-auto-summary"]').trigger('click')
    await wrapper.get('[data-testid="publish-workflow-new-file-auto-summary"]').trigger('click')
    await wrapper.get('[data-testid="execute-workflow-new-file-auto-summary"]').trigger('click')

    const createPayload = vi.mocked(workspace.createWorkflow).mock.calls[0]?.[0]
    expect(createPayload).toMatchObject({
      description: '自动整理团队目录',
      name: '团队周报流程',
      trigger: 'manual',
    })
    expect(createPayload?.nodes).toHaveLength(4)
    expect(workspace.selectWorkflow).toHaveBeenCalledWith('new-file-auto-summary')
    expect(workspace.validateWorkflow).toHaveBeenCalledWith('new-file-auto-summary')
    expect(workspace.publishWorkflow).toHaveBeenCalledWith('new-file-auto-summary')
    expect(workspace.executeWorkflow).toHaveBeenCalledWith('new-file-auto-summary', {
      fileId: 'file-microscope',
      targetKbId: 'kb-biology',
    })
  })

  it('wires permission rule panel actions to the workspace store', async () => {
    const TestHost = defineComponent({
      setup: () => () => h(NConfigProvider, null, { default: () => h(WorkspaceView) }),
    })

    const wrapper = mount(TestHost, {
      global: {
        plugins: [naive, createTestingPinia({ createSpy: vi.fn })],
        stubs: {
          Background: true,
          Controls: true,
          VueFlow: { template: '<div><slot /></div>' },
        },
      },
    })
    const workspace = useWorkspaceStore()

    await flushPromises()
    await wrapper.get('[data-testid="submit-permission-rule"]').trigger('click')
    await wrapper.get('[data-testid="delete-permission-rule-demo-rule-folder-deny"]').trigger('click')

    expect(workspace.createPermissionRule).toHaveBeenCalledWith({
      action: 'read',
      effect: 'deny',
      inherit: true,
      resourceId: 'personal-root',
      resourceType: 'folder',
      subjectId: 'team-biology:guest',
      subjectType: 'role',
    })
    expect(workspace.deletePermissionRule).toHaveBeenCalledWith('demo-rule-folder-deny')
  })
})
