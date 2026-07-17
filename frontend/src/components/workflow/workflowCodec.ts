import type {
  WorkspaceWorkflow,
  WorkspaceWorkflowCreateInput,
  WorkspaceWorkflowEdge,
  WorkspaceWorkflowNode,
  WorkspaceWorkflowUpdateInput,
} from '@/client/workspace'
import type {
  SupportedWorkflowNodeKind,
  WorkflowDesignerDocument,
  WorkflowDesignerEdge,
  WorkflowDesignerNode,
} from './workflowDesignerTypes'

const supportedKinds = new Set<SupportedWorkflowNodeKind>([
  'input', 'trigger', 'tool', 'condition', 'loop', 'transform', 'aggregate', 'output',
])

export function workflowToDesigner(workflow: WorkspaceWorkflow): WorkflowDesignerDocument {
  return {
    id: workflow.id,
    name: workflow.name,
    description: workflow.description,
    trigger: normalizeTrigger(workflow.trigger),
    version: workflow.version,
    revision: workflow.revision ?? 0,
    nodes: (workflow.nodes ?? []).map(nodeToDesigner),
    edges: (workflow.edges ?? []).map(edgeToDesigner),
  }
}

export function designerToWorkflowPayload(
  document: WorkflowDesignerDocument,
): WorkspaceWorkflowCreateInput & WorkspaceWorkflowUpdateInput {
  return {
    name: document.name.trim() || '未命名流程',
    description: document.description.trim() || null,
    trigger: normalizeTrigger(document.trigger),
    nodes: document.nodes.map(nodeToPayload),
    edges: document.edges.map(edgeToPayload),
  }
}

export function emptyWorkflowDocument(): WorkflowDesignerDocument {
  return {
    id: null,
    name: '新建流程',
    description: '',
    trigger: 'manual',
    version: '0.1.0',
    revision: 0,
    nodes: [],
    edges: [],
  }
}

function nodeToDesigner(node: WorkspaceWorkflowNode): WorkflowDesignerNode {
  const kind = supportedKinds.has(node.type as SupportedWorkflowNodeKind)
    ? node.type as SupportedWorkflowNodeKind
    : 'tool'
  return {
    id: node.id,
    type: 'workflow',
    position: {
      x: Number(node.position?.x ?? 0),
      y: Number(node.position?.y ?? 0),
    },
    data: {
      label: node.name,
      kind,
      description: node.tool_name ?? '',
      status: 'idle',
      toolName: node.tool_name ?? null,
      parameters: structuredClone(node.parameters ?? {}),
    },
  }
}

function edgeToDesigner(edge: WorkspaceWorkflowEdge): WorkflowDesignerEdge {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.source_handle ?? undefined,
    targetHandle: edge.target_handle ?? undefined,
    type: 'smoothstep',
    label: edge.label ?? undefined,
  }
}

function nodeToPayload(node: WorkflowDesignerNode): WorkspaceWorkflowNode {
  return {
    id: node.id,
    name: node.data.label,
    type: node.data.kind,
    tool_name: node.data.toolName,
    parameters: serializeBindings(node.data.parameters) as Record<string, unknown>,
    position: { x: node.position.x, y: node.position.y },
  }
}

function serializeBindings(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(serializeBindings)
  if (!value || typeof value !== 'object') return value
  const record = value as Record<string, unknown>
  if (record.mode === 'input') {
    return { mode: 'input', input_key: record.inputKey ?? record.input_key ?? '' }
  }
  if (record.mode === 'node') {
    return {
      mode: 'node',
      node_id: record.nodeId ?? record.node_id ?? '',
      path: record.path ?? 'output',
    }
  }
  if (record.mode === 'expression') {
    return { mode: 'ref', value: record.expression ?? '' }
  }
  return Object.fromEntries(Object.entries(record).map(([key, item]) => [key, serializeBindings(item)]))
}

function edgeToPayload(edge: WorkflowDesignerEdge): WorkspaceWorkflowEdge {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    source_handle: edge.sourceHandle ?? null,
    target_handle: edge.targetHandle ?? null,
    label: typeof edge.label === 'string' ? edge.label : null,
    type: typeof edge.type === 'string' ? edge.type : null,
  }
}

function normalizeTrigger(trigger: string) {
  return trigger === 'file_uploaded' ? 'file_upload' : trigger
}
