import { flushPromises, mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import naive, { NConfigProvider, NMessageProvider } from 'naive-ui'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'

import { useAgentStore } from '@/stores/agent'
import { useWorkspaceStore } from '@/stores/workspace'
import { useWorkflowStore } from '@/stores/workflow'
import type { WorkspaceAgentTask } from '@/client/workspace'
import WorkflowBuilderView from '../WorkflowBuilderView.vue'

vi.mock('@/layouts/DesktopWorkspaceLayout.vue', () => ({
  default: defineComponent({
    name: 'DesktopWorkspaceLayoutStub',
    setup: (_, { slots }) => () => h('main', { 'data-testid': 'desktop-layout' }, slots.default?.()),
  }),
}))

vi.mock('@/layouts/MobileWorkspaceLayout.vue', () => ({
  default: defineComponent({
    name: 'MobileWorkspaceLayoutStub',
    setup: (_, { slots }) => () => h('main', { 'data-testid': 'mobile-layout' }, slots.default?.()),
  }),
}))

vi.mock('@vue-flow/core', async () => {
  const actual = await vi.importActual<typeof import('@vue-flow/core')>('@vue-flow/core')
  return {
    ...actual,
    VueFlow: defineComponent({
      name: 'VueFlow',
      setup: (_, { slots }) => () => h('div', { class: 'workflow-canvas-stub' }, slots.default?.()),
    }),
    useVueFlow: () => ({
      fitView: vi.fn(),
      project: ({ x, y }: { x: number; y: number }) => ({ x, y }),
    }),
  }
})

vi.mock('@vue-flow/background', () => ({
  Background: defineComponent({ name: 'Background', setup: () => () => h('div') }),
}))

vi.mock('@vue-flow/controls', () => ({
  Controls: defineComponent({ name: 'Controls', setup: () => () => h('div') }),
}))

vi.mock('@vue-flow/minimap', () => ({
  MiniMap: defineComponent({ name: 'MiniMap', setup: () => () => h('div') }),
}))

const task: WorkspaceAgentTask = {
  final_answer: '已整理结果。',
  id: 'task-1',
  messages: [],
  plan_revisions: [],
  result_view: { content: '已整理结果。', type: 'text' },
  status: 'completed' as const,
  steps: [
    {
      content: '已整理结果。',
      phase: 'answer' as const,
      status: 'success' as const,
      title: '最终回答',
      type: 'answer' as const,
    },
  ],
  task: '整理知识库文档',
  tool_calls: [],
}

function mountView() {
  const pinia = createTestingPinia({ createSpy: vi.fn })
  const workspace = useWorkspaceStore()
  vi.mocked(workspace.loadWorkspace).mockResolvedValue(undefined as any)
  vi.mocked(workspace.createWorkflow).mockResolvedValue({ id: 'workflow-1' } as any)
  workspace.snapshot = {
    audit_logs: [],
    files: [{ id: 'file-1', name: '课程资料.md' } as any],
    summary: {
      file_count: 1,
      indexed_count: 1,
      knowledge_base_count: 1,
      running_workflows: 0,
      tools_enabled: 1,
      unread_notifications: 0,
    },
    teams: [],
    tools: [],
    workflows: [],
  }
  workspace.knowledgeBases = [{ id: 'kb-1', name: '课程知识库' } as any]

  const workflow = useWorkflowStore()
  vi.mocked(workflow.listWorkflows).mockResolvedValue({ items: [] } as any)

  const agent = useAgentStore()
  vi.mocked(agent.loadTools).mockResolvedValue({ items: [] } as any)
  vi.mocked(agent.loadTaskHistory).mockResolvedValue({ items: [task] } as any)
  vi.mocked(agent.loadTask).mockResolvedValue(task as any)
  vi.mocked(agent.deleteTask).mockResolvedValue(undefined)
  vi.mocked(agent.clearPlanPreview).mockReturnValue(undefined)
  agent.taskHistory = [task]
  agent.activeTask = task
  agent.executionSteps = task.steps as any
  agent.tools = [
    {
      description: '读取知识库文档并提取兴趣',
      input_schema: { properties: { kb_id: { type: 'string' } }, type: 'object' },
      name: 'kb_interest_extract',
      risk_level: 'low',
    } as any,
  ]

  const TestHost = defineComponent({
    setup: () => () =>
      h(NConfigProvider, null, {
        default: () =>
          h(NMessageProvider, null, {
            default: () => h(WorkflowBuilderView),
          }),
      }),
  })

  const wrapper = mount(TestHost, {
    attachTo: document.body,
    global: {
      plugins: [naive, pinia],
      stubs: {
        RouterLink: { props: ['to'], template: '<a><slot /></a>' },
      },
    },
  })

  return { agent, workflow, workspace, wrapper }
}

describe('WorkflowBuilderView', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  it('defaults to the visual designer and keeps agent task creation in a separate tab', async () => {
    const { agent, workspace, wrapper } = mountView()

    await flushPromises()
    await nextTick()

    expect(workspace.loadWorkspace).toHaveBeenCalled()
    expect(agent.loadTools).toHaveBeenCalled()
    expect(agent.loadTaskHistory).toHaveBeenCalled()
    expect(wrapper.text()).toContain('智能体任务')
    expect(wrapper.text()).toContain('节点库')
    expect(document.querySelector('.workflow-canvas-stub')).not.toBeNull()

    await findTab(wrapper, '智能体任务').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('任务列表')
    expect(wrapper.text()).toContain('整理知识库文档')

    await findButton('创建任务').click()
    await nextTick()

    expect(agent.clearPlanPreview).toHaveBeenCalled()
    expect(document.body.textContent).toContain('创建智能体任务')
    expect(document.body.textContent).toContain('例如：查询高等数学课程安排并整理成表格')

    wrapper.unmount()
  })

  it('wires task list selection and deletion to agent store actions', async () => {
    const { agent, wrapper } = mountView()

    await flushPromises()
    await nextTick()

    await findTab(wrapper, '智能体任务').trigger('click')
    await nextTick()

    await wrapper.find('.agent-task-list__item').trigger('click')
    expect(agent.loadTask).toHaveBeenCalledWith('task-1')

    await wrapper.find('button[aria-label="删除任务"]').trigger('click')
    await nextTick()
    findButton('删除').click()
    await nextTick()

    expect(agent.deleteTask).toHaveBeenCalledWith('task-1')

    wrapper.unmount()
  })

  it('renders the visual workflow designer as the primary tool-flow surface', async () => {
    const { wrapper } = mountView()

    await flushPromises()
    await nextTick()

    expect(wrapper.text()).toContain('可视化编排')
    expect(wrapper.text()).toContain('节点库')
    expect(wrapper.text()).toContain('添加输出节点')
    expect(document.querySelector('.workflow-canvas-stub')).not.toBeNull()

    wrapper.unmount()
  })
})

function findButton(label: string) {
  const button = [...document.querySelectorAll<HTMLButtonElement>('button')]
    .find((item) => item.textContent?.includes(label))
  expect(button).toBeTruthy()
  return button!
}

function findTab(wrapper: ReturnType<typeof mount>, label: string) {
  const tab = wrapper.findAll('.n-tabs-tab').find((item) => item.text().includes(label))
  expect(tab).toBeTruthy()
  return tab!
}
