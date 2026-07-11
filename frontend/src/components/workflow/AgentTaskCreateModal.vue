<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Bot, Send } from '@lucide/vue'

import type {
  WorkspaceAgentPlanPreview,
  WorkspaceAgentTaskInput,
  WorkspaceFile,
  WorkspaceKnowledgeBase,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  files?: WorkspaceFile[]
  knowledgeBases?: WorkspaceKnowledgeBase[]
  loading?: boolean
  planPreview?: WorkspaceAgentPlanPreview | null
  show?: boolean
}>(), {
  files: () => [],
  knowledgeBases: () => [],
  loading: false,
  planPreview: null,
  show: false,
})

const emit = defineEmits<{
  preview: [payload: WorkspaceAgentTaskInput]
  stream: [payload: WorkspaceAgentTaskInput]
  submit: [payload: WorkspaceAgentTaskInput]
  'update:show': [show: boolean]
}>()

const taskText = shallowRef('')
const selectedKbId = shallowRef<string | null>(null)
const selectedFileIds = shallowRef<string[]>([])
const streamOutput = shallowRef(true)

const kbOptions = computed(() =>
  props.knowledgeBases.map((kb) => ({ label: kb.name, value: kb.id })),
)
const fileOptions = computed(() =>
  props.files.map((file) => ({ label: file.name, value: file.id })),
)
const canPreview = computed(() => taskText.value.trim().length > 0 && !props.loading)

function closeModal() {
  emit('update:show', false)
}

function buildPayload(): WorkspaceAgentTaskInput | null {
  const task = taskText.value.trim()
  if (!task) return null
  return {
    contextFileIds: selectedFileIds.value,
    kbId: selectedKbId.value,
    task,
  }
}

function previewTask() {
  const payload = buildPayload()
  if (!payload) return
  emit('preview', payload)
}

function confirmTask() {
  const payload = buildPayload()
  if (!payload) return
  if (streamOutput.value) {
    emit('stream', payload)
  } else {
    emit('submit', payload)
  }
  taskText.value = ''
  selectedKbId.value = null
  selectedFileIds.value = []
  closeModal()
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    title="创建智能体任务"
    class="agent-task-create-modal"
    :bordered="false"
    @update:show="emit('update:show', $event)"
  >
    <section class="agent-task-create" aria-label="创建智能体任务">
      <div class="agent-task-create__intro">
        <NIcon aria-hidden="true"><Bot /></NIcon>
        <span>用自然语言描述目标，系统会先给出计划，再按确认的方式执行。</span>
      </div>
      <NInput
        v-model:value="taskText"
        type="textarea"
        placeholder="例如：查询高等数学课程安排并整理成表格"
        :autosize="{ minRows: 4, maxRows: 7 }"
        :disabled="loading"
      />
      <div class="agent-task-create__selectors">
        <NSelect v-model:value="selectedKbId" clearable :options="kbOptions" placeholder="可选知识库" />
        <NSelect
          v-model:value="selectedFileIds"
          multiple
          clearable
          :options="fileOptions"
          placeholder="可选上下文文件"
        />
      </div>
      <div class="agent-task-create__toolbar">
        <div class="agent-task-create__switch">
          <NSwitch v-model:value="streamOutput" :disabled="loading" />
          <span>流式输出</span>
        </div>
        <NButton type="primary" :disabled="!canPreview" :loading="loading" @click="previewTask">
          <template #icon><NIcon aria-hidden="true"><Send /></NIcon></template>
          预览计划
        </NButton>
      </div>

      <NAlert
        v-if="planPreview"
        :type="planPreview.risk_level === 'high' ? 'error' : planPreview.risk_level === 'medium' ? 'warning' : 'info'"
        :bordered="false"
      >
        <div class="agent-task-create__preview">
          <div class="agent-task-create__risk">
            <strong>{{ planPreview.intent || '直接回答' }}</strong>
            <NTag size="small" round :bordered="false">{{ planPreview.risk_level }}</NTag>
            <span>{{ planPreview.risk_reason }}</span>
          </div>
          <div v-if="planPreview.steps?.length" class="agent-task-create__steps">
            <div
              v-for="step in planPreview.steps"
              :key="`${step.tool_name}-${step.rationale}`"
              class="agent-task-create__step"
            >
              <strong>{{ step.tool_name }}</strong>
              <span>{{ step.rationale || step.risk_reason }}</span>
            </div>
          </div>
          <NButton type="primary" :loading="loading" @click="confirmTask">
            {{ streamOutput ? '确认并流式执行' : '确认执行' }}
          </NButton>
        </div>
      </NAlert>
    </section>
  </NModal>
</template>

<style scoped>
.agent-task-create {
  display: grid;
  gap: 12px;
}

.agent-task-create__intro,
.agent-task-create__toolbar,
.agent-task-create__switch,
.agent-task-create__risk {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-task-create__intro {
  color: #475569;
  font-size: 13px;
}

.agent-task-create__selectors {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.agent-task-create__toolbar {
  justify-content: space-between;
}

.agent-task-create__switch {
  color: #64748b;
  font-size: 13px;
}

.agent-task-create__preview,
.agent-task-create__steps {
  display: grid;
  gap: 8px;
}

.agent-task-create__risk {
  flex-wrap: wrap;
}

.agent-task-create__step {
  border-radius: 6px;
  background: #f8fafd;
  padding: 6px 8px;
  color: #172033;
  font-size: 12px;
}

.agent-task-create__step span {
  margin-left: 8px;
  color: #64748b;
}

:global(.agent-task-create-modal) {
  width: min(720px, calc(100vw - 32px));
}

@media (max-width: 720px) {
  .agent-task-create__selectors {
    grid-template-columns: 1fr;
  }

  .agent-task-create__toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
