<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Bot, Send } from '@lucide/vue'

import type {
  WorkspaceAgentPlanPreview,
  WorkspaceAgentTaskContinueInput,
  WorkspaceAgentTaskInput,
  WorkspaceFile,
  WorkspaceKnowledgeBase,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  clarificationQuestion?: string
  files?: WorkspaceFile[]
  knowledgeBases?: WorkspaceKnowledgeBase[]
  loading?: boolean
  planPreview?: WorkspaceAgentPlanPreview | null
}>(), {
  clarificationQuestion: '',
  files: () => [],
  knowledgeBases: () => [],
  loading: false,
  planPreview: null,
})

const emit = defineEmits<{
  continue: [payload: WorkspaceAgentTaskContinueInput]
  preview: [payload: WorkspaceAgentTaskInput]
  stream: [payload: WorkspaceAgentTaskInput]
  submit: [payload: WorkspaceAgentTaskInput]
}>()

const taskText = shallowRef('')
const selectedKbId = shallowRef<string | null>(null)
const selectedFileIds = shallowRef<string[]>([])
const clarificationInput = shallowRef('')
const streamOutput = shallowRef(true)

const kbOptions = computed(() =>
  props.knowledgeBases.map((kb) => ({ label: kb.name, value: kb.id })),
)
const fileOptions = computed(() =>
  props.files.map((file) => ({ label: file.name, value: file.id })),
)

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
}

function submitClarification() {
  const value = clarificationInput.value.trim()
  if (!value) return
  emit('continue', { inputs: { answer: value, course_name: value, query: value } })
  clarificationInput.value = ''
}
</script>

<template>
  <section class="grid gap-3" aria-label="智能体任务输入">
    <div class="flex items-center gap-2">
      <NIcon aria-hidden="true"><Bot /></NIcon>
      <h2 class="m-0 text-ink text-16px font-750">自然语言任务</h2>
    </div>
    <NInput
      v-model:value="taskText"
      type="textarea"
      placeholder="描述要完成的任务，例如：查询高等数学课程安排并整理成表格"
      :autosize="{ minRows: 3, maxRows: 5 }"
      :disabled="loading"
    />
    <div class="grid grid-cols-2 gap-2 max-md:grid-cols-1">
      <NSelect v-model:value="selectedKbId" clearable :options="kbOptions" placeholder="可选知识库" />
      <NSelect
        v-model:value="selectedFileIds"
        multiple
        clearable
        :options="fileOptions"
        placeholder="可选上下文文件"
      />
    </div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <NSwitch v-model:value="streamOutput" :disabled="loading" />
        <span class="text-sub text-13px">流式输出</span>
      </div>
      <NButton type="primary" :disabled="!taskText.trim()" :loading="loading" @click="previewTask">
        <template #icon><NIcon aria-hidden="true"><Send /></NIcon></template>
        预览计划
      </NButton>
    </div>

    <NAlert
      v-if="planPreview"
      :type="planPreview.risk_level === 'high' ? 'error' : planPreview.risk_level === 'medium' ? 'warning' : 'info'"
      :bordered="false"
    >
      <div class="grid gap-2">
        <div class="flex flex-wrap items-center gap-2">
          <strong>{{ planPreview.intent || '直接回答' }}</strong>
          <NTag size="small" round :bordered="false">{{ planPreview.risk_level }}</NTag>
          <span>{{ planPreview.risk_reason }}</span>
        </div>
        <div v-if="planPreview.steps?.length" class="grid gap-1">
          <div v-for="step in planPreview.steps" :key="`${step.tool_name}-${step.rationale}`" class="rounded-1 bg-#F8FAFD px-2 py-1 text-12px">
            <strong>{{ step.tool_name }}</strong>
            <span class="ml-2 text-sub">{{ step.rationale || step.risk_reason }}</span>
          </div>
        </div>
        <NButton type="primary" :loading="loading" @click="confirmTask">
          {{ streamOutput ? '确认并流式执行' : '确认执行' }}
        </NButton>
      </div>
    </NAlert>

    <NAlert v-if="clarificationQuestion" type="warning" :bordered="false">
      {{ clarificationQuestion }}
      <div class="mt-2 flex gap-2">
        <NInput v-model:value="clarificationInput" placeholder="补充必要信息" />
        <NButton :disabled="!clarificationInput.trim()" :loading="loading" @click="submitClarification">
          继续
        </NButton>
      </div>
    </NAlert>
  </section>
</template>
