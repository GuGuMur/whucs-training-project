import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { saveWorkspaceSession } from '@/auth'
import * as workspaceClient from '@/client/workspace'
import type { WorkspaceAgentTask, ToolDefinition } from '@/client/workspace'
import { useAgentStore } from '@/stores/agent'

const calculatorTool: ToolDefinition = {
  category: 'utility',
  description: '执行安全算术计算',
  enabled: true,
  id: 'tool-calculator',
  input_schema: {
    properties: { expression: { type: 'string' } },
    required: ['expression'],
    type: 'object',
  },
  name: 'calculator',
  output_schema: { type: 'object' },
  version: '1.0.0',
}

const clarificationTask: WorkspaceAgentTask = {
  final_answer: '请补充要查询的课程名称。',
  id: 'task-course',
  result_view: { kind: 'text', text: '请补充要查询的课程名称。' },
  status: 'needs_clarification',
  steps: [
    {
      content: '识别到课程查询，但缺少课程名称。',
      phase: 'understand',
      status: 'needs_clarification',
      title: '需要补充信息',
      type: 'thought',
    },
  ],
  task: '查询课程信息',
}

const completedTask: WorkspaceAgentTask = {
  final_answer: '高等数学周一上课。',
  id: 'task-course',
  result_view: {
    columns: ['课程', '时间'],
    kind: 'table',
    rows: [{ course: '高等数学', time: '周一' }],
  },
  status: 'completed',
  steps: [
    ...clarificationTask.steps,
    {
      content: '调用 course_lookup 查询课程。',
      input_json: { query: '高等数学' },
      output_json: { time: '周一' },
      phase: 'call',
      status: 'success',
      title: '调用课程查询',
      tool_name: 'course_lookup',
      type: 'action',
    },
    {
      content: '高等数学周一上课。',
      phase: 'answer',
      status: 'success',
      title: '最终回答',
      type: 'answer',
    },
  ],
  task: '查询课程信息',
}

const cancelledTask: WorkspaceAgentTask = {
  final_answer: '任务已取消。',
  id: 'task-course',
  result_view: { content: '任务已取消。', type: 'text' },
  status: 'cancelled',
  steps: [
    ...clarificationTask.steps,
    {
      content: '用户已取消该智能体任务。',
      error_message: 'AGENT_TASK_CANCELLED',
      metadata: { cancelled_by: '小明' },
      phase: 'answer',
      status: 'failed',
      title: '任务已取消',
      type: 'answer',
    },
  ],
  task: '查询课程信息',
}

function saveSession() {
  saveWorkspaceSession({
    accessToken: 'access-token',
    displayName: '小明',
    refreshToken: 'refresh-token',
    userId: '1',
  })
}

