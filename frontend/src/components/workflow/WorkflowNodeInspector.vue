<script setup lang="ts">
import { computed } from 'vue'
import type { ToolDefinition } from '@/client/workspace'
import WorkflowValueBindingEditor from './WorkflowValueBindingEditor.vue'
import type {
  WorkflowDesignerNode,
  WorkflowInputOption,
  WorkflowNodeOutputOption,
  WorkflowValueBinding,
} from './workflowDesignerTypes'

const props = withDefaults(defineProps<{
  node: WorkflowDesignerNode | null
  tools?: ToolDefinition[]
  availableInputs?: WorkflowInputOption[]
  availableNodeOutputs?: WorkflowNodeOutputOption[]
}>(), {
  tools: () => [],
  availableInputs: () => [],
  availableNodeOutputs: () => [],
})
const emit = defineEmits<{ update: [patch: Partial<WorkflowDesignerNode['data']>] }>()

const tool = computed(() => props.tools.find((item) => item.name === props.node?.data.toolName) ?? null)
const schemaFields = computed(() => {
  const properties = tool.value?.input_schema?.properties
  const required = new Set(Array.isArray(tool.value?.input_schema?.required) ? tool.value!.input_schema!.required!.map(String) : [])
  if (!properties || typeof properties !== 'object') return []
  return Object.entries(properties as Record<string, Record<string, unknown>>).map(([key, schema]) => ({
    key,
    label: `${key}${required.has(key) ? ' *' : ''}`,
    type: String(schema.type ?? 'string'),
  }))
})

const rawParametersText = computed({
  get: () => JSON.stringify(props.node?.data.parameters ?? {}, null, 2),
  set: (value: string) => {
    try { emit('update', { parameters: JSON.parse(value || '{}') }) } catch { /* retain last valid JSON */ }
  },
})

function bindingFor(key: string): WorkflowValueBinding {
  const value = props.node?.data.parameters[key]
  if (value && typeof value === 'object' && 'mode' in value) {
    const binding = value as Record<string, unknown>
    if (binding.mode === 'input') return { mode: 'input', inputKey: String(binding.inputKey ?? binding.input_key ?? '') }
    if (binding.mode === 'node') return { mode: 'node', nodeId: String(binding.nodeId ?? binding.node_id ?? ''), path: String(binding.path ?? 'output') }
    if (binding.mode === 'expression' || binding.mode === 'ref') return { mode: 'expression', expression: String(binding.expression ?? binding.value ?? '') }
    return { mode: 'literal', value: binding.value }
  }
  return { mode: 'literal', value: value ?? '' }
}

function updateBinding(key: string, binding: WorkflowValueBinding) {
  if (!props.node) return
  emit('update', { parameters: { ...props.node.data.parameters, [key]: binding } })
}

function updateParameter(key: string, value: unknown) {
  if (!props.node) return
  emit('update', { parameters: { ...props.node.data.parameters, [key]: value } })
}

function listParameterText(value: unknown) {
  return Array.isArray(value) ? value.map(String).join(', ') : ''
}

function parseListParameter(value: string) {
  return value.split(',').map((item: string) => item.trim()).filter(Boolean)
}

const conditionOperators = [
  ['truthy', '为真'], ['falsy', '为假'], ['eq', '等于'], ['ne', '不等于'], ['contains', '包含'],
  ['not_contains', '不包含'], ['gt', '大于'], ['gte', '大于等于'], ['lt', '小于'], ['lte', '小于等于'],
].map(([value, label]) => ({ value, label }))
const transformOperations = ['identity', 'pick', 'omit', 'to_array', 'json_stringify', 'flatten'].map(value => ({ value, label: value }))
const aggregateOperations = ['collect', 'count', 'sum', 'avg', 'min', 'max', 'join'].map(value => ({ value, label: value }))
</script>

