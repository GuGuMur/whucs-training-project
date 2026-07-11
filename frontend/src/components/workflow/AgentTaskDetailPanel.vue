<script setup lang="ts">
import { computed, h, shallowRef } from 'vue'
import { Ban, Clock3, MessageSquarePlus, RotateCw } from '@lucide/vue'

import type {
  WorkspaceAgentTask,
  WorkspaceAgentTaskContinueInput,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  activeTask?: WorkspaceAgentTask | null
  loading?: boolean
  taskHistory?: WorkspaceAgentTask[]
}>(), {
  activeTask: null,
  loading: false,
  taskHistory: () => [],
})

const emit = defineEmits<{
  cancel: [taskId: string]
  continue: [payload: WorkspaceAgentTaskContinueInput]
  selectTask: [taskId: string]
}>()

const followUpText = shallowRef('')
const activeTab = shallowRef<'messages' | 'tools' | 'plans'>('messages')

const historyItems = computed(() =>
  props.taskHistory.map((task) => ({
    label: `${statusLabel(task.status)} · ${task.task || task.id}`,
    value: task.id,
  })),
)
const selectedTaskId = computed(() => props.activeTask?.id ?? null)
const messages = computed(() => props.activeTask?.messages ?? [])
const toolCalls = computed(() => props.activeTask?.tool_calls ?? [])
const planRevisions = computed(() => props.activeTask?.plan_revisions ?? [])
const taskStats = computed(() => ({
  messages: messages.value.length,
  plans: planRevisions.value.length,
  tools: toolCalls.value.length,
}))
const latestToolLatency = computed(() => {
  if (!toolCalls.value.length) return 0
  return toolCalls.value.reduce((total, call) => total + (call.latency_ms ?? 0), 0)
})
const canCancel = computed(() =>
  props.activeTask ? !['completed', 'failed', 'cancelled'].includes(props.activeTask.status) : false,
)

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

function roleLabel(role: string) {
  if (role === 'user') return '用户'
  if (role === 'assistant') return '智能体'
  return '系统'
}

function messageType(metadata: Record<string, unknown> | undefined) {
  if (!metadata) return ''
  if (metadata.kind === 'history_summary') return '历史摘要'
  if (metadata.task) return '任务'
  return ''
}

function formatJson(value: unknown) {
  if (!value || typeof value !== 'object') return ''
  return JSON.stringify(value, null, 2)
}

function compactJson(value: unknown) {
  if (!value || typeof value !== 'object') return '无'
  const record = value as Record<string, unknown>
  const keys = Object.keys(record)
  if (!keys.length) return '空对象'
  return keys.slice(0, 4).map((key) => `${key}: ${String(record[key]).slice(0, 36)}`).join('，')
}

function planToolNames(planJson: unknown) {
  if (!planJson || typeof planJson !== 'object') return 'direct_answer'
  const plan = planJson as Record<string, unknown>
  const steps = Array.isArray(plan.plan_steps) ? plan.plan_steps : []
  const names = steps
    .map((item) => (item && typeof item === 'object' ? (item as Record<string, unknown>).tool_name : null))
    .filter((name): name is string => typeof name === 'string' && name.length > 0)
  return names.length ? names.join(' -> ') : 'direct_answer'
}

function renderHistoryLabel(option: { label?: string }) {
  return h('span', { class: 'agent-detail__history-option' }, option.label ?? '')
}

function selectTask(taskId: string | null) {
  if (!taskId) return
  emit('selectTask', taskId)
}

function submitFollowUp() {
  const message = followUpText.value.trim()
  if (!message) return
  emit('continue', { message, inputs: {} })
  followUpText.value = ''
}

function cancelActiveTask() {
  if (!props.activeTask) return
  emit('cancel', props.activeTask.id)
}
</script>

