<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Bot, Send } from '@lucide/vue'

import type {
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
}>(), {
  clarificationQuestion: '',
  files: () => [],
  knowledgeBases: () => [],
  loading: false,
})

const emit = defineEmits<{
  continue: [payload: WorkspaceAgentTaskContinueInput]
  submit: [payload: WorkspaceAgentTaskInput]
}>()

const taskText = shallowRef('')
const selectedKbId = shallowRef<string | null>(null)
const selectedFileIds = shallowRef<string[]>([])
const clarificationInput = shallowRef('')

const kbOptions = computed(() =>
  props.knowledgeBases.map((kb) => ({ label: kb.name, value: kb.id })),
)
const fileOptions = computed(() =>
  props.files.map((file) => ({ label: file.name, value: file.id })),
)

function submitTask() {
  const task = taskText.value.trim()
  if (!task) return
  emit('submit', {
    contextFileIds: selectedFileIds.value,
    kbId: selectedKbId.value,
    task,
  })
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
    <NButton type="primary" :disabled="!taskText.trim()" :loading="loading" @click="submitTask">
      <template #icon><NIcon aria-hidden="true"><Send /></NIcon></template>
      执行任务
    </NButton>

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
