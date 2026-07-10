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

  it('continues a task with clarification inputs and stores final result', async () => {
    saveSession()
    const continueSpy = vi.spyOn(workspaceClient, 'continueAgentTask').mockResolvedValue(completedTask)
    const agent = useAgentStore()
    agent.activeTask = clarificationTask

    await agent.continueTask('task-course', { inputs: { course_name: '高等数学' } })

    expect(continueSpy).toHaveBeenCalledWith('access-token', 'task-course', {
      inputs: { course_name: '高等数学' },
    })
    expect(agent.activeTask?.status).toBe('completed')
    expect(agent.finalAnswer).toBe('高等数学周一上课。')
    expect(agent.resultView).toEqual(completedTask.result_view)
    expect(agent.taskHistory[0]?.id).toBe('task-course')
  })
})
