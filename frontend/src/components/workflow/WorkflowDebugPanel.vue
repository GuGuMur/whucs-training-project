<script setup lang="ts">
import type { WorkspaceWorkflowDebugSession, WorkspaceWorkflowDebugStep } from '@/client/workspace'

defineProps<{
  loading: boolean
  session: WorkspaceWorkflowDebugSession | null
  steps: WorkspaceWorkflowDebugStep[]
}>()

const emit = defineEmits<{ cancel: []; start: []; step: [] }>()
</script>

<template>
  <NCard size="small" title="逐步调试">
    <template #header-extra>
      <NSpace>
        <NButton v-if="!session" size="small" :loading="loading" @click="emit('start')">启动调试</NButton>
        <template v-else>
          <NButton size="small" :loading="loading" @click="emit('cancel')">结束调试</NButton>
          <NButton size="small" type="primary" :loading="loading" @click="emit('step')">执行下一节点</NButton>
        </template>
      </NSpace>
    </template>
    <NEmpty v-if="!steps.length" size="small" description="发布流程后可按真实拓扑逐步执行" />
    <NTimeline v-else>
      <NTimelineItem
        v-for="item in steps"
        :key="`${item.step}-${item.node_id}`"
        :type="item.status === 'success' ? 'success' : item.status === 'skipped' ? 'warning' : 'error'"
        :title="`${item.step}. ${item.node_name}`"
        :content="`${item.status} · 剩余 ${item.remaining}`"
      >
        <NCode :code="JSON.stringify(item.output, null, 2)" language="json" word-wrap />
      </NTimelineItem>
    </NTimeline>
  </NCard>
</template>
