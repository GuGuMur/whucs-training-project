<script setup lang="ts">
import { computed } from 'vue'
import { Trash2 } from '@lucide/vue'

import type { WorkspaceAgentTask } from '@/client/workspace'

const props = withDefaults(defineProps<{
  activeTaskId?: string | null
  loading?: boolean
  tasks?: WorkspaceAgentTask[]
}>(), {
  activeTaskId: null,
  loading: false,
  tasks: () => [],
})

const emit = defineEmits<{
  deleteTask: [taskId: string]
  selectTask: [taskId: string]
}>()

const visibleTasks = computed(() => props.tasks)

function statusType(status: WorkspaceAgentTask['status']) {
  if (status === 'completed') return 'success'
  if (status === 'failed' || status === 'cancelled') return 'error'
  if (status === 'needs_clarification') return 'warning'
  if (status === 'running') return 'info'
  return 'default'
}

function statusLabel(status: WorkspaceAgentTask['status']) {
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'cancelled') return '已取消'
  if (status === 'needs_clarification') return '需补充'
  if (status === 'running') return '执行中'
  return '排队中'
}

function answerPreview(task: WorkspaceAgentTask) {
  return task.final_answer || task.steps[task.steps.length - 1]?.content || '暂无结果'
}
</script>

<template>
  <section class="agent-task-list" aria-label="智能体任务列表">
    <div class="agent-task-list__header">
      <div>
        <h2 class="agent-task-list__title">任务列表</h2>
        <p class="agent-task-list__subtitle">{{ visibleTasks.length }} 个历史任务</p>
      </div>
    </div>

    <NEmpty v-if="!visibleTasks.length" size="small" description="暂无任务" />

    <div v-else class="agent-task-list__items">
      <article
        v-for="task in visibleTasks"
        :key="task.id"
        class="agent-task-list__item"
        :class="{ 'is-active': task.id === activeTaskId }"
        tabindex="0"
        @click="emit('selectTask', task.id)"
        @keydown.enter.prevent="emit('selectTask', task.id)"
      >
        <div class="agent-task-list__main">
          <div class="agent-task-list__line">
            <strong class="agent-task-list__name">{{ task.task || task.id }}</strong>
            <NTag size="small" round :bordered="false" :type="statusType(task.status)">
              {{ statusLabel(task.status) }}
            </NTag>
          </div>
          <p class="agent-task-list__preview">{{ answerPreview(task) }}</p>
          <div class="agent-task-list__meta">
            <span>{{ task.steps.length }} 步</span>
            <span>{{ task.tool_calls?.length ?? 0 }} 次工具调用</span>
            <span>{{ task.messages?.length ?? 0 }} 条对话</span>
          </div>
        </div>
        <NPopconfirm
          :show-icon="false"
          positive-text="删除"
          negative-text="取消"
          @positive-click="emit('deleteTask', task.id)"
        >
          <template #trigger>
            <NButton
              quaternary
              circle
              type="error"
              size="small"
              :disabled="loading"
              aria-label="删除任务"
              @click.stop
            >
              <template #icon><NIcon aria-hidden="true"><Trash2 /></NIcon></template>
            </NButton>
          </template>
          删除后将从历史任务中移除。
        </NPopconfirm>
      </article>
    </div>
  </section>
</template>

<style scoped>
.agent-task-list {
  display: grid;
  gap: 12px;
}

.agent-task-list__header,
.agent-task-list__line,
.agent-task-list__meta,
.agent-task-list__item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-task-list__header,
.agent-task-list__item {
  justify-content: space-between;
}

.agent-task-list__title {
  margin: 0;
  color: #172033;
  font-size: 16px;
  font-weight: 750;
}

.agent-task-list__subtitle,
.agent-task-list__meta,
.agent-task-list__preview {
  color: #64748b;
  font-size: 12px;
}

.agent-task-list__subtitle,
.agent-task-list__preview {
  margin: 2px 0 0;
}

.agent-task-list__items {
  display: grid;
  gap: 8px;
}

.agent-task-list__item {
  min-width: 0;
  cursor: pointer;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #fff;
  padding: 10px;
  outline: none;
}

.agent-task-list__item:hover,
.agent-task-list__item:focus-visible,
.agent-task-list__item.is-active {
  border-color: #246bfe;
  box-shadow: 0 0 0 2px rgba(36, 107, 254, 0.12);
}

.agent-task-list__main,
.agent-task-list__name,
.agent-task-list__preview {
  min-width: 0;
}

.agent-task-list__main {
  display: grid;
  gap: 4px;
}

.agent-task-list__name,
.agent-task-list__preview {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-task-list__meta {
  flex-wrap: wrap;
}
</style>
