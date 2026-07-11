<script setup lang="ts">
import { computed } from 'vue'

import type { WorkflowInputBlockConfig, WorkflowInputKind } from './workflowDesignerTypes'

const props = withDefaults(defineProps<{
  disabled?: boolean
}>(), {
  disabled: false,
})

const model = defineModel<WorkflowInputBlockConfig>({
  default: () => ({
    defaultValue: '',
    key: 'input_text',
    kind: 'text',
    label: '文本输入',
    required: false,
  }),
})

const kindOptions: Array<{ label: string; value: WorkflowInputKind }> = [
  { label: '文本', value: 'text' },
  { label: '数字', value: 'number' },
  { label: 'JSON', value: 'json' },
  { label: '文件', value: 'file' },
  { label: '知识库', value: 'knowledge_base' },
]

const defaultValueText = computed({
  get() {
    if (model.value.defaultValue == null) return ''
    if (typeof model.value.defaultValue === 'string') return model.value.defaultValue
    return JSON.stringify(model.value.defaultValue, null, 2)
  },
  set(value: string) {
    model.value = { ...model.value, defaultValue: parseDefaultValue(model.value.kind, value) }
  },
})

function updateField<Key extends keyof WorkflowInputBlockConfig>(
  key: Key,
  value: WorkflowInputBlockConfig[Key],
) {
  model.value = { ...model.value, [key]: value }
}

function handleKindUpdate(kind: WorkflowInputKind) {
  model.value = {
    ...model.value,
    defaultValue: defaultForKind(kind),
    kind,
  }
}

function defaultForKind(kind: WorkflowInputKind) {
  if (kind === 'json') return {}
  if (kind === 'number') return 0
  return ''
}

function parseDefaultValue(kind: WorkflowInputKind, value: string) {
  if (kind === 'number') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }
  if (kind === 'json') {
    try {
      return JSON.parse(value || '{}')
    } catch {
      return value
    }
  }
  return value
}
</script>

<template>
  <section class="workflow-input-config" aria-label="输入块配置">
    <div class="workflow-input-config__row">
      <NInput
        :value="model.key"
        :disabled="disabled"
        data-testid="input-config-key"
        placeholder="输入键，例如 query"
        size="small"
        @update:value="updateField('key', $event)"
      />
      <NSelect
        :value="model.kind"
        :disabled="disabled"
        :options="kindOptions"
        data-testid="input-config-kind"
        size="small"
        @update:value="handleKindUpdate"
      />
    </div>
    <NInput
      :value="model.label"
      :disabled="disabled"
      data-testid="input-config-label"
      placeholder="显示名称"
      size="small"
      @update:value="updateField('label', $event)"
    />
    <NInput
      :value="model.description"
      :disabled="disabled"
      data-testid="input-config-description"
      placeholder="说明"
      size="small"
      @update:value="updateField('description', $event || undefined)"
    />
    <NInput
      v-if="model.kind === 'json'"
      v-model:value="defaultValueText"
      :disabled="disabled"
      data-testid="input-config-default"
      placeholder="{ }"
      type="textarea"
      :autosize="{ minRows: 3, maxRows: 5 }"
    />
    <NInput
      v-else
      v-model:value="defaultValueText"
      :disabled="disabled"
      data-testid="input-config-default"
      placeholder="默认值"
      size="small"
    />
    <NCheckbox
      :checked="model.required"
      :disabled="disabled"
      data-testid="input-config-required"
      @update:checked="updateField('required', Boolean($event))"
    >
      必填
    </NCheckbox>
  </section>
</template>

<style scoped>
.workflow-input-config {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.workflow-input-config__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px;
  gap: 8px;
}

@media (max-width: 640px) {
  .workflow-input-config__row {
    grid-template-columns: 1fr;
  }
}
</style>

