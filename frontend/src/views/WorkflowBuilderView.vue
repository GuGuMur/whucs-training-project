<script setup lang="ts">
import { computed, markRaw, nextTick, onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { storeToRefs } from 'pinia'
import type { NodeMouseEvent } from '@vue-flow/core'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import {
  ArrowLeft,
  Bot,
  Bug,
  CheckCircle2,
  CircleDot,
  Download,
  FileInput,
  GitBranch,
  GitMerge,
  History,
  Play,
  Plus,
  RefreshCw,
  Save,
  UploadCloud,
  Workflow,
  XCircle,
} from '@lucide/vue'

import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import AgentExecutionTimeline from '@/components/workflow/AgentExecutionTimeline.vue'
import AgentTaskCreateModal from '@/components/workflow/AgentTaskCreateModal.vue'
import AgentTaskDetailPanel from '@/components/workflow/AgentTaskDetailPanel.vue'
import AgentTaskList from '@/components/workflow/AgentTaskList.vue'
import WorkflowInputConfigForm from '@/components/workflow/WorkflowInputConfigForm.vue'
import WorkflowNodePalette from '@/components/workflow/WorkflowNodePalette.vue'
import WorkflowValueBindingEditor from '@/components/workflow/WorkflowValueBindingEditor.vue'
import ToolCatalogPanel from '@/components/workflow/ToolCatalogPanel.vue'
import ToolResultViewer from '@/components/workflow/ToolResultViewer.vue'
import { useAgentStore } from '@/stores/agent'
import { useWorkspaceStore } from '@/stores/workspace'
import type { ToolDefinition } from '@/client/workspace'
import type {
  WorkflowInputBlockConfig,
  WorkflowInputKind,
  WorkflowInputOption,
  WorkflowNodeOutputOption,
  WorkflowPaletteNodePayload,
  WorkflowValueBinding,
} from '@/components/workflow/workflowDesignerTypes'

type NodeStatus = 'idle' | 'running' | 'success' | 'error'
type ParamValue = string | number | boolean | string[] | Record<string, unknown> | WorkflowValueBinding | null

interface ToolNodeData {
  label: string
  kind: string
  description: string
  status: NodeStatus
  params: Record<string, ParamValue>
  input?: WorkflowInputBlockConfig
  toolName?: string | null
  inputType?: string | null
}

interface NodePreset {
  kind: string
  title: string
  description: string
  icon: object
  color: string
  params: Record<string, ParamValue>
}

interface WorkflowNode {
  id: string
  type?: string
  position: { x: number; y: number }
  class?: string
  data: ToolNodeData
}

interface WorkflowEdge {
  id: string
  source: string
  target: string
  animated?: boolean
  label?: string
  type?: string
}

interface ValidationIssue {
  type: 'error' | 'warning'
  title: string
  detail: string
}

const message = useMessage()
const workspace = useWorkspaceStore()
const agent = useAgentStore()
const { apiState, files, knowledgeBases, summary } = storeToRefs(workspace)
const {
  activeTask,
  executionSteps,
  finalAnswer,
  loading: agentLoading,
  isStreaming: agentStreaming,
  planPreview,
  resultView,
  taskHistory,
  tools: agentTools,
} = storeToRefs(agent)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'workflow')
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const flow = useVueFlow()
const selectedNodeId = ref<string | null>('start-1')
const showJson = ref(false)
const showVersionDrawer = ref(false)
const activeRunStep = ref(0)
const running = ref(false)
const executionProgress = ref(0)
const debugCollapsed = ref(true)
const debugHeight = ref(320)
const showAgentTaskModal = ref(false)
const versionLog = ref<string[]>([])

const templateWorkflows = computed(() =>
  workspace.workflows.filter((wf) => wf.status === 'template'),
)
const catalogTools = computed<ToolDefinition[]>(() =>
  agentTools.value.length ? agentTools.value : (workspace.tools as ToolDefinition[]),
)
const toolOptions = computed(() =>
  catalogTools.value.map((tool) => ({ label: tool.name, value: tool.name })),
)
const selectedToolDefinition = computed(() =>
  selectedData.value?.toolName
    ? catalogTools.value.find((tool) => tool.name === selectedData.value?.toolName) ?? null
    : null,
)
const selectedToolSchemaFields = computed(() => schemaFields(selectedToolDefinition.value))

function loadTemplateToCanvas(workflowId: string) {
  const template = templateWorkflows.value.find((wf) => wf.id === workflowId)
  if (!template) return
  flowName.value = template.name
  triggerMode.value = template.trigger
  nodes.value = (template.nodes ?? []).map((n: any) => ({
    id: n.id,
    type: n.type,
    position: n.position ?? { x: 80 + nodes.value.length * 48, y: 120 + nodes.value.length * 24 },
    class: `workflow-node is-${n.type || 'tool'}`,
      data: {
        label: n.name,
        kind: n.type || 'tool',
        description: n.tool_name || '',
        status: 'idle' as const,
        params: n.parameters ?? {},
        toolName: n.tool_name ?? null,
      },
  }))
  edges.value = (template.edges ?? []).map((e: any) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    animated: true,
    label: e.label ?? '',
    type: e.type ?? 'smoothstep',
  }))
  selectedNodeId.value = nodes.value[0]?.id ?? null
  activeWorkflowId.value = null
  message.success(`已加载模板「${template.name}」`)
  nextTick(() => flow.fitView({ padding: 0.25 }))
}

