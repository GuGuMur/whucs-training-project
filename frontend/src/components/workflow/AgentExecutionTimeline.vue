<script setup lang="ts">
import type { AgentStep } from '@/client/workspace'

withDefaults(defineProps<{
  steps?: AgentStep[]
}>(), {
  steps: () => [],
})

const phaseLabels: Record<NonNullable<AgentStep['phase']>, string> = {
  answer: '回答',
  call: '调用',
  observe: '观察',
  plan: '规划',
  understand: '理解',
}

function phaseLabel(phase: AgentStep['phase']) {
  return phase ? phaseLabels[phase] : '步骤'
}

function statusLabel(status: AgentStep['status']) {
  if (status === 'needs_clarification') return '需要补充'
  if (status === 'success') return '成功'
  if (status === 'failed') return '失败'
  if (status === 'running') return '执行中'
  return '等待'
}

function statusType(status: AgentStep['status']) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'needs_clarification') return 'warning'
  if (status === 'running') return 'info'
  return 'default'
}

function formatJson(value: unknown) {
  if (!value || typeof value !== 'object') return ''
  return JSON.stringify(value, null, 2)
}

function metadataValue(step: AgentStep, key: string) {
  const metadata = step.metadata
  if (!metadata || typeof metadata !== 'object') return null
  return (metadata as Record<string, unknown>)[key]
}

function plannedTools(step: AgentStep) {
  const input = step.input_json
  if (!input || typeof input !== 'object') return []
  const planned = (input as Record<string, unknown>).planned_tools
  if (!Array.isArray(planned)) return []
  return planned
    .map((item) => {
      if (!Array.isArray(item)) return ''
      return typeof item[0] === 'string' ? item[0] : ''
    })
    .filter(Boolean)
}

function outputSummary(value: unknown) {
  if (!value || typeof value !== 'object') return ''
  const record = value as Record<string, unknown>
  const keys = Object.keys(record)
  if (!keys.length) return ''
  return keys.slice(0, 4).map((key) => `${key}: ${String(record[key]).slice(0, 48)}`).join('，')
}
</script>

<template>
  <section class="grid gap-3" aria-label="智能体执行步骤">
    <div class="flex items-center justify-between gap-3">
      <h2 class="m-0 text-ink text-16px font-750">执行轨迹</h2>
      <NTag size="small" round :bordered="false">{{ steps.length }} 步</NTag>
    </div>
    <NEmpty v-if="!steps.length" size="small" description="尚未执行任务" />
    <div v-else class="grid gap-3">
      <article
        v-for="(step, index) in steps"
        :key="`${step.phase ?? step.type}-${index}`"
        class="execution-step border border-line rounded-2 bg-surface px-3 py-2"
      >
        <div class="flex flex-wrap items-center gap-2">
          <NTag size="small" round :bordered="false" type="info">{{ phaseLabel(step.phase) }}</NTag>
          <NTag size="small" round :bordered="false" :type="statusType(step.status)">
            {{ statusLabel(step.status) }}
          </NTag>
          <strong class="text-ink text-13px">{{ step.title }}</strong>
          <NTag v-if="step.tool_name" size="small" round :bordered="false">工具: {{ step.tool_name }}</NTag>
          <NTag v-if="metadataValue(step, 'retry_count')" size="small" round :bordered="false" type="warning">
            重试 {{ metadataValue(step, 'retry_count') }}
          </NTag>
          <NTag v-if="metadataValue(step, 'latency_ms')" size="small" round :bordered="false">
            {{ metadataValue(step, 'latency_ms') }} ms
          </NTag>
        </div>
        <p class="m-0 mt-2 text-ink text-13px leading-[1.65]">{{ step.content }}</p>
        <div v-if="plannedTools(step).length" class="mt-2 flex flex-wrap gap-1">
          <NTag v-for="tool in plannedTools(step)" :key="tool" size="small" round :bordered="false" type="success">
            {{ tool }}
          </NTag>
        </div>
        <p v-if="outputSummary(step.output_json)" class="m-0 mt-2 text-#475569 text-12px leading-[1.55]">
          输出摘要：{{ outputSummary(step.output_json) }}
        </p>
        <div v-if="formatJson(step.input_json)" class="execution-json">
          <NCode :code="formatJson(step.input_json)" language="json" word-wrap />
        </div>
        <div v-if="formatJson(step.output_json)" class="execution-json">
          <NCode :code="formatJson(step.output_json)" language="json" word-wrap />
        </div>
        <p v-if="step.error_message" class="m-0 mt-2 text-danger text-12px">{{ step.error_message }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.execution-step {
  min-width: 0;
}

.execution-json {
  overflow: auto;
  max-width: 100%;
  max-height: 220px;
  margin-top: 8px;
  border-radius: 6px;
  background: #f8fafd;
  padding: 8px;
}

.execution-json :deep(.n-code) {
  min-width: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  font-size: 11px;
  line-height: 1.55;
}
</style>
