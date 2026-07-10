import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { resolveOptionalAccessToken } from '@/auth'
import {
  continueAgentTask,
  createAgentTask,
  getAgentTask,
  listTools,
  type AgentStep,
  type ToolDefinition,
  type WorkspaceAgentTask,
  type WorkspaceAgentTaskContinueInput,
  type WorkspaceAgentTaskInput,
} from '@/client/workspace'

export const useAgentStore = defineStore('agent', () => {
  const tools = shallowRef<ToolDefinition[]>([])
  const activeTask = shallowRef<WorkspaceAgentTask | null>(null)
  const taskHistory = shallowRef<WorkspaceAgentTask[]>([])
  const executionSteps = shallowRef<AgentStep[]>([])
  const clarificationQuestion = shallowRef('')
  const resultView = shallowRef<Record<string, unknown> | null>(null)
  const loading = shallowRef(false)
  const errorMessage = shallowRef('')

  const finalAnswer = computed(() => activeTask.value?.final_answer ?? '')

  async function loadTools(token?: string) {
    const accessToken = requireAccessToken(token)

    loading.value = true
    errorMessage.value = ''
    try {
      const response = await listTools(accessToken)
      tools.value = response.items
      return response
    } catch (error) {
      errorMessage.value = '工具目录加载失败，请稍后重试'
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createTask(payload: WorkspaceAgentTaskInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceAgentTaskInput = {
      contextFileIds: payload.contextFileIds ?? [],
      kbId: payload.kbId ?? null,
      task: payload.task.trim(),
    }

    loading.value = true
    errorMessage.value = ''
    try {
      const task = await createAgentTask(accessToken, nextPayload)
      applyTask(task)
      return task
    } catch (error) {
      errorMessage.value = '智能体任务创建失败，请检查输入内容'
      throw error
    } finally {
      loading.value = false
    }
  }

  async function loadTask(taskId: string, token?: string) {
    const accessToken = requireAccessToken(token)

    loading.value = true
    errorMessage.value = ''
    try {
      const task = await getAgentTask(accessToken, taskId)
      applyTask(task)
      return task
    } catch (error) {
      errorMessage.value = '智能体任务加载失败，请稍后重试'
      throw error
    } finally {
      loading.value = false
    }
  }

  async function continueTask(taskId: string, payload: WorkspaceAgentTaskContinueInput) {
    const accessToken = requireAccessToken()

    loading.value = true
    errorMessage.value = ''
    try {
      const task = await continueAgentTask(accessToken, taskId, {
        inputs: payload.inputs ?? {},
      })
      applyTask(task)
      return task
    } catch (error) {
      errorMessage.value = '智能体任务继续执行失败，请补充必要参数后重试'
      throw error
    } finally {
      loading.value = false
    }
  }

  function resetAgent() {
    activeTask.value = null
    taskHistory.value = []
    executionSteps.value = []
    clarificationQuestion.value = ''
    resultView.value = null
    errorMessage.value = ''
  }

  function applyTask(task: WorkspaceAgentTask) {
    activeTask.value = task
    executionSteps.value = task.steps
    clarificationQuestion.value = task.status === 'needs_clarification' ? task.final_answer : ''
    resultView.value = isRecord(task.result_view) ? task.result_view : null
    taskHistory.value = [
      task,
      ...taskHistory.value.filter((item) => item.id !== task.id),
    ]
  }

  function requireAccessToken(token?: string) {
    const accessToken = token ?? resolveOptionalAccessToken()
    if (!accessToken) {
      errorMessage.value = '请先登录后再执行智能体任务'
      throw new Error(errorMessage.value)
    }
    return accessToken
  }

  function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value)
  }

  return {
    activeTask,
    clarificationQuestion,
    continueTask,
    createTask,
    errorMessage,
    executionSteps,
    finalAnswer,
    loadTask,
    loadTools,
    loading,
    resetAgent,
    resultView,
    taskHistory,
    tools,
  }
})