const nodePresets: NodePreset[] = [
  { kind: 'tool', title: '工具节点', description: '调用摘要、检索、分类等智能工具', icon: markRaw(Bot), color: '#246bfe', params: { tool: 'document-summarizer', timeout: 30, retry: 2 } },
  { kind: 'condition', title: '条件节点', description: '按规则分支，例如置信度或标签', icon: markRaw(GitBranch), color: '#7c3aed', params: { expression: 'confidence >= 0.8', trueLabel: '通过', falseLabel: '复核' } },
  { kind: 'loop', title: '循环节点', description: '遍历文件、段落或团队成员', icon: markRaw(RefreshCw), color: '#ea580c', params: { iterator: 'files', maxRounds: 5, breakOnError: true } },
  { kind: 'aggregate', title: '聚合节点', description: '汇总多个上游结果', icon: markRaw(GitMerge), color: '#0891b2', params: { strategy: 'merge', requireAll: true } },
  { kind: 'output', title: '输出节点', description: '输出文档、报告或通知', icon: markRaw(UploadCloud), color: '#16a34a', params: { format: 'docx', destination: 'team-space', notify: true } },
]


const triggerOptions = [
  { label: '手动触发', value: 'manual' },
  { label: '文件上传后', value: 'file_uploaded' },
  { label: '定时任务', value: 'schedule' },
  { label: 'WebSocket 事件', value: 'websocket' },
]

const activeWorkflowId = ref<string | null>(null)
const flowName = ref('')
const triggerMode = ref('manual')
const currentVersion = ref('0.1.0')
const nodes = ref<WorkflowNode[]>([])
const edges = ref<WorkflowEdge[]>([])

const selectedNode = computed<WorkflowNode | null>(() => nodes.value.find((node) => node.id === selectedNodeId.value) ?? null)
const selectedData = computed<ToolNodeData | null>(() => selectedNode.value?.data ?? null)
const selectedParams = computed<Record<string, ParamValue>>(() => selectedData.value?.params ?? {})
const selectedInputConfig = computed<WorkflowInputBlockConfig>({
  get() {
    return inputConfigFromData(selectedData.value)
  },
  set(config) {
    if (!selectedData.value || selectedData.value.kind !== 'input') return
    selectedData.value.input = config
    selectedData.value.inputType = config.kind
    selectedData.value.label = config.label
    selectedData.value.description = config.description ?? ''
    selectedData.value.params = inputParametersFromConfig(config)
  },
})
const workflowInputOptions = computed<WorkflowInputOption[]>(() =>
  nodes.value
    .filter((node) => node.data.kind === 'input')
    .map((node) => {
      const input = inputConfigFromData(node.data)
      return { key: input.key, kind: input.kind, label: input.label }
    }),
)
const selectedNodeOutputOptions = computed<WorkflowNodeOutputOption[]>(() => {
  if (!selectedNode.value) return []
  const upstreamIds = collectUpstreamNodeIds(selectedNode.value.id)
  return nodes.value
    .filter((node) => upstreamIds.has(node.id))
    .flatMap((node) => nodeOutputOptions(node))
})
const canvasAreaStyle = computed(() => ({
  height: debugCollapsed.value ? 'clamp(560px, calc(100vh - 270px), 780px)' : `calc(clamp(560px, calc(100vh - 270px), 780px) - ${debugHeight.value}px)`,
}))
const jsonDefinition = computed(() => JSON.stringify({
  name: flowName.value,
  version: currentVersion.value,
  trigger: triggerMode.value,
  nodes: workflowNodesPayload(),
  edges: workflowEdgesPayload(),
}, null, 2))

const validationIssues = computed<ValidationIssue[]>(() => {
  const issues: ValidationIssue[] = []
  const ids = new Set<string>()
  const targets = new Set<string>()
  const sources = new Set<string>()

  for (const node of nodes.value) ids.add(node.id)
  for (const edge of edges.value) {
    sources.add(edge.source)
    targets.add(edge.target)
    if (!ids.has(edge.source) || !ids.has(edge.target)) {
      issues.push({ type: 'error', title: '连线引用缺失', detail: `${edge.id} 指向了不存在的节点` })
    }
  }

  for (const node of nodes.value) {
    if (node.data.kind === 'tool') {
      if (!node.data.toolName) {
        issues.push({ type: 'error', title: '缺少工具', detail: `${node.data.label} 未选择工具` })
      } else if (!catalogTools.value.some((tool) => tool.name === node.data.toolName)) {
        issues.push({ type: 'error', title: '未知工具', detail: `${node.data.label} 引用了未注册工具 ${node.data.toolName}` })
      }
      const tool = catalogTools.value.find((item) => item.name === node.data.toolName)
      for (const field of schemaFields(tool ?? null)) {
        const value = node.data.params[field.key]
        if (field.required && isMissingParamValue(value)) {
          issues.push({ type: 'error', title: '缺少参数', detail: `${node.data.label} 缺少必填参数 ${field.key}` })
        }
      }
    } else if (Object.values(node.data.params).some((value) => value === null || value === undefined)) {
      issues.push({ type: 'error', title: '缺少参数', detail: `${node.data.label} 存在未填写参数` })
    }
    if (node.data.kind !== 'input' && !targets.has(node.id)) {
      issues.push({ type: 'warning', title: '孤立上游', detail: `${node.data.label} 没有上游输入` })
    }
    if (node.data.kind !== 'output' && !sources.has(node.id)) {
      issues.push({ type: 'warning', title: '孤立下游', detail: `${node.data.label} 没有连接到后续节点` })
    }
  }

  if (hasCycle()) {
    issues.push({ type: 'error', title: 'DAG 校验失败', detail: '流程中存在环，请删除回指连线' })
  }

  return issues
})

