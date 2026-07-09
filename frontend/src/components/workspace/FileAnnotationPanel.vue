<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { MessageSquareText, Reply, Trash2, X } from '@lucide/vue'

import type {
  WorkspaceFile,
  WorkspaceFileAnnotation,
  WorkspaceFileAnnotationCreateInput,
  WorkspaceFileAnnotationReplyInput,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  annotations?: WorkspaceFileAnnotation[]
  deletingAnnotationId?: string | null
  file: WorkspaceFile | null
  loading?: boolean
  saving?: boolean
}>(), {
  annotations: () => [],
  deletingAnnotationId: null,
  loading: false,
  saving: false,
})

const emit = defineEmits<{
  close: []
  'create-annotation': [fileId: string, payload: WorkspaceFileAnnotationCreateInput]
  'delete-annotation': [fileId: string, annotationId: string]
  'load-annotations': [fileId: string]
  'reply-annotation': [annotationId: string, payload: WorkspaceFileAnnotationReplyInput]
}>()

const contentDraft = shallowRef('')
const replyDrafts = shallowRef<Record<string, string>>({})
const errorMessage = shallowRef('')

const sortedAnnotations = computed(() =>
  [...props.annotations].sort((first, second) => Date.parse(second.created_at) - Date.parse(first.created_at)),
)

watch(
  () => props.file?.id,
  (fileId) => {
    contentDraft.value = ''
    replyDrafts.value = {}
    errorMessage.value = ''
    if (fileId) {
      emit('load-annotations', fileId)
    }
  },
  { immediate: true },
)

function handleCreateAnnotation() {
  if (!props.file) {
    return
  }
  const content = contentDraft.value.trim()
  if (!content) {
    errorMessage.value = '请填写批注内容'
    return
  }
  emit('create-annotation', props.file.id, { content, position: null })
  contentDraft.value = ''
  errorMessage.value = ''
}

function handleReply(annotationId: string) {
  const content = (replyDrafts.value[annotationId] ?? '').trim()
  if (!content) {
    errorMessage.value = '请填写回复内容'
    return
  }
  emit('reply-annotation', annotationId, { content })
  replyDrafts.value = {
    ...replyDrafts.value,
    [annotationId]: '',
  }
  errorMessage.value = ''
}

function updateReplyDraft(annotationId: string, value: string) {
  replyDrafts.value = {
    ...replyDrafts.value,
    [annotationId]: value,
  }
}

function handleDelete(annotationId: string) {
  if (!props.file) {
    return
  }
  emit('delete-annotation', props.file.id, annotationId)
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <section v-if="file" data-testid="file-annotation-panel" class="border-t border-line bg-#F8FAFD px-4 py-4">
    <div class="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <NIcon class="text-primary" aria-hidden="true"><MessageSquareText /></NIcon>
          <h3 class="m-0 text-ink text-16px font-700">文件批注</h3>
        </div>
        <p class="m-0 mt-1 break-words text-13px text-sub leading-[1.55]">
          {{ file.name }} · {{ annotations.length }} 条讨论
        </p>
      </div>
      <NButton quaternary size="small" @click="emit('close')">
        <template #icon>
          <NIcon aria-hidden="true"><X /></NIcon>
        </template>
        关闭
      </NButton>
    </div>

    <NAlert v-if="errorMessage" class="mt-3" type="warning" :bordered="false">
      {{ errorMessage }}
    </NAlert>

    <section class="mt-4 border border-line rounded-2 bg-surface p-3">
      <NInput
        v-model:value="contentDraft"
        type="textarea"
        placeholder="添加文件批注"
        :autosize="{ minRows: 2, maxRows: 5 }"
      />
      <div class="mt-3 flex justify-end">
        <NButton
          data-testid="submit-file-annotation"
          type="primary"
          :disabled="!contentDraft.trim()"
          :loading="saving"
          @click="handleCreateAnnotation"
        >
          <template #icon>
            <NIcon aria-hidden="true"><MessageSquareText /></NIcon>
          </template>
          发布批注
        </NButton>
      </div>
    </section>

    <div class="mt-4">
      <NSpin v-if="loading" class="py-5" />
      <NEmpty v-else-if="!sortedAnnotations.length" size="small" description="暂无文件批注" />
      <NList v-else :show-divider="false">
        <NListItem v-for="annotation in sortedAnnotations" :key="annotation.id" class="!px-0 !py-2">
          <article class="grid gap-3 border border-line rounded-2 bg-surface p-3">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <strong class="text-ink text-13px">{{ annotation.author_name }}</strong>
                <span class="ml-2 text-12px text-sub">{{ formatTime(annotation.created_at) }}</span>
              </div>
              <NButton
                :data-testid="`delete-annotation-${annotation.id}`"
                tertiary
                size="tiny"
                :loading="deletingAnnotationId === annotation.id"
                @click="handleDelete(annotation.id)"
              >
                <template #icon>
                  <NIcon aria-hidden="true"><Trash2 /></NIcon>
                </template>
                删除
              </NButton>
            </div>
            <p class="m-0 whitespace-pre-wrap break-words text-13px text-ink leading-[1.6]">
              {{ annotation.content }}
            </p>
            <p v-if="annotation.position?.selected_text" class="m-0 text-12px text-sub">
              定位：{{ annotation.position.selected_text }}
            </p>

            <div v-if="annotation.replies?.length" class="grid gap-2 border-l-3 border-primary/35 pl-3">
              <div v-for="reply in annotation.replies" :key="reply.id" class="rounded-2 bg-#F8FAFD p-2">
                <div class="flex items-start justify-between gap-2">
                  <p class="m-0 text-12px text-sub">
                    <strong class="text-ink">{{ reply.author_name }}</strong>
                    · {{ formatTime(reply.created_at) }}
                  </p>
                  <NButton
                    :data-testid="`delete-annotation-${reply.id}`"
                    quaternary
                    size="tiny"
                    :loading="deletingAnnotationId === reply.id"
                    @click="handleDelete(reply.id)"
                  >
                    <template #icon>
                      <NIcon aria-hidden="true"><Trash2 /></NIcon>
                    </template>
                  </NButton>
                </div>
                <p class="m-0 mt-1 whitespace-pre-wrap break-words text-13px text-ink leading-[1.55]">
                  {{ reply.content }}
                </p>
              </div>
            </div>

            <div class="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2 max-md:grid-cols-1">
              <NInput
                :value="replyDrafts[annotation.id] ?? ''"
                type="textarea"
                placeholder="回复批注"
                :autosize="{ minRows: 1, maxRows: 4 }"
                @update:value="updateReplyDraft(annotation.id, $event)"
              />
              <NButton
                :data-testid="`reply-annotation-${annotation.id}`"
                secondary
                :disabled="!(replyDrafts[annotation.id] ?? '').trim()"
                :loading="saving"
                @click="handleReply(annotation.id)"
              >
                <template #icon>
                  <NIcon aria-hidden="true"><Reply /></NIcon>
                </template>
                回复
              </NButton>
            </div>
          </article>
        </NListItem>
      </NList>
    </div>
  </section>
</template>
