import type { ToolDefinition } from '@/client/workspace'

export type WorkflowDesignerNodeKind = 'input' | 'tool'

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

