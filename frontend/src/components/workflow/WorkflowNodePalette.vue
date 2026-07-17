<script setup lang="ts">
import { computed } from 'vue'
import { Braces, FileText, GitBranch, Hash, IterationCcw, Library, Merge, Plus, Shuffle, Type, Wrench } from '@lucide/vue'

import type { ToolDefinition } from '@/client/workspace'
import type {
  AdvancedWorkflowNodeKind,
  WorkflowInputBlockConfig,
  WorkflowInputKind,
  WorkflowPaletteNodePayload,
} from './workflowDesignerTypes'

const advancedNodes: Array<{ kind: AdvancedWorkflowNodeKind; label: string; description: string; icon: typeof GitBranch }> = [
  { kind: 'condition', label: '条件分支', description: '按 true / false 选择后续路径', icon: GitBranch },
  { kind: 'transform', label: '数据转换', description: '提取、过滤或整理结构化数据', icon: Shuffle },
  { kind: 'loop', label: '数组循环', description: '有上限地逐项处理数组', icon: IterationCcw },
  { kind: 'aggregate', label: '数据聚合', description: '统计、求和或合并数组', icon: Merge },
]

const props = withDefaults(defineProps<{
  inputKinds?: WorkflowInputKind[]
  showDisabledTools?: boolean
  tools?: ToolDefinition[]
}>(), {
  inputKinds: () => ['text', 'knowledge_base', 'file', 'json', 'number'],
  showDisabledTools: false,
  tools: () => [],
})

const emit = defineEmits<{
  addNode: [payload: WorkflowPaletteNodePayload]
  nodeDragStart: [payload: WorkflowPaletteNodePayload]
}>()

const inputPresets: Record<WorkflowInputKind, Omit<WorkflowInputBlockConfig, 'key'>> = {
  file: {
    description: '从执行上下文选择文件 ID',
    kind: 'file',
    label: '文件输入',
    required: false,
  },
  json: {
    defaultValue: {},
    description: '提供结构化 JSON 参数',
    kind: 'json',
    label: 'JSON 输入',
    required: false,
  },
  knowledge_base: {
    description: '从执行上下文选择知识库 ID',
    kind: 'knowledge_base',
    label: '知识库输入',
    required: false,
  },
  number: {
    defaultValue: 0,
    description: '提供数字参数',
    kind: 'number',
    label: '数字输入',
    required: false,
  },
  text: {
    defaultValue: '',
    description: '提供自然语言或短文本参数',
    kind: 'text',
    label: '文本输入',
    required: false,
  },
}

const visibleTools = computed(() =>
  props.tools.filter((tool) => props.showDisabledTools || tool.enabled !== false),
)

const groupedTools = computed(() => {
  const groups = new Map<string, ToolDefinition[]>()
  for (const tool of visibleTools.value) {
    const category = toolCategory(tool)
    groups.set(category, [...(groups.get(category) ?? []), tool])
  }
  return Array.from(groups.entries()).map(([category, items]) => ({ category, items }))
})

const inputBlocks = computed(() =>
  props.inputKinds.map((kind) => ({
    ...inputPresets[kind],
    key: defaultInputKey(kind),
  })),
)

function defaultInputKey(kind: WorkflowInputKind) {
  if (kind === 'file') return 'file_id'
  if (kind === 'knowledge_base') return 'target_kb_id'
  return `input_${kind}`
}

function buildInputPayload(input: WorkflowInputBlockConfig): WorkflowPaletteNodePayload {
  return {
    input,
    kind: 'input',
    label: input.label,
  }
}

function buildToolPayload(tool: ToolDefinition): WorkflowPaletteNodePayload {
  return {
    kind: 'tool',
    label: toolLabel(tool),
    tool,
    toolName: toolLabel(tool),
  }
}

function buildAdvancedPayload(item: typeof advancedNodes[number]): WorkflowPaletteNodePayload {
  return { kind: item.kind, label: item.label }
}

function handleDragStart(event: DragEvent, payload: WorkflowPaletteNodePayload) {
  event.dataTransfer?.setData('application/x-whucs-workflow-node', JSON.stringify(payload))
  event.dataTransfer?.setData('text/plain', payload.label)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
  }
  emit('nodeDragStart', payload)
}

function inputIcon(kind: WorkflowInputKind) {
  return {
    file: FileText,
    json: Braces,
    knowledge_base: Library,
    number: Hash,
    text: Type,
  }[kind]
}

function requiredParams(tool: ToolDefinition) {
  const required = tool.input_schema?.required
  return Array.isArray(required) ? required.map(String) : []
}

function toolCategory(tool: ToolDefinition) {
  return tool.category || 'general'
}

function toolLabel(tool: ToolDefinition) {
  return tool.name || tool.id
}