const hasBlockingIssue = computed(() => validationIssues.value.some((issue) => issue.type === 'error'))
const validationSummary = computed(() => (validationIssues.value.length === 0 ? 'DAG、参数与连线校验均通过' : `${validationIssues.value.length} 个问题待处理`))

onMounted(() => {
  void workspace.loadWorkspace()
  void agent.loadTools().catch(() => {
    message.warning('工具目录加载失败，已尝试使用工作区快照')
  })
  void agent.loadTaskHistory().catch(() => {
    message.warning('历史任务加载失败，可继续创建新任务')
  })
  nextTick(() => {
    flow.fitView({ padding: 0.25 })
    window.setTimeout(() => flow.fitView({ padding: 0.25 }), 120)
  })
})

function makeNode(id: string, kind: string, label: string, description: string, x: number, y: number, params: Record<string, ParamValue>, type?: string): WorkflowNode {
  return {
    id,
    type,
    position: { x, y },
    class: `workflow-node is-${kind}`,
    data: { label, kind, description, status: 'idle', params },
  }
}

function inputConfigFromData(data: ToolNodeData | null): WorkflowInputBlockConfig {
  if (data?.input) return data.input
  const rawKind = String(data?.inputType ?? data?.params.kind ?? 'text')
  const kind: WorkflowInputKind = ['text', 'number', 'json', 'file', 'knowledge_base'].includes(rawKind)
    ? rawKind as WorkflowInputKind
    : 'text'
  return {
    defaultValue: data?.params.defaultValue ?? defaultValueForInputKind(kind),
    description: data?.description ?? '',
    key: String(data?.params.key ?? defaultInputKey(kind)),
    kind,
    label: data?.label ?? '文本输入',
    required: Boolean(data?.params.required),
  }
}

function defaultInputKey(kind: WorkflowInputKind) {
  if (kind === 'file') return 'file_id'
  if (kind === 'knowledge_base') return 'target_kb_id'
  if (kind === 'json') return 'payload'
  return kind
}

function defaultValueForInputKind(kind: WorkflowInputKind) {
  if (kind === 'json') return {}
  if (kind === 'number') return 0
  return ''
}

function inputParametersFromConfig(config: WorkflowInputBlockConfig): Record<string, ParamValue> {
  return {
    [config.key]: { input_key: config.key, mode: 'input' },
    defaultValue: config.defaultValue as ParamValue,
    key: config.key,
    kind: config.kind,
    required: config.required,
  }
}

function presetByKind(kind: string) {
  return nodePresets.find((preset) => preset.kind === kind)
}

function nodeIcon(kind: string) {
  if (kind === 'input') return FileInput
  return presetByKind(kind)?.icon ?? CircleDot
}

function nodeColor(kind: string) {
  if (kind === 'input') return '#0f766e'
  return presetByKind(kind)?.color ?? '#64748b'
}

function hasCycle() {
  const graph = new Map<string, string[]>()
  nodes.value.forEach((node) => graph.set(node.id, []))
  edges.value.forEach((edge) => graph.get(edge.source)?.push(edge.target))

  const visiting = new Set<string>()
  const visited = new Set<string>()

  function dfs(id: string): boolean {
    if (visiting.has(id)) return true
    if (visited.has(id)) return false
    visiting.add(id)
    for (const next of graph.get(id) ?? []) {
      if (dfs(next)) return true
    }
    visiting.delete(id)
    visited.add(id)
    return false
  }

  return nodes.value.some((node) => dfs(node.id))
}

function collectUpstreamNodeIds(nodeId: string) {
  const incoming = new Map<string, string[]>()
  edges.value.forEach((edge) => {
    incoming.set(edge.target, [...(incoming.get(edge.target) ?? []), edge.source])
  })
  const result = new Set<string>()
  const visit = (id: string) => {
    for (const source of incoming.get(id) ?? []) {
      if (result.has(source)) continue
      result.add(source)
      visit(source)
    }
  }
  visit(nodeId)
  return result
}

