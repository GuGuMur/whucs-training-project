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
        class="border border-line rounded-2 bg-surface px-3 py-2"
      >
        <div class="flex flex-wrap items-center gap-2">
          <NTag size="small" round :bordered="false" type="info">{{ phaseLabel(step.phase) }}</NTag>
          <NTag size="small" round :bordered="false" :type="statusType(step.status)">
            {{ statusLabel(step.status) }}
          </NTag>
          <strong class="text-ink text-13px">{{ step.title }}</strong>
          <NTag v-if="step.tool_name" size="small" round :bordered="false">工具: {{ step.tool_name }}</NTag>
        </div>
        <p class="m-0 mt-2 text-ink text-13px leading-[1.65]">{{ step.content }}</p>
        <pre v-if="formatJson(step.input_json)" class="mt-2 overflow-auto rounded-1 bg-#F8FAFD p-2 text-11px">{{ formatJson(step.input_json) }}</pre>
        <pre v-if="formatJson(step.output_json)" class="mt-2 overflow-auto rounded-1 bg-#F8FAFD p-2 text-11px">{{ formatJson(step.output_json) }}</pre>
        <p v-if="step.error_message" class="m-0 mt-2 text-danger text-12px">{{ step.error_message }}</p>
      </article>
    </div>
  </section>
</template>