<template>
  <section class="agent-detail" aria-label="智能体任务详情">
    <div class="agent-detail__header">
      <div>
        <h2 class="agent-detail__title">任务详情</h2>
        <p class="agent-detail__subtitle">多轮对话、工具调用和计划修订</p>
      </div>
      <NTag v-if="activeTask" round :bordered="false" :type="statusType(activeTask.status)">
        {{ statusLabel(activeTask.status) }}
      </NTag>
    </div>

    <NSelect
      :value="selectedTaskId"
      clearable
      :options="historyItems"
      placeholder="选择历史任务"
      :render-label="renderHistoryLabel"
      @update:value="selectTask"
    />

    <div v-if="taskHistory.length" class="agent-detail__history-list" aria-label="任务历史">
      <NButton
        v-for="task in taskHistory.slice(0, 5)"
        :key="task.id"
        size="small"
        :type="task.id === selectedTaskId ? 'primary' : 'default'"
        :secondary="task.id !== selectedTaskId"
        @click="selectTask(task.id)"
      >
        {{ task.task || task.id }}
      </NButton>
    </div>

    <NEmpty v-if="!activeTask" size="small" description="尚未选择任务" />

    <template v-else>
      <div class="agent-detail__summary">
        <div>
          <span class="agent-detail__summary-label">对话</span>
          <strong>{{ taskStats.messages }}</strong>
        </div>
        <div>
          <span class="agent-detail__summary-label">工具</span>
          <strong>{{ taskStats.tools }}</strong>
        </div>
        <div>
          <span class="agent-detail__summary-label">修订</span>
          <strong>{{ taskStats.plans }}</strong>
        </div>
        <div>
          <span class="agent-detail__summary-label">工具耗时</span>
          <strong>{{ latestToolLatency }} ms</strong>
        </div>
      </div>

      <div class="agent-detail__actions">
        <NInput
          v-model:value="followUpText"
          type="textarea"
          placeholder="继续追问或补充约束"
          :autosize="{ minRows: 2, maxRows: 4 }"
          :disabled="loading"
        />
        <div class="agent-detail__action-row">
          <NButton :disabled="!followUpText.trim()" :loading="loading" type="primary" @click="submitFollowUp">
            <template #icon><NIcon aria-hidden="true"><MessageSquarePlus /></NIcon></template>
            继续对话
          </NButton>
          <NButton :disabled="!canCancel" :loading="loading" secondary type="error" @click="cancelActiveTask">
            <template #icon><NIcon aria-hidden="true"><Ban /></NIcon></template>
            取消任务
          </NButton>
        </div>
      </div>

      <NTabs v-model:value="activeTab" type="segment">
        <NTabPane name="messages" tab="对话">
          <div v-if="messages.length" class="agent-detail__list">
            <article v-for="message in messages" :key="message.id" class="agent-detail__item">
              <div class="agent-detail__meta">
                <NTag size="small" round :bordered="false">{{ roleLabel(message.role) }}</NTag>
                <NTag v-if="messageType(message.metadata)" size="small" round :bordered="false" type="info">
                  {{ messageType(message.metadata) }}
                </NTag>
              </div>
              <p class="agent-detail__content">{{ message.content }}</p>
            </article>
          </div>
          <NEmpty v-else size="small" description="暂无对话记录" />
        </NTabPane>

        <NTabPane name="tools" tab="工具调用">
          <div v-if="toolCalls.length" class="agent-detail__list">
            <article v-for="call in toolCalls" :key="call.id" class="agent-detail__item">
              <div class="agent-detail__meta">
                <NTag size="small" round :bordered="false" type="info">{{ call.tool_name }}</NTag>
                <NTag size="small" round :bordered="false">{{ call.status }}</NTag>
                <NIcon aria-hidden="true"><Clock3 /></NIcon>
                <span class="agent-detail__latency">{{ call.latency_ms ?? 0 }} ms</span>
              </div>
              <p class="agent-detail__content">输入摘要：{{ compactJson(call.input_json) }}</p>
              <p class="agent-detail__content">输出摘要：{{ compactJson(call.output_json) }}</p>
              <pre v-if="formatJson(call.input_json)" class="agent-detail__code">{{ formatJson(call.input_json) }}</pre>
              <pre v-if="formatJson(call.output_json)" class="agent-detail__code">{{ formatJson(call.output_json) }}</pre>
              <p v-if="call.error_message" class="agent-detail__error">{{ call.error_message }}</p>
            </article>
          </div>
          <NEmpty v-else size="small" description="暂无工具调用" />
        </NTabPane>

        <NTabPane name="plans" tab="计划修订">
          <div v-if="planRevisions.length" class="agent-detail__list">
            <article v-for="revision in planRevisions" :key="revision.id" class="agent-detail__item">
              <div class="agent-detail__meta">
                <NIcon aria-hidden="true"><RotateCw /></NIcon>
                <strong>第 {{ revision.revision_no + 1 }} 版</strong>
                <span>{{ revision.reason }}</span>
              </div>
              <p class="agent-detail__content">计划路径：{{ planToolNames(revision.plan_json) }}</p>
              <pre v-if="formatJson(revision.plan_json)" class="agent-detail__code">{{ formatJson(revision.plan_json) }}</pre>
            </article>
          </div>
          <NEmpty v-else size="small" description="暂无计划修订" />
        </NTabPane>
      </NTabs>
    </template>
  </section>
</template>

<style scoped>
.agent-detail {
  display: grid;
  gap: 12px;
}

.agent-detail__header,
.agent-detail__action-row,
.agent-detail__meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-detail__header {
  justify-content: space-between;
}

.agent-detail__title {
  margin: 0;
  color: #172033;
  font-size: 16px;
  font-weight: 750;
}

.agent-detail__subtitle,
.agent-detail__latency {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 12px;
}

.agent-detail__actions,
.agent-detail__list,
.agent-detail__history-list {
  display: grid;
  gap: 10px;
}

.agent-detail__history-list {
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.agent-detail__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.agent-detail__summary > div {
  min-width: 0;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #f8fafd;
  padding: 8px;
}

.agent-detail__summary-label {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.agent-detail__history-option {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-detail__item {
  min-width: 0;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #fff;
  padding: 10px;
}

.agent-detail__content {
  margin: 8px 0 0;
  white-space: pre-wrap;
  color: #172033;
  font-size: 13px;
  line-height: 1.65;
}

.agent-detail__code {
  overflow: auto;
  max-height: 180px;
  margin: 8px 0 0;
  border-radius: 6px;
  background: #f8fafd;
  padding: 8px;
  color: #172033;
  font-size: 11px;
}

.agent-detail__error {
  margin: 8px 0 0;
  color: #dc2626;
  font-size: 12px;
}

@media (max-width: 720px) {
  .agent-detail__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