function toolKey(tool: ToolDefinition) {
  return tool.id || tool.name
}
</script>

<template>
  <section class="workflow-node-palette" aria-label="流程节点库">
    <div class="workflow-node-palette__heading">
      <div class="workflow-node-palette__title">
        <NIcon aria-hidden="true"><Plus /></NIcon>
        <h3>节点库</h3>
      </div>
      <NTag size="small" :bordered="false" round>{{ inputBlocks.length + visibleTools.length }} 个</NTag>
    </div>

    <section class="workflow-node-palette__group" aria-label="输入块">
      <h4>输入块</h4>
      <div class="workflow-node-palette__items">
        <button
          v-for="input in inputBlocks"
          :key="input.kind"
          class="workflow-node-palette__item"
          draggable="true"
          type="button"
          :data-testid="`palette-input-${input.kind}`"
          @click="emit('addNode', buildInputPayload(input))"
          @dragstart="handleDragStart($event, buildInputPayload(input))"
        >
          <NIcon aria-hidden="true" class="workflow-node-palette__icon">
            <component :is="inputIcon(input.kind)" />
          </NIcon>
          <span class="workflow-node-palette__item-copy">
            <strong>{{ input.label }}</strong>
            <small>{{ input.description }}</small>
          </span>
        </button>
      </div>
    </section>

    <section class="workflow-node-palette__group" aria-label="高级节点">
      <h4>高级节点</h4>
      <div class="workflow-node-palette__items">
        <button
          v-for="item in advancedNodes"
          :key="item.kind"
          class="workflow-node-palette__item"
          draggable="true"
          type="button"
          :data-testid="`palette-advanced-${item.kind}`"
          @click="emit('addNode', buildAdvancedPayload(item))"
          @dragstart="handleDragStart($event, buildAdvancedPayload(item))"
        >
          <NIcon aria-hidden="true" class="workflow-node-palette__icon"><component :is="item.icon" /></NIcon>
          <span class="workflow-node-palette__item-copy"><strong>{{ item.label }}</strong><small>{{ item.description }}</small></span>
        </button>
      </div>
    </section>

    <NEmpty v-if="!visibleTools.length" size="small" description="暂无可接入工具" />
    <section
      v-for="group in groupedTools"
      v-else
      :key="group.category"
      class="workflow-node-palette__group"
      :aria-label="`${group.category} 工具`"
    >
      <h4>工具节点 · {{ group.category }}</h4>
      <div class="workflow-node-palette__items">
        <button
          v-for="tool in group.items"
          :key="toolKey(tool)"
          class="workflow-node-palette__item"
          draggable="true"
          type="button"
          :data-testid="`palette-tool-${toolKey(tool)}`"
          @click="emit('addNode', buildToolPayload(tool))"
          @dragstart="handleDragStart($event, buildToolPayload(tool))"
        >
          <NIcon aria-hidden="true" class="workflow-node-palette__icon"><Wrench /></NIcon>
          <span class="workflow-node-palette__item-copy">
            <strong>{{ toolLabel(tool) }}</strong>
            <small>{{ tool.description }}</small>
          </span>
          <span v-if="requiredParams(tool).length" class="workflow-node-palette__params">
            {{ requiredParams(tool).join(', ') }}
          </span>
        </button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.workflow-node-palette {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.workflow-node-palette__heading,
.workflow-node-palette__title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-node-palette__heading {
  justify-content: space-between;
}

.workflow-node-palette__title h3,
.workflow-node-palette__group h4 {
  margin: 0;
}

.workflow-node-palette__title h3 {
  color: #172033;
  font-size: 15px;
  font-weight: 750;
}

.workflow-node-palette__group {
  display: grid;
  gap: 8px;
  min-height: 0;
}

.workflow-node-palette__group h4 {
  color: #64748b;
  font-size: 12px;
  font-weight: 750;
  text-transform: uppercase;
}

.workflow-node-palette__items {
  display: grid;
  gap: 8px;
  max-height: 220px;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.workflow-node-palette__item {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  gap: 8px;
  width: 100%;
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  padding: 9px 10px;
  color: #172033;
  cursor: grab;
  text-align: left;
}

.workflow-node-palette__item:hover {
  border-color: #9db7ef;
  background: #f8fafd;
}

.workflow-node-palette__icon {
  margin-top: 1px;
  color: #2563eb;
}

.workflow-node-palette__item-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.workflow-node-palette__item-copy strong,
.workflow-node-palette__item-copy small,
.workflow-node-palette__params {
  overflow-wrap: anywhere;
}

.workflow-node-palette__item-copy strong {
  font-size: 13px;
  font-weight: 750;
}

.workflow-node-palette__item-copy small,
.workflow-node-palette__params {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.workflow-node-palette__params {
  grid-column: 2;
}
</style>