function nodeOutputOptions(node: WorkflowNode): WorkflowNodeOutputOption[] {
  const baseLabel = node.data.label || node.id
  const options: WorkflowNodeOutputOption[] = [
    { label: `${baseLabel} · output`, nodeId: node.id, path: 'output' },
  ]
  if (node.data.kind === 'input') {
    const input = inputConfigFromData(node.data)
    options.push({ label: `${baseLabel} · ${input.key}`, nodeId: node.id, path: `output.${input.key}` })
  } else if (node.data.kind === 'tool') {
    options.push(
      { label: `${baseLabel} · result`, nodeId: node.id, path: 'output.result' },
      { label: `${baseLabel} · summary`, nodeId: node.id, path: 'output.summary' },
    )
  }
  return options
}

function onNodeClick(event: NodeMouseEvent) {
  selectedNodeId.value = event.node.id
}

function onPresetDragStart(event: DragEvent, preset: NodePreset) {
  event.dataTransfer?.setData('application/vueflow', JSON.stringify({ kind: 'preset', value: preset.kind }))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDrop(event: DragEvent) {
  const payload = parseDragPayload(
    event.dataTransfer?.getData('application/x-whucs-workflow-node')
      || event.dataTransfer?.getData('application/vueflow')
      || '',
  )
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = flow.project({ x: event.clientX - bounds.left, y: event.clientY - bounds.top })
  addNodeFromPalettePayload(payload, position.x, position.y)
}

function parseDragPayload(raw: string): WorkflowPaletteNodePayload | { kind: 'preset'; value: string } {
  try {
    const parsed = JSON.parse(raw) as WorkflowPaletteNodePayload | { kind?: string; value?: string }
    if (parsed.kind === 'input' || parsed.kind === 'tool') return parsed as WorkflowPaletteNodePayload
    return { kind: 'preset', value: ('value' in parsed ? parsed.value : raw) || raw }
  } catch {
    return { kind: 'preset', value: raw }
  }
}

function handlePaletteAddNode(payload: WorkflowPaletteNodePayload) {
  addNodeFromPalettePayload(payload, 260 + nodes.value.length * 48, 120 + nodes.value.length * 24)
  nextTick(() => flow.fitView({ padding: 0.25 }))
}

function addNodeFromPalettePayload(payload: WorkflowPaletteNodePayload | { kind: 'preset'; value: string }, x: number, y: number) {
  if (payload.kind === 'tool') {
    addNodeFromTool(payload.tool, x, y)
    return
  }
  if (payload.kind === 'input') {
    addNodeFromInput(payload.input, x, y)
    return
  }
  const preset = presetByKind(payload.value)
  if (preset) addNodeFromPreset(preset, x, y)
}

function addPresetNode(preset: NodePreset) {
  addNodeFromPreset(preset, 260 + nodes.value.length * 48, 120 + nodes.value.length * 24)
  nextTick(() => flow.fitView({ padding: 0.25 }))
}

function addNodeFromPreset(preset: NodePreset, x: number, y: number) {
  const id = `${preset.kind}-${Date.now().toString(36)}`
  nodes.value.push(makeNode(id, preset.kind, preset.title, preset.description, x, y, { ...preset.params }, preset.kind === 'output' ? preset.kind : undefined))
  selectedNodeId.value = id
  message.success(`已添加${preset.title}`)
}

function addNodeFromInput(input: WorkflowInputBlockConfig, x: number, y: number) {
  const normalizedInput = {
    ...input,
    key: input.key || defaultInputKey(input.kind),
  }
  const id = `input-${normalizedInput.key}-${Date.now().toString(36)}`
  const params = inputParametersFromConfig(normalizedInput)
  nodes.value.push({
    ...makeNode(id, 'input', normalizedInput.label, normalizedInput.description ?? '', x, y, params, 'input'),
    data: {
      label: normalizedInput.label,
      kind: 'input',
      description: normalizedInput.description ?? '',
      status: 'idle',
      params,
      input: normalizedInput,
      inputType: normalizedInput.kind,
    },
  })
  selectedNodeId.value = id
  message.success(`已添加输入块「${normalizedInput.label}」`)
}

function addNodeFromTool(tool: ToolDefinition, x: number, y: number) {
  const id = `tool-${tool.name}-${Date.now().toString(36)}`
  const params = defaultParamsFromSchema(tool)
  nodes.value.push({
    ...makeNode(id, 'tool', tool.name, tool.description, x, y, params),
    data: {
      label: tool.name,
      kind: 'tool',
      description: tool.description,
      status: 'idle',
      params,
      toolName: tool.name,
    },
  })
  selectedNodeId.value = id
  message.success(`已添加工具「${tool.name}」`)
}

function updateParam(key: string, value: ParamValue) {
  if (!selectedData.value) return
  selectedData.value.params[key] = value
}

function updateToolName(toolName: string | null) {
  if (!selectedData.value) return
  const tool = catalogTools.value.find((item) => item.name === toolName)
  selectedData.value.toolName = toolName
  if (tool) {
    selectedData.value.label = tool.name
    selectedData.value.description = tool.description
    selectedData.value.params = defaultParamsFromSchema(tool, selectedData.value.params)
  }
}

function schemaFields(tool: ToolDefinition | null) {
  const properties = tool?.input_schema?.properties
  if (!properties || typeof properties !== 'object') return []
  const rawRequired = tool?.input_schema?.required
  const required = new Set(Array.isArray(rawRequired) ? rawRequired.map(String) : [])
  return Object.entries(properties as Record<string, Record<string, unknown>>).map(([key, schema]) => ({
    key,
    required: required.has(key),
    schema,
    type: String(schema?.type ?? 'string'),
  }))
}

function defaultParamsFromSchema(tool: ToolDefinition, existing: Record<string, ParamValue> = {}) {
  const params: Record<string, ParamValue> = {}
  for (const field of schemaFields(tool)) {
    if (field.key in existing) {
      params[field.key] = bindingValue(existing[field.key])
      continue
    }
    params[field.key] = { mode: 'literal', value: defaultLiteralValueForSchemaField(field.type) }
  }
  return params
}

function defaultLiteralValueForSchemaField(type: string) {
  if (type === 'integer' || type === 'number') return 0
  if (type === 'boolean') return false
  if (type === 'array') return []
  if (type === 'object') return {}
  return ''
}

function bindingValue(value: ParamValue | undefined): WorkflowValueBinding {
  if (isWorkflowValueBinding(value)) return value
  return { mode: 'literal', value: value ?? '' }
}

function isMissingParamValue(value: ParamValue | undefined) {
  if (isWorkflowValueBinding(value)) {
    if (value.mode !== 'literal') return false
    const literal = value.value
    return literal === '' || literal === null || literal === undefined || (Array.isArray(literal) && literal.length === 0)
  }
  return value === '' || value === null || value === undefined || (Array.isArray(value) && value.length === 0)
}

function isWorkflowValueBinding(value: unknown): value is WorkflowValueBinding {
  if (!value || typeof value !== 'object') return false
  const mode = (value as { mode?: unknown }).mode
  return mode === 'literal' || mode === 'input' || mode === 'node' || mode === 'expression'
}

function serializeParamValue(value: ParamValue | undefined): unknown {
  if (Array.isArray(value)) return value.map((item) => serializeParamValue(item as ParamValue))
  if (isWorkflowValueBinding(value)) {
    if (value.mode === 'literal') return { mode: 'literal', value: value.value }
    if (value.mode === 'input') return { input_key: value.inputKey, mode: 'input' }
    if (value.mode === 'node') return { mode: 'node', node_id: value.nodeId, path: value.path }
    return { mode: 'ref', value: value.expression }
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, serializeParamValue(item as ParamValue)]),
    )
  }
  return value
}

