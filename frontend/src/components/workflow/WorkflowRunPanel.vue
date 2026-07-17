<script setup lang="ts">
import { computed } from 'vue'
import type { WorkspaceWorkflowExecution } from '@/client/workspace'
import type { WorkflowInputOption } from './workflowDesignerTypes'

const props = defineProps<{
  execution: WorkspaceWorkflowExecution | null
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

function updateValue(key: string, value: string) {
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
        <NInput
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
