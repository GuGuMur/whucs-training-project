import { describe, expect, it } from 'vitest'

import { designerToWorkflowPayload, workflowToDesigner } from '../workflowCodec'
import type { WorkspaceWorkflow } from '@/client/workspace'

describe('workflow codec', () => {
  it('round-trips node positions, bindings, and edge handles', () => {
    const workflow: WorkspaceWorkflow = {
      id: 'wf-1',
      name: '计算流程',
      description: 'codec',
      trigger: 'manual',
      version: '0.1.0',
      status: 'draft',
      node_count: 2,
      nodes: [
        {
          id: 'input', name: '输入', type: 'input', tool_name: null,
          parameters: { expression: { mode: 'input', input_key: 'expression' } },
          position: { x: 10.5, y: 20.5 },
        },
        {
          id: 'calc', name: '计算', type: 'tool', tool_name: 'calculator',
          parameters: { expression: { mode: 'node', node_id: 'input', path: 'output.expression' } },
          position: { x: 300, y: 20 },
        },
      ],
      edges: [{ id: 'e1', source: 'input', target: 'calc', source_handle: 'output', target_handle: 'input', label: null, type: 'smoothstep' }],
    }

    const payload = designerToWorkflowPayload(workflowToDesigner(workflow))

    expect(payload.nodes).toEqual(workflow.nodes)
    expect(payload.edges).toEqual(workflow.edges)
  })

  it('preserves advanced node kinds and condition branch handles', () => {
    const workflow = {
      id: 'wf-advanced', name: '高级流程', description: '', trigger: 'manual', version: '1.0.0',
      status: 'draft', node_count: 2,
      nodes: [
        { id: 'condition', name: '条件', type: 'condition', tool_name: null, parameters: { operator: 'truthy', left: true }, position: { x: 1, y: 2 } },
        { id: 'aggregate', name: '聚合', type: 'aggregate', tool_name: null, parameters: { operation: 'sum', values: [1, 2] }, position: { x: 3, y: 4 } },
      ],
      edges: [{ id: 'branch', source: 'condition', target: 'aggregate', source_handle: 'true', target_handle: 'input', label: '命中', type: 'smoothstep' }],
    } as WorkspaceWorkflow

    const designer = workflowToDesigner(workflow)
    const payload = designerToWorkflowPayload(designer)

    expect(designer.nodes.map(node => node.data.kind)).toEqual(['condition', 'aggregate'])
    expect(payload.nodes).toEqual(workflow.nodes)
    expect(payload.edges).toEqual(workflow.edges)
  })
})