function arrayParamValue(value: ParamValue | undefined) {
  return Array.isArray(value) ? value : []
}

function collectWorkflowInputs() {
  const inputs: Record<string, unknown> = {}
  for (const node of nodes.value) {
    if (node.data.kind !== 'input') continue
    const config = inputConfigFromData(node.data)
    if (config.defaultValue !== undefined) {
      inputs[config.key] = config.defaultValue
    }
  }
  return inputs
}

function workflowNodeParametersPayload(node: WorkflowNode) {
  if (node.data.kind !== 'input') {
    return Object.fromEntries(
      Object.entries(node.data.params).map(([key, value]) => [key, serializeParamValue(value)]),
    )
  }
  const config = inputConfigFromData(node.data)
  return {
    [config.key]: { input_key: config.key, mode: 'input' },
  }
}

function workflowNodesPayload() {
  return nodes.value.map((node) => ({
    id: node.id,
    name: node.data.label,
    type: node.data.kind,
    tool_name: node.data.toolName || null,
    parameters: workflowNodeParametersPayload(node),
    position: node.position,
  }))
}

function workflowEdgesPayload() {
  return edges.value.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    source_handle: null,
    target_handle: null,
  }))
}

async function saveFlow() {
  try {
    const payload = { name: flowName.value || '新建流程', trigger: triggerMode.value, nodes: workflowNodesPayload() as any, edges: workflowEdgesPayload() as any }
    if (activeWorkflowId.value) {
      await workspace.updateWorkflow(activeWorkflowId.value, payload)
    } else {
      const created = await workspace.createWorkflow({ ...payload, description: null })
      activeWorkflowId.value = created.id
    }
    versionLog.value.unshift(`${currentVersion.value} 保存于 ${new Date().toLocaleString()}`)
    message.success('流程定义已保存到服务端')
  } catch { message.error('保存失败') }
}

function validateFlow() {
  if (validationIssues.value.length === 0) message.success('校验通过，可以执行')
  else message.warning(validationSummary.value)
}

