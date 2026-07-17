<script setup lang="ts">
import { computed } from 'vue'
import type { WorkspaceFile, WorkspaceWorkflowExecution } from '@/client/workspace'
import type { WorkflowInputOption } from './workflowDesignerTypes'

const props = defineProps<{
  execution: WorkspaceWorkflowExecution | null
  files?: WorkspaceFile[]
  inputs: WorkflowInputOption[]
  loading: boolean
}>()

const executionCounts = computed(() => {
  const items = props.execution?.node_executions ?? []
  return {
    completed: items.filter(item => item.status === 'success').length,
    skipped: items.filter(item => item.status === 'skipped').length,
  }
})

const emit = defineEmits<{ run: [] }>()
const values = defineModel<Record<string, unknown>>('values', { required: true })
const fileOptions = computed(() => (props.files ?? []).map(file => ({
  label: `${file.name} · ${file.type}`,
  value: file.id,
})))

function isFileSelectionInput(key: string) {
  return key === 'file_a' || key === 'file_b'
}

function stringValue(key: string) {
  return typeof values.value[key] === 'string' ? values.value[key] : null
}

function updateValue(key: string, value: string | null) {
  values.value = { ...values.value, [key]: value }
}
</script>

<template>
  <NCard size="small" title="运行流程">
    <template #header-extra>
      <NButton type="primary" size="small" :loading="loading" @click="emit('run')">使用当前输入运行</NButton>
    </template>
    <NEmpty v-if="!inputs.length" size="small" description="当前流程没有显式输入，可直接运行" />
    <NForm v-else label-placement="left" label-width="140">
      <NFormItem v-for="item in inputs" :key="item.key" :label="item.label">
        <NSelect
          v-if="isFileSelectionInput(item.key)"
          clearable
          filterable
          :options="fileOptions"
          :placeholder="item.key === 'file_a' ? '选择基准文件' : '选择对比文件'"
          :value="stringValue(item.key)"
          @update:value="updateValue(item.key, $event)"
        />
        <NInput
          v-else
          :value="String(values[item.key] ?? '')"
          :placeholder="item.kind ? `输入 ${item.kind}` : '输入运行值'"
          @update:value="updateValue(item.key, $event)"
        />
      </NFormItem>
    </NForm>
    <NAlert v-if="execution" class="workflow-run-panel__result" :type="execution.status === 'completed' ? 'success' : 'error'">
      {{ execution.id }} · {{ execution.status }} · 成功 {{ executionCounts.completed }} · 跳过 {{ executionCounts.skipped }}
    </NAlert>
  </NCard>
</template>

<style scoped>
.workflow-run-panel__result { margin-top: 10px; }
</style>
