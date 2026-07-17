import type { ToolDefinition } from '@/client/workspace'
import type { Edge, Node } from '@vue-flow/core'

export type WorkflowDesignerNodeKind = 'input' | 'tool'

export type AdvancedWorkflowNodeKind = 'condition' | 'loop' | 'transform' | 'aggregate'
export type SupportedWorkflowNodeKind = 'input' | 'trigger' | 'tool' | AdvancedWorkflowNodeKind | 'output'

export type WorkflowNodeStatus = 'idle' | 'running' | 'success' | 'error' | 'skipped'

export interface WorkflowDesignerNodeData extends Record<string, unknown> {
  label: string
  kind: SupportedWorkflowNodeKind
  description: string
  status: WorkflowNodeStatus
  toolName: string | null
  parameters: Record<string, unknown>
}

export type WorkflowDesignerNode = Omit<Node<WorkflowDesignerNodeData>, 'data'> & {
  data: WorkflowDesignerNodeData
}
export type WorkflowDesignerEdge = Edge

export interface WorkflowDesignerDocument {
  id: string | null
  name: string
  description: string
  trigger: string
  version: string
  revision: number
  nodes: WorkflowDesignerNode[]
  edges: WorkflowDesignerEdge[]
}

export type WorkflowInputKind = 'text' | 'number' | 'json' | 'file' | 'knowledge_base'

export type WorkflowValueBinding =
  | { mode: 'literal'; value: unknown }
  | { mode: 'input'; inputKey: string }
  | { mode: 'node'; nodeId: string; path: string }
  | { mode: 'expression'; expression: string }

export interface WorkflowInputBlockConfig {
  key: string
  kind: WorkflowInputKind
  label: string
  description?: string
  required: boolean
  defaultValue?: unknown
}

export interface WorkflowInputOption {
  key: string
  label: string
  kind?: WorkflowInputKind
}

export interface WorkflowNodeOutputOption {
  label: string
  nodeId: string
  path: string
}

export type WorkflowPaletteNodePayload =
  | {
      kind: 'input'
      input: WorkflowInputBlockConfig
      label: string
    }
  | {
      kind: 'tool'
      label: string
      tool: ToolDefinition
      toolName: string
    }
  | {
      kind: AdvancedWorkflowNodeKind
      label: string
    }
