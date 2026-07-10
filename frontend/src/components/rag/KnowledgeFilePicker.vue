<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { FilePlus2, FileX2 } from '@lucide/vue'

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
const removableDocuments = computed(() => props.documents)

const desktopColumns = computed(() => [
  { key: 'name', title: '文件' },
  { key: 'parseStatus', title: '解析状态' },
  { key: 'tags', title: '标签' },
])

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

function parseStatusLabel(status: WorkspaceFile['parse_status']) {
  if (status === 'indexed') return '已解析'
  if (status === 'parsing') return '解析中'
  if (status === 'failed') return '解析失败'
  return '等待解析'
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
  <section class="grid gap-4" aria-label="知识库文件管理">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="min-w-0">
        <h2 class="m-0 text-ink text-16px font-750">文件入库</h2>
        <p class="m-0 mt-1 text-sub text-12px">选择已解析文件批量加入或移出当前知识库</p>
      </div>
      <div class="flex gap-2">
        <NButton
          data-testid="batch-add-files"
          type="primary"
          size="small"
          :disabled="!activeKbId || !selectedAddFileIds.length"
          :loading="adding"
          @click="submitBatchAdd"
        >
          <template #icon><NIcon aria-hidden="true"><FilePlus2 /></NIcon></template>
          批量加入
        </NButton>
        <NButton
          data-testid="batch-remove-files"
          secondary
          size="small"
          :disabled="!activeKbId || !selectedRemoveFileIds.length"
          :loading="removing || loading"
          @click="submitBatchRemove"
        >
          <template #icon><NIcon aria-hidden="true"><FileX2 /></NIcon></template>
          批量移除
        </NButton>
      </div>
    </div>

    <div class="hidden md:block">
      <NDataTable :columns="desktopColumns" :data="addableFiles" size="small" :pagination="false" />
    </div>

    <div class="grid gap-2">
      <div class="flex items-center justify-between gap-3">
        <h3 class="m-0 text-ink text-14px font-700">可加入文件</h3>
        <NTag size="small" round :bordered="false">{{ addableFiles.length }} 个</NTag>
      </div>
      <NEmpty v-if="!addableFiles.length" size="small" description="暂无可加入的已解析文件" />
      <button
        v-for="file in addableFiles"
        v-else
        :key="file.id"
        type="button"
        :data-testid="`select-file-${file.id}`"
        class="w-full border rounded-2 px-3 py-2 text-left transition-colors"
        :class="selectedAddFileIds.includes(file.id) ? 'border-primary bg-#EEF5FF' : 'border-line bg-surface hover:bg-muted'"
        @click="toggleAddFile(file.id)"
      >
        <div class="flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="m-0 truncate text-ink text-13px font-700">{{ file.name }}</p>
            <p class="m-0 mt-0.5 text-sub text-12px">{{ file.tags.join(' / ') || '无标签' }}</p>
          </div>
          <NTag size="small" round :bordered="false" :type="statusType(file.parse_status)">
            {{ parseStatusLabel(file.parse_status) }}
          </NTag>
        </div>
      </button>
    </div>

    <div class="grid gap-2">
      <div class="flex items-center justify-between gap-3">
        <h3 class="m-0 text-ink text-14px font-700">已入库文件</h3>
        <NTag size="small" round :bordered="false">{{ removableDocuments.length }} 个</NTag>
      </div>
      <NEmpty v-if="!removableDocuments.length" size="small" description="当前知识库暂无文件" />
      <button
        v-for="document in removableDocuments"
        v-else
        :key="document.id"
        type="button"
        :data-testid="`select-document-${document.file_id}`"
        class="w-full border rounded-2 px-3 py-2 text-left transition-colors"
        :class="selectedRemoveFileIds.includes(document.file_id) ? 'border-danger bg-#FFF1F2' : 'border-line bg-#F8FAFD hover:bg-muted'"
        @click="toggleRemoveFile(document.file_id)"
      >
        <div class="flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="m-0 truncate text-ink text-13px font-700">{{ document.file_name }}</p>
            <p class="m-0 mt-0.5 text-sub text-12px">
              {{ document.chunk_count }} 片段
              <span v-if="document.error_message"> · {{ document.error_message }}</span>
            </p>
          </div>
          <NTag size="small" round :bordered="false" :type="statusType(document.index_status)">
            {{ indexStatusLabel(document.index_status) }}
          </NTag>
        </div>
      </button>
    </div>
  </section>
</template>
