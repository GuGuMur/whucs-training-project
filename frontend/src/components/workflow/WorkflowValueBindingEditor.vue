<script setup lang="ts">
import { computed } from 'vue'

import type {
  WorkflowInputOption,
  WorkflowNodeOutputOption,
  WorkflowValueBinding,
} from './workflowDesignerTypes'

const props = withDefaults(defineProps<{
  availableInputs?: WorkflowInputOption[]
  availableNodeOutputs?: WorkflowNodeOutputOption[]
  disabled?: boolean
  label?: string
  schemaType?: string
}>(), {
  availableInputs: () => [],
  availableNodeOutputs: () => [],
  disabled: false,
  label: '参数绑定',
  schemaType: 'string',
})

const model = defineModel<WorkflowValueBinding>({
  default: () => ({ mode: 'literal', value: '' }),
})

const modeOptions = [
  { label: '固定值', value: 'literal' },
  { label: '输入块', value: 'input' },
  { label: '上游输出', value: 'node' },
  { label: '表达式', value: 'expression' },
]

const inputOptions = computed(() =>
  props.availableInputs.map((input) => ({
    label: input.kind ? `${input.label} · ${input.kind}` : input.label,
    value: input.key,
  })),
)

const nodeOutputOptions = computed(() =>
  props.availableNodeOutputs.map((output) => ({
    label: output.label,
    value: `${output.nodeId}::${output.path}`,
  })),
)

const selectedNodeOutput = computed({
  get() {
    return model.value.mode === 'node' ? `${model.value.nodeId}::${model.value.path}` : null
  },
  set(value: string | null) {
    const [nodeId = '', path = ''] = (value ?? '').split('::')
    model.value = { mode: 'node', nodeId, path }
  },
})

const selectedInput = computed({
  get() {
    return model.value.mode === 'input' ? model.value.inputKey : null
  },
  set(value: string | null) {
    model.value = { mode: 'input', inputKey: value ?? '' }
  },
})

const literalText = computed({
  get() {
    if (model.value.mode !== 'literal') return ''
    if (typeof model.value.value === 'string') return model.value.value
    return JSON.stringify(model.value.value ?? '')
  },
  set(value: string) {
    if (props.schemaType === 'number' || props.schemaType === 'integer') {
      const parsed = Number(value)
      model.value = { mode: 'literal', value: Number.isFinite(parsed) ? parsed : 0 }
    } else if (props.schemaType === 'boolean') {
      model.value = { mode: 'literal', value: value === 'true' }
    } else if (props.schemaType === 'array' || props.schemaType === 'object') {
      try { model.value = { mode: 'literal', value: JSON.parse(value || (props.schemaType === 'array' ? '[]' : '{}')) } }
      catch { model.value = { mode: 'literal', value } }
    } else {
      model.value = { mode: 'literal', value }
    }
  },
})

const expressionText = computed({
  get() {
    return model.value.mode === 'expression' ? model.value.expression : ''
  },
  set(value: string) {
    model.value = { mode: 'expression', expression: value }
  },
})

const currentMode = computed({
  get() {
    return model.value.mode
  },
  set(mode: WorkflowValueBinding['mode']) {
    if (mode === model.value.mode) return
    if (mode === 'input') {
      model.value = { mode, inputKey: props.availableInputs[0]?.key ?? '' }
    } else if (mode === 'node') {
      const first = props.availableNodeOutputs[0]
      model.value = { mode, nodeId: first?.nodeId ?? '', path: first?.path ?? '' }
    } else if (mode === 'expression') {
      model.value = { mode, expression: '' }
    } else {
      model.value = { mode, value: '' }
    }
  },
})
</script>

<template>
  <section class="workflow-binding-editor" :aria-label="label">
    <label class="workflow-binding-editor__label">{{ label }}</label>
    <NSelect
      v-model:value="currentMode"
      :disabled="disabled"
      :options="modeOptions"
      size="small"
      data-testid="binding-mode"
    />

    <NInput
      v-if="model.mode === 'literal'"
      v-model:value="literalText"
      :disabled="disabled"
      data-testid="binding-literal"
      placeholder="输入固定值"
      size="small"
    />
    <NSelect
      v-else-if="model.mode === 'input'"
      v-model:value="selectedInput"
      :disabled="disabled"
      :options="inputOptions"
      data-testid="binding-input"
      placeholder="选择输入块"
      size="small"
    />
    <NSelect
      v-else-if="model.mode === 'node'"
      v-model:value="selectedNodeOutput"
      :disabled="disabled"
      :options="nodeOutputOptions"
      data-testid="binding-node-output"
      placeholder="选择上游输出"
      size="small"
    />
    <NInput
      v-else
      v-model:value="expressionText"
      :disabled="disabled"
      data-testid="binding-expression"
      placeholder="$node.output.path"
      size="small"
    />
  </section>
</template>

<style scoped>
.workflow-binding-editor {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.workflow-binding-editor__label {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}
</style>
