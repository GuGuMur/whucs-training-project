<script setup lang="ts">
import { Play } from '@lucide/vue'
import type { AgentStep, ToolDefinition, WorkflowDefinition } from '@/client/workspace'
import StatusChip from './StatusChip.vue'

defineProps<{
  agentSteps: AgentStep[]
  tools: ToolDefinition[]
  workflows: WorkflowDefinition[]
}>()

function timelineType(status: AgentStep['status']) {
  return {
    pending: 'default',
    running: 'info',
    success: 'success',
    failed: 'error',
  }[status] as 'default' | 'info' | 'success' | 'error'
}
</script>

<template>
  <NCard id="automation" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" size="small">
    <template #header>
      <div class="flex items-start justify-between gap-3">
        <div>
          <h2 class="panel-title">智能体与工具流</h2>
          <p class="mt-1 panel-subtitle">ReAct 执行步骤、工具注册中心和可运行模板</p>
        </div>
        <RouterLink class="btn-primary no-underline" to="/workflow">
          <NIcon aria-hidden="true" class="mr-1.5"><Play /></NIcon>
          打开编排器
        </RouterLink>
      </div>
    </template>

    <NList bordered>
      <NListItem v-for="workflow in workflows" :key="workflow.id">
        <NThing :title="workflow.name" :description="workflow.description">
          <template #header-extra>
            <StatusChip tone="success" :label="workflow.status === 'published' ? '已发布' : '草稿'" />
          </template>
        </NThing>
      </NListItem>
    </NList>

    <NSpace class="my-4" aria-label="内置工具">
      <NTag
        v-for="tool in tools"
        :key="tool.id"
        round
        :color="{ color: '#F1EEFF', textColor: '#5141D8', borderColor: '#DAD4FF' }"
      >
        {{ tool.name }}
      </NTag>
    </NSpace>

    <NTimeline>
      <NTimelineItem v-for="step in agentSteps" :key="`${step.type}-${step.title}`" :type="timelineType(step.status)">
        <template #header>
          <span class="text-ink text-13px font-700">{{ step.title }}</span>
          <NTag
            v-if="step.tool_name"
            size="small"
            round
            class="ml-2"
            :color="{ color: '#F1EEFF', textColor: '#5141D8', borderColor: '#DAD4FF' }"
          >
            {{ step.tool_name }}
          </NTag>
        </template>
        <template #default>
          <p class="m-0 text-sub text-13px leading-[1.5]">{{ step.type }} · {{ step.content }}</p>
        </template>
      </NTimelineItem>
    </NTimeline>
  </NCard>
</template>
