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
import AgentTaskDetailPanel from '@/components/workflow/AgentTaskDetailPanel.vue'
import AgentTaskComposer from '@/components/workflow/AgentTaskComposer.vue'
import ToolCatalogPanel from '@/components/workflow/ToolCatalogPanel.vue'
import ToolResultViewer from '@/components/workflow/ToolResultViewer.vue'
import { useAgentStore } from '@/stores/agent'
import { useWorkspaceStore } from '@/stores/workspace'

type NodeStatus = 'idle' | 'running' | 'success' | 'error'
type ParamValue = string | number | boolean | string[]

interface ToolNodeData {
  label: string
  kind: string
  description: string
  status: NodeStatus
  params: Record<string, ParamValue>
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
  clarificationQuestion,
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
const versionLog = ref<string[]>([])

const templateWorkflows = computed(() =>
  workspace.workflows.filter((wf) => wf.status === 'template'),
)

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
const canvasAreaStyle = computed(() => ({
  height: debugCollapsed.value ? 'clamp(560px, calc(100vh - 270px), 780px)' : `calc(clamp(560px, calc(100vh - 270px), 780px) - ${debugHeight.value}px)`,
}))
const jsonDefinition = computed(() => JSON.stringify({ name: flowName.value, version: currentVersion.value, trigger: triggerMode.value, nodes: nodes.value, edges: edges.value }, null, 2))

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
    if (Object.values(node.data.params).some((value) => value === '' || value === null || value === undefined)) {
      issues.push({ type: 'error', title: '缺少参数', detail: `${node.data.label} 存在未填写参数` })
    }
    if (node.type !== 'input' && !targets.has(node.id)) {
      issues.push({ type: 'warning', title: '孤立上游', detail: `${node.data.label} 没有上游输入` })
    }
    if (node.type !== 'output' && !sources.has(node.id)) {
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
  void agent.loadTools()
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

function stepColor(type: string) {
  switch (type) {
    case 'thought': return '#7c3aed'
    case 'action': return '#246bfe'
    case 'observation': return '#ea580c'
    case 'answer': return '#16a34a'
    default: return '#64748b'
  }
}

function stepTypeLabel(type: string) {
  switch (type) {
    case 'thought': return '思考'
    case 'action': return '动作'
    case 'observation': return '观察'
    case 'answer': return '回答'
    default: return type
  }
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

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function onNodeClick(event: NodeMouseEvent) {
  selectedNodeId.value = event.node.id
}

function onDragStart(event: DragEvent, preset: NodePreset) {
  event.dataTransfer?.setData('application/vueflow', preset.kind)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDrop(event: DragEvent) {
  const kind = event.dataTransfer?.getData('application/vueflow') ?? ''
  const preset = presetByKind(kind)
  if (!preset) return
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = flow.project({ x: event.clientX - bounds.left, y: event.clientY - bounds.top })
  addNodeFromPreset(preset, position.x, position.y)
}

function addPresetNode(preset: NodePreset) {
  addNodeFromPreset(preset, 260 + nodes.value.length * 48, 120 + nodes.value.length * 24)
  nextTick(() => flow.fitView({ padding: 0.25 }))
}

function addNodeFromPreset(preset: NodePreset, x: number, y: number) {
  const id = `${preset.kind}-${Date.now().toString(36)}`
  nodes.value.push(makeNode(id, preset.kind, preset.title, preset.description, x, y, { ...preset.params }, preset.kind === 'output' ? 'output' : undefined))
  selectedNodeId.value = id
  message.success(`已添加${preset.title}`)
}

function updateParam(key: string, value: ParamValue) {
  if (!selectedData.value) return
  selectedData.value.params[key] = value
}

async function saveFlow() {
  try {
    const payload = { name: flowName.value || '新建流程', trigger: triggerMode.value, nodes: nodes.value as any, edges: edges.value as any }
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
    const exec = await workspace.executeWorkflow(activeWorkflowId.value, { fileId: '', targetKbId: null })
    versionLog.value.unshift(`执行完成: ${exec.status} (${new Date().toLocaleString()})`)
    message.success('流程执行完成')
  } catch { message.error('流程执行失败') }
  finally { running.value = false }
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

async function cancelAgentTask(taskId: string) {
  try {
    await agent.cancelTask(taskId)
    executionProgress.value = 100
  } catch {
    message.error('任务取消失败')
  }
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
      <div class="builder-heading">
        <NSpace align="center">
          <NSelect v-model:value="triggerMode" :options="triggerOptions" class="trigger-select" />
          <NButton circle secondary @click="showVersionDrawer = true">
            <template #icon>
              <NIcon>
                <History />
              </NIcon>
            </template>
          </NButton>
          <NButton secondary type="info" @click="showJson = true">
            <template #icon>
              <NIcon>
                <Download />
              </NIcon>
            </template>
            定义
          </NButton>
          <NButton secondary type="primary" @click="saveFlow">
            <template #icon>
              <NIcon>
                <Save />
              </NIcon>
            </template>
            保存
          </NButton>
          <NButton type="primary" :loading="running" @click="runFlow">
            <template #icon>
              <NIcon>
                <Play />
              </NIcon>
            </template>
            执行
          </NButton>
        </NSpace>
      </div>

      <div class="builder-shell">
        <aside class="builder-sidebar">
          <NCard size="small" title="节点库" :bordered="false" class="builder-card">
            <div class="node-palette">
              <button v-for="item in nodePresets" :key="item.kind" class="palette-item" draggable="true"
                @dragstart="onDragStart($event, item)" @click="addPresetNode(item)">
                <span class="palette-icon" :style="{ color: item.color, backgroundColor: `${item.color}14` }">
                  <NIcon :component="item.icon" />
                </span>
                <span><strong>{{ item.title }}</strong><small>{{ item.description }}</small></span>
                <Plus :size="16" />
              </button>
            </div>
          </NCard>

          <NCard size="small" title="校验状态" :bordered="false" class="builder-card">
            <NAlert :type="hasBlockingIssue ? 'error' : validationIssues.length ? 'warning' : 'success'"
              :show-icon="false">
              {{ validationSummary }}
            </NAlert>
            <div v-if="validationIssues.length" class="issue-list">
              <div v-for="issue in validationIssues" :key="`${issue.title}-${issue.detail}`" class="issue-row">
                <NIcon :component="issue.type === 'error' ? XCircle : CheckCircle2" />
                <span>{{ issue.detail }}</span>
              </div>
            </div>
          </NCard>
        </aside>

        <main class="builder-main">
          <div class="builder-toolbar">
            <NInput v-model:value="flowName" size="large" class="title-input" placeholder="输入流程名称" />
            <NSelect v-if="templateWorkflows.length" :value="null"
              :options="templateWorkflows.map(t => ({ label: t.name, value: t.id }))" placeholder="从模板创建..."
              class="template-select" @update:value="loadTemplateToCanvas" />
            <NTag type="info" round>{{ currentVersion }}</NTag>
            <NTag :type="hasBlockingIssue ? 'error' : 'success'" round>{{ hasBlockingIssue ? '待修复' : '可执行' }}</NTag>
          </div>

          <section class="agent-composer-panel" aria-label="自然语言工具流">
            <AgentTaskComposer :clarification-question="clarificationQuestion" :files="files"
              :knowledge-bases="knowledgeBases" :loading="agentLoading || agentStreaming" :plan-preview="planPreview"
              @continue="continueActiveAgentTask" @preview="previewAgentTask"
              @stream="streamAgentTaskAction"
              @submit="submitAgentTask" />
          </section>

          <div class="canvas-area" :style="canvasAreaStyle" @drop="onDrop" @dragover.prevent>
            <VueFlow v-model:nodes="nodes" v-model:edges="edges" :default-viewport="{ zoom: 0.92, x: 40, y: 28 }"
              :fit-view-on-init="true" class="workflow-canvas" @node-click="onNodeClick">
              <Background pattern-color="#d6e0ee" :gap="18" />
              <MiniMap pannable zoomable />
              <Controls />
              <template #node-default="nodeProps">
                <div class="custom-node" :class="`status-${nodeProps.data.status}`">
                  <div class="node-head">
                    <span class="node-icon"
                      :style="{ color: nodeColor(nodeProps.data.kind), backgroundColor: `${nodeColor(nodeProps.data.kind)}16` }">
                      <NIcon :component="nodeIcon(nodeProps.data.kind)" />
                    </span>
                    <span>{{ nodeProps.data.label }}</span>
                  </div>
                  <p>{{ nodeProps.data.description }}</p>
                  <NTag size="small" :bordered="false">{{ nodeProps.data.kind }}</NTag>
                </div>
              </template>
              <template #node-input="nodeProps">
                <div class="custom-node input-node" :class="`status-${nodeProps.data.status}`">
                  <div class="node-head">
                    <FileInput :size="18" />{{ nodeProps.data.label }}
                  </div>
                  <p>{{ nodeProps.data.description }}</p>
                  <NTag size="small" type="info" :bordered="false">输入</NTag>
                </div>
              </template>
              <template #node-output="nodeProps">
                <div class="custom-node output-node" :class="`status-${nodeProps.data.status}`">
                  <div class="node-head">
                    <UploadCloud :size="18" />{{ nodeProps.data.label }}
                  </div>
                  <p>{{ nodeProps.data.description }}</p>
                  <NTag size="small" type="success" :bordered="false">输出</NTag>
                </div>
              </template>
            </VueFlow>
          </div>

          <div class="debug-entry">
            <div>
              <strong>参数与调试</strong>
              <span>查看当前节点参数、执行进度和单步调试结果</span>
            </div>
            <NButton secondary type="primary" @click="toggleDebugPanel">
              {{ debugCollapsed ? '打开参数调试' : '收起参数调试' }}
            </NButton>
          </div>

          <section v-if="!debugCollapsed" class="debug-panel" :style="{ height: `${debugHeight}px` }">
            <div class="resize-handle" title="上下拖拽调整面板高度" @mousedown="startDebugResize"></div>
            <div class="debug-panel-body">
              <NCard size="small" :bordered="false" class="builder-card">
                <NStatistic label="执行进度" :value="`${executionProgress}%`" />
                <NProgress type="line" :percentage="executionProgress" :show-indicator="false" />
                <NSpace class="run-actions">
                  <NButton size="small" secondary @click="singleStep"><template #icon>
                      <NIcon>
                        <Bug />
                      </NIcon>
                    </template>单步调试
                  </NButton>
                  <NButton size="small" quaternary @click="resetRunState">重置</NButton>
                </NSpace>
              </NCard>

              <NCard size="small" title="节点参数" :bordered="false" class="builder-card grow-card">
                <template v-if="selectedData">
                  <NThing>
                    <template #avatar><span class="detail-icon"
                        :style="{ color: nodeColor(selectedData.kind), backgroundColor: `${nodeColor(selectedData.kind)}16` }">
                        <NIcon :component="nodeIcon(selectedData.kind)" />
                      </span></template>
                    <template #header>{{ selectedData.label }}</template>
                    <template #description>{{ selectedData.description }}</template>
                  </NThing>
                  <NDivider />
                  <NForm label-placement="top" size="small">
                    <NFormItem label="节点名称">
                      <NInput v-model:value="selectedData.label" />
                    </NFormItem>
                    <NFormItem label="说明">
                      <NInput v-model:value="selectedData.description" type="textarea"
                        :autosize="{ minRows: 2, maxRows: 4 }" />
                    </NFormItem>
                    <NFormItem v-for="(value, key) in selectedParams" :key="key" :label="String(key)">
                      <NSwitch v-if="typeof value === 'boolean'" :value="value"
                        @update:value="updateParam(String(key), $event)" />
                      <NInputNumber v-else-if="typeof value === 'number'" :value="value"
                        @update:value="updateParam(String(key), $event ?? 0)" />
                      <NDynamicInput v-else-if="Array.isArray(value)" :value="value"
                        @update:value="updateParam(String(key), $event.map(String))" />
                      <NInput v-else :value="String(value)" @update:value="updateParam(String(key), $event)" />
                    </NFormItem>
                  </NForm>
                </template>
                <NEmpty v-else description="选择一个节点查看参数" />
              </NCard>

              <NCard size="small" :bordered="false" class="builder-card">
                <ToolCatalogPanel :tools="agentTools" />
              </NCard>

              <NCard size="small" :bordered="false" class="builder-card grow-card">
                <AgentTaskDetailPanel
                  :active-task="activeTask"
                  :loading="agentLoading"
                  :task-history="taskHistory"
                  @cancel="cancelAgentTask"
                  @continue="continueActiveAgentTask"
                  @select-task="loadAgentTask"
                />
              </NCard>

              <NCard size="small" :bordered="false" class="builder-card">
                <AgentExecutionTimeline v-if="executionSteps.length" :steps="executionSteps" />
                <NSteps v-else vertical size="small" :current="activeRunStep"
                  :status="running ? 'process' : executionProgress === 100 ? 'finish' : 'wait'">
                  <NStep v-for="node in [...nodes].sort((a, b) => a.position.x - b.position.x)" :key="node.id"
                    :title="node.data.label" :description="node.data.status" />
                </NSteps>
              </NCard>

              <NCard size="small" :bordered="false" class="builder-card">
                <ToolResultViewer :final-answer="finalAnswer" :result-view="resultView" />
              </NCard>
            </div>
          </section>
        </main>
      </div>
    </section>

    <NModal v-model:show="showJson" preset="card" title="流程定义 JSON" class="json-modal">
      <pre>{{ jsonDefinition }}</pre>
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
  min-height: 0;
}

.builder-sidebar {
  display: grid;
  align-content: start;
  gap: 12px;
  min-width: 0;
}

.builder-main {
  min-width: 0;
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
  margin: 12px 12px 0;
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
  width: min(900px, 92vw);
}

.json-modal pre {
  overflow: auto;
  max-height: 62vh;
  padding: 14px;
  color: #dbeafe;
  background: #0f172a;
  border-radius: 8px;
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
