<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardSummary } from '@/client/workspace'

const props = defineProps<{
  summary: DashboardSummary
}>()

const statItems = computed(() => [
  { label: '文件总数', value: props.summary.file_count },
  { label: '已入库', value: props.summary.indexed_count },
  { label: '知识库', value: props.summary.knowledge_base_count },
  { label: '工具', value: props.summary.tools_enabled },
  { label: '未读', value: props.summary.unread_notifications },
])
</script>

<template>
  <section class="grid grid-cols-5 gap-2.5 max-md:grid-cols-2" aria-label="工作台统计">
    <NCard
      v-for="item in statItems"
      :key="item.label"
      class="min-w-0"
      size="small"
      :bordered="true"
      content-class="!p-3"
    >
      <NStatistic :label="item.label" :value="item.value" />
    </NCard>
  </section>
</template>
