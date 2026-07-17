import { computed, shallowRef } from 'vue'
import type { Connection } from '@vue-flow/core'

import type { ToolDefinition, WorkspaceWorkflow } from '@/client/workspace'
import {
  designerToWorkflowPayload,
  emptyWorkflowDocument,
  workflowToDesigner,
} from '@/components/workflow/workflowCodec'
import type {
  AdvancedWorkflowNodeKind,
  SupportedWorkflowNodeKind,
  WorkflowDesignerDocument,
  WorkflowDesignerEdge,
  WorkflowDesignerNode,
} from '@/components/workflow/workflowDesignerTypes'

export function useWorkflowDesigner() {
  const initial = emptyWorkflowDocument()
  const workflowId = shallowRef<string | null>(initial.id)
  const name = shallowRef(initial.name)
  const description = shallowRef(initial.description)
  const trigger = shallowRef(initial.trigger)
  const version = shallowRef(initial.version)
  const revision = shallowRef(initial.revision)
  const nodes = shallowRef<WorkflowDesignerNode[]>(initial.nodes)
  const edges = shallowRef<WorkflowDesignerEdge[]>(initial.edges)
  const selectedNodeId = shallowRef<string | null>(null)
  const selectedEdgeId = shallowRef<string | null>(null)
  const baseline = shallowRef(snapshot())
  const undoStack = shallowRef<string[]>([])
  const redoStack = shallowRef<string[]>([])

  const document = computed<WorkflowDesignerDocument>(() => ({
    id: workflowId.value,
    name: name.value,
    description: description.value,
    trigger: trigger.value,
    version: version.value,
    revision: revision.value,
    nodes: nodes.value,
    edges: edges.value,
  }))
  const selectedNode = computed(() =>
    nodes.value.find((node) => node.id === selectedNodeId.value) ?? null,
  )
  const isDirty = computed(() => snapshot() !== baseline.value)
  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  function hydrate(workflow: WorkspaceWorkflow) {
    setDocument(workflowToDesigner(workflow))
    markSaved()
  }

  function reset() {
    setDocument(emptyWorkflowDocument())
    markSaved()
  }

  function setDocument(next: WorkflowDesignerDocument) {
    workflowId.value = next.id
    name.value = next.name
    description.value = next.description
    trigger.value = next.trigger
    version.value = next.version
    revision.value = next.revision
    nodes.value = structuredClone(next.nodes)
    edges.value = structuredClone(next.edges)
    selectedNodeId.value = nodes.value[0]?.id ?? null
    selectedEdgeId.value = null
  }

  function checkpoint() {
    const current = snapshot()
    if (undoStack.value[undoStack.value.length - 1] === current) return
    undoStack.value = [...undoStack.value.slice(-49), current]
    redoStack.value = []
  }

  function restoreSnapshot(value: string) {
    setDocument(JSON.parse(value) as WorkflowDesignerDocument)
  }

  function undo() {
    const previous = undoStack.value[undoStack.value.length - 1]
    if (!previous) return
    redoStack.value = [...redoStack.value, snapshot()]
    undoStack.value = undoStack.value.slice(0, -1)
    restoreSnapshot(previous)
  }

  function redo() {
    const next = redoStack.value[redoStack.value.length - 1]
    if (!next) return
    undoStack.value = [...undoStack.value, snapshot()]
    redoStack.value = redoStack.value.slice(0, -1)
    restoreSnapshot(next)
  }

  function addInputNode(position = { x: 80, y: 120 }) {
    addNode('input', '文本输入', position, null, {
      input_text: { mode: 'input', input_key: 'input_text' },
    })
  }

  function addOutputNode(position = { x: 680, y: 120 }) {
    addNode('output', '流程输出', position, null, {})
  }

  function addToolNode(tool: ToolDefinition, position = { x: 360, y: 120 }) {
    const parameters = Object.fromEntries(
      Object.keys(tool.input_schema?.properties ?? {}).map((key) => [key, { mode: 'literal', value: '' }]),
    )
    addNode('tool', tool.name, position, tool.name, parameters, tool.description)
  }

  function addAdvancedNode(kind: AdvancedWorkflowNodeKind, position = { x: 500, y: 220 }) {
    const presets: Record<AdvancedWorkflowNodeKind, { label: string; description: string; parameters: Record<string, unknown> }> = {
      condition: { label: '条件分支', description: '按条件选择 true / false 出边', parameters: { left: { mode: 'literal', value: '' }, operator: 'truthy', right: { mode: 'literal', value: '' } } },
      transform: { label: '数据转换', description: '执行安全的结构化数据转换', parameters: { value: { mode: 'literal', value: {} }, operation: 'identity' } },
      loop: { label: '数组循环', description: '有上限地逐项投影数组', parameters: { items: { mode: 'literal', value: [] }, path: '', max_iterations: 100 } },
      aggregate: { label: '数据聚合', description: '汇总数组中的值', parameters: { values: { mode: 'literal', value: [] }, operation: 'collect', separator: ', ' } },
    }
    const preset = presets[kind]
    addNode(kind, preset.label, position, null, preset.parameters, preset.description)
  }

  function addNode(
    kind: SupportedWorkflowNodeKind,
    label: string,
    position: { x: number; y: number },
    toolName: string | null,
    parameters: Record<string, unknown>,
    descriptionText = '',
  ) {
    checkpoint()
    const id = `${kind}-${crypto.randomUUID()}`
    nodes.value = [...nodes.value, {
      id,
      type: 'workflow',
      position,
      data: {
        label,
        kind,
        description: descriptionText,
        status: 'idle',
        toolName,
        parameters,
      },
    }]
    selectedNodeId.value = id
  }

  function connect(connection: Connection) {
    if (!connection.source || !connection.target || connection.source === connection.target) return false
    if (edges.value.some((edge) => edge.source === connection.source && edge.target === connection.target)) return false
    const source = nodes.value.find((node) => node.id === connection.source)
    const target = nodes.value.find((node) => node.id === connection.target)
    if (!source || !target || source.data.kind === 'output' || ['input', 'trigger'].includes(target.data.kind)) return false
    checkpoint()
    edges.value = [...edges.value, {
      id: `edge-${crypto.randomUUID()}`,
      source: connection.source,
      target: connection.target,
      sourceHandle: connection.sourceHandle ?? undefined,
      targetHandle: connection.targetHandle ?? undefined,
      type: 'smoothstep',
    }]
    return true
  }

  function removeSelection() {
    const nodeId = selectedNodeId.value
    if (!nodeId && !selectedEdgeId.value) return
    checkpoint()
    if (nodeId) {
      nodes.value = nodes.value.filter((node) => node.id !== nodeId)
      edges.value = edges.value.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
    } else if (selectedEdgeId.value) {
      edges.value = edges.value.filter((edge) => edge.id !== selectedEdgeId.value)
    }
    selectedNodeId.value = null
    selectedEdgeId.value = null
  }

  function updateSelectedNode(patch: Partial<WorkflowDesignerNode['data']>) {
    if (!selectedNodeId.value) return
    checkpoint()
    nodes.value = nodes.value.map((node) => node.id === selectedNodeId.value
      ? { ...node, data: { ...node.data, ...patch } }
      : node)
  }

  function markSaved(workflow?: WorkspaceWorkflow) {
    if (workflow) setDocument(workflowToDesigner(workflow))
    baseline.value = snapshot()
    undoStack.value = []
    redoStack.value = []
  }

  function payload() {
    return designerToWorkflowPayload(document.value)
  }

  function snapshot() {
    return JSON.stringify({
      id: workflowId.value,
      name: name.value,
      description: description.value,
      trigger: trigger.value,
      version: version.value,
      revision: revision.value,
      nodes: nodes.value.map((node) => ({
        id: node.id,
        type: 'workflow',
        position: { x: node.position.x, y: node.position.y },
        data: {
          label: node.data.label,
          kind: node.data.kind,
          description: node.data.description,
          status: 'idle',
          toolName: node.data.toolName,
          parameters: node.data.parameters,
        },
      })),
      edges: edges.value.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
        type: edge.type,
        label: edge.label,
      })),
    })
  }

  return {
    connect,
    canRedo,
    canUndo,
    checkpoint,
    description,
    document,
    edges,
    hydrate,
    isDirty,
    markSaved,
    name,
    nodes,
    payload,
    removeSelection,
    redo,
    reset,
    selectedEdgeId,
    selectedNode,
    selectedNodeId,
    trigger,
    undo,
    version,
    revision,
    workflowId,
    addInputNode,
    addOutputNode,
    addToolNode,
    addAdvancedNode,
    updateSelectedNode,
  }
}
