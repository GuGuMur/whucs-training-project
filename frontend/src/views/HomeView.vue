<script setup lang="ts">
import { computed, markRaw, nextTick, onMounted, ref } from 'vue'
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
  NAlert,
  NButton,
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NDrawer,
  NDrawerContent,
  NDynamicInput,
  NEmpty,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
  NModal,
  NProgress,
  NSelect,
  NSpace,
  NStatistic,
  NSteps,
  NStep,
  NSwitch,
  NTag,
  NThing,
  NTooltip,
  useMessage,
} from 'naive-ui'
import {
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
const flow = useVueFlow()
const selectedNodeId = ref<string | null>('start-1')
const showJson = ref(false)
const showVersionDrawer = ref(false)
const activeRunStep = ref(0)
const running = ref(false)
const executionProgress = ref(0)
const inspectorCollapsed = ref(true)
const inspectorHeight = ref(320)
const versionLog = ref<string[]>(['v1 草稿已创建'])

const nodePresets: NodePreset[] = [
  { kind: 'tool', title: '工具节点', description: '调用摘要、检索、分类等智能工具', icon: markRaw(Bot), color: '#2563eb', params: { tool: 'document-summarizer', timeout: 30, retry: 2 } },
  { kind: 'condition', title: '条件节点', description: '按规则分支，例如置信度或标签', icon: markRaw(GitBranch), color: '#7c3aed', params: { expression: 'confidence >= 0.8', trueLabel: '通过', falseLabel: '复核' } },
  { kind: 'loop', title: '循环节点', description: '遍历文件、段落或团队成员', icon: markRaw(RefreshCw), color: '#ea580c', params: { iterator: 'files', maxRounds: 5, breakOnError: true } },
  { kind: 'aggregate', title: '聚合节点', description: '汇总多个上游结果', icon: markRaw(GitMerge), color: '#0891b2', params: { strategy: 'merge', requireAll: true } },
  { kind: 'output', title: '输出节点', description: '输出文档、报告或通知', icon: markRaw(UploadCloud), color: '#16a34a', params: { format: 'docx', destination: 'team-space', notify: true } },
]

const templateOptions = [
  { label: '新文件自动摘要', value: 'summary' },
  { label: '团队周报生成', value: 'weekly' },
  { label: '文件内容比对', value: 'compare' },
]

const triggerOptions = [
  { label: '手动触发', value: 'manual' },
  { label: '文件上传后', value: 'file_uploaded' },
  { label: '定时任务', value: 'schedule' },
  { label: 'WebSocket 事件', value: 'websocket' },
]

const flowName = ref('智能文件处理流程')
const triggerMode = ref('file_uploaded')
const currentVersion = ref('v1.2.0')
const template = ref('summary')

const nodes = ref<WorkflowNode[]>([
  makeNode('start-1', 'input', '新文件事件', '监听知识库中新上传的文件', 80, 170, { source: 'knowledge-base', event: 'file.created', required: true }, 'input'),
  makeNode('tool-1', 'tool', '文件自动摘要', '生成标题、摘要、关键词与行动项', 360, 110, { tool: 'document-summarizer', timeout: 30, retry: 2 }),
  makeNode('condition-1', 'condition', '可信度判断', '低可信度结果进入人工复核路径', 650, 170, { expression: 'confidence >= 0.8', trueLabel: '自动通过', falseLabel: '人工复核' }),
  makeNode('output-1', 'output', '写入协同空间', '保存摘要并推送执行结果', 930, 170, { format: 'markdown', destination: 'team-space', notify: true }, 'output'),
])

const edges = ref<WorkflowEdge[]>([
  { id: 'e-start-tool', source: 'start-1', target: 'tool-1', animated: true, label: '文件内容', type: 'smoothstep' },
  { id: 'e-tool-condition', source: 'tool-1', target: 'condition-1', animated: true, label: '摘要结果', type: 'smoothstep' },
  { id: 'e-condition-output', source: 'condition-1', target: 'output-1', animated: true, label: '通过', type: 'smoothstep' },
])

const selectedNode = computed<WorkflowNode | null>(() => nodes.value.find((node) => node.id === selectedNodeId.value) ?? null)
const selectedData = computed<ToolNodeData | null>(() => selectedNode.value?.data ?? null)
const selectedParams = computed<Record<string, ParamValue>>(() => selectedData.value?.params ?? {})
const jsonDefinition = computed(() => JSON.stringify({ name: flowName.value, version: currentVersion.value, trigger: triggerMode.value, nodes: nodes.value, edges: edges.value }, null, 2))
const mainStageStyle = computed(() => ({
  '--debug-panel-height': `${inspectorHeight.value}px`,
}))
const canvasAreaStyle = computed(() => ({
  height: inspectorCollapsed.value
    ? 'calc(100vh - 72px - 57px)'
    : `calc(100vh - 72px - 57px - ${inspectorHeight.value}px)`,
}))

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

onMounted(() => {
  nextTick(() => {
    flow.fitView({ padding: 0.25 })
    window.setTimeout(() => flow.fitView({ padding: 0.25 }), 120)
  })
})

function toggleDebugPanel() {
  inspectorCollapsed.value = !inspectorCollapsed.value
  nextTick(() => flow.fitView({ padding: 0.25 }))
}

function startInspectorResize(event: MouseEvent) {
  event.preventDefault()
  const startY = event.clientY
  const startHeight = inspectorHeight.value

  const onMove = (moveEvent: MouseEvent) => {
    const nextHeight = startHeight - (moveEvent.clientY - startY)
    inspectorHeight.value = Math.min(460, Math.max(240, nextHeight))
  }

  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function saveFlow() {
  const saved = { name: flowName.value, version: currentVersion.value, trigger: triggerMode.value, nodes: nodes.value, edges: edges.value }
  localStorage.setItem('workflow-definition', JSON.stringify(saved))
  versionLog.value.unshift(`${currentVersion.value} 保存于 ${new Date().toLocaleString()}`)
  message.success('流程定义已保存')
}

function validateFlow() {
  if (validationIssues.value.length === 0) message.success('校验通过，可以执行')
  else message.warning(validationSummary.value)
}

async function runFlow() {
  validateFlow()
  if (hasBlockingIssue.value) return

  running.value = true
  executionProgress.value = 0
  activeRunStep.value = 0
  nodes.value.forEach((node) => (node.data.status = 'idle'))

  const orderedNodes = [...nodes.value].sort((a, b) => a.position.x - b.position.x)
  for (let index = 0; index < orderedNodes.length; index += 1) {
    const current = orderedNodes[index]
    if (!current) continue
    activeRunStep.value = index + 1
    current.data.status = 'running'
    await wait(460)
    current.data.status = 'success'
    executionProgress.value = Math.round(((index + 1) / orderedNodes.length) * 100)
  }

  running.value = false
  message.success('执行完成，进度已通过 WebSocket 面板同步')
}

function singleStep() {
  const orderedNodes = [...nodes.value].sort((a, b) => a.position.x - b.position.x)
  const next = orderedNodes.find((node) => node.data.status === 'idle') ?? orderedNodes[0]
  if (!next) return
  next.data.status = next.data.status === 'success' ? 'idle' : 'success'
  selectedNodeId.value = next.id
  executionProgress.value = Math.round((orderedNodes.filter((node) => node.data.status === 'success').length / orderedNodes.length) * 100)
  message.info(`单步调试：${next.data.label}`)
}

function resetRunState() {
  nodes.value.forEach((node) => (node.data.status = 'idle'))
  executionProgress.value = 0
  activeRunStep.value = 0
}

function loadTemplate(value: string) {
  template.value = value
  resetRunState()

  if (value === 'weekly') {
    flowName.value = '团队周报自动生成流程'
    triggerMode.value = 'schedule'
    nodes.value = [
      makeNode('input-weekly', 'input', '周报触发器', '每周五收集团队动态', 90, 180, { cron: '0 18 * * 5', source: 'workspace' }, 'input'),
      makeNode('loop-members', 'loop', '遍历成员动态', '按成员聚合文件、任务与评论', 360, 130, { iterator: 'members', maxRounds: 20, breakOnError: false }),
      makeNode('aggregate-weekly', 'aggregate', '聚合周报素材', '合并亮点、风险与计划', 650, 190, { strategy: 'group-by-section', requireAll: true }),
      makeNode('output-weekly', 'output', '发布团队周报', '输出 Markdown 并通知团队', 940, 190, { format: 'markdown', destination: 'team-channel', notify: true }, 'output'),
    ]
    edges.value = [
      { id: 'e1', source: 'input-weekly', target: 'loop-members', animated: true, type: 'smoothstep' },
      { id: 'e2', source: 'loop-members', target: 'aggregate-weekly', animated: true, type: 'smoothstep' },
      { id: 'e3', source: 'aggregate-weekly', target: 'output-weekly', animated: true, type: 'smoothstep' },
    ]
  } else if (value === 'compare') {
    flowName.value = '文件内容比对流程'
    triggerMode.value = 'manual'
    nodes.value = [
      makeNode('input-compare', 'input', '选择文件组', '接收待比对文件与基准文件', 90, 180, { source: 'manual', required: true }, 'input'),
      makeNode('tool-extract', 'tool', '抽取结构化内容', '抽取标题、段落、表格与实体', 360, 110, { tool: 'content-extractor', timeout: 45, retry: 1 }),
      makeNode('tool-compare', 'tool', '差异比对', '生成相似度、差异段落和冲突项', 650, 200, { tool: 'semantic-diff', timeout: 60, retry: 2 }),
      makeNode('output-compare', 'output', '导出比对报告', '生成可审阅的比对报告', 940, 170, { format: 'docx', destination: 'review-folder', notify: false }, 'output'),
    ]
    edges.value = [
      { id: 'e1', source: 'input-compare', target: 'tool-extract', animated: true, type: 'smoothstep' },
      { id: 'e2', source: 'tool-extract', target: 'tool-compare', animated: true, type: 'smoothstep' },
      { id: 'e3', source: 'tool-compare', target: 'output-compare', animated: true, type: 'smoothstep' },
    ]
  } else {
    flowName.value = '智能文件处理流程'
    triggerMode.value = 'file_uploaded'
    nodes.value = [
      makeNode('start-1', 'input', '新文件事件', '监听知识库中新上传的文件', 80, 170, { source: 'knowledge-base', event: 'file.created', required: true }, 'input'),
      makeNode('tool-1', 'tool', '文件自动摘要', '生成标题、摘要、关键词与行动项', 360, 110, { tool: 'document-summarizer', timeout: 30, retry: 2 }),
      makeNode('condition-1', 'condition', '可信度判断', '低可信度结果进入人工复核路径', 650, 170, { expression: 'confidence >= 0.8', trueLabel: '自动通过', falseLabel: '人工复核' }),
      makeNode('output-1', 'output', '写入协同空间', '保存摘要并推送执行结果', 930, 170, { format: 'markdown', destination: 'team-space', notify: true }, 'output'),
    ]
    edges.value = [
      { id: 'e-start-tool', source: 'start-1', target: 'tool-1', animated: true, label: '文件内容', type: 'smoothstep' },
      { id: 'e-tool-condition', source: 'tool-1', target: 'condition-1', animated: true, label: '摘要结果', type: 'smoothstep' },
      { id: 'e-condition-output', source: 'condition-1', target: 'output-1', animated: true, label: '通过', type: 'smoothstep' },
    ]
  }

  selectedNodeId.value = nodes.value[0]?.id ?? null
  nextTick(() => flow.fitView({ padding: 0.25 }))
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
</script>

<template>
  <n-layout class="workflow-shell" has-sider>
    <n-layout-sider bordered :width="292" class="left-panel">
      <div class="brand-block">
        <div class="brand-icon"><Workflow :size="26" /></div>
        <div>
          <h1>工具流编排</h1>
          <p>Vue Flow 可视化流程编辑器</p>
        </div>
      </div>

      <n-card size="small" title="流程模板" :bordered="false" class="panel-card">
        <n-select v-model:value="template" :options="templateOptions" @update:value="loadTemplate" />
      </n-card>

      <n-card size="small" title="节点库" :bordered="false" class="panel-card">
        <div class="node-palette">
          <button v-for="item in nodePresets" :key="item.kind" class="palette-item" draggable="true" @dragstart="onDragStart($event, item)" @click="addPresetNode(item)">
            <span class="palette-icon" :style="{ color: item.color, backgroundColor: `${item.color}14` }"><n-icon :component="item.icon" /></span>
            <span><strong>{{ item.title }}</strong><small>{{ item.description }}</small></span>
            <Plus :size="16" />
          </button>
        </div>
      </n-card>

      <n-card size="small" title="校验状态" :bordered="false" class="panel-card">
        <n-alert :type="hasBlockingIssue ? 'error' : validationIssues.length ? 'warning' : 'success'" :show-icon="false">{{ validationSummary }}</n-alert>
        <div v-if="validationIssues.length" class="issue-list">
          <div v-for="issue in validationIssues" :key="`${issue.title}-${issue.detail}`" class="issue-row">
            <n-icon :component="issue.type === 'error' ? XCircle : CheckCircle2" />
            <span>{{ issue.detail }}</span>
          </div>
        </div>
      </n-card>
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="topbar">
        <div class="flow-title">
          <n-input v-model:value="flowName" size="large" class="title-input" />
          <n-tag type="info" round>{{ currentVersion }}</n-tag>
          <n-tag :type="hasBlockingIssue ? 'error' : 'success'" round>{{ hasBlockingIssue ? '待修复' : '可执行' }}</n-tag>
        </div>
        <n-space align="center">
          <n-select v-model:value="triggerMode" :options="triggerOptions" class="trigger-select" />
          <n-tooltip trigger="hover">
            <template #trigger><n-button circle @click="showVersionDrawer = true"><template #icon><History /></template></n-button></template>
            版本记录
          </n-tooltip>
          <n-button secondary type="info" @click="showJson = true"><template #icon><Download /></template>定义</n-button>
          <n-button secondary type="primary" @click="saveFlow"><template #icon><Save /></template>保存</n-button>
          <n-button type="primary" :loading="running" @click="runFlow"><template #icon><Play /></template>执行</n-button>
        </n-space>
      </n-layout-header>

      <n-layout-content class="main-stage" :style="mainStageStyle">
        <div class="canvas-area" :style="canvasAreaStyle" @drop="onDrop" @dragover.prevent>
          <VueFlow v-model:nodes="nodes" v-model:edges="edges" :default-viewport="{ zoom: 0.92, x: 40, y: 28 }" :fit-view-on-init="true" class="workflow-canvas" @node-click="onNodeClick">
            <Background pattern-color="#cbd5e1" :gap="18" />
            <MiniMap pannable zoomable />
            <Controls />
            <template #node-default="nodeProps">
              <div class="custom-node" :class="`status-${nodeProps.data.status}`">
                <div class="node-head">
                  <span class="node-icon" :style="{ color: nodeColor(nodeProps.data.kind), backgroundColor: `${nodeColor(nodeProps.data.kind)}16` }"><n-icon :component="nodeIcon(nodeProps.data.kind)" /></span>
                  <span>{{ nodeProps.data.label }}</span>
                </div>
                <p>{{ nodeProps.data.description }}</p>
                <n-tag size="small" :bordered="false">{{ nodeProps.data.kind }}</n-tag>
              </div>
            </template>
            <template #node-input="nodeProps">
              <div class="custom-node input-node" :class="`status-${nodeProps.data.status}`">
                <div class="node-head"><FileInput :size="18" />{{ nodeProps.data.label }}</div>
                <p>{{ nodeProps.data.description }}</p>
                <n-tag size="small" type="info" :bordered="false">输入</n-tag>
              </div>
            </template>
            <template #node-output="nodeProps">
              <div class="custom-node output-node" :class="`status-${nodeProps.data.status}`">
                <div class="node-head"><UploadCloud :size="18" />{{ nodeProps.data.label }}</div>
                <p>{{ nodeProps.data.description }}</p>
                <n-tag size="small" type="success" :bordered="false">输出</n-tag>
              </div>
            </template>
          </VueFlow>
        </div>

        <div class="debug-entry">
          <div>
            <strong>参数与调试</strong>
            <span>查看当前节点参数、执行进度和单步调试结果</span>
          </div>
          <n-button secondary type="primary" @click="toggleDebugPanel">
            {{ inspectorCollapsed ? '打开参数调试' : '收起参数调试' }}
          </n-button>
        </div>

        <section v-if="!inspectorCollapsed" class="debug-panel" :style="{ height: `${inspectorHeight}px` }">
          <div class="resize-handle" title="上下拖拽调整面板高度" @mousedown="startInspectorResize"></div>
          <div class="debug-panel-body">
            <n-card size="small" :bordered="false" class="panel-card">
              <n-statistic label="执行进度" :value="`${executionProgress}%`" />
              <n-progress type="line" :percentage="executionProgress" :show-indicator="false" />
              <n-space class="run-actions">
                <n-button size="small" secondary @click="singleStep"><template #icon><Bug /></template>单步调试</n-button>
                <n-button size="small" quaternary @click="resetRunState">重置</n-button>
              </n-space>
            </n-card>

            <n-card size="small" title="节点参数" :bordered="false" class="panel-card grow-card">
              <template v-if="selectedData">
                <n-thing>
                  <template #avatar><span class="detail-icon" :style="{ color: nodeColor(selectedData.kind), backgroundColor: `${nodeColor(selectedData.kind)}16` }"><n-icon :component="nodeIcon(selectedData.kind)" /></span></template>
                  <template #header>{{ selectedData.label }}</template>
                  <template #description>{{ selectedData.description }}</template>
                </n-thing>
                <n-divider />
                <n-form label-placement="top" size="small">
                  <n-form-item label="节点名称"><n-input v-model:value="selectedData.label" /></n-form-item>
                  <n-form-item label="说明"><n-input v-model:value="selectedData.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" /></n-form-item>
                  <n-form-item v-for="(value, key) in selectedParams" :key="key" :label="String(key)">
                    <n-switch v-if="typeof value === 'boolean'" :value="value" @update:value="updateParam(String(key), $event)" />
                    <n-input-number v-else-if="typeof value === 'number'" :value="value" @update:value="updateParam(String(key), $event ?? 0)" />
                    <n-dynamic-input v-else-if="Array.isArray(value)" :value="value" @update:value="updateParam(String(key), $event.map(String))" />
                    <n-input v-else :value="String(value)" @update:value="updateParam(String(key), $event)" />
                  </n-form-item>
                </n-form>
              </template>
              <n-empty v-else description="选择一个节点查看参数" />
            </n-card>

            <n-card size="small" title="实时执行" :bordered="false" class="panel-card">
              <n-steps vertical size="small" :current="activeRunStep" :status="running ? 'process' : executionProgress === 100 ? 'finish' : 'wait'">
                <n-step v-for="node in [...nodes].sort((a, b) => a.position.x - b.position.x)" :key="node.id" :title="node.data.label" :description="node.data.status" />
              </n-steps>
            </n-card>
          </div>
        </section>
      </n-layout-content>
    </n-layout>
  </n-layout>

  <n-modal v-model:show="showJson" preset="card" title="流程定义 JSON" class="json-modal"><pre>{{ jsonDefinition }}</pre></n-modal>

  <n-drawer v-model:show="showVersionDrawer" :width="360">
    <n-drawer-content title="版本记录">
      <n-descriptions :column="1" bordered size="small">
        <n-descriptions-item v-for="item in versionLog" :key="item" label="记录">{{ item }}</n-descriptions-item>
      </n-descriptions>
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
.workflow-shell {
  --brand: #2563eb;
  --brand-soft: #eff6ff;
  --brand-strong: #1d4ed8;
  --surface: #ffffff;
  --surface-muted: #f8fafc;
  --page-bg: #f3f6fb;
  --line: #dbe4f0;
  --line-soft: #e8eef6;
  --text: #0f172a;
  --muted: #64748b;
  --shadow-soft: 0 10px 28px rgba(15, 23, 42, 0.08);
  --shadow-node: 0 16px 34px rgba(30, 41, 59, 0.14);

  width: 100vw;
  max-width: 100vw;
  height: 100vh;
  overflow: hidden;
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 28rem),
    linear-gradient(180deg, #f8fbff 0%, var(--page-bg) 100%);
}

.left-panel {
  background: rgba(255, 255, 255, 0.94);
  border-right: 1px solid var(--line-soft);
  backdrop-filter: blur(12px);
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 18px 18px;
  border-bottom: 1px solid var(--line-soft);
}

.brand-icon {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  color: var(--brand);
  background: linear-gradient(145deg, #eff6ff, #dbeafe);
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.brand-block h1 {
  margin: 0;
  color: var(--text);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0;
}

.brand-block p {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.panel-card {
  margin: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
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
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
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
  color: var(--muted);
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

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
  padding: 0 18px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid var(--line-soft);
  backdrop-filter: blur(14px);
}

.flow-title {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.title-input {
  width: 340px;
}

.trigger-select {
  width: 168px;
}

.main-stage {
  display: block;
  width: 100%;
  min-width: 0;
  height: calc(100vh - 72px);
  overflow: hidden;
}

.canvas-area {
  width: 100%;
  min-width: 0;
  min-height: 420px;
  padding: 14px 14px 0;
}

.workflow-canvas {
  overflow: hidden;
  width: 100%;
  height: 100%;
  background:
    linear-gradient(rgba(37, 99, 235, 0.025), rgba(37, 99, 235, 0.025)),
    #fbfdff;
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85), var(--shadow-soft);
}

.debug-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.94);
  border-top: 1px solid var(--line-soft);
  backdrop-filter: blur(10px);
}

.debug-entry strong {
  display: block;
  color: var(--text);
  font-size: 15px;
  font-weight: 800;
}

.debug-entry span {
  display: block;
  margin-top: 2px;
  color: var(--muted);
  font-size: 12px;
}

.debug-panel {
  position: relative;
  overflow: auto;
  min-height: 240px;
  max-height: 460px;
  background: #fff;
  border-top: 1px solid var(--line);
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
  background: var(--brand);
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
  color: var(--text);
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #cbd5e1;
  border-left: 5px solid var(--brand);
  border-radius: 8px;
  box-shadow: var(--shadow-node);
  backdrop-filter: blur(8px);
}

.input-node {
  border-left-color: #0f766e;
}

.output-node {
  border-left-color: #16a34a;
}

.status-running {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.16), var(--shadow-node);
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
  border-color: var(--brand);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.16), 0 18px 36px rgba(15, 23, 42, 0.16);
}

:deep(.vue-flow__edge-path) {
  stroke: #64748b;
  stroke-width: 2;
}

:deep(.vue-flow__edge.animated path) {
  stroke: var(--brand);
}

:deep(.vue-flow__controls) {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

:deep(.vue-flow__minimap) {
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

@media (max-width: 1100px) {
  .workflow-shell {
    height: auto;
    overflow: auto;
  }

  .topbar {
    align-items: flex-start;
    flex-direction: column;
    height: auto;
    gap: 10px;
    padding: 12px;
  }

  .main-stage {
    height: auto;
    overflow: visible;
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