describe('agent store', () => {
  beforeEach(() => {
    window.localStorage.clear()
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('loads the tool catalog', async () => {
    saveSession()
    const listSpy = vi.spyOn(workspaceClient, 'listTools').mockResolvedValue({
      items: [calculatorTool],
    })
    const agent = useAgentStore()

    await agent.loadTools()

    expect(listSpy).toHaveBeenCalledWith('access-token')
    expect(agent.tools).toEqual([calculatorTool])
  })

  it('creates a task and exposes needs-clarification state', async () => {
    saveSession()
    const createSpy = vi.spyOn(workspaceClient, 'createAgentTask').mockResolvedValue(clarificationTask)
    const agent = useAgentStore()

    await agent.createTask({ task: ' 查询课程信息 ', kbId: null, contextFileIds: [] })

    expect(createSpy).toHaveBeenCalledWith('access-token', {
      contextFileIds: [],
      kbId: null,
      task: '查询课程信息',
    })
    expect(agent.activeTask?.id).toBe('task-course')
    expect(agent.clarificationQuestion).toBe('请补充要查询的课程名称。')
    expect(agent.executionSteps).toEqual(clarificationTask.steps)
  })

  it('streams a task and updates execution steps before final task arrives', async () => {
    saveSession()
    async function* events() {
      yield { type: 'plan' as const, step: completedTask.steps[0] }
      yield { type: 'call' as const, step: completedTask.steps[1] }
      yield { type: 'answer' as const, step: completedTask.steps[2] }
      yield { type: 'done' as const, task: completedTask }
    }
    const streamSpy = vi.spyOn(workspaceClient, 'streamAgentTask').mockReturnValue(events())
    const agent = useAgentStore()

    await agent.createTaskStream({ task: '查询高等数学课程信息', kbId: null, contextFileIds: [] })

    expect(streamSpy).toHaveBeenCalledWith('access-token', {
      contextFileIds: [],
      kbId: null,
      task: '查询高等数学课程信息',
    })
    expect(agent.executionSteps).toEqual(completedTask.steps)
    expect(agent.streamedAnswer).toBe('高等数学周一上课。')
    expect(agent.activeTask?.id).toBe('task-course')
    expect(agent.isStreaming).toBe(false)
  })

  it('rejects an error SSE event and exposes its message instead of silently returning no result', async () => {
    saveSession()
    vi.spyOn(workspaceClient, 'streamAgentTask').mockImplementation(async function* () {
      yield { type: 'error' as const, message: '工具执行失败' }
    })
    const agent = useAgentStore()

    await expect(agent.createTaskStream({ task: '执行失败任务' })).rejects.toThrow('工具执行失败')

    expect(agent.errorMessage).toBe('工具执行失败')
    expect(agent.activeTask).toBeNull()
    expect(agent.isStreaming).toBe(false)
  })

  it('rejects a stream that closes before returning its terminal task', async () => {
    saveSession()
    vi.spyOn(workspaceClient, 'streamAgentTask').mockImplementation(async function* () {
      yield { type: 'plan' as const, step: completedTask.steps[0] }
    })
    const agent = useAgentStore()

    await expect(agent.createTaskStream({ task: '异常断流任务' })).rejects.toThrow('未收到最终结果')

    expect(agent.errorMessage).toContain('未收到最终结果')
  })

  it('previews a risky task plan before execution', async () => {
    saveSession()
    const previewSpy = vi.spyOn(workspaceClient, 'previewAgentPlan').mockResolvedValue({
      answer_strategy: 'use_tools_then_answer',
      intent: '查询数据库',
      missing_fields: [],
      requires_confirmation: true,
      risk_level: 'high',
      risk_reason: '将访问受限系统数据或外部服务，执行前需要确认。',
      steps: [
        {
          arguments: { table: 'files' },
          rationale: '查询受限文件表',
          risk_level: 'high',
          risk_reason: '将访问受限系统数据或外部服务，执行前需要确认。',
          tool_name: 'database_query',
        },
      ],
    })
    const agent = useAgentStore()

    await agent.previewTaskPlan({ task: '数据库查询文件', kbId: null, contextFileIds: [] })

    expect(previewSpy).toHaveBeenCalledWith('access-token', {
      contextFileIds: [],
      kbId: null,
      task: '数据库查询文件',
    })
    expect(agent.planPreview?.risk_level).toBe('high')
    expect(agent.planPreview?.requires_confirmation).toBe(true)
  })

  it('loads persisted task history and selects the latest task', async () => {
    saveSession()
    const historySpy = vi.spyOn(workspaceClient, 'listAgentTasks').mockResolvedValue({
      items: [completedTask, clarificationTask],
    })
    const agent = useAgentStore()

    await agent.loadTaskHistory()

    expect(historySpy).toHaveBeenCalledWith('access-token')
    expect(agent.taskHistory.map((task) => task.id)).toEqual(['task-course'])
    expect(agent.activeTask?.final_answer).toBe('高等数学周一上课。')
  })

  it('continues a task with clarification inputs and stores final result', async () => {
    saveSession()
    const continueSpy = vi.spyOn(workspaceClient, 'continueAgentTask').mockResolvedValue(completedTask)
    const agent = useAgentStore()
    agent.activeTask = clarificationTask

    await agent.continueTask('task-course', { inputs: { course_name: '高等数学' }, message: '继续查询上课时间' })

    expect(continueSpy).toHaveBeenCalledWith('access-token', 'task-course', {
      inputs: { course_name: '高等数学' },
      message: '继续查询上课时间',
    })
    expect(agent.activeTask?.status).toBe('completed')
    expect(agent.finalAnswer).toBe('高等数学周一上课。')
    expect(agent.resultView).toEqual(completedTask.result_view)
    expect(agent.taskHistory[0]?.id).toBe('task-course')
  })

  it('cancels a task and stores cancelled state', async () => {
    saveSession()
    const cancelSpy = vi.spyOn(workspaceClient, 'cancelAgentTask').mockResolvedValue(cancelledTask)
    const agent = useAgentStore()
    agent.activeTask = clarificationTask

    await agent.cancelTask('task-course')

    expect(cancelSpy).toHaveBeenCalledWith('access-token', 'task-course')
    expect(agent.activeTask?.status).toBe('cancelled')
    expect(agent.finalAnswer).toBe('任务已取消。')
    expect(agent.executionSteps[agent.executionSteps.length - 1]?.title).toBe('任务已取消')
  })

  it('deletes the active task and selects the next history item', async () => {
    saveSession()
    const deleteSpy = vi.spyOn(workspaceClient, 'deleteAgentTask').mockResolvedValue()
    const nextTask: WorkspaceAgentTask = {
      ...completedTask,
      final_answer: '备用任务已完成。',
      id: 'task-next',
      task: '备用任务',
    }
    const agent = useAgentStore()
    agent.activeTask = completedTask
    agent.taskHistory = [completedTask, nextTask]
    agent.executionSteps = completedTask.steps

    await agent.deleteTask('task-course')

    expect(deleteSpy).toHaveBeenCalledWith('access-token', 'task-course')
    expect(agent.taskHistory.map((task) => task.id)).toEqual(['task-next'])
    expect(agent.activeTask?.id).toBe('task-next')
    expect(agent.finalAnswer).toBe('备用任务已完成。')
  })
})