async function runFlow() {
  validateFlow()
  if (hasBlockingIssue.value) return
  if (!activeWorkflowId.value) { message.warning('请先保存流程定义'); return }
  try {
    running.value = true
    executionProgress.value = 5
    activeRunStep.value = 1
    nodes.value.forEach((node) => {
      node.data.status = 'running'
    })
    const inputs = collectWorkflowInputs()
    const exec = await workspace.executeWorkflow(activeWorkflowId.value, {
      fileId: typeof inputs.file_id === 'string' ? inputs.file_id : null,
      inputs,
      targetKbId: typeof inputs.target_kb_id === 'string' ? inputs.target_kb_id : null,
    })
    applyWorkflowExecutionToCanvas(exec)
    versionLog.value.unshift(`执行完成: ${exec.status} (${new Date().toLocaleString()})`)
    if (exec.status === 'failed') message.error('流程执行失败')
    else message.success('流程执行完成')
  } catch {
    nodes.value.forEach((node) => {
      if (node.data.status === 'running') node.data.status = 'error'
    })
    executionProgress.value = 100
    message.error('流程执行失败')
  } finally { running.value = false }
}

function applyWorkflowExecutionToCanvas(exec: Awaited<ReturnType<typeof workspace.executeWorkflow>>) {
  const statusByNodeId = new Map(exec.node_executions.map((item) => [item.node_id, item.status]))
  nodes.value.forEach((node) => {
    const status = statusByNodeId.get(node.id)
    if (status === 'success') node.data.status = 'success'
    else if (status === 'failed') node.data.status = 'error'
    else node.data.status = exec.status === 'failed' ? 'idle' : 'success'
  })
  activeRunStep.value = exec.node_executions.length
  executionProgress.value = 100
}

const debugStepResult = ref<{ done?: boolean; node_name?: string; status?: string; remaining?: number } | null>(null)

async function singleStep() {
  const nodeLabel = selectedData.value?.label ?? (flowName.value || '当前流程')
  try {
    const task = await agent.createTask({
      contextFileIds: [],
      kbId: null,
      task: `调试流程节点：${nodeLabel}`,
    })
    debugStepResult.value = {
      done: task.status === 'completed',
      node_name: nodeLabel,
      status: task.status,
      remaining: task.status === 'needs_clarification' ? 1 : 0,
    }
    executionProgress.value = task.status === 'completed' || task.status === 'cancelled' ? 100 : 50
    message.success(task.status === 'needs_clarification' ? '需要补充参数' : '智能体调试已执行')
  } catch { message.error('单步调试失败') }
}

function resetRunState() {
  debugStepResult.value = null
  nodes.value.forEach((node) => (node.data.status = 'idle'))
  executionProgress.value = 0
  activeRunStep.value = 0
}

async function submitAgentTask(payload: { task: string; kbId?: string | null; contextFileIds?: string[] }) {
  try {
    await agent.createTask(payload)
    executionProgress.value = activeTask.value?.status === 'completed' || activeTask.value?.status === 'cancelled' ? 100 : 50
  } catch {
    message.error('智能体任务执行失败')
  }
}

async function previewAgentTask(payload: { task: string; kbId?: string | null; contextFileIds?: string[] }) {
  try {
    await agent.previewTaskPlan(payload)
  } catch {
    message.error('智能体计划预览失败')
  }
}

async function streamAgentTaskAction(payload: { task: string; kbId?: string | null; contextFileIds?: string[] }) {
  try {
    await agent.createTaskStream(payload)
    executionProgress.value = activeTask.value?.status === 'completed' || activeTask.value?.status === 'cancelled' ? 100 : 75
  } catch {
    message.error('智能体流式执行失败')
  }
}

async function continueActiveAgentTask(payload: { inputs?: Record<string, unknown>; message?: string | null }) {
  if (!activeTask.value) return
  try {
    await agent.continueTask(activeTask.value.id, payload)
    executionProgress.value = activeTask.value?.status === 'completed' || activeTask.value?.status === 'cancelled' ? 100 : 75
  } catch {
    message.error('智能体任务继续执行失败')
  }
}

async function loadAgentTask(taskId: string) {
  try {
    await agent.loadTask(taskId)
  } catch {
    message.error('历史任务加载失败')
  }
}

async function deleteAgentTaskAction(taskId: string) {
  try {
    await agent.deleteTask(taskId)
    message.success('任务已删除')
  } catch {
    message.error('任务删除失败')
  }
}

async function cancelAgentTask(taskId: string) {
  try {
    await agent.cancelTask(taskId)
    executionProgress.value = 100
  } catch {
    message.error('任务取消失败')
  }
}

function openAgentTaskModal() {
  agent.clearPlanPreview()
  showAgentTaskModal.value = true
}

function toggleDebugPanel() {
  debugCollapsed.value = !debugCollapsed.value
  nextTick(() => flow.fitView({ padding: 0.25 }))
}