<template>
  <aside class="node-inspector">
    <h3>节点配置</h3>
    <NEmpty v-if="!node" size="small" description="选择节点后编辑" />
    <template v-else>
      <NFormItem label="名称">
        <NInput :value="node.data.label" @update:value="emit('update', { label: $event })" />
      </NFormItem>
      <NFormItem label="类型"><NTag>{{ node.data.kind }}</NTag></NFormItem>
      <NFormItem v-if="node.data.toolName" label="工具"><NText code>{{ node.data.toolName }}</NText></NFormItem>
      <section v-if="node.data.kind === 'condition'" class="node-inspector__parameters">
        <WorkflowValueBindingEditor :model-value="bindingFor('left')" :available-inputs="availableInputs" :available-node-outputs="availableNodeOutputs" label="左值" @update:model-value="updateBinding('left', $event)" />
        <NFormItem label="运算符"><NSelect :value="String(node.data.parameters.operator ?? 'truthy')" :options="conditionOperators" @update:value="updateParameter('operator', $event)" /></NFormItem>
        <WorkflowValueBindingEditor v-if="!['truthy', 'falsy'].includes(String(node.data.parameters.operator))" :model-value="bindingFor('right')" :available-inputs="availableInputs" :available-node-outputs="availableNodeOutputs" label="右值" @update:model-value="updateBinding('right', $event)" />
        <NAlert type="info" :bordered="false">请从节点右侧 true / false 端口分别连接分支。</NAlert>
      </section>
      <section v-else-if="node.data.kind === 'transform'" class="node-inspector__parameters">
        <WorkflowValueBindingEditor :model-value="bindingFor('value')" :available-inputs="availableInputs" :available-node-outputs="availableNodeOutputs" label="输入值" @update:model-value="updateBinding('value', $event)" />
        <NFormItem label="转换操作"><NSelect :value="String(node.data.parameters.operation ?? 'identity')" :options="transformOperations" @update:value="updateParameter('operation', $event)" /></NFormItem>
        <NFormItem v-if="['pick', 'omit'].includes(String(node.data.parameters.operation))" :label="node.data.parameters.operation === 'pick' ? '路径（逗号分隔）' : '键（逗号分隔）'">
          <NInput :value="listParameterText(node.data.parameters.paths ?? node.data.parameters.keys)" @update:value="updateParameter(node.data.parameters.operation === 'pick' ? 'paths' : 'keys', parseListParameter($event))" />
        </NFormItem>
      </section>
      <section v-else-if="node.data.kind === 'loop'" class="node-inspector__parameters">
        <WorkflowValueBindingEditor :model-value="bindingFor('items')" :available-inputs="availableInputs" :available-node-outputs="availableNodeOutputs" label="数组" @update:model-value="updateBinding('items', $event)" />
        <NFormItem label="元素路径"><NInput :value="String(node.data.parameters.path ?? '')" placeholder="留空返回整个元素" @update:value="updateParameter('path', $event)" /></NFormItem>
        <NFormItem label="最大迭代次数"><NInputNumber :value="Number(node.data.parameters.max_iterations ?? 100)" :min="1" :max="1000" @update:value="updateParameter('max_iterations', $event ?? 100)" /></NFormItem>
      </section>
      <section v-else-if="node.data.kind === 'aggregate'" class="node-inspector__parameters">
        <WorkflowValueBindingEditor :model-value="bindingFor('values')" :available-inputs="availableInputs" :available-node-outputs="availableNodeOutputs" label="数组" @update:model-value="updateBinding('values', $event)" />
        <NFormItem label="聚合操作"><NSelect :value="String(node.data.parameters.operation ?? 'collect')" :options="aggregateOperations" @update:value="updateParameter('operation', $event)" /></NFormItem>
        <NFormItem v-if="node.data.parameters.operation === 'join'" label="分隔符"><NInput :value="String(node.data.parameters.separator ?? ', ')" @update:value="updateParameter('separator', $event)" /></NFormItem>
      </section>
      <section v-else-if="schemaFields.length" class="node-inspector__parameters">
        <WorkflowValueBindingEditor
          v-for="field in schemaFields"
          :key="field.key"
          :model-value="bindingFor(field.key)"
          :available-inputs="availableInputs"
          :available-node-outputs="availableNodeOutputs"
          :label="field.label"
          :schema-type="field.type"
          @update:model-value="updateBinding(field.key, $event)"
        />
      </section>
      <NFormItem v-else label="参数 JSON">
        <NInput v-model:value="rawParametersText" type="textarea" :autosize="{ minRows: 8, maxRows: 18 }" />
      </NFormItem>
    </template>
  </aside>
</template>

<style scoped>
.node-inspector { padding: 12px; background: #fff; border: 1px solid #d8e0ea; border-radius: 8px; }
.node-inspector h3 { margin: 0 0 12px; color: #172033; font-size: 15px; }
.node-inspector__parameters { display: grid; gap: 14px; }
</style>
