<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { FilePlus2, FileX2, FileText } from '@lucide/vue'

import type {
  WorkspaceFile,
  WorkspaceKnowledgeDocument,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  activeKbId?: string | null
  adding?: boolean
  documents?: WorkspaceKnowledgeDocument[]
  files?: WorkspaceFile[]
  loading?: boolean
  removing?: boolean
}>(), {
  activeKbId: null,
  adding: false,
  documents: () => [],
  files: () => [],
  loading: false,
  removing: false,
})

const emit = defineEmits<{
  'batch-add': [fileIds: string[]]
  'batch-remove': [fileIds: string[]]
}>()

const selectedAddFileIds = shallowRef<string[]>([])
const selectedRemoveFileIds = shallowRef<string[]>([])

const documentFileIds = computed(() => new Set(props.documents.map((document) => document.file_id)))
const addableFiles = computed(() =>
  props.files.filter((file) => file.parse_status === 'indexed' && !documentFileIds.value.has(file.id)),
)

function toggleSelected(list: string[], id: string) {
  return list.includes(id) ? list.filter((item) => item !== id) : [...list, id]
}

function toggleAddFile(fileId: string) {
  selectedAddFileIds.value = toggleSelected(selectedAddFileIds.value, fileId)
}

function toggleRemoveFile(fileId: string) {
  selectedRemoveFileIds.value = toggleSelected(selectedRemoveFileIds.value, fileId)
}

function submitBatchAdd() {
  if (!selectedAddFileIds.value.length) return
  emit('batch-add', selectedAddFileIds.value)
  selectedAddFileIds.value = []
}

function submitBatchRemove() {
  if (!selectedRemoveFileIds.value.length) return
  emit('batch-remove', selectedRemoveFileIds.value)
  selectedRemoveFileIds.value = []
}

function indexStatusLabel(status: WorkspaceKnowledgeDocument['index_status']) {
  if (status === 'indexed') return '已索引'
  if (status === 'indexing') return '索引中'
  if (status === 'failed') return '索引失败'
  return '等待索引'
}

function statusType(status: string) {
  if (status === 'indexed') return 'success'
  if (status === 'failed') return 'error'
  return 'warning'
}
</script>

<template>
  <section class="grid gap-3" aria-label="知识库文件管理">
    <!-- Addable files -->
    <div v-if="addableFiles.length" class="rounded-2 bg-#F7F9FC p-3">
      <div class="flex items-center justify-between gap-2 mb-2">
        <p class="m-0 text-ink text-13px font-700">可入库文件</p>
        <NButton
          data-testid="batch-add-files"
          type="primary"
          size="tiny"
          :disabled="!activeKbId || !selectedAddFileIds.length"
          :loading="adding"
          @click="submitBatchAdd"
        >
          <template #icon><NIcon :size="12"><FilePlus2 /></NIcon></template>
          加入知识库
        </NButton>
      </div>
      <div class="grid gap-1.5 max-h-240px overflow-auto">
        <button
          v-for="file in addableFiles" :key="file.id" type="button"
          :data-testid="`select-file-${file.id}`"
          class="w-full flex items-center gap-2 rounded-1.5 border px-2.5 py-1.5 text-left text-13px transition-colors"
          :class="selectedAddFileIds.includes(file.id) ? 'border-primary bg-primary/8' : 'border-transparent bg-white hover:bg-muted'"
          @click="toggleAddFile(file.id)"
        >
          <NIcon :size="13" color="var(--sub-color)"><FileText /></NIcon>
          <span class="flex-1 truncate text-ink">{{ file.name }}</span>
          <span class="text-sub text-11px shrink-0">{{ file.type }}</span>
        </button>
      </div>
    </div>

    <!-- Indexed documents -->
    <div>
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="flex items-center gap-2">
          <p class="m-0 text-ink text-13px font-700">已入库文件</p>
          <NTag size="tiny" round :bordered="false">{{ documents.length }}</NTag>
        </div>
        <NButton
          v-if="selectedRemoveFileIds.length"
          data-testid="batch-remove-files"
          type="error"
          size="tiny"
          :loading="removing || loading"
          @click="submitBatchRemove"
        >
          <template #icon><NIcon :size="12"><FileX2 /></NIcon></template>
          移出 {{ selectedRemoveFileIds.length }} 个
        </NButton>
      </div>
      <NEmpty v-if="!documents.length" size="small" description="上传文件后将自动入库，或点击「重建索引」" />
      <div v-else class="grid gap-1.5 max-h-320px overflow-auto">
        <button
          v-for="document in documents" :key="document.id" type="button"
          :data-testid="`select-document-${document.file_id}`"
          class="w-full flex items-center gap-2 rounded-1.5 border px-2.5 py-1.5 text-left text-13px transition-colors"
          :class="selectedRemoveFileIds.includes(document.file_id) ? 'border-danger bg-danger/8' : 'border-transparent bg-#F8FAFD hover:bg-muted'"
          @click="toggleRemoveFile(document.file_id)"
        >
          <NIcon :size="13" color="var(--sub-color)"><FileText /></NIcon>
          <div class="flex-1 min-w-0">
            <p class="m-0 truncate text-ink font-550">{{ document.file_name }}</p>
            <p class="m-0 text-sub text-11px">{{ document.chunk_count }} 片段
              <span v-if="document.error_message"> · {{ document.error_message }}</span>
            </p>
          </div>
          <NTag size="tiny" round :bordered="false" :type="statusType(document.index_status)">
            {{ indexStatusLabel(document.index_status) }}
          </NTag>
        </button>
      </div>
    </div>
  </section>
</template>