function startDebugResize(event: MouseEvent) {
  event.preventDefault()
  const startY = event.clientY
  const startHeight = debugHeight.value
  const onMove = (moveEvent: MouseEvent) => {
    const nextHeight = startHeight - (moveEvent.clientY - startY)
    debugHeight.value = Math.min(460, Math.max(240, nextHeight))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}
</script>

<template>
  <component :is="workspaceLayout" :api-state-label="apiStateLabel" :api-state-type="apiStateType" :nav-items="navItems"
    :unread-notifications="summary.unread_notifications" page-title="工具流编排">
    <section class="workflow-builder">
      <div class="agent-console-heading">
        <div>
          <h1 class="agent-console-heading__title">智能体任务</h1>
          <p class="agent-console-heading__subtitle">创建、查看和管理自然语言工具流任务</p>
        </div>
        <NButton type="primary" @click="openAgentTaskModal">
          <template #icon><NIcon aria-hidden="true"><Plus /></NIcon></template>
          创建任务
        </NButton>
      </div>

      <section class="agent-console" aria-label="智能体任务控制台">
        <div class="agent-console__main">
          <section class="agent-composer-panel" aria-label="智能体任务列表">
            <AgentTaskList
              :active-task-id="activeTask?.id"
              :loading="agentLoading || agentStreaming"
              :tasks="taskHistory"
              @delete-task="deleteAgentTaskAction"
              @select-task="loadAgentTask"
            />
          </section>

          <section class="agent-console__results" aria-label="智能体执行结果">
            <AgentExecutionTimeline v-if="executionSteps.length" :steps="executionSteps" />
            <NEmpty v-else size="small" description="提交任务后展示执行轨迹" />
            <ToolResultViewer :final-answer="finalAnswer" :result-view="resultView" />
          </section>
        </div>

        <aside class="agent-console__side">
          <AgentTaskDetailPanel
            :active-task="activeTask"
            :loading="agentLoading"
            @cancel="cancelAgentTask"
            @continue="continueActiveAgentTask"
          />
          <ToolCatalogPanel :tools="catalogTools" />
        </aside>
      </section>
      <AgentTaskCreateModal
        v-model:show="showAgentTaskModal"
        :files="files"
        :knowledge-bases="knowledgeBases"
        :loading="agentLoading || agentStreaming"
        :plan-preview="planPreview"
        @preview="previewAgentTask"
        @stream="streamAgentTaskAction"
        @submit="submitAgentTask"
      />
    </section>

    <NModal v-model:show="showJson" preset="card" title="流程定义 JSON" class="json-modal">
      <div class="json-code-panel">
        <NCode :code="jsonDefinition" language="json" word-wrap />
      </div>
    </NModal>

    <NDrawer v-model:show="showVersionDrawer" :width="360">
      <NDrawerContent title="版本记录">
        <NDescriptions :column="1" bordered size="small">
          <NDescriptionsItem v-for="item in versionLog" :key="item" label="记录">{{ item }}</NDescriptionsItem>
        </NDescriptions>
      </NDrawerContent>
    </NDrawer>
  </component>
</template>

<style scoped>
.workflow-builder {
  display: grid;
  gap: 4px;
}

.agent-console-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.agent-console-heading__title {
  margin: 0;
  color: #172033;
  font-size: 20px;
  font-weight: 800;
}

.agent-console-heading__subtitle {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 13px;
}

.agent-console {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 14px;
  align-items: start;
}

.agent-console__main,
.agent-console__side,
.agent-console__results {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.agent-console__side {
  align-content: start;
}

.builder-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.builder-heading .eyebrow {
  margin: 14px 0 4px;
  color: #64748b;
  font-size: 13px;
}

.builder-heading h2 {
  margin: 0;
  color: #172033;
  font-size: 30px;
  font-weight: 800;
  line-height: 1.2;
}

.builder-heading span {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 14px;
}

.builder-shell {
  display: grid;
  grid-template-columns: 292px minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
  height: clamp(620px, calc(100vh - 190px), 900px);
  min-height: 0;
}

.builder-sidebar {
  display: grid;
  align-content: start;
  gap: 12px;
  max-height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.builder-main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto auto;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}

.builder-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #e8eef6;
  background: rgba(255, 255, 255, 0.95);
}

.builder-card {
  overflow: hidden;
  border: 1px solid #e8eef6;
  border-radius: 8px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
}

.agent-composer-panel {
  padding: 12px;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #f8fafd;
}

.title-input {
  width: 340px;
}

.trigger-select {
  width: 168px;
}

.node-palette {
  display: grid;
  gap: 10px;
  max-height: 220px;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.palette-item {
  display: grid;
  grid-template-columns: 38px 1fr 18px;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 10px;
  color: #334155;
  text-align: left;
  cursor: grab;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  border: 1px solid #e8eef6;
  border-radius: 8px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.palette-item:hover {
  border-color: #93c5fd;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.1);
  transform: translateY(-1px);
}

.palette-icon,
.detail-icon,
.node-icon {
  display: grid;
  place-items: center;
  border-radius: 8px;
}

.palette-icon {
  width: 36px;
  height: 36px;
  font-size: 20px;
}

.palette-item strong,
.palette-item small {
  display: block;
}

.palette-item strong {
  color: #1e293b;
  font-size: 14px;
  font-weight: 750;
}

.palette-item small {
  margin-top: 2px;
  color: #64748b;
  line-height: 1.35;
}

.issue-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.issue-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  color: #475569;
  font-size: 12px;
}

.canvas-area {
  width: 100%;
  min-width: 0;
  min-height: 420px;
  overflow: hidden;
  padding: 12px 12px 0;
}

.workflow-canvas {
  overflow: hidden;
  width: 100%;
  height: 100%;
  background: linear-gradient(rgba(36, 107, 254, 0.025), rgba(36, 107, 254, 0.025)), #fbfdff;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.debug-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.94);
  border-top: 1px solid #e8eef6;
}

.debug-entry strong {
  display: block;
  color: #172033;
  font-size: 15px;
  font-weight: 800;
}

.debug-entry span {
  display: block;
  margin-top: 2px;
  color: #64748b;
  font-size: 12px;
}

.debug-panel {
  position: relative;
  overflow: auto;
  min-height: 240px;
  max-height: 460px;
  background: #fff;
  border-top: 1px solid #d8e0ea;
  box-shadow: 0 -10px 24px rgba(15, 23, 42, 0.055);
}

.resize-handle {
  position: sticky;
  top: 0;
  z-index: 4;
  height: 10px;
  cursor: row-resize;
  background: #fff;
}

.resize-handle::after {
  position: absolute;
  top: 4px;
  left: 50%;
  width: 56px;
  height: 2px;
  content: '';
  background: #cbd5e1;
  border-radius: 999px;
  transform: translateX(-50%);
}

.resize-handle:hover::after {
  background: #246bfe;
}

.debug-panel-body {
  display: grid;
  grid-template-columns: 280px minmax(320px, 1fr) 320px;
  gap: 12px;
  padding: 0 12px 12px;
}

.grow-card {
  min-height: 300px;
}

.run-actions {
  margin-top: 12px;
}

.detail-icon {
  width: 40px;
  height: 40px;
  font-size: 22px;
}

.custom-node {
  width: 230px;
  padding: 13px;
  color: #172033;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #cbd5e1;
  border-left: 5px solid #246bfe;
  border-radius: 8px;
  box-shadow: 0 16px 34px rgba(30, 41, 59, 0.14);
  backdrop-filter: blur(8px);
}

.input-node {
  border-left-color: #0f766e;
}

.output-node {
  border-left-color: #16a34a;
}

.status-running {
  box-shadow: 0 0 0 4px rgba(36, 107, 254, 0.16), 0 16px 34px rgba(30, 41, 59, 0.14);
}

.status-success {
  border-color: #86efac;
  background: #f0fdf4;
}

.status-error {
  border-color: #fecaca;
  background: #fef2f2;
}

.node-head {
  display: flex;
  gap: 9px;
  align-items: center;
  color: #172033;
  font-weight: 800;
}

@media (max-width: 1080px) {
  .agent-console,
  .builder-shell {
    grid-template-columns: 1fr;
    height: auto;
  }
}

.node-icon {
  width: 30px;
  height: 30px;
  font-size: 16px;
}

.custom-node p {
  min-height: 40px;
  margin: 9px 0 10px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

.json-modal {
  width: min(860px, calc(100vw - 32px));
}

.json-code-panel {
  overflow: auto;
  max-width: 100%;
  max-height: 62vh;
  border-radius: 8px;
  background: #0f172a;
  padding: 14px;
}

.json-code-panel :deep(.n-code) {
  min-width: 0;
  font-size: 12px;
  line-height: 1.55;
}

:deep(.vue-flow__node.selected .custom-node) {
  border-color: #246bfe;
  box-shadow: 0 0 0 4px rgba(36, 107, 254, 0.16), 0 18px 36px rgba(15, 23, 42, 0.16);
}

:deep(.vue-flow__edge-path) {
  stroke: #64748b;
  stroke-width: 2;
}

:deep(.vue-flow__edge.animated path) {
  stroke: #246bfe;
}

:deep(.vue-flow__controls) {
  overflow: hidden;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

:deep(.vue-flow__minimap) {
  overflow: hidden;
  border: 1px solid #e8eef6;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.agent-steps-timeline {
  display: grid;
  gap: 0;
}

.agent-step-item {
  display: flex;
  gap: 12px;
  padding: 10px 0;
}

.agent-step-item:not(:last-child) {
  border-left: 2px solid #e8eef6;
  margin-left: 7px;
  padding-left: 23px;
}

.step-marker {
  position: relative;
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 16px;
  height: 16px;
  margin-top: 2px;
  margin-left: -8px;
  border: 2px solid;
  border-radius: 50%;
}

.step-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.step-detail {
  flex: 1;
  min-width: 0;
}

.step-header {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.step-badge {
  padding: 1px 6px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  white-space: nowrap;
}

.step-title {
  color: #172033;
  font-size: 13px;
  font-weight: 700;
}

.step-content {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 1100px) {
  .agent-console-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .builder-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .builder-shell {
    grid-template-columns: 1fr;
  }

  .canvas-area {
    height: 620px !important;
  }

  .debug-entry {
    align-items: flex-start;
    flex-direction: column;
  }

  .debug-panel {
    height: auto !important;
    max-height: none;
  }

  .debug-panel-body {
    grid-template-columns: 1fr;
  }

  .resize-handle {
    display: none;
  }
}
</style>
