import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { resolveWorkspaceToken } from '@/auth'
import { useAuthStore } from '@/stores/auth'

import type {
  WorkspaceWorkflow,
  WorkspaceWorkflowCreateInput,
  WorkspaceWorkflowExecuteInput,
  WorkspaceWorkflowExecution,
  WorkspaceWorkflowUpdateInput,
  WorkspaceWorkflowValidation,
} from '@/client/workspace'
import {
  createWorkspaceWorkflow,
  executeWorkspaceWorkflow,
  listWorkspaceWorkflows,
  publishWorkspaceWorkflow,
  updateWorkspaceWorkflow,
  validateWorkspaceWorkflow,
} from '@/client/workspace'

export const useWorkflowStore = defineStore('workflow', () => {
  const auth = useAuthStore()

  const activeWorkflowId = shallowRef<string | null>(null)
  const activeWorkflowValidation = shallowRef<WorkspaceWorkflowValidation | null>(null)
  const activeWorkflowExecution = shallowRef<WorkspaceWorkflowExecution | null>(null)
  const workflowOperationLoading = shallowRef(false)
  const workflows = shallowRef<WorkspaceWorkflow[]>([])

  const activeWorkflow = computed<WorkspaceWorkflow | null>(
    () => workflows.value.find((workflow) => workflow.id === activeWorkflowId.value) ?? null,
  )

  function requireAccessToken(): string {
    const accessToken = auth.session?.accessToken ?? resolveWorkspaceToken()
    if (!accessToken) {
      throw new Error('请先登录后再执行工作流操作')
    }
    return accessToken
  }

  function upsertWorkflow(workflow: WorkspaceWorkflow, moveToFront = false) {
    const current = workflows.value
    const existing = current.some((item) => item.id === workflow.id)
    const nextWorkflows = moveToFront
      ? [workflow, ...current.filter((item) => item.id !== workflow.id)]
      : existing
        ? current.map((item) => (item.id === workflow.id ? workflow : item))
        : [workflow, ...current]

    workflows.value = nextWorkflows
  }

  async function listWorkflows() {
    const token = requireAccessToken()

    workflowOperationLoading.value = true
    try {
      const response = await listWorkspaceWorkflows(token)
      workflows.value = response.items ?? []
      ensureActiveWorkflowSelection()
      return response
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function createWorkflow(payload: WorkspaceWorkflowCreateInput) {
    const token = requireAccessToken()
    const nextPayload: WorkspaceWorkflowCreateInput = {
      description: payload.description?.trim() || null,
      edges: payload.edges ?? [],
      name: payload.name.trim(),
      nodes: payload.nodes ?? [],
      trigger: payload.trigger?.trim() || 'manual',
    }

    workflowOperationLoading.value = true
    try {
      const created = await createWorkspaceWorkflow(token, nextPayload)
      upsertWorkflow(created, true)
      activeWorkflowId.value = created.id
      activeWorkflowValidation.value = null
      activeWorkflowExecution.value = null
      return created
    } finally {
      workflowOperationLoading.value = false
    }
  }

  function normalizeWorkflowUpdatePayload(
    payload: WorkspaceWorkflowUpdateInput,
  ): WorkspaceWorkflowUpdateInput {
    const nextPayload: WorkspaceWorkflowUpdateInput = {}
    if ('description' in payload) {
      nextPayload.description = payload.description?.trim() || null
    }
    if ('edges' in payload) {
      nextPayload.edges = payload.edges ?? null
    }
    if ('name' in payload) {
      nextPayload.name = payload.name?.trim() || null
    }
    if ('nodes' in payload) {
      nextPayload.nodes = payload.nodes ?? null
    }
    if ('trigger' in payload) {
      nextPayload.trigger = payload.trigger?.trim() || null
    }
    return nextPayload
  }

  async function updateWorkflow(workflowId: string, payload: WorkspaceWorkflowUpdateInput) {
    const token = requireAccessToken()
    const nextPayload = normalizeWorkflowUpdatePayload(payload)

    workflowOperationLoading.value = true
    try {
      const updated = await updateWorkspaceWorkflow(token, workflowId, nextPayload)
      upsertWorkflow(updated)
      activeWorkflowId.value = updated.id
      activeWorkflowValidation.value = null
      return updated
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function validateWorkflow(workflowId: string) {
    const token = requireAccessToken()

    workflowOperationLoading.value = true
    try {
      const validation = await validateWorkspaceWorkflow(token, workflowId)
      activeWorkflowId.value = workflowId
      activeWorkflowValidation.value = validation
      return validation
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function publishWorkflow(workflowId: string) {
    const token = requireAccessToken()

    workflowOperationLoading.value = true
    try {
      const published = await publishWorkspaceWorkflow(token, workflowId)
      upsertWorkflow(published)
      activeWorkflowId.value = published.id
      return published
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function executeWorkflow(workflowId: string, payload: WorkspaceWorkflowExecuteInput) {
    const token = requireAccessToken()

    workflowOperationLoading.value = true
    try {
      const execution = await executeWorkspaceWorkflow(token, workflowId, payload)
      activeWorkflowId.value = workflowId
      activeWorkflowExecution.value = execution
      return execution
    } finally {
      workflowOperationLoading.value = false
    }
  }

  function ensureActiveWorkflowSelection() {
    if (!workflows.value.some((workflow) => workflow.id === activeWorkflowId.value)) {
      activeWorkflowId.value = workflows.value[0]?.id ?? null
    }
  }

  return {
    activeWorkflow,
    activeWorkflowExecution,
    activeWorkflowId,
    activeWorkflowValidation,
    createWorkflow,
    ensureActiveWorkflowSelection,
    executeWorkflow,
    listWorkflows,
    publishWorkflow,
    updateWorkflow,
    validateWorkflow,
    workflowOperationLoading,
    workflows,
  }
})
