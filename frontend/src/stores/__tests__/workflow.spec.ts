import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { saveWorkspaceSession } from '@/auth'
import * as client from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'
import { useWorkflowStore } from '@/stores/workflow'

describe('workflow store debug lifecycle', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    saveWorkspaceSession({
      accessToken: 'access-token',
      displayName: '测试用户',
      refreshToken: 'refresh-token',
      userId: '1',
    })
    useAuthStore().restoreLocalSession()
    vi.restoreAllMocks()
  })

  it('starts and advances a real workflow debug session', async () => {
    vi.spyOn(client, 'startWorkspaceWorkflowDebug').mockResolvedValue({
      session_id: 'debug-1', status: 'ready', node_count: 2,
    })
    vi.spyOn(client, 'stepWorkspaceWorkflowDebug').mockResolvedValue({
      done: false, step: 1, node_id: 'calc', node_name: '计算', status: 'success',
      input: { expression: '6 * 7' }, output: { result: 42 }, remaining: 1,
    })
    const store = useWorkflowStore()

    await store.startDebug('wf-1')
    const step = await store.stepDebug('wf-1')

    expect(client.stepWorkspaceWorkflowDebug).toHaveBeenCalledWith('access-token', 'wf-1', 'debug-1')
    expect(step.output).toEqual({ result: 42 })
    expect(store.debugSteps).toHaveLength(1)
  })

  it('loads persisted versions and executions with workflow detail', async () => {
    vi.spyOn(client, 'getWorkspaceWorkflow').mockResolvedValue({
      id: 'wf-1', name: '流程', description: '', trigger: 'manual', version: '0.2.0',
      status: 'published', node_count: 0, nodes: [], edges: [],
    })
    vi.spyOn(client, 'listWorkspaceWorkflowVersions').mockResolvedValue([{
      id: 'v1', workflow_id: 'wf-1', version: '0.2.0', name: '流程', description: '', trigger: 'manual',
      nodes: [], edges: [], published_at: '2026-07-16T00:00:00Z',
    }])
    vi.spyOn(client, 'listWorkspaceWorkflowExecutions').mockResolvedValue([{
      id: 'exec-1', workflow_id: 'wf-1', workflow_version: '0.2.0', status: 'completed',
      node_executions: [], output: {}, created_at: '2026-07-16T00:01:00Z',
    }])
    const store = useWorkflowStore()

    await store.loadWorkflow('wf-1')

    expect(store.workflowVersions[0]?.id).toBe('v1')
    expect(store.workflowExecutions[0]?.id).toBe('exec-1')
  })

  it('restores an immutable version as a draft workflow', async () => {
    vi.spyOn(client, 'restoreWorkspaceWorkflowVersion').mockResolvedValue({
      id: 'wf-1', name: '旧版本', description: '', trigger: 'manual', version: '0.2.0',
      status: 'draft', node_count: 0, nodes: [], edges: [],
    })
    const store = useWorkflowStore()

    const restored = await store.restoreVersion('wf-1', 'version-1')

    expect(client.restoreWorkspaceWorkflowVersion).toHaveBeenCalledWith('access-token', 'wf-1', 'version-1')
    expect(restored.status).toBe('draft')
  })
})
